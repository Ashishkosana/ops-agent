from ranges import inclusive_upto


def test_inclusive_upto() -> None:
    assert inclusive_upto(3) == [0, 1, 2, 3]
    assert inclusive_upto(0) == [0]
