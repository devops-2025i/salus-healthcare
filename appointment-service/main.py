import mysql.connector
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, ConfigDict, EmailStr
import datetime
import os
from typing import Optional, List
import logging

# OpenTelemetry imports - COMENTADOS para deshabilitar trazas
# from opentelemetry import trace
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
# from opentelemetry.sdk.resources import SERVICE_NAME, Resource
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk._logs import LoggingHandler, LoggerProvider
# from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
# from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# Prometheus imports - MANTENER ACTIVO
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram
import time
import functools

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("appointment-service")

# OpenTelemetry Tracing configuration - COMENTADO
# resource = Resource(attributes={SERVICE_NAME: "appointment-service"})
# trace.set_tracer_provider(TracerProvider(resource=resource))
# tracer = trace.get_tracer(__name__)

# otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
# span_processor = BatchSpanProcessor(otlp_exporter)
# trace.get_tracer_provider().add_span_processor(span_processor)

# logger_provider = LoggerProvider(resource=resource)
# log_exporter = OTLPLogExporter(endpoint="http://localhost:4318/v1/logs")
# log_processor = BatchLogRecordProcessor(log_exporter)
# logger_provider.add_log_record_processor(log_processor)
# otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
# logging.getLogger().addHandler(otel_handler)

# Mock tracer para reemplazar las llamadas a tracer cuando está deshabilitado
class MockTracer:
    def start_as_current_span(self, name):
        from contextlib import nullcontext
        return nullcontext()

tracer = MockTracer()
logger.info("OpenTelemetry tracing disabled - using Prometheus metrics only")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppassword")
DB_NAME = os.getenv("DB_NAME", "appointments_db")

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

app = FastAPI(title="Appointment Service", version="1.0.0")

# FastAPI OpenTelemetry instrumentation - COMENTADO
# FastAPIInstrumentor.instrument_app(app)

# Prometheus metrics integration - MANTENER ACTIVO
Instrumentator().instrument(app).expose(app)

# Prometheus custom metrics - MANTENER ACTIVO
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

DB_OPERATIONS = Counter(
    'appointment_service_db_operations_total',
    'Total database operations',
    ['operation', 'status']
)

APPOINTMENTS_CREATED = Counter(
    'appointment_service_appointments_created_total',
    'Total appointments created',
    ['status']
)

def track_metrics(endpoint_func):
    """Decorator para tracking de métricas personalizadas"""
    @functools.wraps(endpoint_func)
    def wrapper(*args, **kwargs):
        method = "GET" if "get" in endpoint_func.__name__ else "POST" if "create" in endpoint_func.__name__ else "PUT" if "update" in endpoint_func.__name__ else "DELETE"
        endpoint = endpoint_func.__name__
        start_time = time.time()
        status = "200"
        
        try:
            response = endpoint_func(*args, **kwargs)
            logger.info("Request to %s completed successfully", endpoint)
            return response
        except HTTPException as e:
            status = str(e.status_code)
            logger.warning("Request to %s failed with status %s", endpoint, status)
            raise
        except Exception as e:
            status = "500"
            logger.error("Request to %s failed with error: %s", endpoint, str(e))
            raise
        finally:
            # Record Prometheus metrics
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
    
    return wrapper

# Pydantic models
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
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

# API Endpoints
@app.post("/appointments/", response_model=AppointmentOut)
@track_metrics
def create_appointment(appointment: AppointmentCreate) -> AppointmentOut:
    logger.info("Creating appointment for %s", appointment.patient_email)
    
    # OpenTelemetry span - COMENTADO pero manteniendo la estructura
    # with tracer.start_as_current_span("create_appointment"):
    with tracer.start_as_current_span("create_appointment"):  # Mock tracer - no hace nada
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                INSERT INTO appointments (
                    patient_name, patient_email, doctor_name, doctor_specialty,
                    appointment_time, status, notes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
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
            
            # Prometheus metrics
            DB_OPERATIONS.labels(operation="insert", status="success").inc()
            APPOINTMENTS_CREATED.labels(status=appointment.status).inc()
            
            logger.info("Created appointment with ID %s", appointment_id)
            return AppointmentOut(**row)
            
        except Exception as e:
            DB_OPERATIONS.labels(operation="insert", status="error").inc()
            logger.error("Failed to create appointment: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to create appointment")
        finally:
            cursor.close()
            conn.close()

@app.get("/appointments/", response_model=List[AppointmentOut])
@track_metrics
def list_appointments() -> List[AppointmentOut]:
    logger.info("Listing all appointments")
    
    # OpenTelemetry span - COMENTADO pero manteniendo la estructura
    with tracer.start_as_current_span("list_appointments"):  # Mock tracer
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM appointments ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            # Prometheus metrics
            DB_OPERATIONS.labels(operation="select", status="success").inc()
            logger.info("Retrieved %d appointments", len(rows))
            
            return [AppointmentOut(**row) for row in rows]
            
        except Exception as e:
            DB_OPERATIONS.labels(operation="select", status="error").inc()
            logger.error("Failed to list appointments: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve appointments")
        finally:
            cursor.close()
            conn.close()

@app.get("/appointments/{appointment_id}", response_model=AppointmentOut)
@track_metrics
def get_appointment(appointment_id: int = Path(..., gt=0)) -> AppointmentOut:
    logger.info("Getting appointment with id %s", appointment_id)
    
    with tracer.start_as_current_span("get_appointment"):  # Mock tracer
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
            row = cursor.fetchone()
            
            if not row:
                DB_OPERATIONS.labels(operation="select", status="not_found").inc()
                logger.warning("Appointment with id %s not found", appointment_id)
                raise HTTPException(status_code=404, detail="Appointment not found")
            
            DB_OPERATIONS.labels(operation="select", status="success").inc()
            logger.info("Retrieved appointment with id %s", appointment_id)
            return AppointmentOut(**row)
            
        except HTTPException:
            raise
        except Exception as e:
            DB_OPERATIONS.labels(operation="select", status="error").inc()
            logger.error("Failed to get appointment: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve appointment")
        finally:
            cursor.close()
            conn.close()

@app.put("/appointments/{appointment_id}", response_model=AppointmentOut)
@track_metrics
def update_appointment(appointment_id: int, appointment: AppointmentUpdate) -> AppointmentOut:
    logger.info("Updating appointment with id %s", appointment_id)
    
    with tracer.start_as_current_span("update_appointment"):  # Mock tracer
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
            row = cursor.fetchone()
            
            if not row:
                DB_OPERATIONS.labels(operation="update", status="not_found").inc()
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
            
            DB_OPERATIONS.labels(operation="update", status="success").inc()
            logger.info("Appointment with id %s updated", appointment_id)
            
            return AppointmentOut(**updated_row)
            
        except HTTPException:
            raise
        except Exception as e:
            DB_OPERATIONS.labels(operation="update", status="error").inc()
            logger.error("Failed to update appointment: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to update appointment")
        finally:
            cursor.close()
            conn.close()

@app.delete("/appointments/{appointment_id}")
@track_metrics
def delete_appointment(appointment_id: int) -> dict[str, bool]:
    logger.info("Deleting appointment with id %s", appointment_id)
    
    with tracer.start_as_current_span("delete_appointment"):  # Mock tracer
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM appointments WHERE id = %s", (appointment_id,))
            row = cursor.fetchone()
            
            if not row:
                DB_OPERATIONS.labels(operation="delete", status="not_found").inc()
                logger.warning("Appointment with id %s not found", appointment_id)
                raise HTTPException(status_code=404, detail="Appointment not found")
            
            cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
            conn.commit()
            
            DB_OPERATIONS.labels(operation="delete", status="success").inc()
            logger.info("Appointment with id %s deleted", appointment_id)
            
            return {"ok": True}
            
        except HTTPException:
            raise
        except Exception as e:
            DB_OPERATIONS.labels(operation="delete", status="error").inc()
            logger.error("Failed to delete appointment: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to delete appointment")
        finally:
            cursor.close()
            conn.close()

@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint - sin métricas personalizadas para evitar ruido"""
    return {"status": "ok"}
