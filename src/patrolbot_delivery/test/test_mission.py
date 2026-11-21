import pytest

from patrolbot_delivery.mission import code_is_valid, parse_mission


def test_parse_mission():
    assert parse_mission('1.5, -0.5, 1234') == (1.5, -0.5, '1234')


@pytest.mark.parametrize('text', ['1.0,2.0', 'a,b,1234', '1,2,'])
def test_parse_mission_invalid(text):
    with pytest.raises(ValueError):
        parse_mission(text)


def test_code_is_valid():
    assert code_is_valid('1234', '1234')
    assert not code_is_valid('1235', '1234')
