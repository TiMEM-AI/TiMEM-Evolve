# TiMEM-Evolve: Build Agents that EVOLVE Over Time

<!-- 保持原有风格和核心信息，并融入新功能介绍 -->

[![GitHub Stars](https://img.shields.io/github/stars/TiMEM-AI/TiMEM-Evolve?style=social)](https://github.com/TiMEM-AI/TiMEM-Evolve)
[![GitHub Forks](https://img.shields.io/github/forks/TiMEM-AI/TiMEM-Evolve?style=social)](https://github.com/TiMEM-AI/TiMEM-Evolve/fork)
[![License](https://img.shields.io/github/license/TiMEM-AI/TiMEM-Evolve)](LICENSE)

**TiMEM-Evolve** 是一个基于 LangGraph 的自进化智能体框架，旨在通过**时序记忆**和**经验学习**，构建能够随着时间推移而**自我提升**的认知引擎。

> **核心理念:** 记忆驱动，随时间演化，自我提升的认知引擎。

## 核心进化机制

TiMEM-Evolve 提供了以下核心机制，驱动 Agent 的持续进化：

| 机制 | 描述 | 学习来源 | 产出物 |
| :--- | :--- | :--- | :--- |
| **时序记忆 (Session)** | 记录完整的任务执行过程和对话，作为 Agent 的“记忆”。 | 任务会话 | 会话记录 (SQLite) |
| **经验学习 (Feedback)** | 通过用户对单轮对话的**好评/差评**，触发即时反思和学习。 | 用户反馈 | Skills 或 Rules |
| **技能提炼 (Skill)** | 从**成功经验**中提炼出可复用的**标准操作流程 (SOP)** 或**工作流**。 | 正面反馈/成功会话 | 可复用技能 |
| **规则学习 (Rule)** | 从**失败经验**中提炼出**约束条件**和**行为规则**，避免重复犯错。 | 负面反馈/失败会话 | 行为约束 |
| **教练模式 (Coach/Gym)** | 具有观测能力的 Coach Agent 驱动 Learner Agent 在受控环境中**预训练**和**自我进化**。 | 模拟任务 | 主动提升 |

## 架构与集成

项目采用清晰的 **API/Services/DAO** 分层架构，并提供多种集成方式：

### 1. 架构分层

| 分层 | 模块 | 职责 |
| :--- | :--- | :--- |
| **API** | `api/main.py` | 暴露 **RESTful API** 和 **MCP 协议接口**。 |
| **SDK** | `sdk/client.py` | Python 客户端封装，简化接口调用。 |
| **Services** | `services/*.py` | 核心业务逻辑，如会话管理、学习逻辑、Coach 流程。 |
| **DAO** | `dao/memory_dao.py` | 数据访问层，负责与 SQLite/JSON 文件（未来支持 Qdrant）的交互。 |

### 2. 接口与集成

*   **FastAPI RESTful API**: 提供 `/sessions`, `/skills`, `/rules`, `/coach` 等标准接口，方便任何应用集成。
*   **Gradio UI**: 提供可视化界面，用于监控 Agent 运行状态、学习效果和 Coach 模式操作。
*   **MCP 协议**: 专为开发工具（如 **Cursor**）设计，通过 `evolve_agent` 工具的 `feedback_turn` 和 `search_knowledge` 函数，实现经验的沉淀和知识的检索。
*   **LangChain 集成**: 提供了示例，展示如何将 TiMEM-Evolve 的知识检索能力作为 LangChain Agent 的工具。

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/TiMEM-AI/TiMEM-Evolve.git
cd TiMEM-Evolve
# main 分支已包含最新代码
```

### 2. 环境准备

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置与启动

复制 `env.template` 为 `.env` 并配置您的 `OPENAI_API_KEY`。

```bash
cp env.template .env
# 编辑 .env 文件

# 启动 FastAPI 后端服务
python -m timem_evolve.api.main
```

### 4. 运行示例

查看 `examples/` 目录下的示例，了解如何使用 **SDK**、**LangChain**，以及如何演示 **Skill/Rule 提炼**和 **Coach 模式**。

```bash
# 运行 Coach 模式演示
python examples/coach_gym_demo.py
```

## 贡献

欢迎提交 Pull Request 到 `dev` 分支。

## 许可证

[待定]
