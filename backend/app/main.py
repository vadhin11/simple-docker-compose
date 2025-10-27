from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware   # <-- add
from pydantic import BaseModel, Field
from passlib.hash import sha256_crypt
from mysql.connector.errors import IntegrityError

from .db import DBManager

app = FastAPI(title=" FastAPI + MariaDB")

# ---- CORS (so the HTML app on :8080 can call the API on :80/8000) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # for demo; restrict in prod
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------------------------------------------------

db: DBManager | None = None
bootstrapped = False


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str
    created_at: str

# ---- NEW: login model ----
class LoginIn(BaseModel):
    username: str
    password: str

class LoginOut(BaseModel):
    id: int
    username: str
    created_at: str
# --------------------------

@app.on_event("startup")
def startup() -> None:
    global db
    db = DBManager()
    db.ensure_users_table()  # make sure users table exists


@app.get("/", response_class=HTMLResponse)
def list_blog() -> HTMLResponse:
    """
    Original behavior:
    - On first request after process start: drop/create/seed blog
    - Return simple HTML list
    """
    global bootstrapped, db
    assert db is not None, "DB not initialized"

    if not bootstrapped:
        db.populate_db()
        bootstrapped = True

    titles = db.query_titles()
    html = "".join(f"<div>   Hello  {t}</div>" for t in titles)
    return HTMLResponse(content=html)


@app.get("/posts", response_class=JSONResponse)
def list_posts_json() -> JSONResponse:
    assert db is not None, "DB not initialized"
    return JSONResponse({"titles": db.query_titles()})


@app.get("/healthz", response_class=PlainTextResponse)
def healthz() -> PlainTextResponse:
    return PlainTextResponse("ok")


# --------- NEW: Users API ---------

@app.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate) -> UserOut:
    """
    Create a user with hashed password (sha256_crypt via passlib).
    Returns 409 if the username already exists.
    """
    assert db is not None, "DB not initialized"

    password_hash = sha256_crypt.hash(payload.password)

    try:
        user_id = db.insert_user(username=payload.username, password_hash=password_hash)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")

    # fetch back for consistent shape
    row = db.get_user_by_username(payload.username)
    assert row is not None
    uid, uname, created_at = row
    return UserOut(id=uid, username=uname, created_at=created_at)


@app.get("/users", response_model=list[UserOut])
def list_users() -> list[UserOut]:
    assert db is not None, "DB not initialized"
    rows = db.list_users()
    return [UserOut(id=i, username=u, created_at=ts) for (i, u, ts) in rows]


@app.get("/users/{username}", response_model=UserOut)
def get_user(username: str) -> UserOut:
    assert db is not None, "DB not initialized"
    row = db.get_user_by_username(username)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    uid, uname, created_at = row
    return UserOut(id=uid, username=uname, created_at=created_at)

# --------- NEW: Auth APIs ---------
@app.post("/auth/login", response_model=LoginOut)
def login(payload: LoginIn) -> LoginOut:
    """
    Stateless demo login:
    - fetch user by username
    - verify password against stored passlib sha256_crypt hash
    - return user info (client stores it; 'logout' is client-side clear)
    """
    assert db is not None, "DB not initialized"
    row = db.get_user_auth(payload.username)
    if not row:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    uid, uname, password_hash, created_at = row
    if not sha256_crypt.verify(payload.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return LoginOut(id=uid, username=uname, created_at=created_at)