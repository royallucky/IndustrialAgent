from LLMs.functions.tools import normalize_header

type_ = "table"
description = "对表格数据中指定多列计算相关性。参数1: data: List[List], 表格数据；参数2: header: List, 表头字段；参数3: target_columns: List[str], 要计算相关性的列名列表；参数4: method: str, 相关系数计算方法，可选 'pearson' / 'spearman' / 'kendall'"

from typing import List, Dict, Any
import numpy as np
from scipy.stats import pearsonr, spearmanr, kendalltau

def run(data: List[List], header: List[str], target_columns: List[str], method: str = "pearson") -> Dict[str, Any]:
    """
    对表格数据中指定多列计算相关性（可选皮尔逊、斯皮尔曼、肯德尔秩相关系数）

    Args:
        data (List[List]): 表格数据，每行为一个数据行
        header (List[str]): 表头字段名列表
        target_columns (List[str]): 要计算相关性的列名列表
        method (str): 相关系数计算方法，支持 'pearson' / 'spearman' / 'kendall'

    Returns:
        Dict[str, Any]: 指定方法的相关系数矩阵字典，或错误信息
    """
    # 参数合法性校验
    if not data or not header:
        return {"error": "无效输入，data 或 header 为空"}

    # 统一表头和目标列
    header = normalize_header(header)
    target_columns = normalize_header(target_columns)

    if not target_columns or not all(col in header for col in target_columns):
        return {"error": "target_columns 中存在不在 header 中的列名"}

    if method not in ("pearson", "spearman", "kendall"):
        return {"error": f"不支持的相关性计算方法：{method}"}

    try:
        # 获取目标列的索引
        col_indices = [header.index(col) for col in target_columns]

        # 提取目标列数据，过滤空值和非法值，统一为float类型
        extracted_data = []
        for row in data:
            try:
                values = [float(row[idx]) if row[idx] not in ("", None) else np.nan for idx in col_indices]
                extracted_data.append(values)
            except (ValueError, TypeError):
                extracted_data.append([np.nan] * len(col_indices))

        extracted_data = np.array(extracted_data, dtype=np.float64)

        # 删除含有 NaN 的行
        valid_data = extracted_data[~np.isnan(extracted_data).any(axis=1)]

        if valid_data.shape[0] < 2:
            return {"error": "有效数据不足，无法计算相关性（至少需要两行完整数据）"}

        # 定义计算方法映射
        method_funcs = {
            "pearson": pearsonr,
            "spearman": spearmanr,
            "kendall": kendalltau
        }

        corr_func = method_funcs[method]

        # 初始化结果字典
        result = {
            "目标列名": target_columns,
            "相关性方法": method,
            "相关性结果": {}
        }

        num_cols = len(target_columns)
        for i in range(num_cols):
            for j in range(i+1, num_cols):
                col_x = valid_data[:, i]
                col_y = valid_data[:, j]

                try:
                    corr_value, _ = corr_func(col_x, col_y)
                except Exception:
                    corr_value = None

                key = f"{target_columns[i]} vs {target_columns[j]}"
                result["相关性结果"][key] = float(corr_value)

        return result

    except Exception as e:
        return {"error": f"计算异常：{str(e)}"}



"""
    {
  "target_columns": ["A", "B", "C"],
  "method": "spearman",
  "correlations": {
    "A vs B": 0.8823,
    "A vs C": -0.2114,
    "B vs C": 0.0457
  }
}

"""