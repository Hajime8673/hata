__all__ = ()
# ApplicationCommand

APPLICATION_COMMAND_LIMIT_GLOBAL = 100
APPLICATION_COMMAND_LIMIT_GUILD = 100
APPLICATION_COMMAND_LENGTH_MAX = 4000

# ApplicationCommand & ApplicationCommandOption
APPLICATION_COMMAND_NAME_LENGTH_MIN = 1
APPLICATION_COMMAND_NAME_LENGTH_MAX = 32
APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN = 2
APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX = 100
APPLICATION_COMMAND_OPTIONS_MAX = 25
APPLICATION_COMMAND_CHOICES_MAX = 25

# ApplicationCommandOptionChoice
APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MIN = 1
APPLICATION_COMMAND_CHOICE_NAME_LENGTH_MAX = 100
APPLICATION_COMMAND_CHOICE_VALUE_LENGTH_MIN = 0
APPLICATION_COMMAND_CHOICE_VALUE_LENGTH_MAX = 100

# ApplicationCommandPermissionOverwrite
APPLICATION_COMMAND_PERMISSION_OVERWRITE_MAX = 10

# Components
COMPONENT_SUB_COMPONENT_LIMIT = 5
COMPONENT_LABEL_LENGTH_MAX = 80
COMPONENT_CUSTOM_ID_LENGTH_MAX = 100
COMPONENT_OPTION_LENGTH_MIN = 1
COMPONENT_OPTION_LENGTH_MAX = 25
COMPONENT_OPTION_MIN_VALUES_MIN = 1
COMPONENT_OPTION_MIN_VALUES_MAX = 15
COMPONENT_OPTION_MAX_VALUES_MIN = 1
COMPONENT_OPTION_MAX_VALUES_MAX = 25

# ChannelThread

AUTO_ARCHIVE_DEFAULT = 3600
AUTO_ARCHIVE_OPTIONS = frozenset((3600, 86400, 259200, 604800))
