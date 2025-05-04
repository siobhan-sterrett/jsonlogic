import enum
import json
import pytest
import requests

from decimal import Decimal
from pathlib import Path
from typing import cast, Final

from jsonlogic import JSON, evaluate

tests_path = Path(__file__).parent / 'tests.json'

def load_tests():
    if not tests_path.exists():
        test_url = 'https://jsonlogic.com/tests.json'
        response = requests.get(test_url)
        response.raise_for_status()
        tests_path.write_text(response.text)

load_tests()

def pytest_collect_file(parent: object, file_path: Path):
    if file_path.name == 'tests.json':
        return JSONTestFile.from_parent(parent, path=file_path)
    
class JSONTestFile(pytest.File):
    def collect(self):
        with self.path.open() as f:
            tests = json.load(f, parse_float=Decimal)
            for i, test in enumerate(tests):
                match test:
                    case str():
                        pass
                    case list():
                        test = cast(list[object], test)
                        yield JSONTestItem.from_parent(self, name=str(i), test=test)
                    case _:
                        raise TypeError(f"Cannot parse item {i} of {self.path}")

class _Empty(enum.Enum):
    empty = None

_empty: Final[_Empty] = _Empty.empty

class JSONTestItem(pytest.Item):
    logic: object
    data: object
    expected: object
    actual: JSON | _Empty = _empty

    def __init__(self, *, name: str, parent: object, test: list[object]):
        super().__init__(name=name, parent=parent)
        self.logic, self.data, self.expected = test

    def runtest(self):
        self.actual = evaluate(JSON(self.logic), JSON(self.data))
        assert self.expected == self.actual
    
    def repr_failure(self, excinfo: pytest.ExceptionInfo[BaseException], *args: object, **kwargs: object):
        file_name, *_ = self.location
        lines = [
            f"Test failed: {file_name}::{self.name}",
            f"    logic: {self.logic}",
            f"    data: {self.data}",
            f"    expected: {self.expected}",
        ]

        if self.actual is not _empty:
            lines.append(f"    actual: {self.actual}")
        else:
            lines.append(str(excinfo.getrepr(style='line')))

        return "\n".join(lines)
