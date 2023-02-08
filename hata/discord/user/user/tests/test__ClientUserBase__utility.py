import vampytest

from ....bases import Icon, IconType
from ....color import Color

from ..flags import UserFlag
from ..client_user_base import ClientUserBase

from .test__ClientUserBase__constructor import _assert_fields_set


def test__ClientUserBase__copy():
    """
    Tests whether ``ClientUserBase.copy`` works as intended.
    """
    avatar = Icon(IconType.static, 14)
    banner = Icon(IconType.animated, 12)
    banner_color = Color(1236)
    discriminator = 2222
    flags = UserFlag(1)
    name = 'orin'
    bot = True
    
    user = ClientUserBase(
        avatar = avatar,
        banner = banner,
        banner_color = banner_color,
        discriminator = discriminator,
        flags = flags,
        name = name,
        bot = bot,
    )
    
    copy = user.copy()
    _assert_fields_set(copy)
    vampytest.assert_is_not(user, copy)
    
    vampytest.assert_eq(user, copy)


def test__ClientUserBase__copy_with__0():
    """
    Tests whether ``ClientUserBase.copy_with`` works as intended.
    
    Case: No fields given.
    """
    avatar = Icon(IconType.static, 14)
    banner = Icon(IconType.animated, 12)
    banner_color = Color(1236)
    discriminator = 2222
    flags = UserFlag(1)
    name = 'orin'
    bot = True
    
    user = ClientUserBase(
        avatar = avatar,
        banner = banner,
        banner_color = banner_color,
        discriminator = discriminator,
        flags = flags,
        name = name,
        bot = bot,
    )
    
    copy = user.copy_with()
    _assert_fields_set(copy)
    vampytest.assert_is_not(user, copy)
    
    vampytest.assert_eq(user, copy)


def test__ClientUserBase__copy_with__1():
    """
    Tests whether ``ClientUserBase.copy_with`` works as intended.
    
    Case: All fields given.
    """
    old_avatar = Icon(IconType.static, 14)
    old_banner = Icon(IconType.static, 15)
    old_banner_color = Color(1236)
    old_discriminator = 2222
    old_flags = UserFlag(1)
    old_name = 'orin'
    old_bot = True
    
    new_avatar = Icon(IconType.animated, 23)
    new_banner = Icon(IconType.static, 10)
    new_banner_color = Color(1236)
    new_discriminator = 1
    new_flags = UserFlag(2)
    new_name = 'okuu'
    new_bot = False
    
    user = ClientUserBase(
        avatar = old_avatar,
        banner = old_banner,
        banner_color = old_banner_color,
        discriminator = old_discriminator,
        flags = old_flags,
        name = old_name,
        bot = old_bot,
    )
    
    copy = user.copy_with(
        avatar = new_avatar,
        banner = new_banner,
        banner_color = new_banner_color,
        discriminator = new_discriminator,
        flags = new_flags,
        name = new_name,
        bot = new_bot,
    )
    _assert_fields_set(copy)
    vampytest.assert_is_not(user, copy)
    
    vampytest.assert_eq(copy.avatar, new_avatar)
    vampytest.assert_eq(copy.banner, new_banner)
    vampytest.assert_eq(copy.banner_color, new_banner_color)
    vampytest.assert_eq(copy.discriminator, new_discriminator)
    vampytest.assert_eq(copy.flags, new_flags)
    vampytest.assert_eq(copy.name, new_name)
    vampytest.assert_eq(copy.bot, new_bot)
