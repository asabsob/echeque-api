from fastapi import FastAPI, Header, HTTPException, Depends
import uuid
import logging
from pydantic import BaseModel
from datetime import date

app = FastAPI()

# Setup logging
timestamp_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(filename="audit.log", level=logging.INFO, format='%(asctime)s - %(message)s', datefmt=timestamp_format)

# Simulated in-memory database
cheques = {}

# Authorized API keys
AUTHORIZED_KEYS = {
    "bank-abc-key": "Bank ABC",
    "bank-xyz-key": "Bank XYZ"
}

# API Key Validator
def verify_api_key(x_api_key: str = Header(..., convert_underscores=False)):
    if x_api_key not in AUTHORIZED_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

# Pydantic model for cheque issue request
class ChequeIssueRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    cheque_date: date
    expiry_date: date

# Endpoint to issue a cheque
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
