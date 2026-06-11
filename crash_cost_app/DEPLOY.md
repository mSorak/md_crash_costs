# Deploying Maryland Crash Costs (Fly.io)

Production is a **single Docker image**: Vite static files + FastAPI/DuckDB + baked-in `data_cache/`.

**Live app:** [https://crash-cost-md.fly.dev](https://crash-cost-md.fly.dev)

---

## Prerequisites

1. **Prepared `data_cache/`** — run `python prepare_data.py` from `backend/` (requires source data on disk; not in this repo).
2. **[flyctl](https://fly.io/docs/hands-on/install-flyctl/)** installed.
3. **Docker** (optional, for local image smoke test).

---

## 1. Smoke-test locally

From this folder (`crash_cost_app/`):

```powershell
docker build -t crash-cost-md .
docker run --rm -p 8080:8080 crash-cost-md
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080). Health: `/api/health`.

---

## 2. Fly.io deploy

```powershell
fly auth login
fly deploy
```

`data_cache/` must exist locally when you deploy — it is gitignored but included in the Docker build context.

```powershell
fly open
fly status
fly logs
```

Config: `fly.toml` (`crash-cost-md`, region `iad`).

---

## 3. Clone from GitHub

```powershell
git clone https://github.com/mSorak/md_crash_costs.git
cd md_crash_costs/crash_cost_app
```

Build `data_cache/` locally, then `fly deploy` from this directory.

---

## 4. Updates

| Change | Action |
|--------|--------|
| App code | `git pull`, `fly deploy` |
| Source crash data | Re-run `prepare_data.py`, then `fly deploy` |

---

## 5. Custom domain (optional)

```powershell
fly certs add your.domain.example
```

Add the DNS record Fly prints. TLS is automatic.
