import vampytest

from ..fields import parse_id


def test__parse_id():
    """
    Tests whether ``parse_id`` works as intended.
    """
    for input_data, expected_output in (
        ({}, ''),
        ({'id': None}, ''),
        ({'id': ''}, ''),
        ({'id': 'a'}, 'a'),
    ):
        output = parse_id(input_data)
        vampytest.assert_eq(output, expected_output)
