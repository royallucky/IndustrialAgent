from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, \
    QStyledItemDelegate
from PyQt5.QtCore import Qt
from LLMs.utils import BaseComponent


class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("请选择函数功能类型")
        self.setItemDelegate(QStyledItemDelegate())
        self.view().pressed.connect(self.handle_item_pressed)

        # 固定高度
        self.setFixedHeight(40)
        self.setStyleSheet("""
        QComboBox { height: 40px; font-size: 20px; }  /* 下拉框本体字体 */
            QAbstractItemView::item { font-size: 20px; } /* 下拉项字体 */""")

    def add_check_items(self, items):
        """添加多选项"""
        for item in items:
            self.addItem(item)
            index = self.model().index(self.count() - 1, 0)
            self.model().setData(index, Qt.Unchecked, Qt.CheckStateRole)

            # # 为每个项添加大图标
            # icon = QIcon("path_to_your_icon.png")  # 这里你可以根据需求更换图标路径
            # icon = icon.pixmap(20, 20)  # 设置图标大小
            # self.setItemIcon(self.count() - 1, icon)

    def handle_item_pressed(self, index):
        """点击选项时切换选中状态"""
        state = self.model().data(index, Qt.CheckStateRole)
        new_state = Qt.Unchecked if state == Qt.Checked else Qt.Checked
        self.model().setData(index, new_state, Qt.CheckStateRole)
        self.update_text()

    def update_text(self):
        """根据选中项更新显示文本"""
        selected_items = []
        for i in range(self.count()):
            if self.model().data(self.model().index(i, 0), Qt.CheckStateRole) == Qt.Checked:
                selected_items.append(self.itemText(i))
        self.lineEdit().setText(", ".join(selected_items))

    def get_selected_items(self):
        """获取所有选中的项"""
        selected_items = []
        for i in range(self.count()):
            if self.model().data(self.model().index(i, 0), Qt.CheckStateRole) == Qt.Checked:
                selected_items.append(self.itemText(i))
        return selected_items


class LoginComponent(BaseComponent):
    """功能登录配置组件，支持配置函数类型、描述、参数和代码，并注册功能"""

    def __init__(self, external_log_fn):
        """
        初始化 LoginComponent 组件，包含说明区域、4个输入框和注册按钮

        Args:
            external_log_fn (function): 外部日志函数，用于记录注册操作日志
        """
        super().__init__()
        self.widget = QWidget()
        self.external_log_fn = external_log_fn

        main_layout = QVBoxLayout(self.widget)

        # ===== 说明区域 =====
        spec_label = QLabel(
            "【规范说明】\n"
            "1. 函数功能类型：仅支持 'image' 或 'table'\n"
            "2. 描述：填写函数的功能描述\n"
            "3. 参数：形如 '参数1: 名称: 类型, 描述；参数2: ...'\n"
            "4. 代码：填写完整函数实现代码"
        )
        spec_label.setWordWrap(True)
        spec_label.setAlignment(Qt.AlignLeft)

        # ===== 输入区域 =====
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)  # 控件间间距，适当可调

        # ===== 函数功能类型 多选下拉 =====
        self.type_input = CheckableComboBox()
        self.type_input.add_check_items(["image", "table"])
        input_layout.addWidget(self.type_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("请输入函数功能描述")
        input_layout.addWidget(self.desc_input)

        self.param_input = QTextEdit()
        self.param_input.setPlaceholderText("请输入参数说明，如：参数1: data: List[List], 表格数据")
        input_layout.addWidget(self.param_input)

        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText("请输入函数代码")
        input_layout.addWidget(self.code_input)

        self.register_button = QPushButton("注册功能")
        self.register_button.clicked.connect(self.register_function)
        input_layout.addWidget(self.register_button)

        # ===== 主布局添加控件，并按 3:7 设置比例 =====
        main_layout.addWidget(spec_label)
        main_layout.addWidget(input_widget)

        main_layout.setStretch(0, 2)
        main_layout.setStretch(1, 8)

    def get_name(self) -> str:
        """
        获取组件名称

        Returns:
            str: 组件名称
        """
        return "Login"

    def get_widget(self) -> QWidget:
        """
        获取当前组件主界面 Widget

        Returns:
            QWidget: 组件界面
        """
        return self.widget

    def update(self, data: str) -> None:
        """
        接收外部数据并更新组件中的描述输入框

        Args:
            data (str): 外部数据内容
        """
        self.desc_input.setPlainText(data)

    def register_function(self) -> None:
        """
        点击【注册功能】按钮时触发，读取所有输入内容，执行注册逻辑
        """
        func_type = self.type_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        params = self.param_input.toPlainText().strip()
        code = self.code_input.toPlainText().strip()

        print("✅ 注册功能")
        print(f"类型: {func_type}")
        print(f"描述: {description}")
        print(f"参数: {params}")
        print(f"代码:\n{code}")

        # 这里你可以接着做功能注册、保存、调用等后续逻辑


