from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time

from gateway.chain_guard import ChainGuard

app = FastAPI(title="ZKTrustLLM-Agents Secure Gateway")
guard = ChainGuard()

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

    if not guard.is_registered(msg.senderAgentId):
        raise HTTPException(status_code=403, detail="sender not registered")

    if not guard.capability_valid(msg.capabilityId):
        raise HTTPException(status_code=403, detail="capability invalid or expired")

    cap = guard.get_capability(msg.capabilityId)
    if cap["policyClass"] != msg.policyClass:
        raise HTTPException(status_code=403, detail="policy class mismatch")

    expected_agent_key = guard.agent_key(msg.senderAgentId)
    if cap["agentKey"] != expected_agent_key:
        raise HTTPException(status_code=403, detail="capability does not belong to sender")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/message/validate")
def message_validate(msg: AgentMessage):
    validate_message(msg)
    return {"accepted": True, "taskId": msg.taskId, "sender": msg.senderAgentId}

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
