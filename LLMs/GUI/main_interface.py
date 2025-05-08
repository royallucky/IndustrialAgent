import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QTextEdit, QFrame, QListWidget, QLabel
)

from LLMs.GUI.algorithm_component import AlgoComponent
from LLMs.GUI.chart_component import ChartComponent
from LLMs.GUI.chat_component import ChatComponent
from LLMs.GUI.login_algorithm_component import LoginComponent
from LLMs.GUI.table_component import TableComponent


# ---------------- 中间区域组件衔接基类及注册 ----------------

class ComponentRegistry:
    """组件注册中心（工厂模式）"""
    registry = {}

    @classmethod
    def register(cls, name, constructor):
        """
        注册组件类型
        :param name: 组件名称
        :param constructor: 组件构造函数
        """
        cls.registry[name] = constructor

    @classmethod
    def create(cls, name, **kwargs):
        """
        创建指定类型的组件实例
        :param name: 要创建的组件名称
        :return: 组件实例
        :raises ValueError: 当组件未注册时抛出
        """
        if name in cls.registry:
            return cls.registry[name](**kwargs)
        raise ValueError(f"Component '{name}' not registered")


# 注册可用组件类型
ComponentRegistry.register("Table", TableComponent)
ComponentRegistry.register("Chart", ChartComponent)
ComponentRegistry.register("Chat", ChatComponent)
ComponentRegistry.register("Algo", AlgoComponent)
ComponentRegistry.register("Login", LoginComponent)


class ComponentManager:
    def __init__(self, layout):
        self.layout = layout
        self.components = {}
        self.current_widget = None  # 只保存当前显示的widget对象

        """ 初始状态时展示Logo """
        self.placeholder = QLabel("Crucial Insight")  # 默认占位
        self.placeholder.setStyleSheet("""
            font-size: 64px;
            font-weight: bold;
            color: #999999;
        """)
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.placeholder)

    def load_component(self, name, data=None, **kwargs):
        # 移除当前显示的widget（如果存在）
        if self.current_widget is not None:
            self.layout.removeWidget(self.current_widget)
            self.current_widget.hide()
            # 注意：不再调用deleteLater()

        # 移除placeholder（如果存在）
        if self.placeholder is not None:
            self.layout.removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            self.placeholder = None

        # 获取/创建组件实例
        if name not in self.components:
            self.components[name] = ComponentRegistry.create(name, **kwargs)

        # 获取组件widget并显示
        widget = self.components[name].get_widget()
        self.layout.addWidget(widget)
        widget.show()
        self.current_widget = widget

        # 更新数据
        self.components[name].update(data)


# ---------------- 主界面 ----------------

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Expert")
        self.setMinimumSize(1200, 800)

        # 主窗口布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # === 左侧菜单区域 ===
        self.menu = QListWidget()
        self.menu.addItems(["查询知识", "操作知识库", "算法工作台", "注册插件"])  # 菜单选项
        # 设置字体加粗 + 大一号
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        for i in range(self.menu.count()):
            item = self.menu.item(i)
            item.setFont(font)

        self.menu.setFocusPolicy(Qt.NoFocus)        # 不接收焦点
        # 设置菜单项高度为窗口高度的0.1
        self.menu.setStyleSheet("""
            QListWidget {
                background-color: #f4f4f4;
                border: 1px solid #0078d7;
                outline: none;
            }
            QListWidget::item {
                height: 64px;
                font-size: 18px;
                font-weight: bold;
                color: #333333;
                padding-left: 40px;  /* 调整这里，让文字右移 */
                margin: 6px 0;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e6f0fa;
                color: #0078d7;
            }
            QListWidget::item:focus {
                outline: none;
            }
        """)

        main_layout.addWidget(self.menu, stretch=2)  # 占20%宽度

        # === 中间内容区域 ===
        self.center_frame = QFrame()
        self.center_layout = QVBoxLayout(self.center_frame)
        self.center_manager = ComponentManager(self.center_layout)  # 组件管理器
        main_layout.addWidget(self.center_frame, stretch=6)  # 占60%宽度

        # === 右侧日志区域 ===
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)  # 设置为只读
        main_layout.addWidget(self.log_area, stretch=2)  # 占20%宽度

        # 连接菜单点击事件
        self.menu.clicked.connect(self.menu_clicked)

        self.log_file_path = "app_log.txt"
        self.executor = ThreadPoolExecutor(max_workers=2)

    def menu_clicked(self, index):
        """
        处理菜单点击事件
        :param index: 被点击项的索引（自动传入）
        """
        item_text = self.menu.currentItem().text()
        if "查询知识" in item_text:
            self.center_manager.load_component("Chat", data="工程规范库v2.1")
            self.append_log("加载了LLM组件", "blue")

        elif "操作知识库" in item_text:
            self.center_manager.load_component("Table", data="测试数据B")
            self.append_log("加载了知识库组件", "blue")

        elif "算法" in item_text:
            self.center_manager.load_component("Algo", data="算法工作台", external_log_fn=self.append_log)
            self.append_log("加载了算法工作台组件", "blue")

        elif "注册" in item_text:
            self.center_manager.load_component("Login", data="注册平台", external_log_fn=self.append_log)
            self.append_log("加载了注册平台组件", "blue")

    def append_log(self, message, color="#000000"):
        """
        添加日志信息
        :param message: 要显示的日志内容
        :param color: 文本颜色（十六进制代码，默认黑色）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 添加灰色时间戳
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#888888"))
        cursor.insertText(f"[{timestamp}] ", fmt)

        # 添加带颜色的日志内容
        fmt.setForeground(QColor(color))
        cursor.insertText(f"{message}\n", fmt)

        # 自动滚动到底部
        self.log_area.setTextCursor(cursor)
        self.log_area.ensureCursorVisible()

        # 异步写入本地日志
        log_entry = f"[{timestamp}] {message}\n"
        self.write_log_async(log_entry)

    def write_log_async(self, log_entry):
        """
        异步写入日志到本地文件
        """
        self.executor.submit(self.write_log_to_file, log_entry)

    def write_log_to_file(self, log_entry):
        """
        实际写入日志到本地文件
        """
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"日志写入出错: {e}")


# ---------------- 主程序入口 ----------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()  # 默认全屏显示
    sys.exit(app.exec_())