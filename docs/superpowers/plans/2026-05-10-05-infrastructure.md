# AI Office — Chunk 5: Infrastructure, CI/CD & Fine-Tuning

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire everything together — Docker Compose full stack, Nginx reverse proxy with SSL termination, GitHub Actions CI/CD, Prometheus + Grafana monitoring, and NVIDIA NeMo fine-tuning configs for each agent role.

**Architecture:** Docker Compose runs 6 services: postgres, redis, backend (uvicorn), worker (Celery), frontend (nginx SPA), proxy (nginx reverse proxy). GitHub Actions: CI runs pytest + vitest on every PR; CD builds and pushes Docker images on merge to main. Fine-tuning configs are standalone YAML files — not part of the web app runtime.

**Tech Stack:** Docker Compose 3.9, Nginx 1.25, GitHub Actions, Prometheus 2.x, Grafana 10.x, NVIDIA NeMo 1.23 (fine-tuning only)

**Prerequisites:** All chunks 1–4 complete

---

## File Map

```
The-office/
├── docker-compose.yml               # prod: all 6 services
├── docker-compose.dev.yml           # dev overrides: hot reload
├── .env.example                     # all required env vars documented
├── infrastructure/
│   ├── nginx/
│   │   ├── nginx.conf               # reverse proxy: /, /api, /ws
│   │   └── ssl/                     # SSL certs (gitignored, managed by certbot)
│   └── monitoring/
│       ├── prometheus.yml
│       └── grafana/
│           └── dashboard.json       # pre-built AI office dashboard
├── finetuning/
│   ├── README.md
│   ├── configs/
│   │   ├── cto_agent_lora.yaml
│   │   ├── frontend_dev_sft.yaml
│   │   ├── backend_dev_lora.yaml
│   │   ├── api_engineer_ptuning.yaml
│   │   └── qa_engineer_sft.yaml
│   └── data_prep/
│       └── prepare_dataset.py
└── .github/
    └── workflows/
        ├── ci.yml                   # test on PR
        └── cd.yml                   # build+push on main merge
```

---

## Task 1: Root .env.example

**Files:**
- Create: `.env.example` (root level)

- [ ] **Step 1: Write root .env.example**

```ini
# ─── Database ───────────────────────────────────────────────
POSTGRES_DB=office
POSTGRES_USER=office
POSTGRES_PASSWORD=change-me-in-prod
DATABASE_URL=postgresql+asyncpg://office:change-me-in-prod@postgres:5432/office

# ─── Redis ──────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ─── JWT ────────────────────────────────────────────────────
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=change-me-32-char-hex-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# ─── NVIDIA NIM ─────────────────────────────────────────────
# Get key from: https://integrate.api.nvidia.com
NIM_API_KEY=nvapi-your-key-here
NIM_BASE_URL=https://integrate.api.nvidia.com/v1

# Optional: encrypt NIM key at rest
# Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
NIM_API_KEY_ENCRYPTION_KEY=

# ─── App ────────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "chore: document all required env vars in root .env.example"
```

---

## Task 2: Docker Compose (Production)

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Write docker-compose.yml**

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-office}
      POSTGRES_USER: ${POSTGRES_USER:-office}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-office}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --save 20 1 --loglevel warning
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"
    ports:
      - "8000:8000"   # exposed directly for dev; behind nginx in prod
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A app.worker worker --loglevel=info --concurrency=2
    healthcheck:
      test: ["CMD", "celery", "-A", "app.worker", "inspect", "ping", "--timeout", "5"]
      interval: 60s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      - backend

  proxy:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./infrastructure/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend

  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    volumes:
      - ./infrastructure/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infrastructure/monitoring/grafana:/etc/grafana/provisioning:ro
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

- [ ] **Step 2: Write docker-compose.dev.yml**

```yaml
version: "3.9"

# Usage: docker compose -f docker-compose.yml -f docker-compose.dev.yml up
services:
  backend:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app     # live reload: mount source
    environment:
      DATABASE_URL: postgresql+asyncpg://office:office@postgres:5432/office

  worker:
    command: celery -A app.worker worker --loglevel=debug --concurrency=1
    volumes:
      - ./backend:/app

  frontend:
    # Dev: run Vite directly instead of nginx-served build
    build:
      context: ./frontend
      target: build   # stops before nginx stage — use node image
    command: npm run dev -- --host
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

- [ ] **Step 3: Verify compose starts**

```bash
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, JWT_SECRET_KEY, NIM_API_KEY
docker compose up postgres redis -d
docker compose up backend --build
# Expected: backend /health returns {"status":"ok"}
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml docker-compose.dev.yml
git commit -m "feat: Docker Compose — 6 services: postgres, redis, backend, worker, frontend, nginx proxy"
```

---

## Task 3: Nginx Reverse Proxy

**Files:**
- Create: `infrastructure/nginx/nginx.conf`

- [ ] **Step 1: Write infrastructure/nginx/nginx.conf**

```nginx
# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;

    # Security headers (belt-and-suspenders with middleware)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;

    client_max_body_size 10M;

    # WebSocket — must come before /api
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }

    # API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Health check (no auth required)
    location /health {
        proxy_pass http://backend:8000;
    }

    # Frontend SPA
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
    }
}
```

- [ ] **Step 2: Generate self-signed cert for dev**

```bash
mkdir -p infrastructure/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infrastructure/nginx/ssl/key.pem \
  -out infrastructure/nginx/ssl/cert.pem \
  -subj "/CN=localhost"
```

- [ ] **Step 3: Add ssl/ to .gitignore**

```bash
echo "infrastructure/nginx/ssl/" >> .gitignore
```

> **Production SSL:** Replace self-signed cert with Let's Encrypt via certbot:
> ```bash
> certbot certonly --standalone -d yourdomain.com
> # Copy to infrastructure/nginx/ssl/ or mount /etc/letsencrypt directly
> ```

- [ ] **Step 4: Test proxy routing**

```bash
docker compose up -d
curl -k https://localhost/health
# Expected: {"status":"ok","service":"ai-office-backend"}
curl -k https://localhost/api/auth/login -X POST -H "Content-Type: application/json" -d '{"email":"x","password":"x"}'
# Expected: 401 {"detail":"Invalid credentials"}
```

- [ ] **Step 5: Commit**

```bash
git add infrastructure/nginx/nginx.conf .gitignore
git commit -m "feat: Nginx reverse proxy — SSL termination, /api, /ws, SPA routing"
```

---

## Task 4: Prometheus + Grafana

**Files:**
- Create: `infrastructure/monitoring/prometheus.yml`
- Create: `infrastructure/monitoring/grafana/provisioning/datasources/prometheus.yml`
- Create: `infrastructure/monitoring/grafana/provisioning/dashboards/dashboard.yml`

- [ ] **Step 1: Write prometheus.yml**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "ai-office-backend"
    static_configs:
      - targets: ["backend:8000"]
    metrics_path: "/metrics"

  - job_name: "celery-worker"
    static_configs:
      - targets: ["worker:8000"]

  - job_name: "postgres"
    static_configs:
      - targets: ["postgres:5432"]

  - job_name: "redis"
    static_configs:
      - targets: ["redis:6379"]
```

- [ ] **Step 2: Add prometheus metrics to FastAPI**

```python
# Add to backend/requirements.txt:
# prometheus-fastapi-instrumentator==6.1.0

# Add to backend/app/main.py (after app definition):
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

- [ ] **Step 3: Write Grafana datasource config**

```yaml
# infrastructure/monitoring/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
    access: proxy
```

- [ ] **Step 4: Write Grafana dashboard provision**

```yaml
# infrastructure/monitoring/grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1
providers:
  - name: default
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

- [ ] **Step 5: Verify metrics endpoint**

```bash
docker compose up backend -d
curl http://localhost:8000/metrics | grep http_requests_total
# Expected: lines like: http_requests_total{...} N
```

- [ ] **Step 6: Open Grafana**

```bash
# Navigate to: http://localhost:3000
# Login: admin / admin (change GRAFANA_PASSWORD in .env for prod)
# Prometheus datasource auto-configured
```

- [ ] **Step 7: Commit**

```bash
git add infrastructure/monitoring/ backend/app/main.py backend/requirements.txt
git commit -m "feat: Prometheus metrics + Grafana provisioning"
```

---

## Task 5: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write .github/workflows/ci.yml**

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: office_test
          POSTGRES_USER: office
          POSTGRES_PASSWORD: office
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install backend deps
        run: cd backend && pip install -r requirements.txt

      - name: Run backend tests
        env:
          DATABASE_URL: postgresql+asyncpg://office:office@localhost:5432/office_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test-secret-key-for-ci-only
          NIM_API_KEY: test-key-replaced-by-mocks
          NIM_BASE_URL: https://integrate.api.nvidia.com/v1
        run: |
          cd backend
          python -m pytest tests/ -v --cov=app --cov-report=xml --cov-fail-under=70

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  frontend-tests:
    name: Frontend Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend deps
        run: cd frontend && npm ci

      - name: Run frontend tests
        run: cd frontend && npx vitest run

      - name: Build frontend
        run: cd frontend && npm run build

  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install ruff
      - run: ruff check backend/app/
```

- [ ] **Step 2: Add ruff to requirements.txt**

```
# Add to backend/requirements.txt:
ruff==0.4.4
```

- [ ] **Step 3: Create ruff config**

```toml
# Add to backend/pyproject.toml (create if missing):
[tool.ruff]
line-length = 120
target-version = "py311"
select = ["E", "F", "I"]
ignore = ["E501"]
```

- [ ] **Step 4: Run lint locally**

```bash
cd backend && ruff check app/
# Expected: All checks passed.
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml backend/requirements.txt backend/pyproject.toml
git commit -m "feat: GitHub Actions CI — pytest, vitest, ruff, coverage gate 70%"
```

---

## Task 6: GitHub Actions CD

**Files:**
- Create: `.github/workflows/cd.yml`

- [ ] **Step 1: Add GitHub secrets (do in repo settings UI)**

```
# Add these secrets in GitHub → Settings → Secrets:
DOCKER_USERNAME       # Docker Hub username
DOCKER_PASSWORD       # Docker Hub password or access token
```

- [ ] **Step 2: Write .github/workflows/cd.yml**

```yaml
name: CD

on:
  push:
    branches: [main]

env:
  REGISTRY: docker.io
  BACKEND_IMAGE: ${{ secrets.DOCKER_USERNAME }}/ai-office-backend
  FRONTEND_IMAGE: ${{ secrets.DOCKER_USERNAME }}/ai-office-frontend

jobs:
  build-and-push:
    name: Build & Push Docker Images
    runs-on: ubuntu-latest
    needs: []   # runs independently of CI job on main merge

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.BACKEND_IMAGE }}:latest
            ${{ env.BACKEND_IMAGE }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.FRONTEND_IMAGE }}:latest
            ${{ env.FRONTEND_IMAGE }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/cd.yml
git commit -m "feat: GitHub Actions CD — build + push Docker images on main merge"
```

---

## Task 7: Fine-Tuning Configs (NeMo)

**Files:**
- Create: `finetuning/configs/cto_agent_lora.yaml`
- Create: `finetuning/configs/frontend_dev_sft.yaml`
- Create: `finetuning/configs/backend_dev_lora.yaml`
- Create: `finetuning/configs/api_engineer_ptuning.yaml`
- Create: `finetuning/configs/qa_engineer_sft.yaml`
- Create: `finetuning/data_prep/prepare_dataset.py`
- Create: `finetuning/README.md`

- [ ] **Step 1: Write finetuning/configs/cto_agent_lora.yaml**

```yaml
# CTO Agent — LoRA fine-tuning on nemotron-3-super-120b-a12b
# Run on: NVIDIA A100/H100 · Framework: NVIDIA NeMo 1.23
name: cto_agent_lora
trainer:
  num_nodes: 1
  devices: 1          # single GPU min; use 4+ for 120B model
  max_epochs: 3
  precision: bf16

model:
  restore_from_path: null          # set to NeMo checkpoint path
  peft:
    peft_scheme: lora
    lora_tuning:
      adapter_dim: 32
      adapter_dropout: 0.1
      target_modules: [q_proj, v_proj, k_proj, o_proj]

  data:
    train_ds:
      file_path: data/cto_agent/train.jsonl     # format: {"input": "...", "output": "{\"verdict\":\"APPROVE\",...}"}
      max_seq_length: 8192
      micro_batch_size: 1
      global_batch_size: 8
    validation_ds:
      file_path: data/cto_agent/val.jsonl
      max_seq_length: 8192

  optim:
    name: fused_adam
    lr: 1e-4
    weight_decay: 0.01
    sched:
      name: CosineAnnealing
      warmup_steps: 50

# Training data sources (collect before running):
# - Architecture Decision Records (ADRs)
# - Senior code review comments with APPROVE/REVISE/REJECT labels
# - System design documents + review verdicts
# - RFC templates with structured feedback
# Goal: model always outputs {"verdict":"APPROVE|REVISE|REJECT","reasoning":"...","line_citations":[...],"risk_level":"low|medium|high"}
```

- [ ] **Step 2: Write finetuning/configs/frontend_dev_sft.yaml**

```yaml
# Frontend Dev — SFT on deepseek-v4-flash
# Method: Supervised Fine-Tuning on UI code pairs
name: frontend_dev_sft
trainer:
  num_nodes: 1
  devices: 1
  max_epochs: 5
  precision: bf16

model:
  restore_from_path: null
  peft:
    peft_scheme: none    # full SFT

  data:
    train_ds:
      file_path: data/frontend_dev/train.jsonl
      # Format: {"input": "Spec: Build a login form", "output": "{\"component_code\":\"...\",\"filename\":\"Login.tsx\",...}"}
      # Sources: 10K+ React/Vue component examples, Figma-to-code pairs, Tailwind CSS examples, WCAG-compliant UIs
      max_seq_length: 4096
      micro_batch_size: 2
    validation_ds:
      file_path: data/frontend_dev/val.jsonl
      max_seq_length: 4096

  optim:
    name: fused_adam
    lr: 5e-5
```

- [ ] **Step 3: Write finetuning/configs/backend_dev_lora.yaml**

```yaml
# Backend Dev — LoRA on deepseek-v4-pro
name: backend_dev_lora
trainer:
  num_nodes: 1
  devices: 2
  max_epochs: 3
  precision: bf16

model:
  peft:
    peft_scheme: lora
    lora_tuning:
      adapter_dim: 64
      adapter_dropout: 0.05
      target_modules: [q_proj, v_proj]

  data:
    train_ds:
      file_path: data/backend_dev/train.jsonl
      # Format: {"input": "Spec: ...", "output": "{\"implementation_code\":\"...\",\"security_notes\":[...]}"}
      # Sources: REST API implementations, PostgreSQL/MongoDB schemas, auth flows (JWT/OAuth), error handling patterns
      max_seq_length: 8192
      micro_batch_size: 1
    validation_ds:
      file_path: data/backend_dev/val.jsonl

  optim:
    name: fused_adam
    lr: 1e-4
```

- [ ] **Step 4: Write finetuning/configs/api_engineer_ptuning.yaml**

```yaml
# API Engineer — P-Tuning on glm-5.1
name: api_engineer_ptuning
trainer:
  num_nodes: 1
  devices: 1
  max_epochs: 5
  precision: bf16

model:
  peft:
    peft_scheme: p_tuning
    p_tuning:
      virtual_tokens: 10
      bottleneck_dim: 1024

  data:
    train_ds:
      file_path: data/api_engineer/train.jsonl
      # Format: {"input": "Design REST API for: ...", "output": "{\"openapi_spec\":\"...\",\"implementation_code\":\"...\"}"}
      # Sources: OpenAPI 3.0 spec examples, Postman collections, webhook patterns, OAuth flows, SDK wrappers
      max_seq_length: 8192
      micro_batch_size: 2
    validation_ds:
      file_path: data/api_engineer/val.jsonl

  optim:
    name: fused_adam
    lr: 2e-4
```

- [ ] **Step 5: Write finetuning/configs/qa_engineer_sft.yaml**

```yaml
# QA Engineer — SFT on mistral-small-4-119b
name: qa_engineer_sft
trainer:
  num_nodes: 1
  devices: 1
  max_epochs: 4
  precision: bf16

model:
  peft:
    peft_scheme: none    # full SFT

  data:
    train_ds:
      file_path: data/qa_engineer/train.jsonl
      # Format: {"input": "Spec: ...\nCode:\n...", "output": "{\"unit_tests\":\"...\",\"verdict\":\"PASS|FAIL\",...}"}
      # Sources: Jest/Pytest test files, Cypress E2E tests, bug report templates, edge case catalogs
      max_seq_length: 8192
      micro_batch_size: 1
    validation_ds:
      file_path: data/qa_engineer/val.jsonl

  optim:
    name: fused_adam
    lr: 5e-5
```

- [ ] **Step 6: Write finetuning/data_prep/prepare_dataset.py**

```python
"""
Convert raw training examples to JSONL format expected by NeMo SFT/LoRA.
Usage: python prepare_dataset.py --role cto_agent --input raw/ --output data/cto_agent/
"""
import argparse
import json
import random
from pathlib import Path

ROLE_OUTPUT_SCHEMA = {
    "cto_agent": {"verdict": "APPROVE", "reasoning": "", "line_citations": [], "risk_level": "low"},
    "frontend_dev": {"component_code": "", "filename": "Component.tsx", "dependencies": [], "explanation": ""},
    "backend_dev": {"implementation_code": "", "filename": "router.py", "db_schema_changes": None, "security_notes": []},
    "api_engineer": {"openapi_spec": "", "implementation_code": "", "integration_notes": []},
    "qa_engineer": {"unit_tests": "", "integration_tests": None, "edge_cases": [], "bugs_found": [], "verdict": "PASS", "failure_reasons": []},
}

def prepare(role: str, input_dir: Path, output_dir: Path, val_split: float = 0.1):
    output_dir.mkdir(parents=True, exist_ok=True)
    schema = ROLE_OUTPUT_SCHEMA.get(role, {})

    raw_files = list(input_dir.glob("*.json")) + list(input_dir.glob("*.jsonl"))
    if not raw_files:
        raise FileNotFoundError(f"No JSON/JSONL files in {input_dir}")

    examples = []
    for f in raw_files:
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                # Each raw record must have 'input' and 'output' keys
                if "input" not in raw or "output" not in raw:
                    print(f"Skipping malformed record in {f}: missing input/output")
                    continue
                # Validate output keys match schema
                output = raw["output"] if isinstance(raw["output"], dict) else json.loads(raw["output"])
                missing = [k for k in schema if k not in output]
                if missing:
                    print(f"Warning: output missing keys {missing} in {f}")
                examples.append({"input": raw["input"], "output": json.dumps(output)})

    random.shuffle(examples)
    split = int(len(examples) * (1 - val_split))
    train, val = examples[:split], examples[split:]

    for name, data in [("train.jsonl", train), ("val.jsonl", val)]:
        out = output_dir / name
        with open(out, "w") as fh:
            for ex in data:
                fh.write(json.dumps(ex) + "\n")
        print(f"Wrote {len(data)} examples → {out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True, choices=list(ROLE_OUTPUT_SCHEMA.keys()))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--val-split", type=float, default=0.1)
    args = parser.parse_args()
    prepare(args.role, args.input, args.output, args.val_split)
```

- [ ] **Step 7: Write finetuning/README.md**

```markdown
# AI Office — Fine-Tuning Guide

Fine-tune each agent model for its role using NVIDIA NeMo.

## Requirements
- NVIDIA A100 or H100 GPU (at least 1x for LoRA/P-Tuning; 4x+ for full SFT of large models)
- NVIDIA NeMo 1.23: `pip install nemo_toolkit[nlp]`
- NGC container (recommended): `nvcr.io/nvidia/nemo:24.01`

## Workflow

### 1. Prepare data
```bash
python data_prep/prepare_dataset.py \
  --role cto_agent \
  --input raw/cto_reviews/ \
  --output data/cto_agent/
```

Minimum examples per role:
- CTO Agent: 500+ (ADRs, code reviews with verdicts)
- Frontend Dev: 10K+ (component spec → React code pairs)
- Backend Dev: 2K+ (API spec → implementation pairs)
- API Engineer: 1K+ (OpenAPI spec examples)
- QA Engineer: 2K+ (code → test suite pairs)

### 2. Run fine-tuning
```bash
python -m nemo.collections.nlp.models.language_modeling.megatron_gpt_sft_model \
  --config-path configs/ \
  --config-name cto_agent_lora \
  trainer.devices=1 \
  model.data.train_ds.file_path=data/cto_agent/train.jsonl
```

### 3. Export to NIM
```bash
# Convert NeMo checkpoint → NIM-compatible format
# Then deploy as NIM microservice and update MODEL_MAP in app/agents/roles.py
```

## Method by role
| Role | Method | Why |
|------|--------|-----|
| CTO Agent | LoRA | Large model (120B), few high-quality examples |
| Frontend Dev | SFT | Code generation needs full weight update |
| Backend Dev | LoRA | Large model (deepseek-v4-pro), domain adaptation |
| API Engineer | P-Tuning | Structured output format, lightweight tuning |
| QA Engineer | SFT | Test generation needs full pattern learning |
```

- [ ] **Step 8: Commit**

```bash
git add finetuning/
git commit -m "feat: NeMo fine-tuning configs + data prep script for all 5 tunable roles"
```

---

## Task 8: End-to-End Smoke Test

**Files:**
- None new — verifies everything wired

- [ ] **Step 1: Start full stack**

```bash
cp .env.example .env
# Edit .env — set real NIM_API_KEY, POSTGRES_PASSWORD, JWT_SECRET_KEY
docker compose up -d --build
# Wait ~30s for postgres healthcheck
```

- [ ] **Step 2: Run backend migrations**

```bash
docker compose exec backend alembic upgrade head
# Expected: Running upgrade -> xxxx, initial schema
```

- [ ] **Step 3: Create owner account**

```bash
curl -k -X POST https://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@aioffice.com","password":"SecureP@ss123"}'
# Expected: {"id":"...","email":"owner@aioffice.com","is_owner":true}
```

- [ ] **Step 4: Login + get token**

```bash
TOKEN=$(curl -s -k -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@aioffice.com","password":"SecureP@ss123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: ${TOKEN:0:20}..."
```

- [ ] **Step 5: Submit a task**

```bash
TASK=$(curl -s -k -X POST https://localhost/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Build login page","description":"React login form with email and password, JWT auth, TailwindCSS styling","task_type":"frontend"}')
echo $TASK | python3 -m json.tool
TASK_ID=$(echo $TASK | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

- [ ] **Step 6: Watch pipeline progress**

```bash
# Poll approvals every 5s
watch -n 5 "curl -s -k https://localhost/api/tasks/$TASK_ID/approvals -H 'Authorization: Bearer $TOKEN' | python3 -m json.tool"
# Expected: steps appear one by one with status changing: pending → running → approved/rejected
```

- [ ] **Step 7: Open frontend**

```bash
# Navigate to https://localhost in browser
# Login → Dashboard → see task → click → view live pipeline
```

- [ ] **Step 8: Check monitoring**

```bash
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
# Check: http_requests_total, process_cpu_seconds_total
```

- [ ] **Step 9: Final commit**

```bash
git add .
git commit -m "chore: end-to-end smoke test verified, infra complete"
```

---

## Chunk 5 Complete

All done when:
- `docker compose up` → all 6 services healthy
- `https://localhost/health` → 200 OK through nginx
- Register → login → submit task → pipeline runs → see steps in UI
- GitHub Actions CI passes on PR
- Docker images pushed to registry on merge to main

---

## Full Project Checklist

- [ ] Chunk 1: Backend Foundation (auth, DB, security)
- [ ] Chunk 2: Agent Layer (all 11 NIM role agents)
- [ ] Chunk 3: Pipeline Orchestrator (Celery, approval chain, API)
- [ ] Chunk 4: Frontend Dashboard (React, WebSocket, OrgChart)
- [ ] Chunk 5: Infrastructure (Docker, Nginx, CI/CD, monitoring, NeMo configs)

**Production hardening before go-live:**
- Replace self-signed SSL cert with Let's Encrypt
- Set strong POSTGRES_PASSWORD, JWT_SECRET_KEY in production .env
- Enable NVIDIA NIM rate limit monitoring (NIM has per-model quotas)
- Set GRAFANA_PASSWORD in .env
- Configure database backups (pg_dump cron or managed Postgres)
- Review slowapi rate limits per endpoint (auth tighter than task submit)
