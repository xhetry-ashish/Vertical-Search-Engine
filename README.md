# Coventry Pure Portal Vertical Search Engine

This project implements Task 1 of the Information Retrieval final assignment.

Current progress covers the first three methods:

1. Crawl Coventry Pure Portal pages for the Centre for Healthcare and Community Transformation.
2. Extract publication and author metadata from crawled pages.
3. Store publication and author records in MongoDB.

## Project Structure

```text
search_engine/
  config.py
  models.py
  main.py
  crawler/
    polite_client.py
    parsers.py
    pureportal_crawler.py
  database/
    mongo.py
    repositories.py
tests/
  test_steps_1_to_3.py
```

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` and set your own `MONGO_URI`.

Do not commit `.env` to GitHub.

## Run Step 1 to Step 3

From inside the `Final Assignment` folder:

```bash
python3 -m search_engine.main crawl --max-listing-pages 2 --max-publications 10
```

To test crawling and extraction without saving to MongoDB:

```bash
python3 -m search_engine.main crawl --max-listing-pages 1 --max-publications 5 --dry-run
```

To check only MongoDB connectivity:

```bash
python3 -m search_engine.main check-db
```

## MongoDB Collections

The code creates and updates these collections:

```text
publications
authors
crawl_runs
```

`publications` stores extracted publication records, including title, year, source, publication URL, author links, and searchable text.

`authors` stores author profile data and references back to publication records.

`crawl_runs` stores crawl history, including visited page count, saved record count, blocked URLs, and failed URLs.

## Suggested Commits So Far

```bash
git add "Final Assignment"
git commit -m "chore: initialize search engine project"
git commit -m "feat: add polite Pure Portal crawler and metadata parser"
git commit -m "feat: store crawled publication records in MongoDB"
```

If you want separate commits exactly, stage only the related files for each commit.
