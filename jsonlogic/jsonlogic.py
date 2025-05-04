from functools import wraps
from typing import Protocol

from .json import JSON, Array, Object

class Operator[T: JSON](Protocol):
    """
    An Operator is a function which receives a list of JSON args,
    and a JSON data, and executes the args against the data, returning
    a JSON.
    """
    def __call__(self, arg: JSON, data: JSON) -> T: ...

operators: dict[str, Operator[JSON]] = {}

def register(key: str, operator: Operator[JSON]):
    if key in operators:
        raise TypeError
    operators[key] = operator

def evaluates_arg[T: JSON](operator: Operator[T]) -> Operator[T]:
    """
    Returns a wrapped version of operator that evaluates
    all its arguments as jsonlogic against the data, before
    actually calling the operator.
    """

    @wraps(operator)
    def wrapped(arg: JSON, data: JSON):
        return operator(evaluate(arg, data), data)
    
    return wrapped
    

def operator(key: str, eval_arg: bool = True):
    """
    Convenience decorator for Operator registration. Use like:

    @operator("+")
    def op_add(args: list[JSON], data: JSON) -> Number:
        ...
    
    The decorated function is returned unchanged.
    """

    def decorator[T: JSON](operator: Operator[T]) -> Operator[T]:
        if eval_arg:
            register(key, evaluates_arg(operator))
        else:
            register(key, operator)
        return operator
    
    return decorator

def evaluate(logic: object, data: object) -> JSON:
    logic, data = JSON(logic), JSON(data)
    match logic:
        case Object() if len(logic) == 1:
            op, arg = next(iter(logic.items()))
            if operator := operators.get(op):
                return JSON(operator(arg, data), path=arg.path)
            else:
                raise ValueError(f"{logic.path}: Unrecognized operator: '{op}'")
        case Object():
            return Object({
                key: JSON(evaluate(value, data), value.path)
                for key, value in logic.items()
            }, path=logic.path)
        case Array():
            return Array([
                JSON(evaluate(item, data), item.path)
                for item in logic
            ], path=logic.path)
        case _:
            return logic
