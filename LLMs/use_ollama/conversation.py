""" 多轮对话上下文管理 """
class ConversationManager:
    def __init__(self, system_prompt="你是一个有帮助的助手。回答问题使用中文。不要生成重复的答复，不要进行多次思考", max_turns=50):
        self.system_prompt = system_prompt
        self.history = []
        self.max_turns = max_turns

    def append_turn(self, user_input: str, assistant_reply: str):
        self.history.append((user_input, assistant_reply))
        if len(self.history) > self.max_turns:
            self.history.pop(0)

    def build_prompt(self, user_input: str):
        full_prompt = f"System: {self.system_prompt}\n"
        for q, a in self.history:
            full_prompt += f"User: {q}\nAssistant: {a}\n"
        full_prompt += f"User: {user_input}\nAssistant:"
        return full_prompt
