import mysql.connector
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, ConfigDict, EmailStr
import datetime
import os
from typing import Optional, List
import logging
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggingHandler, LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram
import time

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("appointment-service")

# OpenTelemetry Tracing configuration
resource = Resource(attributes={SERVICE_NAME: "appointment-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

logger_provider = LoggerProvider(resource=resource)
log_exporter = OTLPLogExporter()
log_processor = BatchLogRecordProcessor(log_exporter)
logger_provider.add_log_record_processor(log_processor)
otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(otel_handler)


# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "appointments_db")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppassword")


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


app = FastAPI(title="Appointment Service", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)

# Prometheus metrics integration
Instrumentator().instrument(app).expose(app)

# Prometheus custom metrics
REQUEST_COUNT = Counter(
    'appointment_service_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'appointment_service_request_latency_seconds',
    'Request latency',
    ['method', 'endpoint']
)


def track_metrics(endpoint_func):
    def wrapper(*args, **kwargs):
        method = endpoint_func.__name__
        endpoint = f"/{endpoint_func.__name__}"
        start_time = time.time()
        try:
            response = endpoint_func(*args, **kwargs)
            status = getattr(response, 'status_code', 200)
        except Exception as e:
            status = 500
            raise
        finally:
            REQUEST_COUNT.labels(method, endpoint, status).inc()
            REQUEST_LATENCY.labels(method, endpoint).observe(time.time() - start_time)
        return response
    return wrapper


class AppointmentBase(BaseModel):
    patient_name: str
    patient_email: EmailStr
    doctor_name: str
    doctor_specialty: str
    appointment_time: datetime.datetime
    status: Optional[str] = "scheduled"
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    patient_name: Optional[str] = None
    patient_email: Optional[EmailStr] = None
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    appointment_time: Optional[datetime.datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AppointmentOut(AppointmentBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


@app.post("/appointments/", response_model=AppointmentOut)
@track_metrics
def create_appointment(appointment: AppointmentCreate) -> AppointmentOut:
    logger.info("Creating appointment for %s", appointment.patient_email)
    with tracer.start_as_current_span("create_appointment"):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = ("""
            INSERT INTO appointments (
                patient_name, patient_email, doctor_name, doctor_specialty,
                appointment_time, status, notes, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """)
        values = (
            appointment.patient_name,
            appointment.patient_email,
            appointment.doctor_name,
            appointment.doctor_specialty,
            appointment.appointment_time,
            appointment.status,
            appointment.notes,
        )
        cursor.execute(query, values)
        conn.commit()
        appointment_id = cursor.lastrowid
        cursor.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create appointment")
        return AppointmentOut(**row)


@app.get("/appointments/", response_model=List[AppointmentOut])
@track_metrics
def list_appointments() -> List[AppointmentOut]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM appointments")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [AppointmentOut(**row) for row in rows]


@app.get("/appointments/{appointment_id}", response_model=AppointmentOut)
@track_metrics
def get_appointment(appointment_id: int = Path(..., gt=0)) -> AppointmentOut:
    logger.info("Listing all appointments")
    with tracer.start_as_current_span("list_appointments"):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            logger.info("Appointment with id %s not found", appointment_id)
            raise HTTPException(status_code=404, detail="Appointment not found")
        return AppointmentOut(**row)


@app.put("/appointments/{appointment_id}", response_model=AppointmentOut)
@track_metrics
def update_appointment(appointment_id: int, appointment: AppointmentUpdate) -> AppointmentOut:
    logger.info("Updating appointment with id %s", appointment_id)
    with tracer.start_as_current_span("update_appointment"):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            logger.info("Appointment with id %s not found", appointment_id)
            raise HTTPException(status_code=404, detail="Appointment not found")
        fields = []
        values = []
        for field, value in appointment.model_dump(exclude_unset=True).items():
            fields.append(f"{field} = %s")
            values.append(value)
        if fields:
            update_query = f"UPDATE appointments SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s"
            values.append(appointment_id)
            cursor.execute(update_query, tuple(values))
            conn.commit()
        cursor.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
        updated_row = cursor.fetchone()
        logger.info("Appointment with id %s updated", appointment_id)
        cursor.close()
        conn.close()
        return AppointmentOut(**updated_row)


@app.delete("/appointments/{appointment_id}")
@track_metrics
def delete_appointment(appointment_id: int) -> dict[str, bool]:
    logger.info("Deleting appointment with id %s", appointment_id)
    with tracer.start_as_current_span("delete_appointment"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM appointments WHERE id = %s", (appointment_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            logger.warning("Appointment with id %s not found", appointment_id)
            raise HTTPException(status_code=404, detail="Appointment not found")
        cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Appointment with id %s deleted", appointment_id)
        return {"ok": True}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

# Nota: Ya no se crean tablas automáticamente, debes crearlas manualmente en la base de datos.
