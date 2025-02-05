import vampytest

from ....user import User

from ..fields import put_user_into


def test__put_user_into():
    """
    Tests whether ``put_user_into`` is working as intended.
    """
    user = User.precreate(202301040013, name = 'Ken')
    
    for input_value, defaults, expected_output in (
        (user, True, {'user': user.to_data(defaults = True, include_internals = True)}),
    ):
        data = put_user_into(input_value, {}, defaults, include_internals = True)
        vampytest.assert_eq(data, expected_output)
