"""
JSONPath is an object that represents a location in a JSON document.

This implementation is representation-agnostic; a JSONPath object can be
converted to/from:
- RFC 9535: JSONPath (https://datatracker.ietf.org/doc/html/rfc9535)
- RFC 6901: JSONPointer (https://datatracker.ietf.org/doc/html/rfc6901)
- The "dot notation" used by JSONLogic (https://jsonlogic.com/)
"""

from typing import Self

class JSONPath(tuple[int | str, ...]):
    @classmethod
    def empty(cls) -> Self:
        return cls([])
    
    @classmethod
    def from_dot_notation(cls, value: str) -> Self:
        path = cls.empty()

        for key in value.split('.'):
            try:
                path = cls([*path, int(key)])
            except ValueError:
                path = cls([*path, key])
        
        return path
    
    def rfc9535(self) -> str:
        value = "$"
        for key in self:
            match key:
                case int():
                    value += f"[{key}]"
                case str():
                    value += f".{key}"
        return value
    
    def __str__(self):
        return self.rfc9535()
