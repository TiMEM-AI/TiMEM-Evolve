"""会话数据模型"""
from datetime import datetime
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid


class Message(BaseModel):
    """单条消息"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Session(BaseModel):
    """任务会话"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task: str = Field(..., description="任务描述")
    messages: List[Message] = Field(default_factory=list)
    outcome: Literal["success", "failure", "unknown"] = "unknown"
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionCreate(BaseModel):
    """创建会话的请求模型"""
    task: str
    messages: List[Message]
    outcome: Literal["success", "failure", "unknown"] = "unknown"
    metadata: Dict[str, Any] = Field(default_factory=dict)
