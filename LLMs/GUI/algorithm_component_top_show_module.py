from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QPixmap, QGuiApplication, QCursor
from PyQt5.QtWidgets import QLabel, QMessageBox, QScrollArea, QDialog, QVBoxLayout


class ClickableLabel(QLabel):
    """可点击的标签控件，用于显示图像并支持点击放大功能"""
    clicked = pyqtSignal()  # 点击信号，当标签被点击时发射

    def __init__(self, text=None, parent=None):
        """
        初始化可点击标签

        Args:
            text (str, optional): 标签初始文本. Defaults to None.
            parent (QWidget, optional): 父级控件. Defaults to None.
        """
        super().__init__(text, parent)
        self.full_image = None  # 存储原始完整图像
        self.drag_start_position = None  # 拖动起始位置
        self.dialog = None  # 悬浮对话框引用

    def mousePressEvent(self, event):
        """
        鼠标按下事件处理

        Args:
            event (QMouseEvent): 鼠标事件对象
        """
        try:
            if event.button() == Qt.LeftButton:
                self.clicked.emit()  # 发射点击信号
                self.show_full_image()  # 显示完整图像
        except Exception as e:
            QMessageBox.critical(self, "错误", f"图像显示失败: {str(e)}")

    def set_full_image(self, pixmap):
        """
        设置完整图像

        Args:
            pixmap (QPixmap): 要设置的完整图像

        Raises:
            TypeError: 如果参数不是QPixmap类型
        """
        if not isinstance(pixmap, QPixmap):
            raise TypeError("参数必须是QPixmap类型")
        self.full_image = pixmap

    def show_full_image(self):
        """显示完整尺寸的图像对话框"""
        try:
            # 检查是否有有效图像
            if not self.full_image or self.full_image.isNull():
                QMessageBox.warning(self, "提示", "没有可显示的图像")
                return

            # 如果已有对话框，先关闭
            if self.dialog and self.dialog.isVisible():
                self.dialog.close()

            # 创建悬浮对话框
            self.dialog = QDialog()
            self.dialog.setWindowTitle("放大图像 (可拖动)")
            # 设置窗口标志：置顶且无边框
            self.dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

            # 创建滚动区域以支持大图像查看
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)  # 允许小部件调整大小

            # 创建显示完整图像的标签
            self.image_label = QLabel()
            self.image_label.setPixmap(self.full_image)
            self.image_label.setAlignment(Qt.AlignCenter)

            # 获取屏幕可用尺寸
            screen = QGuiApplication.primaryScreen()
            if not screen:
                raise RuntimeError("无法获取屏幕信息")

            screen_geometry = screen.availableGeometry()
            max_width = screen_geometry.width() * 0.8  # 最大宽度为屏幕宽度的80%
            max_height = screen_geometry.height() * 0.8  # 最大高度为屏幕高度的80%

            # 获取原始图像尺寸
            img_size = self.full_image.size()

            # 如果图像大于最大允许尺寸，则进行缩放
            if img_size.width() > max_width or img_size.height() > max_height:
                scaled_size = img_size.scaled(
                    QSize(round(max_width), round(max_height)),
                    Qt.KeepAspectRatio  # 保持宽高比
                )
                scaled_pixmap = self.full_image.scaled(
                    scaled_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation  # 平滑变换
                )
                self.image_label.setPixmap(scaled_pixmap)
                img_size = scaled_pixmap.size()

            # 设置对话框大小（添加20像素边距防止紧贴屏幕边缘）
            dialog_width = min(img_size.width() + 20, screen_geometry.width())
            dialog_height = min(img_size.height() + 20, screen_geometry.height())
            self.dialog.resize(dialog_width, dialog_height)

            # 设置对话框居中显示
            center_point = screen_geometry.center()
            self.dialog.move(
                int(center_point.x() - dialog_width / 2),
                int(center_point.y() - dialog_height / 2)
            )

            # 重写鼠标事件处理函数以实现拖动
            self.image_label.mousePressEvent = self.image_mouse_press
            self.image_label.mouseMoveEvent = self.image_mouse_move
            self.image_label.mouseReleaseEvent = self.image_mouse_release

            # 将图像标签添加到滚动区域
            scroll_area.setWidget(self.image_label)

            # 设置对话框布局
            layout = QVBoxLayout(self.dialog)
            layout.addWidget(scroll_area)
            layout.setContentsMargins(0, 0, 0, 0)  # 去除边距

            self.dialog.exec_()  # 模态显示对话框

        except Exception as e:
            QMessageBox.critical(self, "错误", f"图像显示失败: {str(e)}")
            if self.dialog:
                self.dialog.close()

    def image_mouse_press(self, event):
        """
        图像标签鼠标按下事件处理（用于拖动对话框）

        Args:
            event (QMouseEvent): 鼠标事件对象
        """
        try:
            if event.button() == Qt.LeftButton and self.dialog:
                # 计算拖动起始位置（全局坐标 - 对话框位置）
                self.drag_start_position = event.globalPos() - self.dialog.pos()
                self.image_label.setCursor(QCursor(Qt.ClosedHandCursor))  # 设置手型光标
        except:
            pass

    def image_mouse_move(self, event):
        """
        图像标签鼠标移动事件处理（用于拖动对话框）

        Args:
            event (QMouseEvent): 鼠标事件对象
        """
        try:
            if (self.drag_start_position is not None and
                    self.dialog and
                    event.buttons() & Qt.LeftButton):
                # 移动对话框到新位置
                self.dialog.move(event.globalPos() - self.drag_start_position)
        except:
            pass

    def image_mouse_release(self, event):
        """
        图像标签鼠标释放事件处理（结束拖动）

        Args:
            event (QMouseEvent): 鼠标事件对象
        """
        try:
            if event.button() == Qt.LeftButton:
                self.drag_start_position = None  # 清除拖动起始位置
                self.image_label.setCursor(QCursor(Qt.ArrowCursor))  # 恢复默认光标
        except:
            pass

    def delete_image(self):
        """删除上传的图像"""
        try:
            if self.full_image:
                # 清空图像标签显示
                self.setPixmap(QPixmap())  # 清空当前的图片
                self.setText("未上传图像")  # 恢复默认文本
                self.full_image = None  # 清空完整图像

                # 如果有额外的路径变量，清空图像路径（假设使用 self.image_path 存储路径）
                if hasattr(self, 'image_path'):
                    self.image_path = None

            else:
                pass
                # self.external_log_fn("没有图像可删除")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除图像失败: {str(e)}")