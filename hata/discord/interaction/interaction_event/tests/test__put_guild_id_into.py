import vampytest

from ..fields import put_guild_id_into


def test__put_guild_id_into():
    """
    Tests whether ``put_guild_id_into`` works as intended.
    """
    guild_id = 202301040002
    
    for input_value, defaults, expected_output in (
        (0, False, {}),
        (0, True, {'guild_id': None}),
        (guild_id, False, {'guild_id': str(guild_id)}),
    ):
        output = put_guild_id_into(input_value, {}, defaults)
        vampytest.assert_eq(output, expected_output)
