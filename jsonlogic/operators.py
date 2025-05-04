from decimal import Decimal
from enum import Enum, auto

from .json import JSON, Null, Boolean, Integer, Float, String, Array, Object
from .jsonlogic import evaluate, operator
from .jsonpath import JSONPath

def wrong_arity(arg: Array, expected: str):
    match expected:
        case "one" | "at least one":
            return TypeError(f"{arg.path}: Expected {expected} arg, but got {len(arg)}")
        case _:
            return TypeError(f"{arg.path}: Expected {expected} args, but got {len(arg)}")

def wrong_type(arg: JSON, *expected: type[JSON]):
    match expected:
        case [t]:
            expected_msg = f"{t.__name__}"
        case [t1, t2]:
            expected_msg = f"{t1.__name__} or {t2.__name__}"
        case [*ts, t_last]:
            expected_msg = f"{", ".join(t.__name__ for t in ts)}, or {t_last.__name__}"

    return TypeError(f"{arg.path}: Expected {expected_msg}, but got {type(arg).__name__}")

def as_number(arg: String) -> Integer | Float:
    try:
        return Integer(int(arg))
    except ValueError:
        pass

    try:
        return Float(Decimal(arg))
    except ValueError:
        pass

    raise ValueError(f"{arg.path}: Cannot convert String value to Number")

class Cmp(Enum):
    Less = auto()
    Equal = auto()
    Greater = auto()

def cmp(left: JSON, right: JSON) -> Cmp | None:
    match left, right:
        case Null(), Null(): return Cmp.Equal

        case Null(), _:
            return cmp(Integer(0), right)
        case _, Null():
            return cmp(left, Integer(0))

        case (Boolean() | Integer() | Float()), (Boolean() | Integer() | Float()):
            if left == right:
                return Cmp.Equal
            elif left < right:
                return Cmp.Less
            else:
                return Cmp.Greater
        
        case (Boolean() | Integer() | Float()), String():
            return cmp(left, as_number(right))
        case String(), (Boolean() | Integer() | Float()):
            return cmp(as_number(left), right)
        
        case String(), String():
            if left == right:
                return Cmp.Equal
            elif left < right:
                return Cmp.Less
            else:
                return Cmp.Greater
        
        case Array(), Array():
            if left == right:
                return Cmp.Equal
            elif left < right:
                return Cmp.Less
            else:
                return Cmp.Greater
        
        case _, _:
            return None

@operator("var")
def op_var(arg: JSON, data: JSON) -> JSON:
    match arg:
        case (Null() | String("")) as key:
            return data
        case (String() | Integer()) as key:
            default = Null()
        
        case Array([(Null() | String("")) as key, *_]):
            return data
        case Array([(String() | Integer()) as key]):
            default = Null()
        case Array([(String() | Integer()) as key, default]):
            pass

        case Array([]):
            return data
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, String, Integer)

    match key:
        case String(_):
            try:
                path = JSONPath.from_dot_notation(key)
            except ValueError:
                path = JSONPath([key])
        case Integer():
            path = JSONPath([key])
     
    try:
        return data.at_path(path)
    except (KeyError, IndexError, ValueError):
        return default
    
@operator("missing")
def op_missing(arg: JSON, data: JSON) -> Array:
    match arg:
        case (String() | Integer()) as key:
            keys = [key]
        case Array([*keys]):
            pass
        case _:
            raise wrong_type(arg, String, Integer)
    
    missing = Array([])
    for key in keys:
        match key:
            case String():
                try:
                    path = JSONPath.from_dot_notation(key)
                except ValueError:
                    path = JSONPath([key])
            case Integer():
                path = JSONPath([key])
            case _:
                raise wrong_type(arg, String, Integer)
        
        try:
            data.at_path(path)
        except (KeyError, IndexError, ValueError):
            missing.append(key)
        
    return missing

    
@operator("missing_some")
def op_missing_some(arg: JSON, data: JSON) -> Array:
    match arg:
        case Array([Integer() as minimum, Array() as keys]):
            pass
        case Array([arg, _]):
            raise wrong_type(arg, Integer)
        case Array([Integer(), arg]):
            raise wrong_type(arg, Array)
        case _:
            raise wrong_type(arg, Array)
    
    missing = op_missing(keys, data)

    found_keys = len(keys) - len(missing)

    if found_keys < minimum:
        return missing
    else:
        return Array([])

@operator("if", eval_arg=False)
@operator("?:", eval_arg=False)
def op_if(arg: JSON, data: JSON) -> JSON:
    match arg:
        case Array([]):
            return Null()
        case Array([if_arg]):
            return evaluate(if_arg, data)
        case Array([if_arg, then_arg, *elses]):
            if evaluate(if_arg, data):
                return evaluate(then_arg, data)
            else:
                return op_if(Array(elses), data)
        case _:
            raise wrong_type(arg, Array)

@operator("==")
def op_eq(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([left, right]):
            return Boolean(cmp(left, right) is Cmp.Equal)
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("===")
def op_eq_eq(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([left, right]):
            return Boolean(op_eq(arg, data) and type(left) == type(right))
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("!=")
def op_neq(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([left, right]):
            return Boolean(cmp(left, right) is not Cmp.Equal)
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)
        
@operator("!==")
def op_neq_eq(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([left, right]):
            return Boolean(op_neq(arg, data) or type(left) != type(right))
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("!")
def op_not(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([value]):
            return Boolean(not value)
        case _:
            return Boolean(not arg)

@operator("!!")
def op_not_not(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([value]):
            return Boolean(not not value)
        case _:
            return Boolean(not not arg)

@operator("or", eval_arg=False)
def op_or(arg: JSON, data: JSON) -> JSON:
    match arg:
        case Array([arg, *args]):
            result = arg
            for arg in [arg, *args]:
                if result := evaluate(arg, data):
                    return result
            return result
        case Array(_):
            raise wrong_arity(arg, "one or more")
        case _:
            raise wrong_type(arg, Array)
        
@operator("and", eval_arg=False)
def op_and(arg: JSON, data: JSON) -> JSON:
    match arg:
        case Array([arg, *args]):
            result = arg
            for arg in [arg, *args]:
                if not (result := evaluate(arg, data)):
                    return result
            return result
        case Array(_):
            raise wrong_arity(arg, "one or more")
        case _:
            raise wrong_type(arg, Array)

@operator("<")
def op_lt(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([left, right]):
            return Boolean(cmp(left, right) is Cmp.Less)
        case Array([left, middle, right]):
            return Boolean(op_lt(Array([left, middle]), data) and op_lt(Array([middle, right]), data))
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("<=")
def op_lte(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([left, right]):
            return Boolean(cmp(left, right) in (Cmp.Less, Cmp.Equal))
        case Array([left, middle, right]):
            return Boolean(op_lte(Array([left, middle]), data) and op_lte(Array([middle, right]), data))
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator(">")
def op_gt(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([left, right]):
            return Boolean(cmp(left, right) is Cmp.Greater)
        case Array([left, middle, right]):
            return Boolean(op_gt(Array([left, middle]), data) and op_gt(Array([middle, right]), data))
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator(">=")
def op_gte(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([left, right]):
            return Boolean(cmp(left, right) in (Cmp.Greater, Cmp.Equal))
        case Array([left, middle, right]):
            return Boolean(op_gte(Array([left, middle]), data) and op_gte(Array([middle, right]), data))
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("max")
def op_max(arg: JSON, data: JSON) -> JSON:
    match arg:
        case Array([arg]):
            return arg
        case Array([left, right]):
            if op_lt(arg, data):
                return right
            else:
                return left
        case Array([left, right, *args]):
            value = op_max(Array([left, right]), data)
            return op_max(Array([value, *args]), data)
        case Array(_):
            raise wrong_arity(arg, "at least one")
        case _:
            raise wrong_type(arg, Array)

@operator("min")
def op_min(arg: JSON, data: JSON) -> JSON:
    match arg:
        case Array([arg]):
            return arg
        case Array([left, right]):
            if op_lte(arg, data):
                return left
            else:
                return right
        case Array([left, right, *args]):
            value = op_min(Array([left, right]), data)
            return op_min(Array([value, *args]), data)
        case Array(_):
            raise wrong_arity(arg, "at least one")
        case _:
            raise wrong_type(arg, Array)

@operator("+")
def op_add(arg: JSON, data: JSON) -> Integer | Float:
    match arg:
        case Array([]):
            return Integer(0)

        case Array([Integer() as n, *args]):
            match op_add(Array(args), data):
                case Integer() as ns:
                    return Integer(n + ns)
                case Float() as ns:
                    return Float(n + ns)
        case Array([Float() as n, *args]):
            return Float(n + op_add(Array(args), data))
        case Array([String() as s, *args]):
            return op_add(Array([as_number(s), *args]), data)
        case Array([x, *args]):
            raise wrong_type(x, Integer, Float, String)

        case (Integer() | Float() | String()):
            return op_add(Array([arg]), data)
        case _:
            raise wrong_type(arg, Integer, Float, String, Array)

@operator("-")
def op_sub(arg: JSON, data: JSON) -> Integer | Float:
    match arg:
        case Array([Integer() as n]):
            return Integer(-n)
        case Array([Float() as n]):
            return Float(-n)
        case Array([String() as s]):
            return op_sub(Array([as_number(s)]), data)

        case Array([Integer() as left, Integer() as right]):
            return Integer(left - right)
        case Array([Integer() as left, Float() as right]):
            return Float(left - right)
        case Array([Integer() as left, String() as right]):
            return op_sub(Array([left, as_number(right)]), data)

        case Array([Float() as left, (Integer() | Float()) as right]):
            return Float(left - right)
        case Array([Float() as left, String() as right]):
            return op_sub(Array([left, as_number(right)]), data)
        
        case Array([String() as left, right]):
            return op_sub(Array([as_number(left), right]), data)
        
        case Array([(Integer() | Float() | String()) as left, right]):
            raise wrong_type(right, Integer, Float, String)
        case Array([left, right]):
            raise wrong_type(left, Integer, Float, String)
        
        case Array(_):
            raise wrong_arity(arg, "one or two")
        
        case (Integer() | Float() | String()):
            return op_sub(Array([arg]), data)
        case _:
            raise wrong_type(arg, Integer, Float, String, Array)
        
@operator("*")
def op_mul(arg: JSON, data: JSON) -> Integer | Float:
    match arg:
        case Array([]):
            return Integer(1)

        case Array([Integer() as n, *args]):
            match op_mul(Array(args), data):
                case Integer() as ns:
                    return Integer(n * ns)
                case Float() as ns:
                    return Float(n * ns)
        case Array([Float() as n, *args]):
            return Float(n * op_mul(Array(args), data))
        case Array([String() as s, *args]):
            return op_mul(Array([as_number(s), *args]), data)
        case Array([x, *args]):
            raise wrong_type(x, Integer, Float, String)

        case (Integer() | Float() | String()):
            return op_mul(Array([arg]), data)
        case _:
            raise wrong_type(arg, Integer, Float, String, Array)

@operator("/")
def op_div(arg: JSON, data: JSON) -> Integer | Float:
    match arg:
        case Array([Integer() as left, Integer() as right]):
            return Float(Float(Decimal(str(left))) / Float(Decimal(str(right))))
        case Array([Integer() as left, Float() as right]):
            return Float(left / right)
        case Array([Integer() as left, String() as right]):
            return op_div(Array([left, as_number(right)]), data)

        case Array([Float() as left, (Integer() | Float()) as right]):
            return Float(left / right)
        case Array([Float() as left, String() as right]):
            return op_div(Array([left, as_number(right)]), data)
        
        case Array([String() as left, right]):
            return op_div(Array([as_number(left), right]), data)
        
        case Array([(Integer() | Float() | String()) as left, right]):
            raise wrong_type(right, Integer, Float, String)
        case Array([left, right]):
            raise wrong_type(left, Integer, Float, String)
        
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("%")
def op_mod(arg: JSON, data: JSON) -> Integer | Float:
    match arg:
        case Array([Integer() as left, Integer() as right]):
            return Float(Float(Decimal(str(left))) % Float(Decimal(str(right))))
        case Array([Integer() as left, Float() as right]):
            return Float(left % right)
        case Array([Integer() as left, String() as right]):
            return op_mod(Array([left, as_number(right)]), data)

        case Array([Float() as left, (Integer() | Float()) as right]):
            return Float(left % right)
        case Array([Float() as left, String() as right]):
            return op_mod(Array([left, as_number(right)]), data)
        
        case Array([String() as left, right]):
            return op_mod(Array([as_number(left), right]), data)
        
        case Array([(Integer() | Float() | String()) as left, right]):
            raise wrong_type(right, Integer, Float, String)
        case Array([left, right]):
            raise wrong_type(left, Integer, Float, String)
        
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("map", eval_arg=False)
def op_map(arg: JSON, data: JSON) -> Array:
    match arg:
        case Array([items, fn]):
            xs = JSON(evaluate(items, data), path=items.path)
            match xs:
                case Null():
                    return Array([])
                case Array(_):
                    return Array([
                        evaluate(fn, x)
                        for x in xs
                    ])
                case _:
                    raise wrong_type(items, Array)
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("filter", eval_arg=False)
def op_filter(arg: JSON, data: JSON) -> Array:
    match arg:
        case Array([items, fn]):
            xs = JSON(evaluate(items, data), path=items.path)
            match xs:
                case Array(_):
                    return Array([
                        x
                        for x in xs
                        if evaluate(fn, x)
                    ])
                case _:
                    raise wrong_type(items, Array)
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("reduce", eval_arg=False)
def op_reduce(arg: JSON, data: JSON) -> JSON:
    match arg:
        case Array([items, fn, initial]):
            xs = JSON(evaluate(items, data), path=items.path)
            initial = JSON(evaluate(initial, data), path=initial.path)
            match xs:
                case Null():
                    return initial
                case Array(_):
                    value = Object({
                        "current": None,
                        "accumulator": initial
                    })
                    for x in xs:
                        value["current"] = x
                        value["accumulator"] = evaluate(fn, value)
                    return value["accumulator"]
                case _:
                    raise wrong_type(items, Array)
        case Array(_):
            raise wrong_arity(arg, "three")
        case _:
            raise wrong_type(arg, Array)
        
@operator("all", eval_arg=False)
def op_all(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([items, fn]):
            xs = evaluate(items, data)
            match xs:
                case Array([]):
                    # This is stupid, but it's according to spec
                    return Boolean(False)
                case Array(_):
                    for x in xs:
                        if not evaluate(fn, x):
                            return Boolean(False)
                    return Boolean(True)
                case _:
                    raise wrong_type(items, Array)
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)
        
@operator("some", eval_arg=False)
def op_some(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([items, fn]):
            xs = evaluate(items, data)
            match xs:
                case Array(_):
                    for x in xs:
                        if evaluate(fn, x):
                            return Boolean(True)
                    return Boolean(False)
                case _:
                    raise wrong_type(items, Array)
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)
        
@operator("none", eval_arg=False)
def op_none(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([items, fn]):
            xs = evaluate(items, data)
            match xs:
                case Array(_):
                    for x in xs:
                        if evaluate(fn, x):
                            return Boolean(False)
                    return Boolean(True)
                case _:
                    raise wrong_type(items, Array)
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)

@operator("merge")
def op_merge(arg: JSON, data: JSON) -> Array:
    match arg:
        case Array([]):
            return Array([])
        case Array([Array() as a, *args]):
            return Array([*a, *op_merge(Array(args), data)])
        case Array([a, *args]):
            return Array([a, *op_merge(Array(args), data)])
        case _:
            return Array([arg])

@operator("in")
def op_in(arg: JSON, data: JSON) -> Boolean:
    match arg:
        case Array([String() as needle, String() as haystack]):
            return Boolean(needle in haystack)
        case Array([needle, Array() as haystack]):
            return Boolean(needle in haystack)
        case Array([String() as needle, haystack]):
            raise wrong_type(haystack, String, Array)
        case Array([needle, haystack]):
            raise wrong_type(haystack, Array)
        case Array(_):
            raise wrong_arity(arg, "two")
        case _:
            raise wrong_type(arg, Array)
        
@operator("cat")
def op_cat(arg: JSON, data: JSON) -> String:
    match arg:
        case Array([]):
            return String("")
        case Array([String() as s, *args]):
            return String(s + op_cat(Array(args), data))
        case Array([(Integer() | Float()) as n, *args]):
            return op_cat(Array([String(str(n)), *args]), data)
        case Array([x, *args]):
            raise wrong_type(x, String)
        case _:
            return op_cat(Array([arg]), data)

@operator("substr")
def op_substr(arg: JSON, data: JSON) -> String:
    match arg:
        case Array([String() as s, Integer() as start]):
            return String(s[start:])
        case Array([String() as s, Integer() as start, Integer() as length]):
            return String(s[start:][:length])
        case Array([String() as s, Integer() as start, length]):
            raise wrong_type(length, Integer)
        case Array([String() as s, start, *_]):
            raise wrong_type(start, Integer)
        case Array([s, *_]):
            raise wrong_type(s, String)
        case Array(_):
            raise wrong_arity(arg, "two or three")
        case _:
            raise wrong_type(arg, Array)

@operator("log")
def op_log(arg: JSON, data: JSON) -> JSON:
    match arg:
        case Array([x, *_]):
            print(x)
            return x
        case arg:
            print(arg)
            return arg
