FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para Prometheus
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Descargar e instalar Prometheus
RUN wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz \
    && tar xvfz prometheus-2.45.0.linux-amd64.tar.gz \
    && mv prometheus-2.45.0.linux-amd64/prometheus /usr/local/bin/ \
    && mv prometheus-2.45.0.linux-amd64/promtool /usr/local/bin/ \
    && mkdir -p /etc/prometheus \
    && mv prometheus-2.45.0.linux-amd64/console_libraries /etc/prometheus/ \
    && mv prometheus-2.45.0.linux-amd64/consoles /etc/prometheus/ \
    && rm -rf prometheus-2.45.0.linux-amd64*

WORKDIR /app
COPY . .

# Instalar dependencias de Python
RUN pip install uv
RUN uv pip install --system -r requirements.txt

# Hacer el script de inicio ejecutable
RUN chmod +x /app/start.sh

# Exponer puertos para FastAPI (80) y Prometheus (9090)
EXPOSE 80 9090

# Usar el script de inicio personalizado
CMD ["/app/start.sh"]
