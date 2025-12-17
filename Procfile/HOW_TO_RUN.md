# SHL GenAI Recommendation Engine - Quick Start Guide

## 🚀 How to Run the Application

### Method 1: Windows Batch File (Easiest)
```bash
start_app.bat
```

### Method 2: Run Services Separately (Recommended)

#### Terminal 1: Start FastAPI Backend
```bash
cd "d:\SHL\Procfile"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Start Streamlit Frontend (in NEW terminal window)
```bash
cd "d:\SHL\Procfile"
python -m streamlit run frontend/app.py --server.port 8501
```

### Method 3: Combined Python Script
```bash
python run_app.py
```

### Method 3: Direct Python Execution
```bash
# Backend only
python main.py

# Frontend only  
python -m streamlit run frontend/app.py
```

## 🔗 Access URLs

- **Streamlit Web App**: http://localhost:8501
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🧪 Testing Commands

### Test the System
```bash
python test_quick.py                # Quick functionality test
python test_system_direct.py        # Comprehensive system test
python test_api_endpoints.py        # API endpoints test
```

### Test API Directly
```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Get recommendations
curl -X POST "http://localhost:8000/recommend" \
     -H "Content-Type: application/json" \
     -d '{"query": "Java developer with collaboration skills"}'
```

## 🐛 Common Issues & Fixes

### Issue 1: "Empty black screen in Streamlit"
**Cause**: Running `streamlit run main.py` (wrong file)  
**Fix**: Use `streamlit run frontend/app.py`

### Issue 2: "Port already in use"
**Fix**: Kill existing processes
```bash
taskkill /F /IM python.exe
taskkill /F /IM streamlit.exe
```

### Issue 3: "Google API quota exceeded"
**Fix**: System has fallback logic, still works without LLM

### Issue 4: "Module not found"
**Fix**: Install dependencies
```bash
pip install -r requirements.txt
```

## 📊 Expected Output

### Streamlit Frontend
- Search interface for job descriptions
- Table showing recommended assessments
- Export functionality

### API Response Format
```json
{
  "recommended_assessments": [
    {
      "name": "Java 8 (New)",
      "description": "Programming & Development - Java programming language assessment",
      "test_type": "K",
      "relevance_score": 0.85
    }
  ]
}
```

## 🎯 For Submission

1. **Streamlit URL**: http://localhost:8501 (or deployed URL)
2. **API Endpoint**: http://localhost:8000/recommend