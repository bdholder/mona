from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from contextlib import AbstractContextManager
from types import TracebackType
from typing import (
    Any,
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


P = ParamSpec("P")
T = TypeVar("T", covariant=True)
U = TypeVar("U")


class MaybeError(Exception):
    pass


class NothingError(MaybeError):
    pass


class Maybe(Generic[T], metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def __bool__(self) -> bool:
        ...

    @abstractmethod
    def __enter__(self: "Maybe[AbstractContextManager[U]]") -> "Maybe[U]":
        ...

    @abstractmethod
    def __exit__(
        self: "Maybe[AbstractContextManager[Any]]",
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        ...

    @abstractmethod
    def __repr__(self) -> str:
        ...

    @abstractmethod
    def and_then(self, f: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        ...

    @abstractmethod
    def apply(self, f: Callable[[T], None]) -> "Maybe[T]":
        ...

    def cast(self, t: type[U]) -> "Maybe[U]":
        return cast("Maybe[t]", self)

    @abstractmethod
    def get(self, default: T) -> T:  # pyright: ignore [reportGeneralTypeIssues]
        ...

    @abstractmethod
    def map(self, f: Callable[[T], U]) -> "Maybe[U]":
        ...

    @abstractmethod
    def or_else(self, f: Callable[[], "Maybe[U]"]) -> "Maybe[T | U]":
        ...

    @abstractmethod
    def or_raise(self, msg: str | None = None) -> "Some[T]":
        ...

    @abstractmethod
    def or_try(self, f: Callable[P, U], *args: P.args, **kwargs: P.kwargs) -> "Some[T | U]":
        ...

    @abstractmethod
    def or_use(self, value: U) -> "Some[T | U]":
        ...

    def transform(self, f: Callable[["Maybe[T]"], U]) -> U:
        return f(self)

    @abstractmethod
    def unwrap(self) -> T:
        ...


@final
class Some(Maybe[T]):
    __match_args__ = __slots__ = ("_value",)

    _value: Final[T]

    def __bool__(self) -> bool:
        return True

    def __enter__(self: "Some[AbstractContextManager[U]]") -> "Some[U]":
        return Some(self._value.__enter__())

    def __exit__(
        self: "Some[AbstractContextManager[Any]]",
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self._value.__exit__(exc_type, exc_val, exc_tb)

    def __init__(self, value: T):
        self._value: T = value

    def __repr__(self) -> str:
        return f"Some({self._value!r})"

    def and_then(self, f: Callable[[T], Maybe[U]]) -> Maybe[U]:
        return f(self._value)

    def apply(self, f: Callable[[T], None]) -> "Some[T]":
        f(self._value)
        return self

    def cast(self, t: type[U]) -> "Some[U]":
        return cast("Some[t]", self)

    def get(self, default: T) -> T:  # pyright: ignore [reportGeneralTypeIssues]
        return self._value

    def map(self, f: Callable[[T], U]) -> "Some[U]":
        return Some(f(self._value))

    def or_else(self, f: Callable[[], Maybe[Any]]) -> "Some[T]":
        return self

    def or_raise(self, msg: str | None = None) -> "Some[T]":
        return self

    def or_try(self, f: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> "Some[T]":
        return self

    def or_use(self, value: Any) -> "Some[T]":
        return self

    def unwrap(self) -> T:
        return self._value

    @property
    def value(self) -> T:
        return self._value


@final
class Nothing(Maybe[Any]):
    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __enter__(self) -> "Nothing":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        pass

    def __repr__(self) -> str:
        return "Nothing()"

    def and_then(self, f: Callable[[Any], Maybe[Any]]) -> "Nothing":
        return self

    def apply(self, f: Callable[[Any], None]) -> "Nothing":
        return self

    def get(self, default: U) -> U:
        return default

    def map(self, f: Callable[[Any], Any]) -> "Nothing":
        return self

    def or_else(self, f: Callable[[], Maybe[U]]) -> Maybe[U]:
        return f()

    def or_raise(self, msg: str | None = None) -> NoReturn:
        raise NothingError if msg is None else NothingError(msg)

    def or_try(self, f: Callable[P, U], *args: P.args, **kwargs: P.kwargs) -> Some[U]:
        return Some(f(*args, **kwargs))

    def or_use(self, value: U) -> Some[U]:
        return Some(value)

    def unwrap(self) -> NoReturn:
        raise MaybeError("unwrapped Nothing")


@overload
def is_nothing(m: Some[Any]) -> Literal[False]:  # pyright: ignore [reportOverlappingOverload]
    ...


@overload
def is_nothing(m: Maybe[Any]) -> TypeGuard[Nothing]:
    ...


def is_nothing(m: Maybe[Any]) -> TypeGuard[Nothing] | Literal[False]:
    return isinstance(m, Nothing)


@overload
def is_some(m: Nothing) -> Literal[False]:
    ...


@overload
def is_some(m: Maybe[T]) -> TypeGuard[Some[T]]:
    ...


def is_some(m: Maybe[T]) -> TypeGuard[Some[T]] | Literal[False]:
    return isinstance(m, Some)
