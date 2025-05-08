from typing import List, Tuple, Dict, Any

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QFileDialog
from PyQt5.QtGui import QTextDocument, QFont
from PyQt5.QtPrintSupport import QPrinter

class ExportDialog(QDialog):
    def __init__(self, result_logs: List[Tuple[Dict[str, Any], str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择要导出的执行结果")
        self.result_logs = result_logs
        self.export_checkboxes = []

        layout = QVBoxLayout(self)

        for idx, (result_dict, user_requirement) in enumerate(self.result_logs, 1):
            checkbox = QCheckBox(f"第 {idx} 次执行 —— 问题：{user_requirement}")
            layout.addWidget(checkbox)
            self.export_checkboxes.append((checkbox, idx-1))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.export_selected_results)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def export_selected_results(self):
        selected_indices = [idx for checkbox, idx in self.export_checkboxes if checkbox.isChecked()]

        if not selected_indices:
            self.reject()
            return

        export_html = "<h2>执行结果导出</h2>"
        export_html += f"<p>共导出 {len(selected_indices)} 条执行记录。</p>"

        for i, idx in enumerate(selected_indices, 1):
            result_dict, user_requirement = self.result_logs[idx]
            export_html += f"<h3>第 {i} 条 —— 问题：{user_requirement}</h3>"
            for name, res in result_dict.items():
                export_html += f"<b>功能：</b>{name}<br>"
                if isinstance(res, dict):
                    export_html += "<ul>"
                    for key, value in res.items():
                        export_html += f"<li>{key}: {value}</li>"
                    export_html += "</ul>"
                else:
                    export_html += f"<i>{res}</i><br>"
            export_html += "<hr>"

        filename, _ = QFileDialog.getSaveFileName(self, "保存 PDF 文件", "", "PDF Files (*.pdf)")
        if filename:
            self.save_html_to_pdf(export_html, filename)

        self.accept()

    def save_html_to_pdf(self, html_content, filename):
        document = QTextDocument()
        document.setHtml(html_content)
        font = QFont("SimSun", 12)
        document.setDefaultFont(font)

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)

        document.print_(printer)
