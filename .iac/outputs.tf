output "frontend_url" {
  value = azurerm_app_service.frontend.default_site_hostname
}

output "gateway_url" {
  value = azurerm_app_service.gateway.default_site_hostname
}

output "appointment_service_url" {
  value = azurerm_app_service.appointment_service.default_site_hostname
} 