"""
Tests for dk.views.info.InfoView.
"""
from unittest.mock import MagicMock

from dk.views.info import InfoView


def make_extension(docker_available=True):
    ext = MagicMock()
    ext.docker_available = docker_available
    return ext


class TestInfoView:

    def test_docker_unavailable(self):
        extension = make_extension(docker_available=False)
        view = InfoView(extension)

        result = view.render()

        assert result.result_list[0].get_name() == "Docker is not running"
        extension.docker_client.version.assert_not_called()

    def test_shows_docker_version(self):
        extension = make_extension()
        extension.docker_client.version.return_value = {"Version": "27.0.1"}
        view = InfoView(extension)

        result = view.render()

        names_and_descriptions = {
            item.get_name(): item.get_description(None) for item in result.result_list
        }
        assert names_and_descriptions["Docker Version"] == "27.0.1"
        assert "Documentation" in names_and_descriptions
