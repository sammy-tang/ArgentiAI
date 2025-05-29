# schemas.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_input: str
    session_id: str = None