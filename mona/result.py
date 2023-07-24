from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager
from functools import wraps
from types import TracebackType
from typing import (
    Any,
    Callable,
    cast,
    Final,
    final,
    Generic,
    Literal,
    NoReturn,
    overload,
    ParamSpec,
    TypeGuard,
    TypeVar,
)


E = TypeVar("E", covariant=True, bound=BaseException)
F = TypeVar("F", bound=BaseException)
P = ParamSpec("P")
T = TypeVar("T", covariant=True)
U = TypeVar("U")
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
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
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

    def cast(self, t: type[U]) -> "Result[U, E]":
        return cast("Result[t, E]", self)

    @abstractmethod
    def get(self, default: T) -> T:  # pyright: ignore [reportGeneralTypeIssues]
        ...

    @abstractmethod
    def map(self, f: Callable[[T], U]) -> "Result[U, E]":
        ...

    @abstractmethod
    def map_err(self, f: Callable[[E], F]) -> "Result[T, F]":
        ...

    @abstractmethod
    def or_else(self, f: Callable[[E], "Result[U, F]"]) -> "Result[T | U, F]":
        ...

    @abstractmethod
    def or_raise(self, msg: str | None = None) -> "Ok[T]":
        ...

    @overload
    @abstractmethod
    def or_try(self, f: Callable[P, U], *args: P.args, **kwargs: P.kwargs) -> "Ok[T | U]":
        ...

    @overload
    @abstractmethod
    def or_try(
        self,
        f: Callable[P, U],
        *args: P.args,
        catch: type[X] | tuple[type[X], ...],  # pyright: ignore [reportGeneralTypeIssues]
        **kwargs: P.kwargs,
    ) -> "Result[T | U, X]":
        ...

    # The catch technique used here is not unsound; it's simply inexpressible in the current type
    # annotation system. Pyright, however, despite disapproving, makes the correct inferences.
    @abstractmethod
    def or_try(
        self,
        f: Callable[P, U],
        *args: P.args,
        catch: type[X] | tuple[type[X], ...] = (),  # pyright: ignore [reportGeneralTypeIssues]
        **kwargs: P.kwargs,
    ) -> "Result[T | U, X]":
        ...

    @abstractmethod
    def or_use(self, value: U) -> "Ok[T | U]":  # pyright: ignore [reportGeneralTypeIssues]
        ...

    def transform(self, f: Callable[["Result[T, E]"], U]) -> U:
        return f(self)

    @abstractmethod
    def unwrap(self) -> T:
        ...


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
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self._value.__exit__(exc_type, exc_val, exc_tb)

    def __init__(self, value: T):
        self._value = value

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"

    def and_then(self, f: Callable[[T], Result[U, F]]) -> Result[U, F]:
        return f(self._value)

    def apply(self, f: Callable[[T], None]) -> "Ok[T]":
        f(self._value)
        return self

    def cast(self, t: type[U]) -> "Ok[U]":
        return cast("Ok[t]", self)

    def get(self, default: T) -> T:  # pyright: ignore [reportGeneralTypeIssues]
        return self._value

    def map(self, f: Callable[[T], U]) -> "Ok[U]":
        return Ok(f(self._value))

    def map_err(self, f: Callable[[Any], Any]) -> "Ok[T]":
        return self

    def or_else(self, f: Callable[[Any], Result[Any, Any]]) -> "Ok[T]":
        return self

    def or_try(
        self,
        f: Callable[P, Any],
        *args: P.args,
        catch: type[X] | tuple[type[X], ...] = (),  # pyright: ignore [reportGeneralTypeIssues]
        **kwargs: P.kwargs,
    ) -> "Ok[T]":
        return self

    def or_use(self, value: Any) -> "Ok[T]":  # pyright: ignore [reportGeneralTypeIssues]
        return self

    def or_raise(self, msg: str | None = None) -> "Ok[T]":
        return self

    def unwrap(self) -> T:
        return self._value

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
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        pass

    def __init__(self, error: E):
        self._error = error

    def __repr__(self) -> str:
        return f"Err({self._error!r})"

    def and_then(self, f: Callable[[Any], Result[Any, Any]]) -> "Err[E]":
        return self

    def apply(self, f: Callable[[Any], None]) -> "Err[E]":
        return self

    def cast(self, t: type) -> "Err[E]":
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

    def or_else(self, f: Callable[[E], Result[U, F]]) -> Result[U, F]:
        return f(self._error)

    @overload
    def or_try(self, f: Callable[P, U], *args: P.args, **kwargs: P.kwargs) -> Ok[U]:
        ...

    @overload
    def or_try(
        self,
        f: Callable[P, U],
        *args: P.args,
        catch: type[X] | tuple[type[X], ...],  # pyright: ignore [reportGeneralTypeIssues]
        **kwargs: P.kwargs,
    ) -> Result[U, X]:
        ...

    def or_try(
        self,
        f: Callable[P, U],
        *args: P.args,
        catch: type[X] | tuple[type[X], ...] = (),  # pyright: ignore [reportGeneralTypeIssues]
        **kwargs: P.kwargs,
    ) -> Result[U, X]:
        try:
            return Ok(f(*args, **kwargs))
        except catch as e:
            return Err(e)

    def or_use(self, value: U) -> "Ok[U]":  # pyright: ignore [reportGeneralTypeIssues]
        return Ok(value)

    def or_raise(self, msg: str | None = None) -> NoReturn:
        if msg is None:
            raise ResultError() from self._error
        raise ResultError(msg) from self._error

    def unwrap(self) -> NoReturn:
        raise ResultError("unwrapped Err") from self._error


def result(
    ex: type[X], *result_args: type[X]
) -> Callable[[Callable[P, U]], Callable[P, Result[U, X]]]:
    def inner_result(f: Callable[P, U]) -> Callable[P, Result[U, X]]:
        @wraps(f)
        def g(*args: P.args, **kwargs: P.kwargs) -> Result[U, X]:
            try:
                return Ok(f(*args, **kwargs))
            except (ex, *result_args) as e:  # pyright: ignore
                return Err(e)

        return g

    return inner_result


@overload
def is_err(r: Ok[Any]) -> Literal[False]:
    ...


@overload
def is_err(r: Result[Any, E]) -> TypeGuard[Err[E]]:
    ...


def is_err(r: Result[Any, E]) -> TypeGuard[Err[E]] | Literal[False]:
    return isinstance(r, Err)


@overload
def is_ok(r: Err[Any]) -> Literal[False]:
    ...


@overload
def is_ok(r: Result[T, Any]) -> TypeGuard[Ok[T]]:
    ...


def is_ok(r: Result[T, Any]) -> TypeGuard[Ok[T]] | Literal[False]:
    return isinstance(r, Ok)
