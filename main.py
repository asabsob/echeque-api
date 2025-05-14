from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from datetime import date
import uuid
import logging

app = FastAPI()

# Logging config
timestamp_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(filename="audit.log", level=logging.INFO, format="%(asctime)s - %(message)s", datefmt=timestamp_format)

# In-memory cheque store
cheques = {}

# Authorized API keys
AUTHORIZED_KEYS = {
    "bank-abc-key": "Bank ABC",
    "bank-xyz-key": "Bank XYZ"
}

# API key validation
def verify_api_key(x_api_key: str = Header(..., convert_underscores=False)):
    if x_api_key not in AUTHORIZED_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

# Cheque model
class ChequeIssueRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    cheque_date: date
    expiry_date: date

# Issue a new cheque
@app.post("/echeques/issue")
def issue_cheque(req: ChequeIssueRequest, api_key: str = Depends(verify_api_key)):
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
    logging.info(f"[{AUTHORIZED_KEYS[api_key]}] Issued cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Pending"}

# Sign a cheque
@app.post("/echeques/sign")
def sign_cheque(cheque_id: str, api_key: str = Depends(verify_api_key)):
    if cheque_id not in cheques:
        raise HTTPException(status_code=404, detail="Cheque not found")
    cheques[cheque_id]["status"] = "Signed"
    logging.info(f"[{AUTHORIZED_KEYS[api_key]}] Signed cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Signed"}

# Present a cheque
@app.post("/echeques/present")
def present_cheque(cheque_id: str, api_key: str = Depends(verify_api_key)):
    if cheque_id not in cheques:
        raise HTTPException(status_code=404, detail="Cheque not found")
    cheques[cheque_id]["status"] = "Presented"
    logging.info(f"[{AUTHORIZED_KEYS[api_key]}] Presented cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Presented"}

# Revoke a cheque
@app.post("/echeques/revoke")
def revoke_cheque(cheque_id: str, api_key: str = Depends(verify_api_key)):
    if cheque_id not in cheques:
        raise HTTPException(status_code=404, detail="Cheque not found")
    cheques[cheque_id]["status"] = "Revoked"
    logging.info(f"[{AUTHORIZED_KEYS[api_key]}] Revoked cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Revoked"}

# Get cheque status
@app.get("/echeques/status")
def get_status(cheque_id: str, api_key: str = Depends(verify_api_key)):
    if cheque_id not in cheques:
        raise HTTPException(status_code=404, detail="Cheque not found")
    return {"cheque_id": cheque_id, "status": cheques[cheque_id]["status"]}
