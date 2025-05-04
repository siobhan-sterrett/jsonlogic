"""
Definitions of JSON types in Python.
"""

from decimal import Decimal
from typing import Literal, Mapping, Sequence, Self, final, overload

from .jsonpath import JSONPath

class JSON:
    path: JSONPath

    @overload
    def __new__(cls, value: None = None, path: JSONPath = JSONPath.empty()) -> 'Null': ...
    @overload
    def __new__(cls, value: 'Null', path: JSONPath = JSONPath.empty()) -> 'Null': ...
    @overload
    def __new__(cls, value: Literal[True, False] | 'Boolean', path: JSONPath = JSONPath.empty()) -> 'Boolean': ...
    @overload
    def __new__(cls, value: int, path: JSONPath = JSONPath.empty()) -> 'Integer': ...
    @overload
    def __new__(cls, value: Decimal, path: JSONPath = JSONPath.empty()) -> 'Float': ...
    @overload
    def __new__(cls, value: str, path: JSONPath = JSONPath.empty()) -> 'String': ...
    @overload
    def __new__(cls, value: list | tuple, path: JSONPath = JSONPath.empty()) -> 'Array': ...
    @overload
    def __new__(cls, value: Sequence, path: JSONPath = JSONPath.empty()) -> 'Array | Object': ...
    @overload
    def __new__(cls, value: Mapping, path: JSONPath = JSONPath.empty()) -> 'Object': ...
    @overload
    def __new__(cls, value: object, path: JSONPath = JSONPath.empty()) -> 'JSON': ...
    def __new__(cls, value: object = None, path: JSONPath = JSONPath.empty()) -> 'JSON':
        match value:
            case None | Null():
                return Null.__new__(Null, None, path)
            case True | False | Boolean():
                return Boolean.__new__(Boolean, value, path)
            case int() | Integer():
                return Integer.__new__(Integer, value, path)
            case Decimal() | Float():
                return Float.__new__(Float, value, path)
            case str() | String():
                return String.__new__(String, value, path)
            case Object():
                return Object.__new__(Object, value, path)
            case _ if isinstance(value, Mapping):
                return Object.__new__(Object, value, path)
            case Array():
                return Array.__new__(Array, value, path)
            case _ if isinstance(value, Sequence):
                return Array.__new__(Array, value, path)
            case _:
                raise TypeError(f"{path}: Cannot convert {type(value).__name__} to JSON")
    
    def __init__(self, value: object, path: JSONPath = JSONPath.empty()):
        self.path = path

    def at_path(self, path: JSONPath) -> 'JSON':
        if not path:
            return self
        
        key, path = path[0], JSONPath(path[1:])

        match key, self:
            case int(), Array():
                return self[key].at_path(path)
            case str(), Object():
                return self[key].at_path(path)
            case _:
                raise ValueError(f"{self.path}: Cannot index {type(self).__name__} with {type(key).__name__}")

@final
class Null(JSON):
    def __new__(cls, value: None = None, path: JSONPath = JSONPath.empty()) -> Self:
        return object.__new__(cls)
    
    def __init__(self, value: None = None, path: JSONPath = JSONPath.empty()):
        super().__init__(value, path)

    def __eq__(self, other: object):
        return other is None
    
    def __repr__(self):
        return "Null()"

@final
class Boolean(int, JSON):  # bool cannot be subclassed
    def __new__(cls, value: int, path: JSONPath = JSONPath.empty()) -> Self:
        return int.__new__(cls, value)
    
    def __str__(self):
        return str(bool(self))

@final
class Integer(int, JSON):
    def __new__(cls, value: int, path: JSONPath = JSONPath.empty()) -> Self:
        return int.__new__(cls, value)

@final
class Float(Decimal, JSON):
    def __new__(cls, value: Decimal, path: JSONPath = JSONPath.empty()) -> Self:
        return Decimal.__new__(cls, value)

@final
class String(str, JSON):
    def __new__(cls, value: str, path: JSONPath = JSONPath.empty()) -> Self:
        return str.__new__(cls, value)

@final
class Array(list['JSON'], JSON):
    def __new__(cls, value: Sequence, path: JSONPath = JSONPath.empty()) -> Self:
        return list.__new__(cls)
    
    def __init__(self, value: Sequence, path: JSONPath = JSONPath.empty()):
        JSON.__init__(self, value, path)
        for i, item in enumerate(value):
            self.append(JSON(item, path=JSONPath([*path, i])))
    
@final
class Object(dict[str, 'JSON'], JSON):
    def __new__(cls, value: Mapping, path: JSONPath = JSONPath.empty()) -> Self:
        return dict.__new__(cls)
    
    def __init__(self, value: Mapping, path: JSONPath = JSONPath.empty()):
        JSON.__init__(self, value, path)
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeError
            self[k] = JSON(v, path=JSONPath([*path, k]))
