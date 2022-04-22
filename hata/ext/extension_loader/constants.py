__all__ = ('EXTENSIONS',)

from scarletio import WeakValueDictionary


EXTENSIONS = WeakValueDictionary()

EXTENSION_STATE_UNDEFINED = 0
EXTENSION_STATE_LOADED = 1
EXTENSION_STATE_UNLOADED = 2
EXTENSION_STATE_UNSATISFIED = 3

EXTENSION_STATE_VALUE_TO_NAME = {
    EXTENSION_STATE_UNDEFINED: 'undefined',
    EXTENSION_STATE_LOADED: 'loaded',
    EXTENSION_STATE_UNLOADED: 'unloaded',
    EXTENSION_STATE_UNSATISFIED: 'unsatisfied',
}

LOADING_EXTENSIONS = set()

# Extension roots define core part for extensions.
EXTENSION_ROOTS = set()
