import vampytest

from ....bases import Icon, IconType
from ....color import Color

from ..flags import UserFlag
from ..orin_user_base import OrinUserBase

from .test__OrinUserBase__constructor import _assert_fields_set


def test__OrinUserBase__copy():
    """
    Tests whether ``OrinUserBase.copy`` works as intended.
    """
    avatar = Icon(IconType.static, 14)
    avatar_decoration = Icon(IconType.animated_apng, 25)
    banner = Icon(IconType.animated, 12)
    banner_color = Color(1236)
    discriminator = 2222
    flags = UserFlag(1)
    name = 'orin'
    
    user = OrinUserBase(
        avatar = avatar,
        avatar_decoration = avatar_decoration,
        banner = banner,
        banner_color = banner_color,
        discriminator = discriminator,
        flags = flags,
        name = name,
    )
    
    copy = user.copy()
    _assert_fields_set(copy)
    vampytest.assert_is_not(user, copy)
    
    vampytest.assert_eq(user, copy)


def test__OrinUserBase__copy_with__0():
    """
    Tests whether ``OrinUserBase.copy_with`` works as intended.
    
    Case: No fields given.
    """
    avatar = Icon(IconType.static, 14)
    avatar_decoration = Icon(IconType.animated_apng, 25)
    banner = Icon(IconType.animated, 12)
    banner_color = Color(1236)
    discriminator = 2222
    flags = UserFlag(1)
    name = 'orin'
    
    user = OrinUserBase(
        avatar = avatar,
        avatar_decoration = avatar_decoration,
        banner = banner,
        banner_color = banner_color,
        discriminator = discriminator,
        flags = flags,
        name = name,
    )
    
    copy = user.copy_with()
    _assert_fields_set(copy)
    vampytest.assert_is_not(user, copy)
    
    vampytest.assert_eq(user, copy)


def test__OrinUserBase__copy_with__1():
    """
    Tests whether ``OrinUserBase.copy_with`` works as intended.
    
    Case: All fields given.
    """
    old_avatar = Icon(IconType.static, 14)
    old_avatar_decoration = Icon(IconType.animated_apng, 25)
    old_banner = Icon(IconType.static, 15)
    old_banner_color = Color(1236)
    old_discriminator = 2222
    old_flags = UserFlag(1)
    old_name = 'orin'
    
    new_avatar = Icon(IconType.animated, 23)
    new_avatar_decoration = Icon(IconType.static, 11)
    new_banner = Icon(IconType.static, 10)
    new_banner_color = Color(1236)
    new_discriminator = 1
    new_flags = UserFlag(2)
    new_name = 'okuu'
    
    user = OrinUserBase(
        avatar = old_avatar,
        avatar_decoration = old_avatar_decoration,
        banner = old_banner,
        banner_color = old_banner_color,
        discriminator = old_discriminator,
        flags = old_flags,
        name = old_name,
    )
    
    copy = user.copy_with(
        avatar = new_avatar,
        avatar_decoration = new_avatar_decoration,
        banner = new_banner,
        banner_color = new_banner_color,
        discriminator = new_discriminator,
        flags = new_flags,
        name = new_name,
    )
    _assert_fields_set(copy)
    vampytest.assert_is_not(user, copy)
    
    vampytest.assert_eq(copy.avatar, new_avatar)
    vampytest.assert_eq(copy.avatar_decoration, new_avatar_decoration)
    vampytest.assert_eq(copy.banner, new_banner)
    vampytest.assert_eq(copy.banner_color, new_banner_color)
    vampytest.assert_eq(copy.discriminator, new_discriminator)
    vampytest.assert_eq(copy.flags, new_flags)
    vampytest.assert_eq(copy.name, new_name)
