# Deploying Maryland Crash Costs (Fly.io)

Production is a **single Docker image**: Vite static files + FastAPI/DuckDB + baked-in `data_cache/`.

**Live app:** [https://crash-cost-md.fly.dev](https://crash-cost-md.fly.dev)

---

## Prerequisites

1. **Prepared `data_cache/`** — run `python prepare_data.py` from `backend/` after building source data ([`../data/DATA.md`](../data/DATA.md)).
2. **[flyctl](https://fly.io/docs/hands-on/install-flyctl/)** installed (`flyctl version`).
3. **Docker** (optional, for local image smoke test).

---

## 1. Smoke-test the image locally

From `crash_cost_app/`:

```powershell
docker build -t crash-cost-md .
docker run --rm -p 8080:8080 crash-cost-md
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080). Health: [http://127.0.0.1:8080/api/health](http://127.0.0.1:8080/api/health).

If the build fails on missing `crashes.parquet`, run `prepare_data.py` first.

---

## 2. Fly.io deploy

```powershell
cd crash_cost_app
fly auth login
fly deploy
```

`fly deploy` uploads your **local** directory. `data_cache/` is included in the Docker build context even though it is gitignored, as long as the files exist on disk.

```powershell
fly open
fly status
fly logs
```

App name and region are in `fly.toml` (`crash-cost-md`, `iad`).

---

## 3. Clone from GitHub

Repository: [github.com/mSorak/md_crash_costs](https://github.com/mSorak/md_crash_costs)

```powershell
git clone https://github.com/mSorak/md_crash_costs.git
cd md_crash_costs
```

Rebuild source data per [`data/DATA.md`](../data/DATA.md), then `prepare_data.py`, then deploy from `crash_cost_app/`.

---

## 4. Updates

| Change | Action |
|--------|--------|
| App code | `git pull`, `fly deploy` from `crash_cost_app/` |
| Source crash CSV | Re-run notebook + `geographic_summaries.py` + `prepare_data.py`, then `fly deploy` |
| VM / region | Edit `fly.toml`, `fly deploy` |

---

## 5. Custom domain (optional)

```powershell
fly certs add your.domain.example
```

Add the DNS record Fly prints (often CNAME to `crash-cost-md.fly.dev`). TLS is automatic.

---

## 6. Notes

- **No authentication** on the API — appropriate for a public research tool; add rate limiting if needed.
- **CI (later):** a workflow can run `fly deploy` only if it restores or regenerates `data_cache/` (artifact or private data store).
