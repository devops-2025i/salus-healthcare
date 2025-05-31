import pytest
import datetime
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import ValidationError

# Patch la base de datos antes de importar main
with patch("main.create_engine"), patch("main.Base"):
    from main import (
        app,
        AppointmentCreate,
        AppointmentUpdate,
        AppointmentStatus,
        get_db,
    )


# Mock de la base de datos
class MockDB:
    def __init__(self):
        self.appointments = []
        self.next_id = 1

    def add(self, appointment):
        appointment.id = self.next_id
        appointment.created_at = datetime.datetime.now()
        appointment.updated_at = datetime.datetime.now()
        self.appointments.append(appointment)
        self.next_id += 1

    def commit(self):
        pass

    def refresh(self, appointment):
        pass

    def delete(self, appointment):
        if appointment in self.appointments:
            self.appointments.remove(appointment)

    def query(self, model):
        return MockQuery(self.appointments)


class MockQuery:
    def __init__(self, appointments):
        self.appointments = appointments
        self.filter_id = None

    def filter(self, condition):
        # Simular filtro por ID - extraer el valor del ID de la condición SQLAlchemy
        mock_query = MockQuery(self.appointments)

        # El condition es una expresión SQLAlchemy como "Appointment.id == appointment_id"
        # Extraemos el valor del lado derecho de la comparación
        if hasattr(condition, "right") and hasattr(condition.right, "value"):
            mock_query.filter_id = condition.right.value
        elif hasattr(condition, "right"):
            # En caso de que sea un valor directo
            mock_query.filter_id = condition.right

        return mock_query

    def first(self):
        # Si hay un filtro por ID, buscar por ID
        if self.filter_id is not None:
            for appt in self.appointments:
                if hasattr(appt, "id") and appt.id == self.filter_id:
                    return appt
            return None
        # Si no hay filtro, devolver el primero
        return self.appointments[0] if self.appointments else None

    def all(self):
        return self.appointments


# Mock database instance
mock_db = MockDB()


def override_get_db():
    return mock_db


# Override dependency
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestAppointmentModels:
    """Test Pydantic models"""

    def test_appointment_create_valid(self):
        """Test valid appointment creation"""
        data = {
            "patient_name": "Juan Pérez",
            "patient_email": "juan@example.com",
            "doctor_name": "Dr. García",
            "doctor_specialty": "Cardiología",
            "appointment_time": datetime.datetime(2024, 7, 1, 10, 0),
        }
        appointment = AppointmentCreate(**data)
        assert appointment.patient_name == "Juan Pérez"
        assert appointment.status == "scheduled"  # Default

    def test_appointment_create_invalid_email(self):
        """Test invalid email"""
        data = {
            "patient_name": "Test",
            "patient_email": "invalid-email",
            "doctor_name": "Dr. Test",
            "doctor_specialty": "Test",
            "appointment_time": datetime.datetime(2024, 7, 1, 10, 0),
        }
        with pytest.raises(ValidationError):
            AppointmentCreate(**data)

    def test_appointment_update_partial(self):
        """Test partial update"""
        update = AppointmentUpdate(patient_name="Updated Name")
        assert update.patient_name == "Updated Name"
        assert update.doctor_name is None


class TestAppointmentStatus:
    """Test appointment status enum"""

    def test_status_values(self):
        """Test enum values"""
        assert AppointmentStatus.scheduled.value == "scheduled"
        assert AppointmentStatus.cancelled.value == "cancelled"
        assert AppointmentStatus.completed.value == "completed"
        assert AppointmentStatus.rescheduled.value == "rescheduled"


class TestHealthEndpoint:
    """Test health endpoint"""

    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAppointmentAPI:
    """Test appointment CRUD operations"""

    def setup_method(self):
        """Clean mock database before each test"""
        mock_db.appointments.clear()
        mock_db.next_id = 1

    def test_create_appointment(self):
        """Test appointment creation"""
        appointment_data = {
            "patient_name": "María González",
            "patient_email": "maria@example.com",
            "doctor_name": "Dr. Rodríguez",
            "doctor_specialty": "Pediatría",
            "appointment_time": "2024-07-01T10:00:00",
        }

        response = client.post("/appointments/", json=appointment_data)
        assert response.status_code == 200

        data = response.json()
        assert data["patient_name"] == "María González"
        assert data["status"] == "scheduled"
        assert "id" in data
        assert len(mock_db.appointments) == 1

    def test_create_appointment_invalid_data(self):
        """Test appointment creation with invalid data"""
        appointment_data = {
            "patient_name": "Test",
            "patient_email": "invalid-email",
        }

        response = client.post("/appointments/", json=appointment_data)
        assert response.status_code == 422

    def test_list_appointments(self):
        """Test listing appointments"""
        # Create test data
        mock_appointment = MagicMock()
        mock_appointment.id = 1
        mock_appointment.patient_name = "Test Patient"
        mock_appointment.patient_email = "test@example.com"
        mock_appointment.doctor_name = "Dr. Test"
        mock_appointment.doctor_specialty = "Test"
        mock_appointment.appointment_time = datetime.datetime.now()
        mock_appointment.status = "scheduled"
        mock_appointment.notes = None
        mock_appointment.created_at = datetime.datetime.now()
        mock_appointment.updated_at = datetime.datetime.now()

        mock_db.appointments.append(mock_appointment)

        response = client.get("/appointments/")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["patient_name"] == "Test Patient"

    def test_list_appointments_empty(self):
        """Test listing empty appointments"""
        response = client.get("/appointments/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_appointment(self):
        """Test getting specific appointment"""
        # Create mock appointment
        mock_appointment = MagicMock()
        mock_appointment.id = 1
        mock_appointment.patient_name = "Test Patient"
        mock_appointment.patient_email = "test@example.com"
        mock_appointment.doctor_name = "Dr. Test"
        mock_appointment.doctor_specialty = "Test"
        mock_appointment.appointment_time = datetime.datetime.now()
        mock_appointment.status = "scheduled"
        mock_appointment.notes = None
        mock_appointment.created_at = datetime.datetime.now()
        mock_appointment.updated_at = datetime.datetime.now()

        mock_db.appointments.append(mock_appointment)

        response = client.get("/appointments/1")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == 1
        assert data["patient_name"] == "Test Patient"

    def test_get_appointment_not_found(self):
        """Test getting non-existent appointment"""
        response = client.get("/appointments/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Appointment not found"

    def test_get_appointment_invalid_id(self):
        """Test getting appointment with invalid ID"""
        response = client.get("/appointments/0")
        assert response.status_code == 422

    def test_update_appointment(self):
        """Test updating appointment"""
        # Create mock appointment
        mock_appointment = MagicMock()
        mock_appointment.id = 1
        mock_appointment.patient_name = "Original Patient"
        mock_appointment.patient_email = "original@example.com"
        mock_appointment.doctor_name = "Dr. Original"
        mock_appointment.doctor_specialty = "Original"
        mock_appointment.appointment_time = datetime.datetime.now()
        mock_appointment.status = "scheduled"
        mock_appointment.notes = None
        mock_appointment.created_at = datetime.datetime.now()
        mock_appointment.updated_at = datetime.datetime.now()

        mock_db.appointments.append(mock_appointment)

        update_data = {"patient_name": "Updated Patient", "status": "completed"}
        response = client.put("/appointments/1", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["patient_name"] == "Updated Patient"
        assert data["status"] == "completed"

    def test_update_appointment_not_found(self):
        """Test updating non-existent appointment"""
        update_data = {"status": "completed"}
        response = client.put("/appointments/999", json=update_data)
        assert response.status_code == 404

    def test_delete_appointment(self):
        """Test deleting appointment"""
        # Create mock appointment
        mock_appointment = MagicMock()
        mock_appointment.id = 1
        mock_db.appointments.append(mock_appointment)

        response = client.delete("/appointments/1")
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        assert len(mock_db.appointments) == 0

    def test_delete_appointment_not_found(self):
        """Test deleting non-existent appointment"""
        response = client.delete("/appointments/999")
        assert response.status_code == 404


class TestValidation:
    """Test validation edge cases"""

    def setup_method(self):
        """Clean mock database before each test"""
        mock_db.appointments.clear()
        mock_db.next_id = 1

    def test_special_characters(self):
        """Test special characters in names"""
        appointment_data = {
            "patient_name": "José María Ñoño",
            "patient_email": "jose@example.com",
            "doctor_name": "Dr. García-López",
            "doctor_specialty": "Médico General",
            "appointment_time": "2024-07-01T10:00:00",
        }

        response = client.post("/appointments/", json=appointment_data)
        assert response.status_code == 200
        assert response.json()["patient_name"] == "José María Ñoño"

    def test_long_notes(self):
        """Test long notes field"""
        appointment_data = {
            "patient_name": "Test Patient",
            "patient_email": "test@example.com",
            "doctor_name": "Dr. Test",
            "doctor_specialty": "Test",
            "appointment_time": "2024-07-01T10:00:00",
            "notes": "A" * 500,  # Long text
        }

        response = client.post("/appointments/", json=appointment_data)
        assert response.status_code == 200
        assert len(response.json()["notes"]) == 500

    def test_invalid_datetime(self):
        """Test invalid datetime format"""
        appointment_data = {
            "patient_name": "Test Patient",
            "patient_email": "test@example.com",
            "doctor_name": "Dr. Test",
            "doctor_specialty": "Test",
            "appointment_time": "invalid-datetime",
        }

        response = client.post("/appointments/", json=appointment_data)
        assert response.status_code == 422


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test"""
    yield
    mock_db.appointments.clear()
    mock_db.next_id = 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
