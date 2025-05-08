import csv
import importlib.util
import json
import re
from typing import Dict, Any, Optional

import cv2
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, QHBoxLayout, \
    QTableWidget, QScrollArea, QTableWidgetItem, QFrame, QMessageBox, QTextBrowser

from LLMs.GUI.algorithm_component_top_show_module import ClickableLabel
from LLMs.GUI.algorithm_component_export_report import ExportDialog
from LLMs.utils import BaseComponent
import importlib.util
import os

from LLMs.use_ollama.modes import DialogModes
from LLMs.business import task_planner_deepseek_instance, safe_parse

# 获取当前文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 自定义算法路径（上一级目录的functions文件夹）
CUSTOM_ALGO_PATH = os.path.abspath(os.path.join(current_dir, "../functions"))


class Prompter:
    def __init__(self):
        pass


class AlgoComponent(BaseComponent):
    """算法功能组件，用于动态加载和执行自定义算法"""

    def __init__(self, external_log_fn=None):
        """
        初始化算法组件
        :param external_log_fn: 外部日志记录函数，用于输出运行状态和结果
        """
        super().__init__()
        self.external_log_fn = external_log_fn  # 外部日志回调函数
        self.widget = QWidget()  # 主控件容器
        self.layout = QVBoxLayout(self.widget)  # 垂直布局

        # 初始化数据存储
        self.result_logs = []  # 存放所有执行结果
        self.functions = {}  # 存储算法函数 {name: function}
        self.descriptions = {}  # 存储算法说明 {name: description}
        self.types = {}  # 存储算法适用类型 {name: type}
        self.image_path = None  # 存储输入图像地址
        self.csv_path = None  # 存储输入表格地址
        self.requirements = None    # 存储输入的需求
        self.data = {
            "image": None,
            "csv": None
        }

        # 界面区域划分
        self.init_ui()
        # 加载注册的算法
        self.load_registry_and_functions()

        self._dialog_n = DialogModes(model="deepseek-r1")
        # self._dialog_c = DialogModes(model="deepseek-coder")

    def init_ui(self):
        """初始化界面布局，分为上、中、下三部分，固定比例 0.4/0.2/0.4，并用浅色区分"""

        """ 上部区域（用于显示图像+表格）"""
        self.top_area = QWidget()
        self.top_area.setStyleSheet("background-color: white;")
        self.top_layout = QHBoxLayout(self.top_area)  # 水平布局
        self.top_layout.setContentsMargins(0, 0, 0, 0)  # 去除边距
        self.top_layout.setSpacing(0)  # 去除部件间距

        # 左侧图像区域 - 使用QWidget作为容器
        self.image_container = QWidget()
        self.image_container.setLayout(QVBoxLayout())
        self.image_container.layout().setContentsMargins(0, 0, 0, 0)

        self.image_label = ClickableLabel("未上传图像")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_container.layout().addWidget(self.image_label)
        self.top_layout.addWidget(self.image_container, stretch=1)  # 宽度均分

        # 添加分隔线
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.VLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.top_layout.addWidget(self.separator)

        # 右侧表格区域 - 使用QWidget作为容器
        self.table_container = QWidget()
        self.table_container.setLayout(QVBoxLayout())
        self.table_container.layout().setContentsMargins(0, 0, 0, 0)

        self.table_widget = QTableWidget()
        self.table_widget.setStyleSheet("background-color: white;")
        self.table_widget.setColumnCount(0)
        self.table_widget.setRowCount(0)
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # 启用内置滚动条

        self.table_container.layout().addWidget(self.table_widget)
        self.top_layout.addWidget(self.table_container, stretch=1)  # 宽度均分

        # 区域加进主 layout
        self.layout.addWidget(self.top_area, stretch=4)  # 高度比例40%

        # 中部区域（上传图像/CSV输入）
        self.middle_area = QWidget()
        self.middle_area.setStyleSheet("background-color: #f0f0f0;")
        self.middle_layout = QVBoxLayout(self.middle_area)

        self.upload_label = QLabel()
        self.upload_label.setAlignment(Qt.AlignLeft)
        self.middle_layout.addWidget(self.upload_label)

        # 水平布局容器，用于放置上传和删除按钮
        self.upload_buttons_layout = QHBoxLayout()

        # 上传图像按钮
        self.image_button = QPushButton("上传图像")
        self.image_button.clicked.connect(self.upload_image)
        self.upload_buttons_layout.addWidget(self.image_button)

        # 删除图像按钮
        self.delete_image_button = QPushButton("删除图像")
        self.delete_image_button.clicked.connect(self.delete_image)
        self.upload_buttons_layout.addWidget(self.delete_image_button)

        # 上传CSV按钮
        self.csv_button = QPushButton("上传CSV文件")
        self.csv_button.clicked.connect(self.upload_csv)
        self.upload_buttons_layout.addWidget(self.csv_button)

        # 删除CSV文件按钮
        self.delete_csv_button = QPushButton("删除CSV文件")
        self.delete_csv_button.clicked.connect(self.delete_show_csv)
        self.upload_buttons_layout.addWidget(self.delete_csv_button)

        # 将水平按钮布局添加到中间区域的垂直布局中
        self.middle_layout.addLayout(self.upload_buttons_layout)

        # 文字输入框
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("或在此输入文字数据...")
        self.middle_layout.addWidget(self.text_input)

        # 获取输入内容按钮
        self.get_input_button = QPushButton("提交需求")
        self.get_input_button.clicked.connect(self.handle_get_input)
        self.middle_layout.addWidget(self.get_input_button)

        # 添加到主布局
        self.layout.addWidget(self.middle_area)

        """ 下部区域（预留）"""
        self.bottom_area = QWidget()
        self.bottom_area.setStyleSheet("background-color: white;")
        self.bottom_layout = QVBoxLayout(self.bottom_area)
        self.layout.addWidget(self.bottom_area)
        # 创建 QTextBrowser 来显示结构化的结果
        self.result_display = QTextBrowser()
        self.result_display.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; padding: 10px;")
        self.result_display.setOpenExternalLinks(True)  # 允许显示链接
        # 创建按钮
        self.export_button = QPushButton("导出报告")
        self.export_button.setStyleSheet("padding: 8px 16px; font-size:16px;")
        self.export_button.clicked.connect(self.show_export_dialog)

        # 将 result_display 添加到布局中
        self.bottom_layout.addWidget(self.result_display)
        self.bottom_layout.addWidget(self.export_button)
        self.layout.addWidget(self.bottom_area)

        # 设置区域高度比例（上:中:下 = 0.4:0.2:0.4）
        self.layout.setStretch(0, 4)
        self.layout.setStretch(1, 2)
        self.layout.setStretch(2, 4)

    def upload_image(self):
        """上传图像的回调"""
        file_path, _ = QFileDialog.getOpenFileName(self.widget, "选择图像文件", "", "Images (*.png *.jpg *.bmp)")
        if file_path:
            try:
                self.external_log_fn(f"[algo-component] 图像已上传: {file_path}")
                self.image_path = file_path

                # 在顶部区域显示图像
                pixmap = QPixmap(file_path)

                # 检查图像是否成功加载
                if pixmap.isNull():
                    raise ValueError("无法加载图像，可能是文件损坏或格式不支持")

                # 缩放图像以适应标签大小，同时保持宽高比
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width(),
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setText("")  # 清除"未上传图像"文本
                self.image_label.set_full_image(pixmap)  # 存储原始图像用于放大显示
                self.data["image"] = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), 1)

            except Exception as e:
                # 捕获异常并显示错误消息
                error_message = f"[algo-component] 图像加载失败: {str(e)}"
                self.external_log_fn(error_message)
                # 弹出错误提示框
                QMessageBox.critical(self.widget, "图像加载错误", error_message)

    def delete_image(self):
        """删除上传的图像"""
        if self.image_path:
            self.image_path = None
            # 清空图像标签显示
            self.image_label.delete_image()
            # 恢复默认文本（如果需要）
            self.image_label.setText("未上传图像")
            self.data["image"] = None
            # 记录日志
            self.external_log_fn("[algo-component] 图像已删除")
        else:
            self.external_log_fn("[algo-component] 没有图像可删除")

    def upload_csv(self):
        """上传CSV文件的回调"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self.widget,
                "选择CSV文件",
                "",
                "CSV Files (*.csv)"
            )
            if file_path:
                self.external_log_fn(f"[algo-component] CSV文件已上传: {file_path}")
                self.csv_path = file_path
                self.show_csv_in_table(file_path)
        except Exception as e:
            self.show_error_message("文件选择错误", f"无法选择CSV文件:\n{str(e)}")

    def delete_show_csv(self):
        """删除上传的CSV文件并清空表格"""
        try:
            if not self.csv_path:
                self.show_warning_message("没有文件", "没有上传CSV文件，无法删除")
                return

            # # 删除CSV文件
            # if os.path.exists(self.csv_path):
            #     os.remove(self.csv_path)
            #     self.external_log_fn(f"[algo-component] CSV文件已删除: {self.csv_path}")
            #     self.csv_path = None
            # else:
            #     self.show_warning_message("文件不存在", "指定的CSV文件不存在，无法删除")
            #     return

            # 清空表格显示
            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            self.external_log_fn("[algo-component] 删除成功，并清空表格显示")
            self.data["csv"] = None

        except Exception as e:
            self.show_error_message("删除失败", f"删除CSV文件时出错:\n{str(e)}")

    def show_csv_in_table(self, csv_path):
        """读取CSV文件并展示到表格"""
        from PyQt5.QtWidgets import QMessageBox
        import csv

        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"文件不存在: {csv_path}")

            file_size = os.path.getsize(csv_path) / (1024 * 1024)
            if file_size > 10:
                reply = QMessageBox.question(
                    self.widget,
                    "文件过大",
                    f"CSV文件较大({file_size:.2f}MB)，加载可能较慢，是否继续？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)

            # 读取CSV
            with open(csv_path, 'r', encoding='utf-8') as file:
                try:
                    data = list(csv.reader(file))
                except UnicodeDecodeError:
                    file.seek(0)
                    data = list(csv.reader(file, encoding='gbk'))

            if not data:
                self.show_warning_message("空文件", "CSV文件内容为空")
                return

            # 找到表头所在行（列数 ≥ 2 的第一行）
            header_row_index = None
            for idx, row in enumerate(data):
                if len(row) >= 5:
                    header_row_index = idx
                    break

            if header_row_index is None:
                self.show_warning_message("无表头", "CSV文件中未找到有效表格数据")
                return

            headers = data[header_row_index]
            col_count = len(headers)

            # 设置表格维度
            self.table_widget.setColumnCount(col_count)
            self.table_widget.setHorizontalHeaderLabels(headers)

            # 填充数据（从表头下一行开始）
            table_data = data[header_row_index + 1:]
            self.data["csv"] = table_data
            self.data["header"] = headers
            max_display_rows = 10000
            if len(table_data) > max_display_rows:
                self.show_warning_message(
                    "数据截断",
                    f"仅显示前{max_display_rows}行数据（共{len(table_data)}行）"
                )
                table_data = table_data[:max_display_rows]

            self.table_widget.setRowCount(len(table_data))

            for row_idx, row_data in enumerate(table_data):
                for col_idx in range(col_count):
                    value = row_data[col_idx] if col_idx < len(row_data) else ""
                    item = QTableWidgetItem(str(value))
                    self.table_widget.setItem(row_idx, col_idx, item)

            self.table_widget.resizeColumnsToContents()
            for col in range(self.table_widget.columnCount()):
                if self.table_widget.columnWidth(col) > 300:
                    self.table_widget.setColumnWidth(col, 300)

        except PermissionError:
            self.show_error_message("权限错误", "没有权限读取该文件")
        except UnicodeDecodeError:
            self.show_error_message("编码错误", "无法解码文件内容，请确保使用UTF-8或GBK编码")
        except csv.Error:
            self.show_error_message("CSV格式错误", "文件不符合CSV格式规范")
        except Exception as e:
            self.show_error_message("加载失败", f"无法加载CSV文件:\n{str(e)}")
        finally:
            self.table_widget.setSortingEnabled(True)

    def show_error_message(self, title, message):
        """显示错误消息弹窗"""
        QMessageBox.critical(
            self.widget,
            title,
            message,
            QMessageBox.Ok
        )
        self.external_log_fn(f"[algo-component][ERROR] {title}: {message}")

    def show_warning_message(self, title, message):
        """显示警告消息弹窗"""
        QMessageBox.warning(
            self.widget,
            title,
            message,
            QMessageBox.Ok
        )
        self.external_log_fn(f"[algo-component][WARN] {title}: {message}")

    def get_input_data(self):
        """
        获取中间区域的输入内容
        :return: 一个字典，包含文字内容、图像路径、CSV路径等
        """
        data = {
            "text": self.text_input.toPlainText(),  # 文本内容
            "image_path": getattr(self, "image_path", None),  # 上传的图像路径
            "csv_path": getattr(self, "csv_path", None)  # 上传的 CSV 路径
        }
        return data

    def handle_get_input(self) -> None:
        """
        获取用户输入，确认内容后根据上传的数据类型（图像或CSV）分发到对应的处理函数。

        Returns:
            None
        """
        input_data: Dict[str, Optional[str]] = self.get_input_data()
        if input_data['text'] is None or input_data['text'] == "":
            self.external_log_fn("[algo-component] 需求信息为空", "blue")
            return

        # 简单展示在日志中
        self.external_log_fn("[algo-component] 当前输入内容确认：")
        self.external_log_fn(f"[algo-component] 文本内容：{input_data['text']}")
        self.external_log_fn(f"[algo-component] 图像路径：{input_data['image_path']}")
        self.external_log_fn(f"[algo-component] CSV路径：{input_data['csv_path']}")

        if input_data['image_path'] is not None:
            self.task_image(input_data)
        elif input_data['csv_path'] is not None:
            self.task_csv(input_data)
        else:
            self.external_log_fn("[algo-component] 请先上传数据", "blue")

    def task_image(self, input_data: Dict[str, Optional[str]]) -> None:
        """
        处理图像路径相关任务，生成 prompt，通过多轮对话获取结果。

        Args:
            input_data (Dict[str, Optional[str]]): 包含用户文本需求、图像路径、CSV路径的输入数据字典。

        Returns:
            None
        """
        try:
            prompt: str = f"{task_planner_deepseek_instance.generate_image_prompt(user_requirement=input_data['text'])}"
            self.external_log_fn(f"[algo-component] {prompt}")

            result_json_str: str = self._dialog_n.multi_turn(
                user_input=prompt,
                show_thought=False
            )
            # 此处可扩展后续 JSON 解析、plan 执行逻辑

        except Exception as e:
            self.external_log_fn(f"[algo-component][阶段: 图像任务] 执行失败: {e}", "red")

    def task_csv(self, input_data: Dict[str, Optional[str]]) -> None:
        """
        处理 CSV 路径相关任务，生成 prompt，执行多轮对话、解析 JSON、生成 plan、执行任务及展示结果。

        Args:
            input_data (Dict[str, Optional[str]]): 包含用户文本需求、图像路径、CSV路径的输入数据字典。

        Returns:
            None
        """
        try:
            prompt: str = f"{task_planner_deepseek_instance.generate_csv_prompt(user_requirement=input_data['text'], csv_data=self.data['csv'][1:5], csv_header=self.data['header'])}"
            self.external_log_fn(f"[algo-component] {prompt}")

            result_json_str: str = self._dialog_n.multi_turn(
                user_input=prompt,
                show_thought=False
            )
            self.external_log_fn(f"[algo-component] {result_json_str}")

            # 提取 JSON 部分并清洗
            try:
                json_part: str = result_json_str.split("```json", 1)[1]
                json_cleaned_str: str = re.sub(r"```|\bjson\b", "", json_part).strip()
                result_json_cleaned: Optional[Dict[str, Any]] = safe_parse(json_cleaned_str)

                if result_json_cleaned is None:
                    raise ValueError("无法解析的 JSON 数据")

            except Exception as e:
                self.external_log_fn(f"[algo-component][阶段: JSON解析] 任务无法处理: {e}", "red")
                return

            # 解析任务
            try:
                plan: Dict[str, Any] = task_planner_deepseek_instance.parse_result(result_json_cleaned)
            except Exception as e:
                self.external_log_fn(
                    f"[algo-component][阶段: 任务解析] 任务解析失败，原始内容:\n{result_json_cleaned}\n异常: {e}", "red")
                return

            self.external_log_fn("[algo-component] 任务生成完成，进入任务执行阶段")

            # 执行任务
            try:
                result_dict: Dict[str, Any] = task_planner_deepseek_instance.execute_plan(
                    plan,
                    data=self.data["csv"],
                    header=self.data["header"]
                )
            except Exception as e:
                self.external_log_fn(f"[algo-component][阶段: 任务执行] 执行失败: {e}", "red")
                return

            # 展示结果
            try:
                self.display_function_run_result(result_dict, user_requirement=input_data['text'])
            except Exception as e:
                self.external_log_fn(f"[algo-component][阶段: 结果展示] 展示失败: {e}", "red")
                return

        except Exception as e:
            self.external_log_fn(f"[algo-component][阶段: CSV任务] 执行失败: {e}", "red")

    def display_function_run_result(self, result_dict: Dict, user_requirement: str):
        """追加方式展示新结果"""
        self.result_logs.append([result_dict, user_requirement])
        result_str = self.format_all_results()
        self.result_display.setHtml(result_str)

    def format_all_results(self):
        """将所有执行结果格式化为 HTML 字符串"""
        result_str = """
            <div style="font-size:18px;">
                <h3>执行结果记录：</h3>
        """
        for idx, [result_dict, user_requirement] in enumerate(self.result_logs, 1):
            result_str += f"""
                <div style="border:1px solid #ccc; padding:8px; margin:8px 0; border-radius:6px;">
                    <input type="checkbox" id="result_{idx}">
                    <label for="result_{idx}"><b>第 {idx} 次执行 —— 问题：{user_requirement}</b></label><br>
            """
            for name, res in result_dict.items():
                result_str += f"<b>系统执行的功能：{name}</b><br>"
                if isinstance(res, dict):
                    result_str += "<ul>"
                    for key, value in res.items():
                        result_str += f"<li>{key}: {value}</li>"
                    result_str += "</ul>"
                else:
                    result_str += f"<i>{res}</i><br>"
            result_str += "</div>"

        result_str += "</div>"
        return result_str

    def get_widget(self):
        """返回主控件对象"""
        return self.widget

    def update(self, data):
        """
        更新输入数据
        :param data: 需要算法处理的数据
        """
        self.input_data = data

    def load_registry_and_functions(self):
        """
        动态加载上级目录functions/__init__.py中的注册算法
        流程：
        1. 定位注册文件
        2. 动态加载注册模块
        3. 遍历算法目录加载注册过的算法
        """
        # 获取注册文件绝对路径
        functions_dir = os.path.abspath(os.path.join(current_dir, "../functions"))
        registry_path = os.path.join(functions_dir, "__init__.py")

        if not os.path.exists(registry_path):
            self.external_log_fn(f"[algo-component] 未找到算法注册文件: {registry_path}")
            return

        try:
            # 动态加载模块
            spec = importlib.util.spec_from_file_location("functions.registry", registry_path)
            registry_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(registry_module)

            # 从模块获取注册表字典（默认为空字典）
            registry = getattr(registry_module, "registry", {})

            # 加载已注册的算法
            for file in os.listdir(functions_dir):
                if file.endswith(".py") and not file.startswith('_'):  # 跳过隐藏文件和__pycache__
                    name = file[:-3]  # 去除.py后缀
                    if name in registry:  # 只加载注册过的算法
                        self.load_function(name)

        except Exception as e:
            self.external_log_fn(f"[algo-component] 加载算法注册失败: {str(e)}", color="red")

    def load_function(self, name):
        """
        加载单个算法模块
        :param name: 算法模块名称（不带.py后缀）
        """
        # 构建算法文件完整路径
        path = os.path.join(CUSTOM_ALGO_PATH, f"{name}.py")

        # 动态导入算法模块
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 存储算法函数和说明
        self.functions[name] = module.run  # 假设每个算法模块都有run函数
        self.descriptions[name] = getattr(module, "description", "无说明")
        self.types[name] = getattr(module, "type_", "无说明")

        """ 注册算法 """
        task_planner_deepseek_instance.upload(
            functions=self.functions,
            descriptions=self.descriptions,
            types=self.types
        )
        self.external_log_fn(message=f"[algo-component] 加载 Function： {name} 成功", color="gray")

    def get_data(self):
        return self.data

    def get_functions(self):
        return self.functions, self.descriptions, self.types

    def show_export_dialog(self):
        dialog = ExportDialog(self.result_logs)
        dialog.exec_()
