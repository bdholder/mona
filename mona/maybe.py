from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from contextlib import AbstractContextManager
from types import TracebackType
from typing import (
    Any,
    Generic,
    NoReturn,
    Optional,
    ParamSpec,
    TypeGuard,
    TypeVar,
    Union,
    final,
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
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
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

    def cast(self, tango: type[U]) -> "Maybe[U]":
        return cast(tango, self)  # type: ignore

    @abstractmethod
    def get(self, default: T) -> T:  # type: ignore
        ...

    @abstractmethod
    def map(self, f: Callable[[T], U]) -> "Maybe[U]":
        ...

    @abstractmethod
    def or_else(self, f: Callable[[], "Maybe[T]"]) -> "Maybe[T]":
        ...

    # Using "Some[T]" | NoReturn here causes TypeError: unsupported operand type(s) for |: 'str' and '_SpecialForm'
    @abstractmethod
    def or_raise(self, msg: Optional[str] = None) -> Union["Some[T]", NoReturn]:
        ...

    def transform(self, f: Callable[["Maybe[T]"], U]) -> U:
        return f(self)


@final
class Some(Maybe[T]):
    __match_args__ = ("_value",)
    __slots__ = ("_value",)

    _value: T

    def __bool__(self) -> bool:
        return True

    def __enter__(self: "Some[AbstractContextManager[U]]") -> "Some[U]":
        return Some(self._value.__enter__())

    def __exit__(
        self: "Some[AbstractContextManager[Any]]",
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        return self._value.__exit__(exc_type, exc_val, exc_tb)

    def __init__(self, value: T):
        self._value: T = value

    def __repr__(self) -> str:
        return f"Some({repr(self._value)})"

    def and_then(self, f: Callable[[T], Maybe[U]]) -> Maybe[U]:
        return f(self._value)

    def apply(self, f: Callable[[T], None]) -> "Some[T]":
        f(self._value)
        return self

    def get(self, default: T) -> T:  # type: ignore
        return self._value

    def map(self, f: Callable[[T], U]) -> "Some[U]":
        return Some(f(self._value))

    def or_else(self, f: Callable[[], Maybe[T]]) -> Maybe[T]:
        return self

    def or_raise(self, msg: Optional[str] = None) -> "Some[T]":
        return self

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
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
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

    def or_else(self, f: Callable[[], Maybe[T]]) -> Maybe[T]:
        return f()

    def or_raise(self, msg: Optional[str] = None) -> NoReturn:
        raise NothingError if msg is None else NothingError(msg)


def is_some(m: Maybe[U]) -> TypeGuard[Some[U]]:
    return isinstance(m, Some)
