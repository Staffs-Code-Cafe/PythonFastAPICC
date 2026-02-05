from fastapi.responses import HTMLResponse
import markdown
from dotenv import load_dotenv
import os
import secrets
import hashlib
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from jose import JWTError, jwt

# ================================
# RATE LIMITING IMPORTS (slowapi)
# ================================
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware

load_dotenv()

# ================================
# CONFIGURATION
# ================================
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in environment variables")

# ================================
# RATE LIMITER SETUP
# ================================
limiter = Limiter(key_func=get_remote_address)

# ================================
# FASTAPI APP
# ================================
app = FastAPI(
    title=os.getenv("APP_TITLE", "Interactive API Learning Platform"),
    description="A secure educational API to teach how APIs work",
    version=os.getenv("APP_VERSION", "1.2.0"),
    openapi_tags=[
        {"name": "Authentication", "description": "Login and token operations"},
        {"name": "Lessons", "description": "Endpoints for teaching GET and POST"},
        {"name": "Protected", "description": "JWT protected endpoints for auth lesson"},
        {"name": "Challenge", "description": "Hidden endpoints scavenger hunt game"}
    ]
)

# Attach limiter
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Custom rate-limit error handler
@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Slow down!"}
    )

# ================================
# AUTH MODELS
# ================================
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

# ================================
# LESSON MODELS
# ================================
class Lesson(BaseModel):
    id: int
    title: str
    description: str
    task: str
    endpoint: str

# ================================
# FAKE DATABASE (for demo)
# ================================
fake_users_db = {
    os.getenv("DEMO_USERNAME"): {
        "username": os.getenv("DEMO_USERNAME"),
        "hashed_password": os.getenv("DEMO_PASSWORD")
    }
}

lessons_db = [
    Lesson(id=1, title="GET Basics", description="Learn how GET requests work", task="Fetch this lesson using GET", endpoint="/lessons"),
    Lesson(id=2, title="POST Basics", description="Learn how POST requests work", task="Create a new lesson using POST", endpoint="/lessons"),
    Lesson(id=3, title="Auth", description="Learn authentication", task="Login and access protected route", endpoint="/protected")
]

# ================================
# SECURITY
# ================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# ================================
# AUTH ENDPOINTS (RATE LIMITED)
# ================================
@app.post("/token", response_model=Token, tags=["Authentication"])
@limiter.limit("5/minute")  # 5 login attempts per minute per IP
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or user["hashed_password"] != form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ================================
# LESSON ENDPOINTS (RATE LIMITED)
# ================================
@app.get("/lessons", response_model=List[Lesson], tags=["Lessons"])
@limiter.limit("30/minute")
def get_lessons(request: Request):
    return lessons_db


@app.post("/lessons", response_model=Lesson, tags=["Lessons"])
@limiter.limit("10/minute")
def create_lesson(request: Request, lesson: Lesson, user=Depends(get_current_user)):
    lessons_db.append(lesson)
    return lesson


@app.get("/protected", tags=["Protected"])
@limiter.limit("20/minute")
def protected_route(request: Request, user=Depends(get_current_user)):
    return {
        "message": "You accessed a protected endpoint!",
        "user": user["username"],
        "lesson": "This demonstrates JWT authentication"
    }

# ================================
# MARKDOWN LESSON VIEWER
# ================================
@app.get("/", tags=["Lessons"], response_class=HTMLResponse)
@limiter.limit("10/minute")
def lesson_markdown_web(request: Request):
    file_path = "lesson.md"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Markdown file not found")

    with open(file_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content, extensions=["fenced_code", "tables"])

    full_html = f"""
    <html>
        <head>
            <title>Lesson</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 2rem; max-width: 800px; margin: auto; }}
                pre {{ background-color: #f4f4f4; padding: 1rem; overflow-x: auto; }}
                code {{ background-color: #f4f4f4; padding: 0.2rem 0.4rem; }}
                h1, h2, h3 {{ color: #333; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
    </html>
    """

    return HTMLResponse(content=full_html)

# ================================
# CHALLENGE MODE (RATE LIMITED)
# ================================
SECRET_NUMBERS = {"alpha": 7, "beta": 13, "gamma": 21}
NONCES = {}
KEYS = {}

@app.get("/challenge", tags=["Challenge"])
@limiter.limit("15/minute")
def challenge_intro(request: Request):
    return {
        "challenge": "API Scavenger Hunt",
        "instructions": [
            "Find hidden endpoints.",
            "Each endpoint returns a number.",
            "Add all numbers together.",
            "Send the result to /challenge/submit to win the prize."
        ],
        "hint": "Look for endpoints with Greek names 😉"
    }

@app.get("/challenge/alpha", tags=["Challenge"])
@limiter.limit("10/minute")
def challenge_alpha(request: Request):
    return {"value": SECRET_NUMBERS["alpha"]}

@app.get("/challenge/beta", tags=["Challenge"])
@limiter.limit("10/minute")
def challenge_beta(request: Request):
    return {"value": SECRET_NUMBERS["beta"]}

@app.get("/challenge/gamma", tags=["Challenge"])
@limiter.limit("10/minute")
def challenge_gamma(request: Request):
    return {"value": SECRET_NUMBERS["gamma"]}

class ChallengeSubmission(BaseModel):
    result: int

class HashSubmission(BaseModel):
    nonce: str
    hash: str

@app.post("/challenge/submit", tags=["Challenge"])
@limiter.limit("5/minute")
def challenge_submit(request: Request, data: ChallengeSubmission):
    correct_value = sum(SECRET_NUMBERS.values())

    if data.result == correct_value:
        return {
            "status": "WIN",
            "message": "🎉 Congratulations! You solved the first API challenge!",
            "prize": "Access granted to the second endpoint",
            "next": "/challenge/key/start"
        }
    else:
        raise HTTPException(status_code=400, detail="Incorrect result. Try again.")

@app.get("/challenge/key/start", tags=["Challenge"])
@limiter.limit("5/minute")
def challenge_key_start(request: Request):
    ip = get_remote_address(request)
    nonce = secrets.token_hex(16)
    NONCES[ip] = nonce
    return {
        "step": "hash",
        "nonce": nonce,
        "instructions": "Compute SHA256 of 'alpha-beta-gamma-<nonce>' and POST to /challenge/key/hash"
    }

@app.post("/challenge/key/hash", tags=["Challenge"])
@limiter.limit("5/minute")
def challenge_key_hash(request: Request, data: HashSubmission):
    ip = get_remote_address(request)
    if NONCES.get(ip) != data.nonce:
        raise HTTPException(status_code=400, detail="Invalid or expired nonce")
    s = f"{SECRET_NUMBERS['alpha']}-{SECRET_NUMBERS['beta']}-{SECRET_NUMBERS['gamma']}-{data.nonce}"
    expected = hashlib.sha256(s.encode()).hexdigest()
    if data.hash != expected:
        raise HTTPException(status_code=400, detail="Incorrect hash")
    key = secrets.token_urlsafe(16)
    KEYS[ip] = key
    return {
        "status": "OK",
        "next": "/challenge/prize",
        "key_hint": "Use query param ?key=...",
        "key": key
    }

@app.get("/challenge/prize", tags=["Challenge"])
@limiter.limit("5/minute")
def challenge_prize(request: Request, key: str | None = None):
    ip = get_remote_address(request)
    if not key or KEYS.get(ip) != key:
        raise HTTPException(status_code=403, detail="Valid key required")
    return {
        "prize": "API Master Badge",
        "reward": "Certificate"
    }

# ================================
# HEALTH CHECK
# ================================
@app.get("/listLessons", tags=["Lessons"])
@limiter.limit("20/minute")
def root(request: Request):
    return {
        "status": "API running",
        "docs": "/docs",
        "lesson_flow": [
            "1. GET /lessons",
            "2. POST /token",
            "3. GET /protected",
            "4. POST /lessons (with token)",
            "5. GET /challenge (scavenger hunt game)"
        ]
    }
