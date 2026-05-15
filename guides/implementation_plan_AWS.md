# UpClout Pipeline Automation on AWS

## Current Architecture (What Exists Today)

Your pipeline is a **manually-run, local-first system** across 6 independent stages. Here's the actual data flow:

```mermaid
graph TD
    A["insta_profiles.txt / brand_profiles.txt"] --> B["Apify Scraper<br/>extract.py + apify_class.py"]
    B --> C["Local disk<br/>data/{username}/"]
    C --> D["Transform<br/>meta_data.py + post_data.py"]
    D --> E["Load to PostgreSQL<br/>load.py"]
    E --> F["Niche Filler<br/>niche_filler.py (LLM)"]
    F --> G["Recommender<br/>SentenceBERT + scoring"]
    G --> H["similarity_matches.json"]
    H --> I["Load Recs to PG<br/>EDA.ipynb cells"]
    E --> J["Boost Detector<br/>boost_detector.py"]
    J --> K["boost_analysis.json"]
    C --> L["Profile Pics → S3<br/>EDA.ipynb cells"]
```

### Per-Stage Breakdown

| Stage | Entry Point | What It Does | Dependencies |
|---|---|---|---|
| **1. Scrape** | `main.py` / `main_brand.py` | Calls Apify Instagram Scraper, downloads profile pics locally, rotates API keys every 4 calls | Apify tokens, `../../data/` on disk |
| **2. Transform** | `meta_data.py`, `post_data.py` | Cleans bios (emoji/whitespace), extracts location from bio, corrects dtypes, extracts hashtags/tags | Reads CSVs + JSONs from `data/{user}/` |
| **3. Load** | `load.py` (Postgres class) | Inserts into `influencers`, `brands`, `posts`, `hashtags`, `posts_hashtags`, `taggeduser`, `posts_taggeduser` | Local PG (`password=1040`) |
| **4. Niche Fill** | `niche_filler.py` | Queries PG for NULL categories, sends bio+captions to Groq LLM, writes category back | `backend-fastapi/app/chatbot.llm` |
| **5. Profile Pics → S3** | `EDA.ipynb` cells | Walks `data/influencers_DONE/` and `data/brands_not_in_AWS/`, uploads `.jpg` to `upclout-profile-pics` S3 bucket | `boto3`, AWS creds in `.env` |
| **6. Recommender** | `recommender/recommender.py` | Fetches all influencers+brands from PG, generates SentenceBERT embeddings, scores with weighted formula (35% semantic, 30% niche, 25% scale, 10% engagement), writes `similarity_matches.json` | `sentence-transformers`, PG |
| **7. Load Recommendations** | `EDA.ipynb` cells | Reads `similarity_matches.json`, creates `brand_recommendations` and `influencer_recommendations` tables, inserts rows | PG |
| **8. Boost Detection** | `boost_detector.py` | Fetches engagement metrics from PG, computes `boost_risk_score` per entity, exports `boost_analysis.json` + CSVs | PG, pandas |

### Key Observations

- **Hardcoded paths everywhere**: `../../data/`, `../../logs/`, `../../insta_profiles.txt`, `r"c:\Users\ismai\..."`
- **Hardcoded DB creds**: `password=1040` in 6+ files
- **Tracking state via .txt files**: `processed_influencers.txt` and `processed_brands.txt` track what's been scraped
- **EDA.ipynb is doing production work**: S3 uploads and recommendation loading are notebook cells, not scripts
- **No retry logic**: If Apify fails mid-run, you restart manually
- **Stages are decoupled**: No orchestration between them; you run each manually in order

---

## Finalized Architecture

```mermaid
graph TD
    subgraph "Vercel (Free)"
        FE["React Frontend<br/>auto-deploy from GitHub"]
    end

    subgraph "EC2 t3.medium (~$20-30/mo)"
        AF["Airflow Scheduler + Webserver"]
        API["FastAPI Backend"]
        NG["nginx + Cloudflare Tunnel<br/>(free HTTPS)"]
    end

    subgraph "Neon (Free Tier)"
        PG["PostgreSQL"]
    end

    subgraph "AWS Services"
        S3["S3 Bucket<br/>profile pics"]
    end

    FE -->|API calls via HTTPS| NG
    NG --> API
    API --> PG
    AF -->|ETL DAGs| PG
    AF -->|upload pics| S3
    FE -->|load images| S3
```

### Decisions Made

| Question | Decision | Rationale |
|---|---|---|
| **Database** | **Neon DB (keep existing)** | Free tier, managed backups, accessible from everywhere (EC2, Vercel, local dev). No RAM overhead on EC2. |
| **Scraping frequency** | **Burst initially → Weekly** | Run ETL multiple times daily until `.txt` backlog is drained, then switch Airflow schedule to `@weekly` |
| **Data migration** | **Migrate existing + re-scrape for updates** | `pg_dump` local → restore to Neon. Then re-scrape same profiles on EC2 to refresh followers/pics. `ON CONFLICT` handles upserts. |
| **Frontend hosting** | **Vercel (free)** | Free CDN, auto-deploy from GitHub, HTTPS included, `.vercel.app` subdomain |
| **Backend hosting** | **EC2** | Colocated with Airflow. Use Cloudflare Tunnel for free HTTPS without a domain. |
| **Kafka** | **Skip** | Pipeline is batch-oriented, single producer/consumer. Adds complexity without solving a real problem. |

### Budget: $117 AWS Credits

| Service | Monthly Cost | Runway |
|---|---|---|
| EC2 `t3.medium` on-demand | ~$30 | ~3.5 months |
| EBS 30GB gp3 | ~$2.40 | negligible |
| S3 (<1GB profile pics) | ~$0.02 | negligible |
| Neon DB | $0 (free tier) | ∞ |
| Vercel frontend | $0 (free tier) | ∞ |
| **Total** | **~$33/mo** | **~3.5 months on credits** |

> [!TIP]
> After credits expire, switch to a **1-year Reserved `t3.medium`** (~$18/mo) or downgrade to `t3.small` (~$15/mo, 2GB RAM) and schedule the heavy recommender job during off-hours.

---

## Airflow DAG Design

### DAG 1: `etl_influencer_pipeline` (Schedule: Burst → `@weekly`)

```
scrape_batch → transform_and_load → upload_pics_to_s3 → fill_niches
```

| Task | Operator | Details |
|---|---|---|
| `scrape_batch` | `PythonOperator` | Reads from `scrape_queue` table (replaces .txt files), calls Apify for up to N profiles per run, handles API rotation |
| `transform_and_load` | `PythonOperator` | Runs `meta_data.clean_meta_data()` + `post_data.clean_post_data()` + `load.py` inserts for each scraped profile |
| `upload_pics_to_s3` | `PythonOperator` | Walks newly scraped folders, uploads to S3, updates `profile_pic` column in PG with S3 URL |
| `fill_niches` | `PythonOperator` | Runs `niche_filler.fill_missing_niches()` for any new NULL-category rows. Has `retries=3` with exponential backoff for LLM rate limits |

### DAG 2: `etl_brand_pipeline` (Schedule: Burst → `@weekly`, offset)

Same structure as DAG 1 but targets `brand_profiles` queue and uses brand-specific load functions.

### DAG 3: `recommender_pipeline` (Schedule: After DAGs 1+2 via `ExternalTaskSensor`)

```
run_boost_detector → run_recommender → load_recommendations_to_pg
```

| Task | Operator | Details |
|---|---|---|
| `run_boost_detector` | `PythonOperator` | Calls `boost_detector.analyze_artificial_boost()`, exports `boost_analysis.json` |
| `run_recommender` | `PythonOperator` | Runs `Recommender().run()`. Heaviest task (~SentenceBERT encoding). Needs ≥4GB RAM. |
| `load_recommendations` | `PythonOperator` | Reads `similarity_matches.json`, upserts into `brand_recommendations` + `influencer_recommendations` tables. Extracted from EDA.ipynb into a proper script. |

---

## What Needs to Change in Code

### Phase 1: Centralize Config (Do First)

| Current | Proposed |
|---|---|
| `password=1040` in 6+ files | Single `DATABASE_URL` env var (Neon connection string) read by all modules |
| `../../data/`, `../../logs/` | Config module: `DATA_DIR = os.getenv("UPCLOUT_DATA_DIR", "/opt/upclout/data")` |
| `r"c:\Users\ismai\..."` in `niche_filler.py` | Remove. Use proper `PYTHONPATH` env var |
| `processed_influencers.txt` / `processed_brands.txt` | Replace with `scrape_queue` DB table (`username, entity_type, status, scraped_at`) |

Create a shared DB module:

```python
# src/etl/db.py (new file)
import os, psycopg2

def get_connection():
    url = os.getenv("DATABASE_URL")
    if url:
        return psycopg2.connect(url)
    return psycopg2.connect(
        database=os.getenv("PG_DB", "postgres"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
    )
```

### Phase 2: Extract Notebook Cells into Scripts

Create these files from EDA.ipynb:

| New File | Source | What It Does |
|---|---|---|
| `src/etl/s3_uploader.py` | EDA.ipynb "Influencer → AWS" + "Brand → AWS" cells | `upload_profile_pic()`, `upload_all_profile_pics()`, `upload_all_brand_pics()` |
| `src/etl/load_recommendations.py` | EDA.ipynb "Influencer Rec" + "Brand Rec" cells | `load_brand_recommendations()`, `load_influencer_recommendations()` |

### Phase 3: Make ETL Functions Idempotent

- Add `ON CONFLICT` to influencer/brand INSERT queries in `load.py` (currently they error on duplicates)
- S3 `put_object` is already idempotent (overwrites same key)
- Recommendation loaders already use `ON CONFLICT DO NOTHING`

### Phase 4: Write Airflow DAGs

- Create `dags/` directory with 3 DAG files
- Each DAG imports from the refactored `src/etl/` modules
- Configure Airflow connections for Neon DB, S3, and Apify tokens

---

## EC2 Setup Checklist

### Instance Configuration

| Resource | Value |
|---|---|
| Instance type | `t3.medium` (2 vCPU, 4GB RAM) |
| Storage | 30GB EBS gp3 |
| OS | Ubuntu 22.04 LTS |
| Security groups | Inbound: 22 (SSH), 8000 (FastAPI), 8080 (Airflow UI) |
| Python | 3.11 via `pyenv` |
| Airflow | `pip install apache-airflow` with `LocalExecutor` |

### Services Running on EC2

```
Airflow Webserver (port 8080) ← DAG monitoring UI
Airflow Scheduler             ← triggers DAG runs
FastAPI Backend (port 8000)   ← your app API
nginx                         ← reverse proxy + Cloudflare Tunnel
```

### Deployment Flow (GitHub Actions → EC2)

```mermaid
graph LR
    A["Push to main"] --> B["GH Actions"]
    B --> C["SSH to EC2"]
    C --> D["git pull"]
    D --> E["pip install -r requirements.txt"]
    E --> F["systemctl restart upclout-api"]
    E --> G["Airflow picks up new DAG code automatically"]
```

---

## Data Migration Plan

### Step 1: Dump Local PG
```bash
pg_dump -U postgres -d postgres --no-owner --no-privileges > upclout_dump.sql
```

### Step 2: Restore to Neon
```bash
psql "postgresql://user:pass@ep-xxx.neon.tech/neondb" < upclout_dump.sql
```

### Step 3: Verify
- Check row counts match for `influencers`, `brands`, `posts`, `hashtags`
- Verify recommendation tables loaded correctly

### Step 4: Point All Code to Neon
- Set `DATABASE_URL` in `.env` on EC2
- Set same in Vercel environment variables (for the FastAPI backend URL, not direct DB access)
- Local dev: update `.env` to point to Neon

### Step 5: Re-scrape on EC2 (Post-Deploy)
- Trigger Airflow DAGs manually to refresh stale profiles
- New followers/pics/posts get upserted via `ON CONFLICT`

---

## Implementation Order

```mermaid
graph TD
    P1["Phase 1: Centralize Config<br/>(shared db.py, env vars, remove hardcoded paths)"] --> P2
    P2["Phase 2: Extract Notebook → Scripts<br/>(s3_uploader.py, load_recommendations.py)"] --> P3
    P3["Phase 3: Idempotency Fixes<br/>(ON CONFLICT on all inserts)"] --> P4
    P4["Phase 4: pg_dump → Neon Migration"] --> P5
    P5["Phase 5: EC2 Setup<br/>(Ubuntu, Python, Airflow, nginx)"] --> P6
    P6["Phase 6: Write Airflow DAGs<br/>(3 DAGs, connections, schedules)"] --> P7
    P7["Phase 7: Deploy Backend to EC2<br/>(FastAPI + Cloudflare Tunnel)"] --> P8
    P8["Phase 8: Deploy Frontend to Vercel"] --> P9
    P9["Phase 9: GH Actions CI/CD Pipeline"]
```

> [!NOTE]
> Phases 1-3 can be done locally before touching AWS. Phase 4 is a one-time migration. Phases 5-9 are the actual cloud deployment.
