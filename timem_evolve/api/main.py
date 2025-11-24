"""FastAPI 主应用"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from typing import List, Optional

from ..core import MemoryStorage, SessionManager, Learner, CoachAgent
from ..models import (
    Session, SessionCreate, 
    Skill, Rule, 
    Feedback, FeedbackCreate,
    CoachTask, CoachState, CoachTaskCreate
)


# 全局实例
storage = MemoryStorage(data_dir="./data")
session_manager = SessionManager(storage)
learner = Learner(storage)
coach_agent = CoachAgent(storage, learner)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await storage.init_db()
    yield
    # 关闭时清理资源（如果需要）


app = FastAPI(
    title="TiMEM-Evolve API",
    description="Build Agents that EVOLVE Over Time - 时序记忆与经验学习",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """根路径重定向到文档"""
    return RedirectResponse(url="/docs")


# 导入并注册 MCP 路由
from .mcp_server import router as mcp_router
app.include_router(mcp_router)


# ==================== Sessions ====================

@app.post("/sessions", response_model=Session)
async def create_session(session_create: SessionCreate):
    """添加新会话"""
    try:
        session = await session_manager.add_session(session_create)
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", response_model=Session)
async def get_session(session_id: str):
    """获取会话详情"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/sessions", response_model=List[Session])
async def list_sessions(
    outcome: Optional[str] = None,
    limit: int = 100
):
    """列出会话"""
    try:
        sessions = await session_manager.list_sessions(outcome=outcome, limit=limit)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Feedbacks ====================

@app.post("/feedbacks", response_model=Feedback)
async def create_feedback(feedback_create: FeedbackCreate):
    """添加反馈并自动学习"""
    try:
        # 创建反馈
        feedback = Feedback(
            session_id=feedback_create.session_id,
            message_index=feedback_create.message_index,
            rating=feedback_create.rating,
            comment=feedback_create.comment
        )
        
        # 保存反馈
        storage.save_feedback(feedback)
        
        # 自动学习
        learned_id = await learner.learn_from_feedback(feedback)
        
        # 重新获取更新后的反馈
        feedback = storage.get_feedback(feedback.feedback_id)
        
        return feedback
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedbacks/{feedback_id}", response_model=Feedback)
async def get_feedback(feedback_id: str):
    """获取反馈详情"""
    feedback = storage.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


@app.get("/feedbacks", response_model=List[Feedback])
async def list_feedbacks(
    session_id: Optional[str] = None,
    learned: Optional[bool] = None,
    limit: int = 100
):
    """列出反馈"""
    try:
        feedbacks = storage.list_feedbacks(
            session_id=session_id,
            learned=learned,
            limit=limit
        )
        return feedbacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Skills ====================

@app.get("/skills/{skill_id}", response_model=Skill)
async def get_skill(skill_id: str):
    """获取技能详情"""
    skill = storage.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@app.get("/skills", response_model=List[Skill])
async def list_skills(limit: int = 100):
    """列出所有技能"""
    try:
        skills = storage.list_skills(limit=limit)
        return skills
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/skills/search/{query}", response_model=List[Skill])
async def search_skills(query: str, top_k: int = 5):
    """搜索技能"""
    try:
        skills = storage.search_skills(query=query, top_k=top_k)
        return skills
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Rules ====================

@app.get("/rules/{rule_id}", response_model=Rule)
async def get_rule(rule_id: str):
    """获取规则详情"""
    rule = storage.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@app.get("/rules", response_model=List[Rule])
async def list_rules(limit: int = 100):
    """列出所有规则"""
    try:
        rules = storage.list_rules(limit=limit)
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rules/search/{query}", response_model=List[Rule])
async def search_rules(query: str, top_k: int = 5):
    """搜索规则"""
    try:
        rules = storage.search_rules(query=query, top_k=top_k)
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Learning ====================

@app.post("/learn/session/{session_id}")
async def learn_from_session(session_id: str):
    """从完整会话中学习"""
    try:
        session = await storage.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        result = {}
        
        if session.outcome == "success":
            skill = await learner.extract_skill_from_session(session)
            if skill:
                result["skill_id"] = skill.skill_id
                result["type"] = "skill"
        elif session.outcome == "failure":
            rule = await learner.extract_rule_from_session(session)
            if rule:
                result["rule_id"] = rule.rule_id
                result["type"] = "rule"
        else:
            raise HTTPException(status_code=400, detail="Session outcome must be 'success' or 'failure'")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Coach ====================

@app.get("/coach/state", response_model=CoachState)
async def get_coach_state():
    """获取 Coach 模块的统计状态"""
    return coach_agent.get_state()


@app.post("/coach/generate_task", response_model=CoachTask)
async def generate_coach_task(task_create: CoachTaskCreate):
    """生成一个新的 Coach 任务"""
    try:
        task = await coach_agent.generate_task(task_create.business_goal)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/coach/run_task/{task_id}", response_model=CoachTask)
async def run_coach_task(task_id: str):
    """运行一个 Coach 任务"""
    try:
        tasks = coach_agent.list_tasks()
        task = next((t for t in tasks if t.task_id == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="Coach Task not found")
            
        if task.status != "pending":
            raise HTTPException(status_code=400, detail=f"Task status is {task.status}, only 'pending' tasks can be run.")
            
        # 异步运行任务
        # 注意：这里直接调用 run_task 会阻塞主线程，实际部署中应使用后台任务
        # 简化处理：直接调用
        updated_task = await coach_agent.run_task(task)
        return updated_task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/coach/tasks", response_model=List[CoachTask])
async def list_coach_tasks(status: Optional[str] = None):
    """列出 Coach 任务"""
    return coach_agent.list_tasks(status=status)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
