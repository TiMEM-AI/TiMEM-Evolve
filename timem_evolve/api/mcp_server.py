"""MCP 协议接口服务 - 用于工具调用"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json

from ..core import MemoryStorage, Learner
from ..models import Session, Message, Feedback, FeedbackCreate

# 假设 MemoryStorage 和 Learner 已经被初始化
# 在实际应用中，可以通过依赖注入或全局变量获取
storage = MemoryStorage(data_dir="./data")
learner = Learner(storage)

router = APIRouter()


class ToolCallRequest(BaseModel):
    """MCP 工具调用请求模型"""
    tool_name: str = Field(..., description="工具名称，例如 'evolve_agent'")
    function_name: str = Field(..., description="要调用的函数名")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="函数参数")


class ToolCallResponse(BaseModel):
    """MCP 工具调用响应模型"""
    status: str = Field(..., description="状态：success 或 error")
    result: Optional[Any] = Field(None, description="函数执行结果")
    error: Optional[str] = Field(None, description="错误信息")


class FeedbackToolArguments(BaseModel):
    """feedback_turn 函数的参数模型"""
    session_id: str = Field(..., description="会话ID")
    message_index: int = Field(..., description="消息索引")
    rating: str = Field(..., description="评价：positive 或 negative")
    comment: Optional[str] = Field(None, description="反馈文本")


class SearchToolArguments(BaseModel):
    """search_knowledge 函数的参数模型"""
    query: str = Field(..., description="查询关键词")
    knowledge_type: str = Field(..., description="知识类型：skill 或 rule")
    top_k: int = Field(5, description="返回数量")


async def feedback_turn(args: FeedbackToolArguments) -> Dict[str, Any]:
    """
    对单轮对话进行反馈并触发学习。
    
    Args:
        session_id: 会话ID
        message_index: 消息索引
        rating: 评价 (positive/negative)
        comment: 反馈文本
        
    Returns:
        学习结果 (learned_skill_id 或 learned_rule_id)
    """
    try:
        feedback_create = FeedbackCreate(
            session_id=args.session_id,
            message_index=args.message_index,
            rating=args.rating,
            comment=args.comment
        )
        
        feedback = Feedback(
            session_id=feedback_create.session_id,
            message_index=feedback_create.message_index,
            rating=feedback_create.rating,
            comment=feedback_create.comment
        )
        
        storage.save_feedback(feedback)
        learned_id = await learner.learn_from_feedback(feedback)
        
        # 重新获取更新后的反馈
        feedback = storage.get_feedback(feedback.feedback_id)
        
        result = {
            "feedback_id": feedback.feedback_id,
            "learned": feedback.learned,
            "learned_skill_id": feedback.learned_skill_id,
            "learned_rule_id": feedback.learned_rule_id
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback failed: {e}")


async def search_knowledge(args: SearchToolArguments) -> List[Dict[str, Any]]:
    """
    搜索已学习的技能或规则。
    
    Args:
        query: 查询关键词
        knowledge_type: 知识类型 (skill/rule)
        top_k: 返回数量
        
    Returns:
        匹配到的技能或规则列表
    """
    try:
        if args.knowledge_type == "skill":
            results = storage.search_skills(args.query, args.top_k)
        elif args.knowledge_type == "rule":
            results = storage.search_rules(args.query, args.top_k)
        else:
            raise ValueError("Invalid knowledge_type. Must be 'skill' or 'rule'.")
        
        return [r.model_dump(mode='json') for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


# 注册工具函数
TOOL_FUNCTIONS = {
    "feedback_turn": feedback_turn,
    "search_knowledge": search_knowledge,
}


@router.post("/mcp/tool_call", response_model=ToolCallResponse)
async def mcp_tool_call(request: ToolCallRequest):
    """MCP 工具调用接口"""
    
    if request.tool_name != "evolve_agent":
        return ToolCallResponse(
            status="error",
            error=f"Unknown tool_name: {request.tool_name}. Expected 'evolve_agent'."
        )
    
    if request.function_name not in TOOL_FUNCTIONS:
        return ToolCallResponse(
            status="error",
            error=f"Unknown function_name: {request.function_name} for tool 'evolve_agent'."
        )
    
    func = TOOL_FUNCTIONS[request.function_name]
    
    try:
        # 验证参数
        if request.function_name == "feedback_turn":
            args = FeedbackToolArguments(**request.arguments)
        elif request.function_name == "search_knowledge":
            args = SearchToolArguments(**request.arguments)
        else:
            # 对于其他函数，直接使用字典
            args = request.arguments
            
        result = await func(args)
        
        return ToolCallResponse(
            status="success",
            result=result
        )
    except HTTPException as e:
        return ToolCallResponse(
            status="error",
            error=e.detail
        )
    except Exception as e:
        return ToolCallResponse(
            status="error",
            error=f"Function execution failed: {e}"
        )


# 将 MCP 路由添加到主应用
from .main import app as main_app

main_app.include_router(router)
