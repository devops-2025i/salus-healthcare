FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv
RUN uv pip install --system -r requirements.txt

EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
