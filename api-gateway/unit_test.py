import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException
from jose import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from main import app, verify_jwt, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

client: TestClient = TestClient(app)


class TestLogin:
    def test_login_success(self) -> None:
        """Test successful login with correct credentials"""
        response = client.post(
            "/login", json={"username": "admin", "password": "123456"}
        )
        assert response.status_code == 200
        data: Dict[str, Any] = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify token is valid
        payload: Dict[str, Any] = jwt.decode(
            data["access_token"], SECRET_KEY, algorithms=[ALGORITHM]
        )
        assert payload["sub"] == "admin"

    def test_login_invalid_credentials(self) -> None:
        """Test login with invalid credentials"""
        response = client.post(
            "/login", json={"username": "wrong", "password": "wrong"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_missing_fields(self) -> None:
        """Test login with missing fields"""
        response = client.post("/login", json={"username": "admin"})
        assert response.status_code == 422


class TestJWTVerification:
    def test_verify_jwt_valid_token(self) -> None:
        """Test JWT verification with valid token"""
        expire: datetime = datetime.now(timezone.utc) + timedelta(  # type: ignore
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode: Dict[str, Any] = {"sub": "admin", "exp": expire}
        token: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )
        payload: Dict[str, Any] = verify_jwt(credentials)
        assert payload["sub"] == "admin"

    def test_verify_jwt_invalid_token(self) -> None:
        """Test JWT verification with invalid token"""
        credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid-token"
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    def test_verify_jwt_expired_token(self) -> None:
        """Test JWT verification with expired token"""
        expire: datetime = datetime.now(timezone.utc) - timedelta(  # type: ignore
            minutes=1
        )  # Expired 1 minute ago
        to_encode: Dict[str, Any] = {"sub": "admin", "exp": expire}
        token: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt(credentials)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"


class TestHealthEndpoint:
    def test_health_endpoint(self) -> None:
        """Test health endpoint returns ok status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestProtectedEndpoint:
    def test_protected_endpoint_with_valid_token(self) -> None:
        """Test protected endpoint with valid authentication"""
        # First login to get token
        login_response = client.post(
            "/login", json={"username": "admin", "password": "123456"}
        )
        token: str = login_response.json()["access_token"]

        # Use token to access protected endpoint
        headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}
        response = client.get("/protected", headers=headers)

        assert response.status_code == 200
        data: Dict[str, Any] = response.json()
        assert "user" in data
        assert data["user"]["sub"] == "admin"

    def test_protected_endpoint_without_token(self) -> None:
        """Test protected endpoint without authentication"""
        response = client.get("/protected")
        assert response.status_code == 403

    def test_protected_endpoint_with_invalid_token(self) -> None:
        """Test protected endpoint with invalid token"""
        headers: Dict[str, str] = {"Authorization": "Bearer invalid-token"}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 401


class TestProxyAppointments:
    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_proxy_appointments_get(self, mock_client: MagicMock) -> None:
        """Test proxy GET request to appointments service"""
        # Setup mock response
        mock_response: MagicMock = MagicMock()
        mock_response.content = b'{"appointments": []}'
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}

        mock_client_instance: AsyncMock = AsyncMock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Get valid token
        login_response = client.post(
            "/login", json={"username": "admin", "password": "123456"}
        )
        token: str = login_response.json()["access_token"]

        # Make request to proxy endpoint
        headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}
        response = client.get("/appointments/list", headers=headers)

        assert response.status_code == 200
        mock_client_instance.request.assert_called_once()

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_proxy_appointments_post(self, mock_client: MagicMock) -> None:
        """Test proxy POST request to appointments service"""
        # Setup mock response
        mock_response: MagicMock = MagicMock()
        mock_response.content = b'{"id": 1, "created": true}'
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}

        mock_client_instance: AsyncMock = AsyncMock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Get valid token
        login_response = client.post(
            "/login", json={"username": "admin", "password": "123456"}
        )
        token: str = login_response.json()["access_token"]

        # Make POST request to proxy endpoint
        headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}
        appointment_data: Dict[str, str] = {"patient": "John Doe", "date": "2024-01-01"}
        response = client.post(
            "/appointments/create", json=appointment_data, headers=headers
        )

        assert response.status_code == 201
        mock_client_instance.request.assert_called_once()

    def test_proxy_appointments_without_auth(self) -> None:
        """Test proxy endpoint without authentication"""
        response = client.get("/appointments/list")
        assert response.status_code == 403
