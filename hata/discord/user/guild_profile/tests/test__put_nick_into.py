import vampytest

from ..fields import put_nick_into


def test__put_nick_into():
    """
    Tests whether ``put_nick_into`` is working as intended.
    """
    for input_, defaults, expected_output in (
        (None, False, {}),
        ('a', False, {'nick': 'a'}),
    ):
        data = put_nick_into(input_, {}, defaults)
        vampytest.assert_eq(data, expected_output)
