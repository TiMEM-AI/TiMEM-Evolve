# MCP 协议接口教程

TiMEM-Evolve 框架提供了一个符合 **Model Context Protocol (MCP)** 的接口，允许外部工具（如 Cursor、IDE 插件等）调用 Agent 的进化能力，实现经验的沉淀和知识的检索。

## 1. 接口概览

MCP 接口通过 FastAPI 暴露，路径为 `/mcp/tool_call`。

**工具名称 (Tool Name):** `evolve_agent`

**可用函数 (Functions):**

| 函数名 | 描述 | 用途 |
| :--- | :--- | :--- |
| `feedback_turn` | 对单轮对话进行反馈并触发学习 | 沉淀经验（技能/规则） |
| `search_knowledge` | 搜索已学习的技能或规则 | 知识检索 |

## 2. 配置和调用

### 2.1 启动后端服务

首先，确保 TiMEM-Evolve 的 FastAPI 服务正在运行：

```bash
# 确保在项目根目录
python -m timem_evolve.api.main
```

服务默认运行在 `http://127.0.0.1:8000`。

### 2.2 `feedback_turn` 函数

该函数用于将用户对 Agent 回复的反馈（好评/差评）转化为学习经验。

**函数签名:**

```json
{
  "session_id": "string",
  "message_index": "integer",
  "rating": "string (positive/negative)",
  "comment": "string (optional)"
}
```

**示例调用 (使用 `curl`):**

假设有一个会话 ID 为 `abc-123`，用户对第 5 条消息（AI回复）给出了好评：

```bash
curl -X POST "http://127.0.0.1:8000/mcp/tool_call" \
-H "Content-Type: application/json" \
-d '{
  "tool_name": "evolve_agent",
  "function_name": "feedback_turn",
  "arguments": {
    "session_id": "abc-123",
    "message_index": 5,
    "rating": "positive",
    "comment": "这个解释非常清晰，步骤很明确，应该作为技能沉淀下来。"
  }
}'
```

**响应示例 (成功):**

```json
{
  "status": "success",
  "result": {
    "feedback_id": "...",
    "learned": true,
    "learned_skill_id": "...",
    "learned_rule_id": null
  }
}
```

### 2.3 `search_knowledge` 函数

该函数用于检索 Agent 已经学习到的技能或规则，供 Agent 在执行任务时参考。

**函数签名:**

```json
{
  "query": "string",
  "knowledge_type": "string (skill/rule)",
  "top_k": "integer (optional, default 5)"
}
```

**示例调用 (搜索技能):**

```bash
curl -X POST "http://127.0.0.1:8000/mcp/tool_call" \
-H "Content-Type: application/json" \
-d '{
  "tool_name": "evolve_agent",
  "function_name": "search_knowledge",
  "arguments": {
    "query": "如何清晰地解释代码",
    "knowledge_type": "skill",
    "top_k": 3
  }
}'
```

**响应示例 (成功):**

返回匹配到的技能或规则的 JSON 列表。

```json
{
  "status": "success",
  "result": [
    {
      "skill_id": "...",
      "name": "清晰的代码解释",
      "description": "...",
      "workflow": { ... },
      "confidence": 0.9
    }
    // ... 其他结果
  ]
}
```

## 3. 与外部工具集成

对于支持 MCP 协议的工具（如 Cursor），您通常需要在工具的设置中配置 TiMEM-Evolve 的 API 地址和工具定义。

**工具定义 (Tool Definition):**

您可以使用以下 JSON Schema 来定义 `evolve_agent` 工具：

```json
{
  "tool_name": "evolve_agent",
  "description": "用于管理和检索 Agent 学习到的技能和规则，实现自我进化。",
  "functions": [
    {
      "name": "feedback_turn",
      "description": "对单轮对话进行反馈并触发学习，用于沉淀经验。",
      "parameters": {
        "type": "object",
        "properties": {
          "session_id": {"type": "string", "description": "会话ID"},
          "message_index": {"type": "integer", "description": "消息索引（AI回复）"},
          "rating": {"type": "string", "enum": ["positive", "negative"], "description": "评价：positive 或 negative"},
          "comment": {"type": "string", "description": "反馈文本（可选）"}
        },
        "required": ["session_id", "message_index", "rating"]
      }
    },
    {
      "name": "search_knowledge",
      "description": "搜索已学习的技能或规则，供 Agent 在执行任务时参考。",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "查询关键词"},
          "knowledge_type": {"type": "string", "enum": ["skill", "rule"], "description": "知识类型：skill 或 rule"},
          "top_k": {"type": "integer", "description": "返回数量（可选，默认 5）"}
        },
        "required": ["query", "knowledge_type"]
      }
    }
  ]
}
```

将此定义和您的 TiMEM-Evolve API 地址配置到您的 IDE 或工具中，即可开始使用 Agent 的进化能力。
