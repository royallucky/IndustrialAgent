from typing import Dict, Any, List

import numpy as np


class TaskPlannerForDeepSeek:
    """
    工业图像AI检测任务规划器，基于注册算法及用户需求，生成DeepSeek Prompt，并解析结果调度方案。
    """

    def __init__(self) -> None:
        self.functions = {}
        self.descriptions = {}
        self.types = {}

    def upload(self, functions: Dict[str, Any], descriptions: Dict[str, str], types: Dict[str, str]):
        """
        初始化任务规划器

        Args:
            functions (Dict[str, Any]): 注册算法函数接口 {name: function}
            descriptions (Dict[str, str]): 算法功能描述 {name: description}
            types (Dict[str, str]): 算法所属类型 {name: type}
        """
        self.functions = functions
        self.descriptions = descriptions
        self.types = types

    def generate_image_prompt(self, user_requirement: str, image_data: np.ndarray=None) -> str:
        """
        根据用户需求，生成 DeepSeek prompt。

        Args:
            user_requirement (str): 用户需求描述
            image_data (np.ndarray): 图像数据
        Returns:
            str: prompt字符串
        """
        algorithm_info = ""
        for name in self.functions.keys():
            full_desc = self.descriptions.get(name, "无描述")
            type_ = self.types.get(name, "通用")

            # 只保留 type_ 包含 'image' 的
            if "image" not in type_:
                continue

            # 拆分功能说明和参数说明
            if "参数" in full_desc:
                func_desc, param_desc = full_desc.split("参数", 1)
                param_desc = "参数" + param_desc  # 补回‘参数’字样
            else:
                func_desc = full_desc
                param_desc = "无参数说明"

            algorithm_info += f"- 名称：{name}\n  类型：{type_}\n  功能说明：{func_desc.strip()}\n  参数说明：{param_desc.strip()}\n\n"

        prompt = f"""
    你是一个工业AI检测系统的规划专家，擅长根据用户需求，自动规划检测任务所需的算法和AI模型。
以下是系统中当前可用的算法/模型：

{algorithm_info}

【用户需求】：{user_requirement}

请你完成以下任务：
1. 从【系统注册算法/模型】中，筛选出本次检测任务需要用到的算法/模型名称
2. 确定这些算法/模型的执行顺序（1、2、3…）
3. 给出每个算法/模型的推荐参数（如阈值、置信度、缺陷尺寸、检测区域）

务必以如下 JSON 格式输出，不要增删任何字段：

```json
{{
  "检测任务规划": [
    {{
      "算法/模型名称": "",
      "执行顺序": 1,
      "推荐参数": {{}}
    }}
  ]
}}
"""
        return prompt

    def generate_csv_prompt(self, user_requirement: str, csv_data: List[List[Any]], csv_header: List[str]) -> str:
        """
        根据用户需求和CSV数据，生成 DeepSeek prompt。

        Args:
            user_requirement (str): 用户需求描述
            csv_data (List[List[Any]]): csv表的数据
            csv_header (List[str]): 表头字段

        Returns:
            str: prompt字符串
        """
        algorithm_info = ""
        for name in self.functions.keys():
            full_desc = self.descriptions.get(name, "无描述")
            type_ = self.types.get(name, "通用")

            # 只保留 type_ 包含 'table' 的
            if "table" not in type_:
                continue

            # 拆分功能说明和参数说明
            if "参数" in full_desc:
                func_desc, param_desc = full_desc.split("参数", 1)
                param_desc = "参数" + param_desc  # 补回‘参数’字样
            else:
                func_desc = full_desc
                param_desc = "无参数说明"

            algorithm_info += f"- 名称：{name}\n  类型：{type_}\n  功能说明：{func_desc.strip()}\n  参数说明：{param_desc.strip()}\n\n"

        if not csv_data or not isinstance(csv_data, list) or not csv_data[0]:
            raise ValueError("CSV数据不能为空，且必须包含表头！")

        sample_rows = csv_data[1:3] if len(csv_data) > 1 else []

        # 格式化表头+示例数据
        sample_data_str = " | ".join(csv_header) + "\n"
        for row in sample_rows:
            sample_data_str += " | ".join(map(str, row)) + "\n"

        prompt = f"""
你是一个工业数据分析AI系统规划专家，擅长根据用户需求、数据表结构、示例数据和系统已注册算法/模型，规划合理、可落地的分析执行方案。

请严格按照以下步骤执行：

【当前可用算法/模型信息】：  
{algorithm_info}

【数据表结构】：  
字段：{csv_header}

【示例数据（前2行）】：  
{sample_data_str.strip()}

【用户需求】：  
{user_requirement}

---

请依次完成以下任务：

1. 判断需求是否可实现：
- 如果可行性低于0.7，直接回复："暂时无法处理"
- 若可行，继续执行

2. 从【当前可用算法/模型信息】中，筛选本次检测任务需要调用的最相关的1个算法/模型，列出名称

3. 为每个算法/模型生成推荐参数：
- **固定参数 data 和 header 不需要列出**
- **所有其它参数必须给出有效、合理、可执行的值**
- **严禁出现空值、说明文字、缺失，严禁无意义填写**
- 参数值必须基于【用户需求】【数据表结构】【示例数据】推导得出  
- **若某算法的非固定参数无合理值可推导，直接剔除此算法，不允许保留空字典**

4. 将最终结果按如下 JSON 格式输出，禁止多余注释、说明或解释：

```json
{{
  "检测任务规划": [
    {{
      "算法/模型名称": "",
      "推荐参数": {{}}
    }}
  ]
}}"""
        return  prompt

    def parse_result(self, result_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析 DeepSeek 返回的任务规划结果，并剔除无效任务。

        Args:
            result_json (Dict[str, Any]): DeepSeek 返回的 JSON 格式规划结果

        Returns:
            List[Dict[str, Any]]: 含顺序、算法、推荐参数的有效执行计划列表，按执行顺序排序
        """
        # 获取检测任务规划
        task_plan = result_json.get("检测任务规划", [])
        if not task_plan:
            raise ValueError("检测任务规划结果为空或格式不正确！")

        valid_tasks = []

        for task in task_plan:
            # 校验必需字段
            if "算法/模型名称" not in task:
                continue
            if "推荐参数" not in task:
                continue

            # 剔除推荐参数为空的任务
            if not task["推荐参数"]:
                continue

            # 全部校验通过，加入有效任务列表
            valid_tasks.append(task)

        if not valid_tasks:
            raise ValueError("检测任务规划中无有效任务！")

        # 按照执行顺序排序
        sorted_plan = sorted(valid_tasks, key=lambda x: x.get("执行顺序", 0))
        return sorted_plan

    def execute_plan(self,
                     plan: List[Dict[str, Any]],
                     data: List[List] = None,
                     header: List[str] = None) -> Dict[str, Any]:
        """按规划执行算法，依次调用注册函数。
        Args:
            plan (List[Dict[str, Any]]): 执行计划列表
            data: List[List]  表格分析型任务（每行一个数据行）
            header: List[str] 表格分析型任务（表头字段名列表）
        Returns:
            Dict[str, Any]: 各算法执行结果字典
        Raises:
            Exception: 执行过程中遇到的所有异常
        """
        results = {}
        for task in plan:
            name = task["算法/模型名称"]
            params = task["推荐参数"]

            if name in self.functions:
                if data is not None:
                    params["data"] = data
                    params["header"] = header

                print(f"开始执行算法 {name}")

                try:
                    result = self.functions[name](**params)
                    results[name] = result if result is not None else "No result"

                except Exception as e:
                    error_msg = f"算法 {name} 执行异常：{str(e)}"
                    raise RuntimeError(error_msg) from e

            else:
                results[name] = "Not registered"

        return results


