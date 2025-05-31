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
    db_appointment = Appointment(**appointment.model_dump())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return AppointmentOut.model_validate(db_appointment)


@app.get("/appointments/", response_model=List[AppointmentOut])
def list_appointments(db: Session = Depends(get_db)) -> List[AppointmentOut]:
    appointments = db.query(Appointment).all()
    return [AppointmentOut.model_validate(appt) for appt in appointments]


@app.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: int = Path(..., gt=0), db: Session = Depends(get_db)
) -> AppointmentOut:
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return AppointmentOut.model_validate(appt)


@app.put("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int, appointment: AppointmentUpdate, db: Session = Depends(get_db)
) -> AppointmentOut:
    db_appointment = (
        db.query(Appointment).filter(Appointment.id == appointment_id).first()
    )
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    for field, value in appointment.model_dump(exclude_unset=True).items():
        setattr(db_appointment, field, value)

    db.commit()
    db.refresh(db_appointment)
    return AppointmentOut.model_validate(db_appointment)


@app.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int, db: Session = Depends(get_db)
) -> dict[str, bool]:
    db_appointment = (
        db.query(Appointment).filter(Appointment.id == appointment_id).first()
    )
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    db.delete(db_appointment)
    db.commit()
    return {"ok": True}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Solo crear tablas si se ejecuta directamente (no en tests)
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
