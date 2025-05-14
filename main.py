from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from datetime import date
from typing import Dict
import uuid

app = FastAPI()

# In-memory database
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
    return {"cheque_id": id, "status": cheque["status"]}
