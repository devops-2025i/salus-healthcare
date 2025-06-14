#!/bin/bash

# Crear directorio para Prometheus si no existe
mkdir -p /app/prometheus_data

# Sustituir variables de entorno en el archivo de configuración de Prometheus
envsubst < /app/prometheus.yml > /app/prometheus_config.yml

# Iniciar Prometheus en segundo plano
prometheus \
  --config.file=/app/prometheus_config.yml \
  --storage.tsdb.path=/app/prometheus_data \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.console.templates=/etc/prometheus/consoles \
  --web.listen-address=0.0.0.0:9090 \
  --storage.tsdb.retention.time=1h \
  --log.level=info &

# Esperar un momento para que Prometheus se inicie
sleep 5

# Verificar que Prometheus esté corriendo
if ! curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "Error: Prometheus no se pudo iniciar correctamente"
    exit 1
fi

echo "Prometheus iniciado correctamente en puerto 9090"

# Iniciar la aplicación FastAPI
echo "Iniciando appointment-service en puerto 80"
exec uvicorn main:app --host 0.0.0.0 --port 80
