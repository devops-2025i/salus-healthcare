import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBearer()
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

APPOINTMENT_SERVICE_URL = os.getenv(
    "APPOINTMENT_SERVICE_URL", "http://appointment-service:8001"
)


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "123456":
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode = {"sub": data.username, "exp": expire}  # type: ignore
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect username or password")


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/protected")
def protected(user=Depends(verify_jwt)):  # type: ignore
    return {"user": user}


# --- Proxy to appointment-service ---


@app.api_route(
    "/appointments/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    include_in_schema=False,
)
async def proxy_appointments(request: Request, path: str, user=Depends(verify_jwt)):  # type: ignore
    url = f"{APPOINTMENT_SERVICE_URL}/{path}"
    method = request.method
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers.pop("transfer-encoding", None)
    async with httpx.AsyncClient() as client:
        req_args = {  # type: ignore
            "url": url,
            "headers": headers,
            "params": dict(request.query_params),
            "timeout": 30.0,
        }
        if method in ["POST", "PUT"]:
            body = await request.body()
            if body:
                req_args["content"] = body
        resp = await client.request(method, **req_args)  # type: ignore
    return Response(
        content=resp.content, status_code=resp.status_code, headers=dict(resp.headers)
    )
