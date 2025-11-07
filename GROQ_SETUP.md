# Groq Setup Guide

This project is configured to use **Groq** as the default LLM provider for fast, free inference.

## What is Groq?

Groq provides extremely fast LLM inference with generous free tier limits. Perfect for development and production use.

**Benefits:**
- ⚡ **Very Fast**: 10x faster than OpenAI
- 💰 **Free**: Generous free tier
- 🎯 **High Quality**: Uses Mixtral-8x7b and Llama models
- 🔒 **Reliable**: Enterprise-grade infrastructure

---

## Getting Your Groq API Key

### Step 1: Sign Up

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up with your email or GitHub account
3. Verify your email

### Step 2: Create API Key

1. Navigate to **API Keys** section
2. Click **"Create API Key"**
3. Name it (e.g., "fund-analysis-dev")
4. Copy the key (starts with `gsk-...`)

⚠️ **Important**: Save your API key securely - you won't be able to see it again!

---

## Configuration

### 1. Update `.env` File

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

### 2. Add Your Groq API Key

Update these lines in `.env`:

```bash
# LLM Provider (options: groq, openai, ollama, anthropic)
LLM_PROVIDER=groq

# Groq Configuration
GROQ_API_KEY=gsk-your-actual-key-here
GROQ_MODEL=mixtral-8x7b-32768

# Optional: OpenAI for embeddings (or leave blank to use HuggingFace local embeddings)
OPENAI_API_KEY=
```

### 3. Choose Embedding Model

#### Option A: Use OpenAI for Embeddings (Recommended)
Best quality, requires OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

#### Option B: Use Local Embeddings (Free)
Uses HuggingFace sentence-transformers locally:
```bash
# Leave OPENAI_API_KEY empty
OPENAI_API_KEY=
```
The system will automatically use `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).

---

## Available Groq Models

You can change the `GROQ_MODEL` in `.env` to use different models:

| Model | Description | Max Tokens | Best For |
|-------|-------------|------------|----------|
| **mixtral-8x7b-32768** | Mixtral 8x7B (default) | 32,768 | General purpose, best quality |
| **llama3-70b-8192** | Llama 3 70B | 8,192 | High quality, good reasoning |
| **llama3-8b-8192** | Llama 3 8B | 8,192 | Fast, efficient |
| **gemma-7b-it** | Google Gemma 7B | 8,192 | Lightweight, fast |

**Recommendation**: Stick with `mixtral-8x7b-32768` for best results.

---

## Verify Setup

### 1. Start the System

```bash
docker-compose up -d
```

### 2. Check Backend Logs

```bash
docker-compose logs backend | grep "Initializing LLM"
```

You should see:
```
INFO: Initializing LLM with provider: groq
```

### 3. Test Chat Endpoint

```bash
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is DPI?",
    "fund_id": null
  }'
```

If successful, you'll get a response with an answer!

---

## Troubleshooting

### Error: "GROQ_API_KEY not set in environment"

**Solution**: Check your `.env` file:
1. Ensure `GROQ_API_KEY=gsk-...` is present
2. Restart containers: `docker-compose restart backend`

### Error: "Failed to import LLM provider groq"

**Solution**: Install langchain-groq package:
```bash
docker-compose exec backend pip install langchain-groq
# Or rebuild containers
docker-compose up --build
```

### Slow Responses

Groq is usually very fast (<1 second). If slow:
1. Check your internet connection
2. Verify API key is valid: [https://console.groq.com/keys](https://console.groq.com/keys)
3. Check Groq status: [https://status.groq.com](https://status.groq.com)

### Rate Limits

Free tier limits:
- **14,400 requests/day**
- **30 requests/minute**

For higher limits, check Groq pricing plans.

---

## Alternative LLM Providers

If you prefer a different provider, change `LLM_PROVIDER` in `.env`:

### OpenAI (GPT-4)
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

### Ollama (Local)
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Install Ollama first:
# brew install ollama  # Mac
# curl -fsSL https://ollama.com/install.sh | sh  # Linux
```

### Anthropic (Claude)
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Cost Comparison

| Provider | Cost (per 1M tokens) | Speed | Quality | Free Tier |
|----------|---------------------|-------|---------|-----------|
| **Groq** | **FREE** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ✅ Generous |
| OpenAI GPT-4 | $30 | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | $5 credit |
| Ollama | FREE | ⚡⚡ | ⭐⭐⭐ | ✅ Unlimited |
| Anthropic | $15 | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Limited |

**For this project**: Groq offers the best balance of cost, speed, and quality!

---

## Example Queries

Once setup is complete, try these queries in the chat interface:

### Definitions
```
"What does DPI mean?"
"Explain Internal Rate of Return"
"What is Paid-In Capital?"
```

### Calculations (requires fund with data)
```
"What is the current DPI for this fund?"
"Calculate the IRR"
"Has the fund returned all capital to LPs?"
```

### Data Retrieval
```
"Show me all capital calls in 2024"
"What was the largest distribution?"
"List all adjustments"
```

---

## Support

- **Groq Documentation**: [https://console.groq.com/docs](https://console.groq.com/docs)
- **Groq Community**: [https://groq.com/community](https://groq.com/community)
- **Project Issues**: Open an issue in this repository

---

**You're all set! 🚀**

The system is configured to use Groq for fast, free LLM inference. Upload a PDF and start asking questions!
