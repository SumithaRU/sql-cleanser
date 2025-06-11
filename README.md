# SQL Cleanser

SQL Cleanser is an end-to-end web project that cleans and transforms PostgreSQL INSERT-only scripts into Oracle-compatible SQL with duplicate detection, ordering fixes, and a human-readable report.

## Prerequisites

- Python 3.8+
- Node.js 16+
- Ollama installed and running locally

## Backend Setup

```bash
cd sql-cleanser/backend
pip install -r requirements.txt
export OLLAMA_HOST=http://localhost:11434
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Setup

```bash
cd sql-cleanser/frontend
npm install
npm run dev
```

## Demo

```bash
cd sql-cleanser
scripts/run_demo.sh
``` 