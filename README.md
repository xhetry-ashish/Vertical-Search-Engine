# Coventry Pure Portal Search Engine

Task 1 project for the Information Retrieval final assignment.

The system crawls Coventry University's Centre for Healthcare and Community Transformation Pure Portal records, stores publication data in MongoDB, builds a custom inverted index, ranks results using TF-IDF cosine similarity, and shows results in a Streamlit UI.

## Setup

From inside the `Final Assignment` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `MONGO_URI`.

Do not commit `.env`.

## Run

Check MongoDB:

```bash
python3 -m search_engine.main check-db
```

Crawl publications, save to MongoDB, and rebuild the index:

```bash
python3 -m search_engine.main crawl --max-listing-pages 1 --max-profile-pages 8 --max-publications 25
```

Build the index manually:

```bash
python3 -m search_engine.main build-index
```

Search from command line:

```bash
python3 -m search_engine.main search "mental wellbeing stress" --limit 5
```

Run one scheduled update for testing:

```bash
python3 -m search_engine.main scheduler --once --max-listing-pages 1 --max-profile-pages 8 --max-publications 25
```

Run weekly scheduled updates:

```bash
python3 -m search_engine.main scheduler
```

Run the UI:

```bash
streamlit run search_engine/app.py
```

Open:

```text
http://localhost:8501
```

In the UI, open the `Scheduler` tab and click `Run Crawl Update` to crawl more records, save them to MongoDB, and rebuild the search index.

## Main Features

- polite crawler with `robots.txt` checking
- publication and author metadata extraction
- MongoDB storage
- text preprocessing
- custom inverted index
- TF-IDF vector scoring
- cosine similarity ranking
- weekly scheduled crawl/index updates
- Streamlit search, records viewer, and scheduler update controls

## Tests

```bash
python3 -m unittest discover -s tests
```
