"""
Tests for dk.extension.DockerExtension.
"""
import pickle
import subprocess
from unittest.mock import MagicMock, patch

import docker

from dk.actions import ACTION_CONFIRM_PRUNE

VALID_CONTAINER_ID = "a" * 12


class TestDockerAvailable:
    """ `docker_available` must be re-checked on every access. """

    def test_true_when_ping_succeeds(self, extension, mock_docker_client):
        mock_docker_client.ping.return_value = True
        assert extension.docker_available is True

    def test_false_when_ping_fails(self, extension, mock_docker_client):
        mock_docker_client.ping.side_effect = docker.errors.APIError("boom")
        assert extension.docker_available is False

    def test_recovers_after_daemon_restarts(self, extension, mock_docker_client):
        """ Regression: availability used to be cached once at __init__ time. """
        mock_docker_client.ping.side_effect = docker.errors.APIError("down")
        assert extension.docker_available is False

        mock_docker_client.ping.side_effect = None
        mock_docker_client.ping.return_value = True
        assert extension.docker_available is True

    def test_recreates_client_when_missing(self, extension, mock_docker_client):
        extension.docker_client = None
        with patch("dk.extension.docker.from_env", return_value=mock_docker_client):
            assert extension.docker_available is True
        assert extension.docker_client is mock_docker_client


class TestShowNotification:

    def test_truncates_long_text(self, extension):
        with patch("dk.extension.Notify") as mock_notify:
            extension.show_notification("x" * 300)
            args = mock_notify.Notification.new.call_args[0]
            assert len(args[1]) == 203  # 200 chars + "..."

    def test_escapes_html(self, extension):
        with patch("dk.extension.Notify") as mock_notify:
            extension.show_notification("<script>alert(1)</script>")
            args = mock_notify.Notification.new.call_args[0]
            assert "<script>" not in args[1]


class TestContainerLifecycle:

    def test_start_rejects_invalid_id_format(self, extension, mock_docker_client):
        extension.start_container("../../etc/passwd; rm -rf /")
        mock_docker_client.containers.get.assert_not_called()

    def test_start_when_docker_unavailable(self, extension, mock_docker_client):
        mock_docker_client.ping.side_effect = docker.errors.APIError("down")
        with patch.object(extension, "show_notification") as notify:
            extension.start_container(VALID_CONTAINER_ID)
            notify.assert_called_once_with("Docker daemon is not running")
        mock_docker_client.containers.get.assert_not_called()

    def test_start_success(self, extension, mock_docker_client):
        container = MagicMock()
        mock_docker_client.containers.get.return_value = container
        with patch.object(extension, "show_notification") as notify:
            extension.start_container(VALID_CONTAINER_ID)
        container.start.assert_called_once()
        notify.assert_called_once_with(
            "Container %s started successfully" % VALID_CONTAINER_ID[:12])

    def test_start_not_found(self, extension, mock_docker_client):
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound("nope")
        with patch.object(extension, "show_notification") as notify:
            extension.start_container(VALID_CONTAINER_ID)
            notify.assert_called_once_with("Container not found")

    def test_stop_notification_truncates_id(self, extension, mock_docker_client):
        """ Regression: stop/restart used to leak the full container id. """
        long_id = "b" * 64
        mock_docker_client.containers.get.return_value = MagicMock()
        with patch.object(extension, "show_notification") as notify:
            extension.stop_container(long_id)
            notify.assert_called_once_with(
                "Container %s stopped with success" % long_id[:12])

    def test_restart_notification_truncates_id(self, extension, mock_docker_client):
        long_id = "c" * 64
        mock_docker_client.containers.get.return_value = MagicMock()
        with patch.object(extension, "show_notification") as notify:
            extension.restart_container(long_id)
            notify.assert_called_once_with(
                "Container %s restarted with success" % long_id[:12])


class TestPrune:

    def test_confirm_prune_does_not_run_prune(self, extension):
        """ Regression: dk:prune must ask for confirmation, not act immediately. """
        result = extension.confirm_prune()
        item = result.result_list[0]
        action_data = pickle.loads(item._on_enter._data)
        assert action_data == {'action': ACTION_CONFIRM_PRUNE}

    def test_prune_success(self, extension):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok")
        with patch("dk.extension.subprocess.run", return_value=completed), \
             patch.object(extension, "show_notification") as notify:
            extension.prune()
            notify.assert_called_once()
            assert "successfully" in notify.call_args[0][0]

    def test_prune_failure(self, extension):
        with patch("dk.extension.subprocess.run",
                   side_effect=subprocess.CalledProcessError(1, "docker")), \
             patch.object(extension, "show_notification") as notify:
            extension.prune()
            notify.assert_called_once()
            assert "failed" in notify.call_args[0][0]


class TestListContainers:

    def test_default_query_shows_only_running(self, extension):
        extension.list_containers_view = MagicMock()
        extension.list_containers("")
        extension.list_containers_view.render.assert_called_once_with(
            "", only_running=True)

    def test_dash_a_shows_all_containers(self, extension):
        extension.list_containers_view = MagicMock()
        extension.list_containers("-a")
        extension.list_containers_view.render.assert_called_once_with(
            "", only_running=False)

    def test_dash_a_with_name_filter(self, extension):
        extension.list_containers_view = MagicMock()
        extension.list_containers("-a nginx")
        extension.list_containers_view.render.assert_called_once_with(
            "nginx", only_running=False)
