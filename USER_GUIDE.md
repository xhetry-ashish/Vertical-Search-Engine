# User Guide: Information Retrieval Search and Clustering System

This guide explains how to use the GUI and how the main backend operations work. It is written for assignment understanding and video demonstration.

## 1. System Overview

The application contains two assignment tasks in one Streamlit interface.

Task 1 is the search engine. It crawls Coventry Pure Portal publication records, stores them in MongoDB, builds an inverted index, and ranks search results using TF-IDF and cosine similarity.

Task 2 is document clustering. It groups documents from Economics, Entertainment, and Politics into 3 clusters using TF-IDF and K-Means. It can also assign a new document to the nearest cluster.

Main workflow:

```text
crawl records -> store in MongoDB -> preprocess text -> build index -> search/rank results -> display in GUI
```

Task 2 workflow:

```text
load documents -> preprocess text -> create TF-IDF vectors -> run K-Means -> predict cluster for new document
```

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

Keep the terminal running while using the GUI. If the terminal is stopped, the Streamlit app and GUI scheduler will stop.

## 3. Main Dashboard

At the top of the app, the dashboard shows the current system state.

### Publications

What it is: total number of publication records stored in MongoDB.

Use: shows how many crawled records are available for browsing and searching.

Backend: the app counts documents in the `publications` collection.

### Authors

What it is: total number of author records stored in MongoDB.

Use: shows how many unique authors were extracted from publication metadata.

Backend: the app counts documents in the `authors` collection.

### Crawl Runs

What it is: total number of crawler executions saved by the system.

Use: proves that the crawler activity is logged.

Backend: every crawl creates a record in the `crawl_runs` collection.

### Index Terms

What it is: total number of unique terms in the inverted index.

Use: shows that the search engine has processed text and built a searchable vocabulary.

Backend: the app counts terms stored in the `inverted_index` collection.

### Latest Crawl (Local)

What it is: finish date and time of the latest crawl run using the local machine time.

Use: shows when the data was most recently updated.

Backend: crawl times are stored as datetimes and converted to local display format:

```text
YYYY-MM-DD HH:MM
```

## 4. GUI Tabs

The app has these tabs:

```text
Search
Publications
Authors
Crawl Runs
Scheduler
Document Clustering
```

## 5. Search Tab

Use this tab to search publication records already stored in MongoDB and indexed by the system.

The Search tab does not crawl Pure Portal live. It searches only the stored and indexed publication collection. To add more searchable records, use the Scheduler tab first.

### Search Publications Input

What it is: the text box where the user enters a query.

Use: type words related to publications you want to find.

Example:

```text
mental wellbeing stress
```

Backend:

1. The query is lowercased.
2. Punctuation is removed.
3. Stop words are removed.
4. Terms are stemmed.
5. Query terms are matched against the inverted index.
6. TF-IDF query vector is created.
7. Cosine similarity is calculated against document vectors.
8. Results are ranked by score.

### Results Slider

What it is: controls how many search results are displayed.

Use: choose a small number for a quick demo or a larger number to inspect more results.

Backend: the search function limits the number of ranked results returned from the index.

### Search Result Fields

Title: publication title.

Publication link: opens the original Pure Portal record.

Year: publication year if extracted.

Source/type: publication source or publication type.

Authors: extracted author names and profile links.

Score: cosine similarity score. Higher score means the publication is more relevant to the query.

Matched terms: query terms that matched index terms.

## 6. Publications Tab

Use this tab to browse records stored in MongoDB.

This tab is not a ranked search page. It is a record viewer with filters.

### Year Filter

What it is: filters publications by publication year.

Use: view publications from one year only.

Backend: MongoDB query filters records by `publication_year`.

### Sort Filter

What it is: changes the order of displayed publication records.

Options:

- `newest`: newest publication year first
- `oldest`: oldest publication year first
- `title`: alphabetical title order
- `recently crawled`: latest crawled records first

Use: makes browsing easier depending on what you want to show.

Backend: MongoDB applies the selected sort order.

### Records Slider

What it is: controls how many publication records are shown in the tab.

Use: keep it low for a short video demo, increase it to inspect more records.

Backend: MongoDB query returns only the selected number of records.

### Author Filter

What it is: searches inside stored author names.

Use: find publications linked to a specific author.

Backend: MongoDB filters publication records where author names match the entered text.

### Title or Source Filter

What it is: searches within publication titles and source/type fields.

Use: quickly find records by title words, journal/source name, or publication type.

Backend: MongoDB filters stored publication metadata.

## 7. Authors Tab

Use this tab to view extracted authors.

### Name

What it is: author name extracted from Pure Portal.

Use: shows which researchers are connected to the stored publications.

Backend: author names are collected during parsing and saved in the `authors` collection.

### Publications

What it is: number of stored publication records linked to that author.

Use: shows how many records the author appears in.

Backend: author records store linked publication keys.

### Profile

What it is: Pure Portal profile link if available.

Use: opens the author's Pure Portal page.

Backend: profile URLs are extracted from publication pages and profile/listing pages.

## 8. Crawl Runs Tab

Use this tab to view crawler history.

### Refresh Button

What it is: reloads dashboard and crawl history data from MongoDB.

Use: click after running or scheduling a crawl to see updated records.

Backend: Streamlit cache is cleared and the app reloads data.

### Finished At (Local)

What it is: time when the crawl finished, shown in local machine time.

Use: confirms when a crawl was completed.

Backend: stored crawl datetime is converted to local time.

### Status

What it is: result of the crawl run.

Use: tells whether the crawl completed or failed.

Backend: crawler saves a status value in the `crawl_runs` collection.

### Pages Visited

What it is: number of web pages requested during the crawl.

Use: shows crawler activity.

Backend: crawler counts visited organisation, listing, profile, and publication pages.

### Publications Found

What it is: number of publication records extracted during the crawl.

Use: shows how many records the crawler discovered.

Backend: parser creates publication objects from crawled pages.

### Publications Saved

What it is: number of publication records inserted or updated in MongoDB.

Use: proves that crawl results were stored.

Backend: repository saves records using upsert logic, so duplicates are updated instead of inserted again.

### Failed URLs

What it is: number of URLs that could not be crawled.

Use: helps identify blocked or failed pages.

Backend: crawler stores failed URLs in the crawl run log.

## 9. Scheduler Tab

Use this tab to run a crawl/index update immediately or schedule one for a specific local date and time.

The Scheduler tab is the main GUI method for adding more publication records.

### Crawl Settings

These settings control the size of the crawl.

### Listing Pages

What it is: number of Pure Portal listing pages the crawler checks.

Use: listing pages can contain publication links.

How to use: keep it low for a quick demo.

Recommended quick demo value:

```text
1
```

Backend: crawler visits up to this number of listing pages from the organisation/publication area.

### Profile Pages

What it is: number of researcher profile pages the crawler visits.

Use: profile pages help find more publication links when the main publication listing has limited access.

How to use: use `1` or `2` for a quick demo; use more if you want more records.

Recommended quick demo value:

```text
1
```

Backend: crawler extracts profile links, visits selected profiles, and collects publication links from them.

### Publications

What it is: maximum number of publication detail records to crawl and save.

Use: this is the main control for quick demonstration speed.

Recommended quick demo value:

```text
5
```

Backend: crawler stops after reaching this publication limit.

Quick showcase settings:

```text
Listing Pages: 1
Profile Pages: 1
Publications: 5
```

### Run Crawl Update Now

What it is: button for immediate crawl/index update.

Use: click this when you want to crawl now without waiting.

Backend process:

```text
click button -> crawl Pure Portal -> parse records -> save MongoDB -> save crawl log -> rebuild inverted index -> update GUI
```

After it finishes, the Search tab uses the newly rebuilt index.

### Schedule by Date and Time

Use this section to schedule one crawl update for a specific local date and time.

### Run Date

What it is: calendar date when the crawl should run.

Use: choose today's date or a future date.

Backend: the chosen date is combined with Run Time to create one scheduled datetime.

### Run Time

What it is: local machine time when the crawl should run.

Use: select time in 24-hour format.

Example:

```text
20:26
```

Backend: the app combines Run Date and Run Time, converts it to an internal datetime, and waits until that time.

### Schedule Crawl Update

What it is: button that creates a scheduled crawl job.

Use: click after choosing Run Date, Run Time, and crawl settings.

Backend process:

```text
schedule button -> create waiting background job -> wait until selected time -> run crawler -> save MongoDB -> rebuild index
```

Important: the Streamlit server must stay running until the scheduled time. This GUI schedule is stored in memory while the app server is active.

### Scheduled Run Status

What it is: shows the state of the scheduled crawl.

Possible statuses:

- `Idle`: no job is scheduled
- `Waiting`: job is scheduled and waiting for the selected time
- `Running`: crawl/index update is currently running
- `Completed`: scheduled update finished successfully
- `Failed`: scheduled update failed
- `Cancelled`: waiting job was cancelled

Use: check this section to explain scheduler behavior in the video.

### Refresh Status

What it is: reloads the scheduler status display.

Use: click after the scheduled time to see whether the job has started or completed.

Backend: Streamlit reruns the page and reads the current scheduler state.

### Cancel Scheduled Run

What it is: cancels a waiting scheduled run.

Use: click if you selected the wrong date/time.

Backend: cancellation signal is sent to the background scheduler job before it starts.

## 10. Document Clustering Tab

Use this tab for Task 2.

The clustering task uses exactly 3 clusters because the assignment categories are:

```text
Economics
Entertainment
Politics
```

### Documents Metric

What it is: number of documents used for clustering.

Use: shows that the dataset has more than 100 documents.

Backend: the app loads the included document collection.

### Vocabulary Metric

What it is: number of unique processed terms.

Use: shows how many terms are used to create document vectors.

Backend: preprocessing creates tokens and unique terms are stored in a vocabulary list.

### Clusters Metric

What it is: number of K-Means clusters.

Use: confirms the assignment requirement of 3 clusters.

Backend: K-Means is run with `k = 3`.

### Iterations Metric

What it is: number of K-Means update rounds needed before convergence.

Use: shows that the clustering algorithm actually ran.

Backend: K-Means repeatedly assigns documents to centroids and updates centroids until labels stop changing or the maximum iteration limit is reached.

### Cluster Summary

What it is: table describing each cluster.

Fields:

- `Cluster`: cluster number
- `Documents`: number of documents assigned to that cluster
- `Majority Category`: most common known category inside that cluster
- `Top Terms`: important terms near that cluster centroid
- `Category Counts`: category distribution inside the cluster

Use: explains what each cluster represents.

Backend: after K-Means finishes, the system counts categories per cluster and extracts top centroid terms.

### Assign New Document

What it is: text area where you paste or type a new document.

Use: tests which cluster a new unseen document belongs to.

Example Economics text:

```text
Inflation and interest rates changed household spending and business investment.
```

Example Entertainment text:

```text
The film festival highlighted new directors and award nominations.
```

Example Politics text:

```text
The government debated new legislation before parliament.
```

Backend process:

```text
new text -> preprocess -> TF-IDF vector -> compare with cluster centroids -> choose nearest cluster
```

### Predicted Cluster

What it is: cluster number assigned to the new document.

Use: shows the clustering result.

Backend: nearest centroid is selected using distance calculation.

### Likely Category

What it is: category label inferred from the majority category of the predicted cluster.

Use: makes the cluster result easier to understand.

Backend: the system checks which known category appears most often in that cluster.

### Distance

What it is: distance between the new document vector and the selected cluster centroid.

Use: lower distance means the new document is closer to that cluster.

Backend: vector distance is calculated against all centroids.

### Cluster Terms

What it is: important terms from the selected cluster.

Use: explains why the document may belong to that cluster.

Backend: top weighted centroid terms are displayed.

### Document Collection Preview

What it is: sample rows from the document collection.

Use: shows that the dataset contains Economics, Entertainment, and Politics documents.

Backend: the preview displays a balanced sample from each category.

## 11. Manual Backend Commands

These commands are useful if you need to show backend functionality outside the GUI.

### Check MongoDB

What it is: tests whether the app can connect to MongoDB.

Command:

```bash
python3 -m search_engine.main check-db
```

Use: run before the video to confirm database access.

### Crawl From Terminal

What it is: runs the crawler without the GUI.

Command:

```bash
python3 -m search_engine.main crawl --max-listing-pages 1 --max-profile-pages 1 --max-publications 5
```

Use: good for testing or showing command-line control.

Backend: crawls Pure Portal, saves MongoDB records, saves crawl run log, and rebuilds the index.

### Build Index Manually

What it is: rebuilds the inverted index from stored MongoDB publications.

Command:

```bash
python3 -m search_engine.main build-index
```

Use: run after changing stored records if you want to rebuild search data manually.

Backend: reads `publications`, preprocesses text, builds `inverted_index`, `document_vectors`, and `index_metadata`.

### Search From Terminal

What it is: runs ranked search without the GUI.

Command:

```bash
python3 -m search_engine.main search "mental wellbeing stress" --limit 5
```

Use: proves the search engine works from backend commands too.

Backend: uses the same index and ranking process as the Search tab.

### One-Time Scheduler Command

What it is: runs one scheduled update and exits.

Command:

```bash
python3 -m search_engine.main scheduler --once --max-listing-pages 1 --max-profile-pages 1 --max-publications 5
```

Use: useful for quick testing from terminal.

Backend: performs one crawl, saves records, and rebuilds the index.

### Continuous Weekly Scheduler

What it is: terminal scheduler that keeps running and repeats updates.

Command:

```bash
python3 -m search_engine.main scheduler
```

Use: shows how the system can stay updated over time.

Backend: runs once immediately, then waits for the configured interval.

Default interval:

```text
7 days
```

Stop it with:

```text
Ctrl + C
```

### Run Tests

What it is: runs automated checks.

Command:

```bash
python3 -m unittest discover -s tests
```

Use: proves the main backend functionality still works after changes.

## 12. Logical Backend Process

### Step 1: Polite Crawling

Main file:

```text
search_engine/crawler/polite_client.py
```

What it is: responsible for making web requests carefully.

Use: avoids sending too many requests too quickly.

How it is done:

- uses a custom user agent
- checks `robots.txt`
- waits between requests
- limits crawling to `pureportal.coventry.ac.uk`

### Step 2: Pure Portal Crawling

Main file:

```text
search_engine/crawler/pureportal_crawler.py
```

What it is: crawler logic for Coventry Pure Portal.

Use: finds publication URLs and collects publication pages.

How it is done:

1. Starts from the Centre for Healthcare and Community Transformation page.
2. Extracts publication links.
3. Extracts researcher profile links.
4. Visits selected profile pages.
5. Collects more publication links.
6. Visits publication detail pages.

### Step 3: Metadata Parsing

Main file:

```text
search_engine/crawler/parsers.py
```

What it is: converts raw HTML pages into structured publication data.

Use: extracts useful fields for storage and search.

How it is done:

- parses publication title
- parses publication URL
- parses authors
- parses author profile URLs
- parses publication year
- parses source/type
- stores available page text for indexing

### Step 4: MongoDB Storage

Main files:

```text
search_engine/database/mongo.py
search_engine/database/repositories.py
```

What it is: database layer.

Use: stores crawled publications, authors, crawl logs, and index data.

MongoDB collections:

```text
publications
authors
crawl_runs
inverted_index
document_vectors
index_metadata
```

Collection details:

`publications`

What it stores: the main publication records collected from Coventry Pure Portal.

Important fields:

- `publication_key`: stable unique ID generated from the publication URL
- `title`: publication title
- `publication_url`: original Pure Portal publication link
- `authors`: author names and profile links attached to the publication
- `author_keys`: unique IDs of linked authors
- `publication_year`: extracted publication year
- `published_date`: extracted publication date if available
- `source`: journal, event, or source text if available
- `publication_type`: article, conference item, report, or other type if available
- `abstract`: abstract text if available
- `full_text`: page text collected from the crawled page
- `searchable_text`: combined text used for indexing and searching
- `crawled_from`: page where the crawler found the record
- `crawled_at`: time when the page was crawled
- `first_seen_at`: first time this record was saved
- `updated_at`: latest time this record was saved or updated

Use: this collection is the main dataset for the Search and Publications tabs.

`authors`

What it stores: unique author records extracted from publications.

Important fields:

- `author_key`: stable unique ID generated from profile URL or author name
- `name`: author name
- `profile_url`: Pure Portal profile link if available
- `affiliation`: affiliation if available
- `publication_keys`: list of publications linked to the author
- `first_seen_at`: first time the author was saved
- `updated_at`: latest time the author was updated

Use: this collection powers the Authors tab and links authors back to publications.

`crawl_runs`

What it stores: history of crawler executions.

Important fields:

- `seed_url`: starting URL used by the crawler
- `pages_visited`: number of pages requested
- `publications_found`: number of publications extracted
- `publications_saved`: number of publications inserted or updated in MongoDB
- `skipped_by_robots`: URLs skipped because of `robots.txt`
- `failed_urls`: URLs that failed during crawling
- `status`: crawl result, usually completed or failed
- `started_at`: time when the crawl started
- `finished_at`: time when the crawl finished

Use: this collection powers the Crawl Runs tab and proves crawler activity for the assignment.

`inverted_index`

What it stores: the custom search index that maps each processed term to matching publications.

Important fields:

- `term`: processed word after cleaning/stemming
- `document_frequency`: number of publications containing the term
- `idf`: inverse document frequency weight for the term
- `postings`: list of publication entries where the term appears
- `postings.publication_key`: matching publication ID
- `postings.term_frequency`: number of times the term appears in that publication
- `postings.positions`: token positions where the term appears

Use: this collection lets the system find candidate publications for a query using IR indexing.

`document_vectors`

What it stores: normalized TF-IDF vectors for each publication.

Important fields:

- `publication_key`: publication ID
- `title`: publication title
- `publication_url`: original Pure Portal link
- `publication_year`: publication year
- `authors`: linked authors
- `token_count`: number of processed tokens in the publication text
- `unique_term_count`: number of unique terms in the publication
- `vector`: normalized TF-IDF term-weight dictionary
- `indexed_at`: time when the vector was created

Use: this collection is used for cosine similarity ranking in the Search tab.

`index_metadata`

What it stores: summary information about the current search index.

Important fields:

- `name`: index name, currently `publication_index`
- `document_count`: number of publications indexed
- `vocabulary_size`: number of unique indexed terms
- `indexed_at`: time when the index was last rebuilt

Use: this collection helps show whether the index is built and when it was last updated.

How it is done:

- connects using `MONGO_URI`
- saves records with upsert logic
- updates existing records instead of duplicating them
- stores crawl history separately

### Step 5: Text Preprocessing

Main file:

```text
search_engine/indexer/preprocessing.py
```

What it is: cleans raw text before indexing/searching/clustering.

Use: makes matching more consistent.

How it is done:

1. Lowercase conversion.
2. Punctuation removal.
3. Tokenization.
4. Stop-word removal.
5. Simple stemming.

Example:

```text
Mental health studies
```

can become:

```text
mental health studi
```

### Step 6: Inverted Index

Main file:

```text
search_engine/indexer/inverted_index.py
```

What it is: data structure that maps terms to documents.

Use: makes search faster and demonstrates IR indexing.

Example:

```text
mental -> publication_1, publication_2
stress -> publication_1
health -> publication_1, publication_3
```

How it is done:

- each publication text is preprocessed
- term frequencies are counted
- each term is connected to the documents where it appears
- index data is stored in MongoDB

### Step 7: TF-IDF Weighting

What it is: weighting method for terms.

Use: gives more importance to specific terms and less importance to very common terms.

Meaning:

```text
TF = how often a term appears in a document
IDF = how rare or important a term is across all documents
TF-IDF = TF * IDF
```

How it is done:

- calculate term frequency for each document
- calculate document frequency for each term
- calculate IDF
- create document vectors

### Step 8: Ranking With Cosine Similarity

Main file:

```text
search_engine/indexer/ranking.py
```

What it is: method for ranking documents against a query.

Use: puts the most relevant search results at the top.

How it is done:

1. Convert query into a TF-IDF vector.
2. Compare query vector with each matching document vector.
3. Calculate cosine similarity.
4. Sort documents by score.

Higher score means stronger relevance.

### Step 9: Scheduler Backend

Main files:

```text
search_engine/scheduler/weekly_update.py
search_engine/scheduler/gui_schedule.py
```

What it is: update system for running crawl and index rebuild.

Use: keeps publication records and search index updated.

How it is done:

- immediate GUI update calls `run_update_once`
- scheduled GUI update waits until selected local date/time
- terminal scheduler can run continuously every configured interval
- every update crawls, saves, logs, and rebuilds the index

### Step 10: Document Clustering

Main files:

```text
search_engine/clustering/dataset.py
search_engine/clustering/text_clustering.py
```

What it is: Task 2 clustering backend.

Use: groups documents by content and predicts a cluster for new text.

How it is done:

1. Load the document collection.
2. Preprocess document text.
3. Build vocabulary.
4. Build TF-IDF matrix.
5. Initialize 3 centroids.
6. Assign each document to the nearest centroid.
7. Recalculate centroids.
8. Repeat until stable.
9. Summarize clusters using top terms and category counts.
10. Convert new document text into a TF-IDF vector.
11. Assign the new document to the nearest centroid.

## 13. Suggested Video Demonstration Flow

Use this order for your video:

1. Show the project folder.
2. Explain that the app has Task 1 search engine and Task 2 document clustering.
3. Run MongoDB connection check:

```bash
python3 -m search_engine.main check-db
```

4. Start the GUI:

```bash
streamlit run search_engine/app.py
```

5. Show dashboard metrics.
6. Open the Publications tab and explain filters.
7. Open the Authors tab and explain author records.
8. Open the Crawl Runs tab and explain crawl history.
9. Open the Scheduler tab and use quick showcase settings:

```text
Listing Pages: 1
Profile Pages: 1
Publications: 5
```

10. Click `Run Crawl Update Now`.
11. Explain that the crawler saves records to MongoDB and rebuilds the index.
12. Open the Search tab and search:

```text
mental wellbeing stress
```

13. Explain score and matched terms.
14. Open the Scheduler tab again and show scheduled date/time controls.
15. Open the Document Clustering tab.
16. Explain documents, vocabulary, clusters, and iterations.
17. Show the Cluster Summary table.
18. Paste one new document and explain the predicted cluster.

## 14. Short Explanation for Video

You can say:

> This application combines two Information Retrieval assignment tasks. For Task 1, it works as a vertical search engine for Coventry Pure Portal publications. It crawls publication pages, extracts metadata, stores records in MongoDB, preprocesses text, builds an inverted index, calculates TF-IDF vectors, and ranks search results using cosine similarity. The GUI allows searching, browsing publications, viewing authors, checking crawl history, and running or scheduling crawler updates. For Task 2, the Document Clustering tab groups Economics, Entertainment, and Politics documents into 3 clusters using TF-IDF and K-Means, then assigns a new user-entered document to the nearest cluster.
