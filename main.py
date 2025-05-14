from fastapi import FastAPI, HTTPException, Path, Request, Depends
from pydantic import BaseModel
from datetime import date, datetime
from typing import Dict
import uuid
import logging

app = FastAPI()

# Setup audit logging
logging.basicConfig(filename="audit.log", level=logging.INFO)

# Support multiple banks with unique API keys
AUTHORIZED_KEYS = {
    "bank-abc-key": "Bank ABC",
    "bank-xyz-key": "Bank XYZ"
}

def verify_api_key(request: Request):
    key = request.headers.get("x-api-key")
    if key not in AUTHORIZED_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return AUTHORIZED_KEYS[key]

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
def issue_cheque(req: ChequeIssueRequest, bank_name: str = Depends(verify_api_key)):
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
    logging.info(f"{datetime.now()} | {bank_name} | Issued cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Pending"}

@app.post("/echeques/sign")
def sign_cheque(req: ChequeSignRequest, bank_name: str = Depends(verify_api_key)):
    cheque = cheques.get(req.cheque_id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Cheque cannot be signed")
    if cheque["expiry_date"] < datetime.today().date():
        cheque["status"] = "Expired"
        raise HTTPException(status_code=400, detail="Cheque is expired and cannot be signed")
    cheque["status"] = "Signed"
    logging.info(f"{datetime.now()} | {bank_name} | Signed cheque {req.cheque_id}")
    return {"cheque_id": req.cheque_id, "status": "Signed"}

@app.post("/echeques/{id}/present")
def present_cheque(id: str = Path(...), bank_name: str = Depends(verify_api_key)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] != "Signed":
        raise HTTPException(status_code=400, detail="Cheque not signed")
    cheque["status"] = "Cleared"
    logging.info(f"{datetime.now()} | {bank_name} | Presented cheque {id}")
    return {"cheque_id": id, "status": "Cleared"}

@app.post("/echeques/{id}/revoke")
def revoke_cheque(id: str = Path(...), bank_name: str = Depends(verify_api_key)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["status"] in ["Cleared", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Cheque cannot be revoked")
    cheque["status"] = "Cancelled"
    logging.info(f"{datetime.now()} | {bank_name} | Revoked cheque {id}")
    return {"cheque_id": id, "status": "Cancelled"}

@app.get("/echeques/{id}/status")
def cheque_status(id: str = Path(...), bank_name: str = Depends(verify_api_key)):
    cheque = cheques.get(id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque["expiry_date"] < datetime.today().date() and cheque["status"] in ["Pending", "Signed"]:
        cheque["status"] = "Expired"
    logging.info(f"{datetime.now()} | {bank_name} | Checked status of cheque {id}")
    return {"cheque_id": id, "status": cheque["status"]}
