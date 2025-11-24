"""Coach 模块核心逻辑 - Gym 模式"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..models import CoachTask, CoachTaskCreate, CoachState, Session, Message
from .storage import MemoryStorage
from .learner import Learner


class CoachStorage:
    """Coach 任务存储（简化为 JSON 文件）"""
    
    def __init__(self, data_dir: str = "./data"):
        self.tasks_path = Path(data_dir) / "coach_tasks.json"
        if not self.tasks_path.exists():
            self.tasks_path.write_text("[]")
        
    def _load_tasks(self) -> List[Dict[str, Any]]:
        return json.loads(self.tasks_path.read_text())
    
    def _save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        self.tasks_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))
        
    def save_task(self, task: CoachTask) -> None:
        tasks = self._load_tasks()
        
        # 检查是否已存在
        for i, t in enumerate(tasks):
            if t["task_id"] == task.task_id:
                tasks[i] = task.model_dump(mode='json')
                self._save_tasks(tasks)
                return
        
        # 新增
        tasks.append(task.model_dump(mode='json'))
        self._save_tasks(tasks)
        
    def list_tasks(self, status: Optional[str] = None) -> List[CoachTask]:
        tasks = self._load_tasks()
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        return [CoachTask(**t) for t in tasks]


class CoachAgent:
    """Coach Agent - 负责生成任务、观察和评估"""
    
    def __init__(self, storage: MemoryStorage, learner: Learner, model_name: str = "gpt-4.1-mini"):
        self.storage = storage
        self.coach_storage = CoachStorage(data_dir=storage.data_dir)
        self.learner = learner
        self.llm = ChatOpenAI(model=model_name, temperature=0.5)
        self.learner_llm = ChatOpenAI(model=model_name, temperature=0.7) # 模拟 Learner Agent
        
        # Coach Agent 的 LangGraph
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """构建 Coach Agent 的工作流"""
        
        class CoachGraphState(BaseModel):
            task: CoachTask
            session: Optional[Session] = None
            
        workflow = StateGraph(CoachGraphState)
        
        workflow.add_node("execute_task", self._execute_task)
        workflow.add_node("evaluate_result", self._evaluate_result)
        workflow.add_node("learn_from_session", self._learn_from_session)
        
        workflow.set_entry_point("execute_task")
        workflow.add_edge("execute_task", "evaluate_result")
        workflow.add_edge("evaluate_result", "learn_from_session")
        workflow.add_edge("learn_from_session", END)
        
        return workflow.compile()
        
    async def generate_task(self, business_goal: str) -> CoachTask:
        """生成一个有益的任务"""
        
        prompt = f"""
你是一个经验丰富的 Coach Agent，你的目标是为 Learner Agent 生成一个有挑战性且有益的学习任务。
Learner Agent 的目标是积累技能（SOP/Workflow）和规则（约束）。

当前业务目标: {business_goal}

请根据这个目标，生成一个具体的、可执行的任务描述，并评估其难度。

输出 JSON 格式：
{{
    "task_description": "具体的任务描述，例如：编写一个 Python 函数，实现快速排序算法，并处理边界条件。",
    "difficulty": "easy" | "medium" | "hard"
}}
"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        
        task = CoachTask(
            business_goal=business_goal,
            task_description=data["task_description"],
            difficulty=data["difficulty"],
            status="pending"
        )
        self.coach_storage.save_task(task)
        return task
        
    async def run_task(self, task: CoachTask) -> CoachTask:
        """运行 Coach 任务"""
        
        task.status = "running"
        self.coach_storage.save_task(task)
        
        try:
            # 运行 LangGraph
            result = await self.graph.ainvoke({"task": task})
            
            # 更新任务状态
            final_task = result["task"]
            final_task.status = "completed"
            final_task.session_id = result["session"].session_id
            final_task.outcome = result["session"].outcome
            
            self.coach_storage.save_task(final_task)
            return final_task
            
        except Exception as e:
            task.status = "failed"
            task.coach_feedback = f"执行失败: {e}"
            self.coach_storage.save_task(task)
            raise
            
    async def _execute_task(self, state: CoachGraphState) -> CoachGraphState:
        """模拟 Learner Agent 执行任务"""
        task = state.task
        
        # 模拟 Learner Agent 的对话
        system_prompt = f"你是一个 Learner Agent，你的任务是完成 Coach Agent 给你布置的任务：{task.task_description}。请尝试完成任务，并提供最终结果。"
        
        # 模拟对话过程
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=task.task_description),
        ]
        
        # 模拟执行
        response = await self.learner_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=task.task_description)
        ])
        
        messages.append(Message(role="assistant", content=response.content))
        
        # 模拟 Coach Agent 评估任务结果
        evaluation_prompt = f"""
Learner Agent 尝试完成以下任务：
任务描述: {task.task_description}

Learner Agent 的最终回复:
{response.content}

请以 Coach Agent 的身份，严格评估 Learner Agent 的回复是否成功完成了任务。
如果成功，返回 "success"。如果失败或不完整，返回 "failure"。
只需要返回 "success" 或 "failure"，不要其他内容。
"""
        evaluation_response = await self.llm.ainvoke([HumanMessage(content=evaluation_prompt)])
        outcome = evaluation_response.content.strip().lower()
        
        if outcome not in ["success", "failure"]:
            outcome = "failure" # 默认失败
            
        # 创建会话
        session = Session(
            task=task.task_description,
            messages=messages,
            outcome=outcome
        )
        await self.storage.save_session(session)
        
        state.session = session
        return state
        
    async def _evaluate_result(self, state: CoachGraphState) -> CoachGraphState:
        """Coach Agent 评估并生成反馈"""
        session = state.session
        
        prompt = f"""
你是一个 Coach Agent，你正在评估 Learner Agent 的表现。

任务描述: {session.task}
执行结果: {session.outcome}

Learner Agent 的对话:
{self.learner._format_messages(session.messages)}

请根据执行结果，为 Learner Agent 生成一个详细的反馈和总结。
如果成功，总结成功的关键步骤。如果失败，指出失败的原因和改进方向。
"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        state.task.coach_feedback = response.content.strip()
        return state
        
    async def _learn_from_session(self, state: CoachGraphState) -> CoachGraphState:
        """Learner Agent 从 Coach 的会话中学习"""
        session = state.session
        task = state.task
        
        if session.outcome == "success":
            skill = await self.learner.extract_skill_from_session(session)
            if skill:
                task.learned_skill_id = skill.skill_id
                task.learned_rule_id = None
        elif session.outcome == "failure":
            rule = await self.learner.extract_rule_from_session(session)
            if rule:
                task.learned_rule_id = rule.rule_id
                task.learned_skill_id = None
        
        return state
        
    def get_state(self) -> CoachState:
        """获取 Coach 模块的统计状态"""
        tasks = self.coach_storage.list_tasks()
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "completed"])
        successful_tasks = len([t for t in tasks if t.outcome == "success"])
        failed_tasks = len([t for t in tasks if t.outcome == "failure"])
        
        skills_gained = len([t for t in tasks if t.learned_skill_id])
        rules_gained = len([t for t in tasks if t.learned_rule_id])
        
        return CoachState(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            skills_gained=skills_gained,
            rules_gained=rules_gained,
            last_update=datetime.now()
        )
        
    def list_tasks(self, status: Optional[str] = None) -> List[CoachTask]:
        """列出 Coach 任务"""
        return self.coach_storage.list_tasks(status=status)

from pathlib import Path
