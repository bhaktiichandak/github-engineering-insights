# GitHub Engineering Insights Analyzer

A backend analytics system that ingests GitHub repository commit data into PostgreSQL and provides engineering insights using SQL aggregations.

## 🚀 Features

- Fetches commit data from GitHub API
- Stores commit metadata in PostgreSQL
- Prevents duplicate ingestion using commit SHA
- Provides analytics endpoints:
  - Top contributors
  - Commit activity over time
  - Repository summary statistics

## 🏗 Architecture

User → FastAPI → GitHub API → PostgreSQL  
Analytics Endpoints → PostgreSQL Aggregation Queries

## 📊 Endpoints

### Ingest Commits
`/commits?owner=<owner>&repo=<repo>`

### Top Contributors
`/top-contributors?owner=<owner>&repo=<repo>`

### Commit Activity
`/commit-activity?owner=<owner>&repo=<repo>`

### Repository Summary
`/repo-summary?owner=<owner>&repo=<repo>`

## 🛠 Tech Stack

- Python
- FastAPI
- PostgreSQL
- psycopg2
- GitHub REST API

---
Built as part of backend engineering and data analytics practice.
