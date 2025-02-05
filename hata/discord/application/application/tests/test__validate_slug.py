import vampytest

from ..fields import validate_slug


def test__validate_slug__0():
    """
    Tests whether `validate_slug` works as intended.
    
    Case: passing.
    """
    for input_value, expected_output in (
        (None, None),
        ('', None),
        ('https://orindance.party/', 'https://orindance.party/'),
    ):
        output = validate_slug(input_value)
        vampytest.assert_eq(output, expected_output)


def test__validate_slug__1():
    """
    Tests whether `validate_slug` works as intended.
    
    Case: `ValueError`.
    """
    for input_value in (
        'a',
    ):
        with vampytest.assert_raises(ValueError):
            validate_slug(input_value)


def test__validate_slug__2():
    """
    Tests whether `validate_slug` works as intended.
    
    Case: `TypeError`.
    """
    for input_value in (
        12.6,
    ):
        with vampytest.assert_raises(TypeError):
            validate_slug(input_value)
