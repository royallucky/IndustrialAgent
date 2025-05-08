from typing import List


def normalize_header(header: List[str]) -> List[str]:
    """统一表头，去除空格，统一中英文符号"""
    symbol_map = str.maketrans({
        '（': '(', '）': ')',
        '：': ':', '，': ',',
        '。': '.', '“': '"', '”': '"',
        '、': ',', '；': ';'
    })
    return [h.translate(symbol_map).strip() for h in header]
