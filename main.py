from fastapi import FastAPI, Header, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from datetime import date
import uuid
import logging

# Setup logging
timestamp_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(filename="audit.log", level=logging.INFO, format="%(asctime)s - %(message)s", datefmt=timestamp_format)

# App and in-memory DB
app = FastAPI()
cheques = {}

# API key security
AUTHORIZED_KEYS = {
    "bank-abc-key": "Bank ABC",
    "bank-xyz-key": "Bank XYZ"
}
api_key_header = APIKeyHeader(name="x_api_key", auto_error=False)

async def verify_api_key(x_api_key: str = Security(api_key_header)):
    if not x_api_key or x_api_key not in AUTHORIZED_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

# Global dependency
app = FastAPI(dependencies=[Depends(verify_api_key)])

# Cheque request model
class ChequeIssueRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    cheque_date: date
    expiry_date: date

# ====== ROUTES ======

@app.post("/echeques/issue")
def issue_cheque(req: ChequeIssueRequest, api_key: str = Depends(verify_api_key)):
    cheque_id = str(uuid.uuid4())
    cheques[cheque_id] = {
        "id": cheque_id,
        "sender": req.sender_account,
        "receiver": req.receiver_account,
        "amount": req.amount,
        "cheque_date": req.cheque_date.isoformat(),
        "expiry_date": req.expiry_date.isoformat(),
        "status": "Pending"
    }
    logging.info(f"[{AUTHORIZED_KEYS[api_key]}] Issued cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Pending"}

@app.post("/echeques/sign")
def sign_cheque(cheque_id: str, api_key: str = Depends(verify_api_key)):
    if cheque_id not in cheques:
        raise HTTPException(status_code=404, detail="Cheque not found")
    cheques[cheque_id]["status"] = "Signed"
    logging.info(f"[{AUTHORIZED_KEYS[api_key]}] Signed cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Signed"}

@app.post("/echeques/present")
def present_cheque(cheque_id: str, api_key: str = Depends(verify_api_key)):
    if cheque_id not in cheques:
        raise HTTPException(status_code=404, detail="Cheque not found")
    cheques[cheque_id]["status"] = "Presented"
    logging.info(f"[{AUTHORIZED_KEYS[api_key]}] Presented cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Presented"}

@app.post("/echeques/revoke")
def revoke_cheque(cheque_id: str, api_key: str = Depends(verify_api_key)):
    if cheque_id not in cheques:
        raise HTTPException(status_code=404, detail="Cheque not found")
    cheques[cheque_id]["status"] = "Revoked"
    logging.info(f"[{AUTHORIZED_KEYS[api_key]}] Revoked cheque {cheque_id}")
    return {"cheque_id": cheque_id, "status": "Revoked"}

@app.get("/echeques/status")
def get_status(cheque_id: str, api_key: str = Depends(verify_api_key)):
    if cheque_id not in cheques:
        raise HTTPException(status_code=404, detail="Cheque not found")
    return {"cheque_id": cheque_id, "status": cheques[cheque_id]["status"]}

# ✅ New: Get all cheques
@app.get("/echeques/all")
def get_all_cheques(api_key: str = Depends(verify_api_key)):
    return list(cheques.values())

# ====== Swagger UI Security ======

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="E-Cheque API",
        version="1.0.0",
        description="E-Cheque Management System",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "x_api_key"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
