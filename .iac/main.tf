terraform {
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
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "salus" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_service_plan" "salus" {
  name                = var.app_service_plan_name
  location            = azurerm_resource_group.salus.location
  resource_group_name = azurerm_resource_group.salus.name
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_mysql_flexible_server" "appointments" {
  name                   = "appointments-mysql"
  resource_group_name    = azurerm_resource_group.salus.name
  location               = azurerm_resource_group.salus.location
  administrator_login    = var.appointments_mysql_admin_username
  administrator_password = var.appointments_mysql_admin_password
  sku_name               = "B_Standard_B1ms"
  version                = "8.0.21"
  #zone                   = "1"
  backup_retention_days  = 7
  geo_redundant_backup_enabled = false
}

resource "azurerm_mysql_flexible_database" "appointments" {
  name                = var.appointments_mysql_database_name
  resource_group_name = azurerm_resource_group.salus.name
  server_name         = azurerm_mysql_flexible_server.appointments.name
  charset             = "utf8"
  collation           = "utf8_unicode_ci"

  depends_on = [azurerm_mysql_flexible_server.appointments]
}

resource "azurerm_mysql_flexible_server_firewall_rule" "allow_azure_services" {
  name                = "AllowAzureServices"
  resource_group_name = azurerm_resource_group.salus.name
  server_name         = azurerm_mysql_flexible_server.appointments.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"

  depends_on = [azurerm_mysql_flexible_server.appointments]
}

resource "azurerm_linux_web_app" "frontend" {
  name                = "salus-frontend"
  location            = azurerm_resource_group.salus.location
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
  name                = "salus-api-gateway"
  location            = azurerm_resource_group.salus.location
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
  name                = "salus-appointment-service"
  location            = azurerm_resource_group.salus.location
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
  }

  depends_on = [azurerm_service_plan.salus, azurerm_mysql_flexible_server.appointments]
}
