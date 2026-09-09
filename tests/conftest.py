"""
Shared pytest fixtures for the ulauncher-docker test suite.
"""
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def ulauncher_ws_env(monkeypatch):
    """
    ulauncher's base Extension/Client classes require this env var to be set
    at construction time, even though no real websocket connection is made
    until .run() is called.
    """
    monkeypatch.setenv("ULAUNCHER_WS_API", "ws://localhost:5054")


@pytest.fixture
def mock_docker_client():
    """A MagicMock standing in for docker.DockerClient."""
    client = MagicMock()
    client.ping.return_value = True
    return client


@pytest.fixture
def extension(mock_docker_client):
    """
    A real DockerExtension instance with the Docker SDK and GTK
    notifications mocked out, so tests don't need a running Docker daemon
    or a D-Bus session.
    """
    with patch("dk.extension.docker.from_env", return_value=mock_docker_client), \
         patch("dk.extension.Notify"):
        from dk.extension import DockerExtension
        ext = DockerExtension()
        yield ext
