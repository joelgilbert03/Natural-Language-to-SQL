# Quick Start Guide - NL2SQL System

Get your NL2SQL system up and running in 10 minutes!

## Prerequisites

✅ Python 3.10+  
✅ PostgreSQL database (Neon recommended)  
✅ API keys ready (see below)

## Step 1: Clone & Setup (2 min)

```bash
# Clone the repository
git clone <your-repo-url>
cd nl2sql-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Get API Keys (3 min)

### Groq API (FREE)
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up with Google/GitHub
3. Create API Key → Copy it
4. Free tier: 30 requests/min

### Cloudflare Workers AI (FREE)
1. Visit [dash.cloudflare.com](https://dash.cloudflare.com)
2. Go to AI → Workers AI
3. Get Account ID from overview
4. Create API Token → Copy it
5. Free tier: 10,000 requests/day

### Upstash Vector (FREE)
1. Visit [console.upstash.com](https://console.upstash.com)
2. Create Vector Index
3. Dimension: 384 (for text embeddings)
4. Copy URL and Token
5. Free tier: 10,000 queries/day

### Neon PostgreSQL (FREE)
1. Visit [neon.tech](https://neon.tech)
2. Create new project
3. Copy connection string
4. Create read-only user:
```sql
CREATE USER readonly_user WITH PASSWORD 'your_password';
GRANT CONNECT ON DATABASE your_db TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

## Step 3: Configure Environment (2 min)

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values
nano .env  # or use your favorite editor
```

**Minimal .env configuration:**
```env
# Database (use same for both if you don't have separate users)
NEON_READONLY_CONNECTION_STRING=postgresql://user:pass@host/db?sslmode=require
NEON_DBA_CONNECTION_STRING=postgresql://user:pass@host/db?sslmode=require

# API Keys (paste the ones you got)
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
CLOUDFLARE_ACCOUNT_ID=xxxxxxxxxxxxx
CLOUDFLARE_AUTH_TOKEN=xxxxxxxxxxxxx

# Upstash Vector
UPSTASH_VECTOR_URL=https://xxxxx.upstash.io
UPSTASH_VECTOR_TOKEN=xxxxxxxxxxxxx

# Security
DBA_PASSWORD=choose_a_strong_password

# App Settings
APP_ENV=development
LOG_LEVEL=INFO
```

## Step 4: Initialize Vector Store (2 min)

```bash
# This populates Upstash with your database schema
python scripts/init_vector_store.py
```

You should see:
```
✅ Database connection successful
✅ Upstash Vector initialized
✅ Found X tables
✅ Successfully stored X schemas
✅ Search test successful!
```

## Step 5: Run the App (1 min)

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 🎉 You're Ready!

Try these example queries:

**Simple:**
- "How many users do we have?"
- "Show me all active customers"

**Aggregated:**
- "Total sales by region"
- "Average order value per customer"

**Time-based:**
- "Sales in the last 7 days"
- "New users this month"

## 🔧 Troubleshooting

### Can't connect to database?
```bash
# Test your connection string
psql "postgresql://user:pass@host/db?sslmode=require"
```

### Vector store initialization fails?
- Check Upstash credentials in .env
- Verify database has tables
- Run with debug: `LOG_LEVEL=DEBUG python scripts/init_vector_store.py`

### Streamlit won't start?
```bash
# Verify all dependencies
pip install -r requirements.txt --upgrade

# Check for Python errors
python app.py
```

### API rate limits?
- Free tiers have limits
- Groq: 30 req/min
- Cloudflare: 10,000 req/day
- Upstash: 10,000 queries/day

### Nothing happens when I ask a question?
- Check browser console (F12) for errors
- Check terminal for Python errors
- Verify API keys are correct
- Check LOG_LEVEL=DEBUG in .env for detailed logs

## 🚀 Next Steps

1. ✅ **Test DBA Mode** - Login with your DBA_PASSWORD
2. ✅ **Check Audit Logs** - View in sidebar statistics
3. ✅ **Customize Prompts** - Edit `config/prompts.py`
4. ✅ **Add More Examples** - Update `EXAMPLE_QUERIES` in `config/prompts.py`
5. ✅ **Deploy to Production** - See `DEPLOYMENT_CHECKLIST.md`

## 📚 More Documentation

- Full setup: `README.md`
- Deployment: `DEPLOYMENT_CHECKLIST.md`
- Architecture: See `README.md` → Architecture section

## 💡 Tips

**For better results:**
- Be specific in your questions
- Mention table names if you know them
- Include time ranges explicitly
- Use natural language, not SQL keywords

**For development:**
- Set `LOG_LEVEL=DEBUG` to see detailed logs
- Check `audit_logs/` folder for query history
- Use DBA mode to test write operations
- Run tests: `pytest tests/ -v`

## ❓ Need Help?

- Check logs in terminal
- Review audit logs in sidebar
- See `DEPLOYMENT_CHECKLIST.md` for common issues
- Check README.md troubleshooting section

---

**Happy querying! 🔍**
