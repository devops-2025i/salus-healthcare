import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders login form when not authenticated', () => {
    render(<App />);
    expect(screen.getByText(/login/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });
});