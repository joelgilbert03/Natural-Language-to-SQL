# 🔍 NL2SQL - Natural Language to SQL Query System

<div align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.32-FF4B4B.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

**Transform natural language questions into SQL queries using AI**

[Demo](https://huggingface.co/spaces/joelgilbert/NL2SQL) • [Documentation](#-documentation) • [Quick Start](#-quick-start) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

NL2SQL is an intelligent multi-agent system that converts natural language questions into SQL queries, executes them safely, and explains results in plain English. Built with enterprise-grade security and a modern tech stack.

### ✨ Key Features

- 🤖 **Multi-Agent Architecture** - Three specialized AI agents work together
- 🔒 **Enterprise Security** - SQL injection prevention, query validation, audit logging
- 🚀 **Smart Query Generation** - Automatic error correction with up to 3 retry attempts
- 🔍 **Semantic Search** - Vector-based schema and query similarity matching
- 📊 **Interactive Results** - Beautiful data visualizations with natural language explanations
- 🎯 **Two-Tier Access** - Read-only mode for BI, DBA mode for data modifications
- ⚡ **Real-time Processing** - Fast query execution with connection pooling

---

## 🏗️ Architecture

```mermaid
graph TB
    User[User Question] --> A1[Agent 1: Gatekeeper]
    A1 --> |Validates| VS[Vector Store Search]
    VS --> |Relevant Schemas| A2[Agent 2: SQL Generator]
    A2 --> |Generates SQL| VAL[Security Validator]
    VAL --> |Safe Query| EXEC[Query Executor]
    EXEC --> |Results| A3[Agent 3: Explainer]
    A3 --> |Natural Language| User
```

### 🧠 Agent Workflow

1. **Gatekeeper Agent** (Groq/Llama-3.1-70B)
   - Validates user intent
   - Filters out-of-scope questions
   - Preprocesses queries for better results

2. **SQL Generator Agent** (Cloudflare/SQLCoder-7B-2)
   - Generates SQL from natural language
   - Auto-corrects syntax errors
   - Optimizes queries for performance

3. **Explainer Agent** (Groq/Llama-3.1-70B)
   - Analyzes query results
   - Generates business insights
   - Creates human-friendly summaries

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database (we recommend [Neon](https://neon.tech))
- API keys:
  - [Groq API](https://console.groq.com) - For LLM inference
  - [Cloudflare Workers AI](https://dash.cloudflare.com) - For SQL generation
  - [Upstash Vector](https://console.upstash.com) - For semantic search

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/nl2sql-query-system.git
cd nl2sql-query-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```env
   # Database
   NEON_READONLY_CONNECTION_STRING=postgresql://user:pass@host/db
   NEON_DBA_CONNECTION_STRING=postgresql://user:pass@host/db
   
   # API Keys
   GROQ_API_KEY=gsk_xxxxx
   CLOUDFLARE_ACCOUNT_ID=xxxxx
   CLOUDFLARE_AUTH_TOKEN=xxxxx
   
   # Upstash Vector
   UPSTASH_VECTOR_URL=https://xxxxx.upstash.io
   UPSTASH_VECTOR_TOKEN=xxxxx
   
   # Security
   DBA_PASSWORD=your_secure_password
   ```

3. **Set up sample database** (optional):
   ```bash
   psql -h your-host -U your-user -d your-db -f scripts/sample_data.sql
   ```

4. **Initialize vector store:**
   ```bash
   python scripts/init_vector_store.py
   ```

### Run the Application

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`

---

## 💡 Usage Examples

### Basic Queries
```
"How many customers do we have?"
"Show me total sales by region"
"List the top 10 products by revenue"
```

### Complex Analysis
```
"What's the average order value for customers in California last month?"
"Show me products with low stock levels (less than 50 units)"
"Which regions had the highest growth in Q4?"
```

### DBA Mode (Password Protected)
```
"Update the price of product_id 42 to 29.99"
"Delete orders older than 2 years"
"Insert a new customer record"
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit |
| **Backend** | Python 3.10+ |
| **Database** | PostgreSQL (Neon Serverless) |
| **Vector DB** | Upstash Vector |
| **LLM Inference** | Groq API (Llama 3.1), Cloudflare Workers AI |
| **Embeddings** | BAAI/bge-m3 (1024 dimensions) |
| **Security** | Custom SQL validation, audit logging |

---

## 📂 Project Structure

```
nl2sql-query-system/
├── agents/              # AI agent implementations
│   ├── gatekeeper.py    # Intent classification & validation
│   ├── sql_generator.py # SQL query generation
│   └── explainer.py     # Result explanation
├── config/              # Configuration management
│   ├── settings.py      # Pydantic settings
│   └── prompts.py       # LLM prompts
├── database/            # Database operations
│   ├── connection.py    # Connection pooling
│   ├── schema_manager.py
│   └── query_executor.py
├── security/            # Security layer
│   ├── validator.py     # SQL injection prevention
│   ├── auth.py          # DBA authentication
│   └── audit_logger.py  # Query audit trails
├── vector_store/        # Semantic search
│   ├── upstash_client.py
│   └── embeddings.py
├── utils/               # Helper utilities
├── tests/               # Unit tests
├── scripts/             # Utility scripts
│   ├── health_check.py
│   ├── init_vector_store.py
│   └── sample_data.sql
└── app.py              # Main Streamlit app
```

---

## 🔐 Security Features

### Query Validation
- ✅ SQL injection pattern detection
- ✅ Destructive operation warnings
- ✅ Multi-statement prevention
- ✅ Table access control

### Access Control
- 🔒 **Read-Only Mode** - Default, SELECT queries only
- 🔓 **DBA Mode** - Password protected, full CRUD access
- ⏱️ Session timeout (1 hour)
- 🔐 Timing-attack resistant authentication

### Audit Trail
- 📝 All queries logged with timestamps
- 👤 User session tracking
- ⚡ Performance metrics
- ❌ Error tracking

---

## 📊 Database Schema

The system works with any PostgreSQL database. A sample e-commerce schema is provided:

- `customers` - Customer records with demographics
- `products` - Product catalog with categories
- `orders` - Order transactions
- `order_items` - Line items for orders
- `categories` - Product categories
- `regions` - Geographic regions

See [`scripts/sample_data.sql`](scripts/sample_data.sql) for the complete schema.

---

## 🚢 Deployment

### Local Development
```bash
streamlit run app.py
```

### Hugging Face Spaces
```bash
# See HF_DEPLOYMENT_CHECKLIST.md for detailed instructions
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
git push hf main
```

### Docker (Coming Soon)
```bash
docker build -t nl2sql .
docker run -p 8501:8501 nl2sql
```

For detailed deployment instructions, see:
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)
- [Hugging Face Guide](HF_DEPLOYMENT_CHECKLIST.md)

---

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run health check:
```bash
python scripts/health_check.py
```

---

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Get up and running in 5 minutes
- [Project Structure](PROJECT_STRUCTURE.md) - Detailed code organization
- [Database Setup](scripts/DATABASE_SETUP.md) - Sample database installation
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Production deployment guide
- [HuggingFace Guide](HF_DEPLOYMENT_CHECKLIST.md) - Deploy to HF Spaces

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

---

## 🐛 Known Issues & Limitations

- Cloudflare Workers AI has rate limits (free tier: 10,000 requests/day)
- Complex JOINs across 5+ tables may timeout
- Schema changes require vector store reinitialization
- Groq API may have occasional latency spikes

---

## 🗺️ Roadmap

- [ ] Add support for multiple databases (MySQL, SQLite)
- [ ] Implement query caching for faster responses
- [ ] Add support for chart generation from query results
- [ ] Create Docker container for easy deployment
- [ ] Add multi-user authentication
- [ ] Implement query history and favorites
- [ ] Add support for aggregate functions and window functions
- [ ] Create browser extension for quick queries

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com) - Lightning-fast LLM inference
- [Cloudflare Workers AI](https://ai.cloudflare.com) - SQL generation model
- [Upstash](https://upstash.com) - Serverless vector database
- [Neon](https://neon.tech) - Serverless PostgreSQL
- [Streamlit](https://streamlit.io) - Beautiful Python web apps
- [Llama 3.1](https://ai.meta.com/llama/) - Meta's open-source LLM
- [SQLCoder](https://github.com/defog-ai/sqlcoder) - Specialized SQL generation model

---

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/YOUR_USERNAME/nl2sql-query-system/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/YOUR_USERNAME/nl2sql-query-system/discussions)
- **Email**: your.email@example.com

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=YOUR_USERNAME/nl2sql-query-system&type=Date)](https://star-history.com/#YOUR_USERNAME/nl2sql-query-system&Date)

---

<div align="center">

**Made with ❤️ and AI**

[⬆ Back to Top](#-nl2sql---natural-language-to-sql-query-system)

</div>
