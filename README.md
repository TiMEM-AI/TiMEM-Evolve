# TiMEM-Evolve: Build Agents that EVOLVE Over Time

**TiMEM-Evolve** 是一个基于 LangGraph 的自进化智能体框架，旨在通过**时序记忆**和**经验学习**，构建能够随着时间推移而**自我提升**的智能体。

它提供了一套完整的机制，用于：
1.  **存储**有价值的会话（时序记忆）。
2.  **识别**会话中的成功和失败经验。
3.  **提炼**成功的经验为可复用的 **Skills (SOP/Workflow)**。
4.  **提炼**失败的经验为 **Rules (约束/规则)**。
5.  通过 **Coach 模块 (Gym 模式)** 实现 Agent 的**预训练**和**自我进化**。
6.  通过 **FastAPI** 和 **MCP 协议** 暴露服务，方便集成到任何应用或 IDE 中。

## 核心概念

| 概念 | 描述 | 学习机制 | 存储方式 |
| :--- | :--- | :--- | :--- |
| **Session (会话)** | 完整的任务执行记录，包含对话、任务描述和结果（成功/失败）。 | 时序记忆 | SQLite 数据库 |
| **Feedback (反馈)** | 对单轮对话的评价（好评/差评），可触发即时学习。 | 经验学习 | JSON 文件 |
| **Skill (技能)** | 从成功经验中提炼出的可复用标准操作流程 (SOP) 或工作流。 | 成功经验提炼 | JSON 文件 (未来 Qdrant) |
| **Rule (规则)** | 从失败经验中提炼出的约束条件，用于避免重复错误。 | 失败经验提炼 | JSON 文件 (未来 Qdrant) |
| **Coach (教练)** | 具有观测能力的 Agent，负责生成任务、评估结果，驱动 Agent 在 **Gym 模式**下自我提升。 | 自我进化 | JSON 文件 |

## 架构分层

项目采用清晰的分层架构，便于维护和扩展：

| 分层 | 模块 | 职责 |
| :--- | :--- | :--- |
| **API** | `api/main.py`, `api/mcp_server.py` | 暴露 RESTful 和 MCP 接口，处理外部请求。 |
| **SDK** | `sdk/client.py` | Python 客户端封装，简化接口调用。 |
| **Services** | `services/*.py` | 核心业务逻辑，如会话管理、学习逻辑、Coach 流程。 |
| **DAO** | `dao/memory_dao.py` | 数据访问层，负责与 SQLite/JSON 文件（未来 Qdrant）的交互。 |
| **Models** | `models/*.py` | Pydantic 数据模型定义 (Schema)。 |
| **Prompt** | `prompt/` | 存储 LLM 提示词模板（待实现 YAML 格式）。 |

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/TiMEM-AI/TiMEM-Evolve.git
cd TiMEM-Evolve
git checkout dev # 切换到最新开发分支
```

### 2. 环境准备

推荐使用虚拟环境。

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置

复制 `env.template` 为 `.env` 并配置您的 `OPENAI_API_KEY`。

```bash
cp env.template .env
# 编辑 .env 文件
```

### 4. 启动服务

启动 FastAPI 后端服务：

```bash
python -m timem_evolve.api.main
```

服务将在 `http://127.0.0.1:8000` 启动。

### 5. 使用

#### 方式一：Python SDK

使用封装好的 `EvolveClient` 简化接口调用。

```python
from timem_evolve.sdk.client import EvolveClient
from timem_evolve.models import SessionCreate, Message

client = EvolveClient()

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

# 2. 从会话中学习（提炼技能）
learned_id = client.learn_from_session(session.session_id)
print(f"学习结果 ID: {learned_id}")

# 3. 搜索技能
skills = client.search_skills(query="斐波那契")
print(f"搜索到的技能数量: {len(skills)}")
```

#### 方式二：Gradio UI (监控和 Gym 模式)

启动 Gradio UI 进行可视化监控和 Coach 模式操作：

```bash
python -m timem_evolve.ui.gradio_app
```

UI 将在 `http://127.0.0.1:7860` 启动。

#### 方式三：LangChain 集成

请参考 `examples/langchain_integration.py` 文件，了解如何将 TiMEM-Evolve 的知识检索能力集成到 LangChain Agent 中。

## 6. 进阶功能

### 6.1 Coach 模块 (Gym 模式)

Coach 模块允许 Agent 在一个受控的“训练场”中进行自我提升。

**操作流程:**
1.  **生成任务**: 通过 Gradio UI 或 API 调用 `/coach/generate_task`，Coach Agent 根据业务目标生成一个具体的学习任务。
2.  **运行任务**: 调用 `/coach/run_task/{task_id}`，Learner Agent 模拟执行任务。
3.  **评估学习**: Coach Agent 评估任务结果，并触发 Learner Agent 从成功或失败的会话中提炼技能或规则。

### 6.2 MCP 协议集成

TiMEM-Evolve 提供了符合 **Model Context Protocol (MCP)** 的接口，允许外部工具（如 Cursor）调用 Agent 的进化能力。

**接口地址**: `http://127.0.0.1:8000/mcp/tool_call`

**工具名称**: `evolve_agent`

**关键函数**:
*   `feedback_turn`: 对单轮对话进行反馈，触发学习。
*   `search_knowledge`: 搜索已学习的技能或规则。

详细配置和使用教程请参考 `docs/mcp_tutorial.md`。

## 贡献

欢迎提交 Pull Request 到 `dev` 分支。

## 许可证

[待定]
