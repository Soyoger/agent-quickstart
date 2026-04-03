# 四、高阶进阶：Agent 智能代理（大模型由"被动对话"到"主动规划"的跨越）

## 4.1 Agent 智能代理的由来与发展

### 4.1.1 Agent 的定义：具备自主性、反应性、主动性和社交能力的智能实体

在人工智能领域，Agent（智能代理）是一个能够感知环境、进行决策并采取行动以实现目标的系统。在大模型时代，Agent 指的是以大语言模型（LLM）为核心大脑，通过赋予其规划、记忆和工具使用能力，使其能够自主完成复杂任务的智能体。

### 4.1.2 发展历程：从 LLM 到 Agent 的演进

- **1.0 阶段：基础对话（LLM as a Chatbot）**：大模型仅作为对话接口，提供信息咨询和文本生成。
- **2.0 阶段：能力增强（RAG & Function Call）**：通过知识库增强（RAG）和工具调用（Function Call）解决模型知识滞后和缺乏执行力的问题。
- **3.0 阶段：智能代理（Agentic AI）**：模型不再仅仅是执行单一指令，而是能够自主拆解任务、自我反思、多轮迭代并最终交付结果。

## 4.2 Agent 的核心原理与架构

Agent 的本质是 **LLM + 规划（Planning）+ 记忆（Memory）+ 工具使用（Tool Use）** 的组合体。

### 4.2.1 核心模块拆解

1.  **规划（Planning）**：
    - **任务拆解**：将复杂目标分解为可执行的子任务。
    - **自我反思**：对过去的决策进行审视和纠错（Self-Reflection/Self-Correction）。
2.  **记忆（Memory）**：
    - **短期记忆**：上下文（Context），记录当前任务的执行进度。
    - **长期记忆**：通过 RAG 或外部数据库存储的历史经验和知识。
3.  **工具使用（Tool Use）**：
    - 能够识别何时需要外部工具（如计算器、搜索、API），并准确调用。

## 4.3 Agent 的运行逻辑：While 循环

与传统的线性程序不同，Agent 的核心运行逻辑是一个 **While 循环**。它不断地感知当前状态，进行思考，采取行动，观察结果，直到任务完成。

### 4.3.1 While 循环伪代码逻辑

```python
# Agent 核心运行逻辑伪代码
def run_agent(task):
    state = initialize_state(task)
    while not is_task_finished(state):
        # 1. 思考 (Think)
        thought = llm.generate_thought(state)
        
        # 2. 决策与行动 (Act)
        action = llm.decide_action(thought)
        observation = execute_tool(action)
        
        # 3. 更新状态 (Observe)
        state.update(thought, action, observation)
        
    return state.final_result
```

## 4.4 ReAct 循环示例：典型的 Agent 执行模式

ReAct（Reason + Act）是目前最流行的 Agent 提示工程框架之一。它要求模型在执行每一个行动之前，先写下自己的思考过程。

### 4.4.1 ReAct 交互示例

**任务**：帮我查询今天北京的天气，并根据天气建议我是否需要带伞。

**执行过程**：

1.  **Thought (思考)**：用户想知道北京的天气。我需要先调用天气查询工具获取实时信息。
2.  **Action (行动)**：调用 `get_weather(city="北京")`。
3.  **Observation (观察)**：返回结果：“北京今日有阵雨，降水概率 70%，气温 18-25℃”。
4.  **Thought (思考)**：根据观察到的结果，今天北京有雨。降水概率较高，应该建议用户带伞。
5.  **Final Answer (最终回答)**：今天北京有阵雨，气温在 18-25℃ 之间。由于降水概率较大（70%），建议您出门带一把雨伞以防万一。

---
*下一章我们将探讨多 Agent 协同（Multi-Agent Systems），看多个 Agent 如何像团队一样分工合作。*
