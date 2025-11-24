"""技能数据模型"""
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class Workflow(BaseModel):
    """工作流程"""
    steps: List[str] = Field(..., description="执行步骤")
    sop: str = Field(..., description="标准操作流程描述")


class Skill(BaseModel):
    """从成功经验中提炼的技能"""
    skill_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="技能名称")
    description: str = Field(..., description="技能描述")
    workflow: Workflow = Field(..., description="工作流程")
    source_sessions: List[str] = Field(default_factory=list, description="来源会话ID")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
