# -*- coding: utf-8 -*-
__all__ = ('CheckBase', )

from ...backend.futures import Task
from ...backend.analyzer import CallableAnalyzer
from ...backend.utils import copy_docs

from ...discord.client_core import KOKORO
from ...discord.bases import instance_or_id_to_instance, instance_or_id_to_snowflake
from ...discord.guild import Guild
from ...discord.permission import Permission
from ...discord.role import Role
from ...discord.channel import ChannelBase, ChannelText, ChannelCategory, ChannelGuildBase, ChannelPrivate, \
    ChannelGroup
from ...discord.client import Client


def _convert_permission(permission):
    """
    Validates the given `permission`.
    
    Parameters
    ----------
    permission : `None`, ``Permission`` or `int` instance.
        Permission to validate.
    
    Returns
    -------
    permissions : ``Permission``
    
    Raises
    ------
    TypeError
        If `permissions` was not given as `None`, ``Permission`` nor as `int` instance.
    """
    if permission is None:
        permission = Permission()
    else:
        if type(permission) is Permission:
            pass
        elif isinstance(permission, int):
            permission = Permission(permission)
        else:
            raise TypeError(f'`permission` can be given as `None`, `{Permission.__name__}` or as `int` instance, got '
                f'{permission.__class__.__name__}.')
    
    return permission


class CheckMeta(type):
    """
    Check metaclass for collecting their `__slots__` in a `__all_slot__` class attribute.
    """
    def __new__(cls, class_name, class_parents, class_attributes):
        """
        Parameters
        ----------
        class_name : `str`
            The created class's name.
        class_parents : `tuple` of `type` instances
            The superclasses of the creates type.
        class_attributes : `dict` of (`str`, `Any`) items
            The class attributes of the created type.
        
        Returns
        -------
        type : ``CheckMeta`` instance
        """
        if class_parents:
            parent = class_parents[0]
            inherited_slots = getattr(parent, '__all_slot__', None)
        else:
            inherited_slots = None
        
        new_slots = class_attributes.get('__slots__', None)
        
        final_slots = []
        if (inherited_slots is not None):
            final_slots.extend(inherited_slots)
        
        if (new_slots is not None):
            final_slots.extend(new_slots)
        
        class_attributes['__all_slot__'] = tuple(final_slots)
        
        return type.__new__(cls, class_name, class_parents, class_attributes)


class CheckBase(metaclass=CheckMeta):
    """
    Base class for checks.
    """
    __slots__ = ()
    def __new__(cls):
        """
        Creates a new check instance.
        
        Subclasses should overwrite it.
        """
        return object.__new__(cls)
    
    async def __call__(client, context):
        """
        Returns whether the check's condition passes.
        
        Subclasses should overwrite it.
        
        This method is a coroutine.
        
        Parameters
        ----------
        context : ``CommandContext``
            Processing context for the respective command.
        
        Returns
        -------
        passed : `bool`
            Whether the check passed.
        """
    
    def __repr__(self):
        """Returns the check's representation."""
        result = [
            self.__class__.__name__,
            '(',
                ]
        
        slots = self.__all_slot__
        limit = len(slots)
        if limit:
            index = 0
            while True:
                name = slots[index]
                index += 1
                if name.startswith('_'):
                    if index == limit:
                        break
                    else:
                        continue
                
                # case of `channel_id`, `guild_id`
                if name.endswith('id'):
                    display_name = name[:-3]
                # case of `channel_ids`, `guild_ids`
                elif name.endswith('ids'):
                    display_name = name[:-4]
                else:
                    display_name = name
                
                result.append(display_name)
                result.append('=')
                attr = getattr(self,name)
                result.append(repr(attr))
                
                if index == limit:
                    break
                
                result.append(', ')
                continue
        
        result.append(')')
        
        return ''.join(result)


class CheckHasRole(CheckBase):
    """
    Checks whether the message's author has the given role.
    
    Attributes
    ----------
    role : ``Role``
        The legend itself.
    """
    __slots__ = ('role', )
    def __new__(cls, role):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        role : `str`, `int` or ``Role``
            The role what the message's author should have.
        
        Raises
        ------
        TypeError
            If `role` was not given neither as ``Role``, `str` or `int` instance.
        ValueError
            If `role` was given as `str` or as `int` instance, but not as a valid snowflake, so ``Role`` instance
            cannot be precreated with it.
        """
        role = instance_or_id_to_instance(role, Role, 'role')
        
        self = object.__new__(cls)
        self.role = role
        return self
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if context.message.author.has_role(self.role):
            return True
        
        return False


class CheckIsOwnerOrHasRole(CheckHasRole):
    """
    Checks whether the message's author has the given role, or if it the client's owner.
    
    Attributes
    ----------
    role : ``Role``
        The legend itself.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        user = context.message.author
        if user.has_role(self.role):
            return True
        
        if context.client.is_owner(user):
            return True
        
        return False


class CheckHasAnyRole(CheckBase):
    """
    Checks whether the message's author has any of the given roles.
    
    Attributes
    ----------
    roles : `set` of ``Role``
        The legends themselves.
    """
    __slots__ = ('roles', )
    def __new__(cls, *roles):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        *roles : `str`, `int` or ``Role``
            Role from which the message's author should have at least one.
        
        Raises
        ------
        TypeError
            If a role was not given neither as ``Role``, `str` or `int` instance.
        ValueError
            If a role was given as `str` or as `int` instance, but not as a valid snowflake, so a ``Role`` instance
            cannot be precreated with it.
        """
        roles_processed = set()
        for role in roles:
            role = instance_or_id_to_instance(role, Role, 'role')
            roles_processed.add(role)
        
        roles_processed_length = len(roles_processed)
        if roles_processed_length == 0:
            return CheckBase()
        
        if roles_processed_length == 1:
            return CheckHasRole(roles_processed.pop())
        
        self = object.__new__(cls)
        self.roles = roles_processed
        return self
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        user = context.message.author
        for role in self.roles:
            if  user.has_role(role):
                return True
        
        return False


class CheckIsOwnerOrHasAnyRole(CheckHasAnyRole):
    """
    Checks whether the message's author has any of the given roles, or whether is it the client's owner.
    
    Attributes
    ----------
    roles : `set` of ``Role``
        The roles from what the user should have at least 1.
    """
    __slots__ = ()
    def __new__(cls, *roles):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        *roles : `str`, `int` or ``Role``
            Role from which the message's author should have at least one.
        
        Raises
        ------
        TypeError
            If an element of role was not given neither as ``Role``, `str` or `int` instance.
        ValueError
            If a role was given as `str` or as `int` instance, but not as a valid snowflake, so a ``Role`` instance
            cannot be precreated with it.
        """
        roles_processed = set()
        for role in roles:
            role = instance_or_id_to_instance(role, Role, 'role')
            roles_processed.add(role)
        
        roles_processed_length = len(roles_processed)
        if roles_processed_length == 0:
            return CheckIsOwner()
        
        if roles_processed_length == 1:
            return CheckIsOwnerOrHasRole(roles_processed.pop())
        
        self = object.__new__(cls)
        self.roles = roles_processed
        return self
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        user = context.message.author
        for role in self.roles:
            if  user.has_role(role):
                return True
        
        if context.client.is_owner(user):
            return True
        
        return False


class CheckIsInGuild(CheckHasAnyRole):
    """
    Checks whether the command was called from a guild.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if isinstance(context.message.channel, ChannelGuildBase):
            return True
        
        return False


class CheckIsInPrivate(CheckHasAnyRole):
    """
    Checks whether the command was used inside of a private channel.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if isinstance(context.message.channel, (ChannelPrivate, ChannelGroup)):
            return True
        
        return False


class CheckIsOwner(CheckBase):
    """
    Checks whether the command was called by the client's owner.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if context.client.is_owner(context.message.author):
            return True
        
        return False


class CheckIsGuildOwner(CheckBase):
    """
    Checks whether the command was called by the local guild's owner.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        message = context.context
        guild = message.channel.guild
        if guild is None:
            return False
        
        if guild.owner_id == message.author.id:
            return True
        
        return False


class CheckIsOwnerOrIsGuildOwner(CheckBase):
    """
    Checks whether a message was sent by the message's guild's owner or by the client's owner.
    
    > Guild check is always applied.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        message = context.context
        guild = message.channel.guild
        if guild is None:
            return False
        
        user = message.author
        if guild.owner_id == user.id:
            return True
        
        if context.client.is_owner(user):
            return True
        
        return False


class CheckHasPermission(CheckBase):
    """
    Checks whether the message's author has the given permissions in the message's channel.
    
    Attributes
    ----------
    permission : ``Permission``
        The required permissions to pass the check.
    """
    __slots__ = ('permission', )
    
    def __new__(cls, permission=None, **kwargs):
        """
        Creates a check, which will validate whether the a received message of a client passes the given condition.
        
        Parameters
        ----------
        permissions : `None`, ``Permission`` or `int` instance, Optional
            The permission, which the respective user should have. Defaults to `None`
        **kwargs : Keyword parameters
            `permission-name` - `bool` relations.
        
        Raises
        ------
        LookupError
            If a keyword is not a valid permission name.
        TypeError
            If `permission` was not given neither as `None`, ``Permission`` nor as `int` instance.
        """
        permission = _convert_permission(permission)
        permission = permission.update_by_keys(**kwargs)
        
        self = object.__new__(cls)
        self.permission = permission
        return self
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        message = context.message
        if message.channel.permissions_for(message.author) >= self.permission:
            return True
        
        return False


class CheckIsOwnerOrHasPermission(CheckHasPermission):
    """
    Checks whether the message's author is the client's owner or has the given permissions in the message's channel.
    
    Attributes
    ----------
    permission : ``Permission``
        The required permissions to pass the check.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        message = context.message
        user = message.author
        if message.channel.permissions_for(user) >= self.permission:
            return True
        
        if context.client.is_owner(user):
            return True
        
        return False
    

class CheckHasGuildPermission(CheckHasPermission):
    """
    Checks whether the message's author has the given permissions in the message's guild.
    
    Attributes
    ----------
    permission : ``Permission``
        The required permissions to pass the check.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        message = context.message
        guild = message.channel.guild
        if guild is None:
            return False
        
        if guild.permissions_for(message.author) >= self.permission:
            return True
        
        return False


class CheckIsOwnerHasGuildPermission(CheckHasGuildPermission):
    """
    Checks whether the message's author has the given permissions in the message's guild.
    
    > Guild check is always applied.
    
    Attributes
    ----------
    permission : ``Permission``
        The required permissions to pass the check.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        message = context.message
        guild = message.channel.guild
        if guild is None:
            return False
        
        user = message.author
        if guild.permissions_for(user) >= self.permission:
            return True
        
        if context.client.is_owner(user):
            return True
        
        return False


class CheckHasClientPermission(CheckHasPermission):
    """
    Checks whether the client has the given permissions in the message's channel.
    
    ----------
    permission : ``Permission``
        The required permissions to pass the check.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if context.message.channel.cached_permissions_for(context.client) >= self.permission:
            return True
        
        return False


class CheckHasClientGuildPermission(CheckHasClientPermission):
    """
    Checks whether the client has the given permissions in the message's guild.
    
    ----------
    permission : ``Permission``
        The required permissions to pass the check.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        guild = context.message.channel.guild
        if guild is None:
            return False
        
        if guild.cached_permissions_for(context.client) >= self.permission:
            return True
        
        return False


class CheckIsGuild(CheckBase):
    """
    Checks whether the message was sent to the given guild.
    
    Attributes
    ----------
    guild_id : `int`
        The respective guild's id.
    """
    __slots__ = ('guild_id', )
    def __new__(cls, guild):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        guild : `str`, `int` or ``Guild``
            The guild where the message should be sent.
        
        Raises
        ------
        TypeError
            If `guild` was not given neither as ``Guild``, `str` or `int` instance.
        ValueError
            If `guild` was given as `str` or as `int` instance, but not as a valid snowflake.
        """
        guild_id = instance_or_id_to_snowflake(guild, Guild, 'guild')
        
        self = object.__new__(cls)
        self.guild_id = guild_id
        return self

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        guild = context.message.channel.guild
        if guild is None:
            return False
        
        if (guild.id == self.guild_id):
            return True
        
        return False


class CheckIsAnyGuild(CheckBase):
    """
    Checks whether the message was sent into any of the given guilds.
    
    Attributes
    ----------
    guild_ids : `set` of `int`
        The respective guilds' identifiers.
    """
    __slots__ = ('guild_ids', )
    def __new__(cls, *guilds):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        *guilds : `str`, `int` or ``Guild``
            The guilds where the message should be sent.
        
        Raises
        ------
        TypeError
            If a guild was not given neither as ``Guild``, `str` or `int` instance.
        ValueError
            If a guild was given as `str` or as `int` instance, but not as a valid snowflake.
        """
        guild_ids_processed = set()
        
        for guild in guilds:
            guild_id = instance_or_id_to_snowflake(guild, Guild, 'guild')
            guild_ids_processed.add(guild_id)
        
        guild_ids_processed_length = len(guild_ids_processed)
        if guild_ids_processed_length == 0:
            return CheckBase()
        
        if guild_ids_processed_length == 1:
            return CheckIsGuild(guild_ids_processed.pop())
        
        self = object.__new__(cls)
        self.guild_ids = guild_ids_processed
        return self
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        guild = context.message.channel.guild
        if guild is None:
            return False
        
        if (guild.id in self.guild_ids):
            return True
        
        return False


class CheckCustom(CheckBase):
    """
    Does a custom check.
    
    Attributes
    ----------
    _is_async : `bool`
        Whether ``.check`` is async.
    check : `callable`
        The custom check's function.
    """
    __slots__ = ('_is_async', 'check', )

    def __new__(cls, check):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        check : `callable`
            The custom check which should pass. Can be async.
        
        Raises
        ------
        TypeError
            - If `check` was not given as an `callable`.
            - If `check` accepts more or less non reserved positional non default arguments.
        
        Notes
        -----
        Only `int` instances are evaluated to boolean.
        """
        analyzer = CallableAnalyzer(check)
        non_reserved_positional_argument_count = analyzer.get_non_reserved_positional_argument_count()
        if  non_reserved_positional_argument_count != 1:
            raise TypeError(f'The passed check: {check!r} should have accept `1` non reserved, positional, '
                f'non default arguments, meanwhile it accepts `{non_reserved_positional_argument_count}`.')
        
        is_async = analyzer.is_async()
        
        self = object.__new__(cls)
        self.check = check
        self._is_async = is_async
        return self
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        try:
            result = self.check(context)
            if self._is_async:
                result = await result
        except BaseException as err:
            client = context.client
            Task(client.events.error(client, repr(self), err), KOKORO)
            return False
        
        if result is None:
            return False
        
        if isinstance(result, int) and result:
            return True
        
        return False


class CheckIsChannel(CheckBase):
    """
    Checks whether the message was sent to the given channel.
    
    Attributes
    ----------
    channel_id : `int`
        The respective channel's id.
    """
    __slots__ = ('channel_id', )
    def __new__(cls, channel):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        channel : `str`, `int` or ``Guild``
            The guild where the message should be sent.
        
        Raises
        ------
        TypeError
            If `channel` was not given neither as ``ChannelBase``, `str` or `int` instance.
        ValueError
            If `channel` was given as `str` or as `int` instance, but not as a valid snowflake.
        """
        channel_id = instance_or_id_to_snowflake(channel, ChannelBase, 'channel')
        
        self = object.__new__(cls)
        self.channel_id = channel_id
        return self

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if (context.message.channel.id == self.channel_id):
            return True
        
        return False


class CheckIsAnyChannel(CheckBase):
    """
    Checks whether the message was sent into any of the given channels.
    
    Attributes
    ----------
    channel_ids : `set` of `int`
        The respective channels' identifiers.
    """
    __slots__ = ('channel_ids', )
    def __new__(cls, *channels):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        *channels : `str`, `int` or ``ChannelBase``
            The channel where the message should be sent.
        
        Raises
        ------
        TypeError
            If a channel was not given neither as ``ChannelBase``, `str` or `int` instance.
        ValueError
            If a channel was given as `str` or as `int` instance, but not as a valid snowflake.
        """
        channel_ids_processed = set()
        
        for channel in channels:
            channel_id = instance_or_id_to_snowflake(channel, ChannelBase, 'guild')
            channel_ids_processed.add(channel_id)
        
        channel_ids_processed_length = len(channel_ids_processed)
        if channel_ids_processed_length == 0:
            return CheckBase()
        
        if channel_ids_processed_length == 1:
            return CheckIsChannel(channel_ids_processed.pop())
        
        self = object.__new__(cls)
        self.channel_ids = channel_ids_processed
        return self
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if (context.message.channel.id in self.channel_ids):
            return True
        
        return False


class CheckIsNsfwChannel(CheckBase):
    """
    Checks whether the message was sent to an nsfw channel.
    """
    __slots__ = ()

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        channel = context.message.channel
        if (isinstance(channel, ChannelText) and channel.nsfw):
            return True
        
        return False


class CheckIsAnnouncementChannel(CheckBase):
    """
    Checks whether the message was sent to an announcement channel.
    """
    __slots__ = ()

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if context.message.channel.type == 5:
            return True
        
        return False


class CheckIsInVoice(CheckBase):
    """
    Checks whether the message's author is in a voice channel in the respective guild.
    """
    __slots__ = ()

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        message = context.message
        guild = message.channel.guild
        if guild is None:
            return False
        
        if message.author.id in guild.voice_states:
            return True
        
        return False


class CheckIsBooster(CheckBase):
    """
    Checks whether the message's author boosts the respective guild.
    """
    __slots__ = ()

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        message = context.message
        guild = message.channel.guild
        if guild is None:
            return
        
        try:
            profile = message.author.guild_profiles[guild]
        except KeyError:
            return False
        
        if profile.boosts_since is None:
            return False
        
        return True


class CheckIsClient(CheckBase):
    """
    Check whether the message was sent by a client.
    """
    __slots__ = ()

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if isinstance(context.message.author, Client):
            return True
        
        return False


class CheckUserAccount(CheckBase):
    """
    Checks whether the message was sent by an user account.
    """
    __slots__ = ()

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if not context.message.author.is_bot:
            return True
        
        return False


class CheckBotAccount(CheckBase):
    """
    Checks whether the message was sent by a bot account.
    """
    __slots__ = ()

    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        if context.message.author.is_bot:
            return True
        
        return False


class CheckIsUserAccountOrIsClient(CheckBase):
    """
    Checks whether the message was sent by a user account or by a client.
    """
    __slots__ = ()
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        user = context.message.author
        if not user.is_bot:
            return True
        
        if isinstance(user, Client):
            return True
        
        return False


class CheckIsCategory(CheckBase):
    """
    Checks whether the message was sent into any channel of the given category.
    Attributes
    ----------
    category_id : `int`
        The respective category's id.
    """
    __slots__ = ('category_id', )
    def __new__(cls, category):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        category : `str`, `int`, ``ChannelCategory`` or ``Guild``
            The category, within sent messages pass the check.
            
            If you want to check whether the channel is not in a category, pass the parameter as the respective guild
            instead.
        
        Raises
        ------
        TypeError
            If `category` was not given neither as ``ChannelCategory``, ``Guild``, `str` or `int` instance.
        ValueError
            If `category` was given as `str` or as `int` instance, but not as a valid snowflake.
        """
        category_id = instance_or_id_to_snowflake(category, (ChannelCategory, Guild), 'category')
        
        self = object.__new__(cls)
        self.category_id = category_id
        return self
    
    @copy_docs(CheckBase.__call__)
    async def __call__(self, context):
        channel = context.message.channel
        if not isinstance(channel, ChannelGuildBase):
            return False
        
        category = channel.category
        if category is None:
            return False
        
        if category.id == self.category_id:
            return True
        
        return False

class CheckIsAnyCategory(CheckBase):
    """
    Checks whether the message was sent into any channel of the given categories.
    
    Attributes
    ----------
    category_ids : `set` of `int`
        The respective categories' id.
    """
    __slots__ = ('category_ids', )
    def __new__(cls, *categories):
        """
        Checks whether a respective condition passes.
        
        Parameters
        ----------
        *categories : `str`, `int`, ``ChannelCategory`` or ``Guild``
            The categories, within sent messages pass the check.
            
            If you want to check whether the channel is not in a category, pass the parameter as the respective guild
            instead.
        
        Raises
        ------
        TypeError
            If a category was not given neither as ``ChannelCategory``, ``Guild``, `str` or `int` instance.
        ValueError
            If a category was given as `str` or as `int` instance, but not as a valid snowflake.
        """
        category_ids_processed = set()
        
        for category in categories:
            category_id = instance_or_id_to_snowflake(category, (ChannelCategory, Guild), 'category')
            category_ids_processed.add(category_id)
        
        category_ids_processed_length = len(category_ids_processed)
        if category_ids_processed_length == 0:
            return CheckBase()
        if category_ids_processed_length == 1:
            return CheckIsCategory(category_ids_processed.pop())
        
        self = object.__new__(cls)
        self.category_ids = category_ids_processed
        return self
