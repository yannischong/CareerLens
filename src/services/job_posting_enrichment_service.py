import html
import ipaddress
import json
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx


FETCH_TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 2_000_000
MAX_REDIRECTS = 5

BLOCKED_HOST_SUFFIXES = {
    "localhost",
    "localhost.localdomain",
}

AGGREGATOR_HOST_HINTS = (
    "google.com",
    "googleusercontent.com",
    "linkedin.com",
    "indeed.com",
    "jooble.org",
    "jooble.com",
)

ATS_HOST_HINTS = {
    "greenhouse": (
        "greenhouse.io",
        "greenhouse.com",
    ),
    "lever": (
        "lever.co",
    ),
    "smartrecruiters": (
        "smartrecruiters.com",
    ),
    "workday": (
        "myworkdayjobs.com",
        "myworkdaysite.com",
    ),
    "ashby": (
        "ashbyhq.com",
    ),
}

HYDRATION_KEY_HINTS = {
    "description",
    "descriptionhtml",
    "descriptionplain",
    "jobdescription",
    "jobdescriptionhtml",
    "jobdescriptiontext",
    "jobsummary",
    "responsibilities",
    "qualifications",
    "requirements",
    "skills",
    "additionaljobdescription",
    "experience",
    "education",
}

TARGET_ATTRIBUTE_HINTS = (
    "job-description",
    "jobdescription",
    "job_description",
    "job-details",
    "jobdetails",
    "job-content",
    "jobcontent",
    "posting-description",
    "postingdescription",
    "position-description",
    "positiondescription",
    "job-posting-description",
    "jobpostingdescription",
    "jobPostingDescription",
)

BLOCK_TAGS = {
    "p",
    "div",
    "section",
    "article",
    "li",
    "ul",
    "ol",
    "br",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "tr",
    "td",
}

SKIP_TAGS = {
    "script",
    "style",
    "svg",
    "canvas",
    "noscript",
    "form",
}


class _PostingHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._depth = 0
        self._skip_roots = []
        self._target_roots = []
        self._main_roots = []
        self._json_ld_root = None
        self._json_ld_chunks = []
        self._json_root = None
        self._json_chunks = []
        self.json_ld_blocks = []
        self.json_blocks = []
        self.target_chunks = []
        self.main_chunks = []

    def _inside(self, roots):
        return bool(roots)

    def handle_starttag(self, tag, attrs):
        self._depth += 1
        tag = tag.casefold()
        attrs_dict = {
            str(key).casefold(): str(value or "")
            for key, value in attrs
        }

        if tag == "script" and (
            attrs_dict.get("type", "")
            .casefold()
            .startswith("application/ld+json")
        ):
            self._json_ld_root = self._depth
            self._json_ld_chunks = []
            return

        if tag == "script":
            script_type = attrs_dict.get("type", "").casefold()
            script_id = attrs_dict.get("id", "").casefold()

            if (
                "application/json" in script_type
                or script_id == "__next_data__"
            ):
                self._json_root = self._depth
                self._json_chunks = []
                return

        if tag in SKIP_TAGS:
            self._skip_roots.append(self._depth)
            return

        if self._inside(self._skip_roots):
            return

        if tag in {"main", "article"}:
            self._main_roots.append(self._depth)

        attr_blob = " ".join(
            [
                attrs_dict.get("id", ""),
                attrs_dict.get("class", ""),
                attrs_dict.get("data-testid", ""),
                attrs_dict.get("data-automation-id", ""),
                attrs_dict.get("data-test", ""),
            ]
        )

        normalized_blob = re.sub(
            r"[^a-z0-9]+",
            "",
            attr_blob.casefold(),
        )

        if any(
            re.sub(r"[^a-z0-9]+", "", hint.casefold())
            in normalized_blob
            for hint in TARGET_ATTRIBUTE_HINTS
        ):
            self._target_roots.append(self._depth)

        if tag in BLOCK_TAGS:
            self._append_break()

    def handle_endtag(self, tag):
        tag = tag.casefold()

        if (
            tag == "script"
            and self._json_ld_root is not None
        ):
            value = "".join(self._json_ld_chunks).strip()
            if value:
                self.json_ld_blocks.append(value)
            self._json_ld_chunks = []
            self._json_ld_root = None
            self._depth = max(0, self._depth - 1)
            return

        if (
            tag == "script"
            and self._json_root is not None
        ):
            value = "".join(self._json_chunks).strip()
            if value:
                self.json_blocks.append(value)
            self._json_chunks = []
            self._json_root = None
            self._depth = max(0, self._depth - 1)
            return

        if self._inside(self._skip_roots):
            if self._skip_roots[-1] == self._depth:
                self._skip_roots.pop()
            self._depth = max(0, self._depth - 1)
            return

        if tag in BLOCK_TAGS:
            self._append_break()

        self._target_roots = [
            root
            for root in self._target_roots
            if root != self._depth
        ]
        self._main_roots = [
            root
            for root in self._main_roots
            if root != self._depth
        ]

        self._depth = max(0, self._depth - 1)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if self._json_ld_root is not None:
            self._json_ld_chunks.append(data)
            return

        if self._json_root is not None:
            self._json_chunks.append(data)
            return

        if self._inside(self._skip_roots):
            return

        cleaned = re.sub(r"\s+", " ", data or "").strip()
        if not cleaned:
            return

        if self._inside(self._target_roots):
            self.target_chunks.append(cleaned)

        if self._inside(self._main_roots):
            self.main_chunks.append(cleaned)

    def _append_break(self):
        if self._inside(self._target_roots):
            self.target_chunks.append("\n")
        if self._inside(self._main_roots):
            self.main_chunks.append("\n")


def _clean_text(value):
    if value is None:
        return ""

    value = html.unescape(str(value))
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"</(?:p|div|li|h[1-6]|section|article)>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s*\n+", "\n\n", value)
    return value.strip()


def _dedupe_lines(value):
    seen = set()
    output = []

    for raw_line in str(value or "").splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            if output and output[-1] != "":
                output.append("")
            continue

        key = line.casefold()
        if key in seen:
            continue

        seen.add(key)
        output.append(line)

    while output and output[-1] == "":
        output.pop()

    return "\n".join(output).strip()


def _extract_jobposting_objects(value):
    found = []

    if isinstance(value, list):
        for item in value:
            found.extend(_extract_jobposting_objects(item))
        return found

    if not isinstance(value, dict):
        return found

    type_value = value.get("@type")
    if isinstance(type_value, list):
        type_names = {str(item).casefold() for item in type_value}
    else:
        type_names = {str(type_value or "").casefold()}

    if "jobposting" in type_names:
        found.append(value)

    for key in ("@graph", "mainEntity", "itemListElement"):
        child = value.get(key)
        if child is not None:
            found.extend(_extract_jobposting_objects(child))

    return found


def _jsonld_job_text(parser):
    candidates = []

    for raw_block in parser.json_ld_blocks:
        try:
            parsed = json.loads(raw_block)
        except (json.JSONDecodeError, TypeError):
            continue

        for jobposting in _extract_jobposting_objects(parsed):
            parts = []

            description = _clean_text(jobposting.get("description"))
            if description:
                parts.append(description)

            field_map = [
                ("Qualifications", "qualifications"),
                ("Responsibilities", "responsibilities"),
                ("Skills", "skills"),
                ("Experience requirements", "experienceRequirements"),
                ("Education requirements", "educationRequirements"),
            ]

            normalized_description = description.casefold()

            for heading, key in field_map:
                field_value = _clean_text(jobposting.get(key))
                if not field_value:
                    continue

                if (
                    normalized_description
                    and field_value.casefold() in normalized_description
                ):
                    continue

                parts.append(f"{heading}\n{field_value}")

            merged = _dedupe_lines("\n\n".join(parts))
            if merged:
                candidates.append(merged)

    if not candidates:
        return ""

    return max(candidates, key=len)


def _flatten_hydration_text(value, path=()):
    """Recover job-description fields from application state JSON.

    Modern ATS pages often render a short shell first and hydrate the full job
    description from JSON embedded in the HTML. This walker deliberately only
    keeps values under job-description-like keys so navigation/app state does
    not become part of the analysis text.
    """

    found = []

    if isinstance(value, list):
        for item in value:
            found.extend(_flatten_hydration_text(item, path))
        return found

    if not isinstance(value, dict):
        return found

    for raw_key, child in value.items():
        key = re.sub(r"[^a-z0-9]+", "", str(raw_key).casefold())
        child_path = (*path, key)

        if isinstance(child, str) and key in HYDRATION_KEY_HINTS:
            cleaned = _clean_text(child)
            if len(cleaned) >= 80:
                found.append((child_path, cleaned))

        elif isinstance(child, (dict, list)):
            found.extend(_flatten_hydration_text(child, child_path))

    return found


def _hydration_job_text(parser):
    candidates = []

    for raw_block in parser.json_blocks:
        try:
            parsed = json.loads(raw_block)
        except (json.JSONDecodeError, TypeError):
            continue

        pieces = _flatten_hydration_text(parsed)
        if not pieces:
            continue

        # Prefer larger job-description values, then supplement with distinct
        # requirements/responsibilities found in the same state payload.
        pieces.sort(key=lambda item: len(item[1]), reverse=True)
        selected = []
        normalized = ""

        for _, text_value in pieces:
            folded = text_value.casefold()
            if normalized and folded in normalized:
                continue
            if selected and normalized in folded:
                selected = [text_value]
                normalized = folded
                continue
            selected.append(text_value)
            normalized = "\n\n".join(selected).casefold()

        merged = _dedupe_lines("\n\n".join(selected))
        if merged:
            candidates.append(merged)

    return max(candidates, key=len) if candidates else ""


def _detect_ats(url):
    host = (urlparse(url).hostname or "").casefold()

    for ats_name, hints in ATS_HOST_HINTS.items():
        if any(hint in host for hint in hints):
            return ats_name

    return None


def _fetch_json(url, *, method="GET", payload=None):
    if not _is_safe_url(url):
        raise ValueError("Unsafe or unreachable ATS API URL")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; CareerLens/1.0; "
            "+https://github.com/yannischong/CareerLens)"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    with httpx.Client(
        timeout=FETCH_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers=headers,
    ) as client:
        if method == "POST":
            response = client.post(url, json=payload or {})
        else:
            response = client.get(url)

        response.raise_for_status()

        if len(response.content) > MAX_RESPONSE_BYTES:
            raise ValueError("ATS response exceeded size limit")

        return response.json()


def _greenhouse_adapter(url):
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    query = {}
    for pair in (parsed.query or "").split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            query[key] = value

    job_id = query.get("gh_jid")
    board = None

    if "jobs" in parts:
        idx = parts.index("jobs")
        if idx > 0:
            board = parts[idx - 1]
        if not job_id and idx + 1 < len(parts):
            if parts[idx + 1].isdigit():
                job_id = parts[idx + 1]

    # New Greenhouse URLs are /{board}/jobs/{id}; old ones follow the same
    # board token convention on boards.greenhouse.io.
    if not board and len(parts) >= 1:
        board = parts[0]

    if not board or not job_id:
        return None

    api_url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        f"{board}/jobs/{job_id}?content=true"
    )
    data = _fetch_json(api_url)
    content = _clean_text(data.get("content"))

    if len(content) < 200:
        return None

    return "ats_greenhouse", content, api_url


def _lever_adapter(url):
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]

    if len(parts) < 2:
        return None

    site, posting_id = parts[0], parts[1]
    api_url = f"https://api.lever.co/v0/postings/{site}/{posting_id}"
    data = _fetch_json(api_url)
    parts_out = []

    description = _clean_text(
        data.get("descriptionPlain")
        or data.get("description")
    )
    if description:
        parts_out.append(description)

    for item in data.get("lists") or []:
        if not isinstance(item, dict):
            continue
        heading = _clean_text(item.get("text"))
        content = _clean_text(item.get("content"))
        if content:
            parts_out.append(
                f"{heading}\n{content}" if heading else content
            )

    additional = _clean_text(
        data.get("additionalPlain")
        or data.get("additional")
    )
    if additional:
        parts_out.append(additional)

    merged = _dedupe_lines("\n\n".join(parts_out))
    if len(merged) < 200:
        return None

    return "ats_lever", merged, api_url


def _smartrecruiters_adapter(url):
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]

    if len(parts) < 2:
        return None

    company, posting_id = parts[0], parts[1]
    api_url = (
        "https://api.smartrecruiters.com/v1/companies/"
        f"{company}/postings/{posting_id}"
    )
    data = _fetch_json(api_url)
    sections = ((data.get("jobAd") or {}).get("sections") or {})
    parts_out = []

    for key in (
        "jobDescription",
        "qualifications",
        "responsibilities",
        "additionalInformation",
    ):
        section = sections.get(key) or {}
        if isinstance(section, dict):
            title = _clean_text(section.get("title"))
            body = _clean_text(section.get("text"))
        else:
            title = ""
            body = _clean_text(section)

        if body:
            parts_out.append(f"{title}\n{body}" if title else body)

    merged = _dedupe_lines("\n\n".join(parts_out))
    if len(merged) < 200:
        return None

    return "ats_smartrecruiters", merged, api_url


def _workday_adapter(url):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    tenant = host.split(".")[0]
    parts = [part for part in parsed.path.split("/") if part]

    if "job" not in parts:
        return None

    job_index = parts.index("job")
    if job_index < 1 or job_index + 1 >= len(parts):
        return None

    site = parts[job_index - 1]
    # Locale is often the first path segment, followed by the site name.
    if re.fullmatch(r"[a-z]{2}(?:-[A-Z]{2})?", site):
        return None

    job_tail = "/".join(parts[job_index + 1:])
    api_url = (
        f"{parsed.scheme}://{host}/wday/cxs/"
        f"{tenant}/{site}/job/{job_tail}"
    )
    data = _fetch_json(api_url)

    posting = data.get("jobPostingInfo") or data
    parts_out = []
    for key in (
        "jobDescription",
        "additionalJobDescription",
        "qualifications",
        "responsibilities",
    ):
        value = _clean_text(posting.get(key)) if isinstance(posting, dict) else ""
        if value:
            parts_out.append(value)

    if not parts_out:
        pieces = _flatten_hydration_text(posting)
        parts_out = [item[1] for item in pieces]

    merged = _dedupe_lines("\n\n".join(parts_out))
    if len(merged) < 200:
        return None

    return "ats_workday", merged, api_url


def _ashby_adapter(url):
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]

    if len(parts) < 2:
        return None

    board, posting_id = parts[0], parts[1]
    api_url = f"https://api.ashbyhq.com/posting-api/job-board/{board}"
    data = _fetch_json(api_url)

    jobs = data.get("jobs") or []
    selected = None
    for job in jobs:
        if not isinstance(job, dict):
            continue

        identifiers = {
            str(job.get("id") or ""),
            str(job.get("jobId") or ""),
        }
        job_url = str(job.get("jobUrl") or "")

        if posting_id in identifiers or posting_id in job_url:
            selected = job
            break

    if selected is None:
        return None

    parts_out = []
    for key in (
        "descriptionPlain",
        "descriptionHtml",
        "description",
    ):
        value = _clean_text(selected.get(key))
        if value:
            parts_out.append(value)

    merged = _dedupe_lines("\n\n".join(parts_out))
    if len(merged) < 200:
        return None

    return "ats_ashby", merged, api_url


def _fetch_ats_posting(url):
    ats = _detect_ats(url)
    if not ats:
        return None

    adapters = {
        "greenhouse": _greenhouse_adapter,
        "lever": _lever_adapter,
        "smartrecruiters": _smartrecruiters_adapter,
        "workday": _workday_adapter,
        "ashby": _ashby_adapter,
    }

    adapter = adapters.get(ats)
    if adapter is None:
        return None

    try:
        return adapter(url)
    except Exception:
        return None


def _joined_chunks(chunks):
    value = " ".join(chunks)
    value = value.replace(" \n ", "\n")
    value = value.replace(" \n", "\n").replace("\n ", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s*\n+", "\n\n", value)
    return _dedupe_lines(value)


def _is_safe_url(url):
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    hostname = (parsed.hostname or "").strip().casefold()
    if not hostname:
        return False

    if hostname in BLOCKED_HOST_SUFFIXES or hostname.endswith(".localhost"):
        return False

    try:
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        return False

    if not addresses:
        return False

    for address in addresses:
        raw_ip = address[4][0]
        try:
            ip = ipaddress.ip_address(raw_ip)
        except ValueError:
            return False

        if not ip.is_global:
            return False

    return True


def _fetch_html(url):
    current_url = url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; CareerLens/1.0; "
            "+https://github.com/yannischong/CareerLens)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    with httpx.Client(
        timeout=FETCH_TIMEOUT_SECONDS,
        follow_redirects=False,
        headers=headers,
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            if not _is_safe_url(current_url):
                raise ValueError("Unsafe or unreachable job posting URL")

            with client.stream("GET", current_url) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Redirect response had no destination")
                    current_url = urljoin(current_url, location)
                    continue

                response.raise_for_status()

                content_type = response.headers.get("content-type", "").casefold()
                if not any(
                    allowed in content_type
                    for allowed in ("text/html", "application/xhtml+xml", "text/plain")
                ):
                    raise ValueError("Job posting did not return HTML/text")

                chunks = []
                total = 0

                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > MAX_RESPONSE_BYTES:
                        break
                    chunks.append(chunk)

                raw = b"".join(chunks)
                encoding = response.encoding or "utf-8"
                return raw.decode(encoding, errors="replace"), str(response.url)

    raise ValueError("Too many redirects while fetching job posting")


def _candidate_urls(job):
    urls = []

    def add(value):
        value = str(value or "").strip()
        if value and value not in urls:
            urls.append(value)

    metadata = job.get("source_metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    for option in metadata.get("apply_options") or []:
        if isinstance(option, dict):
            add(option.get("link"))

    add(job.get("job_url"))
    add(metadata.get("share_link"))

    def score(url):
        host = (urlparse(url).hostname or "").casefold()
        aggregator = any(hint in host for hint in AGGREGATOR_HOST_HINTS)
        return (1 if aggregator else 0, len(url))

    return sorted(urls, key=score)


def _select_page_text(html_text, provider_text):
    parser = _PostingHTMLParser()

    try:
        parser.feed(html_text)
    except Exception:
        pass

    jsonld_text = _jsonld_job_text(parser)
    hydration_text = _hydration_job_text(parser)
    target_text = _joined_chunks(parser.target_chunks)
    main_text = _joined_chunks(parser.main_chunks)

    provider_length = len(provider_text or "")
    candidates = []

    if jsonld_text:
        candidates.append(("employer_jsonld", jsonld_text, 4))

    if hydration_text:
        candidates.append(("employer_hydration", hydration_text, 3))

    if target_text:
        candidates.append(("employer_html", target_text, 2))

    # <main>/<article> is a weaker fallback. Only use it when it is materially
    # richer than the provider text and not implausibly huge.
    if (
        main_text
        and len(main_text) <= 120_000
        and len(main_text) >= max(900, int(provider_length * 1.35))
    ):
        candidates.append(("employer_main_html", main_text, 1))

    if not candidates:
        return None

    # Prefer structured data, then targeted HTML, while still requiring enough
    # content to plausibly improve on the provider snippet.
    candidates.sort(key=lambda item: (item[2], len(item[1])), reverse=True)

    for source, text_value, _ in candidates:
        if len(text_value) >= max(500, int(provider_length * 1.10)):
            return source, text_value

    return None


def _merge_provider_supplements(full_text, job):
    parts = [full_text]
    normalized = full_text.casefold()

    for heading, key in (
        ("Requirements", "requirements_text"),
        ("Education requirements", "education_requirements"),
        ("Experience requirements", "experience_requirements"),
    ):
        value = str(job.get(key) or "").strip()
        if not value:
            continue
        if value.casefold() in normalized:
            continue
        parts.append(f"{heading}\n{value}")

    return _dedupe_lines("\n\n".join(parts))


def enrich_provider_job_description(job, provider_text):
    """Return the richest safe job description available for one provider job.

    Network/page extraction failures are intentionally non-fatal. Callers always
    receive the provider text as a fallback.
    """

    provider_text = str(provider_text or "").strip()
    metadata = job.get("source_metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    description_type = str(metadata.get("description_type") or "").casefold()

    base_completeness = (
        "partial"
        if description_type == "snippet" or len(provider_text) < 700
        else "likely_full"
    )

    result = {
        "analysis_text": provider_text,
        "description_source": "provider",
        "description_completeness": base_completeness,
        "source_url": None,
        "provider_characters": len(provider_text),
        "analysis_characters": len(provider_text),
        "full_posting_retrieved": False,
        "fetch_attempted": False,
    }

    for url in _candidate_urls(job):
        result["fetch_attempted"] = True

        # Phase 4B: for common ATS platforms, call the public job-data
        # endpoint that powers the rendered page. This retrieves descriptions
        # that may not exist in the initial HTML at all.
        ats_result = _fetch_ats_posting(url)
        if ats_result is not None:
            source, page_text, final_url = ats_result
            enriched_text = _merge_provider_supplements(page_text, job)

            if len(enriched_text) > len(provider_text):
                result.update(
                    {
                        "analysis_text": enriched_text,
                        "description_source": source,
                        "description_completeness": "full",
                        "source_url": final_url,
                        "analysis_characters": len(enriched_text),
                        "full_posting_retrieved": True,
                    }
                )
                return result

        try:
            html_text, final_url = _fetch_html(url)
            selected = _select_page_text(html_text, provider_text)
        except Exception:
            continue

        if selected is None:
            continue

        source, page_text = selected
        enriched_text = _merge_provider_supplements(page_text, job)

        if len(enriched_text) <= len(provider_text):
            continue

        ratio = (
            len(enriched_text) / max(len(provider_text), 1)
        )

        if (
            source in {"employer_jsonld", "employer_hydration"}
            and len(enriched_text) >= 800
        ):
            completeness = "full"
        elif len(enriched_text) >= 1200 or ratio >= 1.5:
            completeness = "likely_full"
        else:
            completeness = "partial"

        result.update(
            {
                "analysis_text": enriched_text,
                "description_source": source,
                "description_completeness": completeness,
                "source_url": final_url,
                "analysis_characters": len(enriched_text),
                "full_posting_retrieved": completeness in {"full", "likely_full"},
            }
        )

        return result

    return result
