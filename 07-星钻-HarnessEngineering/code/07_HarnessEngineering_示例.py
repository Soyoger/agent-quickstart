from dataclasses import dataclass
from typing import Callable, Dict, List
import json
import random


@dataclass
class TaskCase:
    name: str
    prompt: str
    expected_keywords: List[str]
    must_not_contain: List[str]


def demo_agent(prompt: str) -> str:
    knowledge = {
        "什么是RAG": "RAG 是检索增强生成，通过先检索外部知识再生成答案，降低幻觉。",
        "MCP有什么用": "MCP 用于标准化模型与工具的连接协议，提升系统集成效率。",
        "请给出一个订票流程": "先确定日期，再查询航班，选择最优方案后完成下单并发送通知。"
    }
    for key, value in knowledge.items():
        if key in prompt:
            return value
    if random.random() < 0.15:
        return "我不太确定，可能需要更多信息。"
    return "这是一个演示回答，建议补充更多上下文。"


class Harness:
    def __init__(self, agent_fn: Callable[[str], str], cases: List[TaskCase]):
        self.agent_fn = agent_fn
        self.cases = cases

    def run(self) -> Dict[str, object]:
        details: List[Dict[str, object]] = []
        passed = 0
        for case in self.cases:
            answer = self.agent_fn(case.prompt)
            keyword_hit = all(k in answer for k in case.expected_keywords)
            safety_hit = all(k not in answer for k in case.must_not_contain)
            ok = keyword_hit and safety_hit
            if ok:
                passed += 1
            details.append(
                {
                    "name": case.name,
                    "prompt": case.prompt,
                    "answer": answer,
                    "pass": ok,
                    "keyword_hit": keyword_hit,
                    "safety_hit": safety_hit,
                }
            )
        total = len(self.cases)
        score = round(passed / total, 4) if total else 0.0
        return {"total": total, "passed": passed, "score": score, "details": details}


def build_cases() -> List[TaskCase]:
    return [
        TaskCase(
            name="RAG解释准确性",
            prompt="请回答：什么是RAG",
            expected_keywords=["检索增强生成", "检索"],
            must_not_contain=["胡编", "不知道"],
        ),
        TaskCase(
            name="MCP价值表达",
            prompt="MCP有什么用",
            expected_keywords=["标准化", "协议"],
            must_not_contain=["无法连接"],
        ),
        TaskCase(
            name="任务流程完整性",
            prompt="请给出一个订票流程",
            expected_keywords=["查询航班", "下单", "通知"],
            must_not_contain=["跳过"],
        ),
    ]


if __name__ == "__main__":
    harness = Harness(agent_fn=demo_agent, cases=build_cases())
    report = harness.run()
    print(json.dumps(report, ensure_ascii=False, indent=2))
