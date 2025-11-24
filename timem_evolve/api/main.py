"""FastAPI 主应用"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from typing import List, Optional

from ..dao.memory_dao import MemoryDAO
from ..services.session_service import SessionService
from ..services.learner_service import LearnerService
from ..services.coach_service import CoachService
from ..services.analyzer_service import AnalyzerService
from ..models import (
    Session, SessionCreate, 
    Skill, Rule, 
    Feedback, FeedbackCreate,
    CoachTask, CoachState, CoachTaskCreate
)


# 全局实例
dao = MemoryDAO(data_dir="./data")
session_service = SessionService(dao)
learner_service = LearnerService(dao)
coach_service = CoachService(dao, learner_service)
analyzer_service = AnalyzerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    await dao.init_db()
    yield


app = FastAPI(
    title="TiMEM-Evolve API",
    version="0.1.0",
    description="自进化智能体框架的后端服务",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


# ==================== Sessions ====================

@app.post("/sessions", response_model=Session)
async def add_session(session_create: SessionCreate):
    """添加新会话"""
    return await session_service.add_session(session_create)


@app.get("/sessions/{session_id}", response_model=Optional[Session])
async def get_session(session_id: str):
    """获取会话"""
    return await session_service.get_session(session_id)


@app.get("/sessions", response_model=List[Session])
async def list_sessions(outcome: Optional[str] = None, limit: int = 100):
    """列出会话"""
    return await session_service.list_sessions(outcome=outcome, limit=limit)


# ==================== Feedbacks ====================

@app.post("/feedbacks", response_model=Feedback)
async def add_feedback(feedback_create: FeedbackCreate):
    """添加反馈并触发学习"""
    feedback = Feedback(**feedback_create.model_dump())
    
    # 1. 保存反馈
    dao.save_feedback(feedback)
    
    # 2. 触发学习
    learned_id = await learner_service.learn_from_feedback(feedback)
    
    # 3. 重新获取反馈（可能已更新 learned 状态）
    if learned_id:
        feedback = dao.get_feedback(feedback.feedback_id)
    
    return feedback


@app.get("/feedbacks", response_model=List[Feedback])
async def list_feedbacks(
    session_id: Optional[str] = None, 
    learned: Optional[bool] = None, 
    limit: int = 100
):
    """列出反馈"""
    return dao.list_feedbacks(session_id=session_id, learned=learned, limit=limit)


# ==================== Skills ====================

@app.get("/skills", response_model=List[Skill])
async def list_skills(limit: int = 100):
    """列出技能"""
    return dao.list_skills(limit=limit)


@app.get("/skills/search", response_model=List[Skill])
async def search_skills(query: str, top_k: int = 5):
    """搜索技能"""
    return dao.search_skills(query=query, top_k=top_k)


# ==================== Rules ====================

@app.get("/rules", response_model=List[Rule])
async def list_rules(limit: int = 100):
    """列出规则"""
    return dao.list_rules(limit=limit)


@app.get("/rules/search", response_model=List[Rule])
async def search_rules(query: str, top_k: int = 5):
    """搜索规则"""
    return dao.search_rules(query=query, top_k=top_k)


# ==================== Learning ====================

@app.post("/learn/session/{session_id}", response_model=Optional[str])
async def learn_from_session(session_id: str):
    """从完整的会话中学习（成功->技能，失败->规则）"""
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.outcome == "success":
        skill = await learner_service.extract_skill_from_session(session)
        return skill.skill_id if skill else None
    elif session.outcome == "failure":
        rule = await learner_service.extract_rule_from_session(session)
        return rule.rule_id if rule else None
    
    return None


# ==================== Coach ====================

@app.get("/coach/state", response_model=CoachState)
async def get_coach_state():
    """获取 Coach 模块的统计状态"""
    return coach_service.get_state()


@app.post("/coach/generate_task", response_model=CoachTask)
async def generate_coach_task(task_create: CoachTaskCreate):
    """生成一个新的 Coach 任务"""
    try:
        task = await coach_service.generate_task(task_create.business_goal)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/coach/run_task/{task_id}", response_model=CoachTask)
async def run_coach_task(task_id: str):
    """运行一个 Coach 任务"""
    try:
        tasks = coach_service.list_tasks()
        task = next((t for t in tasks if t.task_id == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="Coach Task not found")
            
        if task.status != "pending":
            raise HTTPException(status_code=400, detail=f"Task status is {task.status}, only 'pending' tasks can be run.")
            
        # 异步运行任务
        # 注意：这里直接调用 run_task 会阻塞主线程，实际部署中应使用后台任务
        # 简化处理：直接调用
        updated_task = await coach_service.run_task(task)
        return updated_task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/coach/tasks", response_model=List[CoachTask])
async def list_coach_tasks(status: Optional[str] = None):
    """列出 Coach 任务"""
    return coach_service.list_tasks(status=status)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
