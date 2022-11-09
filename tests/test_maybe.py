# pyright: strict
import math
from typing import cast
from unittest.mock import MagicMock

import pytest

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
    m.foo.return_value = None  # type: ignore
    match Some(m).apply(lambda x: x.foo()):  # type: ignore
        case Some(v):
            assert v is m
            v.foo.assert_called_once()  # type: ignore
        case _:
            assert False
    
    assert isinstance(Nothing().apply(lambda x: x.foo()), Nothing)


def test_assign_value():
    s = Some(2)
    with pytest.raises(AttributeError):
        s.value = 3  # type: ignore
    n = Nothing()
    with pytest.raises(AttributeError):
        n.value = 2  # type: ignore


def test_get():
    assert Some(2).get(0) == 2
    assert Nothing().get(0) == 0


def test_is_some():
    s = cast(Maybe[int], Some(2))
    assert is_some(s)
    if is_some(s):
        assert s.value == 2  # There shouldn't be a type error here.

    assert not is_some(Nothing())


def test_is_some_non_maybe():
    assert not is_some(Ok("foo"))  # type: ignore
    assert not is_some(1)  # type: ignore


def test_map():
    match Some(2).map(lambda x: x**2), Nothing().map(lambda x: x**2):
        case Some(v), Nothing():
            assert v == 4
        case _:
            assert False


def test_match_args():
    match cast(Maybe[int], Some(2)), cast(Maybe[int], Nothing()):
        case Some(v), Nothing():
            assert v == 2
        case _:
            assert False


def test_or_else():
    f = lambda: Some(3)
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
        case _:
            assert False

    try:
        Nothing().or_raise("error message")
    except NothingError as e:
        assert e.args == ("error message",)
    else:
        assert False


def test_value():
    assert Some(2).value == 2
    with pytest.raises(AttributeError):
        Nothing().value  # type: ignore # This is correctly flagged as an error.