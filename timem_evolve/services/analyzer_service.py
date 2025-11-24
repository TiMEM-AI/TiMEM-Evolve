"""LangGraph 分析器 - 使用 LLM 反思和分析会话"""
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os

from ..models import Session


class AnalysisState(TypedDict):
    """分析状态"""
    session: Session
    task_type: str
    is_successful: bool
    key_insights: str
    reflection: str
    error: str


class AnalyzerService:
    """基于 LangGraph 的会话分析器"""
    
    def __init__(self, model_name: str = "gpt-4.1-mini"):
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
        )
        
        # 构建图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建分析流程图"""
        workflow = StateGraph(AnalysisState)
        
        # 添加节点
        workflow.add_node("identify_task", self._identify_task)
        workflow.add_node("evaluate_outcome", self._evaluate_outcome)
        workflow.add_node("extract_insights", self._extract_insights)
        workflow.add_node("reflect", self._reflect)
        
        # 定义边
        workflow.set_entry_point("identify_task")
        workflow.add_edge("identify_task", "evaluate_outcome")
        workflow.add_edge("evaluate_outcome", "extract_insights")
        workflow.add_edge("extract_insights", "reflect")
        workflow.add_edge("reflect", END)
        
        return workflow.compile()
    
    async def _identify_task(self, state: AnalysisState) -> AnalysisState:
        """识别任务类型"""
        session = state["session"]
        
        prompt = f"""
分析以下任务会话，识别任务类型和目标。

任务描述: {session.task}

会话消息:
{self._format_messages(session.messages)}

请简洁地描述这个任务的类型（例如：数据分析、代码调试、信息检索等）。
只需要返回任务类型，不要其他内容。
"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        state["task_type"] = response.content.strip()
        return state
    
    async def _evaluate_outcome(self, state: AnalysisState) -> AnalysisState:
        """评估任务结果"""
        session = state["session"]
        
        # 如果已经标记了结果，直接使用
        if session.outcome in ["success", "failure"]:
            state["is_successful"] = (session.outcome == "success")
        else:
            # 使用 LLM 评估
            prompt = f"""
分析以下任务会话，判断任务是否成功完成。

任务描述: {session.task}

会话消息:
{self._format_messages(session.messages)}

请判断这个任务是否成功完成。只需要返回 "成功" 或 "失败"，不要其他内容。
"""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            state["is_successful"] = "成功" in response.content
        
        return state
    
    async def _extract_insights(self, state: AnalysisState) -> AnalysisState:
        """提取关键洞察"""
        session = state["session"]
        
        if state["is_successful"]:
            prompt = f"""
分析以下成功的任务会话，提取关键的成功要素和方法。

任务类型: {state['task_type']}
任务描述: {session.task}

会话消息:
{self._format_messages(session.messages)}

请提取：
1. 关键的成功步骤
2. 使用的方法和技巧
3. 可以复用的模式

以简洁的要点形式返回。
"""
        else:
            prompt = f"""
分析以下失败的任务会话，提取失败的原因和教训。

任务类型: {state['task_type']}
任务描述: {session.task}

会话消息:
{self._format_messages(session.messages)}

请提取：
1. 失败的原因
2. 遇到的问题
3. 应该避免的做法

以简洁的要点形式返回。
"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        state["key_insights"] = response.content.strip()
        return state
    
    async def _reflect(self, state: AnalysisState) -> AnalysisState:
        """反思和总结"""
        session = state["session"]
        
        if state["is_successful"]:
            prompt = f"""
基于以下成功案例的分析，生成一个可复用的技能总结。

任务类型: {state['task_type']}
任务描述: {session.task}
关键洞察: {state['key_insights']}

请生成：
1. 技能名称（简短）
2. 技能描述（1-2句话）
3. 标准操作流程（SOP，3-5个步骤）

以 JSON 格式返回：
{{
    "name": "技能名称",
    "description": "技能描述",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "sop": "详细的标准操作流程描述"
}}
"""
        else:
            prompt = f"""
基于以下失败案例的分析，生成一个约束规则。

任务类型: {state['task_type']}
任务描述: {session.task}
关键洞察: {state['key_insights']}

请生成：
1. 规则名称（简短）
2. 规则描述（1-2句话）
3. 约束条件（应该避免什么）
4. 原因（为什么需要这个规则）

以 JSON 格式返回：
{{
    "name": "规则名称",
    "description": "规则描述",
    "constraint": "约束条件",
    "reason": "原因说明"
}}
"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        state["reflection"] = response.content.strip()
        return state
    
    def _format_messages(self, messages) -> str:
        """格式化消息"""
        formatted = []
        for msg in messages:
            role = msg.role if hasattr(msg, 'role') else msg.get('role', 'unknown')
            content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
    
    async def analyze(self, session: Session) -> AnalysisState:
        """分析会话"""
        initial_state: AnalysisState = {
            "session": session,
            "task_type": "",
            "is_successful": False,
            "key_insights": "",
            "reflection": "",
            "error": ""
        }
        
        try:
            result = await self.graph.ainvoke(initial_state)
            return result
        except Exception as e:
            initial_state["error"] = str(e)
            return initial_state
