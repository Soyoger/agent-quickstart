"""
07_ReactAgent_示例.py
展示 ReAct (Reason + Act) 模式的 Agent 运行逻辑。
核心逻辑：While 循环，包含 Thought -> Action -> Observation 的迭代过程。
"""

import json
from openai import OpenAI
import config

# 初始化硅基流动客户端
client = OpenAI(
    api_key=config.api_key,
    base_url=config.base_url
)

def get_weather(city):
    """模拟天气查询工具"""
    weather_data = {
        "北京": "晴，25℃",
        "上海": "小雨，20℃",
        "广州": "多云，28℃"
    }
    return weather_data.get(city, "未知天气")

# 定义工具列表
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如北京、上海"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

def run_react_agent(user_query):
    print(f"--- Agent 开始执行任务: {user_query} ---")
    
    # 初始化消息队列，包含系统提示，指导模型进行 ReAct 思考
    messages = [
        {
            "role": "system", 
            "content": "你是一个具备 ReAct 思考能力的助手。在采取任何行动之前，请先输出你的 Thought（思考过程）。"
                       "如果需要调用工具，请使用工具调用功能。如果已经得到答案，请给出最终回答。"
        },
        {"role": "user", "content": user_query}
    ]
    
    max_steps = 5
    step = 0
    
    while step < max_steps:
        step += 1
        print(f"\n>> 步骤 {step}:")
        
        # 1. 模型思考与决策
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        # 输出模型返回的思考内容 (如果模型有 content 输出，则视为 Thought)
        if message.content:
            print(f"【思考/回答】: {message.content}")
            
        # 2. 检查是否有工具调用 (Action)
        if message.tool_calls:
            for tool_call in message.tool_calls:
                action_name = tool_call.function.name
                action_input = json.loads(tool_call.function.arguments)
                
                print(f"【行动】: 调用工具 {action_name}, 参数: {action_input}")
                
                # 执行具体工具逻辑
                if action_name == "get_weather":
                    observation = get_weather(action_input.get("city"))
                else:
                    observation = "未知工具"
                
                print(f"【观察】: 工具返回结果 - {observation}")
                
                # 3. 将观察结果反馈给模型
                # 注意：反馈后，循环会回到顶部，模型将根据观察结果进行下一步思考
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(observation)
                })
        else:
            # 如果没有工具调用且有内容输出，通常意味着任务完成
            if message.content:
                print(f"\n【最终回答】: {message.content}")
                break
            
    print("\n--- 任务执行完毕 ---")

if __name__ == "__main__":
    user_input = "帮我查一下北京的天气，顺便建议我是否需要带伞。"
    run_react_agent(user_input)
