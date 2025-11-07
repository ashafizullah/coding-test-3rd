# Fund Performance Analysis System

**Coding Test - Adam Suchi Hafizullah**
LinkedIn: [https://www.linkedin.com/in/ashafizullah/](https://www.linkedin.com/in/ashafizullah/)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Groq API Key (Free) - Get from: https://console.groq.com

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd coding-test-3rd
```

2. **Set up environment variables**
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your-key-here
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Wait for initialization** (first time only, ~30 seconds)
```bash
# Check logs to see when ready
docker-compose logs -f backend

# You should see: "Database tables created successfully!"
```

5. **Access the application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📚 How to Use

### 1. Create/Upload Fund Data

**Option A: Create New Fund**
1. Go to http://localhost:3000/upload
2. Click "Create New Fund" tab
3. Fill in fund details (name, GP name, vintage year)
4. Click "Create Fund"

**Option B: Use Existing Fund**
1. Go to http://localhost:3000/upload
2. Select a fund from dropdown
3. Drag & drop PDF or click to browse
4. Wait for processing (check status at /documents)

### 2. View Fund Portfolio
- Go to http://localhost:3000/funds
- See all funds with metrics (DPI, IRR, PIC)
- Click "View Details" for detailed analysis
- Export to Excel if needed

### 3. Chat with Your Data
- Go to http://localhost:3000/chat
- Select a fund from dropdown
- Ask questions like:
  - "What is the current DPI?"
  - "Calculate the IRR for this fund"
  - "Show me all capital calls in 2024"
  - "What does Paid-In Capital mean?"

### 4. View Documents
- Go to http://localhost:3000/documents
- See all uploaded documents
- Check parsing status
- Delete documents if needed

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 with pgvector
- **Cache/Queue**: Redis + Celery
- **LLM**: Groq (llama-3.3-70b-versatile)
- **Embeddings**: OpenAI text-embedding-3-small
- **PDF Parser**: pdfplumber + LLM fallback

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI**: Tailwind CSS
- **State**: TanStack Query
- **Charts**: Recharts
- **Alerts**: SweetAlert2

### Infrastructure
- **Containerization**: Docker Compose
- **Services**: 4 containers (postgres, redis, backend, celery_worker, frontend)

---

## 📊 Features Implemented

### ✅ Core Features
- [x] PDF document upload and parsing
- [x] Automatic table extraction (capital calls, distributions, adjustments)
- [x] LLM-based text extraction fallback
- [x] Vector storage with pgvector
- [x] RAG (Retrieval Augmented Generation) Q&A
- [x] Fund metrics calculation (DPI, IRR, PIC, NAV, TVPI, RVPI)
- [x] Conversation history per fund

### ✅ Advanced Features
- [x] Multi-fund support with fund selector
- [x] Interactive dashboard with charts
- [x] Excel export (multi-sheet reports)
- [x] Markdown rendering in chat
- [x] Document pagination (10 per page)
- [x] Delete with cascade (fund → documents)
- [x] SweetAlert2 confirmations
- [x] Real-time processing status
- [x] Error handling with user-friendly messages

### ✅ UI/UX
- [x] Responsive design
- [x] Loading states
- [x] Success/error notifications
- [x] Empty states with helpful messages
- [x] Sample questions in chat
- [x] Footer with credits

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                   │
│         Upload → Funds → Documents → Chat               │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────┐
│                 Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Document Processor → Table Parser → Embeddings │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Query Engine → RAG → LLM → Metrics Calculator   │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────────┐ ┌────▼─────┐ ┌────────▼────────┐
│   PostgreSQL   │ │  Redis   │ │  Celery Worker  │
│  + pgvector    │ │  Cache   │ │  Background     │
└────────────────┘ └──────────┘ └─────────────────┘
```

---

## 🔧 Useful Commands

### Docker Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Restart a service
docker-compose restart backend

# Rebuild containers
docker-compose up -d --build

# Check status
docker-compose ps
```

### Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U funduser -d funddb

# List tables
\dt

# Check funds
SELECT * FROM funds;

# Check documents
SELECT * FROM documents;
```

### Cleanup
```bash
# Stop and remove everything (including volumes)
docker-compose down -v

# Remove unused Docker resources
docker system prune -a
```

---

## 📝 API Endpoints

### Documents
```
POST   /api/documents/upload          # Upload PDF
GET    /api/documents/                # List documents
GET    /api/documents/{id}/status     # Check parsing status
DELETE /api/documents/{id}            # Delete document
```

### Funds
```
GET    /api/funds/                    # List all funds
POST   /api/funds/                    # Create fund
GET    /api/funds/{id}                # Get fund details
DELETE /api/funds/{id}                # Delete fund (cascade)
GET    /api/funds/{id}/transactions   # Get transactions
GET    /api/funds/{id}/metrics        # Get calculated metrics
GET    /api/funds/{id}/export         # Export to Excel
```

### Chat
```
POST   /api/chat/query                # Ask question
POST   /api/chat/conversations        # Create conversation
GET    /api/chat/conversations/{id}   # Get conversation
```

Full API documentation: http://localhost:8000/docs

---

## 🧪 Sample Data

### Test with Sample PDF
1. Upload a fund performance report PDF
2. PDF should contain tables with:
   - **Capital Calls**: Date, Amount, Description
   - **Distributions**: Date, Amount, Type, Recallable
   - **Adjustments**: Date, Amount, Type

### Sample Questions
```
# Definitions
"What does DPI mean?"
"Explain Paid-In Capital"
"What is a recallable distribution?"

# Calculations
"What is the current DPI?"
"Calculate the IRR for this fund"
"Show me the NAV"

# Data Retrieval
"Show me all capital calls in 2024"
"What was the largest distribution?"
"List all transactions"
```

---

## ⚙️ Environment Variables

### Required
```bash
# LLM Provider
LLM_PROVIDER=groq                     # groq, openai, anthropic, ollama

# Groq (Free, Recommended)
GROQ_API_KEY=gsk-your-key-here
GROQ_MODEL=llama-3.3-70b-versatile
```

### Optional
```bash
# OpenAI (for embeddings, optional)
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Ollama (local LLM, optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Anthropic (optional)
ANTHROPIC_API_KEY=your-key-here
```

See `.env.example` for full configuration.

---

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Common issues:
# 1. Port already in use → Change ports in docker-compose.yml
# 2. Out of disk space → docker system prune -a
# 3. Old containers running → docker-compose down -v
```

### Frontend can't connect to backend
```bash
# Check backend is running
curl http://localhost:8000/docs

# Check CORS settings in backend/app/main.py
# Should allow http://localhost:3000
```

### Document parsing fails
```bash
# Check celery worker logs
docker-compose logs -f celery_worker

# Common issues:
# 1. Invalid PDF format → Try different PDF
# 2. Missing API keys → Check .env
# 3. Model deprecated → Update GROQ_MODEL in docker-compose.yml
```

### Database connection error
```bash
# Wait for postgres to be ready
docker-compose logs postgres

# Check health
docker-compose ps

# All services should show "Up (healthy)"
```

---

## 📦 Project Structure

```
coding-test-3rd/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/       # API routes
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/            # Business logic
│   │   ├── schemas/             # Pydantic schemas
│   │   └── main.py              # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                     # Next.js 14 pages
│   │   ├── upload/
│   │   ├── funds/
│   │   ├── documents/
│   │   └── chat/
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 📄 License

This project is created as a coding test submission.

---

## 👤 Author

**Adam Suchi Hafizullah**
LinkedIn: [https://www.linkedin.com/in/ashafizullah/](https://www.linkedin.com/in/ashafizullah/)

---

## 🙏 Acknowledgments

- Built with FastAPI, Next.js, PostgreSQL, and Redis
- Uses Groq for fast LLM inference (free tier)
- Implements RAG with pgvector for semantic search
- UI components styled with Tailwind CSS

---

**Last Updated**: 2025-01-07
