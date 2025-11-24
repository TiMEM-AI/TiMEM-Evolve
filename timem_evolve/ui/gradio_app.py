"""Gradio UI - 可视化查看学习到的技能和规则"""
import gradio as gr
import requests
import os
from typing import List, Dict, Any, Optional

# 假设 FastAPI 服务运行在 8000 端口
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


def fetch_data(endpoint: str) -> Optional[List[Dict[str, Any]]]:
    """从 FastAPI 后端获取数据"""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return None


def format_skills_table() -> List[List[Any]]:
    """格式化技能表格"""
    skills = fetch_data("skills")
    
    if not skills:
        return [["暂无技能", "", "", ""]]
    
    rows = []
    for skill in skills:
        rows.append([
            skill.get("name", ""),
            skill.get("description", ""),
            f"{skill.get('confidence', 0):.2f}",
            skill.get("created_at", "")[:10]
        ])
    
    return rows


def format_rules_table() -> List[List[Any]]:
    """格式化规则表格"""
    rules = fetch_data("rules")
    
    if not rules:
        return [["暂无规则", "", "", "", ""]]
    
    rows = []
    for rule in rules:
        rows.append([
            rule.get("name", ""),
            rule.get("description", ""),
            rule.get("constraint", ""),
            f"{rule.get('confidence', 0):.2f}",
            rule.get("created_at", "")[:10]
        ])
    
    return rows


def get_skill_detail(skill_name: str) -> str:
    """获取技能详情"""
    skills = fetch_data("skills")
    
    if not skills:
        return "未找到技能详情"
        
    for skill in skills:
        if skill.get("name") == skill_name:
            workflow = skill.get("workflow", {})
            steps = workflow.get("steps", [])
            sop = workflow.get("sop", "")
            
            detail = f"""
## {skill.get("name")}

**描述**: {skill.get("description")}

**置信度**: {skill.get("confidence", 0):.2f}

**创建时间**: {skill.get("created_at", "")}

### 执行步骤

{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(steps))}

### 标准操作流程 (SOP)

{sop}

### 元数据

- 来源会话: {', '.join(skill.get("source_sessions", []))}
- 技能ID: {skill.get("skill_id", "")}
"""
            return detail
    
    return "未找到技能详情"


def get_rule_detail(rule_name: str) -> str:
    """获取规则详情"""
    rules = fetch_data("rules")
    
    if not rules:
        return "未找到规则详情"
        
    for rule in rules:
        if rule.get("name") == rule_name:
            detail = f"""
## {rule.get("name")}

**描述**: {rule.get("description")}

**置信度**: {rule.get("confidence", 0):.2f}

**创建时间**: {rule.get("created_at", "")}

### 约束条件

{rule.get("constraint", "")}

### 原因说明

{rule.get("reason", "")}

### 元数据

- 来源会话: {', '.join(rule.get("source_sessions", []))}
- 规则ID: {rule.get("rule_id", "")}
"""
            return detail
    
    return "未找到规则详情"


def get_statistics() -> str:
    """获取统计信息"""
    skills = fetch_data("skills")
    rules = fetch_data("rules")
    feedbacks = fetch_data("feedbacks")
    sessions = fetch_data("sessions")
    coach_state = fetch_data("coach/state")
    
    num_skills = len(skills) if skills else 0
    num_rules = len(rules) if rules else 0
    num_feedbacks = len(feedbacks) if feedbacks else 0
    num_sessions = len(sessions) if sessions else 0
    
    avg_skill_confidence = sum(s.get('confidence', 0) for s in skills) / num_skills if num_skills else 0
    avg_rule_confidence = sum(r.get('confidence', 0) for r in rules) / num_rules if num_rules else 0
    
    coach_stats = ""
    if coach_state:
        coach_stats = f"""
### Coach 模块 (Gym 模式) 统计
- **总任务数**: {coach_state.get('total_tasks', 0)}
- **已完成任务**: {coach_state.get('completed_tasks', 0)}
- **成功任务**: {coach_state.get('successful_tasks', 0)}
- **失败任务**: {coach_state.get('failed_tasks', 0)}
- **通过 Coach 学习的技能**: {coach_state.get('skills_gained', 0)}
- **通过 Coach 学习的规则**: {coach_state.get('rules_gained', 0)}
"""
    
    stats = f"""
### 基础学习统计
- **会话总数**: {num_sessions}
- **反馈总数**: {num_feedbacks}
- **技能总数**: {num_skills}
- **规则总数**: {num_rules}
- **平均技能置信度**: {avg_skill_confidence:.2f}
- **平均规则置信度**: {avg_rule_confidence:.2f}

---
{coach_stats}
"""
    return stats


def create_gradio_app():
    """创建 Gradio 应用"""
    
    with gr.Blocks(title="TiMEM-Evolve - 智能体进化监控") as app:
        gr.Markdown(f"""
        # 🧠 TiMEM-Evolve - 智能体进化监控
        
        查看智能体从经验中学习到的技能和规则。
        **FastAPI 后端**: {API_BASE_URL}
        """)
        
        with gr.Tabs():
            # 统计标签页 (放在前面方便监控)
            with gr.Tab("📊 统计 (Statistics)"):
                gr.Markdown("### 学习统计")
                
                stats_output = gr.Markdown(value=get_statistics())
                
                refresh_stats_btn = gr.Button("🔄 刷新统计")
                refresh_stats_btn.click(
                    fn=get_statistics,
                    outputs=stats_output
                )
            
            # Coach 标签页
            with gr.Tab("🏋️ Coach (Gym Mode)"):
                gr.Markdown("### Coach Agent 任务管理")
                
                with gr.Row():
                    business_goal_input = gr.Textbox(
                        label="业务目标",
                        placeholder="例如：提高代码调试的准确率"
                    )
                    generate_task_btn = gr.Button("🚀 生成新任务")
                
                task_output = gr.Markdown(label="最新生成的任务")
                
                def generate_task_action(goal: str):
                    if not goal:
                        return "请输入业务目标"
                    try:
                        response = requests.post(f"{API_BASE_URL}/coach/generate_task", json={"business_goal": goal, "task_description": "待生成"})
                        response.raise_for_status()
                        task = response.json()
                        return f"""
**任务ID**: {task['task_id']}
**业务目标**: {task['business_goal']}
**任务描述**: {task['task_description']}
**难度**: {task['difficulty']}
**状态**: {task['status']}
"""
                    except requests.exceptions.RequestException as e:
                        return f"生成任务失败: {e}"
                
                generate_task_btn.click(
                    fn=generate_task_action,
                    inputs=business_goal_input,
                    outputs=task_output
                )
                
                gr.Markdown("---")
                gr.Markdown("### 任务列表")
                
                task_status_dropdown = gr.Dropdown(
                    choices=["pending", "running", "completed", "failed", "all"],
                    value="all",
                    label="筛选状态"
                )
                
                tasks_table = gr.Dataframe(
                    headers=["ID", "业务目标", "任务描述", "难度", "状态", "结果"],
                    interactive=False
                )
                
                def format_tasks_table(status: str):
                    endpoint = "coach/tasks"
                    if status != "all":
                        endpoint += f"?status={status}"
                    
                    tasks = fetch_data(endpoint)
                    
                    if not tasks:
                        return [["暂无任务", "", "", "", "", ""]]
                    
                    rows = []
                    for task in tasks:
                        rows.append([
                            task.get("task_id", "")[:8] + "...",
                            task.get("business_goal", ""),
                            task.get("task_description", "")[:50] + "...",
                            task.get("difficulty", ""),
                            task.get("status", ""),
                            task.get("outcome", "N/A")
                        ])
                    return rows
                
                tasks_table.value = format_tasks_table("all")
                
                refresh_tasks_btn = gr.Button("🔄 刷新任务列表")
                
                refresh_tasks_btn.click(
                    fn=format_tasks_table,
                    inputs=task_status_dropdown,
                    outputs=tasks_table
                )
                
                task_status_dropdown.change(
                    fn=format_tasks_table,
                    inputs=task_status_dropdown,
                    outputs=tasks_table
                )
                
                gr.Markdown("---")
                gr.Markdown("### 运行任务")
                
                with gr.Row():
                    run_task_id_input = gr.Textbox(
                        label="输入任务ID",
                        placeholder="输入要运行的任务ID"
                    )
                    run_task_btn = gr.Button("▶️ 运行任务")
                
                run_task_output = gr.Markdown(label="运行结果")
                
                def run_task_action(task_id: str):
                    if not task_id:
                        return "请输入任务ID"
                    try:
                        response = requests.post(f"{API_BASE_URL}/coach/run_task/{task_id}")
                        response.raise_for_status()
                        task = response.json()
                        
                        feedback = task.get('coach_feedback', '无反馈')
                        
                        return f"""
**任务ID**: {task['task_id']}
**状态**: {task['status']}
**结果**: {task['outcome']}
**学习结果**: 
- 技能ID: {task.get('learned_skill_id', 'N/A')}
- 规则ID: {task.get('learned_rule_id', 'N/A')}

---
**Coach 反馈**:
{feedback}
"""
                    except requests.exceptions.HTTPError as e:
                        return f"运行任务失败: {e.response.json().get('detail', str(e))}"
                    except requests.exceptions.RequestException as e:
                        return f"运行任务失败: {e}"
                
                run_task_btn.click(
                    fn=run_task_action,
                    inputs=run_task_id_input,
                    outputs=run_task_output
                )
            
            # 技能标签页
            with gr.Tab("✨ 技能 (Skills)"):
                gr.Markdown("### 从成功经验中提炼的可复用技能")
                
                skills_table = gr.Dataframe(
                    headers=["名称", "描述", "置信度", "创建时间"],
                    value=format_skills_table(),
                    interactive=False
                )
                
                refresh_skills_btn = gr.Button("🔄 刷新技能列表")
                refresh_skills_btn.click(
                    fn=format_skills_table,
                    outputs=skills_table
                )
                
                gr.Markdown("---")
                gr.Markdown("### 技能详情")
                
                skill_name_input = gr.Textbox(
                    label="输入技能名称查看详情",
                    placeholder="例如：清晰的代码解释"
                )
                skill_detail_output = gr.Markdown()
                
                skill_name_input.change(
                    fn=get_skill_detail,
                    inputs=skill_name_input,
                    outputs=skill_detail_output
                )
            
            # 规则标签页
            with gr.Tab("⚠️ 规则 (Rules)"):
                gr.Markdown("### 从失败经验中提炼的约束规则")
                
                rules_table = gr.Dataframe(
                    headers=["名称", "描述", "约束条件", "置信度", "创建时间"],
                    value=format_rules_table(),
                    interactive=False
                )
                
                refresh_rules_btn = gr.Button("🔄 刷新规则列表")
                refresh_rules_btn.click(
                    fn=format_rules_table,
                    outputs=rules_table
                )
                
                gr.Markdown("---")
                gr.Markdown("### 规则详情")
                
                rule_name_input = gr.Textbox(
                    label="输入规则名称查看详情",
                    placeholder="例如：避免过于技术化的解释"
                )
                rule_detail_output = gr.Markdown()
                
                rule_name_input.change(
                    fn=get_rule_detail,
                    inputs=rule_name_input,
                    outputs=rule_detail_output
                )
    
    return app


if __name__ == "__main__":
    app = create_gradio_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
