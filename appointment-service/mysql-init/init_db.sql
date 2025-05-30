CREATE DATABASE IF NOT EXISTS appointments_db;

USE appointments_db;

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    patient_email VARCHAR(100) NOT NULL,
    doctor_name VARCHAR(100) NOT NULL,
    doctor_specialty VARCHAR(100) NOT NULL,
    appointment_time DATETIME NOT NULL,
    status ENUM('scheduled', 'cancelled', 'completed', 'rescheduled') DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO appointments (patient_name, patient_email, doctor_name, doctor_specialty, appointment_time, status, notes)
VALUES
('Juan Perez', 'juan.perez@example.com', 'Dra. Ana Torres', 'Cardiología', '2024-07-01 09:00:00', 'scheduled', 'Primera consulta de chequeo.'),
('Maria Gomez', 'maria.gomez@example.com', 'Dr. Luis Rivas', 'Dermatología', '2024-07-02 11:30:00', 'scheduled', 'Consulta por erupción cutánea.'),
('Carlos Ruiz', 'carlos.ruiz@example.com', 'Dra. Ana Torres', 'Cardiología', '2024-07-03 10:00:00', 'completed', 'Control de presión arterial.'),
('Lucia Fernández', 'lucia.fernandez@example.com', 'Dr. Pablo Soto', 'Pediatría', '2024-07-04 15:00:00', 'cancelled', 'Cancelada por el paciente.'),
('Sofía Martínez', 'sofia.martinez@example.com', 'Dra. Ana Torres', 'Cardiología', '2024-07-05 08:30:00', 'rescheduled', 'Reprogramada por el doctor.'); 