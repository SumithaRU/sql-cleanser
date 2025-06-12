# SQL Cleanser - Complete Project Overview

## 🏗️ **System Architecture**

### **Components:**

- **Frontend (React + Vite)**: Web interface at `http://localhost:3000`
- **Backend (FastAPI)**: Processing engine at `http://localhost:8000`
- **AI Engine (Ollama + LLaMA 3)**: Smart analysis for primary keys and anomalies
- **Sample Data**: PostgreSQL scripts in `sample-scripts/base/`, Oracle scripts in `sample-scripts/clod/`

### **Technology Stack:**

- **Frontend**: React 18, TypeScript, Vite, Axios, React-Dropzone
- **Backend**: Python 3.13, FastAPI, Uvicorn, Pandas, NetworkX
- **AI/ML**: Ollama, LangChain, LLaMA 3:8b model
- **Database**: SQL parsing with regex and sqlparse
- **File Processing**: ZIP compression, multipart uploads

---

## 🔄 **Complete Workflow**

### **Step 1: Upload (Frontend)**

- User drags PostgreSQL `.sql` files into web interface
- React dropzone validates and queues files
- FormData sent to `/upload` endpoint via Axios

### **Step 2: Parse (Backend - ingest.py)**

```python
# Regex pattern for INSERT statements
INSERT_REGEX = r"INSERT\s+INTO\s+['\"]?(\w+)['\"]?\s*\((.*?)\)\s*VALUES\s*(\(.+\));"

# Process: Extract table, columns, values from each INSERT
# Output: Dictionary organized by table name
rows_by_table = {
    'users': [{'columns': ['id', 'name'], 'values': ['1', 'John'], 'source_file': 'users.sql'}],
    'orders': [{'columns': ['id', 'user_id'], 'values': ['1', '1'], 'source_file': 'orders.sql'}]
}
```

### **Step 3: AI Analysis (Backend - ollama_utils.py)**

```python
# Primary Key Inference using LLaMA 3
prompt = f"### Input\n{json.dumps(sample_data)}\n### Task\nReturn the most likely primary key columns as JSON list.\n### Output"
response = ollama_call(prompt)
primary_keys = json.loads(response)  # ['id'] or ['user_id', 'order_id']
```

### **Step 4: Duplicate Detection (Backend - fuzz.py)**

```python
# Hash-based duplicate detection
for row in rows:
    key = tuple(row['values'][row['columns'].index(col)] for col in primary_keys)
    key_hash = hashlib.sha256(str(key).encode()).hexdigest()
    if key_hash in seen:
        duplicates.append(row)
```

### **Step 5: Table Ordering (Backend - fuzz.py)**

```python
# NetworkX dependency graph based on foreign keys
G = nx.DiGraph()
for table, rows in rows_by_table.items():
    for col in rows[0]['columns']:
        if col.upper().endswith('_ID'):
            ref_table = col[:-3]  # user_id -> user
            if ref_table in rows_by_table:
                G.add_edge(ref_table, table)
order = list(nx.topological_sort(G))  # Dependency-ordered execution
```

### **Step 6: PostgreSQL → Oracle Transformation (Backend - transform.py)**

```python
# Syntax conversions:
PostgreSQL -> Oracle
-----------   ------
VARCHAR     -> VARCHAR2
NOW()       -> SYSDATE
NULL IDs    -> SEQUENCE.NEXTVAL
"quotes"    -> 'quotes'
lowercase   -> UPPERCASE

# Example output:
CREATE SEQUENCE USERS_SEQ START WITH 1;
INSERT INTO USERS (ID, NAME, CREATED_AT) VALUES (USERS_SEQ.NEXTVAL, 'JOHN', SYSDATE);
```

### **Step 7: AI Report Generation (Backend - ollama_utils.py)**

```python
# Anomaly analysis and remediation suggestions
prompt = f"### Input\n{json.dumps(anomalies)}\n### Task\nReturn remediation plan and markdown explanation in JSON with keys 'plan' and 'markdown'.\n### Output"
remediation = ollama_call(prompt)
# Generates human-readable markdown analysis
```

### **Step 8: ZIP & Download (Backend - main.py)**

- Oracle SQL files written to `output/` directory
- Markdown report generated with statistics and AI insights
- All files compressed into downloadable ZIP
- Frontend polls `/status/{job_id}` for progress updates

---

## 📁 **File Structure & Responsibilities**

```
sql-cleanser/
├── backend/
│   ├── main.py              # FastAPI app, job orchestration
│   ├── ingest.py            # SQL parsing, table extraction
│   ├── fuzz.py              # Duplicate detection, table ordering
│   ├── transform.py         # PostgreSQL → Oracle conversion
│   ├── ollama_utils.py      # AI integration (LLaMA 3)
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── main.tsx         # React entry point
│   │   ├── api.ts           # Backend communication
│   │   └── components/
│   │       ├── Dropzone.tsx # File upload interface
│   │       └── ProgressBar.tsx # Status visualization
│   ├── index.html           # HTML entry point
│   ├── vite.config.ts       # Vite configuration
│   └── package.json         # Node.js dependencies
├── sample-scripts/
│   ├── base/                # PostgreSQL sample files
│   └── clod/                # Oracle sample files (for comparison)
├── README.md                # Setup instructions
└── PROJECT_OVERVIEW.md      # This document
```

---

## 🔍 **Key Features & Capabilities**

### **Smart Analysis:**

- **AI-Powered Primary Key Detection**: LLaMA 3 analyzes sample data to infer likely primary keys
- **Dependency Graph Resolution**: NetworkX creates proper table execution order
- **Duplicate Detection**: Hash-based identification of duplicate rows
- **Syntax Translation**: Comprehensive PostgreSQL → Oracle conversion

### **Enterprise Features:**

- **Async Processing**: Background jobs with real-time progress tracking
- **Error Handling**: Graceful fallbacks and comprehensive error reporting
- **Scalable Architecture**: RESTful API design for integration
- **Human-Readable Reports**: AI-generated markdown analysis with remediation suggestions

### **Sample Data Insights:**

Your `sample-scripts/` contains business rule engine data:

- **Base (PostgreSQL)**: 7 files, ~550KB total
  - Business process definitions
  - Rule execution metadata
  - Switch/operator configurations
- **Clod (Oracle)**: 7 corresponding files for comparison testing

---

## 🚀 **Usage Instructions**

### **1. Start Services:**

```bash
# Terminal 1 - Backend
cd backend
$Env:OLLAMA_HOST='http://localhost:11434'
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev

# Terminal 3 - AI Engine
ollama serve  # (if not already running)
```

### **2. Access Application:**

- **Web Interface**: `http://localhost:3000`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/status/{job_id}`

### **3. Test Workflow:**

1. Drag PostgreSQL files from `sample-scripts/base/` into dropzone
2. Click "Upload" button
3. Monitor progress: parsing → AI analysis → transformation → reporting
4. Download ZIP with cleaned Oracle SQL + analysis report
5. Compare with existing `sample-scripts/clod/` files

### **4. Expected Output:**

- **Oracle SQL Files**: One per table with sequences and proper syntax
- **Report.md**: Detailed analysis including:
  - Row counts and duplicate statistics
  - AI-generated primary key inferences
  - Remediation suggestions for anomalies
  - Conversion summary and recommendations

---

## 🔧 **Advanced Configuration**

### **Ollama Model Tuning:**

```python
# Change model in ollama_utils.py
llm = Ollama(model='llama3:8b', base_url=OLLAMA_HOST, max_tokens=512)
# Available: llama3:8b, codellama:latest, custom fine-tuned models
```

### **Processing Customization:**

```python
# Modify transform.py for custom syntax rules
# Adjust fuzz.py for different duplicate detection strategies
# Extend ingest.py for additional SQL statement types
```

### **Frontend Customization:**

```typescript
// Modify vite.config.ts for different ports/proxies
// Extend App.tsx for additional UI features
// Customize Dropzone.tsx for different file types
```

---

## 🎯 **Next Steps & Potential Enhancements**

1. **Batch Processing**: Handle multiple PostgreSQL databases simultaneously
2. **Schema Validation**: Add DDL statement processing for table structures
3. **Performance Optimization**: Implement streaming for large files
4. **Advanced AI**: Fine-tune LLaMA for domain-specific SQL patterns
5. **Integration**: Add REST API endpoints for programmatic access
6. **Monitoring**: Implement logging and performance metrics
7. **Testing**: Add unit tests and integration test suite

---

## 🏁 **Ready to Use**

Your SQL Cleanser is now fully operational with:

- ✅ Frontend running on port 3000
- ✅ Backend API on port 8000
- ✅ Ollama AI service active
- ✅ Sample data ready for testing

**Go to `http://localhost:3000` and start cleaning your SQL!**
