# SQL Cleanser - Project Structure

This document outlines the organized structure of the SQL Cleanser project.

## 📁 Directory Structure

```
sql-cleanser/
├── 📁 config/                     # Configuration files
│   └── app_settings.yaml          # Application settings and parameters
├── 📁 docs/                       # Project documentation
│   ├── DIFFICULTIES.md            # Known challenges and solutions
│   ├── INTERNAL_WORKINGS.md       # Technical implementation details
│   └── PROJECT_OVERVIEW.md        # High-level architecture overview
├── 📁 logs/                       # Application logs (runtime generated)
│   └── .gitkeep                   # Maintains directory in version control
├── 📁 results/                    # Processing outputs (runtime generated)
│   └── .gitkeep                   # Maintains directory in version control
├── 📁 sample-input-scripts/       # Example SQL files for testing
│   ├── 📁 base/                   # PostgreSQL sample scripts
│   └── 📁 oracle/                 # Oracle sample scripts
├── 📁 scripts/                    # Utility and demo scripts
│   ├── demo_local.sh              # Local development demo
│   ├── run_demo.sh                # Main demo script
│   └── verify.sh                  # Verification script
├── 📁 src/                        # Source code
│   ├── 📁 backend/                # FastAPI backend application
│   │   ├── compare_utils.py       # Data comparison and analysis
│   │   ├── fuzz.py                # AI-powered duplicate detection
│   │   ├── ingest.py              # SQL parsing and data extraction
│   │   ├── main.py                # FastAPI application and endpoints
│   │   ├── ollama_utils.py        # AI/LLM integration utilities
│   │   ├── requirements.txt       # Python dependencies
│   │   ├── tests/                 # Backend unit tests
│   │   └── transform.py           # PostgreSQL to Oracle transformation
│   └── 📁 frontend/               # React frontend application
│       ├── 📁 src/                # Frontend source code
│       │   ├── App.tsx            # Main React component
│       │   ├── api.ts             # API communication layer
│       │   ├── components/        # Reusable UI components
│       │   └── main.tsx           # Application entry point
│       ├── index.html             # HTML template
│       ├── package.json           # Node.js dependencies
│       ├── tsconfig.json          # TypeScript configuration
│       └── vite.config.ts         # Vite build configuration
├── .gitignore                     # Git ignore rules
├── PROJECT_STRUCTURE.md           # This file
└── README.md                      # Project overview and setup
```

## 🚀 Key Components

### **Backend (FastAPI + AI)**

- **AI-Powered Analysis**: Ollama LLaMA 3 8B for intelligent data processing
- **Smart Duplicate Detection**: Fuzzy matching and semantic analysis
- **PostgreSQL → Oracle Conversion**: Automated syntax transformation
- **Comprehensive Reporting**: Detailed analysis and migration plans

### **Frontend (React + TypeScript)**

- **Modern UI**: Drag-and-drop file upload interface
- **Real-time Progress**: Live status updates during processing
- **Responsive Design**: Works on desktop and mobile devices
- **Type Safety**: Full TypeScript implementation

### **AI Features**

- **Primary Key Inference**: Intelligent detection of table relationships
- **Duplicate Analysis**: Semantic and fuzzy duplicate identification
- **Data Quality Assessment**: Business logic validation
- **Migration Planning**: AI-generated step-by-step guides

## 📊 Data Flow

1. **Upload** → Files uploaded via React frontend
2. **Parse** → SQL statements extracted and analyzed
3. **AI Analysis** → LLM processes data for insights
4. **Transform** → PostgreSQL syntax converted to Oracle
5. **Report** → Comprehensive analysis and results generated
6. **Download** → ZIP package with all outputs

## 🛠️ Development

- **Backend**: Python 3.8+ with FastAPI
- **Frontend**: Node.js 16+ with React + Vite
- **AI**: Ollama with LLaMA 3 8B model
- **Dependencies**: Managed via requirements.txt and package.json

## 📋 Generated Outputs

All processing results are organized in the `results/` directory:

```
results/{job-id}/
├── 📁 oracle_sql/              # Converted Oracle SQL files
├── 📁 reports/                 # AI-generated analysis reports
├── 📁 metadata/                # Processing logs and details
└── output.zip                  # Complete results package
```

## 🧹 Maintenance

- **Logs**: Automatically managed in `logs/` directory
- **Cache**: Python cache and build artifacts excluded via .gitignore
- **Results**: Generated files excluded from version control
- **Cleanup**: Temporary files automatically removed after processing
