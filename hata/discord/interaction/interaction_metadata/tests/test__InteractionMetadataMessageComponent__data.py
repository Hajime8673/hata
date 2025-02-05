import vampytest

from ....component import ComponentType
from ....message import Attachment

from ...interaction_event import InteractionEvent
from ...resolved import Resolved

from ..message_component import InteractionMetadataMessageComponent

from .test__InteractionMetadataMessageComponent__constructor import _check_is_all_field_set


def test__InteractionMetadataMessageComponent__from_data():
    """
    Tests whether ``InteractionMetadataMessageComponent.from_data`` works as intended.
    """
    component_type = ComponentType.button
    custom_id = 'Inaba'
    resolved = Resolved(attachments = [Attachment.precreate(202211060048)])
    values = ['black', 'rock', 'shooter']
    
    interaction_event = InteractionEvent()
    
    data = {
        'component_type': component_type.value,
        'custom_id': custom_id,
        'resolved': resolved.to_data(defaults = True, interaction_event = interaction_event),
        'values': values,
    }
    
    interaction_metadata = InteractionMetadataMessageComponent.from_data(data, interaction_event)
    _check_is_all_field_set(interaction_metadata)

    vampytest.assert_eq(interaction_metadata.component_type, component_type)
    vampytest.assert_eq(interaction_metadata.custom_id, custom_id)
    vampytest.assert_eq(interaction_metadata.resolved, resolved)
    vampytest.assert_eq(interaction_metadata.values, tuple(values))
    

def test__InteractionMetadataMessageComponent__to_data():
    """
    Tests whether ``InteractionMetadataMessageComponent.to_data`` works as intended.
    """
    guild_id = 202211060046
    interaction_event = InteractionEvent(guild_id = guild_id)
    
    component_type = ComponentType.button
    custom_id = 'Inaba'
    resolved = Resolved(attachments = [Attachment.precreate(202211060049)])
    values = ['black', 'rock', 'shooter']
    
    interaction_metadata = InteractionMetadataMessageComponent(
        component_type = component_type,
        custom_id = custom_id,
        resolved = resolved,
        values = values,
    )
    
    vampytest.assert_eq(
        interaction_metadata.to_data(
            defaults = True,
            interaction_event = interaction_event,
        ),
        {
            'component_type': component_type.value,
            'custom_id': custom_id,
            'resolved': resolved.to_data(defaults = True, interaction_event = interaction_event),
            'values': values,
        },
    )
