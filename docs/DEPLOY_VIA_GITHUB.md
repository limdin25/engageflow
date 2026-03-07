# Deploy EngageFlow via GitHub

Repo: **https://github.com/limdin25/engageflow**

## 1. Push from your Mac (when you have changes)

```bash
cd /Users/hugo/Downloads/AI\ Folder/openclaw/engageflow-repo
git add -A
git status   # review; remove any secrets if listed
git commit -m "Sync for Alibaba deploy"
git push -u origin dev
```

Use `main` instead of `dev` if your default branch is `main`.

## 2. On Alibaba: clone and run

### First time (clone + install)

```bash
cd /root/.openclaw/workspace-margarita
rm -rf engageflow   # only if you want a clean clone (backs up nothing)
git clone https://github.com/limdin25/engageflow.git engageflow
cd engageflow
git checkout dev    # or main
```

### Backend (venv)

```bash
cd /root/.openclaw/workspace-margarita/engageflow/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Frontend (separate terminal)

```bash
cd /root/.openclaw/workspace-margarita/engageflow/frontend
npm install
npm run build
npx -y serve -s dist -l 3000
```

### Or with Docker (from repo root)

```bash
cd /root/.openclaw/workspace-margarita/engageflow
docker compose up --build -d
```

## 3. Later: pull updates on Alibaba

```bash
cd /root/.openclaw/workspace-margarita/engageflow
git pull origin dev
cd frontend && npm install && npm run build
# Restart backend (or docker compose restart)
```

## 4. Secrets on Alibaba

After cloning, add any env or config the app needs (e.g. `backend/.env`) on the server. Do not commit secrets to GitHub.
