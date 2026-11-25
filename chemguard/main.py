import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from openai import OpenAI
from .audit import record
from .safety import evaluate
from .schemas import Evaluation, Operation, SimulateRequest

app = FastAPI(title="ChemGuard", version="0.1.0", description="Conservative, simulation-only laboratory safety gateway")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

@app.get("/")
def chat_page():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

@app.post("/api/v1/chat")
def chat(request: ChatRequest):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="请先设置 OPENAI_API_KEY 环境变量。")
    client = OpenAI(api_key=api_key)
    try:
        extracted = client.responses.create(
            model=os.environ.get("CHEMGUARD_MODEL", "gpt-5.4-mini"),
            instructions="你是化学操作请求解析器。把用户意图转换为 ChemGuard 操作字段。没有实验操作就标记 has_operation=false。不得批准或执行任何操作；描述缺失字段时填入保守默认值，并让安全引擎决定。",
            input=request.message,
            text={"format": {"type": "json_schema", "name": "operation_proposal", "strict": True, "schema": {
                "type": "object", "additionalProperties": False,
                "properties": {"has_operation": {"type": "boolean"}, "device_id": {"type": "string"}, "action": {"type": "string"}, "parameters": {"type": "object", "additionalProperties": {"type": ["string", "number", "integer", "boolean", "null"]}}, "duration_seconds": {"type": "integer"}, "chemicals": {"type": "array", "items": {"type": "string"}}, "description": {"type": "string"}},
                "required": ["has_operation", "device_id", "action", "parameters", "duration_seconds", "chemicals", "description"]
            }}}
        )
        import json
        proposal = json.loads(extracted.output_text)
        if not proposal["has_operation"]:
            return {"reply": "ChemGuard 自动接入已就绪。请描述你希望执行的实验操作；所有操作提议都会先经过安全评估。", "proposal": None, "evaluation": None}
        try:
            operation = Operation(**{k: proposal[k] for k in ("device_id", "action", "parameters", "duration_seconds", "chemicals", "description")})
        except Exception:
            return {"reply": "操作信息不完整或格式无效，已停止请求。请补充设备、操作和参数信息。", "proposal": proposal, "evaluation": {"decision": "HOLD", "reasons": ["Operation proposal failed schema validation."], "simulation_only": True}}
        result = evaluate(operation)
        result.execution_id = record(operation.model_dump(), result.decision.value, result.reasons)
        return {"reply": "已将操作提议交给 ChemGuard 评估。此结果只用于模拟，不会启动设备。", "proposal": proposal, "evaluation": result.model_dump(mode="json")}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"模型服务调用失败：{type(exc).__name__}。请检查密钥、网络和模型配置。") from exc


@app.get("/health")
def health():
    return {"status": "ok", "hardware_enabled": False, "mode": "simulation_only"}


@app.post("/api/v1/evaluate", response_model=Evaluation)
def evaluate_operation(operation: Operation):
    result = evaluate(operation)
    result.execution_id = record(operation.model_dump(), result.decision.value, result.reasons)
    return result


@app.post("/api/v1/simulate", response_model=Evaluation)
def simulate(request: SimulateRequest):
    # Approval is deliberately not implemented: every accepted request is evaluated, never actuated.
    result = evaluate(request.operation)
    result.execution_id = record(request.operation.model_dump(), result.decision.value, result.reasons)
    return result
