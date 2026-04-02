from openai import OpenAI
from config import base_url, api_key

client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

# 发送带有流式输出的请求
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3.2",
    messages=[
         {"role": "system", "content": "你是一个专业的问答助手，你的任务是回答用户的问题,限制100字以内。"},
         {"role": "user", "content": "今天天气怎么样？"}
    ],
    stream=True  # 启用流式输出
)

# 逐步接收并处理响应
for chunk in response:
    if not chunk.choices:
        continue
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
    if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end="", flush=True)# 01_基础交互_一问一答示例.py