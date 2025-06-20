terraform {
  backend "remote" {
    organization = "fund-devops-2025i"

    workspaces {
      name = "salus-infra-dev"
    }
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0"
    }
  }
  required_version = ">= 1.0.0"
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "salus" {
  name     = var.resource_group_name
  location = var.rg_location
}


resource "random_string" "asp_suffix" {
  length  = 4
  upper   = false
  special = false
}

resource "azurerm_service_plan" "salus" {
  name                = "salus-asp-${random_string.asp_suffix.result}"
  resource_group_name = azurerm_resource_group.salus.name
  location            = var.asp_location
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_mysql_flexible_server" "appointments" {
  name                   = "appointments-mysql-2"
  resource_group_name    = azurerm_resource_group.salus.name
  administrator_login    = var.appointments_mysql_admin_username
  administrator_password = var.appointments_mysql_admin_password
  location               = var.db_location
  sku_name               = "B_Standard_B1ms"
  version                = "8.0.21"
  #zone                   = "1"
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false
}

resource "azurerm_mysql_flexible_database" "appointments" {
  name                = var.appointments_mysql_database_name
  resource_group_name = azurerm_resource_group.salus.name
  server_name         = azurerm_mysql_flexible_server.appointments.name
  charset   = "utf8mb3"
  collation = "utf8mb3_unicode_ci"

  depends_on = [azurerm_mysql_flexible_server.appointments]
}

resource "azurerm_mysql_flexible_server_firewall_rule" "allow_azure_services" {
  name                = "AllowAzureServices"
  resource_group_name = azurerm_resource_group.salus.name
  server_name         = azurerm_mysql_flexible_server.appointments.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"

  depends_on = [azurerm_mysql_flexible_server.appointments, azurerm_mysql_flexible_database.appointments]
}

resource "azurerm_linux_web_app" "frontend" {
  name                = "salus-frontend-2"
  location            = azurerm_service_plan.salus.location
  resource_group_name = azurerm_resource_group.salus.name
  service_plan_id     = azurerm_service_plan.salus.id

  site_config {
    always_on = false
  }

  app_settings = {
    # DOCKER_CUSTOM_IMAGE_NAME = "ialemusm/salus-frontend:latest"
    API_GATEWAY_URL = "https://${azurerm_linux_web_app.gateway.default_hostname}"
  }

  depends_on = [azurerm_service_plan.salus, azurerm_mysql_flexible_server.appointments]
}

resource "azurerm_linux_web_app" "gateway" {
  name                = "salus-api-gateway-2"
  location            = azurerm_service_plan.salus.location
  resource_group_name = azurerm_resource_group.salus.name
  service_plan_id     = azurerm_service_plan.salus.id

  site_config {
    always_on = false
  }

  app_settings = {
    # DOCKER_CUSTOM_IMAGE_NAME = "ialemusm/salus-api-gateway:latest"
    APPOINTMENT_SERVICE_URL = "https://${azurerm_linux_web_app.appointment_service.default_hostname}"
  }

  depends_on = [azurerm_service_plan.salus, azurerm_mysql_flexible_server.appointments]
}

resource "azurerm_linux_web_app" "appointment_service" {
  name                = "salus-appointment-service-2"
  location            = azurerm_service_plan.salus.location
  resource_group_name = azurerm_resource_group.salus.name
  service_plan_id     = azurerm_service_plan.salus.id

  site_config {
    always_on = false
  }

  app_settings = {
    # DOCKER_CUSTOM_IMAGE_NAME = "ialemusm/salus-appointment-service:latest"
    DB_HOST     = azurerm_mysql_flexible_server.appointments.fqdn
    DB_PORT     = "3306"
    DB_NAME     = var.appointments_mysql_database_name
    DB_USER     = var.appointments_mysql_admin_username
    DB_PASSWORD = var.appointments_mysql_admin_password
    
    # === NUEVAS VARIABLES DE OBSERVABILIDAD ===
    GRAFANA_API_TOKEN           = var.grafana_api_token
    GRAFANA_PROMETHEUS_URL      = var.grafana_prometheus_url
    GRAFANA_PROMETHEUS_USERNAME = var.grafana_prometheus_username
  }

  depends_on = [azurerm_service_plan.salus, azurerm_mysql_flexible_server.appointments]
}

resource "random_string" "demo_suffix" {
  length  = 4
  upper   = false
  special = false
}
