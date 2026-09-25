import html
import ipaddress
import json
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx


from src.services.original_job_source_resolver import (
    cached_original_source,
    discover_outbound_source_urls,
    host_for_url,
    is_aggregator_url,
    search_official_job_candidates,
)


FETCH_TIMEOUT_SECONDS = 8.0
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
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
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
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Referer": "https://www.google.com/",
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


def _metadata_dict(job):
    metadata = job.get("source_metadata") or {}

    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    return metadata if isinstance(metadata, dict) else {}


def _provider_structured_text(job, provider_text):
    """Merge structured provider fields that are richer than the visible card.

    SerpAPI can return job_highlights / qualifications / responsibilities even
    when the main description is shortened. These fields should be analysed
    before we conclude that the provider only supplied a snippet.
    """

    metadata = _metadata_dict(job)
    parts = [str(provider_text or "").strip()]

    def add(value, heading=None):
        cleaned = _clean_text(value)
        if not cleaned:
            return

        current = "\n\n".join(parts).casefold()
        if cleaned.casefold() in current:
            return

        parts.append(
            f"{heading}\n{cleaned}"
            if heading
            else cleaned
        )

    for key, heading in (
        ("description", None),
        ("job_description", "Job description"),
        ("jobDescription", "Job description"),
        ("description_text", "Job description"),
        ("descriptionText", "Job description"),
        ("qualifications", "Qualifications"),
        ("requirements", "Requirements"),
        ("responsibilities", "Responsibilities"),
        ("skills", "Skills"),
    ):
        add(metadata.get(key), heading)

    for highlights_key in ("job_highlights", "highlights"):
        highlights = metadata.get(highlights_key) or []
        if not isinstance(highlights, list):
            continue

        for block in highlights:
            if not isinstance(block, dict):
                continue

            title = _clean_text(
                block.get("title")
                or block.get("heading")
            )
            items = block.get("items") or block.get("content") or []

            if isinstance(items, list):
                body = "\n".join(
                    _clean_text(item)
                    for item in items
                    if _clean_text(item)
                )
            else:
                body = _clean_text(items)

            add(body, title or "Job details")

    # Some providers retain the raw result under a nested key. Reuse the same
    # hydration walker we use for embedded application state to recover long
    # description-like values without pulling in unrelated metadata.
    for _, value in _flatten_hydration_text(metadata):
        add(value)

    return _dedupe_lines("\n\n".join(part for part in parts if part))


def _iter_metadata_urls(value, parent_key=""):
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = re.sub(
                r"[^a-z0-9]+",
                "",
                str(key).casefold(),
            )
            yield from _iter_metadata_urls(child, normalized_key)
        return

    if isinstance(value, list):
        for child in value:
            yield from _iter_metadata_urls(child, parent_key)
        return

    if not isinstance(value, str):
        return

    candidate = html.unescape(value).strip().replace("\\/", "/")
    if not candidate.startswith(("http://", "https://")):
        return

    # Only treat URL-like/apply-like metadata as navigation candidates. This
    # avoids wasting requests on thumbnails, logos and unrelated resources.
    if parent_key and not any(
        hint in parent_key
        for hint in (
            "url",
            "link",
            "apply",
            "posting",
            "career",
            "job",
        )
    ):
        return

    yield candidate


def _candidate_urls(job):
    urls = []

    def add(value):
        value = str(value or "").strip()
        if not value or value in urls:
            return

        lowered = value.casefold().split("?", 1)[0]
        if lowered.endswith(
            (
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".svg",
                ".webp",
                ".ico",
                ".pdf",
            )
        ):
            return

        urls.append(value)

    metadata = _metadata_dict(job)

    resolved = cached_original_source(job)
    if resolved is not None:
        add(resolved.get("url"))

    for option in metadata.get("apply_options") or []:
        if isinstance(option, dict):
            add(option.get("link"))
            add(option.get("url"))

    for value in _iter_metadata_urls(metadata):
        add(value)

    add(job.get("job_url"))
    add(metadata.get("share_link"))

    def score(url):
        host = (urlparse(url).hostname or "").casefold()
        ats = _detect_ats(url) is not None
        aggregator = any(hint in host for hint in AGGREGATOR_HOST_HINTS)
        return (
            0 if ats else 1 if not aggregator else 2,
            len(url),
        )

    return sorted(urls, key=score)[:12]


def _discover_page_urls(html_text, base_url):
    """Find likely employer/ATS destinations exposed by aggregator pages.

    Phase 4C also unwraps Jooble/tracking URLs and recognises data-href,
    form-action and JavaScript-embedded destinations.
    """

    discovered = []

    def add(raw_url, context=""):
        if not raw_url:
            return

        value = html.unescape(str(raw_url)).replace("\\/", "/").strip()
        if value.startswith(("mailto:", "javascript:", "tel:", "#")):
            return

        value = urljoin(base_url, value)
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return

        if value == base_url:
            return

        lowered = value.casefold().split("?", 1)[0]
        if lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")):
            return

        key = (value, context.casefold())
        if key not in discovered:
            discovered.append(key)

    anchor_pattern = re.compile(
        r"<a\b[^>]*?href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL,
    )
    for match in anchor_pattern.finditer(html_text or ""):
        label = re.sub(r"<[^>]+>", " ", match.group(2) or "")
        add(match.group(1), label)

    for match in re.finditer(
        r"<link\b[^>]*?href=[\"']([^\"']+)[\"'][^>]*>",
        html_text or "",
        re.IGNORECASE,
    ):
        tag = match.group(0).casefold()
        if "canonical" in tag:
            add(match.group(1), "canonical")

    for match in re.finditer(
        r"https?:\\?/\\?/[^\"'<>\s]+",
        html_text or "",
        re.IGNORECASE,
    ):
        raw = match.group(0).replace("\\/", "/")
        if _detect_ats(raw):
            add(raw, "ats embedded url")

    # Dedicated resolver catches encoded Jooble redirect targets, data-href
    # attributes and other application links that the generic parser misses.
    for item in discover_outbound_source_urls(html_text or "", base_url):
        add(item.get("url"), "jooble outbound apply link")

    def score(item):
        url, context = item
        host = (urlparse(url).hostname or "").casefold()
        ats = _detect_ats(url) is not None
        aggregator = any(hint in host for hint in AGGREGATOR_HOST_HINTS)
        applyish = any(
            token in context
            for token in (
                "apply",
                "view job",
                "view original",
                "job posting",
                "career",
                "position",
                "company website",
            )
        )
        return (
            0 if ats else 1 if applyish and not aggregator else 2 if not aggregator else 3,
            len(url),
        )

    return [url for url, _ in sorted(discovered, key=score)[:12]]


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

    Original-source resolution order:
    1. Reuse a previously resolved employer/ATS URL from source_metadata.
    2. Merge structured provider fields.
    3. Try provider-supplied external/ATS links.
    4. For Jooble, unwrap outbound Apply/View-original destinations.
    5. If Jooble exposes no usable destination, run one exact SerpAPI web
       lookup for title + company + location and validate the resulting page.
    6. Fall back to provider data without failing the analysis request.
    """

    original_provider_text = str(provider_text or "").strip()
    provider_text = _provider_structured_text(job, original_provider_text)
    metadata = _metadata_dict(job)
    description_type = str(metadata.get("description_type") or "").casefold()

    has_structured_sections = any(
        metadata.get(key)
        for key in (
            "job_highlights",
            "highlights",
            "qualifications",
            "requirements",
            "responsibilities",
        )
    )

    if len(provider_text) >= 1200 and has_structured_sections:
        base_completeness = "likely_full"
        base_source = "provider_structured"
    elif description_type == "snippet" or len(provider_text) < 700:
        base_completeness = "partial"
        base_source = (
            "provider_structured"
            if provider_text != original_provider_text
            else "provider"
        )
    else:
        base_completeness = "likely_full"
        base_source = (
            "provider_structured"
            if provider_text != original_provider_text
            else "provider"
        )

    result = {
        "analysis_text": provider_text,
        "description_source": base_source,
        "description_completeness": base_completeness,
        "source_url": None,
        "original_source_url": None,
        "original_source_host": None,
        "source_resolution_method": None,
        "source_resolution_confidence": None,
        "provider_characters": len(provider_text),
        "analysis_characters": len(provider_text),
        "full_posting_retrieved": False,
        "fetch_attempted": False,
        "official_source_search_attempted": False,
    }

    attempted = set()
    source_search_candidates = 0

    title_tokens = {
        token
        for token in re.findall(
            r"[a-z0-9]+",
            str(job.get("raw_title") or "").casefold(),
        )
        if len(token) >= 2
        and token not in {"the", "and", "for", "with", "job", "role"}
    }

    company_tokens = {
        token
        for token in re.findall(
            r"[a-z0-9]+",
            str(job.get("raw_company_name") or "").casefold(),
        )
        if len(token) >= 2
        and token not in {"pte", "ltd", "limited", "inc", "the", "and"}
    }

    def identity_match(page_text, final_url):
        """Strict enough to avoid analysing a similarly named different job."""

        evidence = (
            str(page_text or "")
            + " "
            + host_for_url(final_url).replace(".", " ")
        ).casefold()
        evidence_tokens = set(re.findall(r"[a-z0-9]+", evidence))

        title_score = (
            len(title_tokens & evidence_tokens) / len(title_tokens)
            if title_tokens
            else 0.0
        )
        company_score = (
            len(company_tokens & evidence_tokens) / len(company_tokens)
            if company_tokens
            else 0.0
        )

        title_text = re.sub(
            r"\s+",
            " ",
            str(job.get("raw_title") or "").casefold(),
        ).strip()
        exact_title = bool(title_text) and title_text in re.sub(r"\s+", " ", evidence)

        return (
            (exact_title or title_score >= 0.55)
            and (
                company_score >= 0.34
                or _detect_ats(final_url) is not None
            )
        )

    def apply_text(
        source,
        page_text,
        final_url,
        *,
        force_full=False,
        resolution_method=None,
        resolution_confidence=None,
        require_identity=False,
    ):
        enriched_text = _merge_provider_supplements(page_text, job)

        if require_identity and not identity_match(enriched_text, final_url):
            return False

        if len(enriched_text) <= len(result["analysis_text"]):
            return False

        ratio = len(enriched_text) / max(len(provider_text), 1)

        if force_full or (
            source in {"employer_jsonld", "employer_hydration"}
            and len(enriched_text) >= 800
        ):
            completeness = "full"
        elif len(enriched_text) >= 1200 or ratio >= 1.5:
            completeness = "likely_full"
        else:
            completeness = "partial"

        final_host = host_for_url(final_url)
        is_original = bool(final_url) and not is_aggregator_url(final_url)

        result.update(
            {
                "analysis_text": enriched_text,
                "description_source": source,
                "description_completeness": completeness,
                "source_url": final_url,
                "original_source_url": final_url if is_original else None,
                "original_source_host": final_host if is_original else None,
                "source_resolution_method": resolution_method,
                "source_resolution_confidence": resolution_confidence,
                "analysis_characters": len(enriched_text),
                "full_posting_retrieved": completeness in {"full", "likely_full"},
            }
        )
        return True

    def try_one(
        url,
        *,
        allow_outbound=True,
        resolution_method=None,
        resolution_confidence=None,
        require_identity=False,
    ):
        url = str(url or "").strip()
        if not url or url in attempted:
            return False

        attempted.add(url)
        result["fetch_attempted"] = True

        try:
            ats_result = _fetch_ats_posting(url)
        except Exception:
            ats_result = None

        if ats_result is not None:
            source, page_text, final_url = ats_result
            if apply_text(
                source,
                page_text,
                final_url,
                force_full=True,
                resolution_method=resolution_method,
                resolution_confidence=resolution_confidence,
                require_identity=require_identity,
            ):
                return True

        try:
            html_text, final_url = _fetch_html(url)
        except Exception:
            return False

        if final_url and final_url != url:
            try:
                redirected_ats = _fetch_ats_posting(final_url)
            except Exception:
                redirected_ats = None

            if redirected_ats is not None:
                source, page_text, ats_url = redirected_ats
                if apply_text(
                    source,
                    page_text,
                    ats_url,
                    force_full=True,
                    resolution_method=resolution_method or "provider_redirect",
                    resolution_confidence=resolution_confidence or 0.95,
                    require_identity=require_identity,
                ):
                    return True

        selected = _select_page_text(html_text, provider_text)
        if selected is not None:
            source, page_text = selected
            if apply_text(
                source,
                page_text,
                final_url,
                resolution_method=resolution_method,
                resolution_confidence=resolution_confidence,
                require_identity=require_identity,
            ):
                return True

        if not allow_outbound:
            return False

        parent_is_jooble = "jooble" in host_for_url(final_url or url)

        outbound_candidates = discover_outbound_source_urls(
            html_text,
            final_url or url,
        )

        # Preserve generic outbound discovery too, because some employer pages
        # expose canonical/apply links in forms not specific to Jooble.
        generic_outbound = _discover_page_urls(html_text, final_url or url)
        seen_outbound = {
            item.get("url")
            for item in outbound_candidates
            if item.get("url")
        }
        for outbound in generic_outbound:
            if outbound not in seen_outbound:
                outbound_candidates.append(
                    {
                        "url": outbound,
                        "method": (
                            "jooble_outbound"
                            if parent_is_jooble
                            else "provider_outbound"
                        ),
                        "confidence": 0.90,
                    }
                )

        for outbound in outbound_candidates[:6]:
            if try_one(
                outbound.get("url"),
                allow_outbound=False,
                resolution_method=outbound.get("method") or (
                    "jooble_outbound" if parent_is_jooble else "provider_outbound"
                ),
                resolution_confidence=outbound.get("confidence") or 0.90,
                require_identity=parent_is_jooble,
            ):
                return True

        return False

    candidates = _candidate_urls(job)
    cached = cached_original_source(job)
    cached_url = cached.get("url") if cached else None

    for url in candidates:
        host = host_for_url(url)
        if cached_url and url == cached_url:
            method = "cached_original_source"
            confidence = cached.get("confidence") or 1.0
            require_identity = True
        elif "jooble" in host:
            method = "jooble_page"
            confidence = 0.80
            require_identity = False
        elif _detect_ats(url):
            method = "provider_ats_link"
            confidence = 0.98
            require_identity = False
        elif not is_aggregator_url(url):
            method = "provider_external_link"
            confidence = 0.92
            require_identity = False
        else:
            method = "provider_link"
            confidence = 0.75
            require_identity = False

        if try_one(
            url,
            resolution_method=method,
            resolution_confidence=confidence,
            require_identity=require_identity,
        ):
            break

    # Jooble's API frequently gives only its own page + a snippet. If neither
    # the API metadata nor the Jooble page exposes the original destination,
    # use one exact web lookup to locate the employer/ATS copy. This happens
    # only when the user opens that job, never while browsing search results.
    if (
        not result["full_posting_retrieved"]
        and str(job.get("source") or "").casefold() == "jooble"
    ):
        result["official_source_search_attempted"] = True
        official_candidates = search_official_job_candidates(job)
        source_search_candidates = len(official_candidates)

        for candidate in official_candidates:
            if try_one(
                candidate.get("url"),
                allow_outbound=False,
                resolution_method=candidate.get("method") or "serpapi_official_search",
                resolution_confidence=candidate.get("confidence"),
                require_identity=True,
            ):
                break

    print(
        "[CareerLens provider enrichment] "
        f"job_id={job.get('job_id')} "
        f"source={job.get('source')} "
        f"candidate_urls={len(candidates)} "
        f"attempted_urls={len(attempted)} "
        f"official_search_candidates={source_search_candidates} "
        f"resolution={result['source_resolution_method']} "
        f"original_host={result['original_source_host']} "
        f"description_source={result['description_source']} "
        f"completeness={result['description_completeness']} "
        f"chars={result['provider_characters']}->{result['analysis_characters']}",
        flush=True,
    )

    return result

