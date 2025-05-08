# ---------------- 中间区域组件衔接基类及注册 ----------------

class BaseComponent:
    def __init__(self):
        self._widget = None  # 统一widget管理

    def get_widget(self):
        if self._widget is None:
            self._widget = self._create_widget()
        return self._widget

    def _create_widget(self):
        """子类必须实现真正的控件创建"""
        raise NotImplementedError

    def cleanup(self):
        """可选：用于释放资源"""
        pass