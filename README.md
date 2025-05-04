# JSONLogic

## Why another JSONLogic implementation?

The goal of this JSONLogic implementation is two-fold:

1. For well-formed input: to produce correct output
2. For erroneous input: to produce error messages which are useful in debugging the input.

Most JSONLogic implementations accomplish the first goal, but don't even attempt to meet the second goal.

For example, the [json-logic](https://github.com/nadirizr/json-logic-py) Python library produces error messages like the following:

```
>>> jsonLogic({"var": 3.5}, ["a", "b", "c", "d", "e"])
Traceback (most recent call last):
  File "/Users/siobhansterrett/Desktop/jsonlogic/.venv/lib/python3.13/site-packages/json_logic/__init__.py", line 106, in get_var
    data = data[key]
           ~~~~^^^^^
TypeError: string indices must be integers, not 'str'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<python-input-3>", line 1, in <module>
    jsonLogic(logic, data)
    ~~~~~~~~~^^^^^^^^^^^^^
  File "/Users/siobhansterrett/Desktop/jsonlogic/.venv/lib/python3.13/site-packages/json_logic/__init__.py", line 194, in jsonLogic
    return get_var(data, *values)
  File "/Users/siobhansterrett/Desktop/jsonlogic/.venv/lib/python3.13/site-packages/json_logic/__init__.py", line 108, in get_var
    data = data[int(key)]
           ~~~~^^^^^^^^^^
IndexError: string index out of range
```

The canonical Javascript JSONLogic implementation, hosted at [JSONLogic.com](JSONLogic.com), doesn't even alert the user that the logic is ill-formed:

```
>>> jsonLogic.apply({"var": 3.5}, ["a", "b", "c", "d", "e"])
null
```

On the other hand, this library's implementation returns an error message indicating the precise location of the error (as an RFC-9535 JSONPath), and a useful description:

```
>>> evaluate({"var": 3.5}, ["a", "b", "c", "d", "e"])
Traceback (most recent call last):
  File "<python-input-6>", line 1, in <module>
    evaluate({"var": 3.5}, ["a", "b", "c", "d", "e"])
    ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/siobhansterrett/Desktop/jsonlogic/jsonlogic/jsonlogic.py", line 61, in evaluate
    return JSON(operator(arg, data), path=arg.path)
                ~~~~~~~~^^^^^^^^^^^
  File "/Users/siobhansterrett/Desktop/jsonlogic/jsonlogic/jsonlogic.py", line 30, in wrapped
    return operator(evaluate(arg, data), data)
  File "/Users/siobhansterrett/Desktop/jsonlogic/jsonlogic/operators.py", line 105, in op_var
    raise wrong_type(arg, String, Integer)
TypeError: $.var: Expected String or Integer, but got Float
```

This library is therefore well-suited for client-server applications, where the frontend team is responsible for generating the JSONLogic and sending it to the backend. If an error occurs during evaluation, the error message can be sent directly back to the client, who will hopefully be able to understand how the error message applies to their request.
