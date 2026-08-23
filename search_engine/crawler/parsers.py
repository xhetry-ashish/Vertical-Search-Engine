"""HTML parsers for Pure Portal publication and author metadata."""

from __future__ import annotations

import re
from collections import OrderedDict
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup, Tag

from search_engine.models import Author, Publication


PUBLICATION_PATH_PREFIX = "/en/publications/"
PERSON_PATH_PREFIX = "/en/persons/"


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def clean_url(url: str) -> str:
    return url.split("#", 1)[0]


def canonical_content_url(url: str) -> str:
    parsed = urlparse(clean_url(url))
    path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def is_publication_url(url: str) -> bool:
    path = urlparse(url).path.rstrip("/")
    return path.startswith(PUBLICATION_PATH_PREFIX.rstrip("/") + "/")


def is_person_url(url: str) -> bool:
    path = urlparse(url).path.rstrip("/")
    return path.startswith(PERSON_PATH_PREFIX.rstrip("/") + "/")


def normalize_author_name_for_match(name: str) -> str:
    value = name.lower().replace("-", " ")
    value = re.sub(r"[^a-z\s,]", " ", value)
    return clean_text(value)


def author_signature(name: str) -> tuple[str, set[str]]:
    normalized = normalize_author_name_for_match(name)
    if "," in normalized:
        surname, given = normalized.split(",", 1)
        initials = {part[0] for part in given.split() if part}
        return clean_text(surname), initials

    parts = normalized.split()
    if not parts:
        return "", set()

    surname = parts[-1]
    initials = {part[0] for part in parts[:-1] if part}
    return surname, initials


def author_names_match(first: str, second: str) -> bool:
    first_surname, first_initials = author_signature(first)
    second_surname, second_initials = author_signature(second)
    surname_matches = (
        first_surname == second_surname
        or first_surname.endswith(f" {second_surname}")
        or second_surname.endswith(f" {first_surname}")
    )
    if not first_surname or not second_surname or not surname_matches:
        return False
    if not first_initials or not second_initials:
        return normalize_author_name_for_match(first) == normalize_author_name_for_match(second)
    return bool(first_initials & second_initials)


def author_name_quality(name: str) -> int:
    score = len(re.sub(r"[^A-Za-z]", "", name))
    if re.search(r",\s*[A-Z](?:\.|$)", name):
        score -= 20
    return score


def add_or_merge_author(authors_by_key: OrderedDict[str, Author], author: Author) -> None:
    for key, existing in list(authors_by_key.items()):
        same_profile = (
            author.profile_url is not None
            and existing.profile_url is not None
            and author.profile_url == existing.profile_url
        )
        same_name = author_names_match(existing.name, author.name)
        if not same_profile and not same_name:
            continue

        profile_url = existing.profile_url or author.profile_url
        best_name = existing.name
        if author_name_quality(author.name) > author_name_quality(existing.name):
            best_name = author.name
        authors_by_key[key] = Author(
            name=best_name,
            profile_url=profile_url,
            affiliation=existing.affiliation or author.affiliation,
        )
        return

    authors_by_key[author.author_key] = author


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def visible_text(soup: BeautifulSoup | Tag) -> str:
    clone = BeautifulSoup(str(soup), "html.parser")
    for tag in clone(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return clean_text(clone.get_text(" "))


def meta_values(soup: BeautifulSoup, names: list[str]) -> list[str]:
    values = []
    for name in names:
        for tag in soup.find_all("meta"):
            key = tag.get("name") or tag.get("property")
            if key != name:
                continue
            value = clean_text(tag.get("content"))
            if value:
                values.append(value)
    return values


def first_meta_value(soup: BeautifulSoup, names: list[str]) -> str | None:
    values = meta_values(soup, names)
    return values[0] if values else None


def extract_year(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if not match:
        return None
    return int(match.group(0))


def find_result_container(link: Tag) -> Tag:
    for parent in link.parents:
        if not isinstance(parent, Tag):
            continue
        if parent.name in {"li", "article"}:
            return parent
        classes = " ".join(parent.get("class", []))
        if any(word in classes.lower() for word in ["result", "portal_list_item", "rendering"]):
            return parent
    return link.parent if isinstance(link.parent, Tag) else link


def extract_publication_urls(html: str, base_url: str) -> list[str]:
    soup = make_soup(html)
    urls = OrderedDict()

    for link in soup.find_all("a", href=True):
        absolute_url = canonical_content_url(urljoin(base_url, link["href"]))
        if is_publication_url(absolute_url):
            urls[absolute_url] = None

    return list(urls.keys())


def extract_person_urls(html: str, base_url: str) -> list[str]:
    soup = make_soup(html)
    urls = OrderedDict()

    for link in soup.find_all("a", href=True):
        absolute_url = canonical_content_url(urljoin(base_url, link["href"]))
        if is_person_url(absolute_url):
            urls[absolute_url] = None

    return list(urls.keys())


def extract_listing_urls(html: str, base_url: str, organisation_path: str) -> list[str]:
    soup = make_soup(html)
    urls = OrderedDict()

    for link in soup.find_all("a", href=True):
        absolute_url = clean_url(urljoin(base_url, link["href"]))
        parsed = urlparse(absolute_url)
        if parsed.path.startswith(organisation_path) and "/publications" in parsed.path:
            if parsed.query and not parsed.query.startswith("page="):
                continue
            urls[absolute_url] = None

    return list(urls.keys())


def parse_authors(soup_or_tag: BeautifulSoup | Tag, base_url: str) -> list[Author]:
    authors_by_key: OrderedDict[str, Author] = OrderedDict()

    for link in soup_or_tag.find_all("a", href=True):
        absolute_url = canonical_content_url(urljoin(base_url, link["href"]))
        if not is_person_url(absolute_url):
            continue

        name = clean_text(link.get_text(" "))
        if not name or name.lower().startswith("image") or name.lower() in {"profiles", "persons"}:
            continue

        author = Author(name=name, profile_url=absolute_url)
        add_or_merge_author(authors_by_key, author)

    if isinstance(soup_or_tag, BeautifulSoup):
        for author_name in meta_values(soup_or_tag, ["citation_author"]):
            author = Author(name=author_name)
            add_or_merge_author(authors_by_key, author)

    return list(authors_by_key.values())


def extract_publication_type(text: str) -> str | None:
    match = re.search(r"Research output:\s*(.+?)(?:\s+Open Access|\s+File|\s+\d+\s+Downloads|$)", text)
    if not match:
        return None
    return clean_text(match.group(1))


def extract_abstract(soup: BeautifulSoup) -> str | None:
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        heading_text = clean_text(heading.get_text(" ")).lower()
        if heading_text != "abstract":
            continue

        parts = []
        for sibling in heading.find_next_siblings():
            if isinstance(sibling, Tag) and re.match(r"^h[1-6]$", sibling.name or ""):
                break
            text = clean_text(sibling.get_text(" ")) if isinstance(sibling, Tag) else clean_text(str(sibling))
            if text:
                parts.append(text)
        abstract = clean_text(" ".join(parts))
        return abstract or None
    return None


def parse_publication_summaries(html: str, base_url: str) -> list[Publication]:
    soup = make_soup(html)
    publications_by_url: OrderedDict[str, Publication] = OrderedDict()

    for link in soup.find_all("a", href=True):
        publication_url = canonical_content_url(urljoin(base_url, link["href"]))
        if not is_publication_url(publication_url):
            continue

        title = clean_text(link.get_text(" "))
        if not title:
            continue

        container = find_result_container(link)
        text = visible_text(container)
        authors = parse_authors(container, base_url)

        publications_by_url[publication_url] = Publication(
            title=title,
            publication_url=publication_url,
            authors=authors,
            publication_year=extract_year(text),
            published_date=None,
            source=None,
            publication_type=extract_publication_type(text),
            abstract=None,
            full_text=text,
            crawled_from=base_url,
        )

    return list(publications_by_url.values())


def parse_publication_page(html: str, url: str) -> Publication:
    soup = make_soup(html)

    title = first_meta_value(soup, ["citation_title", "og:title"])
    if not title:
        heading = soup.find("h1")
        title = clean_text(heading.get_text(" ")) if heading else ""

    if not title and soup.title:
        title = clean_text(soup.title.get_text(" "))

    full_text = visible_text(soup)
    published_date = first_meta_value(
        soup,
        ["citation_publication_date", "citation_date", "article:published_time"],
    )
    source = first_meta_value(
        soup,
        ["citation_journal_title", "citation_conference_title", "citation_publisher"],
    )

    return Publication(
        title=title,
        publication_url=canonical_content_url(url),
        authors=parse_authors(soup, url),
        publication_year=extract_year(published_date) or extract_year(full_text),
        published_date=published_date,
        source=source,
        publication_type=extract_publication_type(full_text),
        abstract=extract_abstract(soup),
        full_text=full_text,
        crawled_from=url,
    )


def merge_publication_data(summary: Publication, detail: Publication) -> Publication:
    authors_by_key: OrderedDict[str, Author] = OrderedDict()
    for author in summary.authors + detail.authors:
        authors_by_key.setdefault(author.author_key, author)

    return Publication(
        title=detail.title or summary.title,
        publication_url=detail.publication_url or summary.publication_url,
        authors=list(authors_by_key.values()),
        publication_year=detail.publication_year or summary.publication_year,
        published_date=detail.published_date or summary.published_date,
        source=detail.source or summary.source,
        publication_type=detail.publication_type or summary.publication_type,
        abstract=detail.abstract or summary.abstract,
        full_text=detail.full_text or summary.full_text,
        crawled_from=summary.crawled_from,
        crawled_at=detail.crawled_at,
    )
