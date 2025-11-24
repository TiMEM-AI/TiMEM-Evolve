"""
LangChain 集成示例：
将 TiMEM-Evolve 的知识检索功能集成到 LangChain Agent 中。
"""
import os
import asyncio
from typing import List, Dict, Any

# 确保环境变量设置了 OpenAI API Key
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

# 假设 FastAPI 服务运行在 8000 端口
# os.environ["EVOLVE_API_URL"] = "http://127.0.0.1:8000"

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 导入 SDK
from timem_evolve.sdk.client import EvolveClient

# 初始化 SDK 客户端
evolve_client = EvolveClient()


@tool
def search_evolve_knowledge(query: str, knowledge_type: str = "skill") -> str:
    """
    搜索 TiMEM-Evolve 知识库中的技能或规则。
    
    Args:
        query: 搜索关键词。
        knowledge_type: 知识类型，'skill' 或 'rule'。
        
    Returns:
        匹配到的技能或规则的 JSON 字符串列表。
    """
    if knowledge_type not in ["skill", "rule"]:
        return "Error: knowledge_type must be 'skill' or 'rule'."
        
    try:
        if knowledge_type == "skill":
            results = evolve_client.search_skills(query=query, top_k=3)
        else:
            results = evolve_client.search_rules(query=query, top_k=3)
            
        # 格式化结果
        formatted_results = []
        for item in results:
            if knowledge_type == "skill":
                formatted_results.append({
                    "name": item.name,
                    "description": item.description,
                    "sop": item.workflow.sop,
                    "confidence": item.confidence
                })
            else:
                formatted_results.append({
                    "name": item.name,
                    "description": item.description,
                    "constraint": item.constraint,
                    "reason": item.reason,
                    "confidence": item.confidence
                })
                
        return f"Found {len(formatted_results)} {knowledge_type}s:\n{formatted_results}"
        
    except Exception as e:
        return f"Error searching knowledge: {e}"


def create_evolve_agent():
    """创建集成 TiMEM-Evolve 知识库的 LangChain Agent"""
    
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    
    tools = [search_evolve_knowledge]
    
    # 提示词
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个经验丰富的智能体，你可以使用 'search_evolve_knowledge' 工具来检索你过去学习到的技能和规则，以更好地完成任务。"
                "当你需要参考过去的经验或约束时，请使用该工具。"
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    
    # 创建 Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 创建 Agent Executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor


async def main():
    """主函数"""
    print("--- 启动 TiMEM-Evolve LangChain Agent 示例 ---")
    
    # 确保后端服务已运行
    try:
        evolve_client.list_skills(limit=1)
        print(f"后端服务连接成功: {evolve_client.base_url}")
    except Exception as e:
        print(f"警告: 无法连接到后端服务 ({evolve_client.base_url})。请确保 FastAPI 服务已启动。")
        print(f"错误信息: {e}")
        return

    agent = create_evolve_agent()
    
    # 示例 1: 提问一个可能需要技能的问题
    print("\n--- 示例 1: 搜索技能 ---")
    result1 = await agent.ainvoke({"input": "我需要一个关于如何清晰地解释复杂代码的技巧，你能帮我搜索一下吗？", "chat_history": []})
    print(f"Agent 回复: {result1['output']}")
    
    # 示例 2: 提问一个可能需要规则的问题
    print("\n--- 示例 2: 搜索规则 ---")
    result2 = await agent.ainvoke({"input": "我应该注意什么，才能避免在解释技术概念时犯错？请搜索一下规则。", "chat_history": []})
    print(f"Agent 回复: {result2['output']}")
    
    # 示例 3: 一个普通问题
    print("\n--- 示例 3: 普通问题 ---")
    result3 = await agent.ainvoke({"input": "什么是快速排序？", "chat_history": []})
    print(f"Agent 回复: {result3['output']}")


if __name__ == "__main__":
    # 运行 FastAPI 服务后，再运行此文件
    # 1. 启动 FastAPI: python -m timem_evolve.api.main
    # 2. 运行此示例: python examples/langchain_integration.py
    asyncio.run(main())
