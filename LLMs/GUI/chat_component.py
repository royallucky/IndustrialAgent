import json
import queue
import threading
from datetime import datetime

from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import QTextEdit, QPushButton, QHBoxLayout, QCheckBox, QWidget, QVBoxLayout

from LLMs.use_ollama.modes import DialogModes
from LLMs.utils import BaseComponent


class AsyncChatLogger:
    """异步对话记录器"""
    def __init__(self):
        self.log_queue = queue.Queue()
        self.running = True
        self.worker = threading.Thread(target=self._write_worker, daemon=True)
        self.worker.start()

    def log(self, role, content, mode):
        """添加日志到写入队列"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "mode": mode
        }
        self.log_queue.put(entry)

    def _write_worker(self):
        """后台写入线程"""
        while self.running:
            try:
                entry = self.log_queue.get(timeout=1)
                with open("chat_history.json", "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except queue.Empty:
                continue

    def stop(self):
        """安全停止记录器"""
        self.running = False
        self.worker.join()


class ChatComponent(BaseComponent):
    """集成多模式对话的LLM专业问答界面"""
    def __init__(self, model="DeepSeek_1.5B"):
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)

        # 模式选择工具栏
        self.mode_bar = QHBoxLayout()
        self.mode_btns = {
            "single": QPushButton("随便问问"),
            "multi": QPushButton("帮你分析"),
            "strict": QPushButton("帮你查询")
        }
        for btn in self.mode_btns.values():
            btn.setCheckable(True)
            self.mode_bar.addWidget(btn)
        self.mode_btns["single"].setChecked(True)  # 默认单轮模式
        layout.addLayout(self.mode_bar)

        # 消息显示区
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display, stretch=4)

        # 输入控制区
        control_layout = QHBoxLayout()
        self.thought_check = QCheckBox("显示思考过程")
        control_layout.addWidget(self.thought_check)
        layout.addLayout(control_layout)

        # 输入框
        self.input_area = QTextEdit()
        self.input_area.setMaximumHeight(80)
        self.input_area.setPlaceholderText("输入问题 (输入exit退出)...")
        layout.addWidget(self.input_area)

        # 发送按钮
        self.send_btn = QPushButton("发送 (Ctrl+Enter)")
        self.send_btn.setShortcut("Ctrl+Return")
        self.send_btn.clicked.connect(self.process_query)
        layout.addWidget(self.send_btn)

        # 初始化对话引擎
        self.llm_engine = DialogModes(model=model)
        self.current_mode = "single"

        # 绑定模式切换
        self.mode_btns["single"].clicked.connect(lambda: self.set_mode("single"))
        self.mode_btns["multi"].clicked.connect(lambda: self.set_mode("multi"))
        self.mode_btns["strict"].clicked.connect(lambda: self.set_mode("strict"))

        # 添加异步记录器
        self.log_saver = AsyncChatLogger()

    def set_mode(self, mode):
        """切换对话模式"""
        self.current_mode = mode
        for name, btn in self.mode_btns.items():
            btn.setChecked(name == mode)
        self.append_message("系统",
                            f"已切换到【{'单轮' if mode == 'single' else '多轮' if mode == 'multi' else '严谨'}对话模式】",
                            "#FF9900")

    def get_name(self):
        return "专业问答"

    def get_widget(self):
        return self.widget

    def update(self, data):
        """接收领域知识更新"""
        self.append_message("系统", "当前领域知识版本为:【V1.0.1】", "#888888")

    def process_query(self):
        """ 处理用户查询 """
        query = self.input_area.toPlainText().strip()
        if not query or query.lower() in ["exit", "quit"]:
            return

        # 记录用户提问
        self.log_saver.log("user", query, self.current_mode)

        self.append_message("用户", query, "#0066CC")
        self.input_area.clear()

        # 获取LLM响应
        show_thought = self.thought_check.isChecked()
        if self.current_mode == "single":
            reply = self.llm_engine.single_turn(query, show_thought)
        elif self.current_mode == "multi":
            reply = self.llm_engine.multi_turn(query, show_thought)
        else:
            reply = self.llm_engine.strict_query(query, show_thought)

        # 记录AI响应
        self.log_saver.log("assistant", reply, self.current_mode)

        # 解析带思考过程的响应
        if show_thought and "||THOUGHT||" in reply:
            thought, answer = reply.split("||THOUGHT||", 1)
            self.append_message("思考", thought.strip(), "#663399")
            self.append_message("AI助手", answer.strip(), "#009933")
        else:
            self.append_message("AI助手", reply.strip(), "#009933")

    def append_message(self, role, text, color):
        """添加彩色对话消息"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 角色标签
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(f"{role}: ", fmt)

        # 消息内容
        fmt.setForeground(QColor("#000000"))
        cursor.insertText(f"{text}\n\n")

        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

