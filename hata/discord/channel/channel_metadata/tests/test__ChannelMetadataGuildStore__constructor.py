import vampytest

from ...permission_overwrite import PermissionOverwrite, PermissionOverwriteTargetType

from ..guild_store import ChannelMetadataGuildStore


def assert_fields_set(channel_metadata):
    vampytest.assert_instance(channel_metadata.parent_id, int)
    vampytest.assert_instance(channel_metadata.name, str)
    vampytest.assert_instance(channel_metadata._permission_cache, dict, nullable = True)
    vampytest.assert_instance(channel_metadata.permission_overwrites, dict, nullable = True)
    vampytest.assert_instance(channel_metadata.position, int)
    vampytest.assert_instance(channel_metadata.nsfw, bool)


def test__ChannelMetadataGuildStore__new__0():
    """
    Tests whether ``ChannelMetadataGuildStore.__new__`` works as intended.
    
    Case: all fields given.
    """
    parent_id = 2022091700102
    name = 'Armelyrics'
    permission_overwrites = [
        PermissionOverwrite(202209170103, target_type = PermissionOverwriteTargetType.user)
    ]
    position = 7
    nsfw = True
    
    keyword_parameters = {
        'parent_id': parent_id,
        'name': name,
        'permission_overwrites': permission_overwrites,
        'position': position,
        'nsfw': nsfw,
    }
    channel_metadata = ChannelMetadataGuildStore(keyword_parameters)
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildStore)
    vampytest.assert_eq(keyword_parameters, {})
    
    assert_fields_set(channel_metadata)
    
    
    vampytest.assert_eq(channel_metadata.parent_id, parent_id)
    vampytest.assert_eq(channel_metadata.name, name)
    vampytest.assert_eq(
        channel_metadata.permission_overwrites,
        {permission_overwrite.target_id: permission_overwrite for permission_overwrite in permission_overwrites},
    )
    vampytest.assert_eq(channel_metadata.position, position)
    vampytest.assert_eq(channel_metadata.nsfw, nsfw)


def test__ChannelMetadataGuildStore__new__1():
    """
    Tests whether ``ChannelMetadataGuildStore.__new__`` works as intended.
    
    Case: no fields given.
    """
    keyword_parameters = {}
    
    channel_metadata = ChannelMetadataGuildStore(keyword_parameters)
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildStore)
    vampytest.assert_eq(keyword_parameters, {})
    
    assert_fields_set(channel_metadata)


def test__ChannelMetadataGuildStore__create_empty():
    """
    Tests whether ``ChannelMetadataGuildStore._create_empty`` works as intended.
    """
    channel_metadata = ChannelMetadataGuildStore._create_empty()
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildStore)
    
    assert_fields_set(channel_metadata)



def test__ChannelMetadataGuildStore__precreate__0():
    """
    Tests whether ``ChannelMetadataGuildStore.precreate`` works as intended.
    
    Case: all fields given.
    """
    parent_id = 202209170104
    name = 'Armelyrics'
    permission_overwrites = [
        PermissionOverwrite(202209170105, target_type = PermissionOverwriteTargetType.user)
    ]
    position = 7
    nsfw = True
    
    keyword_parameters = {
        'parent_id': parent_id,
        'name': name,
        'permission_overwrites': permission_overwrites,
        'position': position,
        'nsfw': nsfw,
    }
    
    channel_metadata = ChannelMetadataGuildStore.precreate(keyword_parameters)
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildStore)
    vampytest.assert_eq(keyword_parameters, {})
    
    assert_fields_set(channel_metadata)
    
    vampytest.assert_eq(channel_metadata.parent_id, parent_id)
    vampytest.assert_eq(channel_metadata.name, name)
    vampytest.assert_eq(
        channel_metadata.permission_overwrites,
        {permission_overwrite.target_id: permission_overwrite for permission_overwrite in permission_overwrites},
    )
    vampytest.assert_eq(channel_metadata.position, position)
    vampytest.assert_eq(channel_metadata.nsfw, nsfw)


def test__ChannelMetadataGuildStore__precreate__1():
    """
    Tests whether ``ChannelMetadataGuildStore.precreate`` works as intended.
    
    Case: no fields given.
    """
    keyword_parameters = {}
    
    channel_metadata = ChannelMetadataGuildStore.precreate(keyword_parameters)
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildStore)
    vampytest.assert_eq(keyword_parameters, {})
    
    assert_fields_set(channel_metadata)
