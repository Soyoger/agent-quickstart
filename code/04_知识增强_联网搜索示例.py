import json
from openai import OpenAI
from config import base_url, api_key

# 1. 初始化客户端
client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

def web_search(query: str) -> str:
    """
    标准的联网搜索工具（模拟实现）。
    在实际生产环境中，这里通常会调用 Google Search, Bing Search, Tavily 或 Serper 等 API。
    
    Args:
        query: 需要搜索的关键词。
    Returns:
        JSON 格式的搜索结果字符串。
    """
    print(f"  [系统日志] 正在执行联网搜索: {query}")
    
    # 模拟搜索结果库
    mock_results = {
        "deepseek-v3": "DeepSeek-V3 是由深度求索（DeepSeek）公司开发的最新一代大语言模型。它在多项基准测试中表现优异，尤其是在推理和数学能力方面，其训练效率和成本控制也处于行业领先水平。",
        "英伟达股价": "截至 2026 年 4 月 2 日，英伟达（NVIDIA）股票表现强劲，受 AI 算力需求持续增长推动，股价维持在高位，市值位居全球前列。",
        "北京天气": "北京今天天气晴朗，气温 15-25 摄氏度，偏南风 2-3 级，空气质量优良，非常适合户外活动。",
        "2026年世界杯": "2026年国际足联世界杯将由美国、加拿大和墨西哥联合举办。这将是世界杯历史上首次有 48 支球队参加决赛阶段的比赛。"
    }
    
    # 简单的关键词匹配模拟搜索逻辑
    for key in mock_results:
        if key.lower() in query.lower():
            return json.dumps({"query": query, "result": mock_results[key]}, ensure_ascii=False)
    
    return json.dumps({"query": query, "result": f"关于 '{query}' 的实时信息未找到，建议换个关键词试试。"}, ensure_ascii=False)

# 2. 定义工具规范 (Standard Tool Definition)
# 这是大模型识别和调用工具的标准格式
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "当用户询问当前实时信息、新闻、天气或其知识库中未包含的最新事实时，使用此工具进行联网搜索。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要搜索的查询词，应简洁且针对性强。"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def run_search_agent(user_input: str, isSearch: bool = True):
    """
    Agent 执行逻辑：
    1. 接收用户输入。
    2. 如果 isSearch 为 True，询问大模型是否需要调用搜索工具。
    3. 如果需要，执行搜索并反馈结果。
    4. 大模型根据搜索结果生成最终答案。
    """
    print(f"\n>>> 用户提问: {user_input} (联网搜索开关: {'开启' if isSearch else '关闭'})")
    
    messages = [
        {"role": "system", "content": "你是一个具备联网搜索能力的智能助手。请根据搜索结果提供准确、客观且及时的回答。"},
        {"role": "user", "content": user_input}
    ]
    
    # 第一步：大模型决策阶段
    # 如果 isSearch 为 False，则不传递 tools 参数，模型将无法调用搜索工具
    completion_params = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": messages,
    }
    
    if isSearch:
        completion_params["tools"] = tools
        completion_params["tool_choice"] = "auto"

    response = client.chat.completions.create(**completion_params)
    
    message = response.choices[0].message
    tool_calls = message.tool_calls
    
    # 第二步：处理工具执行 (Action Phase)
    if isSearch and tool_calls:
        print(f"  [决策结果] 大模型请求调用工具: {tool_calls[0].function.name}")
        # 将大模型的回应存入上下文（必须包含 tool_calls 信息）
        messages.append(message)
        
        # 依次处理每一个工具调用请求
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "web_search":
                # 执行真实的 Python 函数
                search_content = web_search(query=function_args.get("query"))
                
                # 将工具执行结果存入上下文
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": search_content,
                })
        
        # 第三步：生成最终答案 (Final Generation Phase)
        final_response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=messages
        )
        print(f">>> 助手回复: {final_response.choices[0].message.content}")
    else:
        # 如果不需要搜索或开关关闭，直接给出答案
        if not isSearch:
            print("  [提示] 联网搜索开关已关闭，大模型将根据自身知识回答。")
        print(f">>> 助手回复: {message.content}")

if __name__ == "__main__":
    # 场景 1: 开启联网搜索 (触发搜索)
    run_search_agent("请介绍一下 DeepSeek-V3 模型的最新动态。", isSearch=True)
    
    # 场景 2: 关闭联网搜索 (大模型凭自身知识回答)
    run_search_agent("北京今天的天气适合户外活动吗？", isSearch=False)
    
    # 场景 3: 基础对话 (默认开启搜索，但语义不触发)
    run_search_agent("你好，你是谁？")
