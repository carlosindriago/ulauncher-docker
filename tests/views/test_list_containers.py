"""
Tests for dk.views.list_containers.ListContainersView.
"""
import pickle
from unittest.mock import MagicMock, patch

from dk.actions import ACTION_DETAIL_CONTAINER, ACTION_START_CONTAINER
from dk.views.list_containers import ListContainersView


def make_extension(docker_available=True):
    ext = MagicMock()
    ext.docker_available = docker_available
    ext.icon_path = "images/icon.png"
    return ext


def make_container(name, status, container_id, attrs=None, short_id=None):
    container = MagicMock()
    container.name = name
    container.status = status
    container.id = container_id
    container.short_id = short_id or container_id[:12]
    container.attrs = attrs or {}
    return container


class TestListContainersView:

    def test_docker_unavailable(self):
        extension = make_extension(docker_available=False)
        view = ListContainersView(extension)

        result = view.render("")

        assert result.result_list[0].get_name() == "Docker is not running"
        extension.docker_client.containers.list.assert_not_called()

    def test_rejects_invalid_query_characters(self):
        extension = make_extension()
        view = ListContainersView(extension)

        result = view.render("; rm -rf /")

        assert result.result_list[0].get_name() == "Invalid container name"
        extension.docker_client.containers.list.assert_not_called()

    def test_no_containers_found(self):
        extension = make_extension()
        extension.docker_client.containers.list.return_value = []
        view = ListContainersView(extension)

        result = view.render("ghost")

        assert "No containers found" in result.result_list[0].get_name()

    def test_lists_matching_containers(self):
        extension = make_extension()
        extension.docker_client.containers.list.return_value = [
            make_container("web", "running", "abc123"),
        ]
        view = ListContainersView(extension)

        result = view.render("web")

        extension.docker_client.containers.list.assert_called_once_with(
            filters={"name": "web", "status": "running"}, limit=8)
        assert result.result_list[0].get_name() == "web"
        assert result.result_list[0].get_description(None) == "running"

    def test_only_running_false_omits_status_filter(self):
        extension = make_extension()
        extension.docker_client.containers.list.return_value = []
        view = ListContainersView(extension)

        view.render("", only_running=False)

        extension.docker_client.containers.list.assert_called_once_with(
            filters={}, limit=8)

    def test_description_includes_relative_activity(self):
        from datetime import datetime, timedelta, timezone

        fixed_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        started_at = (fixed_now - timedelta(hours=2, minutes=15)).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ")

        extension = make_extension()
        extension.docker_client.containers.list.return_value = [
            make_container("web", "running", "abc123", attrs={
                "State": {"Status": "running", "StartedAt": started_at},
            }),
        ]
        view = ListContainersView(extension)

        with patch("dk.timeutils.utcnow", return_value=fixed_now):
            result = view.render("")

        assert result.result_list[0].get_description(None) == "running · up 2h 15m"

    def test_enter_on_running_container_opens_details(self):
        extension = make_extension()
        extension.docker_client.containers.list.return_value = [
            make_container("web", "running", "abc123"),
        ]
        view = ListContainersView(extension)

        result = view.render("")
        item = result.result_list[0]

        action_data = pickle.loads(item._on_enter._data)
        assert action_data == {'action': ACTION_DETAIL_CONTAINER, 'container_id': 'abc123'}
        assert item._on_alt_enter is None

    def test_enter_on_stopped_container_starts_it_alt_enter_shows_details(self):
        extension = make_extension()
        extension.docker_client.containers.list.return_value = [
            make_container("web", "exited", "abc123", short_id="abc123def456"),
        ]
        view = ListContainersView(extension)

        result = view.render("", only_running=False)
        item = result.result_list[0]

        enter_data = pickle.loads(item._on_enter._data)
        assert enter_data == {'action': ACTION_START_CONTAINER, 'id': 'abc123def456'}

        alt_enter_data = pickle.loads(item._on_alt_enter._data)
        assert alt_enter_data == {'action': ACTION_DETAIL_CONTAINER, 'container_id': 'abc123'}
