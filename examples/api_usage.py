"""FastAPI 使用示例 - 通过 HTTP API 使用 TiMEM-Evolve"""
import requests
import json


# API 基础 URL
BASE_URL = "http://localhost:8000"


def example_api_usage():
    """API 使用示例"""
    
    print("🚀 TiMEM-Evolve API 使用示例\n")
    
    # 1. 创建会话
    print("1️⃣ 创建会话...")
    session_data = {
        "task": "帮助用户调试 Python 代码",
        "messages": [
            {
                "role": "user",
                "content": "我的代码报错了：TypeError: 'int' object is not iterable"
            },
            {
                "role": "assistant",
                "content": "这个错误通常是因为你尝试对一个整数进行迭代。能分享一下你的代码吗？"
            },
            {
                "role": "user",
                "content": "for i in 5: print(i)"
            },
            {
                "role": "assistant",
                "content": "找到问题了！你应该使用 range(5) 而不是直接用 5。正确的写法是：for i in range(5): print(i)"
            }
        ],
        "outcome": "success"
    }
    
    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    session = response.json()
    session_id = session["session_id"]
    print(f"✅ 会话创建成功: {session_id}\n")
    
    # 2. 添加反馈
    print("2️⃣ 添加好评反馈...")
    feedback_data = {
        "session_id": session_id,
        "message_index": 3,  # 最后一个 AI 回复
        "rating": "positive",
        "comment": "解决了我的问题，解释得很清楚"
    }
    
    response = requests.post(f"{BASE_URL}/feedbacks", json=feedback_data)
    feedback = response.json()
    print(f"✅ 反馈创建成功: {feedback['feedback_id']}")
    print(f"   已学习: {feedback['learned']}")
    if feedback.get('learned_skill_id'):
        print(f"   学到技能: {feedback['learned_skill_id']}\n")
    
    # 3. 查询所有技能
    print("3️⃣ 查询所有技能...")
    response = requests.get(f"{BASE_URL}/skills")
    skills = response.json()
    print(f"✅ 共有 {len(skills)} 个技能:")
    for skill in skills[:3]:  # 只显示前3个
        print(f"   - {skill['name']} (置信度: {skill['confidence']:.2f})")
    print()
    
    # 4. 搜索技能
    print("4️⃣ 搜索技能...")
    query = "调试"
    response = requests.get(f"{BASE_URL}/skills/search/{query}")
    skills = response.json()
    print(f"✅ 搜索 '{query}' 找到 {len(skills)} 个技能:")
    for skill in skills:
        print(f"   - {skill['name']}")
    print()
    
    # 5. 查询所有规则
    print("5️⃣ 查询所有规则...")
    response = requests.get(f"{BASE_URL}/rules")
    rules = response.json()
    print(f"✅ 共有 {len(rules)} 个规则:")
    for rule in rules[:3]:  # 只显示前3个
        print(f"   - {rule['name']} (置信度: {rule['confidence']:.2f})")
    print()
    
    # 6. 获取会话详情
    print("6️⃣ 获取会话详情...")
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    session_detail = response.json()
    print(f"✅ 会话详情:")
    print(f"   任务: {session_detail['task']}")
    print(f"   结果: {session_detail['outcome']}")
    print(f"   消息数: {len(session_detail['messages'])}")
    print()
    
    # 7. 从完整会话中学习
    print("7️⃣ 从完整会话中学习...")
    response = requests.post(f"{BASE_URL}/learn/session/{session_id}")
    result = response.json()
    print(f"✅ 学习结果:")
    print(f"   类型: {result.get('type', 'unknown')}")
    if result.get('skill_id'):
        print(f"   技能ID: {result['skill_id']}")
    if result.get('rule_id'):
        print(f"   规则ID: {result['rule_id']}")
    print()
    
    print("✅ API 示例完成！\n")
    print("💡 更多 API 文档: http://localhost:8000/docs")


if __name__ == "__main__":
    print("⚠️ 请确保 FastAPI 服务正在运行:")
    print("   python -m timem_evolve.api.main\n")
    
    try:
        example_api_usage()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 API 服务，请先启动服务:")
        print("   python -m timem_evolve.api.main")
    except Exception as e:
        print(f"❌ 错误: {e}")
