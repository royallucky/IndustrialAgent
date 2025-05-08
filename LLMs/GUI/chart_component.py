from PyQt5.QtWidgets import QLabel

from LLMs.utils import BaseComponent


class ChartComponent(BaseComponent):
    """图表展示组件"""
    def __init__(self):
        self.label = QLabel("图表组件 - 显示图形")

    def get_name(self):
        return "Chart"

    def get_widget(self):
        return self.label

    def update(self, data):
        self.label.setText(f"图表组件更新内容: {data}")