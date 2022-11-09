# pyright: strict
from typing import cast

import pytest

from mona.maybe import Some, Nothing
from mona.result import Err, Ok, Result, is_err, is_ok


def test_err_error():
    e = Err("error")
    assert e.error == "error"


def test_err_value():
    with pytest.raises(AttributeError):
        Err("error").value  # type: ignore


def test_get():
    assert Ok(2).get(0) == 2
    assert Err("error").get(0) == 0


def test_is_err():
    r = cast(Result[int, str], Err("error"))
    if is_err(r):
        assert r.error == "error"
    assert is_err(r)
    assert not is_err(Ok(2))


def test_is_err_non_result():
    assert not is_err(Nothing())  # type: ignore
    assert not is_err(0)  # type: ignore


def test_is_ok():
    r = cast(Result[int, str], Ok(2))
    if is_ok(r):
        assert r.value == 2
    assert is_ok(r)
    assert not is_ok(Err("error"))


def test_is_ok_non_result():
    assert not is_ok(Some("foo"))  # type: ignore
    assert not is_ok(1)  # type: ignore


def test_ok_error():
    with pytest.raises(AttributeError):
        Ok(2).error  # type: ignore


def test_ok_value():
    o = Ok(2)
    assert o.value == 2