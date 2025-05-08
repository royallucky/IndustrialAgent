"""
LLM Prompt 工程工具 - 将需求转换为优化后的LLM输入 (DeepSeek 专用)
输出格式遵循 ChatML 标准结构，但以 OpenAI SDK 标准 message 列表调用
"""
import os
import re
from dataclasses import dataclass
from typing import List, Dict
import json
from openai import OpenAI


@dataclass
class DeepSeekPrompt:
    """DeepSeek 专用 Prompt 数据结构，用于构造发送给模型的上下文信息"""

    system: str
    # 系统指令：定义模型的角色和任务处理方式，如“你是一个资深算法工程师……”

    tools: List[Dict]
    # 可调用工具：指定模型可以使用的函数/插件，例如 code_interpreter、retrieval 工具等

    examples: List[Dict]
    # Few-shot 示例：给模型一些输入输出示例，帮助其理解任务（例如如何解析需求、如何输出类结构）

    constraints: List[str]
    # 输出限制：对模型的输出结果添加规则，比如“方法参数必须带类型注解”、“避免使用抽象基类”等


def build_deepseek_prompt(requirement: str) -> DeepSeekPrompt:
    """构建 DeepSeek 的 Prompt"""
    return DeepSeekPrompt(
        system=(
            "你是一个资深 算法工程师，请按以下步骤处理需求：\n"
            "1. 识别核心功能逻辑\n"
            "2. 设计类结构和方法\n"
            "3. 函数的入参以 '**kwargs'进行传递\n"
            "4. 输出的结果以dict的形式返回\n"
            "5. 生成的代码最后需要加上 main 函数与示例数据进行使用示例展示\n"
            "6. 输出 PEP8 兼容的 Python 代码，只输出代码即可\n\n"
            f"需求：\n{requirement}"
        ),
        tools=[
            {
                "type": "code_interpreter",
                "description": "需要生成可执行的 Python 代码"
            }
        ],
        examples=[
            {
                "role": "user",
                "content": "设计一个支持图片预览的上传组件"
            },
            {
                "role": "assistant",
                "content": json.dumps({
                    "class": "ImageUploader",
                    "methods": ["preview()", "validate()"],
                    "dependencies": ["PyQt5", "opencv-python"]
                }, ensure_ascii=False)
            }
        ],
        constraints=[
            "方法参数必须带类型注解",
            "避免使用抽象基类"
        ]
    )


def generate_deepseek_messages(requirement: str) -> List[Dict]:
    """生成符合 openai SDK 使用规范的 messages 列表"""
    prompt = build_deepseek_prompt(requirement)
    return [
        {"role": "system", "content": prompt.system},
        {"role": "user", "content": "请根据需求进行技术设计"}
    ]


def classify_requirement(requirement: str, api_key: str, base_url: str = "https://api.deepseek.com") -> bool:
    """
    调用 LLM 判断需求是否是代码开发类任务。
    返回 True 表示是，False 表示不是。
    """
    client = OpenAI(api_key=api_key, base_url=base_url)

    messages = [
        {"role": "system", "content": "你是一个专业需求分析师。请判断用户的需求是否属于软件/算法/代码开发类任务。只用回答“yes”或“no”。"},
        {"role": "user", "content": f"需求：{requirement}"}
    ]

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )

    answer = response.choices[0].message.content.strip()
    print(answer)
    return answer.startswith("yes")


def extract_python_code(text: str) -> str:
    """从模型返回内容中提取Python代码块"""
    matches = re.findall(r"```python(.*?)```", text, re.DOTALL)
    return "\n\n".join(code.strip() for code in matches) if matches else ""


def save_code_to_file(code: str, filename: str = "generated_code.py") -> str:
    """保存代码到本地 .py 文件"""
    os.makedirs("outputs", exist_ok=True)
    filepath = os.path.join("outputs", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    return filepath


def call_deepseek(requirement: str, api_key: str, base_url: str = "https://api.deepseek.com") -> str:
    """调用 DeepSeek Reasoner 接口返回响应内容"""
    if not classify_requirement(requirement, api_key, base_url):
        return "识别结果：非代码开发类任务，未调用 DeepSeek Reasoner。"

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 调用 deepseek-reasoner 处理技术实现
    messages = generate_deepseek_messages(requirement)
    print(messages)

    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages
    )
    content = response.choices[0].message.content
    print(content)
    # 尝试提取代码
    code = extract_python_code(content)
    if code:
        path = save_code_to_file(code)
        return f"已识别为代码任务，模型输出已保存为：{path}"
    else:
        return "已识别为代码任务，但未找到 Python 代码块。模型原始回答如下：\n\n" + content


if __name__ == "__main__":
    # ✅ 自定义你的需求
    requirement = """
    实现数据分析需求：
    1. 输入数据：shape=(n,5)的array
    2. 对第1列、第3列数据，分别进行均值、方差计算
    3. 输出第2步的计算结果
    """

    # ✅ 设置 API Key
    API_KEY = "sk-8da86d5e3eb64e58832fe1fbf65a2254"
    BASE_URL = "https://api.deepseek.com"

    # ✅ 获取响应内容
    try:
        result = call_deepseek(requirement, api_key=API_KEY, base_url=BASE_URL)
        print("DeepSeek 返回内容：\n")
        print(result)
    except Exception as e:
        print("调用失败：", e)
