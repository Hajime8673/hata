import vampytest

from ....user import User, ZEROUSER

from ..fields import put_bot_into


def test__put_bot_into():
    """
    Tests whether ``put_bot_into`` is working as intended.
    """
    user = User.precreate(202210080010, name = 'Ken', bot = True)
    
    for input_value, defaults, expected_output in (
        (ZEROUSER, True, {'bot': None}),
        (ZEROUSER, False, {}),
        (user, True, {'bot': user.to_data(defaults = True, include_internals = True)}),
    ):
        data = put_bot_into(input_value, {}, defaults, include_internals = True)
        vampytest.assert_eq(data, expected_output)
