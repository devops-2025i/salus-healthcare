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
}

resource "azurerm_resource_group" "salus" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_app_service_plan" "salus" {
  name                = var.app_service_plan_name
  location            = azurerm_resource_group.salus.location
  resource_group_name = azurerm_resource_group.salus.name
  kind                = "Linux"
  reserved            = true
  sku {
    tier = "Free"
    size = "F1"
  }
}

resource "azurerm_app_service" "frontend" {
  name                = "salus-frontend"
  location            = azurerm_resource_group.salus.location
  resource_group_name = azurerm_resource_group.salus.name
  app_service_plan_id = azurerm_app_service_plan.salus.id
  site_config {
    linux_fx_version = "DOCKER|<docker-image-frontend>"
  }
}

resource "azurerm_app_service" "gateway" {
  name                = "salus-api-gateway"
  location            = azurerm_resource_group.salus.location
  resource_group_name = azurerm_resource_group.salus.name
  app_service_plan_id = azurerm_app_service_plan.salus.id
  site_config {
    linux_fx_version = "DOCKER|<docker-image-gateway>"
  }
}

resource "azurerm_app_service" "appointment_service" {
  name                = "salus-appointment-service"
  location            = azurerm_resource_group.salus.location
  resource_group_name = azurerm_resource_group.salus.name
  app_service_plan_id = azurerm_app_service_plan.salus.id
  site_config {
    linux_fx_version = "DOCKER|<docker-image-appointment-service>"
  }
} 