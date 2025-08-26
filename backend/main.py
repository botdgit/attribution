from fastapi import FastAPI, Depends
from pydantic import BaseModel

from .auth import get_current_user
from .analysis import run_did_analysis

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


class DIDRequest(BaseModel):
    campaign_id: str


@app.post("/api/analysis/did", dependencies=[Depends(get_current_user)])
def execute_did(request: DIDRequest):
    result = run_did_analysis("cfap-platform-dev", request.campaign_id)
    return result
