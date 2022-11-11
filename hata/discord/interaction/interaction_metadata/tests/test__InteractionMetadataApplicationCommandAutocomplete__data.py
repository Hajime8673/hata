import vampytest

from ...interaction_event import InteractionEvent
from ...interaction_option import InteractionOption

from ..application_command_autocomplete import InteractionMetadataApplicationCommandAutocomplete

from .test__InteractionMetadataApplicationCommandAutocomplete__constructor import _check_is_all_field_set


def test__InteractionMetadataApplicationCommandAutocomplete__from_data():
    """
    Tests whether ``InteractionMetadataApplicationCommandAutocomplete.from_data`` works as intended.
    """
    id_ = 202211060002
    name = 'Inaba'
    options = [InteractionOption(name = 'Rem')]
    
    data = {
        'id': str(id_),
        'name': name,
        'options': [option.to_data(defaults = True) for option in options],
    }
    
    interaction_event = InteractionEvent()
    interaction_metadata = InteractionMetadataApplicationCommandAutocomplete.from_data(data, interaction_event)
    _check_is_all_field_set(interaction_metadata)

    vampytest.assert_eq(interaction_metadata.id, id_)
    vampytest.assert_eq(interaction_metadata.name, name)
    vampytest.assert_eq(interaction_metadata.options, tuple(options))
    

def test__InteractionMetadataApplicationCommandAutocomplete__to_data():
    """
    Tests whether ``InteractionMetadataApplicationCommandAutocomplete.to_data`` works as intended.
    """
    guild_id = 202211060003
    interaction_event = InteractionEvent(guild_id = guild_id)
    
    id_ = 202211060004
    name = 'Inaba'
    options = [InteractionOption(name = 'Rem')]
    
    interaction_metadata = InteractionMetadataApplicationCommandAutocomplete(
        id = id_,
        name = name,
        options = options,
    )
    
    vampytest.assert_eq(
        interaction_metadata.to_data(
            defaults = True,
            interaction_event = interaction_event,
        ),
        {
            'id': str(id_),
            'name': name,
            'options': [option.to_data(defaults = True) for option in options],
        },
    )
