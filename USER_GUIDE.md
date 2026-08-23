# User Guide: Coventry Pure Portal Search Engine

This guide explains how to use the search engine for the assignment video and how the backend process works.

## 1. What the System Does

This system is a vertical search engine for Coventry University's Centre for Healthcare and Community Transformation publications.

It performs these main tasks:

1. Crawls publication records from Coventry Pure Portal.
2. Extracts publication title, authors, year, source, and links.
3. Stores publication and author records in MongoDB.
4. Preprocesses text using tokenization, stop-word removal, and stemming.
5. Builds a custom inverted index.
6. Creates TF-IDF document vectors.
7. Ranks search results using cosine similarity.
8. Displays search results in a Streamlit GUI.
9. Supports scheduled crawl and index updates.

## 2. Start the System

Open a terminal inside the `Final Assignment` folder:

```bash
cd "Final Assignment"
source .venv/bin/activate
```

Check MongoDB connection:

```bash
python3 -m search_engine.main check-db
```

Start the GUI:

```bash
streamlit run search_engine/app.py
```

Open this URL in the browser:

```text
http://localhost:8501
```

## 3. Using the GUI

The GUI has these tabs:

```text
Search
Publications
Authors
Crawl Runs
Scheduler
```

### Search Tab

Use this tab to search stored publications.

Example query:

```text
mental wellbeing stress
```

What happens:

1. The query is preprocessed.
2. Query terms are matched against the stored index.
3. The system calculates cosine similarity between the query vector and publication vectors.
4. Results are shown in ranked order.

Each result shows:

- title
- publication link
- year
- source or publication type
- authors
- relevance score
- matched terms

### Publications Tab

Use this tab to browse stored publication records.

The publication filters are inside this tab. You can filter by:

- year
- author
- title or source
- sort order
- number of records

This tab is useful in the video to show that the crawler saved real Pure Portal records into MongoDB.

### Authors Tab

This tab shows stored author records.

It displays:

- author name
- number of linked publications
- Pure Portal profile link, if available

### Crawl Runs Tab

This tab shows crawler history.

It displays:

- finish time
- status
- pages visited
- publications found
- publications saved
- failed URLs

### Scheduler Tab

This tab lets you add more records from the GUI.

To crawl more records from the GUI:

1. Open the `Scheduler` tab.
2. Set `Listing Pages`, `Profile Pages`, and `Publications`.
3. Click `Run Crawl Update`.
4. Wait until the crawl finishes.

Recommended values for the video:

```text
Listing Pages: 1
Profile Pages: 8
Publications: 25
```

When the update finishes, the system saves new records to MongoDB and rebuilds the search index. The Search tab will then use the updated index. The Crawl Runs tab shows the saved update history.

## 4. Scheduler Usage

The continuous weekly scheduler is started from the terminal, not from the GUI.

For video demonstration, use the one-time scheduler command:

```bash
python3 -m search_engine.main scheduler --once --max-listing-pages 1 --max-profile-pages 8 --max-publications 25
```

This performs one scheduled update and exits.

What it does:

1. Checks MongoDB connection.
2. Crawls the Pure Portal organisation page.
3. Extracts publication metadata.
4. Saves or updates publication records in MongoDB.
5. Saves a crawl run log.
6. Rebuilds the inverted index and TF-IDF vectors.

To run the weekly scheduler continuously:

```bash
python3 -m search_engine.main scheduler
```

This runs immediately once, then waits for the configured interval.

Default interval:

```text
7 days
```

The interval can be changed in `.env`:

```text
SCHEDULER_INTERVAL_DAYS=7
```

For a quick test interval, use a small value:

```bash
python3 -m search_engine.main scheduler --interval-days 0.01 --max-listing-pages 1 --max-profile-pages 2 --max-publications 5
```

Stop the scheduler with:

```text
Ctrl + C
```

## 5. Manual Backend Commands

Crawl and save records:

```bash
python3 -m search_engine.main crawl --max-listing-pages 1 --max-profile-pages 8 --max-publications 25
```

Build the index manually:

```bash
python3 -m search_engine.main build-index
```

Search from terminal:

```bash
python3 -m search_engine.main search "mental wellbeing stress" --limit 5
```

Run tests:

```bash
python3 -m unittest discover -s tests
```

## 6. Logical Backend Process

### Step 1: Polite Crawling

Main file:

```text
search_engine/crawler/polite_client.py
```

The crawler:

- uses a custom user agent
- checks `robots.txt`
- waits between requests
- limits crawling to `pureportal.coventry.ac.uk`
- avoids unnecessary fast requests

### Step 2: Pure Portal Crawling

Main file:

```text
search_engine/crawler/pureportal_crawler.py
```

The crawler starts from the Centre for Healthcare and Community Transformation page and collects publication links.

It then visits publication detail pages to collect richer metadata.

### Step 3: Metadata Parsing

Main file:

```text
search_engine/crawler/parsers.py
```

The parser extracts:

- publication title
- publication URL
- authors
- author profile URLs
- publication year
- source
- publication type
- abstract or page text where available

### Step 4: MongoDB Storage

Main files:

```text
search_engine/database/mongo.py
search_engine/database/repositories.py
```

MongoDB collections:

```text
publications
authors
crawl_runs
inverted_index
document_vectors
index_metadata
```

The system uses update/upsert logic, so existing records are updated instead of duplicated.

### Step 5: Text Preprocessing

Main file:

```text
search_engine/indexer/preprocessing.py
```

Preprocessing includes:

- lowercase conversion
- punctuation removal
- tokenization
- stop-word removal
- simple stemming

The same preprocessing is applied to both publication text and user queries.

### Step 6: Inverted Index

Main file:

```text
search_engine/indexer/inverted_index.py
```

The inverted index maps each term to the publications where it appears.

Example concept:

```text
mental -> publication_1, publication_2
stress -> publication_1
health -> publication_1, publication_3
```

This proves the system uses Information Retrieval indexing concepts rather than only MongoDB text search.

### Step 7: TF-IDF Weighting

For each term, the system calculates:

```text
TF = term frequency in a document
IDF = importance of a term across the whole collection
TF-IDF = TF * IDF
```

Common terms receive lower weight, while more specific terms receive higher weight.

### Step 8: Ranking With Cosine Similarity

Main file:

```text
search_engine/indexer/ranking.py
```

The query and each publication are represented as vectors.

Cosine similarity measures how close the query vector is to each publication vector.

Higher score means higher relevance.

### Step 9: GUI Display

Main file:

```text
search_engine/app.py
```

The Streamlit GUI reads from MongoDB and displays:

- ranked search results
- publication records
- author records
- crawl run history

## 7. Suggested Video Demonstration Flow

Use this order for your video:

1. Show the project folder and mention this is Task 1 Search Engine.
2. Open `.env.example` and explain MongoDB configuration.
3. Run:

```bash
python3 -m search_engine.main check-db
```

4. Run the GUI:

```bash
streamlit run search_engine/app.py
```

5. In the GUI, show:

```text
Publications tab
Authors tab
Crawl Runs tab
Scheduler tab
```

6. Go to the Search tab and search:

```text
mental wellbeing stress
```

7. Explain the ranked results and relevance score.
8. Open the Scheduler tab and click `Run Crawl Update`.
9. Refresh the Search tab and search again to show the larger collection.
10. Explain the backend flow:

```text
crawl -> parse -> MongoDB -> preprocess -> inverted index -> TF-IDF -> cosine ranking -> GUI
```

## 8. Short Explanation for Video

You can say:

> This system is a vertical search engine for Coventry Pure Portal publications. It uses a polite crawler to collect publication records, stores them in MongoDB, preprocesses the text, builds a custom inverted index, calculates TF-IDF vectors, and ranks search results using cosine similarity. The Streamlit interface allows users to search publications and view stored publication, author, and crawl history records. The scheduler can run the crawl and index update weekly so the search engine stays updated.
