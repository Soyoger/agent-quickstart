import sys
sys.path.append('../../agent-quickstart')
import json
import inspect
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Callable, List, Optional
from openai import OpenAI
from config import base_url, api_key

# 1. 初始化客户端
client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

# --- 核心数据模型 ---

@dataclass
class Tool:
    """工具定义数据模型，负责将 Python 函数元数据转换为大模型协议格式"""
    name: str                   # 工具名称/函数名
    description: str            # 工具描述（用于大模型理解）
    parameters: Dict[str, Any]  # 参数 JSON Schema
    function: Callable          # 实际的执行函数

    def to_dict(self) -> dict:
        """转换为 OpenAI Function Calling 标准格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

# --- 工具注册中心 ---

class ToolRegistry:
    """
    工具注册中心：核心职责是“翻译”和“管理”。
    1. 自省与生成：自动读取函数签名和文档，生成 JSON Schema。
    2. 统一执行：解析大模型参数并分发执行。
    """
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register_from_class(self, cls_instance):
        """
        利用 Python 的反射机制（inspect 模块）自动从类实例中注册方法为工具。
        要求：方法必须有文档字符串（docstring）作为描述。
        """
        for name, method in inspect.getmembers(cls_instance, predicate=inspect.ismethod):
            # 过滤掉私有方法和不带文档的方法
            if name.startswith('_') or not inspect.getdoc(method):
                continue
            
            # 获取函数描述
            doc = inspect.getdoc(method)
            
            # 利用 inspect 获取函数签名
            sig = inspect.signature(method)
            
            # 构造 JSON Schema 参数结构
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self': continue
                
                # 简单映射 Python 类型到 JSON Schema 类型
                param_type = "string" # 默认字符串
                if param.annotation == int: param_type = "integer"
                elif param.annotation == float: param_type = "number"
                elif param.annotation == bool: param_type = "boolean"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"参数: {param_name}" # 生产环境可进一步解析 docstring 获取更详细描述
                }
                
                # 如果没有默认值，则为必填项
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)
            
            parameters = {
                "type": "object",
                "properties": properties,
                "required": required
            }
            
            # 存入注册表
            self.tools[name] = Tool(
                name=name,
                description=doc,
                parameters=parameters,
                function=method
            )
        print(f"  [Registry] 成功自动注册工具数量: {len(self.tools)}")

    def get_tools_spec(self) -> List[dict]:
        """获取所有已注册工具的 OpenAI 规范描述"""
        return [tool.to_dict() for tool in self.tools.values()]

    async def execute_tool(self, tool_call) -> dict:
        """
        执行单个工具调用：
        1. 解析参数
        2. 找到对应函数
        3. 异步/同步执行
        4. 序列化结果返回
        """
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        
        if func_name not in self.tools:
            return {"error": f"Tool {func_name} not found"}
        
        tool = self.tools[func_name]
        print(f"  [Registry] 正在执行: {func_name}, 参数: {func_args}")
        
        try:
            # 判断是否为异步函数
            if asyncio.iscoroutinefunction(tool.function):
                result = await tool.function(**func_args)
            else:
                # 即使是同步函数，也在异步上下文中通过多线程或直接调用运行
                result = tool.function(**func_args)
            
            # 序列化结果
            return {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": str(result) if not isinstance(result, str) else result
            }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": f"执行错误: {str(e)}"
            }

# --- 具体的业务工具类 ---

class TravelTools:
    """智能出行助手工具集"""
    
    def search_flights(self, origin: str, destination: str, date: str):
        """查询从出发地到目的地在特定日期的机票航班信息。"""
        print(f"    -> 执行查询: {origin} 到 {destination}")
        flights = [
            {"flight_no": "CA1234", "price": 1200, "time": "08:00"},
            {"flight_no": "MU5678", "price": 980, "time": "14:30"}
        ]
        return json.dumps(flights, ensure_ascii=False)

    def book_ticket(self, flight_no: str, passenger_name: str):
        """根据航班号为指定的乘客预订机票。"""
        print(f"    -> 执行订票: {passenger_name} -> {flight_no}")
        return json.dumps({"status": "success", "order_id": "ORD20260402XYZ"}, ensure_ascii=False)

    def send_notification(self, message: str, channel: str = "SMS"):
        """向用户发送行程确认通知。"""
        print(f"    -> 发送{channel}通知: {message}")
        return json.dumps({"status": "sent"}, ensure_ascii=False)

# --- 核心任务执行逻辑 ---

async def run_task_agent(user_query: str):
    """通过 ToolRegistry 管理的智能 Agent 流程"""
    print(f"\n>>> 任务请求: {user_query}")
    
    # 1. 初始化注册中心并注册工具
    registry = ToolRegistry()
    registry.register_from_class(TravelTools())
    
    messages = [
        {"role": "system", "content": "你是一个专业的出行助理。请通过工具解决用户的问题。"},
        {"role": "user", "content": user_query}
    ]
    
    # 2. 任务循环
    while True:
        # 获取大模型决策
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=messages,
            tools=registry.get_tools_spec(),
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        if not message.tool_calls:
            # 任务结束，输出最终答复
            print(f">>> 助理最终答复: {message.content}")
            break
        
        # 3. 利用 Registry 统一执行所有工具调用请求
        tasks = [registry.execute_tool(tool_call) for tool_call in message.tool_calls]
        results = await asyncio.gather(*tasks)
        
        # 4. 将执行结果添加回上下文
        messages.extend(results)

if __name__ == "__main__":
    # 使用异步运行
    task = "帮我查一下明天北京到上海的机票，并帮张三预订最便宜的那一班，订好后发通知。"
    asyncio.run(run_task_agent(task))
