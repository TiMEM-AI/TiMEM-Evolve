"""学习器 - 从会话和反馈中提炼技能和规则"""
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..models import Session, Skill, Rule, Feedback, Workflow, Message
from ..dao.memory_dao import MemoryDAO


class LearnerService:
    """经验学习器"""
    
    def __init__(self, dao: MemoryDAO, model_name: str = "gpt-4.1-mini"):
        self.dao = dao
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
    
    async def learn_from_feedback(self, feedback: Feedback) -> Optional[str]:
        """从单轮反馈中学习
        
        Returns:
            学到的 skill_id 或 rule_id
        """
        # 获取会话
        session = await self.dao.get_session(feedback.session_id)
        if not session:
            return None
        
        # 获取对应的消息对（用户消息 + AI回复）
        if feedback.message_index < 0 or feedback.message_index >= len(session.messages):
            return None
        
        # 构建上下文：前面的消息 + 当前这一轮
        context_messages = session.messages[:feedback.message_index + 1]
        current_turn = self._extract_dialog_turn(context_messages, feedback.message_index)
        
        if feedback.rating == "positive":
            # 好评 -> 提炼技能
            skill = await self._extract_skill_from_turn(
                task=session.task,
                dialog_turn=current_turn,
                feedback_comment=feedback.comment
            )
            if skill:
                skill.source_sessions = [session.session_id]
                skill.metadata["feedback_id"] = feedback.feedback_id
                self.dao.save_skill(skill)
                
                # 更新反馈状态
                feedback.learned = True
                feedback.learned_skill_id = skill.skill_id
                self.dao.save_feedback(feedback)
                
                return skill.skill_id
        else:
            # 差评 -> 提炼规则
            rule = await self._extract_rule_from_turn(
                task=session.task,
                dialog_turn=current_turn,
                feedback_comment=feedback.comment
            )
            if rule:
                rule.source_sessions = [session.session_id]
                rule.metadata["feedback_id"] = feedback.feedback_id
                self.dao.save_rule(rule)
                
                # 更新反馈状态
                feedback.learned = True
                feedback.learned_rule_id = rule.rule_id
                self.dao.save_feedback(feedback)
                
                return rule.rule_id
        
        return None
    
    def _extract_dialog_turn(self, messages: list, current_index: int) -> dict:
        """提取对话轮次"""
        # 找到当前 AI 回复对应的用户消息
        user_msg = None
        ai_msg = messages[current_index]
        
        # 向前查找最近的用户消息
        for i in range(current_index - 1, -1, -1):
            msg = messages[i]
            role = msg.role if hasattr(msg, 'role') else msg.get('role')
            if role == "user":
                user_msg = msg
                break
        
        return {
            "user_message": user_msg.content if user_msg else "",
            "ai_response": ai_msg.content if hasattr(ai_msg, 'content') else ai_msg.get('content', ''),
            "context": self._format_messages(messages[:current_index])
        }
    
    def _format_messages(self, messages) -> str:
        """格式化消息"""
        formatted = []
        for msg in messages:
            role = msg.role if hasattr(msg, 'role') else msg.get('role', 'unknown')
            content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
    
    async def _extract_skill_from_turn(
        self, 
        task: str,
        dialog_turn: dict,
        feedback_comment: Optional[str]
    ) -> Optional[Skill]:
        """从好评的对话轮次中提炼技能"""
        
        prompt = f"""
基于以下用户好评的对话，提炼一个可复用的技能。

任务背景: {task}

对话上下文:
{dialog_turn['context']}

当前对话轮次:
用户: {dialog_turn['user_message']}
AI: {dialog_turn['ai_response']}

用户反馈: {feedback_comment or '好评'}

请分析这个AI回复为什么获得好评，并提炼成一个可复用的技能。

以 JSON 格式返回：
{{
    "name": "技能名称（简短，例如：清晰的代码解释）",
    "description": "技能描述（1-2句话，说明这个技能是什么）",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "sop": "详细的标准操作流程描述（如何应用这个技能）",
    "confidence": 0.8
}}

只返回 JSON，不要其他内容。
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # 提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            return Skill(
                name=data["name"],
                description=data["description"],
                workflow=Workflow(
                    steps=data["steps"],
                    sop=data["sop"]
                ),
                confidence=data.get("confidence", 0.7)
            )
        except Exception as e:
            print(f"提炼技能失败: {e}")
            return None
    
    async def _extract_rule_from_turn(
        self,
        task: str,
        dialog_turn: dict,
        feedback_comment: Optional[str]
    ) -> Optional[Rule]:
        """从差评的对话轮次中提炼规则"""
        
        prompt = f"""
基于以下用户差评的对话，提炼一个约束规则。

任务背景: {task}

对话上下文:
{dialog_turn['context']}

当前对话轮次:
用户: {dialog_turn['user_message']}
AI: {dialog_turn['ai_response']}

用户反馈: {feedback_comment or '差评'}

请分析这个AI回复为什么获得差评，并提炼成一个约束规则，避免未来犯同样的错误。

以 JSON 格式返回：
{{
    "name": "规则名称（简短，例如：避免过于技术化的解释）",
    "description": "规则描述（1-2句话，说明这个规则是什么）",
    "constraint": "约束条件（应该避免什么行为）",
    "reason": "原因说明（为什么需要这个规则）",
    "confidence": 0.8
}}

只返回 JSON，不要其他内容。
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # 提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            return Rule(
                name=data["name"],
                description=data["description"],
                constraint=data["constraint"],
                reason=data["reason"],
                confidence=data.get("confidence", 0.7)
            )
        except Exception as e:
            print(f"提炼规则失败: {e}")
            return None
    
    async def extract_skill_from_session(self, session: Session) -> Optional[Skill]:
        """从成功的完整会话中提炼技能"""
        
        prompt = f"""
基于以下成功的任务会话，提炼一个可复用的技能。

任务: {session.task}

会话消息:
{self._format_messages(session.messages)}

请分析这个任务是如何成功完成的，并提炼成一个可复用的技能。

以 JSON 格式返回：
{{
    "name": "技能名称",
    "description": "技能描述",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "sop": "详细的标准操作流程描述",
    "confidence": 0.8
}}

只返回 JSON，不要其他内容。
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # 提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            skill = Skill(
                name=data["name"],
                description=data["description"],
                workflow=Workflow(
                    steps=data["steps"],
                    sop=data["sop"]
                ),
                confidence=data.get("confidence", 0.7),
                source_sessions=[session.session_id]
            )
            
            self.dao.save_skill(skill)
            return skill
            
        except Exception as e:
            print(f"提炼技能失败: {e}")
            return None
    
    async def extract_rule_from_session(self, session: Session) -> Optional[Rule]:
        """从失败的完整会话中提炼规则"""
        
        prompt = f"""
基于以下失败的任务会话，提炼一个约束规则。

任务: {session.task}

会话消息:
{self._format_messages(session.messages)}

请分析这个任务为什么失败，并提炼成一个约束规则。

以 JSON 格式返回：
{{
    "name": "规则名称",
    "description": "规则描述",
    "constraint": "约束条件",
    "reason": "原因说明",
    "confidence": 0.8
}}

只返回 JSON，不要其他内容。
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # 提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            rule = Rule(
                name=data["name"],
                description=data["description"],
                constraint=data["constraint"],
                reason=data["reason"],
                confidence=data.get("confidence", 0.7),
                source_sessions=[session.session_id]
            )
            
            self.dao.save_rule(rule)
            return rule
            
        except Exception as e:
            print(f"提炼规则失败: {e}")
            return None
