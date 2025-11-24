"""
示例 2: 信息检索场景 - 从成功经验中提炼技能 (Skill)

模拟 Agent 在信息检索中表现出色，用户给出正面反馈，系统自动提炼出 SOP 技能。
"""
import asyncio
import os
from timem_evolve.sdk.client import EvolveClient
from timem_evolve.models import SessionCreate, Message, FeedbackCreate

# 假设 FastAPI 服务运行在 8000 端口
# os.environ["EVOLVE_API_URL"] = "http://127.0.0.1:8000"
client = EvolveClient()

async def search_to_skill_demo():
    print("--- 示例 2: 信息检索场景 (提炼 Skill) ---")
    
    # 1. 模拟一个成功的会话：Agent 给出结构清晰的回复
    session_create = SessionCreate(
        task="解释 TiMEM-Evolve 的核心概念",
        messages=[
            Message(role="user", content="请用简洁的语言解释 TiMEM-Evolve 的核心概念和工作原理。"),
            Message(role="assistant", content="TiMEM-Evolve 的核心是 '时序记忆' 和 '经验学习'。工作原理是：1. 记录会话；2. 提炼技能/规则；3. 应用知识。")
        ],
        # 标记为成功，因为 Agent 准确且简洁地完成了任务
        outcome="success" 
    )
    session = client.add_session(session_create)
    print(f"会话创建成功: {session.session_id}")
    print(f"会话结果: {session.outcome}")

    # 2. 用户给出正面反馈：针对 Agent 的第一次回复 (索引 1)
    feedback_create = FeedbackCreate(
        session_id=session.session_id,
        message_index=1, 
        rating="positive",
        comment="回复结构清晰，抓住了核心概念，并用数字列表进行了总结，非常棒。"
    )
    feedback = client.add_feedback(feedback_create)
    print(f"反馈添加成功: {feedback.feedback_id}")

    # 3. 检查学习结果
    if feedback.learned and feedback.learned_skill_id:
        skill = client.list_skills(limit=1)[0] # 假设这是最新学习的技能
        print("\n--- 学习到的技能 (Skill) ---")
        print(f"技能 ID: {skill.skill_id}")
        print(f"技能名称: {skill.name}")
        print(f"技能描述: {skill.description}")
        print(f"SOP 步骤: {skill.workflow.steps}")
        print(f"来源会话: {skill.source_sessions}")
    else:
        print("\n未成功提炼出技能，请检查 LLM 响应。")

if __name__ == "__main__":
    # 运行前请确保 FastAPI 服务已启动: python -m timem_evolve.api.main
    asyncio.run(search_to_skill_demo())
