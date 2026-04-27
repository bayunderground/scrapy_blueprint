from typing import get_origin, get_args, List, Dict, Optional, Union
import datetime


def python_type_to_sql(py_type):
    origin = get_origin(py_type)
    args = get_args(py_type)

    # Optional[T] → T
    if origin is Union and type(None) in args:
        non_none = [a for a in args if a is not type(None)][0]
        return python_type_to_sql(non_none)

    # List[T] → T[]
    if origin in (list, List):
        inner = python_type_to_sql(args[0])
        return f"{inner}[]"

    # Dict → JSONB
    if origin in (dict, Dict):
        return "JSONB"

    # primitives
    if py_type == str:
        return "TEXT"
    if py_type == int:
        return "INTEGER"
    if py_type == float:
        return "DOUBLE PRECISION"
    if py_type == bool:
        return "BOOLEAN"
    if py_type == datetime.date:
        return "DATE"
    if py_type == datetime.datetime:
        return "TIMESTAMP"

    # fallback
    return "TEXT"