# 快速开始 - TiMEM-Evolve

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/TiMEM-AI/TiMEM-Evolve.git
cd TiMEM-Evolve
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或者安装为包：

```bash
pip install -e .
```

### 3. 配置环境变量

复制 `env.template` 为 `.env` 文件，并配置 OpenAI API Key：

```bash
cp env.template .env
# 编辑 .env 文件，填入你的 OPENAI_API_KEY
```

```bash
OPENAI_API_KEY=your_api_key_here
```

## 基础使用

### 方式一：Python 代码

```python
import asyncio
from timem_evolve import (
    MemoryStorage,
    SessionManager,
    Learner,
    SessionCreate,
    Message
)

async def main():
    # 初始化
    storage = MemoryStorage(data_dir="./data")
    await storage.init_db()
    
    session_manager = SessionManager(storage)
    learner = Learner(storage)
    
    # 添加会话
    session = await session_manager.add_session(
        SessionCreate(
            task="帮助用户理解概念",
            messages=[
                Message(role="user", content="什么是装饰器？"),
                Message(role="assistant", content="装饰器是...")
            ],
            outcome="success"
        )
    )
    
    # 从会话中学习
    skill = await learner.extract_skill_from_session(session)
    print(f"学到技能: {skill.name}")

asyncio.run(main())
```

### 方式二：FastAPI 服务

#### 启动服务

```bash
python -m timem_evolve.api.main
```

或者使用 uvicorn：

```bash
uvicorn timem_evolve.api.main:app --reload
```

服务将在 `http://localhost:8000` 启动。

#### API 文档

访问 `http://localhost:8000/docs` 查看交互式 API 文档。

**MCP 接口**: 专为开发工具（如 Cursor）设计的接口，用于沉淀经验。
- **URL**: `http://localhost:8000/mcp/tool_call`
- **工具名称**: `evolve_agent`
- **函数**:
    - `feedback_turn`: 对单轮对话进行反馈并触发学习。
    - `search_knowledge`: 搜索已学习的技能或规则。

#### 使用 API

```python
import requests

# 创建会话
response = requests.post("http://localhost:8000/sessions", json={
    "task": "帮助用户调试代码",
    "messages": [
        {"role": "user", "content": "我的代码报错了"},
        {"role": "assistant", "content": "让我帮你看看..."}
    ],
    "outcome": "success"
})

session = response.json()
session_id = session["session_id"]

# 添加反馈
requests.post("http://localhost:8000/feedbacks", json={
    "session_id": session_id,
    "message_index": 1,
    "rating": "positive",
    "comment": "解决了我的问题"
})

# 查询技能
skills = requests.get("http://localhost:8000/skills").json()
print(f"共有 {len(skills)} 个技能")
```

### 方式三：Gradio UI

#### 启动 UI

```bash
python -m timem_evolve.ui.gradio_app
```

UI 将在 `http://localhost:7860` 启动。

#### 功能

- **技能标签页**：查看从成功经验中学到的技能
- **规则标签页**：查看从失败经验中学到的规则
- **统计标签页**：查看学习统计信息

## 核心概念

### 1. Session（会话）

记录一次完整的任务对话，包含：
- 任务描述
- 消息列表（用户和AI的对话）
- 结果（成功/失败）

### 2. Feedback（反馈）

对单轮对话的评价，包含：
- 好评/差评
- 反馈文本
- 自动触发学习

### 3. Skill（技能）

从成功经验中提炼的可复用能力：
- 技能名称和描述
- 执行步骤
- 标准操作流程（SOP）

### 4. Rule（规则）

从失败经验中提炼的约束：
- 规则名称和描述
- 约束条件
- 原因说明

## 工作流程

```
1. 添加会话 (Session)
   ↓
2. 添加反馈 (Feedback) - 对单轮对话评价
   ↓
3. 自动学习
   ├─ 好评 → 提炼技能 (Skill)
   └─ 差评 → 提炼规则 (Rule)
   ↓
4. 存储到本地
   ├─ sessions.db (SQLite)
   ├─ skills.json
   ├─ rules.json
   └─ feedbacks.json
   ↓
5. 查询和应用
   ├─ 搜索相关技能
   └─ 搜索相关规则
```

## 示例

### 运行基础示例

```bash
python examples/basic_usage.py
```

### 运行 API 示例

```bash
# 终端1：启动服务
python -m timem_evolve.api.main

# 终端2：运行示例
python examples/api_usage.py
```

## 数据存储

所有数据存储在 `./data` 目录：

```
data/
├── sessions.db      # 会话数据（SQLite）
├── skills.json      # 技能数据
├── rules.json       # 规则数据
└── feedbacks.json   # 反馈数据
```

## 下一步

- 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系统架构
- 查看 [examples/](examples/) 目录获取更多示例
- 访问 API 文档 `http://localhost:8000/docs` 了解所有接口

## 常见问题

### Q: 如何更换 LLM 提供商？

A: 修改 `Learner` 和 `AnalyzerGraph` 的初始化参数：

```python
learner = Learner(storage, model_name="gpt-4.1-nano")  # 或其他模型
```

### Q: 如何清空学习数据？

A: 删除 `./data` 目录下的文件：

```bash
rm -rf ./data/*
```

### Q: 如何部署到生产环境？

A: 使用 Docker 或直接部署 FastAPI 服务：

```bash
uvicorn timem_evolve.api.main:app --host 0.0.0.0 --port 8000
```

## 支持

- GitHub Issues: https://github.com/TiMEM-AI/TiMEM-Evolve/issues
- Discord: https://discord.gg/timem
- Twitter: [@timem_ai](https://x.com/timem_ai)
