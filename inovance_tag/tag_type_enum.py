"""标签数据类型枚举."""
from enum import Enum


class TagTypeEnum(Enum):
    """标签值的数据类型枚举."""
    INT = "INT"
    BOOL = "BOOL"
    STRING = "STRING"
    DWORD = "DWORD"
    STRUCT = "STRUCT"
    FLOAT = "LREAL"
