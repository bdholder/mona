from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager
from functools import wraps
from types import TracebackType
from typing import (
    Any,
    Callable,
    Final,
    Generic,
    NoReturn,
    Optional,
    ParamSpec,
    TypeGuard,
    TypeVar,
    Union,
    cast,
    final,
)


E = TypeVar("E", covariant=True)
F = TypeVar("F")
M = TypeVar("M")
P = ParamSpec("P")
T = TypeVar("T", covariant=True)
U = TypeVar("U")
V = TypeVar("V")
X = TypeVar("X", bound=BaseException)


class ResultError(Exception):
    pass


class Result(Generic[T, E], metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def __enter__(self: "Result[AbstractContextManager[U], E]") -> "Result[U, E]":
        ...

    @abstractmethod
    def __exit__(
        self: "Result[AbstractContextManager[Any], E]",
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        ...

    @abstractmethod
    def __repr__(self) -> str:
        ...

    @abstractmethod
    def and_then(self, f: Callable[[T], "Result[U, F]"]) -> "Result[U, E | F]":
        ...

    @abstractmethod
    def apply(self, f: Callable[[T], None]) -> "Result[T, E]":
        ...

    def cast(self, tango: type[U]) -> "Result[U, E]":
        return cast(tango, self)  # type: ignore

    @abstractmethod
    def get(self, default: T) -> T:  # type: ignore
        ...

    @abstractmethod
    def map(self, f: Callable[[T], U]) -> "Result[U, E]":
        ...

    @abstractmethod
    def map_err(self, f: Callable[[E], F]) -> "Result[T, F]":
        ...

    @abstractmethod
    def or_else(self, f: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        ...

    # Using "Ok[T]" | NoReturn here causes TypeError: unsupported operand type(s) for |: 'str' and '_SpecialForm'
    @abstractmethod
    def or_raise(self, msg: Optional[str] = None) -> Union["Ok[T]", NoReturn]:
        ...

    def _raise(self, exception: type[BaseException], cause: Any) -> NoReturn:
        raise exception from cause if isinstance(cause, BaseException) else exception(repr(cause))

    def transform(self, f: Callable[["Result[T, E]"], U]) -> U:
        return f(self)


@final
class Ok(Result[T, Any]):
    __match_args__ = __slots__ = ("_value",)

    _value: Final[T]

    def __bool__(self) -> bool:
        return True

    def __enter__(self: "Ok[AbstractContextManager[U]]") -> "Ok[U]":
        return Ok(self._value.__enter__())

    def __exit__(
        self: "Ok[AbstractContextManager[Any]]",
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        return self._value.__exit__(exc_type, exc_val, exc_tb)

    def __init__(self, value: T):
        self._value = value

    def __repr__(self) -> str:
        return f"Ok({repr(self._value)})"

    def and_then(self, f: Callable[[T], Result[U, F]]) -> Result[U, F]:
        return f(self._value)

    def apply(self, f: Callable[[T], None]) -> "Ok[T]":
        f(self._value)
        return self

    def get(self, default: T) -> T:  # type: ignore
        return self._value

    def map(self, f: Callable[[T], U]) -> "Ok[U]":
        return Ok(f(self._value))

    def map_err(self, f: Callable[[Any], Any]) -> "Ok[T]":
        return self

    def or_else(self, f: Callable[[Any], Result[T, Any]]) -> "Ok[T]":
        return self

    def or_raise(self, msg: Optional[str] = None) -> "Ok[T]":
        return self

    @property
    def value(self) -> T:
        return self._value


@final
class Err(Result[Any, E]):
    __match_args__ = __slots__ = ("_error",)

    _error: Final[E]

    def __bool__(self) -> bool:
        return False

    def __enter__(self) -> "Err[E]":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        pass

    def __init__(self, error: E):
        self._error = error

    def __repr__(self) -> str:
        return f"Err({repr(self._error)})"

    def and_then(self, f: Callable[[Any], Result[Any, Any]]) -> "Err[E]":
        return self

    def apply(self, f: Callable[[Any], None]) -> "Err[E]":
        return self

    @property
    def error(self) -> E:
        return self._error

    def get(self, default: U) -> U:
        return default

    def map(self, f: Callable[[Any], Any]) -> "Err[E]":
        return self

    def map_err(self, f: Callable[[E], F]) -> "Err[F]":
        return Err(f(self._error))

    def or_else(self, f: Callable[[E], Result[T, F]]) -> Result[T, F]:
        return f(self._error)

    def or_raise(self, msg: Optional[str] = None) -> NoReturn:
        result_error = ResultError(self._error) if msg is None else ResultError(self._error, msg)
        raise result_error from self._error if isinstance(
            self._error, BaseException
        ) else result_error


# This is actually somewhat dangerous since raising the "wrong" type of exception won't be flagged
def result(
    ex: type[X], *result_args: type[X]
) -> Callable[[Callable[P, U]], Callable[P, Result[U, X]]]:
    def inner_result(f: Callable[P, U]) -> Callable[P, Result[U, X]]:
        @wraps(f)
        def g(*args: P.args, **kwargs: P.kwargs) -> Result[U, X]:
            try:
                return Ok(f(*args, **kwargs))
            except (ex, *result_args) as e:  # type: ignore
                return Err(e)  # type: ignore

        return g

    return inner_result


def is_err(r: Result[Any, E]) -> TypeGuard[Err[E]]:
    return isinstance(r, Err)


def is_ok(r: Result[T, Any]) -> TypeGuard[Ok[T]]:
    return isinstance(r, Ok)
