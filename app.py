# app.py
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from schemas import ChatRequest
from chat_session import ChatSession
import json
from threading import Lock

app = FastAPI()

# 处理跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会话存储（生产环境建议使用Redis等持久化存储）
sessions = {}


def get_session(session_id: str) -> ChatSession:
    if session_id not in sessions:
        sessions[session_id] = ChatSession()
    return sessions[session_id]


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id or uuid.uuid4().hex
    session = get_session(session_id)

    def generate():
        try:
            # 直接 yield 纯文本块，无需 JSON 包装
            for chunk in session.stream_response(request.user_input):
                yield chunk  # 直接发送文本片段，如 "Hello", " how are you?"
        except Exception as e:
            # 错误处理：返回非 200 状态码（前端通过 catch 捕获）
            raise HTTPException(status_code=500, detail=str(e))

    # 返回纯文本流，并添加会话 ID 到 Header
    return StreamingResponse(
        generate(),
        media_type="text/plain",  # 修改为普通文本流
        headers={
            "X-Session-ID": session_id,
            "Content-Disposition": "inline",  # 确保无特殊符号
            "Cache-Control": "no-cache",  # 防止代理缓存流数据
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)