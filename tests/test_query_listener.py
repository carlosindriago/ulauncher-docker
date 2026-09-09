"""
Tests for dk.listeners.query_listener.KeywordQueryEventListener.
"""
from unittest.mock import MagicMock

from dk.listeners.query_listener import KeywordQueryEventListener

PREFERENCES = {
    "kw": "dk",
    "kw_info": "dk:info",
    "kw_prune": "dk:prune",
    "kw_documentation": "dk:docs",
    "default_terminal": "gnome-terminal",
}


def make_extension():
    ext = MagicMock()
    ext.icon_path = "images/icon.png"
    ext.preferences = dict(PREFERENCES)
    return ext


def make_event(keyword, argument=""):
    event = MagicMock()
    event.get_keyword.return_value = keyword
    event.get_argument.return_value = argument
    return event


class TestKeywordQueryEventListener:

    def test_rejects_query_with_invalid_characters(self):
        listener = KeywordQueryEventListener()
        extension = make_extension()
        event = make_event("dk", "; rm -rf /")

        result = listener.on_event(event, extension)

        assert result.result_list[0].get_name() == "Invalid query"
        extension.list_containers.assert_not_called()

    def test_info_keyword_routes_to_show_docker_info(self):
        listener = KeywordQueryEventListener()
        extension = make_extension()
        event = make_event("dk:info", "")

        result = listener.on_event(event, extension)

        extension.show_docker_info.assert_called_once()
        assert result is extension.show_docker_info.return_value

    def test_prune_keyword_asks_for_confirmation_not_prune(self):
        """ Regression: dk:prune must not call prune() directly anymore. """
        listener = KeywordQueryEventListener()
        extension = make_extension()
        event = make_event("dk:prune", "")

        result = listener.on_event(event, extension)

        extension.confirm_prune.assert_called_once()
        extension.prune.assert_not_called()
        assert result is extension.confirm_prune.return_value

    def test_documentation_keyword_routes_with_query(self):
        listener = KeywordQueryEventListener()
        extension = make_extension()
        event = make_event("dk:docs", "volumes")

        listener.on_event(event, extension)

        extension.search_documentation.assert_called_once_with("volumes")

    def test_default_keyword_lists_containers(self):
        listener = KeywordQueryEventListener()
        extension = make_extension()
        event = make_event("dk", "nginx")

        listener.on_event(event, extension)

        extension.list_containers.assert_called_once_with("nginx")

    def test_empty_argument_defaults_to_empty_string(self):
        listener = KeywordQueryEventListener()
        extension = make_extension()
        event = make_event("dk", None)

        listener.on_event(event, extension)

        extension.list_containers.assert_called_once_with("")
