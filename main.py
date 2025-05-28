from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware  # ✅ Add this line
from pydantic import BaseModel
from datetime import date, datetime
from typing import Dict
import uuid

app = FastAPI()

# ✅ Allow frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://e-cheque-fv.vercel.app",  # ✅ correct frontend domain
        "http://localhost:5173"            # ✅ for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cheques: Dict[str, dict] = {}

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
        "cheque_date": req.cheque_date,
        "expiry_date": req.expiry_date,
        "status": "Pending"
    }
    return {"cheque_id": cheque_id, "status": "Pending"}

@app.post("/echeques/sign")
def sign_cheque(req: ChequeSignRequest):
    cheque = cheques.get(req.cheque_id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")

    if cheque["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Cheque cannot be signed")

    if cheque["expiry_date"] < datetime.today().date():
        cheque["status"] = "Expired"
        raise HTTPException(status_code=400, detail="Cheque is expired")

    # ✅ Simulate OTP verification
    if req.otp != "123456":  # Replace with your OTP logic later
        raise HTTPException(status_code=403, detail="Invalid OTP")

    cheque["status"] = "Signed"
    return {"cheque_id": req.cheque_id, "status": "Signed"}

@app.post("/echeques/{id}/present")
def present_cheque(id: str = Path(...)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] != "Signed":
        raise HTTPException(status_code=400, detail="Cheque not signed")
    cheque["status"] = "Cleared"
    return {"cheque_id": id, "status": "Cleared"}

@app.post("/echeques/{id}/revoke")
def revoke_cheque(id: str = Path(...)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] in ["Cleared", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Cheque cannot be revoked")
    cheque["status"] = "Cancelled"
    return {"cheque_id": id, "status": "Cancelled"}

@app.get("/echeques/{id}/status")
def cheque_status(id: str = Path(...)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["expiry_date"] < datetime.today().date() and cheque["status"] in ["Pending", "Signed"]:
        cheque["status"] = "Expired"
    return {"cheque_id": id, "status": cheque["status"]}
