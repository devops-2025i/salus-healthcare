output "frontend_url" {
  value = azurerm_linux_web_app.frontend.default_hostname
}

output "gateway_url" {
  value = azurerm_linux_web_app.gateway.default_hostname
}

output "appointment_service_url" {
  value = azurerm_linux_web_app.appointment_service.default_hostname
}

output "mysql_fqdn" {
  value = azurerm_mysql_flexible_server.appointments.fqdn
}

output "mysql_database_name" {
  value = azurerm_mysql_flexible_database.appointments.name
}
