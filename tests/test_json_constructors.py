from decimal import Decimal
from typing import assert_type

from jsonlogic.json import JSON, Null, Boolean, Integer, Float, String, Array, Object
from jsonlogic.jsonpath import JSONPath

def test_JSON_constructor_static_type_without_path():
    assert_type(JSON(None), Null)
    assert_type(JSON(True), Boolean)
    assert_type(JSON(False), Boolean)
    assert_type(JSON(0), Integer)
    assert_type(JSON(Decimal("0")), Float)
    assert_type(JSON(""), String)
    assert_type(JSON([]), Array)
    assert_type(JSON({}), Object)
    
def test_JSON_constructor_static_type_with_path():
    path = JSONPath([])
    assert_type(JSON(None, path=path), Null)
    assert_type(JSON(True, path=path), Boolean)
    assert_type(JSON(False, path=path), Boolean)
    assert_type(JSON(0, path=path), Integer)
    assert_type(JSON(Decimal("0"), path=path), Float)
    assert_type(JSON("", path=path), String)
    assert_type(JSON([], path=path), Array)
    assert_type(JSON({}, path=path), Object)

def test_type_constructor_static_type():
    assert_type(Null(), Null)
    assert_type(Null(None), Null)
    assert_type(Boolean(True), Boolean)
    assert_type(Boolean(False), Boolean)
    assert_type(Integer(0),Integer)
    assert_type(Float(Decimal("0")), Float)
    assert_type(String(""), String)
    assert_type(Array([]), Array)
    assert_type(Object({}), Object)

def test_type_constructor_static_type_with_path():
    path = JSONPath([])
    assert_type(Null(path=path), Null)
    assert_type(Null(None, path=path), Null)
    assert_type(Boolean(True, path=path), Boolean)
    assert_type(Boolean(False, path=path), Boolean)
    assert_type(Integer(0, path=path), Integer)
    assert_type(Float(Decimal("0"), path=path), Float)
    assert_type(String("", path=path), String)
    assert_type(Array([], path=path), Array)
    assert_type(Object({}, path=path), Object)

def test_JSON_constructor_runtime_type_without_path():
    assert type(JSON(None)) is Null
    assert type(JSON(True)) is Boolean
    assert type(JSON(False)) is Boolean
    assert type(JSON(0)) is Integer
    assert type(JSON(Decimal("0"))) is Float
    assert type(JSON("")) is String
    assert type(JSON([])) is Array
    assert type(JSON({})) is Object
    
def test_JSON_constructor_runtime_type_with_path():
    path = JSONPath([])
    assert type(JSON(None, path=path)) is Null
    assert type(JSON(True, path=path)) is Boolean
    assert type(JSON(False, path=path)) is Boolean
    assert type(JSON(0, path=path)) is Integer
    assert type(JSON(Decimal("0"), path=path)) is Float
    assert type(JSON("", path=path)) is String
    assert type(JSON([], path=path)) is Array
    assert type(JSON({}, path=path)) is Object

def test_type_constructor_runtime_type():
    assert type(Null()) is Null
    assert type(Null(None)) is Null
    assert type(Boolean(True)) is Boolean
    assert type(Boolean(False)) is Boolean
    assert type(Integer(0)) is Integer
    assert type(Float(Decimal("0"))) is Float
    assert type(String("")) is String
    assert type(Array([])) is Array
    assert type(Object({})) is Object

def test_type_constructor_runtime_type_with_path():
    path = JSONPath([])
    assert type(Null(path=path)) is Null
    assert type(Null(None, path=path)) is Null
    assert type(Boolean(True, path=path)) is Boolean
    assert type(Boolean(False, path=path)) is Boolean
    assert type(Integer(0, path=path)) is Integer
    assert type(Float(Decimal("0"), path=path)) is Float
    assert type(String("", path=path)) is String
    assert type(Array([], path=path)) is Array
    assert type(Object({}, path=path)) is Object
