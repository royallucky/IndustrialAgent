from LLMs.functions.tools import normalize_header

type_ = "table"
description = (
    "对表格数据进行关联规则挖掘，找出频繁项集及其之间的关联规则。"
    "参数1: data: List[List], 表格数据；"
    "参数2: header: List, 表头字段；"
    "参数3: target_columns: List[str], 要参与挖掘的列名"
)

from typing import List, Dict, Any
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules


def run(data: List[List], header: List[str], target_columns: List[str]) -> Dict[str, Any]:
    """
    对表格数据进行关联规则挖掘

    Args:
        data (List[List]): 表格数据，每行为一个数据行
        header (List[str]): 表头字段名列表
        target_columns (List[str]): 要参与挖掘的列名

    Returns:
        Dict[str, Any]: 包含频繁项集和关联规则结果
    """
    if not data or not header or not target_columns:
        return {"error": "无效输入，data/header/target_columns 不能为空"}

    # 统一规范化表头和目标列名
    norm_header = normalize_header(header)
    norm_target_columns = normalize_header(target_columns)

    for col in norm_target_columns:
        if col not in norm_header:
            return {"error": f"目标列 {col} 不存在于表头中"}

    df = pd.DataFrame(data, columns=norm_header)

    # 只保留目标列
    df = df[norm_target_columns]

    # 将非空转为布尔型（适合做 one-hot 编码，或简单二值化）
    df = df.notnull()

    # 频繁项集挖掘
    freq_items = apriori(df, min_support=0.2, use_colnames=True)

    if freq_items.empty:
        return {"error": "未发现满足条件的频繁项集"}

    # 关联规则挖掘
    rules = association_rules(freq_items, metric="lift", min_threshold=1.0)

    if rules.empty:
        return {"error": "未发现满足条件的关联规则"}

    result = {
        "频繁项集数量": len(freq_items),
        "关联规则数量": len(rules),
        "频繁项集": freq_items.to_dict(orient="records"),
        "关联规则": rules[["antecedents", "consequents", "support", "confidence", "lift"]].to_dict(orient="records"),
    }

    return result
