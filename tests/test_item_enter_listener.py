"""
Tests for dk.listeners.item_enter_listener.ItemEnterEventListener.
"""
from unittest.mock import MagicMock

from dk.actions import (
    ACTION_CONFIRM_PRUNE,
    ACTION_DETAIL_CONTAINER,
    ACTION_RESTART_CONTAINER,
    ACTION_START_CONTAINER,
    ACTION_STOP_CONTAINER,
)
from dk.listeners.item_enter_listener import ItemEnterEventListener


def make_event(data):
    event = MagicMock()
    event.get_data.return_value = data
    return event


class TestItemEnterEventListener:

    def test_start_container(self):
        listener = ItemEnterEventListener()
        extension = MagicMock()
        event = make_event({'action': ACTION_START_CONTAINER, 'id': 'abc123'})

        listener.on_event(event, extension)

        extension.start_container.assert_called_once_with('abc123')

    def test_stop_container(self):
        listener = ItemEnterEventListener()
        extension = MagicMock()
        event = make_event({'action': ACTION_STOP_CONTAINER, 'id': 'abc123'})

        listener.on_event(event, extension)

        extension.stop_container.assert_called_once_with('abc123')

    def test_restart_container(self):
        listener = ItemEnterEventListener()
        extension = MagicMock()
        event = make_event({'action': ACTION_RESTART_CONTAINER, 'id': 'abc123'})

        listener.on_event(event, extension)

        extension.restart_container.assert_called_once_with('abc123')

    def test_show_container_details(self):
        listener = ItemEnterEventListener()
        extension = MagicMock()
        event = make_event({'action': ACTION_DETAIL_CONTAINER, 'container_id': 'abc123'})

        result = listener.on_event(event, extension)

        extension.show_container_details.assert_called_once_with('abc123')
        assert result is extension.show_container_details.return_value

    def test_confirmed_prune_runs_prune(self):
        """ Regression: only the confirmation action may trigger the real prune(). """
        listener = ItemEnterEventListener()
        extension = MagicMock()
        event = make_event({'action': ACTION_CONFIRM_PRUNE})

        result = listener.on_event(event, extension)

        extension.prune.assert_called_once()
        assert result is extension.prune.return_value
