"""
示例 1: 代码调试场景 - 从失败经验中提炼规则 (Rule)

模拟 Agent 在代码调试中犯错，用户给出负面反馈，系统自动提炼出一条规则。
"""
import asyncio
import os
from timem_evolve.sdk.client import EvolveClient
from timem_evolve.models import SessionCreate, Message, FeedbackCreate

# 假设 FastAPI 服务运行在 8000 端口
# os.environ["EVOLVE_API_URL"] = "http://127.0.0.1:8000"
client = EvolveClient()

async def debug_to_rule_demo():
    print("--- 示例 1: 代码调试场景 (提炼 Rule) ---")
    
    # 1. 模拟一个失败的会话：Agent 给出错误的调试建议
    session_create = SessionCreate(
        task="调试 Python 字典键错误",
        messages=[
            Message(role="user", content="我的 Python 代码报 KeyError，我确定键名是对的，请帮我看看。"),
            Message(role="assistant", content="KeyError 通常是键名写错了，请仔细检查你的拼写。"),
            Message(role="user", content="我检查了，是正确的。问题出在大小写上，我忘了 Python 字典是区分大小写的。")
        ],
        # 标记为失败，因为 Agent 没有给出正确的诊断
        outcome="failure" 
    )
    session = client.add_session(session_create)
    print(f"会话创建成功: {session.session_id}")
    print(f"会话结果: {session.outcome}")

    # 2. 用户给出负面反馈：针对 Agent 的第一次回复 (索引 1)
    feedback_create = FeedbackCreate(
        session_id=session.session_id,
        message_index=1, 
        rating="negative",
        comment="Agent 忽略了用户强调的'确定键名是对的'，没有考虑到大小写敏感性，诊断不全面。"
    )
    feedback = client.add_feedback(feedback_create)
    print(f"反馈添加成功: {feedback.feedback_id}")

    # 3. 检查学习结果
    if feedback.learned and feedback.learned_rule_id:
        rule = client.list_rules(limit=1)[0] # 假设这是最新学习的规则
        print("\n--- 学习到的规则 (Rule) ---")
        print(f"规则 ID: {rule.rule_id}")
        print(f"规则名称: {rule.name}")
        print(f"规则描述: {rule.description}")
        print(f"约束条件: {rule.constraint}")
        print(f"来源会话: {rule.source_sessions}")
    else:
        print("\n未成功提炼出规则，请检查 LLM 响应。")

if __name__ == "__main__":
    # 运行前请确保 FastAPI 服务已启动: python -m timem_evolve.api.main
    asyncio.run(debug_to_rule_demo())
