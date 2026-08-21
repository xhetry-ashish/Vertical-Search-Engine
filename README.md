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
python3 -m search_engine.main crawl --max-listing-pages 1 --max-publications 10
```

Build the index manually:

```bash
python3 -m search_engine.main build-index
```

Search from command line:

```bash
python3 -m search_engine.main search "mental wellbeing stress" --limit 5
```

Run the UI:

```bash
streamlit run search_engine/app.py
```

Open:

```text
http://localhost:8501
```

## Main Features

- polite crawler with `robots.txt` checking
- publication and author metadata extraction
- MongoDB storage
- text preprocessing
- custom inverted index
- TF-IDF vector scoring
- cosine similarity ranking
- Streamlit search and records viewer

## Tests

```bash
python3 -m unittest discover -s tests
```
