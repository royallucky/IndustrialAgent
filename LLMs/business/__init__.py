from LLMs.business.algorithm_component_prompt import TaskPlannerForDeepSeek  # 相对导入当前目录的模块
from LLMs.business.parse_str_2_json import safe_parse

# 实例化对象
task_planner_deepseek_instance = TaskPlannerForDeepSeek()  # 可以在这里初始化参数

# 暴露实例对象（而不是类）
__all__ = ['task_planner_deepseek_instance', 'safe_parse']  # 注意这里是实例的变量名
