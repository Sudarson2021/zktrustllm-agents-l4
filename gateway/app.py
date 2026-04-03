from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time

app = FastAPI(title="ZKTrustLLM-Agents Secure Gateway")

class AgentMessage(BaseModel):
    senderAgentId: str
    receiverAgentId: str
    taskId: str
    capabilityId: str
    contextHash: str
    payloadHash: str
    policyClass: str
    timestamp: int
    signature: str

MAX_CLOCK_SKEW = 300

def validate_message(msg: AgentMessage):
    now = int(time.time())

    if abs(now - msg.timestamp) > MAX_CLOCK_SKEW:
        raise HTTPException(status_code=400, detail="stale timestamp")

    if not msg.signature or len(msg.signature.strip()) == 0:
        raise HTTPException(status_code=400, detail="missing signature")

    if not msg.senderAgentId or not msg.receiverAgentId:
        raise HTTPException(status_code=400, detail="missing sender/receiver")

    if not msg.capabilityId:
        raise HTTPException(status_code=400, detail="missing capability")

    if not msg.policyClass:
        raise HTTPException(status_code=400, detail="missing policy class")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/message/validate")
def message_validate(msg: AgentMessage):
    validate_message(msg)
    return {"accepted": True, "taskId": msg.taskId}

@app.post("/tool/authorize")
def tool_authorize(msg: AgentMessage):
    validate_message(msg)
    return {"authorized": True, "policyClass": msg.policyClass}

@app.post("/trace/store")
def trace_store(payload: dict):
    return {"stored": True, "payloadKeys": list(payload.keys())}

@app.post("/anomaly/report")
def anomaly_report(payload: dict):
    return {"reported": True, "payloadKeys": list(payload.keys())}
