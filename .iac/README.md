## Infrastructure as Code for Salus Healthcare (Terraform + Azure)

This directory contains the Terraform solution for provisioning and managing the core infrastructure of the Salus Healthcare project. The setup is fully integrated with Terraform Cloud (TFC) and Azure, and is connected to this GitHub repository for automated and auditable deployments.

### Overview

The infrastructure defined here provisions the following main components:

- **Frontend Portal**: Azure App Service hosting the user-facing web application.
- **API Gateway**: Azure App Service acting as the main entry point and reverse proxy for backend services.
- **Appointment Microservice**: Azure App Service running the appointments backend (FastAPI/Python).
- **Appointments Database**: Azure Flexible MySQL instance dedicated to the appointments microservice.

All resources are managed as code using Terraform, with state and execution handled by Terraform Cloud. This enables team collaboration, version control, and safe, repeatable deployments.

### Key Features
- **Terraform Cloud Integration**: State management, remote execution, and policy enforcement are handled by TFC, linked to this GitHub repository.
- **Azure Resource Provisioning**: All core services are deployed to Azure, including App Services and managed MySQL.
- **Modular & Auditable**: Infrastructure changes are tracked via pull requests and GitHub Actions, ensuring traceability and review.

### How it Works
1. **Edit Infrastructure**: Make changes to the Terraform files in this directory (`.iac/`).
2. **Version Control**: Changes are pushed to GitHub, triggering validation workflows.
3. **Terraform Cloud**: TFC automatically detects changes, runs `plan` and (if approved) `apply` to update Azure resources.
4. **Azure**: All resources are provisioned and updated according to the latest configuration.

### Main Files
- `main.tf`: Main resource definitions for Azure (App Services, MySQL, etc).
- `variables.tf`: Input variables for customizing resource names, locations, and credentials.

### Requirements
- Access to the linked Terraform Cloud organization and workspace.
- Azure credentials with permissions to create and manage resources.
- (Optional) GitHub Actions for automated validation and deployment.

---
