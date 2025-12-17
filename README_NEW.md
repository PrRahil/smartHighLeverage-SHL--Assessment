# 🎯 SHL GenAI Recommendation Engine

A sophisticated web-based RAG (Retrieval Augmented Generation) system that recommends Individual Test Solutions from SHL's catalog using Google Gemini Pro and ChromaDB.

## 📋 Project Overview

This system scrapes SHL's assessment catalog, filters for Individual Test Solutions (excluding pre-packaged job solutions), and provides intelligent recommendations using semantic search combined with LLM refinement.

### ✨ Key Features

- **Deep Web Scraping**: Extracts 377+ individual assessments from SHL catalog
- **RAG Architecture**: ChromaDB for vector storage + Google Gemini for intelligent refinement
- **Balance Logic**: Automatically balances technical and soft skill recommendations
- **RESTful API**: FastAPI backend with strict schema compliance
- **Web Interface**: Streamlit frontend for interactive testing
- **Submission Generator**: Creates CSV outputs in required stacked format

## 🏗️ Tech Stack

- **LLM**: Google Gemini Pro (Free Tier)
- **Scraping**: Selenium + BeautifulSoup
- **Vector DB**: ChromaDB (Persistent)
- **Framework**: LangChain (RAG flow)
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and enter directory
cd D:\SHL

# Install dependencies
pip install -r requirements.txt

# Setup ChromeDriver and validate environment
python setup.py
```

### 2. Configure API Keys

Edit `.env` file and add your Google Gemini API key:
```
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### 3. Scrape SHL Data (Optional - sample data included)

```bash
# Run the scraper to get fresh data
python run_scraper.py
```

### 4. Start the System

```bash
# Option 1: Start FastAPI backend
python main.py

# Option 2: Start Streamlit frontend (in new terminal)
streamlit run frontend/app.py

# Option 3: Generate submission CSV
python evaluate.py
```

## 📁 Project Structure

```
SHL/
├── src/
│   ├── scraper.py          # Deep scraping logic
│   ├── rag_engine.py       # RAG + balance logic
│   ├── config.py           # Configuration management
│   ├── evaluate.py         # Submission generator
│   ├── models/             # Pydantic models
│   └── utils/              # Utility functions
├── frontend/
│   └── app.py              # Streamlit web interface
├── data/                   # CSV data files
├── chroma_db/              # Vector database
├── logs/                   # Application logs
├── main.py                 # FastAPI server
├── setup.py                # Environment setup
├── run_scraper.py          # Scraper runner
├── evaluate.py             # Evaluation runner
├── requirements.txt        # Dependencies
└── .env                    # Environment variables
```

## 🔧 API Endpoints

### Health Check
```bash
GET /health
Response: {"status": "healthy"}
```

### Get Recommendations
```bash
POST /recommend
Request: {"query": "software developer with Java skills"}
Response: {
  "recommended_assessments": [
    {
      "url": "string",
      "name": "string", 
      "adaptive_support": "Yes/No",
      "description": "string",
      "duration": int,
      "remote_support": "Yes/No",
      "test_type": ["string", "string"]
    }
  ]
}
```

## 🎯 Balance Logic

The system implements sophisticated balance logic:

- **Technical + Soft Skills Query**: Returns mix of "Knowledge & Skills" and "Personality & Behavior" tests
- **Technical Only**: Emphasizes "Knowledge & Skills" assessments
- **Soft Skills Only**: Emphasizes "Personality & Behavior" assessments
- **General Queries**: Balanced recommendations based on semantic similarity

## 📊 Sample Queries

```
"Software developer with Java and Python programming skills"
"Leadership assessment for management roles"  
"Customer service representative with communication skills"
"Data analyst with technical and analytical abilities"
"Project manager with both technical and leadership skills"
```

## 🔍 Scraper Details

The scraper targets: `https://www.shl.com/solutions/products/product-catalog/`

**Filtering Logic**:
- ✅ Include: Individual Test Solutions
- ❌ Exclude: Pre-packaged Job Solutions
- 🎯 Target: 377+ assessments minimum

**Extracted Fields**:
- Name, URL, Description
- Duration (integer minutes)
- Adaptive Support (Yes/No)
- Remote Support (Yes/No)  
- Test Types (array)

## 📈 RAG Workflow

1. **Ingestion**: Load CSV data into ChromaDB with metadata
2. **Embedding**: Generate vectors using sentence-transformers
3. **Retrieval**: Get top 25 semantic matches
4. **Refinement**: Google Gemini selects final 5-10 with balance logic
5. **Response**: Return structured JSON

## 🏃‍♂️ Running Components

### Scraper Only
```bash
python run_scraper.py
```

### API Server Only  
```bash
python main.py
# API available at: http://localhost:8000
```

### Frontend Only
```bash
streamlit run frontend/app.py
# Web UI available at: http://localhost:8501
```

### Generate Submission
```bash
python evaluate.py [test_file.xlsx]
# Output: data/submission.csv (stacked format)
```

## 📝 Submission Format

The evaluation script generates CSV in required stacked format:

```csv
Query,Assessment_url
"Query 1","http://url1..."
"Query 1","http://url2..." 
"Query 1","http://url3..."
"Query 2","http://url1..."
```

## 🔒 Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional (with defaults)
CHROMA_DB_PATH=./chroma_db
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
TOP_K_RETRIEVAL=25
FINAL_RECOMMENDATIONS=8
```

## 🐛 Troubleshooting

### Common Issues

1. **ChromeDriver Error**: Run `python setup.py` to install
2. **Tensorflow Warnings**: Install `tf-keras` if needed
3. **API Key Error**: Ensure `GOOGLE_API_KEY` is set in `.env`
4. **Scraping Fails**: Check internet connection and site availability
5. **Vector DB Error**: Delete `chroma_db/` folder and restart

### Logging

Check logs in `logs/shl_app.log` for detailed error information.

## 🚀 Deployment

### Railway/Render Deployment

1. Add environment variables in platform
2. Update requirements.txt if needed
3. Use `main.py` as entry point
4. Ensure port configuration matches platform

### Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 📜 License

This project is for SHL internship assessment purposes.

## 🤝 Support

For issues or questions, check the logs directory or review the configuration in `src/config.py`.

---

**🎉 Ready to recommend! The system will only require you to update the `.env` file with your API keys.**