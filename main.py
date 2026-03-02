
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
import sqlite3

app = FastAPI()

pwd = CryptContext(schemes=["bcrypt"])
SECRET_KEY = "kunci_rahasia_123"

def get_db():
  conn = sqlite3.connect("todos.db")
  conn.row_factory = sqlite3.Row
  return conn

conn = get_db()
conn.execute("""
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
    )
""")
conn.commit()

class User(BaseModel):
  email: str
  password: str

@app.get("/")
def home():
  return {"pesan": "API berjalan!"}

@app.post("/register")
def register(user: User):
  conn = get_db()
  hashed = pwd.hash(user.password)
  try:
    conn.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                (user.email, hashed))
    conn.commit()
    return {"pesan": "Registrasi berhasil!"}
  except:
    raise HTTPException(status_code=400, detail="Email sudah terdaftar!")

@app.post("/login")
def login(user: User):
  conn = get_db()
  db_user = conn.execute("SELECT * FROM users WHERE email = ?", 
                        (user.email,)).fetchone()
  if not db_user or not pwd.verify(user.password, db_user["password"]):
    raise HTTPException(status_code=401, detail="Email atau password salah!")
  token = jwt.encode({"email": user.email}), SECRET_KEY, algorithm="HS256"
  return {"token": token}
