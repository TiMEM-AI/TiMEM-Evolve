"""反馈数据模型"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid


class Feedback(BaseModel):
    """对单轮对话的反馈"""
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(..., description="所属会话ID")
    message_index: int = Field(..., description="消息索引（在会话中的位置）")
    rating: Literal["positive", "negative"] = Field(..., description="好评/差评")
    comment: Optional[str] = Field(None, description="反馈文本")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # 学习结果
    learned: bool = Field(default=False, description="是否已学习")
    learned_skill_id: Optional[str] = Field(None, description="学到的技能ID")
    learned_rule_id: Optional[str] = Field(None, description="学到的规则ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FeedbackCreate(BaseModel):
    """创建反馈的请求模型"""
    session_id: str
    message_index: int
    rating: Literal["positive", "negative"]
    comment: Optional[str] = None
