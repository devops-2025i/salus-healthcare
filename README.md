# Salus MVP

A monorepo for a healthcare SaaS MVP.

## Structure

- `frontend/`: React + Vite + TypeScript + TailwindCSS UI
- `api-gateway/`: FastAPI gateway with JWT auth, managed by `uv`
- `appointment-service/`: FastAPI microservice for appointments, SQLite, managed by `uv`
- `.github/`: CI/CD workflows
- `.iac/`: Terraform stubs for future infra

## Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### API Gateway

```bash
cd api-gateway
uv venv
uv pip install -r requirements.txt
uvicorn main:app --reload
```

### Appointment Service

```bash
cd appointment-service
uv venv
uv pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Docker

Each Python service has a Dockerfile for containerized runs.

### CI/CD

GitHub Actions in `.github/workflows/` build and lint all services.

### IaC

Terraform stubs in `.iac/` for future infrastructure.

---

## Next Steps

- Expand microservices
- Add monitoring/logging infra
- Implement full authentication/authorization