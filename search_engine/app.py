"""Streamlit interface for viewing crawled Pure Portal records."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from search_engine.config import SearchEngineConfig
from search_engine.database.mongo import MongoConnection
from search_engine.database.repositories import IndexRepository, PublicationRepository
from search_engine.scheduler.weekly_update import ScheduledUpdateResult, run_update_once


SORT_OPTIONS = ["newest", "oldest", "title", "recently crawled"]


def local_timezone():
    return datetime.now().astimezone().tzinfo


def to_local_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(local_timezone())


def format_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return to_local_datetime(value).strftime("%Y-%m-%d %H:%M")
    if value:
        return str(value)
    return "Unknown"


def format_year(value: Any) -> str:
    return str(value) if value else "Unknown year"


def author_markdown(authors: list[dict]) -> str:
    links = []
    for author in authors:
        name = author.get("name") or "Unknown author"
        profile_url = author.get("profile_url")
        if profile_url:
            links.append(f"[{name}]({profile_url})")
        else:
            links.append(name)
    return ", ".join(links) if links else "Unknown authors"


@st.cache_data(ttl=60)
def load_dashboard_data(
    refresh_marker: int,
) -> dict:
    config = SearchEngineConfig.from_env()
    connection = MongoConnection(config)
    try:
        connection.ping()
        repository = PublicationRepository(connection.db)
        index_repository = IndexRepository(connection.db)
        return {
            "database_name": config.mongo_db_name,
            "publication_count": repository.count_publications(),
            "author_count": repository.count_authors(),
            "crawl_run_count": repository.count_crawl_runs(),
            "index_term_count": index_repository.count_terms(),
            "index_document_count": index_repository.count_document_vectors(),
            "index_metadata": index_repository.get_index_metadata(),
            "years": repository.list_available_years(),
            "authors": repository.list_authors(limit=100),
            "crawl_runs": repository.list_crawl_runs(limit=10),
        }
    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_publications(
    year: int | None,
    author_query: str,
    text_query: str,
    sort_by: str,
    limit: int,
    refresh_marker: int,
) -> list[dict]:
    config = SearchEngineConfig.from_env()
    connection = MongoConnection(config)
    try:
        connection.ping()
        repository = PublicationRepository(connection.db)
        return repository.list_publications(
            year=year,
            author_query=author_query or None,
            text_query=text_query or None,
            sort_by=sort_by,
            limit=limit,
        )
    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_search_results(query: str, limit: int, refresh_marker: int) -> list[dict]:
    config = SearchEngineConfig.from_env()
    connection = MongoConnection(config)
    try:
        connection.ping()
        repository = IndexRepository(connection.db)
        return repository.search(query, limit=limit)
    finally:
        connection.close()


def render_metrics(data: dict) -> None:
    latest_run = data["crawl_runs"][0] if data["crawl_runs"] else {}
    latest_run_time = format_datetime(latest_run.get("finished_at"))

    first, second, third, fourth, fifth = st.columns(5)
    first.metric("Publications", data["publication_count"])
    second.metric("Authors", data["author_count"])
    third.metric("Crawl Runs", data["crawl_run_count"])
    fourth.metric("Index Terms", data["index_term_count"])
    fifth.metric("Latest Crawl (Local)", latest_run_time)


def render_publication(publication: dict) -> None:
    title = publication.get("title") or "Untitled publication"
    publication_url = publication.get("publication_url")
    year = format_year(publication.get("publication_year"))
    source = publication.get("source") or publication.get("publication_type") or "No source recorded"
    authors = publication.get("authors", [])
    publication_type = publication.get("publication_type")
    published_date = publication.get("published_date")

    if publication_url:
        st.markdown(f"#### [{title}]({publication_url})")
    else:
        st.markdown(f"#### {title}")

    st.caption(f"{year} | {source}")
    st.markdown(author_markdown(authors))

    if publication_type or published_date:
        details = []
        if publication_type:
            details.append(publication_type)
        if published_date:
            details.append(f"Published: {published_date}")
        st.caption(" | ".join(details))

    st.divider()


def render_publications(publications: list[dict]) -> None:
    if not publications:
        st.info("No publication records match the selected filters.")
        return

    for publication in publications:
        render_publication(publication)


def render_publication_filters(years: list[int]) -> tuple[int | None, str, str, str, int]:
    st.subheader("Browse Publications")

    first, second, third = st.columns([1, 1, 2])
    year_options = ["All years"] + years
    selected_year = first.selectbox("Year", year_options)
    sort_by = second.selectbox("Sort", SORT_OPTIONS)
    limit = third.slider("Records", min_value=5, max_value=100, value=25, step=5)

    fourth, fifth = st.columns(2)
    author_query = fourth.text_input("Author")
    text_query = fifth.text_input("Title or Source")

    year = None if selected_year == "All years" else int(selected_year)
    return year, author_query.strip(), text_query.strip(), sort_by, limit


def render_publications_tab(years: list[int], refresh_marker: int) -> None:
    year, author_query, text_query, sort_by, limit = render_publication_filters(years)

    try:
        publications = load_publications(
            year=year,
            author_query=author_query,
            text_query=text_query,
            sort_by=sort_by,
            limit=limit,
            refresh_marker=refresh_marker,
        )
    except Exception as exc:
        st.error(f"Publication query failed: {exc}")
        return

    render_publications(publications)


def render_search_result(publication: dict) -> None:
    title = publication.get("title") or "Untitled publication"
    publication_url = publication.get("publication_url")
    score = publication.get("score", 0.0)
    matched_terms = ", ".join(publication.get("matched_terms", [])) or "None"
    source = publication.get("source") or publication.get("publication_type") or "No source recorded"

    if publication_url:
        st.markdown(f"#### [{title}]({publication_url})")
    else:
        st.markdown(f"#### {title}")

    st.caption(f"{format_year(publication.get('publication_year'))} | {source}")
    st.markdown(author_markdown(publication.get("authors", [])))
    st.caption(f"Score: {score:.4f} | Matched terms: {matched_terms}")
    st.divider()


def render_search_tab(refresh_marker: int) -> None:
    st.subheader("Search Publications")
    query = st.text_input("Search publications", placeholder="mental health stress")
    limit = st.slider("Results", min_value=5, max_value=50, value=10, step=5)

    if not query.strip():
        return

    try:
        results = load_search_results(query.strip(), limit, refresh_marker)
    except Exception as exc:
        st.error(f"Search failed: {exc}")
        return

    if not results:
        st.info("No ranked results found.")
        return

    for publication in results:
        render_search_result(publication)


def render_authors(authors: list[dict]) -> None:
    st.subheader("Authors")
    if not authors:
        st.info("No author records are stored yet.")
        return

    rows = []
    for author in authors:
        publication_count = len(author.get("publication_keys", []))
        rows.append(
            {
                "Name": author.get("name", "Unknown author"),
                "Publications": publication_count,
                "Profile": author.get("profile_url") or "",
            }
        )

    st.dataframe(rows, hide_index=True, use_container_width=True)


def render_crawl_runs(crawl_runs: list[dict]) -> None:
    st.subheader("Crawl History")
    if not crawl_runs:
        st.info("No crawl runs are stored yet.")
        return

    rows = []
    for crawl_run in crawl_runs:
        rows.append(
            {
                "Finished At (Local)": format_datetime(crawl_run.get("finished_at")),
                "Status": crawl_run.get("status", "unknown"),
                "Pages Visited": crawl_run.get("pages_visited", 0),
                "Publications Found": crawl_run.get("publications_found", 0),
                "Publications Saved": crawl_run.get("publications_saved", 0),
                "Failed URLs": len(crawl_run.get("failed_urls", [])),
            }
        )

    st.dataframe(rows, hide_index=True, use_container_width=True)


def render_update_summary(result: ScheduledUpdateResult) -> None:
    first, second, third, fourth = st.columns(4)
    first.metric("Extracted", result.publications_extracted)
    second.metric("Saved", result.publications_saved)
    third.metric("Pages", result.pages_visited)
    fourth.metric("Profiles", result.profile_pages_visited)
    st.caption(result.index_message)


def render_scheduler_tab() -> None:
    st.subheader("Scheduler")

    last_result = st.session_state.get("last_crawl_update_result")
    if last_result is not None:
        st.success("Last scheduled update completed.")
        render_update_summary(last_result)

    st.caption("Run one crawler/index update from the GUI. The continuous weekly scheduler still runs from the terminal.")

    first, second, third = st.columns(3)
    max_listing_pages = first.number_input(
        "Listing Pages",
        min_value=1,
        max_value=5,
        value=1,
        step=1,
    )
    max_profile_pages = second.number_input(
        "Profile Pages",
        min_value=0,
        max_value=25,
        value=8,
        step=1,
    )
    max_publications = third.number_input(
        "Publications",
        min_value=1,
        max_value=100,
        value=25,
        step=1,
    )

    if not st.button("Run Crawl Update", type="primary"):
        return

    with st.spinner("Crawling Pure Portal and rebuilding the search index..."):
        result = run_update_once(
            max_listing_pages=int(max_listing_pages),
            max_profile_pages=int(max_profile_pages),
            max_publications=int(max_publications),
        )

    st.session_state.last_crawl_update_result = result
    st.cache_data.clear()
    st.session_state.refresh_marker += 1
    st.rerun()


def render_crawl_runs_tab(crawl_runs: list[dict]) -> None:
    left, right = st.columns([3, 1])
    with left:
        st.subheader("Crawl Runs")
    with right:
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.session_state.refresh_marker += 1
            st.rerun()

    render_crawl_runs(crawl_runs)


def main() -> None:
    st.set_page_config(
        page_title="Coventry Pure Portal Search Engine",
        layout="wide",
    )

    st.title("Coventry Pure Portal Search Engine")

    if "refresh_marker" not in st.session_state:
        st.session_state.refresh_marker = 0

    try:
        data = load_dashboard_data(
            refresh_marker=st.session_state.refresh_marker,
        )
    except Exception as exc:
        st.error(f"MongoDB query failed: {exc}")
        return

    st.caption(f"Database: {data['database_name']}")
    render_metrics(data)

    search_tab, publications_tab, authors_tab, crawl_runs_tab, scheduler_tab = st.tabs(
        ["Search", "Publications", "Authors", "Crawl Runs", "Scheduler"]
    )
    with search_tab:
        render_search_tab(st.session_state.refresh_marker)
    with publications_tab:
        render_publications_tab(data["years"], st.session_state.refresh_marker)
    with authors_tab:
        render_authors(data["authors"])
    with crawl_runs_tab:
        render_crawl_runs_tab(data["crawl_runs"])
    with scheduler_tab:
        try:
            render_scheduler_tab()
        except Exception as exc:
            st.error(f"Scheduler update failed: {exc}")


if __name__ == "__main__":
    main()
