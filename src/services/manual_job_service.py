import ipaddress
import json
import logging
import re
import socket
from datetime import (
    datetime,
    timezone,
)
from html import unescape
from html.parser import HTMLParser
from urllib.parse import (
    urljoin,
    urlparse,
)

import httpx


logger = logging.getLogger(
    __name__
)


MAX_HTML_BYTES = 2_000_000
MAX_DESCRIPTION_CHARS = 60_000
REQUEST_TIMEOUT_SECONDS = 12
MAX_REDIRECTS = 5


class JobPageFetchError(Exception):
    pass


def _is_public_ip(
    value: str,
):
    address = ipaddress.ip_address(
        value
    )

    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def validate_public_url(
    url: str,
):
    cleaned = url.strip()

    parsed = urlparse(
        cleaned
    )

    if (
        parsed.scheme
        not in {
            "http",
            "https",
        }
    ):
        raise JobPageFetchError(
            "Use a valid http:// or https:// job listing URL."
        )

    if not parsed.hostname:
        raise JobPageFetchError(
            "The job listing URL does not contain a valid host."
        )

    if (
        parsed.username
        or parsed.password
    ):
        raise JobPageFetchError(
            "URLs containing embedded credentials are not allowed."
        )

    hostname = (
        parsed.hostname
        .strip()
        .lower()
        .rstrip(".")
    )

    if (
        hostname
        == "localhost"
        or hostname.endswith(
            ".localhost"
        )
        or hostname.endswith(
            ".local"
        )
    ):
        raise JobPageFetchError(
            "Local or private network URLs are not allowed."
        )

    try:
        address_info = (
            socket.getaddrinfo(
                hostname,
                parsed.port
                or (
                    443
                    if parsed.scheme
                    == "https"
                    else 80
                ),
                type=
                    socket.SOCK_STREAM,
            )
        )

    except socket.gaierror as exc:
        raise JobPageFetchError(
            "CareerCompass could not resolve that website."
        ) from exc

    resolved_addresses = {
        item[4][0]
        for item in address_info
    }

    if not resolved_addresses:
        raise JobPageFetchError(
            "CareerCompass could not resolve that website."
        )

    for address in resolved_addresses:
        try:
            if not _is_public_ip(
                address
            ):
                raise JobPageFetchError(
                    "Local or private network URLs are not allowed."
                )

        except ValueError as exc:
            raise JobPageFetchError(
                "The job listing resolved to an invalid network address."
            ) from exc

    return cleaned


def _http_get(
    url: str,
    accept: str,
):
    current_url = validate_public_url(
        url
    )

    headers = {
        "User-Agent":
            (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/153.0.0.0 "
                "Safari/537.36"
            ),

        "Accept":
            accept,

        "Accept-Language":
            "en-US,en;q=0.9",
    }

    timeout = httpx.Timeout(
        REQUEST_TIMEOUT_SECONDS
    )

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers=headers,
        ) as client:

            for _ in range(
                MAX_REDIRECTS
                + 1
            ):
                response = client.get(
                    current_url
                )

                if (
                    response.status_code
                    in {
                        301,
                        302,
                        303,
                        307,
                        308,
                    }
                ):
                    location = (
                        response.headers
                        .get(
                            "location"
                        )
                    )

                    if not location:
                        raise JobPageFetchError(
                            "The job listing redirected without a destination."
                        )

                    current_url = (
                        validate_public_url(
                            urljoin(
                                current_url,
                                location,
                            )
                        )
                    )

                    continue

                if (
                    response.status_code
                    >= 400
                ):
                    raise JobPageFetchError(
                        (
                            "The website returned "
                            f"HTTP {response.status_code}."
                        )
                    )

                content_length = (
                    response.headers
                    .get(
                        "content-length"
                    )
                )

                if content_length:
                    try:
                        if (
                            int(
                                content_length
                            )
                            > MAX_HTML_BYTES
                        ):
                            raise JobPageFetchError(
                                "That page is too large for CareerCompass to read safely."
                            )

                    except ValueError:
                        pass

                if (
                    len(
                        response.content
                    )
                    > MAX_HTML_BYTES
                ):
                    raise JobPageFetchError(
                        "That page is too large for CareerCompass to read safely."
                    )

                return (
                    current_url,
                    response,
                )

    except httpx.TimeoutException as exc:
        logger.warning(
            "Timed out opening job listing %s: %r",
            current_url,
            exc,
        )

        raise JobPageFetchError(
            "The job listing took too long to respond."
        ) from exc

    except httpx.RequestError as exc:
        logger.warning(
            "HTTP client failed opening job listing %s: %r",
            current_url,
            exc,
        )

        raise JobPageFetchError(
            "CareerCompass could not open that job listing."
        ) from exc

    raise JobPageFetchError(
        "The job listing redirected too many times."
    )


class JobPageParser(
    HTMLParser
):
    def __init__(
        self,
    ):
        super().__init__(
            convert_charrefs=True
        )

        self.title_parts = []
        self.visible_parts = []
        self.meta = {}
        self.json_ld_blocks = []

        self._in_title = False
        self._ignored_depth = 0
        self._in_json_ld = False
        self._json_ld_parts = []

    def handle_starttag(
        self,
        tag,
        attrs,
    ):
        tag = tag.lower()

        attributes = {
            key.lower():
                value
            for key, value in attrs
            if key
        }

        if (
            tag
            in {
                "script",
                "style",
                "noscript",
                "svg",
            }
        ):
            if (
                tag == "script"
                and (
                    attributes.get(
                        "type",
                        "",
                    )
                    .lower()
                    .split(";")[0]
                    .strip()
                    == "application/ld+json"
                )
            ):
                self._in_json_ld = True
                self._json_ld_parts = []

            else:
                self._ignored_depth += 1

        if tag == "title":
            self._in_title = True

        if tag == "meta":
            key = (
                attributes.get(
                    "property"
                )
                or attributes.get(
                    "name"
                )
            )

            content = (
                attributes.get(
                    "content"
                )
            )

            if (
                key
                and content
            ):
                self.meta[
                    key.lower()
                ] = (
                    content.strip()
                )

    def handle_endtag(
        self,
        tag,
    ):
        tag = tag.lower()

        if tag == "title":
            self._in_title = False

        if (
            tag == "script"
            and self._in_json_ld
        ):
            block = "".join(
                self._json_ld_parts
            ).strip()

            if block:
                self.json_ld_blocks.append(
                    block
                )

            self._in_json_ld = False
            self._json_ld_parts = []

        elif (
            tag
            in {
                "script",
                "style",
                "noscript",
                "svg",
            }
            and self._ignored_depth
            > 0
        ):
            self._ignored_depth -= 1

    def handle_data(
        self,
        data,
    ):
        if self._in_json_ld:
            self._json_ld_parts.append(
                data
            )

            return

        cleaned = re.sub(
            r"\s+",
            " ",
            data,
        ).strip()

        if not cleaned:
            return

        if self._in_title:
            self.title_parts.append(
                cleaned
            )

        if (
            self._ignored_depth
            == 0
        ):
            self.visible_parts.append(
                cleaned
            )


def _find_job_posting(
    value,
):
    if isinstance(
        value,
        dict,
    ):
        item_type = (
            value.get(
                "@type"
            )
        )

        if (
            item_type
            == "JobPosting"
            or (
                isinstance(
                    item_type,
                    list,
                )
                and "JobPosting"
                in item_type
            )
        ):
            return value

        graph = value.get(
            "@graph"
        )

        if graph:
            result = (
                _find_job_posting(
                    graph
                )
            )

            if result:
                return result

        for child in value.values():
            result = (
                _find_job_posting(
                    child
                )
            )

            if result:
                return result

    elif isinstance(
        value,
        list,
    ):
        for child in value:
            result = (
                _find_job_posting(
                    child
                )
            )

            if result:
                return result

    return None


def _extract_json_ld_job(
    blocks,
):
    for block in blocks:
        try:
            parsed = json.loads(
                block
            )

        except json.JSONDecodeError:
            continue

        job = _find_job_posting(
            parsed
        )

        if job:
            return job

    return None


def _clean_html_text(
    value,
):
    if not isinstance(
        value,
        str,
    ):
        return None

    cleaned = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    cleaned = unescape(
        cleaned
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    return (
        cleaned
        or None
    )


def _extract_company(
    job,
):
    organization = job.get(
        "hiringOrganization"
    )

    if isinstance(
        organization,
        dict,
    ):
        name = organization.get(
            "name"
        )

        if isinstance(
            name,
            str,
        ):
            return name.strip()

    return None


def _extract_location(
    job,
):
    location = job.get(
        "jobLocation"
    )

    if isinstance(
        location,
        list,
    ):
        location = (
            location[0]
            if location
            else None
        )

    if not isinstance(
        location,
        dict,
    ):
        return None

    address = location.get(
        "address"
    )

    if isinstance(
        address,
        str,
    ):
        return address.strip()

    if not isinstance(
        address,
        dict,
    ):
        return None

    parts = []

    for key in [
        "addressLocality",
        "addressRegion",
        "addressCountry",
    ]:
        value = address.get(
            key
        )

        if isinstance(
            value,
            dict,
        ):
            value = value.get(
                "name"
            )

        if (
            isinstance(
                value,
                str,
            )
            and value.strip()
        ):
            parts.append(
                value.strip()
            )

    return (
        ", ".join(
            dict.fromkeys(
                parts
            )
        )
        or None
    )


def _extract_employment_type(
    job,
):
    value = job.get(
        "employmentType"
    )

    if isinstance(
        value,
        list,
    ):
        values = [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

        return (
            ", ".join(
                values
            )
            or None
        )

    if isinstance(
        value,
        str,
    ):
        return (
            value.strip()
            or None
        )

    return None


def _parse_generic_html(
    final_url,
    html,
):
    parser = JobPageParser()

    try:
        parser.feed(
            html
        )

    except Exception as exc:
        raise JobPageFetchError(
            "CareerCompass could not read the job listing page."
        ) from exc

    json_ld_job = (
        _extract_json_ld_job(
            parser.json_ld_blocks
        )
    )

    page_title = (
        " ".join(
            parser.title_parts
        ).strip()
        or parser.meta.get(
            "og:title"
        )
        or parser.meta.get(
            "twitter:title"
        )
    )

    description = None
    title = None
    company = None
    location = None
    employment_type = None
    date_posted = None

    extraction_method = (
        "page_text"
    )

    if json_ld_job:
        extraction_method = (
            "json_ld_job_posting"
        )

        title = (
            _clean_html_text(
                json_ld_job.get(
                    "title"
                )
            )
        )

        company = (
            _extract_company(
                json_ld_job
            )
        )

        location = (
            _extract_location(
                json_ld_job
            )
        )

        employment_type = (
            _extract_employment_type(
                json_ld_job
            )
        )

        date_posted_value = (
            json_ld_job.get(
                "datePosted"
            )
        )

        if isinstance(
            date_posted_value,
            str,
        ):
            date_posted = (
                date_posted_value
                .strip()
                or None
            )

        description = (
            _clean_html_text(
                json_ld_job.get(
                    "description"
                )
            )
        )

    if not title:
        title = (
            page_title
            or "Job listing"
        )

    if not description:
        description = (
            parser.meta.get(
                "description"
            )
            or parser.meta.get(
                "og:description"
            )
        )

    if (
        not description
        or len(description)
        < 500
    ):
        visible_text = re.sub(
            r"\s+",
            " ",
            " ".join(
                parser.visible_parts
            ),
        ).strip()

        if (
            len(visible_text)
            > len(
                description
                or ""
            )
        ):
            description = (
                visible_text
            )

    description = (
        description
        or ""
    )[
        :MAX_DESCRIPTION_CHARS
    ]

    return {
        "url":
            final_url,

        "title":
            title,

        "company":
            company,

        "location":
            location,

        "employment_type":
            employment_type,

        "date_posted":
            date_posted,

        "description":
            description,

        "description_characters":
            len(
                description
            ),

        "extraction_method":
            extraction_method,

        "needs_description":
            len(
                description
            )
            < 500,
    }


def _lever_parts(
    url,
):
    parsed = urlparse(
        url
    )

    hostname = (
        parsed.hostname
        or ""
    ).lower()

    if hostname not in {
        "jobs.lever.co",
        "jobs.eu.lever.co",
    }:
        return None

    parts = [
        part
        for part in parsed.path.split(
            "/"
        )
        if part
    ]

    if len(parts) < 2:
        return None

    site = parts[0]
    posting_id = parts[1]

    if (
        not site
        or not posting_id
    ):
        return None

    api_host = (
        "api.eu.lever.co"
        if hostname
        == "jobs.eu.lever.co"
        else "api.lever.co"
    )

    return {
        "site":
            site,

        "posting_id":
            posting_id,

        "api_url":
            (
                f"https://{api_host}"
                f"/v0/postings/{site}/{posting_id}"
            ),
    }


def _lever_created_date(
    value,
):
    if not isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        return None

    try:
        return (
            datetime.fromtimestamp(
                value / 1000,
                tz=timezone.utc,
            )
            .date()
            .isoformat()
        )

    except (
        OSError,
        OverflowError,
        ValueError,
    ):
        return None


def _parse_lever_payload(
    original_url,
    payload,
):
    if not isinstance(
        payload,
        dict,
    ):
        raise JobPageFetchError(
            "Lever returned an unexpected job listing format."
        )

    categories = (
        payload.get(
            "categories"
        )
        or {}
    )

    description_parts = []

    description_plain = (
        payload.get(
            "descriptionPlain"
        )
    )

    if isinstance(
        description_plain,
        str,
    ):
        cleaned = (
            description_plain
            .strip()
        )

        if cleaned:
            description_parts.append(
                cleaned
            )

    elif isinstance(
        payload.get(
            "description"
        ),
        str,
    ):
        cleaned = (
            _clean_html_text(
                payload.get(
                    "description"
                )
            )
        )

        if cleaned:
            description_parts.append(
                cleaned
            )

    lists = (
        payload.get(
            "lists"
        )
        or []
    )

    if isinstance(
        lists,
        list,
    ):
        for item in lists:
            if not isinstance(
                item,
                dict,
            ):
                continue

            heading = (
                item.get(
                    "text"
                )
            )

            content = (
                item.get(
                    "content"
                )
            )

            if (
                isinstance(
                    heading,
                    str,
                )
                and heading.strip()
            ):
                description_parts.append(
                    heading.strip()
                )

            if isinstance(
                content,
                str,
            ):
                cleaned = (
                    _clean_html_text(
                        content
                    )
                )

                if cleaned:
                    description_parts.append(
                        cleaned
                    )

    additional_plain = (
        payload.get(
            "additionalPlain"
        )
    )

    if isinstance(
        additional_plain,
        str,
    ):
        cleaned = (
            additional_plain
            .strip()
        )

        if cleaned:
            description_parts.append(
                cleaned
            )

    elif isinstance(
        payload.get(
            "additional"
        ),
        str,
    ):
        cleaned = (
            _clean_html_text(
                payload.get(
                    "additional"
                )
            )
        )

        if cleaned:
            description_parts.append(
                cleaned
            )

    description = re.sub(
        r"\s+",
        " ",
        "\n".join(
            description_parts
        ),
    ).strip()

    description = (
        description[
            :MAX_DESCRIPTION_CHARS
        ]
    )

    title = (
        payload.get(
            "text"
        )
        or "Job listing"
    )

    if isinstance(
        title,
        str,
    ):
        title = title.strip()

    location = (
        categories.get(
            "location"
        )
        if isinstance(
            categories,
            dict,
        )
        else None
    )

    employment_type = (
        categories.get(
            "commitment"
        )
        if isinstance(
            categories,
            dict,
        )
        else None
    )

    return {
        "url":
            (
                payload.get(
                    "hostedUrl"
                )
                or original_url
            ),

        "title":
            title,

        "company":
            None,

        "location":
            location,

        "employment_type":
            employment_type,

        "date_posted":
            _lever_created_date(
                payload.get(
                    "createdAt"
                )
            ),

        "description":
            description,

        "description_characters":
            len(
                description
            ),

        "extraction_method":
            "lever_postings_api",

        "needs_description":
            len(
                description
            )
            < 500,
    }


def _fetch_lever_listing(
    url,
):
    parts = _lever_parts(
        url
    )

    if parts is None:
        return None

    final_url, response = (
        _http_get(
            parts[
                "api_url"
            ],
            "application/json",
        )
    )

    del final_url

    try:
        payload = response.json()

    except ValueError as exc:
        raise JobPageFetchError(
            "Lever returned an unreadable job listing."
        ) from exc

    return _parse_lever_payload(
        original_url=
            url,

        payload=
            payload,
    )


def fetch_job_listing(
    url: str,
):
    safe_url = validate_public_url(
        url
    )

    generic_error = None

    try:
        final_url, response = (
            _http_get(
                safe_url,
                (
                    "text/html,"
                    "application/xhtml+xml"
                ),
            )
        )

        content_type = (
            response.headers
            .get(
                "content-type",
                "",
            )
            .lower()
        )

        if (
            "text/html"
            not in content_type
            and
            "application/xhtml+xml"
            not in content_type
        ):
            raise JobPageFetchError(
                "That link did not return an HTML job listing page."
            )

        return _parse_generic_html(
            final_url=
                final_url,

            html=
                response.text,
        )

    except JobPageFetchError as exc:
        generic_error = exc

        logger.warning(
            "Generic job page fetch failed for %s: %s",
            safe_url,
            exc,
        )

    # Lever publishes a public Postings API.
    # If the hosted page itself cannot be
    # fetched, use the listing's site +
    # posting ID from the URL.
    try:
        lever_result = (
            _fetch_lever_listing(
                safe_url
            )
        )

        if lever_result is not None:
            return lever_result

    except JobPageFetchError as exc:
        logger.warning(
            "Lever API fallback failed for %s: %s",
            safe_url,
            exc,
        )

    if generic_error is not None:
        raise generic_error

    raise JobPageFetchError(
        "CareerCompass could not read that job listing."
    )
