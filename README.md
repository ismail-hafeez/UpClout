# 🦉 UpClout

**AI-Powered Influencer-Brand Matchmaking Platform**

UpClout is a full-stack web application that connects Instagram influencers with brands using AI-driven recommendations, semantic search, and an intelligent chatbot assistant. Built as a Final Year Project.

---

## 📌 Problem

The influencer marketing industry is fragmented and inefficient. Brands struggle to find the right influencers for their campaigns — manually browsing profiles, guessing engagement quality, and risking partnerships with artificially boosted accounts. Influencers, on the other hand, have no centralized way to discover relevant brand collaborations matching their niche and scale.

## 💡 Solution

UpClout automates the influencer-brand matching process through:
- A **recommendation engine** powered by SentenceBERT embeddings and weighted multi-factor scoring (semantic similarity, niche relevance, follower tier, engagement rate).
- An **AI chatbot ("Owly")** that lets users query the platform's database conversationally — asking about specific influencers, comparing stats, or getting niche-specific suggestions.
- An **artificial boost detector** that flags accounts with suspicious engagement patterns, protecting brands from fake influence.
- A **collaboration management system** with campaign creation, deliverable tracking, and review/rating workflows.

---

## ✨ Features

### Core Platform
- **Smart Recommendations** — SentenceBERT-based matching with 4-factor scoring: 35% semantic, 30% niche, 25% follower scale, 10% engagement
- **Owly AI Chatbot** — RAG-powered conversational assistant using ChromaDB vector search + Llama 3.3 70B (via Groq) with persistent conversation history
- **Artificial Boost Detection** — Multi-signal fraud analysis: engagement variance, follower/following ratio, engagement rate anomalies, posting frequency spikes
- **Real-Time Messaging** — Socket.IO-powered direct messaging between brands and influencers with typing indicators and online presence

### Collaboration Workflow
- **Campaign Management** — Brands create campaigns, invite influencers, and track deliverables
- **Collaboration Pipeline** — Full lifecycle: Invited → Negotiating → Content Creation → Completed
- **Review System** — Post-collaboration ratings that build a "Clout Score" reputation metric

### Data & Analytics
- **ETL Pipeline** — Automated Instagram profile scraping via Apify, with data normalization and PostgreSQL storage
- **Profile Analytics** — Follower growth, engagement breakdowns, hashtag analysis, and post performance metrics
- **Profile Pics on S3** — Profile images stored on AWS S3 with CDN delivery

---

## 🏗️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 + TypeScript | UI framework |
| Socket.IO Client | Real-time messaging |
| Recharts | Analytics data visualization |

### Backend
| Technology | Purpose |
|---|---|
| FastAPI + Uvicorn | REST API + WebSocket server |
| Socket.IO (python-socketio) | Real-time bidirectional events |
| Motor (async MongoDB) | User auth, conversations, collaborations |
| PostgreSQL (psycopg2) | Influencer/brand profiles, posts, metrics |
| JWT (python-jose) | Authentication & authorization |

### AI / ML
| Technology | Purpose |
|---|---|
| LangChain + LangGraph | RAG orchestration for Owly chatbot |
| ChromaDB | Vector database for semantic profile search |
| HuggingFace Embeddings (all-MiniLM-L6-v2) | Local embedding generation |
| Groq (Llama 3.3 70B) | LLM inference for chatbot responses |
| SentenceBERT | Recommendation engine embeddings |

### Infrastructure
| Technology | Purpose |
|---|---|
| PostgreSQL | Primary relational data store |
| MongoDB | Document store for auth, chat, collaborations |
| AWS S3 | Profile picture storage |
| Apify | Instagram data scraping |

---

## 📁 Project Structure

```
UpClout/
├── frontend/                # React TypeScript SPA
│   └── src/
│       ├── pages/           # Landing, Login, Main Dashboard, Owly Chat, Profile, Campaigns
│       ├── components/      # Modals, Icons, Charts, Ratings
│       └── services/        # API client, Socket.IO handlers
│
├── backend-fastapi/         # FastAPI backend
│   └── app/
│       ├── routes/          # Auth, Owly, Conversations, Campaigns, Collaborations, Analytics
│       ├── chatbot.py       # RAG pipeline (mirrors CLI model)
│       ├── socket_handler.py # Real-time messaging
│       └── models/          # Pydantic schemas
│
├── src/
│   ├── chatbot/             # Chatbot core
│   │   ├── config/          # Groq + ChromaDB + embedding config
│   │   ├── embed_data_groq.py  # ETL → ChromaDB embedding pipeline
│   │   └── CLI_Model_groq.py   # CLI chatbot (reference implementation)
│   ├── etl/                 # Instagram data pipeline (Apify → PostgreSQL)
│   └── db_config/           # Database configuration
│
├── recommender/             # Recommendation engine
│   ├── recommender.py       # SentenceBERT matching with weighted scoring
│   ├── boost_detector.py    # Artificial boost fraud detection
│   └── embedding.py         # Text preparation for embeddings
│
└── chroma_db_groq/          # ChromaDB vector store (generated)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (local)
- MongoDB (local or Atlas)

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run embedding pipeline (first time only)
python -m src.chatbot.embed_data_groq

# Start the backend
cd backend-fastapi
uvicorn app.main:app --port 5000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

---

## ⚠️ Challenges

- **Document Chunking vs. Profile Integrity** — When embedding large profiles (10K+ chars with 50 post captions), the text splitter would separate the username/metrics section from the post captions, causing the LLM to see captions without knowing whose they were. Mitigated by tuning chunk size and overlap parameters.

- **Dual Database Architecture** — Running PostgreSQL (structured influencer data) alongside MongoDB (auth, conversations, collaborations) introduced complexity in cross-referencing users. Bridged via username lookups and "shadow user" creation for influencers not yet registered on the platform.

- **Artificial Boost Detection** — Distinguishing genuinely viral content from artificially boosted engagement required combining multiple weak signals (engagement variance, follower ratio, posting frequency) into a composite risk score with careful weight tuning.

- **Real-Time Messaging at Scale** — Coordinating Socket.IO rooms, online presence tracking, and unread count synchronization across multiple conversations while maintaining JWT authentication on every socket connection.

---

## 👥 Team

- [@ismail-hafeez](https://github.com/ismail-hafeez)
- [@talhakayanii](https://github.com/talhakayanii)
- [@remi23242](https://github.com/remi23242)
