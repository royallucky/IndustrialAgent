from LLMs.functions.tools import normalize_header

type_ = "table"
description = "对表格数据中指定列计算统计值，如均值、方差、中位数、最大值、最小值等。参数1: data: List[List], 表格数据；参数2: header: List, 表头字段；参数3: target_column: str, 要统计的列名"

from typing import List, Union, Dict, Any
import statistics

def run(data: List[List], header: List[str], target_column: str) -> Dict[str, Any]:
    """
    对表格数据中指定列计算统计值

    Args:
        data (List[List]): 表格数据，每行为一个数据行
        header (List[str]): 表头字段名列表
        target_column (str): 要统计的列名

    Returns:
        Dict[str, Any]: 包含均值、中位数、方差、最大值、最小值、非空数量的统计结果字典
    """
    # 统一表头和目标列
    header = normalize_header(header)
    target_column = normalize_header([target_column])[0]

    if not data or not header or target_column not in header:
        return {"error": "无效输入，data 或 header 为空，或 target_column 不存在于 header 中"}

    col_index = header.index(target_column)
    values = []

    # 遍历数据，跳过无效值的行
    for row in data:
        value = row[col_index]

        try:
            # 尝试将字符串转换为数字
            value = float(value) if value not in ("", None) else None
        except ValueError:
            # 如果转换失败，跳过该行
            value = None

        if value is not None:  # 只有当值有效时才添加到统计中
            values.append(value)

    if not values:
        return {"error": f"{target_column} 列中无有效数值"}

    result = {
        "目标列名": target_column,
        "有效值计数": len(values),
        "均值": sum(values) / len(values),
        "中位数": statistics.median(values),
        "方差": statistics.variance(values) if len(values) > 1 else 0.0,
        "最小值": min(values),
        "最大值": max(values)
    }

    return result
