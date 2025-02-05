import vampytest

from ....bases import Icon, IconType
from ....color import Color
from ....localization import Locale
from ....user import PremiumType, UserFlag

from ...oauth2_access import Oauth2Access

from ..oauth2_user import Oauth2User


def _assert_fields_set(user):
    """
    Asserts whether every fields of the given user are set.
    
    Parameters
    ----------
    user : ``User``
        The user to check.
    """
    vampytest.assert_instance(user, Oauth2User)
    vampytest.assert_instance(user.access, Oauth2Access)
    vampytest.assert_instance(user.avatar, Icon)
    vampytest.assert_instance(user.avatar_decoration, Icon)
    vampytest.assert_instance(user.banner, Icon)
    vampytest.assert_instance(user.banner_color, Color, nullable = True)
    vampytest.assert_instance(user.discriminator, int)
    vampytest.assert_instance(user.flags, UserFlag)
    vampytest.assert_instance(user.id, int)
    vampytest.assert_instance(user.name, str)
    vampytest.assert_instance(user.email, str, nullable = True)
    vampytest.assert_instance(user.email_verified, bool)
    vampytest.assert_instance(user.locale, Locale)
    vampytest.assert_instance(user.mfa, bool)
    vampytest.assert_instance(user.premium_type, PremiumType)


def test__Oauth2User__new__0():
    """
    Tests whether ``Oauth2User.__new__`` works as intended.
    
    Case: No fields given.
    """
    user = Oauth2User()
    _assert_fields_set(user)


def test__Oauth2User__new__1():
    """
    Tests whether ``Oauth2User.__new__`` works as intended.
    
    Case: All fields given.
    """
    avatar = Icon(IconType.static, 32)
    avatar_decoration = Icon(IconType.animated_apng, 25)
    banner = Icon(IconType.animated, 12)
    banner_color = Color(1236)
    discriminator = 2222
    flags = UserFlag(1)
    name = 'voice in the dark'
    email = 'rin@orindance.party'
    email_verified = True
    locale = Locale.greek
    mfa = True
    premium_type = PremiumType.nitro
    
    user = Oauth2User(
        avatar = avatar,
        avatar_decoration = avatar_decoration,
        banner = banner,
        banner_color = banner_color,
        discriminator = discriminator,
        flags = flags,
        name = name,
        email = email,
        email_verified = email_verified,
        locale = locale,
        mfa = mfa,
        premium_type = premium_type,
    )
    _assert_fields_set(user)
    
    vampytest.assert_eq(user.avatar, avatar)
    vampytest.assert_eq(user.avatar_decoration, avatar_decoration)
    vampytest.assert_eq(user.banner, banner)
    vampytest.assert_eq(user.banner_color, banner_color)
    vampytest.assert_eq(user.discriminator, discriminator)
    vampytest.assert_eq(user.flags, flags)
    vampytest.assert_eq(user.name, name)
    vampytest.assert_eq(user.email, email)
    vampytest.assert_eq(user.email_verified, email_verified)
    vampytest.assert_is(user.locale, locale)
    vampytest.assert_eq(user.mfa, mfa)
    vampytest.assert_is(user.premium_type, premium_type)


def test__Oauth2User__create_empty():
    """
    Tests whether ``Oauth2User._create_empty`` works as intended.
    """
    user_id = 202302040022
    user = Oauth2User._create_empty(user_id)
    _assert_fields_set(user)
    
    vampytest.assert_eq(user.id, user_id)
