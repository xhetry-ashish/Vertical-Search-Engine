"""Streamlit interface for viewing crawled Pure Portal records."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from search_engine.config import SearchEngineConfig
from search_engine.database.mongo import MongoConnection
from search_engine.database.repositories import PublicationRepository


SORT_OPTIONS = ["newest", "oldest", "title", "recently crawled"]


def format_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
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
    year: int | None,
    author_query: str,
    text_query: str,
    sort_by: str,
    limit: int,
    refresh_marker: int,
) -> dict:
    config = SearchEngineConfig.from_env()
    connection = MongoConnection(config)
    try:
        connection.ping()
        repository = PublicationRepository(connection.db)
        publications = repository.list_publications(
            year=year,
            author_query=author_query or None,
            text_query=text_query or None,
            sort_by=sort_by,
            limit=limit,
        )
        return {
            "database_name": config.mongo_db_name,
            "publication_count": repository.count_publications(),
            "author_count": repository.count_authors(),
            "crawl_run_count": repository.count_crawl_runs(),
            "years": repository.list_available_years(),
            "publications": publications,
            "authors": repository.list_authors(limit=100),
            "crawl_runs": repository.list_crawl_runs(limit=10),
        }
    finally:
        connection.close()


def render_metrics(data: dict) -> None:
    latest_run = data["crawl_runs"][0] if data["crawl_runs"] else {}
    latest_run_time = format_datetime(latest_run.get("finished_at"))

    first, second, third, fourth = st.columns(4)
    first.metric("Publications", data["publication_count"])
    second.metric("Authors", data["author_count"])
    third.metric("Crawl Runs", data["crawl_run_count"])
    fourth.metric("Latest Crawl", latest_run_time)


def render_publication(publication: dict) -> None:
    title = publication.get("title") or "Untitled publication"
    publication_url = publication.get("publication_url")
    year = format_year(publication.get("publication_year"))
    source = publication.get("source") or publication.get("publication_type") or "No source recorded"
    authors = publication.get("authors", [])

    if publication_url:
        st.markdown(f"#### [{title}]({publication_url})")
    else:
        st.markdown(f"#### {title}")

    st.caption(f"{year} | {source}")
    st.markdown(author_markdown(authors))

    publication_type = publication.get("publication_type")
    published_date = publication.get("published_date")
    if publication_type or published_date:
        details = []
        if publication_type:
            details.append(publication_type)
        if published_date:
            details.append(f"Published: {published_date}")
        st.caption(" | ".join(details))

    st.divider()


def render_publications(publications: list[dict]) -> None:
    st.subheader("Publications")
    if not publications:
        st.info("No publication records match the selected filters.")
        return

    for publication in publications:
        render_publication(publication)


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
    st.subheader("Crawl Runs")
    if not crawl_runs:
        st.info("No crawl runs are stored yet.")
        return

    rows = []
    for crawl_run in crawl_runs:
        rows.append(
            {
                "Finished At": format_datetime(crawl_run.get("finished_at")),
                "Status": crawl_run.get("status", "unknown"),
                "Pages Visited": crawl_run.get("pages_visited", 0),
                "Publications Found": crawl_run.get("publications_found", 0),
                "Publications Saved": crawl_run.get("publications_saved", 0),
                "Failed URLs": len(crawl_run.get("failed_urls", [])),
            }
        )

    st.dataframe(rows, hide_index=True, use_container_width=True)


def render_sidebar(years: list[int]) -> tuple[int | None, str, str, str, int]:
    st.sidebar.header("Filters")
    year_options = ["All years"] + years
    selected_year = st.sidebar.selectbox("Year", year_options)
    author_query = st.sidebar.text_input("Author")
    text_query = st.sidebar.text_input("Title or Source")
    sort_by = st.sidebar.selectbox("Sort", SORT_OPTIONS)
    limit = st.sidebar.slider("Records", min_value=5, max_value=100, value=25, step=5)

    year = None if selected_year == "All years" else int(selected_year)
    return year, author_query.strip(), text_query.strip(), sort_by, limit


def main() -> None:
    st.set_page_config(
        page_title="Coventry Pure Portal Records",
        layout="wide",
    )

    st.title("Coventry Pure Portal Records")

    if "refresh_marker" not in st.session_state:
        st.session_state.refresh_marker = 0

    try:
        initial_data = load_dashboard_data(
            year=None,
            author_query="",
            text_query="",
            sort_by="newest",
            limit=1,
            refresh_marker=st.session_state.refresh_marker,
        )
    except Exception as exc:
        st.error(f"MongoDB connection failed: {exc}")
        return

    year, author_query, text_query, sort_by, limit = render_sidebar(initial_data["years"])

    if st.sidebar.button("Refresh"):
        st.cache_data.clear()
        st.session_state.refresh_marker += 1
        st.rerun()

    try:
        data = load_dashboard_data(
            year=year,
            author_query=author_query,
            text_query=text_query,
            sort_by=sort_by,
            limit=limit,
            refresh_marker=st.session_state.refresh_marker,
        )
    except Exception as exc:
        st.error(f"MongoDB query failed: {exc}")
        return

    st.caption(f"Database: {data['database_name']}")
    render_metrics(data)

    publications_tab, authors_tab, crawl_runs_tab = st.tabs(
        ["Publications", "Authors", "Crawl Runs"]
    )
    with publications_tab:
        render_publications(data["publications"])
    with authors_tab:
        render_authors(data["authors"])
    with crawl_runs_tab:
        render_crawl_runs(data["crawl_runs"])


if __name__ == "__main__":
    main()
