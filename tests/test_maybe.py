# pyright: strict
# pyright: reportUnnecessaryTypeIgnoreComment = true
import math
from typing import cast
from unittest.mock import MagicMock

import pytest
from typing_extensions import assert_never, assert_type

from mona.maybe import Maybe, Nothing, NothingError, Some, is_some
from mona.result import Ok


def test_and_then():
    def maybe_sqrt(n: int) -> Maybe[float]:
        return Nothing() if n < 0 else Some(math.sqrt(n))
    
    match Some(4).and_then(maybe_sqrt):
        case Some(v):
            assert v == 2.0
        case _:
            assert False
    
    assert isinstance(Some(-4).and_then(maybe_sqrt), Nothing)
    assert isinstance(Nothing().and_then(maybe_sqrt), Nothing)


def test_apply():
    m = MagicMock()
    m.foo.return_value = None  # pyright: ignore [reportUnknownMemberType]
    match Some(m).apply(lambda x: x.foo()):  # pyright: ignore
        case Some(v):
            assert v is m
            v.foo.assert_called_once()  # pyright: ignore [reportUnknownMemberType]
        case _:  # pyright: ignore [reportUnnecessaryComparison]
            assert False

    assert isinstance(Nothing().apply(lambda x: x.foo()), Nothing)


def test_assign_value():
    s = Some(2)
    with pytest.raises(AttributeError):
        s.value = 3  # pyright: ignore [reportGeneralTypeIssues]
    n = Nothing()
    with pytest.raises(AttributeError):
        n.value = 2  # pyright: ignore [reportGeneralTypeIssues]


def test_get():
    assert Some(2).get(0) == 2
    assert Nothing().get(0) == 0


def test_is_some():
    s = cast(Maybe[int], Some(2))
    assert is_some(s)
    if is_some(s):
        assert_type(s, Some[int])
        assert s.value == 2

    n = Nothing()
    if is_some(n):
        assert_type(n, Nothing)
    assert not is_some(n)


def test_is_some_non_maybe():
    assert not is_some(Ok("foo"))  # pyright: ignore
    assert not is_some(1)  # pyright: ignore


def test_map():
    match Some(2).map(lambda x: x**2), Nothing().map(lambda x: x**2):
        case Some(v), Nothing():
            assert v == 4
        case _:  # pyright: ignore [reportUnnecessaryComparison]
            assert False


def test_match_args():
    match cast(Maybe[int], Some(2)), cast(Maybe[int], Nothing()):
        case Some(v), Nothing():
            assert v == 2
        case _:
            assert False


def test_or_else():
    def f():
        return Some(3)

    match Some(2).or_else(f), Nothing().or_else(f):
        case Some(u), Some(v):
            assert u == 2
            assert v == 3
        case _:
            assert False


def test_or_raise():
    match Some(2).or_raise("error message"):
        case Some(v):
            assert v == 2
        case _:  # pyright: ignore [reportUnnecessaryComparison]
            assert False

    try:
        n = Nothing().or_raise("error message")
        assert_never(n)
    except NothingError as e:
        assert e.args == ("error message",)


def test_or_try():
    def f() -> int:
        return 3

    def g() -> str:
        return "three"

    m = Some(2).or_try(f)
    assert_type(m, Some[int])
    assert m.value == 2

    m = Some(2).or_try(g)
    assert_type(m, Some[int])
    assert m.value == 2

    m = Nothing().or_try(f)
    assert_type(m, Some[int])
    assert m.value == 3

    m = cast(Maybe[int], Some(2)).or_try(f)
    assert_type(m, Some[int])
    assert m.value == 2

    m = cast(Maybe[int], Nothing()).or_try(g)
    assert_type(m, Some[int | str])
    assert m.value == "three"


def test_or_use():
    m = Some(2)
    m2 = m.or_use("three")
    assert_type(m2, Some[int])
    assert m2.value == 2

    m = Nothing()
    m2 = m.or_use("three")
    assert_type(m2, Some[str])
    assert m2.value == "three"

    m = cast(Maybe[int], Some(2))
    m2 = m.or_use("three")
    assert_type(m2, Some[int | str])
    assert m2.value == 2

    m = cast(Maybe[int], Nothing())
    m2 = m.or_use("three")
    assert_type(m2, Some[int | str])
    assert m2.value == "three"


def test_value():
    assert Some(2).value == 2
    with pytest.raises(AttributeError):
        Nothing().value  # pyright: ignore