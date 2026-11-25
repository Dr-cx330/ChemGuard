"""Gradio chat front end using DeepSeek's OpenAI-compatible API and local ChemGuard rules."""
import json
import os

import gradio as gr
from openai import OpenAI
from pydantic import ValidationError

from chemguard.audit import record
from chemguard.safety import evaluate
from chemguard.schemas import Operation

MODEL = os.getenv("CHEMGUARD_MODEL", "deepseek-chat")
BASE_URL = os.getenv("CHEMGUARD_BASE_URL", "https://api.deepseek.com")

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "has_operation": {"type": "boolean"}, "device_id": {"type": "string"},
        "action": {"type": "string"}, "parameters": {"type": "object"},
        "duration_seconds": {"type": "integer"}, "chemicals": {"type": "array", "items": {"type": "string"}},
        "description": {"type": "string"}
    },
    "required": ["has_operation", "device_id", "action", "parameters", "duration_seconds", "chemicals", "description"]
}


def chat(user_message, history):
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        return "请先在启动此程序的 PowerShell 中设置 DEEPSEEK_API_KEY。"
    try:
        client = OpenAI(api_key=key, base_url=BASE_URL)
        result = client.chat.completions.create(
            model=MODEL, temperature=0,
            messages=[
                {"role": "system", "content": "将用户输入解析为单个实验操作 JSON。只输出JSON对象，字段为 has_operation, device_id, action, parameters, duration_seconds, chemicals, description。非实验请求 has_operation=false。不要判断安全，不要批准或执行。device_id无法确定时留空；duration缺失时填1；不得省略字段。"},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
        )
        proposal = json.loads(result.choices[0].message.content)
        if not proposal.get("has_operation"):
            return "这条消息没有识别到实验操作请求。ChemGuard 只对操作提议进行评估。"
        op = Operation(**{k: proposal[k] for k in ("device_id", "action", "parameters", "duration_seconds", "chemicals", "description")})
        evaluation = evaluate(op)
        event_id = record(op.model_dump(), evaluation.decision.value, evaluation.reasons)
        return ("**模型提取的操作提议**\n```json\n" + json.dumps(proposal, ensure_ascii=False, indent=2) +
                "\n```\n\n**ChemGuard 判定：" + evaluation.decision.value + "**\n\n原因：" +
                "；".join(evaluation.reasons) + f"\n\n审计编号：{event_id}\n\n仅供模拟评估；没有执行设备操作。")
    except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as exc:
        return f"操作提议格式无效，已按 HOLD 停止：{type(exc).__name__}。"
    except Exception as exc:
        return f"模型请求失败，未执行任何操作：{type(exc).__name__}。请检查 API 密钥、网络和模型配置。"


demo = gr.ChatInterface(chat, title="ChemGuard 安全评估", description="模型提出操作后，ChemGuard 本地规则会自动评估。此界面不会连接或控制真实设备。")

if __name__ == "__main__":
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise SystemExit("请先设置 DEEPSEEK_API_KEY 环境变量。")
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
