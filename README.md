# Mona
Mona is an experimental library implementing Maybe and Result monads. No guarantee is made as to the stability of the API at present. All feedback is welcome. Mona requires Python 3.10 or newer.

## Installation
### pip
`pip install git+https://github.com/bdholder/mona#egg=mona`

### Pipenv
`pipenv install git+https://github.com/bdholder/mona#egg=mona` or add `mona = {git = "https://github.com/bdholder/mona"}` to the `packages` table in your Pipfile.

## Examples
```
>>> from mona import Some, Nothing
>>> s = Some(3)
>>> s
Some(3)
>>> s.map(lambda x: x**2)
Some(9)
>>> s.map(lambda x: x**2).get(0)
9
>>> n = Nothing()
>>> n
Nothing()
>>> n.map(lambda x: x**2)
Nothing()
>>> n.map(lambda x: x**2).get(0)
0
```

A design goal for Mona is to work out of the box with Pyright. The implementation of `parse_int` here suffices for demonstration.

```python
from typing import Any
from mona import Result, Err, Ok


def parse_int(v: Any) -> Result[int, ValueError]:
    try:
        return Ok(int(v))
    except ValueError as e:
        return Err(e)


romeo = parse_int("2")  # Pyright infers romeo's type is Result[int, ValueError]
match romeo:  # Maybe and Result support pattern matching
    case Ok(v):  # Pyright infers v's type to be int
        print(v + 1)
    case Err(e):
        print("Caught an exception. Raising...")
        raise e  # This will type check because Pyright infer e's type to be ValueError
```

The `parse_int` function could also be written more simply using the `result` decorator.

```python
from mona import result


@result(ValueError)
def parse_int(v: Any) -> int:
    return int(v)
```