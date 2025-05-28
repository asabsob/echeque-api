from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime
import sqlite3
import uuid
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://e-cheque-fv.vercel.app",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite setup in Vercel's writable /tmp directory
DB_NAME = os.path.join("/tmp", "cheques.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cheques (
            id TEXT PRIMARY KEY,
            sender TEXT,
            receiver TEXT,
            amount REAL,
            cheque_date TEXT,
            expiry_date TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Models
class ChequeIssueRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    cheque_date: date
    expiry_date: date

class ChequeSignRequest(BaseModel):
    cheque_id: str
    otp: str

# Helpers
def get_cheque(cheque_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM cheques WHERE id=?", (cheque_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "sender": row[1],
            "receiver": row[2],
            "amount": row[3],
            "cheque_date": date.fromisoformat(row[4]),
            "expiry_date": date.fromisoformat(row[5]),
            "status": row[6]
        }
    return None

def update_cheque_status(cheque_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE cheques SET status=? WHERE id=?", (new_status, cheque_id))
    conn.commit()
    conn.close()

# Routes
@app.get("/")
def root():
    return {"message": "E-Cheque API is live ✅"}

@app.post("/echeques/issue")
def issue_cheque(req: ChequeIssueRequest):
    cheque_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO cheques (id, sender, receiver, amount, cheque_date, expiry_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        cheque_id,
        req.sender_account,
        req.receiver_account,
        req.amount,
        req.cheque_date.isoformat(),
        req.expiry_date.isoformat(),
        "Pending"
    ))
    conn.commit()
    conn.close()
    return {"cheque_id": cheque_id, "status": "Pending"}

@app.post("/echeques/sign")
def sign_cheque(req: ChequeSignRequest):
    cheque = get_cheque(req.cheque_id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Cheque cannot be signed")
    if cheque["expiry_date"] < datetime.today().date():
        update_cheque_status(req.cheque_id, "Expired")
        raise HTTPException(status_code=400, detail="Cheque is expired")
    if req.otp != "123456":
        raise HTTPException(status_code=403, detail="Invalid OTP")
    update_cheque_status(req.cheque_id, "Signed")
    return {"cheque_id": req.cheque_id, "status": "Signed"}

@app.post("/echeques/{id}/present")
def present_cheque(id: str = Path(...)):
    cheque = get_cheque(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] != "Signed":
        raise HTTPException(status_code=400, detail="Cheque not signed")
    update_cheque_status(id, "Cleared")
    return {"cheque_id": id, "status": "Cleared"}

@app.post("/echeques/{id}/revoke")
def revoke_cheque(id: str = Path(...)):
    cheque = get_cheque(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] in ["Cleared", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Cheque cannot be revoked")
    update_cheque_status(id, "Cancelled")
    return {"cheque_id": id, "status": "Cancelled"}

@app.get("/echeques/{id}/status")
def cheque_status(id: str = Path(...)):
    cheque = get_cheque(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["expiry_date"] < datetime.today().date() and cheque["status"] in ["Pending", "Signed"]:
        update_cheque_status(id, "Expired")
        cheque["status"] = "Expired"
    return {"cheque_id": id, "status": cheque["status"]}
