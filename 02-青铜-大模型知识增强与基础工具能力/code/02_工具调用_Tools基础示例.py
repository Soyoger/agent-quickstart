import sys
sys.path.append('../../agent-quickstart')
import json
from openai import OpenAI
from config import base_url, api_key

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

def get_weather(city: str) -> str:
    """
    模拟获取天气信息的工具。
    
    Args:
        city: 城市名称。
    Returns:
        JSON 格式的天气信息字符串。
    """
    # 模拟数据
    weather_data = {
        "北京": "晴，25°C",
        "上海": "多云，22°C",
        "广州": "阵雨，28°C"
    }
    result = weather_data.get(city, "未查询到该城市的天气信息")
    return json.dumps({"city": city, "weather": result}, ensure_ascii=False)

def calculate(expression: str) -> str:
    """
    执行数学运算的工具。
    
    Args:
        expression: 数学表达式（如 "123 * 456"）。
    Returns:
        计算结果字符串。
    """
    try:
        # 注意：在生产环境中使用 eval 需谨慎，此处仅为示例
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"

# 定义工具列表，遵循 OpenAI Tool 调用规范
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学运算，如加减乘除",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如：123 * 456"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

def run_conversation(user_prompt: str):
    """
    执行一次完整的对话流程：大模型判断是否需要工具 -> 调用工具 -> 返回最终答案。
    """
    print(f"\n--- 用户提问: {user_prompt} ---")
    
    # 1. 发送初始请求
    messages = [
        {"role": "system", "content": "你是一个实用的助手。你可以使用工具来回答问题。"},
        {"role": "user", "content": user_prompt}
    ]
    
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3", # 使用支持 Tool Calling 的模型
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    
    # 2. 检查大模型是否建议调用工具
    if tool_calls:
        print(f"大模型决定调用 {len(tool_calls)} 个工具。")
        
        # 将大模型的回复（包含 tool_calls）添加到消息列表中
        messages.append(response_message)
        
        # 3. 遍历并执行工具调用
        available_functions = {
            "get_weather": get_weather,
            "calculate": calculate,
        }
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"正在调用工具: {function_name}, 参数: {function_args}")
            
            # 执行实际的 Python 函数
            function_response = function_to_call(**function_args)
            
            # 将工具执行结果添加到消息列表中
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })
        
        # 4. 将工具结果发回大模型，获取最终回复
        second_response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=messages,
        )
        final_answer = second_response.choices[0].message.content
        print(f"最终回复: {final_answer}")
    else:
        print(f"最终回复 (无工具调用): {response_message.content}")

if __name__ == "__main__":
    # 示例 1：调用 1 个工具
    run_conversation("北京现在的天气怎么样？")
    
    # 示例 2：并行调用 2 个工具
    run_conversation("帮我查一下上海的天气，并计算 123 乘以 456 等于多少？")
