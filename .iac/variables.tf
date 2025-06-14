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

variable "appointments_mysql_admin_username" {
  description = "MySQL admin username para appointments"
  type        = string
  default     = "appuser"
}

variable "appointments_mysql_admin_password" {
  description = "MySQL admin password para appointments"
  type        = string
  sensitive   = true
  default     = "User12345#"
}

variable "appointments_mysql_database_name" {
  description = "Nombre de la base de datos appointments"
  type        = string
  default     = "appointments_db"
}
