## CI/CD Pipelines Overview

The following GitHub Actions workflows are used to ensure quality, containerization, and deployment across the system's components.

### 1. `appointment-lint-and-test.yml` — Lint & Test for Appointment Service
- **Purpose:** Code quality checks and unit testing for the medical appointments microservice.
- **Triggers:**
  - Pushes to files inside `appointment-service/`
  - Pull requests that modify this microservice
  - Changes to the workflow file itself
- **Features:**
  - Linting with `flake8` (critical errors and complexity)
  - Unit tests with `pytest` and HTML reports
  - Publishes test results to GitHub Pages via the `gh-pages` branch
  - Uses Python 3.11 with `uv` as package manager
  - Generates XML artifacts for CI/CD integrations

---

### 2. `appointment-service-build-and-push-docker-image.yml` — Docker Build & Push (Production)
- **Purpose:** Build and publish the production Docker image of the appointment service.
- **Triggers:**
  - Pushes to the `master` branch affecting `appointment-service/`
- **Features:**
  - Builds with Docker Buildx
  - Publishes to Docker Hub with `latest` tag
  - Requires `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets
  - Runs only on the `master` branch for production releases

---

### 3. `appointment-service-build-docker-image.yml` — Docker Build Validation (Development)
- **Purpose:** Validate Docker build on development branches for the appointment service.
- **Triggers:**
  - Pushes to any non-`master` branch that modifies `appointment-service/`
- **Features:**
  - Builds Docker image locally without publishing
  - Validates `Dockerfile` and build process
  - Uses `load: true` to load the image into the runner
  - Allows testing containerization before merging to `master`

---

### 4. `deploy-azure.yml` — Azure Infrastructure Deployment with Terraform
- **Purpose:** Automate production infrastructure deployment in Azure.
- **Triggers:**
  - Scheduled: Tuesdays and Thursdays at 9 PM UTC
  - Manual via `workflow_dispatch`
- **Features:**
  - Authenticates with Azure using a Service Principal
  - Executes `terraform plan` and `apply`
  - Deploys App Services for the frontend, API gateway, and appointment service
  - Uses infrastructure definitions from the `.iac/` directory
  - Requires secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`

---

### 5. `frontend-build-and-push-docker-image.yml` — Docker Build & Push for Frontend (Production)
- **Purpose:** Build and publish the production Docker image of the React frontend.
- **Triggers:**
  - Pushes to the `master` branch affecting `frontend/`
- **Features:**
  - Builds a production-optimized React app using Vite, TypeScript, and TailwindCSS
  - Serves the app via Nginx as defined in the Dockerfile
  - Publishes to Docker Hub with the `latest` tag

---

### 6. `frontend-build-docker-image.yml` — Frontend Build Validation (Development)
- **Purpose:** Validate frontend Docker build on development branches.
- **Triggers:**
  - Pushes to non-`master` branches modifying `frontend/`
- **Features:**
  - Installs Node.js 20 and dependencies via `npm ci`
  - Linting with ESLint before build
  - Builds the Docker image without pushing
  - Ensures code quality before merging to `master`

---

### 7. `frontend-test-deploy.yml` — Frontend Lint & Test with Coverage
- **Purpose:** Run full test suite with coverage reports for the frontend.
- **Triggers:**
  - Pushes to `main`, `master`, or `develop`
  - Pull requests targeting `main` or `master`
- **Features:**
  - Linting and tests using Vitest
  - Generates HTML coverage reports
  - Publishes reports to GitHub Pages under `/frontend`
  - Uses Node.js cache to speed up builds
  - Includes permissions required for GitHub Pages

---

### 8. `gateway-build-and-push-docker-image.yml` — Docker Build & Push for API Gateway (Production)
- **Purpose:** Build and publish the API Gateway Docker image for production.
- **Triggers:**
  - Pushes to the `master` branch affecting `api-gateway/`
- **Features:**
  - FastAPI app handling JWT authentication and service proxying
  - Publishes to Docker Hub with the `latest` tag

---

### 9. `gateway-build-docker-image.yml` — API Gateway Docker Build Validation
- **Purpose:** Validate Docker build for the API Gateway on development branches.
- **Triggers:**
  - Pushes to non-`master` branches modifying `api-gateway/`
- **Features:**
  - Local Docker build without publishing
  - Validates the gateway containerization flow

---

### 10. `gateway-lint-and-test.yml` — Lint & Test for API Gateway
- **Purpose:** Code quality and unit testing for the API Gateway.
- **Triggers:**
  - Pushes to `api-gateway/`
  - Pull requests that modify the gateway
- **Features:**
  - Linting with `flake8` for Python 3.11
  - Unit tests with `pytest`, including HTTP client mocks
  - Generates HTML test reports
  - Publishes results to GitHub Pages under `/api-gateway`
  - Uses `uv` for dependency management
