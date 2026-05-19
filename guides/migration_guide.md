# UpClout AWS Migration — Step-by-Step Guide

> This guide is written for **you** to execute. Each step tells you exactly what to do, which files to touch, and what to verify before moving on.

---

## Phase 1: Centralize Database Connections

**Goal**: Replace every hardcoded `password=1040` with a single shared function that reads from your `.env`.

### Step 1.1: Create the shared DB module

Create a new file: `src/etl/db_utils.py`

```python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Single source of truth for all DB connections."""
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_CONNECTION")
    if url:
        return psycopg2.connect(url)
    # Fallback for local dev
    return psycopg2.connect(
        database=os.getenv("PG_DB", "postgres"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "1040"),
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
    )
```

### Step 1.2: Add `DATABASE_URL` to your `.env`

Open your root `.env` file and add this line:

```
DATABASE_URL=postgresql://<NEON_USER>:<NEON_PASSWORD>@<NEON_HOST>/upclout?sslmode=require
```

> [!CAUTION]
> You already have `POSTGRES_CONNECTION` in your `.env` with the Neon URL. You can rename it to `DATABASE_URL` or keep both — just make sure `db_utils.py` checks for whichever name you use.

### Step 1.3: Update every file that has hardcoded credentials

Here is the **exact list** of files and line numbers you need to update. In each file, replace the `psycopg2.connect(database="postgres", user="postgres", password=1040)` call with a call to your shared function.

#### ETL Files (import from `src/etl/db_utils.py`)

| # | File | Line(s) | What to Do |
|---|---|---|---|
| 1 | `src/etl/load.py` | Line 11 | Replace `self.conn = psycopg2.connect(...)` with `from db_utils import get_connection` then `self.conn = get_connection()` |
| 2 | `src/etl/post_data.py` | Lines 82, 145 | Same pattern. Replace both `psycopg2.connect(...)` calls |
| 3 | `src/etl/niche_filler.py` | Line 14 | Replace `get_db()` function body with `return get_connection()` |
| 4 | `src/db_config/create_database.py` | Line 19 | Replace `self.conn = psycopg2.connect(...)` |
| 5 | `recommender/db.py` | Lines 18-24 | Replace `get_connection()` body |
| 6 | `recommender/boost_detector.py` | Lines 30-36 | Replace the fallback `psycopg2.connect(...)` |

#### Backend Files (import differently since they're in a separate package)

For the backend, create a similar helper in the backend:

| # | File | Line(s) | What to Do |
|---|---|---|---|
| 7 | `backend-fastapi/app/auth.py` | Lines 18, 30 | Create `backend-fastapi/app/db.py` with same pattern, import from there |
| 8 | `backend-fastapi/app/routes/analytics.py` | Lines 15, 86 | Import from `app.db` |
| 9 | `backend-fastapi/app/routes/auth.py` | Lines 138, 166, 239 | Import from `app.db` |
| 10 | `backend-fastapi/app/routes/campaigns.py` | Line 37 | Import from `app.db` |
| 11 | `backend-fastapi/app/routes/collaborations.py` | Line 101 | Import from `app.db` |
| 12 | `backend-fastapi/app/routes/profiles.py` | Line 11 | Import from `app.db` |

For the backend, create `backend-fastapi/app/db.py`:

```python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_pg_connection():
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_CONNECTION")
    if url:
        return psycopg2.connect(url)
    return psycopg2.connect(
        database="postgres", user="postgres",
        password=os.getenv("PG_PASSWORD", "1040"),
        host="localhost", port="5432",
    )
```

Also add `DATABASE_URL` to `backend-fastapi/.env`.

### Step 1.4: Verify

- Run your backend locally: `cd backend-fastapi && python -m app.main`
- Hit a few API endpoints (login, fetch recommendations) — confirm they still work
- Run `python src/etl/load.py` and confirm import works (it won't do anything, just shouldn't crash)

> [!IMPORTANT]
> Don't move to Phase 2 until everything works locally with the new shared DB module.

---

## Phase 2: Extract Notebook Cells into Scripts

**Goal**: The production-critical code living in `EDA.ipynb` needs to become proper `.py` files.

### Step 2.1: Create `src/etl/s3_uploader.py`

Create a new file with these functions extracted from your notebook. Write it yourself based on these cells:

- **EDA.ipynb → "Influencer → AWS" cell** → becomes `upload_all_influencer_pics(base_path)`
- **EDA.ipynb → "Brand → AWS" cell** → becomes `upload_all_brand_pics(base_path)`
- **EDA.ipynb → "Save Profile Picture" cell** → becomes `upload_single_pic(username, image_url, entity_type)`

The key changes to make:
1. Use `from db_utils import get_connection` instead of hardcoded creds
2. Accept `base_path` as a parameter, don't hardcode `../data/influencers_DONE`
3. Add a `if __name__ == "__main__"` block so you can run it standalone
4. Use `os.getenv` for AWS creds (they're already in your `.env`)

### Step 2.2: Create `src/etl/load_recommendations.py`

Extract from these notebook cells:

- **EDA.ipynb → "Influencer Rec FOR BRANDS" cell** → becomes `load_brand_recommendations(json_path)`
- **EDA.ipynb → "Brand Rec FOR INFLUENCERS" cell** → becomes `load_influencer_recommendations(json_path)`

Key changes:
1. Use `from db_utils import get_connection`
2. Both functions should accept `json_path` as parameter
3. Add `if __name__ == "__main__"` block

### Step 2.3: Verify

```bash
# Test S3 uploader (dry run — just check imports work)
cd src/etl
python -c "from s3_uploader import upload_all_influencer_pics; print('OK')"

# Test recommendation loader
python -c "from load_recommendations import load_brand_recommendations; print('OK')"
```

---

## Phase 3: Make ETL Idempotent + Replace .txt Tracking

**Goal**: Make it safe to re-run any stage without duplicates or crashes.

### Step 3.1: Add ON CONFLICT to influencer/brand inserts

Open `src/etl/load.py`:

- **`load_influencer_table()`** (line ~53): Change the INSERT query to:
  ```sql
  INSERT INTO Influencers (...) VALUES (...) ON CONFLICT (influencerID) DO UPDATE SET
    followers = EXCLUDED.followers,
    following = EXCLUDED.following,
    postcount = EXCLUDED.postcount,
    bio = EXCLUDED.bio,
    profile_pic = EXCLUDED.profile_pic;
  ```
- **`load_brand_table()`** (line ~86): Same pattern with `ON CONFLICT (brandID) DO UPDATE SET ...`

This means re-scraping a profile will **update** their data instead of crashing.

### Step 3.2: Create `scrape_queue` table (replaces .txt files)

Run this SQL on your local Postgres (and later on Neon):

```sql
CREATE TABLE IF NOT EXISTS scrape_queue (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('influencer', 'brand')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'done', 'failed')),
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);
```

Then populate it from your existing `.txt` files:

```sql
-- Run this once to import your existing lists
-- For influencers:
INSERT INTO scrape_queue (username, entity_type, status)
SELECT username, 'influencer', 'done'
FROM (VALUES ('user1'), ('user2'), ...) AS t(username)
ON CONFLICT (username) DO NOTHING;
```

Or write a quick Python script to read `processed_influencers.txt` and insert each line as `status='done'`, and `insta_profiles.txt` minus processed ones as `status='pending'`.

### Step 3.3: Update `main.py` and `main_brand.py`

Replace the `.txt` file reading logic:
- `get_influencer_list()` → query `SELECT username FROM scrape_queue WHERE entity_type='influencer' AND status='pending'`
- `already_processed()` → no longer needed (the query above handles it)
- `keep_track_influencers()` → `UPDATE scrape_queue SET status='done', scraped_at=NOW() WHERE username=%s`

### Step 3.4: Verify

- Run `main.py` on a single influencer — confirm it reads from the DB queue and marks it done
- Run it again — confirm it skips the already-done profile

---

## Phase 4: Migrate Data to Neon

**Goal**: Get your local Postgres data into Neon so everything is in one place.

### Step 4.1: Dump your local database

```powershell
pg_dump -U postgres -d postgres --no-owner --no-privileges --format=plain > C:\Users\ismai\OneDrive\Desktop\upclout_dump.sql
```

Enter password `1040` when prompted.

### Step 4.2: Check the dump

Open `upclout_dump.sql` in a text editor. Verify:
- You see `CREATE TABLE` statements for `influencers`, `brands`, `posts`, `hashtags`, etc.
- You see `INSERT` or `COPY` statements with actual data
- File size looks reasonable (should be several MB if you have data)

### Step 4.3: Restore to Neon

```powershell
psql "postgresql://<NEON_USER>:<NEON_PASSWORD>@<NEON_HOST>/upclout?sslmode=require" < C:\Users\ismai\OneDrive\Desktop\upclout_dump.sql
```

> [!WARNING]
> If you get errors about tables already existing, either `DROP` them first in Neon or use `--clean` flag with pg_dump. Be careful not to nuke any data already in Neon.

### Step 4.4: Verify

```powershell
psql "postgresql://<NEON_USER>:<NEON_PASSWORD>@<NEON_HOST>/upclout?sslmode=require"
```

Then run:
```sql
SELECT COUNT(*) FROM influencers;
SELECT COUNT(*) FROM brands;
SELECT COUNT(*) FROM posts;
```

Confirm counts match your local DB.

### Step 4.5: Point your local code to Neon

Update your `.env` so `DATABASE_URL` points to Neon. Restart your backend. Test the app locally — everything should work exactly the same but now reading from Neon.

---

## Phase 5: Set Up EC2 & Docker for Airflow

**Goal**: Get a running Ubuntu server on AWS and orchestrate Airflow via Docker.

### Step 5.1: Launch the instance

1. Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2/)
2. Click **Launch Instance**
3. Settings:
   - **Name**: `upclout-server`
   - **AMI**: Ubuntu Server 22.04 LTS (free tier eligible)
   - **Instance type**: `t3.medium` (4GB RAM)
   - **Key pair**: Create/Use existing `.pem` file
   - **Security group**: Allow inbound on ports **22** (SSH), **8000** (FastAPI), **8080** (Airflow UI)
   - **Storage**: 30 GB gp3
4. Click Launch

### Step 5.2: Install Docker on EC2

SSH into your instance and run:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker ubuntu
# Log out and log back in to apply group changes
```

### Step 5.3: Set Up Airflow with Docker Compose

1. **Prepare directories**:
   ```bash
   mkdir -p /opt/upclout/airflow
   cd /opt/upclout/airflow
   mkdir -p ./dags ./logs ./plugins ./config
   ```

2. **Create the Environment File**:
   ```bash
   echo -e "AIRFLOW_UID=$(id -u)" > .env
   # Add your project env vars here too or mount your root .env
   ```

3. **Create `docker-compose.yaml`**:
   Create this file in `/opt/upclout/airflow`. This is a streamlined version for your `t3.medium`:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_USER=airflow
      - POSTGRES_PASSWORD=airflow
      - POSTGRES_DB=airflow
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5

  airflow-webserver:
    image: apache/airflow:2.10.0
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - DATABASE_URL=${DATABASE_URL} # From your .env
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ../src:/opt/airflow/src/project_code # Mount your source logic
    ports:
      - "8080:8080"
    command: webserver

  airflow-scheduler:
    image: apache/airflow:2.10.0
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ../src:/opt/airflow/src/project_code
    command: scheduler
```

### Step 5.4: Initialize and Start Airflow

```bash
# Initialize the DB (first run only)
docker-compose up airflow-init

# Start all Airflow services
docker-compose up -d
```

### Step 5.5: Create Admin User (via Docker)

```bash
docker-compose run airflow-webserver airflow users create \
    --username admin \
    --firstname Ismail \
    --lastname Hafeez \
    --role Admin \
    --email your@email.com \
    --password <choose-a-password>
```

### Step 5.6: Set up FastAPI Backend (Standard systemd or Docker)

You can still use Phase 5.6 from the original guide to run the **FastAPI backend** directly on the host to save some RAM, or wrap it in another small Docker container. 

---

## Phase 6: Write Airflow DAGs

**Goal**: Create the 3 DAG files that orchestrate your pipeline.

### Step 6.1: Create DAGs directory

```bash
mkdir -p /opt/upclout/airflow/dags
```

### Step 6.2: Write the DAGs

You need to create 3 files inside `airflow/dags/`:

| File | What It Does |
|---|---|
| `dag_etl_influencer.py` | Scrape → Transform → Load → S3 Upload → Niche Fill for influencers |
| `dag_etl_brand.py` | Same but for brands |
| `dag_recommender.py` | Boost Detector → Recommender → Load Recommendations |

Each DAG is a Python file that imports your existing functions. Example skeleton:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'ismail',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'etl_influencer_pipeline',
    default_args=default_args,
    schedule_interval='@weekly',  # Change to '*/6 * * *' for burst mode
    start_date=datetime(2026, 4, 10),
    catchup=False,
) as dag:

    scrape = PythonOperator(
        task_id='scrape_batch',
        python_callable=your_scrape_function,
    )

    transform_load = PythonOperator(
        task_id='transform_and_load',
        python_callable=your_transform_function,
    )

    # ... more tasks

    scrape >> transform_load >> upload_s3 >> fill_niches
```

> [!NOTE]
> You'll need to adjust the `python_callable` imports to point to your actual refactored functions. The key is that each function should be self-contained (get its own DB connection, close it when done). When you're ready to write these, come back and I'll help you wire them up.

### Step 6.3: Verify

- Go to Airflow UI (`http://<ec2-ip>:8080`)
- Your 3 DAGs should appear in the list
- Toggle one on, trigger it manually, watch the logs

---

## Phase 7: Set Up HTTPS with Cloudflare Tunnel

**Goal**: Get free HTTPS for your backend API without buying a domain.

### Step 7.1: Install Cloudflare Tunnel on EC2

```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

### Step 7.2: Create and Authenticate Tunnel

Follow the instructions in the [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started-for-free/create-local-tunnel/) to link your EC2 to a tunnel pointing to `http://localhost:8000`.

### Step 7.3: Verify

Open your tunnel URL (e.g., `https://upclout-api.yourname.workers.dev` or similar) and confirm the backend is reachable over HTTPS.

---

## Phase 8: Deploy Frontend to Vercel

### Step 8.1: Push your code to GitHub

Make sure your `frontend/` directory is pushed to your GitHub repo.

### Step 8.2: Go to [vercel.com](https://vercel.com)

1. Sign in with GitHub
2. Click **Import Project** → select your UpClout repo
3. Set:
   - **Root directory**: `frontend`
   - **Framework**: Vite (it should auto-detect)
   - **Build command**: `npm run build`
   - **Output directory**: `dist`
4. Add environment variable:
   - `VITE_API_URL` = `https://random-words-here.trycloudflare.com` (your Cloudflare tunnel URL)
5. Click Deploy

### Step 8.3: Update your frontend API calls

Make sure your frontend's API service reads from `import.meta.env.VITE_API_URL` instead of hardcoded `http://localhost:8000`.

### Step 8.4: Verify

Open your Vercel URL → the app should load and connect to your EC2 backend via Cloudflare Tunnel → which queries Neon DB.

---

## Phase 9: GitHub Actions CI/CD

**Goal**: Auto-deploy when you push to `main`.

### Step 9.1: Create `.github/workflows/deploy.yml`

```yaml
name: Deploy to EC2

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /opt/upclout
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            pip install -r backend-fastapi/requirements.txt
            sudo systemctl restart upclout-api
```

### Step 9.2: Add GitHub Secrets

Go to your repo → Settings → Secrets → Add:
- `EC2_HOST`: Your EC2 public IP
- `EC2_SSH_KEY`: Paste the contents of your `.pem` file

### Step 9.3: Verify

Push a small change → watch the Actions tab → confirm it deploys to EC2.

---

## Checklist Summary

| Phase | What | Can Do Locally? | Depends On |
|---|---|---|---|
| **1** | Centralize DB connections | ✅ Yes | Nothing |
| **2** | Extract notebook → scripts | ✅ Yes | Phase 1 |
| **3** | Idempotency + scrape queue | ✅ Yes | Phase 1 |
| **4** | pg_dump → Neon migration | ✅ Yes | Phase 1 |
| **5** | EC2 setup | ❌ AWS Console | Phase 4 |
| **6** | Write Airflow DAGs | ✅ Locally, deploy to EC2 | Phases 1-3, 5 |
| **7** | Cloudflare Tunnel | ❌ On EC2 | Phase 5 |
| **8** | Vercel deployment | ❌ Vercel Console | Phase 7 |
| **9** | GitHub Actions CI/CD | ✅ Push to repo | Phase 5 |

> [!TIP]
> **Start with Phases 1-4 locally.** You can do all of them on your Windows machine before even touching AWS. Once those are solid, move to Phase 5.
