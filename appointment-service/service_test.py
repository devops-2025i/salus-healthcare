import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app, AppointmentCreate, AppointmentUpdate
import datetime

client = TestClient(app)

# -------------------
# Model tests
# -------------------
def test_appointment_create_valid():
    data = {
        "patient_name": "Juan Pérez",
        "patient_email": "juan@example.com",
        "doctor_name": "Dr. García",
        "doctor_specialty": "Cardiología",
        "appointment_time": datetime.datetime(2024, 7, 1, 10, 0),
    }
    appointment = AppointmentCreate(**data)
    assert appointment.patient_name == "Juan Pérez"
    assert appointment.status == "scheduled"

def test_appointment_create_invalid_email():
    data = {
        "patient_name": "Test",
        "patient_email": "invalid-email",
        "doctor_name": "Dr. Test",
        "doctor_specialty": "Test",
        "appointment_time": datetime.datetime(2024, 7, 1, 10, 0),
    }
    with pytest.raises(Exception):
        AppointmentCreate(**data)

def test_appointment_update_partial():
    update = AppointmentUpdate(patient_name="Updated Name")
    assert update.patient_name == "Updated Name"
    assert update.doctor_name is None

# -------------------
# API endpoint tests (mocking mysql.connector)
# -------------------
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_appointments():
    fake_appointments = [
        {
            "id": 1,
            "patient_name": "Test Patient",
            "patient_email": "test@example.com",
            "doctor_name": "Dr. Test",
            "doctor_specialty": "Test",
            "appointment_time": "2024-07-01T10:00:00",
            "status": "scheduled",
            "notes": None,
            "created_at": "2024-06-13T10:00:00",
            "updated_at": "2024-06-13T10:00:00"
        }
    ]
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = fake_appointments
        response = client.get("/appointments/")
        assert response.status_code == 200
        assert response.json() == fake_appointments

def test_list_appointments_empty():
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        response = client.get("/appointments/")
        assert response.status_code == 200
        assert response.json() == []

def test_get_appointment():
    fake_row = {
        "id": 1,
        "patient_name": "Test Patient",
        "patient_email": "test@example.com",
        "doctor_name": "Dr. Test",
        "doctor_specialty": "Test",
        "appointment_time": "2024-07-01T10:00:00",
        "status": "scheduled",
        "notes": None,
        "created_at": "2024-06-13T10:00:00",
        "updated_at": "2024-06-13T10:00:00"
    }
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = fake_row
        response = client.get("/appointments/1")
        assert response.status_code == 200
        assert response.json() == fake_row

def test_get_appointment_not_found():
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        response = client.get("/appointments/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Appointment not found"

def test_create_appointment():
    appointment_data = {
        "patient_name": "María González",
        "patient_email": "maria@example.com",
        "doctor_name": "Dr. Rodríguez",
        "doctor_specialty": "Pediatría",
        "appointment_time": "2024-07-01T10:00:00",
    }
    fake_row = {
        "id": 1,
        "patient_name": "María González",
        "patient_email": "maria@example.com",
        "doctor_name": "Dr. Rodríguez",
        "doctor_specialty": "Pediatría",
        "appointment_time": "2024-07-01T10:00:00",
        "status": "scheduled",
        "notes": None,
        "created_at": "2024-06-13T10:00:00",
        "updated_at": "2024-06-13T10:00:00"
    }
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.return_value = fake_row
        response = client.post("/appointments/", json=appointment_data)
        assert response.status_code == 200
        assert response.json() == fake_row

def test_create_appointment_invalid_data():
    appointment_data = {
        "patient_name": "Test",
        "patient_email": "invalid-email",
    }
    response = client.post("/appointments/", json=appointment_data)
    assert response.status_code == 422

def test_update_appointment():
    update_data = {"patient_name": "Updated Patient", "status": "completed"}
    fake_row = {
        "id": 1,
        "patient_name": "Updated Patient",
        "patient_email": "test@example.com",
        "doctor_name": "Dr. Test",
        "doctor_specialty": "Test",
        "appointment_time": "2024-07-01T10:00:00",
        "status": "completed",
        "notes": None,
        "created_at": "2024-06-13T10:00:00",
        "updated_at": "2024-06-13T10:00:00"
    }
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        # Simula que existe el registro antes de actualizar
        mock_cursor.fetchone.side_effect = [fake_row, fake_row]
        response = client.put("/appointments/1", json=update_data)
        assert response.status_code == 200
        assert response.json() == fake_row

def test_update_appointment_not_found():
    update_data = {"status": "completed"}
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        response = client.put("/appointments/999", json=update_data)
        assert response.status_code == 404

def test_delete_appointment():
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        # Simula que existe el registro antes de borrar
        mock_cursor.fetchone.return_value = (1,)
        response = client.delete("/appointments/1")
        assert response.status_code == 200
        assert response.json() == {"ok": True}

def test_delete_appointment_not_found():
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        response = client.delete("/appointments/999")
        assert response.status_code == 404

def test_special_characters():
    appointment_data = {
        "patient_name": "José María Ñoño",
        "patient_email": "jose@example.com",
        "doctor_name": "Dr. García-López",
        "doctor_specialty": "Médico General",
        "appointment_time": "2024-07-01T10:00:00",
    }
    fake_row = {
        "id": 1,
        "patient_name": "José María Ñoño",
        "patient_email": "jose@example.com",
        "doctor_name": "Dr. García-López",
        "doctor_specialty": "Médico General",
        "appointment_time": "2024-07-01T10:00:00",
        "status": "scheduled",
        "notes": None,
        "created_at": "2024-06-13T10:00:00",
        "updated_at": "2024-06-13T10:00:00"
    }
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.return_value = fake_row
        response = client.post("/appointments/", json=appointment_data)
        assert response.status_code == 200
        assert response.json()["patient_name"] == "José María Ñoño"

def test_long_notes():
    appointment_data = {
        "patient_name": "Test Patient",
        "patient_email": "test@example.com",
        "doctor_name": "Dr. Test",
        "doctor_specialty": "Test",
        "appointment_time": "2024-07-01T10:00:00",
        "notes": "A" * 500,
    }
    fake_row = {
        "id": 1,
        "patient_name": "Test Patient",
        "patient_email": "test@example.com",
        "doctor_name": "Dr. Test",
        "doctor_specialty": "Test",
        "appointment_time": "2024-07-01T10:00:00",
        "status": "scheduled",
        "notes": "A" * 500,
        "created_at": "2024-06-13T10:00:00",
        "updated_at": "2024-06-13T10:00:00"
    }
    with patch("main.mysql.connector.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.return_value = fake_row
        response = client.post("/appointments/", json=appointment_data)
        assert response.status_code == 200
        assert len(response.json()["notes"]) == 500

def test_invalid_datetime():
    appointment_data = {
        "patient_name": "Test Patient",
        "patient_email": "test@example.com",
        "doctor_name": "Dr. Test",
        "doctor_specialty": "Test",
        "appointment_time": "invalid-datetime",
    }
    response = client.post("/appointments/", json=appointment_data)
    assert response.status_code == 422
