import os
import json
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QDialog, QFormLayout, QLineEdit, QRadioButton, QDialogButtonBox, QHeaderView
)
from PyQt5.QtCore import Qt

from LLMs.utils import BaseComponent
from datetime import datetime


class TableComponent(BaseComponent):
    """表格展示组件"""

    def __init__(self, json_dir="./data/jsons", log_path="./table_edit_log.txt"):
        self.json_dir = json_dir
        self.log_path = log_path
        self.current_file = None
        self.data = []

        self.label = QWidget()
        self.layout = QVBoxLayout()
        self.label.setLayout(self.layout)

        # 选择文件下拉框
        self.file_selector = QComboBox()
        self.file_selector.currentIndexChanged.connect(self.load_selected_file)
        self.layout.addWidget(self.file_selector)

        # 表格展示区
        self.table = QTableWidget()
        # 设置列宽度自动填满整个表格区域
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加")
        self.btn_delete = QPushButton("删除")
        self.btn_save = QPushButton("保存修改")
        self.btn_add.clicked.connect(self.add_row)
        self.btn_delete.clicked.connect(self.delete_selected_row)
        self.btn_save.clicked.connect(self.save_edits)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_save)
        self.layout.addLayout(btn_layout)

        self.load_file_list()

        self.btn_new = QPushButton("新建文件")
        self.btn_new.clicked.connect(self.create_new_file)
        btn_layout.addWidget(self.btn_new)

    def get_name(self):
        return "Table"

    def get_widget(self):
        return self.label

    def update(self, data):
        # QMessageBox.information(None, "更新", "表格组件接收到更新请求: {}".format(data))
        pass

    def load_file_list(self):
        """加载JSON文件列表"""
        if not os.path.exists(self.json_dir):
            os.makedirs(self.json_dir)
        files = [f for f in os.listdir(self.json_dir) if f.endswith(".json")]
        self.file_selector.clear()
        self.file_selector.addItems(files)

    def load_selected_file(self):
        """加载选中的JSON文件"""
        filename = self.file_selector.currentText()
        if not filename:
            return
        self.current_file = os.path.join(self.json_dir, filename)
        with open(self.current_file, "r", encoding="utf-8") as f:
            try:
                json_data = json.load(f)
                # 支持QA或多轮格式
                if isinstance(json_data, list):
                    self.data = self._parse_data(json_data)
                    self.show_table()
            except Exception as e:
                QMessageBox.warning(None, "加载错误", f"加载JSON失败：{str(e)}")

    def _parse_data(self, json_data):
        """统一处理QA或多轮格式为标准结构"""
        result = []
        for item in json_data:
            if "SEMI_S2_QA" in item:
                result.extend(item["SEMI_S2_QA"])
            elif "question" in item and "answer" in item:
                result.append(item)
        return result

    def show_table(self):
        self.table.clear()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["问题", "回答"])
        self.table.setRowCount(len(self.data))
        for i, qa in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(qa.get("question", "")))
            self.table.setItem(i, 1, QTableWidgetItem(qa.get("answer", "")))
        self.table.resizeColumnsToContents()

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem("新问题"))
        self.table.setItem(row, 1, QTableWidgetItem("新回答"))
        self.data.append({"question": "新问题", "answer": "新回答"})
        self._async_save("添加")

    def delete_selected_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            del self.data[row]
            self._async_save("删除")

    def save_edits(self):
        for i in range(self.table.rowCount()):
            question = self.table.item(i, 0).text() if self.table.item(i, 0) else ""
            answer = self.table.item(i, 1).text() if self.table.item(i, 1) else ""
            self.data[i] = {"question": question, "answer": answer}
        self._async_save("修改")

    def _async_save(self, action="更新"):
        """异步写入文件和日志"""
        def _write():
            try:
                with open(self.current_file, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                self._write_log(action, self.current_file)
            except Exception as e:
                self._write_log(f"写入失败: {str(e)}", self.current_file)

        threading.Thread(target=_write).start()

    def _write_log(self, action, file):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {action} => {file}\n")

    def create_new_file(self):
        dialog = QDialog()
        dialog.setWindowTitle("新建 知识 文件")

        layout = QFormLayout(dialog)
        name_edit = QLineEdit()
        radio_qa = QRadioButton("QA 格式")
        radio_dialog = QRadioButton("多轮对话格式")
        radio_qa.setChecked(True)

        layout.addRow("文件名（不含后缀）:", name_edit)
        layout.addRow("格式选择:", radio_qa)
        layout.addRow("", radio_dialog)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        def accept():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(None, "错误", "文件名不能为空")
                return
            filename = os.path.join(self.json_dir, f"{name}.json")
            if os.path.exists(filename):
                QMessageBox.warning(None, "错误", "文件已存在")
                return
            # 结构初始化
            if radio_qa.isChecked():
                content = []
            else:
                content = [{"SEMI_S2_QA": []}]
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
                self._write_log("新建", filename)
                self.load_file_list()
                index = self.file_selector.findText(f"{name}.json")
                self.file_selector.setCurrentIndex(index)
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(None, "错误", f"创建失败：{str(e)}")

        button_box.accepted.connect(accept)
        button_box.rejected.connect(dialog.reject)
        dialog.exec_()
