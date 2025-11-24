"""Coach 模块数据模型"""
from datetime import datetime
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid

from .session import Session


class CoachTask(BaseModel):
    """Coach Agent 生成的任务"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_goal: str = Field(..., description="任务所属的业务目标")
    task_description: str = Field(..., description="Coach Agent 生成的具体任务描述")
    difficulty: Literal["easy", "medium", "hard"] = Field("medium", description="任务难度")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 任务执行状态
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    
    # 任务执行结果
    session_id: Optional[str] = Field(None, description="关联的执行会话ID")
    outcome: Optional[Literal["success", "failure"]] = Field(None, description="执行结果")
    
    # Coach 的评估
    coach_feedback: Optional[str] = Field(None, description="Coach Agent 对执行结果的评估")
    
    # 学习结果
    learned_skill_id: Optional[str] = Field(None, description="学到的技能ID")
    learned_rule_id: Optional[str] = Field(None, description="学到的规则ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CoachTaskCreate(BaseModel):
    """创建 Coach 任务的请求模型"""
    business_goal: str
    task_description: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class CoachState(BaseModel):
    """Coach 模块的整体状态"""
    total_tasks: int = 0
    completed_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    skills_gained: int = 0
    rules_gained: int = 0
    last_update: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
