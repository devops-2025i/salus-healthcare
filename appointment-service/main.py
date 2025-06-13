from fastapi import FastAPI, HTTPException, Depends, Path
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import datetime
import os
import enum
from typing import Optional, Generator, List
from pydantic import EmailStr
import logging
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggingHandler, LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, OTLPLogExporter

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
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Solo crear engine y base, NO crear tablas automáticamente
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
SQLAlchemyInstrumentor().instrument(engine=engine)


class AppointmentStatus(enum.Enum):
    scheduled = "scheduled"
    cancelled = "cancelled"
    completed = "completed"
    rescheduled = "rescheduled"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(100), nullable=False)
    patient_email = Column(String(100), nullable=False)
    doctor_name = Column(String(100), nullable=False)
    doctor_specialty = Column(String(100), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(
        TIMESTAMP, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP"
    )


app = FastAPI(title="Appointment Service", version="1.0.0")
FastAPIInstrumentor.instrument_app(app)


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
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# Database dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API endpoints
@app.post("/appointments/", response_model=AppointmentOut)
def create_appointment(
    appointment: AppointmentCreate, db: Session = Depends(get_db)
) -> AppointmentOut:
    logger.info("Creating appointment for %s", appointment.patient_email)
    with tracer.start_as_current_span("create_appointment"):
        db_appointment = Appointment(**appointment.model_dump())
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        logger.info("Appointment created with id %s", db_appointment.id)
        return AppointmentOut.model_validate(db_appointment)


@app.get("/appointments/", response_model=List[AppointmentOut])
def list_appointments(db: Session = Depends(get_db)) -> List[AppointmentOut]:
    logger.info("Listing all appointments")
    with tracer.start_as_current_span("list_appointments"):
        appointments = db.query(Appointment).all()
        return [AppointmentOut.model_validate(appt) for appt in appointments]


@app.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: int = Path(..., gt=0), db: Session = Depends(get_db)
) -> AppointmentOut:
    logger.info("Getting appointment with id %s", appointment_id)
    with tracer.start_as_current_span("get_appointment"):
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            logger.warning("Appointment with id %s not found", appointment_id)
            raise HTTPException(status_code=404, detail="Appointment not found")
        return AppointmentOut.model_validate(appt)


@app.put("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int, appointment: AppointmentUpdate, db: Session = Depends(get_db)
) -> AppointmentOut:
    logger.info("Updating appointment with id %s", appointment_id)
    with tracer.start_as_current_span("update_appointment"):
        db_appointment = (
            db.query(Appointment).filter(Appointment.id == appointment_id).first()
        )
        if not db_appointment:
            logger.warning("Appointment with id %s not found", appointment_id)
            raise HTTPException(status_code=404, detail="Appointment not found")

        for field, value in appointment.model_dump(exclude_unset=True).items():
            setattr(db_appointment, field, value)

        db.commit()
        db.refresh(db_appointment)
        logger.info("Appointment with id %s updated", appointment_id)
        return AppointmentOut.model_validate(db_appointment)


@app.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int, db: Session = Depends(get_db)
) -> dict[str, bool]:
    logger.info("Deleting appointment with id %s", appointment_id)
    with tracer.start_as_current_span("delete_appointment"):
        db_appointment = (
            db.query(Appointment).filter(Appointment.id == appointment_id).first()
        )
        if not db_appointment:
            logger.warning("Appointment with id %s not found", appointment_id)
            raise HTTPException(status_code=404, detail="Appointment not found")

        db.delete(db_appointment)
        db.commit()
        logger.info("Appointment with id %s deleted", appointment_id)
        return {"ok": True}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Solo crear tablas si se ejecuta directamente (no en tests)
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
