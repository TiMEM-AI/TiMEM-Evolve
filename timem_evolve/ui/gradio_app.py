"""Gradio UI - 可视化查看学习到的技能和规则"""
import gradio as gr
from pathlib import Path
import json
from datetime import datetime


def load_skills(data_dir: str = "./data"):
    """加载技能"""
    skills_path = Path(data_dir) / "skills.json"
    if not skills_path.exists():
        return []
    return json.loads(skills_path.read_text())


def load_rules(data_dir: str = "./data"):
    """加载规则"""
    rules_path = Path(data_dir) / "rules.json"
    if not rules_path.exists():
        return []
    return json.loads(rules_path.read_text())


def format_skills_table(data_dir: str = "./data"):
    """格式化技能表格"""
    skills = load_skills(data_dir)
    
    if not skills:
        return "暂无技能"
    
    # 按置信度排序
    skills.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    rows = []
    for skill in skills:
        rows.append([
            skill.get("name", ""),
            skill.get("description", ""),
            f"{skill.get('confidence', 0):.2f}",
            skill.get("created_at", "")[:10]
        ])
    
    return rows


def format_rules_table(data_dir: str = "./data"):
    """格式化规则表格"""
    rules = load_rules(data_dir)
    
    if not rules:
        return "暂无规则"
    
    # 按置信度排序
    rules.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
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


def get_skill_detail(skill_name: str, data_dir: str = "./data"):
    """获取技能详情"""
    skills = load_skills(data_dir)
    
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


def get_rule_detail(rule_name: str, data_dir: str = "./data"):
    """获取规则详情"""
    rules = load_rules(data_dir)
    
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


def create_gradio_app(data_dir: str = "./data"):
    """创建 Gradio 应用"""
    
    with gr.Blocks(title="TiMEM-Evolve - 智能体进化监控") as app:
        gr.Markdown("""
        # 🧠 TiMEM-Evolve - 智能体进化监控
        
        查看智能体从经验中学习到的技能和规则
        """)
        
        with gr.Tabs():
            # 技能标签页
            with gr.Tab("✨ 技能 (Skills)"):
                gr.Markdown("### 从成功经验中提炼的可复用技能")
                
                skills_table = gr.Dataframe(
                    headers=["名称", "描述", "置信度", "创建时间"],
                    value=format_skills_table(data_dir),
                    interactive=False
                )
                
                refresh_skills_btn = gr.Button("🔄 刷新技能列表")
                refresh_skills_btn.click(
                    fn=lambda: format_skills_table(data_dir),
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
                    fn=lambda name: get_skill_detail(name, data_dir),
                    inputs=skill_name_input,
                    outputs=skill_detail_output
                )
            
            # 规则标签页
            with gr.Tab("⚠️ 规则 (Rules)"):
                gr.Markdown("### 从失败经验中提炼的约束规则")
                
                rules_table = gr.Dataframe(
                    headers=["名称", "描述", "约束条件", "置信度", "创建时间"],
                    value=format_rules_table(data_dir),
                    interactive=False
                )
                
                refresh_rules_btn = gr.Button("🔄 刷新规则列表")
                refresh_rules_btn.click(
                    fn=lambda: format_rules_table(data_dir),
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
                    fn=lambda name: get_rule_detail(name, data_dir),
                    inputs=rule_name_input,
                    outputs=rule_detail_output
                )
            
            # 统计标签页
            with gr.Tab("📊 统计 (Statistics)"):
                gr.Markdown("### 学习统计")
                
                def get_statistics(data_dir: str = "./data"):
                    skills = load_skills(data_dir)
                    rules = load_rules(data_dir)
                    
                    stats = f"""
                    - **技能总数**: {len(skills)}
                    - **规则总数**: {len(rules)}
                    - **平均技能置信度**: {sum(s.get('confidence', 0) for s in skills) / len(skills):.2f if skills else 0}
                    - **平均规则置信度**: {sum(r.get('confidence', 0) for r in rules) / len(rules):.2f if rules else 0}
                    """
                    return stats
                
                stats_output = gr.Markdown(value=get_statistics(data_dir))
                
                refresh_stats_btn = gr.Button("🔄 刷新统计")
                refresh_stats_btn.click(
                    fn=lambda: get_statistics(data_dir),
                    outputs=stats_output
                )
    
    return app


if __name__ == "__main__":
    app = create_gradio_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
