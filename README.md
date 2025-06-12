# 🤖 SQL Cleanser - AI-Powered Database Migration Tool

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18%2B-blue.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![AI Powered](https://img.shields.io/badge/AI-Ollama%20LLaMA%203-orange.svg)](https://ollama.ai)

SQL Cleanser is an **AI-enhanced** end-to-end web application that intelligently transforms SQL scripts between PostgreSQL and Oracle databases in both directions, with advanced duplicate detection, semantic analysis, and comprehensive migration planning.

## ✨ Key Features

- 🤖 **AI-Powered Analysis**: Uses Ollama LLaMA 3 8B for intelligent data processing
- 🔍 **Smart Duplicate Detection**: Fuzzy matching and semantic duplicate identification
- 🔄 **Bidirectional Conversion**: PostgreSQL ↔ Oracle syntax transformation in both directions
- 📊 **Comprehensive Reports**: Detailed analysis with AI-generated insights
- 🎯 **Primary Key Intelligence**: AI-driven relationship detection
- 🌐 **Modern Web Interface**: React + TypeScript frontend with direction selector
- 📦 **Complete Packaging**: ZIP downloads with converted SQL and organized results
- 💾 **Smart Persistence**: Remembers your preferred conversion direction

## Prerequisites

- Python 3.8+
- Node.js 16+
- Ollama installed and running locally

## Backend Setup

```bash
cd src/backend
pip install -r requirements.txt
export OLLAMA_HOST=http://localhost:11434
# if needed here
export LLM_CALL_TIMEOUT="600"        # e.g. 10 minutes
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Setup

```bash
cd src/frontend
npm install
npm run dev
```

## Demo

```bash
bash scripts/run_demo.sh
```

## 🚀 Quick Start

### Start Backend

```bash
cd src/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd src/frontend
npm run dev
```

### Access Application

- **Web Interface**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs

## 🧪 Development Testing

```bash
# CLI comparison (for development)
cd src/backend
python compare_utils.py \
  --base ../../sample-input-scripts/base \
  --oracle ../../sample-input-scripts/oracle
```

## 📁 Project Structure

For detailed project organization, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 📄 Documentation

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Complete project organization
- **[docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)** - Architecture overview
- **[docs/INTERNAL_WORKINGS.md](docs/INTERNAL_WORKINGS.md)** - Technical implementation
- **[docs/DIFFICULTIES.md](docs/DIFFICULTIES.md)** - Known challenges and solutions
