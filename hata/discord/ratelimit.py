# -*- coding: utf-8 -*-
__all__ = ('RATELIMIT_GROUPS', 'RatelimitProxy', )

from email._parseaddr import _parsedate_tz
from datetime import datetime, timedelta, timezone
from time import monotonic
from collections import deque
from threading import current_thread

from ..backend.dereaddons_local import modulize, WeakReferer
from ..backend.futures import Future
from ..backend.hdrs import DATE

from .client_core import KOKORO
from .others import Discord_hdrs

ChannelBase = NotImplemented
Message     = NotImplemented
Role        = NotImplemented
Webhook     = NotImplemented
WebhookRepr = NotImplemented
Guild       = NotImplemented

RATELIMIT_RESET         = Discord_hdrs.RATELIMIT_RESET
RATELIMIT_RESET_AFTER   = Discord_hdrs.RATELIMIT_RESET_AFTER
RATELIMIT_REMAINING     = Discord_hdrs.RATELIMIT_REMAINING
RATELIMIT_LIMIT         = Discord_hdrs.RATELIMIT_LIMIT

#parsing time
#email.utils.parsedate_to_datetime
def parsedate_to_datetime(data):
    *dtuple, tz = _parsedate_tz(data)
    if tz is None:
        return datetime(*dtuple[:6])
    return datetime(*dtuple[:6],tzinfo=timezone(timedelta(seconds=tz)))

class global_lock_canceller:
    __slots__=('session',)
    def __init__(self,session):
        self.session=session
    def __call__(self,future):
        self.session.global_lock=None

def ratelimit_global(session,retry_after):
    future=session.global_lock
    if future is not None:
        return future
    future=Future(session.loop)
    future.add_done_callback(global_lock_canceller(session))
    session.global_lock=future
    future._loop.call_later(retry_after,future.__class__.set_result_if_pending,future,None)
    return future

GLOBALLY_LIMITED = 0x4000000000000000
RATELIMIT_DROP_ROUND = 0.20
MAXIMAL_UNLIMITED_PARARELLITY = -50
UNLIMITED_SIZE_VALUE = -10000
NO_SPECIFIC_RATELIMITER = 0

LIMITER_CHANNEL     = 'channel_id'
LIMITER_GUILD       = 'guild_id'
LIMITER_WEBHOOK     = 'webhook_id'
LIMITER_GLOBAL      = 'global'
LIMITER_UNLIMITED   = 'unlimited'

class RatelimitGroup(object):
    __slots__ = ('group_id', 'limiter', 'size', )
    
    __auto_next_id = 105<<8
    __unlimited = None
    
    def __new__(cls, limiter = LIMITER_GLOBAL, optimistic=False):
        self = object.__new__(cls)
        self.limiter = limiter
        self.size = (-1 if optimistic else 0)
        group_id = cls.__auto_next_id
        cls.__auto_next_id = group_id + (7<<8)
        self.group_id = group_id
        return self
    
    @classmethod
    def unlimited(cls):
        self = cls.__unlimited
        if (self is not None):
            return self
        
        self = object.__new__(cls)
        self.size = UNLIMITED_SIZE_VALUE
        self.group_id = 0
        self.limiter = LIMITER_UNLIMITED
        
        cls.__unlimited = self
        return self
    
    def __hash__(self):
        return self.group_id
    
    def __repr__(self):
        result = [
            '<',
            self.__class__.__name__,
            ' size=',
            repr(self.size),
            ', ',
                ]
        
        limiter = self.limiter
        if limiter is LIMITER_GLOBAL:
            result.append('limited globally')
        elif limiter is LIMITER_UNLIMITED:
            result.append('unlimited')
        else:
            result.append('limited by ')
            result.append(limiter)
        
        result.append('>')
        
        return ''.join(result)

class RatelimitUnit(object):
    __slots__ = ('allocates', 'drop', 'next')
    
    def __init__(self, drop, allocates):
        self.drop = drop
        self.allocates = allocates
        self.next = None
    
    def update_with(self, drop, allocates):
        actual_drop = self.drop
        new_drop_max = drop+RATELIMIT_DROP_ROUND
        if new_drop_max < actual_drop:
            new = object.__new__(type(self))
            new.drop = self.drop
            new.allocates = self.allocates
            new.next = self.next
            self.drop = drop
            self.allocates = allocates
            self.next = new
            return
        
        new_drop_min = drop-RATELIMIT_DROP_ROUND
        if new_drop_min > actual_drop:
            last = self
            while True:
                actual = last.next
                if actual is None:
                    new = object.__new__(type(self))
                    new.drop = drop
                    new.allocates = allocates
                    new.next = None
                    last.next = new
                    break
                
                actual_drop = actual.drop
                if new_drop_max < actual_drop:
                    new = object.__new__(type(self))
                    new.drop = drop
                    new.allocates = allocates
                    new.next = actual
                    last.next = new
                    break
                
                if new_drop_min > actual_drop:
                    last = actual
                    continue
                
                if drop < actual_drop:
                    actual.drop = drop
                
                actual.allocates += allocates
                break
            
            return
            
        if drop < actual_drop:
            self.drop = drop
        
        self.allocates += allocates
        return
        
    def __repr__(self):
        result = [
            '<',
            self.__class__.__name__,
            ' drop=',
            repr(self.drop),
            ', allocates=',
            repr(self.allocates),
                ]
        
        next = self.next
        if (next is not None):
            result.append(', nexts=[')
            while True:
                result.append('(')
                result.append(repr(next.drop))
                result.append(', ')
                result.append(repr(next.allocates))
                result.append(')')
                next = next.next
                if (next is None):
                    break
                
                result.append(', ')
                continue
            
            result.append(']')
        
        result.append('>')
        
        return ''.join(result)

class RatelimitHandler(object):
    __slots__ = ('__weakref__', 'active', 'drops', 'limiter_id', 'parent', 'queue', 'wakeupper', )
    def __init__(self, parent, limiter_id):
        self.parent     = parent
        
        limiter = parent.limiter
        if limiter is LIMITER_UNLIMITED:
            limiter_id = 0
        elif limiter is LIMITER_UNLIMITED:
            limiter_id = GLOBALLY_LIMITED
        
        self.limiter_id = limiter_id
        self.drops      = None
        self.active     = 0
        self.queue      = None
        self.wakeupper  = None
    
    def copy(self):
        new = object.__new__(type(self))
        new.parent      = self.parent
        new.limiter_id  = self.limiter_id
        new.drops       = None
        new.active      = 0
        new.queue       = None
        new.wakeupper   = None
        return new
    
    def __repr__(self):
        result = [
            '<',
            self.__class__.__name__,
                ]
        
        limiter = self.parent.limiter
        if limiter is LIMITER_UNLIMITED:
            result.append(' unlimited')
        else:
            result.append(' size: ')
            size = self.parent.size
            if size==-1:
                result.append('unset')
            else:
                result.append(repr(size))
            
            result.append(', active: ')
            result.append(repr(self.active))
            
            result.append(', cooldown drops: ')
            result.append(repr(self.drops))
            
            result.append(', queue length: ')
            queue = self.queue
            if queue is None:
                length = '0'
            else:
                length = repr(len(self.queue))
            result.append(length)
            
            if limiter is LIMITER_GLOBAL:
                result.append(', limited globally')
            else:
                result.append(', limited by ')
                result.append(limiter)
                result.append(': ')
                result.append(repr(self.limiter_id))
            
            result.append(', group id: ')
            result.append(repr(self.parent.group_id))
            
        result.append('>')
        return ''.join(result)
    
    def __bool__(self):
        if self.active:
            return True
        
        if (self.drops is not None):
            return True
        
        queue = self.queue
        if (queue is not None) and queue:
            return True
        
        return False
    
    def __eq__(self,other):
        if self.limiter_id!=other.limiter_id:
            return False
        
        if self.parent.group_id!=other.parent.group_id:
            return False
        
        return True
    
    def __ne__(self,other):
        if self.limiter_id!=other.limiter_id:
            return True
        
        if self.parent.group_id!=other.parent.group_id:
            return True
        
        return False
    
    def __hash__(self):
        return self.parent.group_id+self.limiter_id
    
    async def enter(self):
        size = self.parent.size
        if size < 1:
            if size == UNLIMITED_SIZE_VALUE:
                return
            
            if size == 0:
                size = 1
            else:
                size = -size
        
        queue = self.queue
        if queue is None:
            self.queue = queue = deque()
        
        active = self.active
        left = size-active
        
        if left <= 0:
            future = Future(KOKORO)
            queue.append(future)
            await future
            
            self.active = self.active+1
            return
        
        left -= self.count_drops()
        if left > 0:
            self.active = active+1
            return
        
        future = Future(KOKORO)
        queue.append(future)
        await future
        
        self.active = self.active+1
    
    def exit(self, headers):
        current_size = self.parent.size
        if current_size == UNLIMITED_SIZE_VALUE:
            return
        
        self.active -=1
        
        optimistic = False
        while True:
            if (headers is not None):
                size = headers.get(RATELIMIT_LIMIT,None)
                if size is None:
                    if current_size < 0:
                        optimistic = True
                        # A not so special case when the endpoint is not ratelimit yet.
                        # If this happens, we increase the maximal size.
                        size = current_size
                        if size > MAXIMAL_UNLIMITED_PARARELLITY:
                            size -=1
                        
                        break
                else:
                    size = int(size)
                    break
            
            wakeupper = self.wakeupper
            if (wakeupper is not None):
                wakeupper.cancel()
                self.wakeupper = None
            
            self.wakeup()
            return
        
        allocates = 1
        
        if size != current_size:
            self.parent.size = size
            
            if optimistic:
                current_size = -current_size
                size = -size
            
            if size > current_size:
                if current_size==-1:
                    current_size = 1
                    # We might have cooldowns from before as well
                    allocates = size-int(headers[RATELIMIT_REMAINING])
                
                can_free = size-current_size
                queue = self.queue
                queue_ln = len(queue)
                
                if can_free>queue_ln:
                    can_free=queue_ln
                
                while can_free>0:
                    future = queue.popleft()
                    future.set_result(None)
                    can_free-=1
                    continue
        
        if optimistic:
            delay = 1.0
        else:
            delay1 = (
                datetime.fromtimestamp(float(headers[RATELIMIT_RESET]),timezone.utc)-parsedate_to_datetime(headers[DATE])
                    ).total_seconds()
            delay2 = float(headers[RATELIMIT_RESET_AFTER])
            
            if delay1 < delay2:
                delay = delay1
            else:
                delay = delay2
        
        drop = monotonic()+delay
        
        drops = self.drops
        if (drops is None):
            self.drops = RatelimitUnit(drop, allocates)
        else:
            drops.update_with(drop, allocates)
        
        wakeupper = self.wakeupper
        if wakeupper is None:
            wakeupper = KOKORO.call_at(drop,type(self).wakeup,self)
            self.wakeupper = wakeupper
            return
        
        if wakeupper.when<=drop:
            return
        
        wakeupper.cancel()
        wakeupper = KOKORO.call_at(drop,type(self).wakeup,self)
        self.wakeupper = wakeupper
    
    def wakeup(self):
        # add some delay, so we wont need to wakeup that much time
        drops = self.drops
        if (drops is None):
            wakeupper = None
        else:
            self.drops = drops = drops.next
            if (drops is not None):
                wakeupper = KOKORO.call_at(drops.drop,type(self).wakeup,self)
            else:
                wakeupper = None
        
        self.wakeupper = wakeupper
        
        queue = self.queue
        queue_ln = len(queue)
        if queue_ln == 0:
            return
        
        # if exception occures, nothing is added to self.drops, but active is descreased by one,
        # so lets check active count as well.
        # also the first requests might set self.parent.size as well, to higher than 1 >.>
        size = self.parent.size
        if size < 0:
            size = -size
        
        can_free = size-self.active-self.count_drops()
        
        if can_free > queue_ln:
            can_free = queue_ln
        
        while can_free>0:
            future = queue.popleft()
            future.set_result(None)
            can_free-=1
            continue
    
    def ctx(self):
        return RatelimitHandlerCTX(self)
    
    def count_drops(self):
        drops = self.drops
        result = 0
        while (drops is not None):
            result += drops.allocates
            drops = drops.next
            continue
        
        return result

class RatelimitHandlerCTX(object):
    __slots__ = ('parent', 'exited', )
    def __init__(self,parent):
        self.parent = parent
        self.exited = False
    
    def exit(self, headers):
        self.exited = True
        self.parent.exit(headers)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exited:
            return
        
        self.exited = True
        self.parent.exit(None)

class RatelimitProxy(object):
    __slots__ = ('_handler', '_key', 'client', 'group',)
    def __new__(cls, client, group, limiter=None, keep_alive=False):
        if type(group) is not RatelimitGroup:
            raise TypeError(f'group should be type `{RatelimitGroup.__name__}`, got `{group!r}`.')
        
        while True:
            group_limiter = group.limiter
            if group_limiter is LIMITER_GLOBAL:
                limiter_id = GLOBALLY_LIMITED
                break
            
            elif group_limiter is LIMITER_UNLIMITED:
                limiter_id = 0
                break
            
            elif group_limiter is LIMITER_CHANNEL:
                if isinstance(limiter, ChannelBase):
                    limiter_id = limiter.id
                    break
                
                if type(limiter) is Message:
                    limiter_id = limiter.channel.id
                    break
            
            elif group_limiter is LIMITER_GUILD:
                if isinstance(limiter, Guild):
                    limiter_id = limiter.id
                    break
                
                if isinstance(limiter, ChannelBase) or (type(limiter) in (Message, Role, Webhook, WebhookRepr)):
                    guild = limiter.guild
                    if (guild is not None):
                        limiter_id = group.id
                        break
            
            elif group_limiter is LIMITER_WEBHOOK:
                if type(limiter) in (Webhook, WebhookRepr):
                    limiter_id = limiter.id
                    break
            
            else:
                raise RuntimeError(f'`{group!r}.limiter` is not any of the defined limit groups.')
            
            raise ValueError(f'Cannot cast ratelimit group\'s: `{group!r}` ratelimit_id of: `{limiter!r}`.')
        
        key = RatelimitHandler(group, limiter_id)
        if keep_alive:
            key = client.http.handlers.set(key)
            handler = WeakReferer(key)
        else:
            handler = None
        
        self = object.__new__(cls)
        self.client = client
        self.group = group
        self._handler = handler
        self._key = key
        return self
    
    def is_limited_by_channel(self):
        return (self.group.limiter is LIMITER_CHANNEL)
    
    def is_limited_by_guild(self):
        return (self.group.limiter is LIMITER_GUILD)
    
    def is_limited_by_webhook(self):
        return (self.group.limiter is LIMITER_WEBHOOK)
    
    def is_limited_globally(self):
        return (self.group.limiter is LIMITER_GLOBAL)
    
    def is_unlimited(self):
        return (self.group.limiter is LIMITER_UNLIMITED)
    
    def is_alive(self):
        return (self.handler is not None)
    
    def has_info(self):
        handler = self.handler
        if handler is None:
            return False
        
        return (handler.queue is not None)
        
    def _get_keep_alive(self):
        handler = self._handler
        if handler is None:
            return False
        
        return (handler() is self._key)
    
    def _set_keep_alive(self, value):
        if value:
            while True:
                handler = self._handler
                if handler is None:
                    break
                
                handler = handler()
                if handler is None:
                    break
                
                if (self._key is not handler):
                    self._key = handler
                
                return
            
            key = self._key
            handler = self.client.http.handlers.set(key)
            if (handler is not key):
                self._key = handler
            self._handler = WeakReferer(handler)
            return
        else:
            handler = self._handler
            if handler is None:
                return
            
            handler = handler()
            if handler is None:
                return
            
            if self._key is handler:
                self._key = handler.copy()
            return
        
    keep_alive = property(_get_keep_alive, _set_keep_alive)
    del _get_keep_alive, _set_keep_alive
    
    @property
    def limiter_id(self):
        return self._key.limiter_id
    
    def has_size_set(self):
        return (self.group.size > 0)
    
    @property
    def size(self):
        return self.group.size
    
    @property
    def handler(self):
        handler = self._handler
        if (handler is not None):
            handler = handler()
            if (handler is not None):
                return handler
        
        handler = self.client.http.handlers.get(self._key)
        if (handler is not None):
            self._handler = WeakReferer(handler)
        
        return handler
    
    @property
    def used_count(self):
        handler = self.handler
        if handler is None:
            return 0
        
        return (handler.active + handler.count_drops())
    
    @property
    def free_count(self):
        size = self.group.size
        if size < 1:
            if size == 0:
                size = 1
            elif size == UNLIMITED_SIZE_VALUE:
                return 0
            else:
                size = -size
        
        handler = self.handler
        if handler is None:
            return size
        
        return (size - handler.active - handler.count_drops())
    
    @property
    def waiting_count(self):
        handler = self.handler
        if handler is None:
            return 0
        
        queue = handler.queue
        if queue is None:
            return 0
        
        return len(queue)
    
    def __hash__(self):
        return self.group.group_id^self._key.limiter_id
    
    class _wait_till_limits_expire_callback(object):
        __slots__ = ('future')
        def __init__(self, future):
            self.future = future
        
        def __call__(self, reference):
            future = self.future
            future.set_result_if_pending(None)
            loop = future._loop
            if current_thread() is not loop:
                loop.wakeup()
    
    async def wait_till_limits_expire(self):
        handler = self._handler
        
        while True:
            if (handler is not None):
                handler = handler()
                if (handler is not None):
                    break
            
            handler = self.client.http.handlers.get(self._key)
            if handler is None:
                return
            
            break
        
        if handler is self._key:
            raise RuntimeError('Cannot use `.wait_till_limits_expire` meanwhile `keep_alive` is `True`.')
        
        future = Future(current_thread())
        self._handler = WeakReferer(handler, self._wait_till_limits_expire_callback(future))
        await future
    
    @property
    def next_reset_at(self):
        handler = self.handler
        if handler is None:
            return 0.0
        
        drops = handler.drops
        if (drops is None) or (not drops):
            return 0.0
        
        return drops[0].drop
    
    @property
    def next_reset_after(self):
        handler = self.handler
        if handler is None:
            return 0.0
        
        drops = handler.drops
        if (drops is None) or (not drops):
            return 0.0
        
        return drops[0].drop-monotonic()
    
@modulize
class RATELIMIT_GROUPS:
    GROUP_REACTION_MODIFY       = RatelimitGroup(LIMITER_CHANNEL)
    GROUP_PIN_MODIFY            = RatelimitGroup(LIMITER_CHANNEL)
    GROUP_USER_MODIFY           = RatelimitGroup(LIMITER_GUILD) # both has the same endpoint
    GROUP_USER_ROLE_MODIFY      = RatelimitGroup(LIMITER_GUILD)
    
    oauth2_token                = RatelimitGroup(optimistic=True)
    application_get             = RatelimitGroup() # untested
    achievement_get_all         = RatelimitGroup()
    achievement_create          = RatelimitGroup()
    achievement_delete          = RatelimitGroup()
    achievement_get             = RatelimitGroup()
    achievement_edit            = RatelimitGroup()
    client_logout               = RatelimitGroup() # untested
    channel_delete              = RatelimitGroup.unlimited()
    channel_group_leave         = RatelimitGroup.unlimited() # untested; same as channel_delete?
    channel_edit                = RatelimitGroup(LIMITER_CHANNEL)
    channel_group_edit          = RatelimitGroup(LIMITER_CHANNEL, optimistic=True) # untested; same as channel_edit?
    channel_follow              = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    invite_get_channel          = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    invite_create               = RatelimitGroup()
    message_logs                = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    message_create              = RatelimitGroup(LIMITER_CHANNEL)
    message_delete_multiple     = RatelimitGroup(LIMITER_CHANNEL)
    message_delete              = RatelimitGroup(LIMITER_CHANNEL)
    message_delete_b2wo         = RatelimitGroup(LIMITER_CHANNEL)
    message_get                 = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    message_edit                = RatelimitGroup(LIMITER_CHANNEL)
    message_mar                 = RatelimitGroup(optimistic=True) # untested
    message_crosspost           = RatelimitGroup(LIMITER_CHANNEL)
    reaction_clear              = GROUP_REACTION_MODIFY
    reaction_delete_emoji       = GROUP_REACTION_MODIFY
    reaction_users              = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    reaction_delete_own         = GROUP_REACTION_MODIFY
    reaction_add                = GROUP_REACTION_MODIFY
    reaction_delete             = GROUP_REACTION_MODIFY
    message_suppress_embeds     = RatelimitGroup()
    permission_ow_delete        = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    permission_ow_create        = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    channel_pins                = RatelimitGroup()
    message_unpin               = GROUP_PIN_MODIFY
    message_pin                 = GROUP_PIN_MODIFY
    channel_group_user_delete   = RatelimitGroup(LIMITER_CHANNEL, optimistic=True) # untested
    channel_group_user_add      = RatelimitGroup(LIMITER_CHANNEL, optimistic=True) # untested
    typing                      = RatelimitGroup(LIMITER_CHANNEL)
    webhook_get_channel         = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    webhook_create              = RatelimitGroup(LIMITER_CHANNEL, optimistic=True)
    client_gateway_hooman       = RatelimitGroup()
    client_gateway_bot          = RatelimitGroup()
    guild_create                = RatelimitGroup.unlimited()
    guild_delete                = RatelimitGroup.unlimited()
    guild_get                   = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_edit                  = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_mar                   = RatelimitGroup() # untested
    audit_logs                  = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_bans                  = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_ban_delete            = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_ban_get               = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_ban_add               = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_channels              = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    channel_move                = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    channel_create              = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_embed_get             = RatelimitGroup(LIMITER_GUILD, optimistic=True) # will be removed, do not bother with testing
    guild_embed_edit            = RatelimitGroup(LIMITER_GUILD, optimistic=True) # will be removed, do not bother with testing
    guild_emojis                = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    emoji_create                = RatelimitGroup(LIMITER_GUILD)
    emoji_delete                = RatelimitGroup(LIMITER_GUILD)
    emoji_get                   = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    emoji_edit                  = RatelimitGroup()
    integration_get_all         = RatelimitGroup() # untested
    integration_create          = RatelimitGroup() # untested
    integration_delete          = RatelimitGroup() # untested
    integration_edit            = RatelimitGroup() # untested
    integration_sync            = RatelimitGroup() # untested
    invite_get_guild            = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_users                 = RatelimitGroup(LIMITER_GUILD)
    client_edit_nick            = RatelimitGroup()
    guild_user_delete           = RatelimitGroup(LIMITER_GUILD)
    guild_user_get              = RatelimitGroup(LIMITER_GUILD)
    user_edit                   = GROUP_USER_MODIFY
    user_move                   = GROUP_USER_MODIFY
    guild_user_add              = RatelimitGroup(LIMITER_GUILD)
    user_role_delete            = GROUP_USER_ROLE_MODIFY
    user_role_add               = GROUP_USER_ROLE_MODIFY
    guild_user_search           = RatelimitGroup(LIMITER_GUILD)
    guild_preview               = RatelimitGroup()
    guild_prune_estimate        = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_prune                 = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_regions               = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_roles                 = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    role_move                   = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    role_create                 = RatelimitGroup(LIMITER_GUILD)
    role_delete                 = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    role_edit                   = RatelimitGroup(LIMITER_GUILD)
    vanity_get                  = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    vanity_edit                 = RatelimitGroup(LIMITER_GUILD, optimistic=True) # untested
    webhook_get_guild           = RatelimitGroup(LIMITER_GUILD, optimistic=True)
    guild_widget_get            = RatelimitGroup.unlimited()
    hypesquad_house_leave       = RatelimitGroup() # untested
    hypesquad_house_change      = RatelimitGroup() # untested
    invite_delete               = RatelimitGroup.unlimited()
    invite_get                  = RatelimitGroup()
    client_application_info     = RatelimitGroup(optimistic=True)
    user_info                   = RatelimitGroup(optimistic=True)
    client_user                 = RatelimitGroup(optimistic=True)
    client_edit                 = RatelimitGroup()
    user_achievements           = RatelimitGroup() # untested; has expected global ratelimit
    user_achievement_update     = RatelimitGroup()
    channel_private_get_all     = RatelimitGroup(optimistic=True)
    channel_private_create      = RatelimitGroup.unlimited()
    client_connections          = RatelimitGroup(optimistic=True)
    user_connections            = RatelimitGroup(optimistic=True)
    guild_get_all               = RatelimitGroup()
    user_guilds                 = RatelimitGroup()
    guild_leave                 = RatelimitGroup.unlimited()
    relationship_friend_request = RatelimitGroup(optimistic=True) # untested
    relationship_delete         = RatelimitGroup(optimistic=True) # untested
    relationship_create         = RatelimitGroup(optimistic=True) # untested
    client_get_settings         = RatelimitGroup(optimistic=True) # untested
    client_edit_settings        = RatelimitGroup(optimistic=True) # untested
    user_get                    = RatelimitGroup()
    channel_group_create        = RatelimitGroup(optimistic=True) # untested
    user_get_profile            = RatelimitGroup(optimistic=True) # untested
    webhook_delete              = RatelimitGroup.unlimited()
    webhook_get                 = RatelimitGroup.unlimited()
    webhook_edit                = RatelimitGroup(LIMITER_WEBHOOK, optimistic=True)
    webhook_delete_token        = RatelimitGroup.unlimited()
    webhook_get_token           = RatelimitGroup.unlimited()
    webhook_edit_token          = RatelimitGroup(LIMITER_WEBHOOK, optimistic=True)
    webhook_send                = RatelimitGroup(LIMITER_WEBHOOK)

del modulize

##INFO :
##    some endpoints might be off 1s
##    groups are not accurate now, because we use autogroups
##    last group id: 98560
##
##endpoint: https://cdn.discordapp.com/
##method  : GET
##auth    : none
##used at :
##limits  : unlimited
##
##endpoint: oauth2/token
##method  : POST
##auth    : application
##used at : oauth2_token
##limits  : unlimited
##
##endpoint: /applications/{application_id}
##method  : GET
##auth    : user
##used at : application_get
##limits  : UNTESTED
##
##endpoint: /applications/{application_id}/achievements
##method  : GET
##auth    : bot
##used at : achievement_get_all
##limits  :
##    group   : 75264
##    limit   : 5
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /applications/{application_id}/achievements
##method  : POST
##auth    : bot
##used at : achievement_create
##limits  :
##    group   : 78848
##    limit   : 5
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /applications/{application_id}/achievements/{achievement_id}
##method  : DELETE
##auth    : bot
##used at : achievement_delete
##limits  :
##    group   : 82432
##    limit   : 5
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /applications/{application_id}/achievements/{achievement_id}
##method  : GET
##auth    : bot
##used at : achievement_get
##limits  :
##    group   : 77056
##    limit   : 5
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /applications/{application_id}/achievements/{achievement_id}
##method  : PATCH
##auth    : bot
##used at : achievement_edit
##limits  :
##    group   : 80640
##    limit   : 5
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /auth/logout
##method  : POST
##auth    : user
##used at : client_logout
##limits  : UNTESTED
##
##endpoint: /channels/{channel_id}
##method  : DELETE
##auth    : bot
##used at : channel_delete
##limits  : unlimited
##
##endpoint: /channels/{channel_id}
##method  : DELETE
##auth    : user
##used at : channel_group_leave
##limits  : UNTESTED
##
##endpoint: /channels/{channel_id}
##method  : PATCH
##auth    : bot
##used at : channel_edit
##limits  :
##limits  :
##    group   : 91392
##    limit   : 5
##    reset   : 15
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}
##method  : PATCH
##auth    : user
##used at : channel_group_edit
##limits  : UNTESTED
##
##endpoint: /channels/{channel_id}/followers
##method  : POT
##auth    : bot
##used at : channel_follow
##limits  : unlimited
##
##endpoint: /channels/{channel_id}/invites
##method  : GET
##auth    : bot
##used at : invite_get_channel
##limits  : unlimited
##
##endpoint: /channels/{channel_id}/invites
##method  : POST
##auth    : bot
##used at : invite_create
##limits  :
##    group   : 39424
##    limit   : 5
##    reset   : 15
##    limiter : GLOBAL
##
##endpoint: /channels/{channel_id}/messages
##method  : GET
##auth    : bot
##used at : message_logs
##limits  : unlimited
##
##endpoint: /channels/{channel_id}/messages
##method  : POST
##auth    : bot
##used at : message_create
##limits  :
##    group   : 28672
##    limit   : 5
##    reset   : 4
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/bulk_delete
##method  : POST
##auth    : bot
##used at : message_delete_multiple
##limits  :
##    group   : 30464
##    limit   : 1
##    reset   : 3
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/{message_id}
##method  : DELETE
##auth    : bot
##used at : message_delete / message_delete_b2wo
##limits  : `newer than 14 days` or `own` / `else`
##    group   : 71680 / 87808
##    limit   : 3 / 30
##    reset   : 1 / 120
##    limiter : channel_id
##comment :
##    For newer messages ratelimit is not every time included, but we ll ignore
##    those, because we cannot detect, at which cases ar those applied.
##
##endpoint: /channels/{channel_id}/messages/{message_id}
##method  : GET
##auth    : bot
##used at : message_get
##limits  : unlimited
##
##endpoint: /channels/{channel_id}/messages/{message_id}
##method  : PATCH
##auth    : bot
##used at : message_edit
##limits  :
##    group   : 32256
##    limit   : 5
##    reset   : 4
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/{message_id}/ack
##method  : POST
##auth    : user
##used at : message_mar
##limits  : UNTESTED
##
##endpoint: /channels/{channel_id}/messages/{message_id}/crosspost
##method  : POST
##auth    : bot
##used at : message_crosspost
##limits  :
##    group : 96768
##    limit : 10
##    reset : 3600
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/{message_id}/reactions
##method  : DELETE
##auth    : bot
##used at : reaction_clear
##limits  :
##    group   : 26880
##    limit   : 1
##    reset   : 0.25
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/{message_id}/reactions/{reaction}
##method  : DELETE
##auth    : bot
##used at : reaction_delete_emoji
##limits  :
##    group   : 26880
##    limit   : 1
##    reset   : 0.25
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/{message_id}/reactions/{reaction}
##method  : GET
##auth    : bot
##used at : reaction_users
##limits  : unlimited
##
##endpoint: /channels/{channel_id}/messages/{message_id}/reactions/{reaction}/@me
##method  : DELETE
##auth    : bot
##used at : reaction_delete_own
##limits  :
##    group   : 26880
##    limit   : 1
##    reset   : 0.25
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/{message_id}/reactions/{reaction}/@me
##method  : PUT
##auth    : bot
##used at : reaction_add
##limits  :
##    group   : 26880
##    limit   : 1
##    reset   : 0.25
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/{message_id}/reactions/{reaction}/{user_id}
##method  : DELETE
##auth    : bot
##used at : reaction_delete
##limits  :
##    group   : 26880
##    limit   : 1
##    reset   : 0.25
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/messages/{message_id}/suppress-embeds
##method  : POST
##auth    : bot
##used at : message_suppress_embeds
##limits  :
##    group   : 73472
##    limit   : 3
##    reset   : 1
##    limiter : GLOBAL
##
##endpoint: /channels/{channel_id}/permissions/{overwrite_id}
##method  : DELETE
##auth    : bot
##used at : permission_ow_delete
##limits  : unlimited
##
##endpoint: /channels/{channel_id}/permissions/{overwrite_id}
##method  : PUT
##auth    : bot
##used at : permission_ow_create
##limits  : unlimited
##
##endpoint: /channels/{channel_id}/pins
##method  : PUT
##auth    : bot
##used at : channel_pins
##limits  :
##    group   : 35840
##    limit   : 1
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /channels/{channel_id}/pins/{message_id}
##method  : DELETE
##auth    : bot
##used at : message_unpin
##limits  :
##    group   : 34048
##    limit   : 5
##    reset   : 4
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/pins/{message_id}
##method  : PUT
##auth    : bot
##used at : message_pin
##limits  :
##    group   : 34048
##    limit   : 5
##    reset   : 4
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/recipients/{user_id}
##method  : DELETE
##auth    : user
##used at : channel_group_user_delete
##limits  : UNTESTED
##
##endpoint: /channels/{channel_id}/recipients/{user_id}
##method  : PUT
##auth    : user
##used at : channel_group_user_add
##limits  : UNTESTED
##
##endpoint: /channels/{channel_id}/typing
##method  : POST
##auth    : bot
##used at : typing
##limits  :
##    group   : 37632
##    limit   : 5
##    reset   : 5
##    limiter : channel_id
##
##endpoint: /channels/{channel_id}/webhooks
##method  : GET
##auth    : bot
##used at : webhook_get_channel
##limits  : unlimited
##
##endpoint: /channels/{channel_id}/webhooks
##method  : POST
##auth    : bot
##used at : webhook_create
##limits  : unlimited
##
##endpoint: /gateway
##method  : GET
##auth    : user
##used at : client_gateway_hooman
##limits  : UNTESTED
##
##endpoint: /gateway/bot
##method  : GET
##auth    : bot
##used at : client_gateway_bot
##limits  :
##    group   : 41216
##    limit   : 2
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /guilds
##method  : POST
##auth    : bot
##used at : guild_create
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}
##method  : DELETE
##auth    : bot
##used at : guild_delete
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}
##method  : GET
##auth    : bot
##used at : guild_get
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}
##method  : PATCH
##auth    : bot
##used at : guild_edit
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/ack
##method  : POST
##auth    : user
##used at : guild_mar
##limits  : UNTESTED
##
##endpoint: /guilds/{guild_id}/audit-logs
##method  : GET
##auth    : bot
##used at : audit_logs
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/bans
##method  : GET
##auth    : bot
##used at : guild_bans
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/bans/{user_id}
##method  : DELETE
##auth    : bot
##used at : guild_ban_delete
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/bans/{user_id}
##method  : GET
##auth    : bot
##used at : guild_ban_get
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/bans/{user_id}
##method  : PUT
##auth    : bot
##used at : guild_ban_add
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/channels
##method  : GET
##auth    : bot
##used at : guild_channels
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/channels
##method  : PATCH
##auth    : bot
##used at : channel_move
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/channels
##method  : POST
##auth    : bot
##used at : channel_create
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/embed
##method  : GET
##auth    : bot
##used at : guild_embed_get
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/embed
##method  : PATCH
##auth    : bot
##used at : guild_embed_edit
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/embed.png
##method  : GET
##auth    : none
##used at : guild.embed_url
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/emojis
##method  : GET
##auth    : bot
##used at : guild_emojis
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/emojis
##method  : POST
##auth    : bot
##used at : emoji_create
##limits  :
##    group   : 43008
##    limit   : 50
##    reset   : 3600
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/emojis/{emoji_id}
##method  : DELETE
##auth    : bot
##used at : emoji_delete
##limits  :
##    group   : 44800
##    limit   : 1
##    reset   : 3
##    limiter : GLOBAL
##
##endpoint: /guilds/{guild_id}/emojis/{emoji_id}
##method  : GET
##auth    : bot
##used at : emoji_get
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/emojis/{emoji_id}
##method  : PATCH
##auth    : bot
##used at : emoji_edit
##limits  :
##    group   : 46592
##    limit   : 1
##    reset   : 3
##    limiter : GLOBAL
##
##endpoint: /guilds/{guild_id}/integrations
##method  : GET
##auth    : bot
##used at : integration_get_all
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/integrations
##method  : POST
##auth    : bot
##used at : integration_create
##limits  : UNTESTED
##
##endpoint: /guilds/{guild_id}/integrations/{integration_id}
##method  : DELETE
##auth    : bot
##used at : integration_delete
##limits  : UNTESTED
##
##endpoint: /guilds/{guild_id}/integrations/{integration_id}
##method  : PATCH
##auth    : bot
##used at : integration_edit
##limits  : UNTESTED
##
##endpoint: /guilds/{guild_id}/integrations/{integration_id}/sync
##method  : POST
##auth    : bot
##used at : integration_sync
##limits  : UNTESTED
##
##endpoint: /guilds/{guild_id}/invites
##method  : GET
##auth    : bot
##used at : invite_get_guild
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/members
##method  : GET
##auth    : bot
##used at : guild_users
##limits  :
##    group   : 68096
##    limit   : 10
##    reset   : 10
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/members/@me/nick
##method  : PATCH
##auth    : bot
##used at : client_edit_nick
##limits  :
##    group   : 48384
##    limit   : 1
##    reset   : 2
##    limiter : GLOBAL
##
##endpoint: /guilds/{guild_id}/members/{user_id}
##method  : DELETE
##auth    : bot
##used at : guild_user_delete
##limits  :
##    group   : 50176
##    limit   : 5
##    reset   : 2
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/members/{user_id}
##method  : GET
##auth    : bot
##used at : guild_user_get
##limits  :
##    group   : 69888
##    limit   : 5
##    reset   : 1
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/members/{user_id}
##method  : PATCH
##auth    : bot
##used at : user_edit, user_move
##limits  :
##    group   : 51968
##    limit   : 10
##    reset   : 10
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/members/{user_id}
##method  : PUT
##auth    : bot
##used at : guild_user_add
##limits  :
##    group   : 53760
##    limit   : 10
##    reset   : 10
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/members/search
##method  : GET
##auth    : bot
##used at : guild_user_search
##limits  :
##    group   : 98560
##    limit   : 10
##    reset   : 10
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/members/{user_id}/roles/{role_id}
##method  : DELETE
##auth    : bot
##used at : user_role_delete
##limits  :
##    group   : 55552
##    limit   : 10
##    reset   : 10
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/members/{user_id}/roles/{role_id}
##method  : PUT
##auth    : bot
##used at : user_role_add
##limits  :
##    group   : 55552
##    limit   : 10
##    reset   : 10
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/preview
##method  : GET
##auth    : bot
##used at : guild_preview
##limits   :
##    group   : 89600
##    limit   : 5
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /guilds/{guild_id}/prune
##method  : GET
##auth    : bot
##used at : guild_prune_estimate
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/prune
##method  : POST
##auth    : bot
##used at : guild_prune
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/regions
##method  : GET
##auth    : bot
##used at : guild_regions
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/roles
##method  : GET
##auth    : bot
##used at : guild_roles
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/roles
##method  : PATCH
##auth    : bot
##used at : role_move
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/roles
##method  : POST
##auth    : bot
##used at : role_create
##limits  : unlimited
##    group   : 94976
##    limit   : 250
##    reset   : 172800
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/roles/{role_id}
##method  : DELETE
##auth    : bot
##used at : role_delete
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/roles/{role_id}
##method  : PATCH
##auth    : bot
##used at : role_edit
##limits  :
##    group   : 93184
##    limit   : 1000
##    reset   : 86400
##    limiter : guild_id
##
##endpoint: /guilds/{guild_id}/vanity-url
##method  : GET
##auth    : bot
##used at : vanity_get
##limits  : UNTESTED
##
##endpoint: /guilds/{guild_id}/vanity-url
##method  : PATCH
##auth    : bot
##used at : vanity_edit
##limits  : UNTESTED
##
##endpoint: /guilds/{guild_id}/webhooks
##method  : GET
##auth    : bot
##used at : webhook_get_guild
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/widget.json
##method  : GET
##auth    : none
##used at : guild_widget_get
##limits  : unlimited
##
##endpoint: /guilds/{guild_id}/widget.png
##method  : GET
##auth    : none
##used at : guild.widget_url
##limits  : unlimited
##
##endpoint: /hypesquad/online
##method  : DELETE
##auth    : user
##used at : hypesquad_house_leave
##limits  : UNTESTED
##
##endpoint: /hypesquad/online
##method  : POST
##auth    : user
##used at : hypesquad_house_change
##limits  : UNTESTED
##
##endpoint: /invites/{invite_code}
##method  : DELETE
##auth    : bot
##used at : invite_delete
##limits  : unlimited
##
##endpoint: /invites/{invite_code}
##method  : GET
##auth    : bot
##used at : invite_get
##limits  :
##    group   : 57344
##    limit   : 250
##    reset   : 6
##    limiter : GLOBAL
##
##endpoint: /oauth2/applications/@me
##method  : GET
##auth    : bot
##used at : client_application_info
##limits  : unlimited
##
##endpoint: /users/@me
##method  : GET
##auth    : bearer
##used at : user_info
##limits  : unlimited
##
##endpoint: /users/@me
##method  : GET
##auth    : bot
##used at : client_user
##limits  : unlimited
##
##endpoint: /users/@me
##method  : PATCH
##auth    : bot
##used at : client_edit
##limits  :
##    group   : 59136
##    limit   : 2
##    reset   : 3600
##    limiter : GLOBAL
##
##endpoint: /users/@me/applications/{application_id}/achievements
##method  : GET
##auth    : bearer
##used at : user_achievements
##limits  : UNTESTED
##    group   : 84224
##    limit   : 2
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /users/{user_id}/applications/{application_id}/achievements/{achievement_id}
##method  : PUT
##auth    : bot
##used at : user_achievement_update
##limits  :
##    group   : 86016
##    limit   : 5
##    reset   : 5
##    limiter : GLOBAL
##
##endpoint: /users/@me/channels
##method  : GET
##auth    : bot
##used at : channel_private_get_all
##limits  : unlimited
##
##endpoint: /users/@me/channels
##method  : POST
##auth    : bot
##used at : channel_private_create
##limits  : unlimited
##
##endpoint: /users/@me/connections
##method  : GET
##auth    : bot
##used at : client_connections
##limits  : unlimited
##
##endpoint: /users/@me/connections
##method  : GET
##auth    : bearer
##used at : user_connections
##limits  : unlimited
##
##endpoint: /users/@me/guilds
##method  : GET
##auth    : bot
##used at : guild_get_all
##limits  :
##    group   : 62720
##    limit   : 1
##    reset   : 1
##    limiter : GLOBAL
##
##endpoint: /users/@me/guilds
##method  : GET
##auth    : bearer
##used at : user_guilds
##limits  :
##    group   : 60928
##    limit   : 1
##    reset   : 1
##    limiter : GLOBAL
##
##endpoint: /users/@me/guilds/{guild_id}
##method  : DELETE
##auth    : bot
##used at : guild_leave
##limits  : unlimited
##
##endpoint: /users/@me/relationships
##method  : POST
##auth    : user
##used at : relationship_friend_request
##limits  : UNTESTED
##
##endpoint: /users/@me/relationships/{user_id}
##method  : DELETE
##auth    : user
##used at : relationship_delete
##limits  : UNTESTED
##
##endpoint: /users/@me/relationships/{user_id}
##method  : PUT
##auth    : user
##used at : relationship_create
##limits  : UNTESTED
##
##endpoint: /users/@me/settings
##method  : GET
##auth    : user
##used at : client_get_settings
##limits  : UNTESTED
##
##endpoint: /users/@me/settings
##method  : PATCH
##auth    : user
##used at : client_edit_settings
##limits  : UNTESTED
##
##endpoint: /users/{user_id}
##method  : GET
##auth    : bot
##used at : user_get
##limits  :
##    group   : 64512
##    limit   : 30
##    reset   : 30
##    limiter : GLOBAL
##
##endpoint: /users/{user_id}/channels
##method  : POST
##auth    : user
##used at : channel_group_create
##limits  : UNTESTED
##
##endpoint: /users/{user_id}/profile
##method  : GET
##auth    : user
##used at : user_get_profle
##limits  : UNTESTED
##
##endpoint: /webhooks/{webhook_id}
##method  : DELETE
##auth    : bot
##used at : webhook_delete
##limits  : unlimited
##
##endpoint: /webhooks/{webhook_id}
##method  : GET
##auth    : bot
##used at : webhook_get
##limits  : unlimited
##
##endpoint: /webhooks/{webhook_id}
##method  : PATCH
##auth    : bot
##used at : webhook_edit
##limits  : unlimited
##
##endpoint: webhooks/{webhook_id}/{webhook_token}
##method  : DELETE
##auth    : none
##used at : webhook_delete_token
##limits  : unlimited
##
##endpoint: webhooks/{webhook_id}/{webhook_token}
##method  : GET
##auth    : none
##used at : webhook_get_token
##limits  : unlimited
##
##endpoint: webhooks/{webhook_id}/{webhook_token}
##method  : PATCH
##auth    : none
##used at : webhook_edit_token
##limits  : unlimited
##
##endpoint: webhooks/{webhook_id}/{webhook_token}
##method  : POST
##auth    : none
##used at : webhook_send
##limits  :
##    group   : 66304
##    limit   : 5
##    reset   : 2
##    limiter : webhook_id
