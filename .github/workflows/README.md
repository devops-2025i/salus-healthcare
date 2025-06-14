## CI/CD Pipelines Overview

This repository uses several GitHub Actions workflows to ensure quality, integration, deployment, and continuous delivery for the main services: Appointment Service, API Gateway, Frontend, and Azure infrastructure.

---

### 1. `appointment-service-continuous-integration.yml` — Lint & Test for Appointment Service
- **Purpose:** Validate code quality and run unit tests for the medical appointments microservice.
- **Triggers:**
  - Push or pull request that modifies `appointment-service/` or the workflow file itself.
- **Features:**
  - Linting with `flake8` (critical errors and complexity)
  - Unit tests with `pytest` and HTML reports
  - Uses Python 3.11 and `uv` as package manager
  - Uploads test result artifacts

---

### 2. `appointment-service-deployment.yml` — Build, Push & Deploy for Appointment Service
- **Purpose:** Build, publish, and deploy the Appointment Service Docker image to Azure App Service.
- **Triggers:**
  - Push to the `master` branch affecting `appointment-service/`
  - Manual execution via `workflow_dispatch`
- **Features:**
  - Runs unit tests before building
  - Builds and pushes the image to Docker Hub
  - Deploys the image to Azure App Service using the commit tag
  - Requires secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `AZURE_CREDENTIALS`

---

### 3. `gateway-continuous-integration.yml` — Lint & Test for API Gateway
- **Purpose:** Validate code quality and run unit tests for the API Gateway.
- **Triggers:**
  - Push or pull request that modifies `api-gateway/` or the workflow file itself.
- **Features:**
  - Linting with `flake8`
  - Unit tests with `pytest` and HTML reports
  - Uses Python 3.11 and `uv` as package manager
  - Uploads test result artifacts

---

### 4. `gateway-deployment.yml` — Build, Push & Deploy for API Gateway
- **Purpose:** Build, publish, and deploy the API Gateway Docker image to Azure App Service.
- **Triggers:**
  - Push to the `master` branch affecting `api-gateway/`
  - Manual execution via `workflow_dispatch`
- **Features:**
  - Runs unit tests before building
  - Builds and pushes the image to Docker Hub
  - Deploys the image to Azure App Service using the commit tag
  - Requires secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `AZURE_CREDENTIALS`

---

### 5. `frontend-continuous-integration.yml` — Lint & Test for Frontend
- **Purpose:** Validate code quality and run tests for the React frontend.
- **Triggers:**
  - Push or pull request that modifies `frontend/` or the workflow file itself.
- **Features:**
  - Linting with ESLint
  - Tests with Vitest and coverage
  - Uses Node.js 20
  - Uploads coverage and report artifacts

---

### 6. `frontend-deployment.yml` — Build, Push & Deploy for Frontend
- **Purpose:** Build, publish, and deploy the frontend Docker image to Azure App Service.
- **Triggers:**
  - Push to the `master` branch affecting `frontend/`
  - Manual execution via `workflow_dispatch`
- **Features:**
  - Builds and pushes the image to Docker Hub
  - Deploys the image to Azure App Service using the commit tag
  - Requires secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `AZURE_CREDENTIALS`

---

### 7. `terraform.yml` — Infrastructure as Code (IaC) with Terraform
- **Purpose:** Automate validation and deployment of Azure infrastructure using Terraform.
- **Triggers:**
  - Push or pull request that modifies `.iac/` or the workflow file itself.
- **Features:**
  - Initializes and runs `terraform plan` in the `.iac` folder
  - Uses the `TF_API_TOKEN` for authentication

---

Each workflow is designed to run automatically on relevant changes and can also be triggered manually (when `workflow_dispatch` is present). See each YAML file for advanced details or custom inputs.
