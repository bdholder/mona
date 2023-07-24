# pyright: strict
# pyright: reportUnnecessaryTypeIgnoreComment = true
from typing import cast

import pytest
from typing_extensions import assert_never, assert_type

from mona.maybe import Some, Nothing
from mona.result import Err, Ok, Result, ResultError, is_err, is_ok


def test_err_error():
    ex = Exception()
    e = Err(ex)
    assert e.error is ex


def test_err_value():
    with pytest.raises(AttributeError):
        Err("error").value  # pyright: ignore


def test_get():
    assert Ok(2).get(0) == 2
    assert Err(Exception()).get(0) == 0


def test_is_err():
    ex = Exception()
    r = cast(Result[int, Exception], Err(ex))
    if is_err(r):
        assert_type(r, Err[Exception])
        assert r.error is ex
    else:
        assert False

    r = Ok(2)
    if is_err(r):
        assert_type(r, Ok[int])
        assert False


def test_is_err_non_result():
    assert not is_err(Nothing())  # pyright: ignore [reportGeneralTypeIssues]
    assert not is_err(0)  # pyright: ignore [reportGeneralTypeIssues]


def test_is_ok():
    r = cast(Result[int, Exception], Ok(2))
    if is_ok(r):
        assert_type(r, Ok[int])
        assert r.value == 2
    assert is_ok(r)

    r = Err(Exception())
    if is_ok(r):
        assert_type(r, Err[Exception])
        assert False


def test_is_ok_non_result():
    assert not is_ok(Some("foo"))  # pyright: ignore [reportGeneralTypeIssues]
    assert not is_ok(1)  # pyright: ignore [reportGeneralTypeIssues]


def test_ok_error():
    with pytest.raises(AttributeError):
        Ok(2).error  # pyright: ignore


def test_ok_value():
    print(3)
    assert Ok(2).value == 2


def test_or_try():
    def f(x: int, y: str) -> float:
        return 3.14

    o = Ok(2)
    r = o.or_try(f, 2, "three")
    assert_type(r, Ok[int])
    assert r.value == 2

    e = Err(Exception())
    r = e.or_try(f, 2, "three")
    assert_type(r, Ok[float])
    assert r.value == 3.14

    r = cast(Result[int, Exception], o).or_try(f, 2, "three")

    with pytest.raises(TypeError):
        e.or_try(f, 2)  # pyright: ignore [reportGeneralTypeIssues]

    def g(x: int, *, catch: str) -> float:
        return 3.14

    with pytest.raises(TypeError):
        e.or_try(g, 3, catch=ValueError)  # pyright: ignore [reportGeneralTypeIssues]

    def h(x: int) -> int:
        if x < 0:
            raise ValueError
        return x**2

    r = e.or_try(h, 4, catch=ValueError)
    assert_type(r, Result[int, ValueError])
    assert is_ok(r)
    assert r.value == 16

    r = e.or_try(h, -4, catch=ValueError)
    assert_type(r, Result[int, ValueError])
    assert is_err(r)

    r = o.or_try(h, -4, catch=ValueError)
    assert_type(r, Ok[int])
    assert is_ok(r)
    assert r.value == 2


def test_or_use():
    r = Ok(2).or_use("three")
    assert_type(r, Ok[int])
    assert r.value == 2

    r = Err(Exception()).or_use("three")
    assert_type(r, Ok[str])
    assert r.value == "three"

    r = cast(Result[int, Exception], Ok(2)).or_use("three")
    assert_type(r, Ok[int | str])


def test_unwrap():
    o = Ok(2)
    assert_type(o.unwrap(), int)
    assert o.unwrap() == 2

    e = Err(Exception())
    with pytest.raises(ResultError):
        assert_never(e.unwrap())
    with pytest.raises(ResultError):
        assert_type(cast(Result[str, Exception], e).unwrap(), str)
