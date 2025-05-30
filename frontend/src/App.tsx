import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import './App.css';

interface Appointment {
  id: number;
  patient_name: string;
  patient_email: string;
  doctor_name: string;
  doctor_specialty: string;
  appointment_time: string;
  status: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

const API_GATEWAY_URL = import.meta.env.VITE_API_GATEWAY_URL;

const initialForm = {
  patient_name: '',
  patient_email: '',
  doctor_name: '',
  doctor_specialty: '',
  appointment_time: '',
  status: 'scheduled',
  notes: '',
};

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('123456');
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ ...initialForm });
  const [creating, setCreating] = useState(false);

  const API_URL = `${API_GATEWAY_URL}/appointments/appointments/`;

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${API_GATEWAY_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) throw new Error('Login failed');
      const data = await res.json();
      setToken(data.access_token);
    } catch (err) {
      setError('Login failed');
    } finally {
      setLoading(false);
    }
  };

  const fetchAppointments = () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    fetch(API_URL, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Error fetching appointments');
        const data = await res.json();
        setAppointments(data);
      })
      .catch(() => setError('Error fetching appointments'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAppointments();
    // eslint-disable-next-line
  }, [token]);

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error('Error creating appointment');
      setForm({ ...initialForm });
      fetchAppointments();
    } catch (err) {
      setError('Error creating appointment');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Error deleting appointment');
      fetchAppointments();
    } catch (err) {
      setError('Error deleting appointment');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
          <h2 className="text-2xl font-bold mb-4 text-center">Login</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Username"
              autoFocus
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
            />
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
            />
            <button type="submit" disabled={loading} className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition disabled:opacity-50">Login</button>
          </form>
          {error && <p className="text-red-500 mt-2 text-center">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center py-8">
      <div className="bg-white p-6 rounded-lg shadow-md w-full max-w-4xl mb-8">
        <h2 className="text-3xl font-bold mb-6 text-center">Appointments</h2>
        {loading && <p className="text-blue-600">Loading...</p>}
        {error && <p className="text-red-500">{error}</p>}
        <form className="appointment-form grid grid-cols-1 md:grid-cols-2 gap-4 mb-8" onSubmit={handleCreate}>
          <input
            name="patient_name"
            value={form.patient_name}
            onChange={handleFormChange}
            placeholder="Patient Name"
            required
            className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          />
          <input
            name="patient_email"
            value={form.patient_email}
            onChange={handleFormChange}
            placeholder="Patient Email"
            type="email"
            required
            className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          />
          <input
            name="doctor_name"
            value={form.doctor_name}
            onChange={handleFormChange}
            placeholder="Doctor Name"
            required
            className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          />
          <input
            name="doctor_specialty"
            value={form.doctor_specialty}
            onChange={handleFormChange}
            placeholder="Doctor Specialty"
            required
            className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          />
          <input
            name="appointment_time"
            value={form.appointment_time}
            onChange={handleFormChange}
            placeholder="YYYY-MM-DDTHH:MM"
            type="datetime-local"
            required
            className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          />
          <select name="status" value={form.status} onChange={handleFormChange} className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300">
            <option value="scheduled">Scheduled</option>
            <option value="cancelled">Cancelled</option>
            <option value="completed">Completed</option>
            <option value="rescheduled">Rescheduled</option>
          </select>
          <textarea
            name="notes"
            value={form.notes}
            onChange={handleFormChange}
            placeholder="Notes"
            className="px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300 md:col-span-2"
          />
          <button type="submit" disabled={creating} className="bg-green-600 text-white py-2 rounded hover:bg-green-700 transition disabled:opacity-50 md:col-span-2">Create</button>
        </form>
        <div className="overflow-x-auto">
          <table className="appointments-table min-w-full bg-white border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-blue-600 text-white">
              <tr>
                <th className="px-4 py-2">Paciente</th>
                <th className="px-4 py-2">Email</th>
                <th className="px-4 py-2">Doctor</th>
                <th className="px-4 py-2">Especialidad</th>
                <th className="px-4 py-2">Fecha/Hora</th>
                <th className="px-4 py-2">Estado</th>
                <th className="px-4 py-2">Notas</th>
                <th className="px-4 py-2">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map(appt => (
                <tr key={appt.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 font-semibold">{appt.patient_name}</td>
                  <td className="px-4 py-2">{appt.patient_email}</td>
                  <td className="px-4 py-2">{appt.doctor_name}</td>
                  <td className="px-4 py-2">{appt.doctor_specialty}</td>
                  <td className="px-4 py-2">{new Date(appt.appointment_time).toLocaleString()}</td>
                  <td className="px-4 py-2">
                    <span className={
                      appt.status === 'scheduled' ? 'text-blue-600 font-bold' :
                      appt.status === 'completed' ? 'text-green-600 font-bold' :
                      appt.status === 'cancelled' ? 'text-red-600 font-bold' :
                      'text-yellow-600 font-bold'
                    }>
                      {appt.status}
                    </span>
                  </td>
                  <td className="px-4 py-2">{appt.notes}</td>
                  <td className="px-4 py-2">
                    <button className="delete-btn bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 transition" onClick={() => handleDelete(appt.id)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <button onClick={() => setToken(null)} className="mt-6 w-full bg-gray-300 hover:bg-gray-400 text-gray-800 py-2 rounded transition">Logout</button>
      </div>
    </div>
  );
}

export default App;
