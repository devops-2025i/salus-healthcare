variable "resource_group_name" {
  description = "Nombre del resource group de Azure."
  type        = string
  default     = "salus-rg"
}

variable "location" {
  description = "Ubicación de los recursos de Azure."
  type        = string
  default     = "East US"
}

variable "app_service_plan_name" {
  description = "Nombre del App Service Plan."
  type        = string
  default     = "salus-asp"
} 