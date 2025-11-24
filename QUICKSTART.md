# 快速开始指南 (QUICKSTART)

本指南将帮助您快速启动 TiMEM-Evolve 框架，并了解其核心功能的使用方法。

## 1. 环境设置

### 1.1 克隆仓库

```bash
git clone https://github.com/TiMEM-AI/TiMEM-Evolve.git
cd TiMEM-Evolve
git checkout dev # 切换到最新开发分支
```

### 1.2 安装依赖

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1.3 配置环境变量

复制 `env.template` 文件，并将其命名为 `.env`。

```bash
cp env.template .env
```

**编辑 `.env` 文件**，配置您的 OpenAI API 密钥：

```ini
# .env
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
# 可选：配置 FastAPI 服务的 URL，用于 Gradio UI 和 SDK
EVOLVE_API_URL="http://127.0.0.1:8000"
```

## 2. 启动服务

### 2.1 启动 FastAPI 后端

这是核心服务，提供 RESTful API 和 MCP 接口。

```bash
python -m timem_evolve.api.main
```

服务启动后，您可以通过浏览器访问 `http://127.0.0.1:8000/docs` 查看 API 文档。

### 2.2 启动 Gradio UI (可选)

用于可视化监控和 Coach 模式操作。

```bash
python -m timem_evolve.ui.gradio_app
```

UI 启动后，您可以通过浏览器访问 `http://127.0.0.1:7860`。

## 3. 核心功能演示

### 3.1 经验学习 (Learning)

通过 SDK 演示如何添加会话和反馈，并触发学习。

```python
# examples/basic_usage.py 示例
import asyncio
from timem_evolve.sdk.client import EvolveClient
from timem_evolve.models import SessionCreate, Message, FeedbackCreate

client = EvolveClient()

async def demo_learning():
    # 1. 添加一个成功的会话
    session_create = SessionCreate(
        task="编写一个简单的 Python 函数",
        messages=[
            Message(role="user", content="请写一个计算斐波那契数列的函数。"),
            Message(role="assistant", content="```python\ndef fib(n):\n    ...\n```")
        ],
        outcome="success"
    )
    session = client.add_session(session_create)
    print(f"会话创建成功: {session.session_id}")

    # 2. 添加一个好评反馈，触发技能提炼
    feedback_create = FeedbackCreate(
        session_id=session.session_id,
        message_index=1, # 针对 AI 的回复
        rating="positive",
        comment="代码简洁高效，应该作为技能沉淀。"
    )
    feedback = client.add_feedback(feedback_create)
    print(f"反馈添加成功，学习结果 ID: {feedback.learned_skill_id}")
    
    # 3. 搜索技能
    skills = client.search_skills(query="斐波那契")
    print(f"搜索到的技能数量: {len(skills)}")
    if skills:
        print(f"搜索到的技能名称: {skills[0].name}")

if __name__ == "__main__":
    asyncio.run(demo_learning())
```

### 3.2 Coach 模块 (Gym 模式)

通过 Gradio UI 或 SDK 驱动 Agent 自我提升。

**通过 SDK 运行 Coach 任务:**

```python
# examples/coach_usage.py (假设您创建了这个文件)
import asyncio
from timem_evolve.sdk.client import EvolveClient
from timem_evolve.models import CoachTaskCreate

client = EvolveClient()

async def demo_coach():
    # 1. 获取 Coach 状态
    state = client.get_coach_state()
    print(f"当前 Coach 任务总数: {state.total_tasks}")

    # 2. 生成一个新任务
    task_create = CoachTaskCreate(
        business_goal="提高 Agent 在代码调试方面的准确率"
    )
    task = client.generate_coach_task(task_create)
    print(f"新任务生成成功: {task.task_id} - {task.task_description}")

    # 3. 运行任务
    print("开始运行 Coach 任务...")
    updated_task = client.run_coach_task(task.task_id)
    
    print(f"任务运行完成，结果: {updated_task.outcome}")
    print(f"学习到的技能 ID: {updated_task.learned_skill_id}")
    print(f"Coach 反馈: {updated_task.coach_feedback[:50]}...")

if __name__ == "__main__":
    asyncio.run(demo_coach())
```

### 3.3 LangChain 集成

请参考 `examples/langchain_integration.py` 文件，了解如何将 TiMEM-Evolve 的知识检索能力作为 LangChain Agent 的工具。

### 3.4 MCP 协议集成

如果您使用支持 MCP 协议的工具（如 Cursor），请参考 `docs/mcp_tutorial.md` 中的详细说明进行配置。

## 4. 核心概念

### 4.1 Session（会话）

记录一次完整的任务对话，包含：
- 任务描述
- 消息列表（用户和AI的对话）
- 结果（成功/失败）

### 4.2 Feedback（反馈）

对单轮对话的评价，包含：
- 好评/差评
- 反馈文本
- 自动触发学习

### 4.3 Coach（教练）

一个具有观测能力的 Agent，负责：
- **生成任务**：根据业务目标创建有益的学习任务。
- **评估结果**：监督 Learner Agent 执行任务，并提供反馈。
- **自我提升（Gym 模式）**：通过不断生成、执行、评估任务，实现 Learner Agent 的预训练和自我进化。

### 4.4 Skill（技能）

从成功经验中提炼的可复用能力：
- 技能名称和描述
- 执行步骤
- 标准操作流程（SOP）

### 4.5 Rule（规则）

从失败经验中提炼的约束：
- 规则名称和描述
- 约束条件
- 原因说明

## 5. 数据存储

所有数据存储在 `./data` 目录：

```
data/
├── sessions.db      # 会话数据（SQLite）
├── skills.json      # 技能数据
├── rules.json       # 规则数据
└── feedbacks.json   # 反馈数据
├── coach_tasks.json # Coach 任务数据
```

## 6. 下一步

- 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系统架构
- 查看 [examples/](examples/) 目录获取更多示例
- 访问 API 文档 `http://127.0.0.1:8000/docs` 了解所有接口
