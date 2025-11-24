"""基础使用示例 - TiMEM-Evolve"""
import asyncio
from timem_evolve import (
    MemoryStorage,
    SessionManager,
    Learner,
    SessionCreate,
    Message,
    FeedbackCreate
)


async def main():
    """基础使用示例"""
    
    # 1. 初始化存储和管理器
    print("📦 初始化 TiMEM-Evolve...")
    storage = MemoryStorage(data_dir="./data")
    await storage.init_db()
    
    session_manager = SessionManager(storage)
    learner = Learner(storage)
    
    # 2. 添加一个成功的会话
    print("\n✅ 添加成功会话...")
    success_session = await session_manager.add_session(
        SessionCreate(
            task="帮助用户理解 Python 装饰器",
            messages=[
                Message(role="user", content="什么是 Python 装饰器？"),
                Message(
                    role="assistant",
                    content="装饰器是 Python 中一种特殊的语法，用于修改函数或类的行为。简单来说，装饰器就是一个函数，它接收另一个函数作为参数，并返回一个新的函数。"
                ),
                Message(role="user", content="能举个例子吗？"),
                Message(
                    role="assistant",
                    content="""当然！这是一个简单的例子：

```python
def my_decorator(func):
    def wrapper():
        print("在函数执行前")
        func()
        print("在函数执行后")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()
```

这会输出：
```
在函数执行前
Hello!
在函数执行后
```
"""
                )
            ],
            outcome="success"
        )
    )
    print(f"会话ID: {success_session.session_id}")
    
    # 3. 从成功会话中学习技能
    print("\n🎓 从成功会话中学习技能...")
    skill = await learner.extract_skill_from_session(success_session)
    if skill:
        print(f"✨ 学到技能: {skill.name}")
        print(f"   描述: {skill.description}")
        print(f"   置信度: {skill.confidence:.2f}")
        print(f"   步骤: {', '.join(skill.workflow.steps)}")
    
    # 4. 添加一个失败的会话
    print("\n❌ 添加失败会话...")
    failure_session = await session_manager.add_session(
        SessionCreate(
            task="解释机器学习算法",
            messages=[
                Message(role="user", content="什么是梯度下降？"),
                Message(
                    role="assistant",
                    content="梯度下降是一种基于一阶导数的优化算法，通过迭代地沿着目标函数梯度的反方向更新参数，以最小化损失函数 J(θ) = 1/2m Σ(h(x) - y)²..."
                ),
                Message(role="user", content="太复杂了，能说得简单点吗？")
            ],
            outcome="failure"
        )
    )
    print(f"会话ID: {failure_session.session_id}")
    
    # 5. 从失败会话中学习规则
    print("\n📚 从失败会话中学习规则...")
    rule = await learner.extract_rule_from_session(failure_session)
    if rule:
        print(f"⚠️ 学到规则: {rule.name}")
        print(f"   描述: {rule.description}")
        print(f"   约束: {rule.constraint}")
        print(f"   原因: {rule.reason}")
        print(f"   置信度: {rule.confidence:.2f}")
    
    # 6. 使用反馈功能（对单轮对话进行评价）
    print("\n👍 添加好评反馈...")
    positive_feedback = FeedbackCreate(
        session_id=success_session.session_id,
        message_index=1,  # 第一个 AI 回复
        rating="positive",
        comment="解释得很清晰，易于理解"
    )
    
    # 保存反馈
    feedback = await create_and_learn_from_feedback(storage, learner, positive_feedback)
    if feedback.learned:
        print(f"✅ 从反馈中学到了技能: {feedback.learned_skill_id}")
    
    # 7. 查询学到的技能
    print("\n📋 查询所有技能...")
    skills = storage.list_skills()
    print(f"共有 {len(skills)} 个技能:")
    for s in skills:
        print(f"  - {s.name} (置信度: {s.confidence:.2f})")
    
    # 8. 查询学到的规则
    print("\n📋 查询所有规则...")
    rules = storage.list_rules()
    print(f"共有 {len(rules)} 个规则:")
    for r in rules:
        print(f"  - {r.name} (置信度: {r.confidence:.2f})")
    
    # 9. 搜索技能
    print("\n🔍 搜索技能...")
    search_results = storage.search_skills("装饰器")
    print(f"找到 {len(search_results)} 个相关技能:")
    for s in search_results:
        print(f"  - {s.name}")
    
    print("\n✅ 示例完成！")
    print("\n💡 提示:")
    print("  - 运行 FastAPI 服务: python -m timem_evolve.api.main")
    print("  - 运行 Gradio UI: python -m timem_evolve.ui.gradio_app")


async def create_and_learn_from_feedback(storage, learner, feedback_create):
    """创建反馈并学习"""
    from timem_evolve.models import Feedback
    
    feedback = Feedback(
        session_id=feedback_create.session_id,
        message_index=feedback_create.message_index,
        rating=feedback_create.rating,
        comment=feedback_create.comment
    )
    
    storage.save_feedback(feedback)
    await learner.learn_from_feedback(feedback)
    
    return storage.get_feedback(feedback.feedback_id)


if __name__ == "__main__":
    asyncio.run(main())
