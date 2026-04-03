import sys
sys.path.append('../../../agent-quickstart')
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from config import api_key, base_url
from openai import OpenAI

class Skill:
    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.meta = self._load_meta()
        self.instructions = self._load_instructions()
        self.name = self.meta.get("name", "unknown")
    
    def _load_meta(self) -> Dict[str, Any]:
        meta_path = self.skill_path / "meta.json"
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_instructions(self) -> str:
        skill_md_path = self.skill_path / "skill.md"
        if skill_md_path.exists():
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def execute(self, *args) -> Dict[str, Any]:
        scripts_dir = self.skill_path / "scripts"
        if not scripts_dir.exists():
            return {"error": "No scripts directory found"}
        
        script_files = list(scripts_dir.glob("*.py"))
        if not script_files:
            return {"error": "No Python script found"}
        
        script_path = script_files[0]
        cmd = [sys.executable, str(script_path)] + list(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=False
            )
            
            stdout = result.stdout
            stderr = result.stderr
            
            def decode_output(output):
                if not output:
                    return ""
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                for enc in encodings:
                    try:
                        return output.decode(enc)
                    except UnicodeDecodeError:
                        continue
                return output.decode('utf-8', errors='replace')
            
            stdout_str = decode_output(stdout)
            stderr_str = decode_output(stderr)
            
            if result.returncode == 0:
                return json.loads(stdout_str)
            else:
                return {"error": stderr_str}
        except Exception as e:
            return {"error": str(e)}

class SkillManager:
    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        self._load_skills()
    
    def _load_skills(self):
        if not self.skills_dir.exists():
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                try:
                    skill = Skill(str(skill_dir))
                    self.skills[skill.name] = skill
                except Exception as e:
                    print(f"Failed to load skill from {skill_dir}: {e}")
    
    def get_skill(self, name: str) -> Skill:
        return self.skills.get(name)
    
    def list_skills(self) -> List[Dict[str, Any]]:
        return [skill.meta for skill in self.skills.values()]
    
    def execute_skill(self, skill_name: str, *args) -> Dict[str, Any]:
        skill = self.get_skill(skill_name)
        if not skill:
            return {"error": f"Skill {skill_name} not found"}
        return skill.execute(*args)

def get_skill_tools(skill_manager: SkillManager) -> List[Dict[str, Any]]:
    tools = []
    for skill_name, skill in skill_manager.skills.items():
        if skill_name == "weather_query":
            tools.append({
                "type": "function",
                "function": {
                    "name": "weather_query",
                    "description": "查询指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称（中文）"
                            }
                        },
                        "required": ["city"]
                    }
                }
            })
        elif skill_name == "ticket_query":
            tools.append({
                "type": "function",
                "function": {
                    "name": "ticket_query",
                    "description": "查询火车票、机票信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_city": {"type": "string", "description": "出发城市"},
                            "to_city": {"type": "string", "description": "到达城市"},
                            "date": {"type": "string", "description": "出发日期（YYYY-MM-DD）"},
                            "type": {"type": "string", "description": "车票类型（train/flight）"}
                        },
                        "required": ["from_city", "to_city", "date", "type"]
                    }
                }
            })
        elif skill_name == "traffic_query":
            tools.append({
                "type": "function",
                "function": {
                    "name": "traffic_query",
                    "description": "查询实时交通状况和路线规划",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string", "description": "起点"},
                            "end": {"type": "string", "description": "终点"}
                        },
                        "required": ["start", "end"]
                    }
                }
            })
    return tools

def llm_with_skills(user_query: str, skill_manager: SkillManager) -> str:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    tools = get_skill_tools(skill_manager)
    messages = [{"role": "user", "content": user_query}]
    
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=messages,
        tools=tools
    )
    
    assistant_message = response.choices[0].message
    
    if assistant_message.tool_calls:
        tool_call = assistant_message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        if function_name == "weather_query":
            result = skill_manager.execute_skill("weather_query", function_args["city"])
        elif function_name == "ticket_query":
            result = skill_manager.execute_skill(
                "ticket_query",
                function_args["from_city"],
                function_args["to_city"],
                function_args["date"],
                function_args["type"]
            )
        elif function_name == "traffic_query":
            result = skill_manager.execute_skill(
                "traffic_query",
                function_args["start"],
                function_args["end"]
            )
        else:
            result = {"error": "Unknown function"}
        
        messages.append(assistant_message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
        
        final_response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=messages
        )
        return final_response.choices[0].message.content
    
    return assistant_message.content

def main():
    print("=" * 60)
    print("Skill 智能执行示例")
    print("=" * 60)
    
    current_dir = Path(__file__).parent
    skills_dir = current_dir / "skills"
    
    skill_manager = SkillManager(str(skills_dir))
    
    print(f"\n已加载 {len(skill_manager.skills)} 个 Skill:")
    for skill_meta in skill_manager.list_skills():
        print(f"  - {skill_meta['name']}: {skill_meta['description']}")
    
    print("\n" + "=" * 60)
    print("测试 Skill 调用")
    print("=" * 60)
    
    test_queries = [
        "北京今天天气怎么样？",
        "帮我查一下2026-04-05从北京到上海的高铁票",
        "从国贸到中关村怎么走最快？"
    ]
    
    for query in test_queries:
        print(f"\n用户: {query}")
        response = llm_with_skills(query, skill_manager)
        print(f"AI: {response}")

if __name__ == "__main__":
    main()
