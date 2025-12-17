# 🚀 **SHL Assessment System - Complete Deployment Guide**

## **📋 Submission Checklist**

### **Required Deliverables:**
- ✅ **API Endpoint** (Railway/Render deployment)
- ✅ **GitHub Repository** (public/private with access)
- ✅ **Web Application** (Streamlit frontend)
- ✅ **2-page Solution Document** (SOLUTION_APPROACH.md)
- ✅ **CSV Predictions** (test set results)

## **🎯 Step-by-Step Deployment Process**

### **Step 1: Get Google Gemini API Key**
1. Go to https://ai.google.dev/
2. Sign in with Google account
3. Create new API key
4. Copy the key

### **Step 2: Configure Environment**
```bash
# Edit .env file
GOOGLE_API_KEY=your_actual_api_key_here
```

### **Step 3: Test Locally**
```bash
# Test the system
python setup.py
python quickstart.py

# Choose option 2 to start FastAPI
# Choose option 3 to start Streamlit
```

### **Step 4: Deploy API (Railway)**

1. **Create Railway Account**: https://railway.app/
2. **Connect GitHub Repository**
3. **Add Environment Variables**:
   ```
   GOOGLE_API_KEY=your_actual_key
   PORT=8000
   ```
4. **Deploy**: Railway auto-deploys from main branch

### **Step 5: Deploy Frontend (Streamlit Cloud)**

1. **Create Streamlit Account**: https://share.streamlit.io/
2. **Connect Repository**  
3. **Set Main File**: `frontend/app.py`
4. **Add Secrets**:
   ```toml
   [secrets]
   GOOGLE_API_KEY = "your_key_here"
   ```

### **Step 6: Generate Test Predictions**
```bash
# Run evaluation on test dataset
python evaluate.py test_dataset.xlsx
```

### **Step 7: GitHub Repository Setup**
```bash
# Initialize git (if not done)
git init
git add .
git commit -m "Initial SHL Assessment System"
git branch -M main
git remote add origin https://github.com/yourusername/shl-assessment.git
git push -u origin main
```

## **🌐 Deployment Platforms**

### **Option 1: Railway (Recommended for API)**
- **Pros**: Easy Python deployment, free tier, automatic SSL
- **Setup**: Connect GitHub → Set env vars → Deploy
- **URL Format**: `https://your-app.railway.app`

### **Option 2: Render**
- **Pros**: Free tier, good for both API and web apps
- **Setup**: Connect GitHub → Create web service → Set env vars
- **URL Format**: `https://your-app.onrender.com`

### **Option 3: Heroku**
- **Pros**: Mature platform, extensive documentation
- **Cons**: Limited free tier
- **Setup**: Heroku CLI deployment with Procfile

## **📝 API Testing Commands**

### **Health Check**
```bash
curl https://your-api-url.railway.app/health
```

### **Recommendation Test**
```bash
curl -X POST "https://your-api-url.railway.app/recommend" \
     -H "Content-Type: application/json" \
     -d '{"query": "Java developer with team collaboration skills"}'
```

## **🔍 Final Validation Steps**

### **Before Submission:**
1. ✅ API responds correctly to both endpoints
2. ✅ Web app loads and functions properly  
3. ✅ CSV file generated in correct format
4. ✅ GitHub repository is accessible
5. ✅ Documentation is complete

### **Submission URLs Format:**
```
API Endpoint: https://your-app.railway.app
GitHub Repo: https://github.com/yourusername/shl-assessment
Web App: https://your-app.streamlit.app
```

## **🐛 Troubleshooting**

### **Common Issues:**

1. **API Key Error**: Ensure GOOGLE_API_KEY is set correctly
2. **Port Issues**: Use PORT environment variable for deployment
3. **Dependency Issues**: Ensure requirements.txt is up to date
4. **Memory Errors**: ChromaDB may need optimization for free tiers

### **Quick Fixes:**
```bash
# Reset ChromaDB if issues
rm -rf chroma_db/

# Test API locally first
python main.py

# Check logs
tail -f logs/shl_app.log
```

## **⚡ Quick Deploy Commands**

```bash
# Complete setup in 5 commands
git add .
git commit -m "Deploy SHL System"
git push origin main
# Then deploy on Railway/Render via web interface
python evaluate.py  # Generate CSV predictions
```

**🎉 Ready for submission once all URLs are working and CSV is generated!**