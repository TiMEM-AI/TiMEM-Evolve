"""
示例 3: Coach 模式 (Gym 模式) 完整演示

演示 Coach Agent 如何生成任务、运行任务并实现自我学习。
"""
import asyncio
import os
from timem_evolve.sdk.client import EvolveClient
from timem_evolve.models import CoachTaskCreate

# 假设 FastAPI 服务运行在 8000 端口
# os.environ["EVOLVE_API_URL"] = "http://127.0.0.1:8000"
client = EvolveClient()

async def coach_gym_demo():
    print("--- 示例 3: Coach 模式 (Gym 模式) 完整演示 ---")
    
    # 1. 获取 Coach 状态
    state = client.get_coach_state()
    print(f"当前 Coach 任务总数: {state.total_tasks}")

    # 2. 生成一个新任务
    business_goal = "提高 Agent 在技术文档总结方面的能力"
    task_create = CoachTaskCreate(
        business_goal=business_goal
    )
    
    print(f"\n-> 步骤 1: 生成新任务 (业务目标: {business_goal})")
    try:
        task = client.generate_coach_task(task_create)
        print(f"新任务生成成功: {task.task_id}")
        print(f"任务描述: {task.task_description}")
    except Exception as e:
        print(f"生成任务失败，请确保 LLM 配置正确: {e}")
        return

    # 3. 运行任务
    print(f"\n-> 步骤 2: 运行 Coach 任务 ({task.task_id})")
    try:
        updated_task = client.run_coach_task(task.task_id)
        
        print(f"\n--- 任务运行结果 ---")
        print(f"状态: {updated_task.status}")
        print(f"结果: {updated_task.outcome}")
        print(f"会话 ID: {updated_task.session_id}")
        print(f"Coach 反馈: {updated_task.coach_feedback[:100]}...")
        
        # 4. 检查学习结果
        if updated_task.outcome == "success" and updated_task.learned_skill_id:
            print(f"\n-> 步骤 3: 学习成功，提炼出技能 ID: {updated_task.learned_skill_id}")
            skill = client.list_skills(limit=1)[0]
            print(f"技能名称: {skill.name}")
            
        elif updated_task.outcome == "failure" and updated_task.learned_rule_id:
            print(f"\n-> 步骤 3: 学习失败，提炼出规则 ID: {updated_task.learned_rule_id}")
            rule = client.list_rules(limit=1)[0]
            print(f"规则名称: {rule.name}")
            
        else:
            print("\n-> 步骤 3: 任务完成，但未提炼出新的技能或规则。")
            
    except Exception as e:
        print(f"运行任务失败: {e}")
        
    # 5. 再次获取 Coach 状态
    final_state = client.get_coach_state()
    print(f"\n最终 Coach 任务总数: {final_state.total_tasks}")
    print(f"学习到的技能总数: {final_state.skills_gained}")
    print(f"学习到的规则总数: {final_state.rules_gained}")


if __name__ == "__main__":
    # 运行前请确保 FastAPI 服务已启动: python -m timem_evolve.api.main
    asyncio.run(coach_gym_demo())
