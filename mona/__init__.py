from typing import Any, Callable, Concatenate, Optional, ParamSpec, TypeVar

from .maybe import Maybe, Nothing, Some
from .result import Err, Ok, Result, ResultError, result  # pyright: ignore [reportUnusedImport]


P = ParamSpec("P")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def curry(f: Callable[Concatenate[V, P], U]) -> Callable[P, Callable[[V], U]]:
    def first_stage(*args: P.args, **kwargs: P.kwargs) -> Callable[[V], U]:
        def second_stage(v: V) -> U:
            return f(v, *args, **kwargs)

        return second_stage

    return first_stage


def from_optional(v: Optional[T]) -> Maybe[T]:
    return Nothing() if v is None else Some(v)


def into_maybe(r: Result[T, Any]) -> Maybe[T]:
    match r:
        case Ok(v):  # type: ignore
            return Some(v)  # type: ignore
        case Err(_):
            return Nothing()
        case _:
            raise TypeError


def into_result(m: Maybe[T]) -> Result[T, None]:
    match m:
        case Some(v):  # type: ignore
            return Ok(v)  # type: ignore
        case Nothing():
            return Err(None)
        case _:
            raise TypeError
