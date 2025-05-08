""" 不同交互模式 """
from LLMs.use_ollama.client import OllamaClient
from LLMs.use_ollama.conversation import ConversationManager

import re


def strip_thought_content(text: str) -> str:
    """
    去除模型输出中的 <think>...</think> 内容。
    默认情况下隐藏思考过程内容。
    """
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class DialogModes:
    def __init__(self, model="llama2"):
        self.client = OllamaClient(model_name=model)
        self.conversation = ConversationManager()

    def single_turn(self, user_input: str, show_thought: bool = False, temperature: float=0.7):
        prompt = f"User: {user_input}\nAssistant:"
        result = self.client.generate(prompt, temperature=temperature)
        return result if show_thought else strip_thought_content(result)

    def multi_turn(self, user_input: str, show_thought: bool = False, temperature: float=0.5):
        prompt = self.conversation.build_prompt(user_input)
        reply = self.client.generate(prompt, temperature=temperature)
        self.conversation.append_turn(user_input, reply)
        return reply if show_thought else strip_thought_content(reply)

    def strict_query(self, user_input: str, show_thought: bool = False):
        system_prompt = (
            "你是一个诚实的知识问答助手，只能基于事实回答问题。"
            "如果你不知道答案，就说 '我不知道'。不要编造答案。"
        )
        prompt = f"{system_prompt}\nUser: {user_input}\nAssistant:"
        result = self.client.generate(prompt, temperature=0.0)
        return result if show_thought else strip_thought_content(result)
