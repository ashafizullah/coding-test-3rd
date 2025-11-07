# Quick Start Guide

Get the Fund Performance Analysis System running in **5 minutes**!

---

## Prerequisites

- Docker Desktop installed
- Groq API key (free) - [Get it here](https://console.groq.com)

---

## Step 1: Clone & Configure (2 minutes)

```bash
# Clone the repository
git clone <repository-url>
cd fund-analysis-system

# Copy environment file
cp .env.example .env

# Edit .env and add your Groq API key
nano .env
```

**Update this line in `.env`:**
```bash
GROQ_API_KEY=gsk-your-actual-key-here
```

**Optional**: Add OpenAI key for better embeddings:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
```
(If omitted, will use free local embeddings)

---

## Step 2: Start Services (2 minutes)

```bash
# Start all services (PostgreSQL, Redis, Backend, Celery, Frontend)
docker-compose up -d

# Wait ~30 seconds for services to initialize
# Check logs
docker-compose logs -f backend
```

**You should see:**
```
INFO: Initializing LLM with provider: groq
INFO: Vector store initialized with dimension 1536
INFO: Application startup complete
```

**Services running:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Step 3: Upload Sample Document (1 minute)

### Option A: Via Web UI

1. Open http://localhost:3000/upload
2. Drag and drop `files/Sample_Fund_Performance_Report.pdf`
3. Wait for "Processing Complete" status (~10-30 seconds)

### Option B: Via API

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@files/Sample_Fund_Performance_Report.pdf" \
  -F "fund_id="
```

---

## Step 4: Try It Out!

### View Fund Dashboard

1. Go to http://localhost:3000/funds
2. Click on "Tech Ventures Fund III"
3. See:
   - ✅ Metrics: DPI 0.39x, IRR 12.5%
   - ✅ Cash Flow Chart
   - ✅ Transaction Tables

### Ask Questions

1. Go to http://localhost:3000/chat
2. Try these questions:

**Definitions:**
```
"What does DPI mean?"
"Explain Internal Rate of Return"
```

**Calculations:**
```
"What is the current DPI for this fund?"
"Calculate the IRR"
```

**Data Retrieval:**
```
"Show me all capital calls"
"What was the largest distribution?"
```

### Export to Excel

1. Go to Fund Detail Page
2. Look for "Export" button (or visit: `http://localhost:8000/api/funds/1/export`)
3. Download comprehensive Excel report with 5 sheets!

---

## Troubleshooting

### Services not starting?

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

### Backend errors?

```bash
# Check environment variables
docker-compose exec backend env | grep GROQ

# Restart backend
docker-compose restart backend

# View real-time logs
docker-compose logs -f backend
```

### Frontend not loading?

```bash
# Check if backend is running
curl http://localhost:8000/health

# Restart frontend
docker-compose restart frontend
```

### Groq API errors?

1. Verify API key: https://console.groq.com/keys
2. Check you copied the full key (starts with `gsk-`)
3. Restart backend after updating `.env`

---

## What's Next?

### Upload Your Own PDFs

The system can parse any fund performance report with tables for:
- Capital Calls
- Distributions
- Adjustments

**Table Requirements:**
- Headers must include keywords like "Date", "Amount", "Type"
- Dates in format: YYYY-MM-DD or MM/DD/YYYY
- Amounts with or without $ signs

### Try Advanced Features

**Multiple Funds:**
```bash
# Create a new fund
curl -X POST "http://localhost:8000/api/funds" \
  -H "Content-Type: application/json" \
  -d '{"name": "Growth Fund II", "gp_name": "Acme Partners", "vintage_year": 2024}'

# Upload another PDF for this fund
```

**Excel Reports:**
- Each fund can export a comprehensive Excel workbook
- Includes all transactions, metrics breakdown, and calculations

**Chat History:**
- Conversations maintain context
- Ask follow-up questions naturally

---

## Sample Queries for Testing

### Definitions (Test RAG)
```
"What is Paid-In Capital?"
"Define recallable distribution"
"What does TVPI stand for?"
```

### Calculations (Test Metrics)
```
"What is the fund's DPI?"
"Calculate the IRR for this fund"
"Has the fund returned all capital?"
"What percentage of capital has been distributed?"
```

### Data Retrieval (Test SQL)
```
"Show me all capital calls in 2024"
"List distributions over $1 million"
"What were the adjustments?"
```

### Complex Queries (Test RAG + Calculations)
```
"How is this fund performing compared to typical PE benchmarks?"
"Explain the trend in capital calls"
"What factors contributed to the IRR?"
```

---

## API Testing

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# List funds
curl http://localhost:8000/api/funds

# Get fund metrics
curl http://localhost:8000/api/funds/1/metrics

# Chat query
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is DPI?", "fund_id": 1}'

# Export Excel
curl http://localhost:8000/api/funds/1/export -o fund_report.xlsx
```

### Using API Docs

Visit http://localhost:8000/docs for interactive Swagger documentation!

---

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove all data (fresh start)
docker-compose down -v
```

---

## Need Help?

1. **Check logs first:**
   ```bash
   docker-compose logs backend
   docker-compose logs celery_worker
   ```

2. **Common issues:**
   - Missing API key → Check `.env` file
   - Port conflicts → Change ports in `docker-compose.yml`
   - Out of memory → Increase Docker memory limit

3. **Documentation:**
   - [Groq Setup Guide](GROQ_SETUP.md)
   - [Complete Setup Guide](SETUP.md)
   - [Features List](FEATURES.md)

4. **GitHub Issues:**
   - Open an issue for bugs or questions

---

## Performance Expectations

**Document Processing:**
- Small PDF (5-10 pages): 10-30 seconds
- Large PDF (20+ pages): 30-60 seconds

**Query Response:**
- Definitions: <1 second (Groq is fast!)
- Calculations: 1-2 seconds (includes SQL + LLM)
- Complex queries: 2-3 seconds

**Excel Export:**
- Any fund size: <2 seconds

---

## Success Checklist

- [ ] Docker services running (4 containers)
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend API responding at http://localhost:8000
- [ ] Sample PDF uploaded successfully
- [ ] Fund dashboard shows metrics
- [ ] Chat interface returns answers
- [ ] Excel export downloads

**All checked?** 🎉 **You're ready to go!**

---

**Happy analyzing! 📊**
