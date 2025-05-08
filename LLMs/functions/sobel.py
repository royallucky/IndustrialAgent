type_ = "image"
description = "计算输入数据的平均值。参数1: data: List[Union[int, float]], 任意一维的列表数据"

from typing import List, Union

def run(data: List[Union[int, float]]) -> float:
    return sum(data) / len(data) if data else 0.0
