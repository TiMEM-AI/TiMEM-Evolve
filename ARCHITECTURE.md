# TiMEM-Evolve 系统架构设计

## 核心概念

### 时序记忆 (Temporal Memory)
- **会话管理**: 记录每个任务会话的完整上下文
- **时间感知**: 理解任务发生的时间模式和周期性

### 经验学习 (Experience Learning)
- **成功经验 → Skills**: 从成功案例中提炼可复用的工作流程 (SOP/Workflow)
- **失败经验 → Rules**: 从失败案例中提炼约束规则和注意事项

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Service Layer                   │
│  - POST /sessions/add        添加会话                       │
│  - POST /sessions/analyze    分析会话并学习                 │
│  - GET  /skills              查询技能                       │
│  - GET  /rules               查询规则                       │
│  - GET  /gradio              Gradio UI 界面                 │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Agent Core                      │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Session    │───▶│   Analyzer   │───▶│   Learner    │  │
│  │   Manager    │    │   (Reflect)  │    │  (Extract)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Memory Storage Layer                    │  │
│  │  - Sessions DB (SQLite)                              │  │
│  │  - Skills DB (JSON/Vector)                           │  │
│  │  - Rules DB (JSON/Vector)                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    LLM Provider Layer                        │
│  - OpenAI (gpt-4.1-mini, gpt-4.1-nano)                      │
│  - Gemini (gemini-2.5-flash)                                │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块设计

### 1. Session Manager (会话管理器)
```python
class SessionManager:
    def add_session(self, task: str, messages: List[Message], outcome: str) -> str
    def get_session(self, session_id: str) -> Session
    def list_sessions(self, filters: dict) -> List[Session]
```

### 2. Analyzer (分析器 - LangGraph)
```python
class AnalyzerGraph:
    # 使用 LangGraph 构建分析流程
    def analyze_session(self, session: Session) -> AnalysisResult
    
    # 节点:
    # - identify_task: 识别任务类型和目标
    # - evaluate_outcome: 评估任务成功/失败
    # - extract_insights: 提取关键洞察
    # - reflect: 反思和总结
```

### 3. Learner (学习器)
```python
class Learner:
    def extract_skill(self, successful_session: Session) -> Skill
    def extract_rule(self, failed_session: Session) -> Rule
    def store_skill(self, skill: Skill) -> None
    def store_rule(self, rule: Rule) -> None
```

### 4. Memory Storage (记忆存储)
```python
class MemoryStorage:
    # Sessions
    def save_session(self, session: Session) -> None
    def query_sessions(self, filters: dict) -> List[Session]
    
    # Skills
    def save_skill(self, skill: Skill) -> None
    def search_skills(self, query: str, top_k: int) -> List[Skill]
    
    # Rules
    def save_rule(self, rule: Rule) -> None
    def search_rules(self, query: str, top_k: int) -> List[Rule]
```

## 数据模型

### Session (会话)
```python
{
    "session_id": "uuid",
    "task": "用户任务描述",
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "outcome": "success" | "failure",
    "timestamp": "2025-11-24T10:00:00Z",
    "metadata": {}
}
```

### Skill (技能)
```python
{
    "skill_id": "uuid",
    "name": "技能名称",
    "description": "技能描述",
    "workflow": {
        "steps": ["步骤1", "步骤2", "步骤3"],
        "sop": "标准操作流程"
    },
    "source_sessions": ["session_id1", "session_id2"],
    "confidence": 0.85,
    "created_at": "2025-11-24T10:00:00Z",
    "metadata": {}
}
```

### Rule (规则)
```python
{
    "rule_id": "uuid",
    "name": "规则名称",
    "description": "规则描述",
    "constraint": "约束条件",
    "reason": "为什么需要这个规则",
    "source_sessions": ["session_id1"],
    "confidence": 0.90,
    "created_at": "2025-11-24T10:00:00Z",
    "metadata": {}
}
```

## 技术栈

- **LangGraph**: 构建智能体工作流
- **FastAPI**: REST API 服务
- **SQLite**: 会话数据存储
- **JSON**: 技能和规则存储
- **OpenAI API**: LLM 推理和反思
- **Gradio**: Web UI 界面
- **Pydantic**: 数据验证

## 目录结构

```
TiMEM-Evolve/
├── timem_evolve/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── session.py          # Session Manager
│   │   ├── analyzer.py         # LangGraph Analyzer
│   │   ├── learner.py          # Learner
│   │   └── storage.py          # Memory Storage
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py          # Session 数据模型
│   │   ├── skill.py            # Skill 数据模型
│   │   └── rule.py             # Rule 数据模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 主应用
│   │   └── routes.py           # API 路由
│   └── ui/
│       ├── __init__.py
│       └── gradio_app.py       # Gradio UI
├── examples/
│   ├── basic_usage.py
│   └── advanced_usage.py
├── tests/
│   └── ...
├── data/                        # 本地数据存储
│   ├── sessions.db
│   ├── skills.json
│   └── rules.json
├── requirements.txt
├── setup.py
├── README.md
└── ARCHITECTURE.md
```
