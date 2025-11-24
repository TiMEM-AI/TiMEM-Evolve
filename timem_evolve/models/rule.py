"""规则数据模型"""
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class Rule(BaseModel):
    """从失败经验中提炼的规则"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="规则名称")
    description: str = Field(..., description="规则描述")
    constraint: str = Field(..., description="约束条件")
    reason: str = Field(..., description="为什么需要这个规则")
    source_sessions: List[str] = Field(default_factory=list, description="来源会话ID")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
