# 07 – Contributing

## Active Modules

- `backend/`
- `admin-web/`
- `client-web/`
- `docs/`

Legacy services live under `archive/` and are not part of active development.

## Local Setup

```bash
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd admin-web && npm install
cd client-web && npm install
```

## Testing

```bash
cd backend && pytest
```

## Branching

- Use short feature branches and keep PRs focused.
- Update documentation for any workflow changes.
