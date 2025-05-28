from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime
from typing import Dict
import uuid
import json
import os

app = FastAPI()

# ✅ Allow frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://e-cheque-fv.vercel.app",  # ✅ frontend domain
        "http://localhost:5173"            # ✅ local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "cheques.json"

# ✅ Load cheques from file
def load_cheques():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# ✅ Save cheques to file
def save_cheques():
    with open(DATA_FILE, "w") as f:
        json.dump(cheques, f, indent=2, default=str)

cheques: Dict[str, dict] = load_cheques()

class ChequeIssueRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    cheque_date: date
    expiry_date: date

class ChequeSignRequest(BaseModel):
    cheque_id: str
    otp: str

@app.post("/echeques/issue")
def issue_cheque(req: ChequeIssueRequest):
    cheque_id = str(uuid.uuid4())
    cheques[cheque_id] = {
        "id": cheque_id,
        "sender": req.sender_account,
        "receiver": req.receiver_account,
        "amount": req.amount,
        "cheque_date": str(req.cheque_date),
        "expiry_date": str(req.expiry_date),
        "status": "Pending"
    }
    save_cheques()
    return {"cheque_id": cheque_id, "status": "Pending"}

@app.post("/echeques/sign")
def sign_cheque(req: ChequeSignRequest):
    cheque = cheques.get(req.cheque_id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Cheque cannot be signed")
    if date.fromisoformat(cheque["expiry_date"]) < datetime.today().date():
        cheque["status"] = "Expired"
        save_cheques()
        raise HTTPException(status_code=400, detail="Cheque is expired")
    if req.otp != "123456":
        raise HTTPException(status_code=403, detail="Invalid OTP")
    cheque["status"] = "Signed"
    save_cheques()
    return {"cheque_id": req.cheque_id, "status": "Signed"}

@app.post("/echeques/{id}/present")
def present_cheque(id: str = Path(...)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] != "Signed":
        raise HTTPException(status_code=400, detail="Cheque not signed")
    cheque["status"] = "Cleared"
    save_cheques()
    return {"cheque_id": id, "status": "Cleared"}

@app.post("/echeques/{id}/revoke")
def revoke_cheque(id: str = Path(...)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] in ["Cleared", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Cheque cannot be revoked")
    cheque["status"] = "Cancelled"
    save_cheques()
    return {"cheque_id": id, "status": "Cancelled"}

@app.get("/echeques/{id}/status")
def cheque_status(id: str = Path(...)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if date.fromisoformat(cheque["expiry_date"]) < datetime.today().date() and cheque["status"] in ["Pending", "Signed"]:
        cheque["status"] = "Expired"
        save_cheques()
    return {"cheque_id": id, "status": cheque["status"]}

@app.get("/")
def root():
    return {"message": "E-Cheque API is live ✅"}
