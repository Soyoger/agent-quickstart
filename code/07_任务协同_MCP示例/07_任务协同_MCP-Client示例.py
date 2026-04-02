
import asyncio
import json
from openai import OpenAI
from fastmcp import Client
import config

# 系统提示词：指导模型如何使用出行助手工具
SYSTEM_PROMPT = """你是一个智能出行助手。
你的任务是根据用户的请求，按顺序执行以下操作：
1.  **日期转换**：如果用户提到了“今天”、“明天”或“后天”，请先使用 `get_date` 工具将其转换为具体的 YYYY-MM-DD 格式。
2.  **查询航班**：使用 `search_flights` 工具（配合转换后的具体日期）查找符合用户要求的航班。
3.  **分析和决策**：从查询结果中选择最合适的航班（例如，最便宜的）。
4.  **预订机票**：使用 `book_ticket` 工具为指定乘客预订选定的航班。
5.  **发送通知**：使用 `send_notification` 工具将预订成功的信息发送给用户。

请确保严格按照“日期转换->查询->预订->通知”的顺序执行任务，并清晰地向用户报告每一步的结果。
"""


async def chat_with_mcp(user_input: str):
    """与 MCP 服务器进行交互的客户端"""
    print(f"--- 任务开始: {user_input} ---")

    # 初始化 LLM 客户端
    llm_client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    # 连接到 MCP 服务器
    async with Client(f"http://127.0.0.1:9005/mcp") as mcp_client:
        # 获取 MCP 服务器提供的工具列表
        mcp_tools = await mcp_client.list_tools()
        print(f"--- 成功连接到 MCP，获取工具列表: {[tool.name for tool in mcp_tools]} ---")

        # 将 MCP 工具转换为 OpenAI 可用的格式
        llm_tools = []
        for tool in mcp_tools:
            llm_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            })

        # 初始化对话历史
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        # 任务循环
        for i in range(5):  # 最多执行 5 轮，防止无限循环
            print(f"\n--- 第 {i+1} 轮交互 ---")

            # 1. 调用 LLM 获取决策
            response = llm_client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3.2",
                messages=messages,
                tools=llm_tools,
                tool_choice="auto",
            )
            assistant_message = response.choices[0].message
            messages.append(assistant_message)

            # 2. 如果没有工具调用，任务结束
            if not assistant_message.tool_calls:
                print(f"\n--- 任务完成 ---")
                print(f"最终答复: {assistant_message.content}")
                break

            # 3. 执行工具调用
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                print(f"LLM 决策 -> 调用工具: {tool_name}, 参数: {arguments}")

                # 通过 MCP Client 执行工具
                tool_result = await mcp_client.call_tool(tool_name, arguments)
                print(f"工具执行结果: {tool_result.structured_content}")

                # 将工具执行结果添加回对话历史
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result.structured_content, ensure_ascii=False),
                    }
                )


if __name__ == "__main__":
    # 定义一个复杂的、需要多工具协作的任务
    user_query = "帮我查一下明天北京到上海的机票，并帮张三预订最便宜的那一班，订好后发通知。"
    asyncio.run(chat_with_mcp(user_query))
