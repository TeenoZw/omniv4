# 09 – Quick Start

Bring up the active Omni Logistics stack (backend + admin + client) locally in minutes.

## Prerequisites

- Python 3.10+
- Node.js 18+

## 1. Clone & Configure

```bash
git clone <repo-url> && cd omniv3
```

## 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend docs: `http://localhost:8000/docs`

## 3. Admin Web

```bash
cd admin-web
npm install
npm run dev
```

Admin app: `http://localhost:5173`

## 4. Client Web

```bash
cd client-web
npm install
npm run dev
```

Client app: `http://localhost:5174`

---

With these steps you can run onboarding, billing, and the enquiry flow locally.
