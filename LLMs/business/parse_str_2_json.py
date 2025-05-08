import json
from typing import Optional, Any, Union


def safe_parse(json_str: str) -> Optional[Any]:
    """
    尝试解析 JSON 字符串，并将无法解析的 Python 特定类型替换为 null。
    同时剔除所有 key 为 'data' 和 'header' 的键值对。

    参数:
        json_str (str): 需要解析的 JSON 字符串。

    返回:
        Optional[Any]: 如果解析成功，返回清洗后的 dict 或 list。如果解析失败，返回 None。
    """
    try:
        # 将字符串按行拆分
        lines = json_str.splitlines()
        # 查找包含 "data" 的行及其后两行，删除这些行
        cleaned_lines = []
        skip_lines = 0

        for line in lines:
            if skip_lines > 0:
                skip_lines -= 1
                continue
            if '"data"' in line:
                if '"header"' in line:
                    skip_lines = 2  # 找到 "data" 后，跳过当前行及后两行
                else:
                    skip_lines = 1
                continue
            else:
                if '"header"' in line:
                    skip_lines = 1
                    continue
            cleaned_lines.append(line)

        # 合并清理后的行
        cleaned_json_str = "\n".join(cleaned_lines)
        # 尝试解析 JSON
        parsed = json.loads(cleaned_json_str)

        return parsed

    except json.JSONDecodeError as e:
        raise ValueError(f"[safe_parse] JSON 解析错误: {e}")
