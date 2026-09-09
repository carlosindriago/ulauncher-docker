"""
Tests for dk.views.container_details.ContainerDetailsView.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import docker

from dk.views.container_details import ContainerDetailsView


def make_extension(docker_available=True, default_terminal="gnome-terminal"):
    ext = MagicMock()
    ext.docker_available = docker_available
    ext.icon_path = "images/icon.png"
    ext.preferences = {"default_terminal": default_terminal}
    return ext


def make_container(status="running", ip_address="172.17.0.2", ports=None,
                   image="nginx:latest", short_id="abc123def456",
                   started_at=None, stats_payload=None):
    container = MagicMock()
    container.name = "web"
    container.status = status
    container.short_id = short_id
    container.attrs = {
        "Config": {"Image": image},
        "State": {
            "Status": status,
            "StartedAt": started_at or "0001-01-01T00:00:00Z",
        },
        "NetworkSettings": {
            "Ports": ports or {},
            "IPAddress": ip_address,
            "Networks": {},
        },
    }
    # Default to an empty (but well-formed) payload, so tests that don't
    # care about resource usage don't need to worry about it either way.
    container.stats.return_value = {} if stats_payload is None else stats_payload
    return container


def make_stats_payload(cpu_delta=20_000_000, system_delta=200_000_000,
                       online_cpus=4, mem_usage=100 * 1024 * 1024,
                       mem_limit=1024 * 1024 * 1024):
    return {
        "cpu_stats": {
            "cpu_usage": {"total_usage": cpu_delta},
            "system_cpu_usage": system_delta,
            "online_cpus": online_cpus,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 0},
            "system_cpu_usage": 0,
        },
        "memory_stats": {"usage": mem_usage, "limit": mem_limit},
    }


class TestBuildTerminalCmd:

    def test_dash_x_terminals(self):
        view = ContainerDetailsView(MagicMock())
        assert view._build_terminal_cmd("xfce4-terminal", "sh") == "xfce4-terminal -x sh"
        assert view._build_terminal_cmd("terminator", "sh") == "terminator -x sh"

    def test_dash_dash_for_kitty(self):
        view = ContainerDetailsView(MagicMock())
        assert view._build_terminal_cmd("kitty", "sh") == "kitty -- sh"

    def test_default_dash_e(self):
        view = ContainerDetailsView(MagicMock())
        assert view._build_terminal_cmd("gnome-terminal", "sh") == "gnome-terminal -e sh"


class TestRender:

    def test_docker_unavailable(self):
        extension = make_extension(docker_available=False)
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        assert result.result_list[0].get_name() == "Docker is not running"

    def test_container_not_found(self):
        extension = make_extension()
        extension.docker_client.containers.get.side_effect = docker.errors.NotFound("nope")
        view = ContainerDetailsView(extension)

        result = view.render("missing")

        assert "No container found" in result.result_list[0].get_name()

    def test_running_container_shows_lifecycle_actions(self):
        extension = make_extension()
        extension.docker_client.containers.get.return_value = make_container()
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        names = [item.get_name() for item in result.result_list]
        assert "IP Address" in names
        assert "Stop" in names
        assert "Restart" in names
        assert "Open container shell" in names
        assert "Logs" in names
        assert "Start" not in names

    def test_shell_command_quotes_the_container_id(self):
        """ Regression: short_id must go through shlex.quote before RunScriptAction. """
        extension = make_extension()
        extension.docker_client.containers.get.return_value = make_container(
            short_id="abc123; rm -rf /")
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        shell_item = next(i for i in result.result_list
                          if i.get_name() == "Open container shell")
        # The dangerous id must be shell-quoted, not passed through raw.
        assert "'abc123; rm -rf /'" in shell_item._on_enter.script

    def test_stopped_container_shows_start_only(self):
        extension = make_extension()
        extension.docker_client.containers.get.return_value = make_container(status="exited")
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        names = [item.get_name() for item in result.result_list]
        assert "Start" in names
        assert "Stop" not in names
        assert "IP Address" not in names

    def test_ports_are_listed_when_present(self):
        extension = make_extension()
        extension.docker_client.containers.get.return_value = make_container(ports={
            "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}],
        })
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        ports_item = next(i for i in result.result_list if i.get_name() == "Ports")
        assert "8080" in ports_item.get_description(None)

    def test_falls_back_to_network_ip_when_default_ip_missing(self):
        extension = make_extension()
        container = make_container(ip_address="")
        container.attrs["NetworkSettings"]["Networks"] = {
            "custom_net": {"IPAddress": "10.0.0.5"},
        }
        extension.docker_client.containers.get.return_value = container
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        ip_item = next(i for i in result.result_list if i.get_name() == "IP Address")
        assert ip_item.get_description(None) == "10.0.0.5"

    def test_falls_back_when_ip_address_key_is_entirely_missing(self):
        """
        Regression: some Docker Engine versions omit the top-level
        NetworkSettings.IPAddress key entirely (not just leave it empty)
        when only custom networks are attached - direct indexing used to
        raise an unhandled KeyError here (found via a live Docker daemon).
        """
        extension = make_extension()
        container = make_container(ip_address="172.17.0.2")
        del container.attrs["NetworkSettings"]["IPAddress"]
        container.attrs["NetworkSettings"]["Networks"] = {
            "custom_net": {"IPAddress": "10.0.0.9"},
        }
        extension.docker_client.containers.get.return_value = container
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        ip_item = next(i for i in result.result_list if i.get_name() == "IP Address")
        assert ip_item.get_description(None) == "10.0.0.9"

    def test_shows_uptime_for_running_container(self):
        fixed_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        started_at = fixed_now - timedelta(hours=2, minutes=15)

        extension = make_extension()
        extension.docker_client.containers.get.return_value = make_container(
            started_at=started_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        view = ContainerDetailsView(extension)

        with patch("dk.views.container_details.utcnow", return_value=fixed_now):
            result = view.render("abc123")

        uptime_item = next(i for i in result.result_list if i.get_name() == "Uptime")
        assert uptime_item.get_description(None) == "2h 15m"

    def test_shows_resource_usage_when_stats_available(self):
        extension = make_extension()
        extension.docker_client.containers.get.return_value = make_container(
            stats_payload=make_stats_payload())
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        usage_item = next(i for i in result.result_list if i.get_name() == "Resource Usage")
        description = usage_item.get_description(None)
        assert "CPU" in description
        assert "Mem" in description

    def test_resource_usage_omitted_when_stats_call_fails(self):
        """ A stats() failure must not break the rest of the details view. """
        extension = make_extension()
        container = make_container()
        container.stats.side_effect = docker.errors.APIError("boom")
        extension.docker_client.containers.get.return_value = container
        view = ContainerDetailsView(extension)

        result = view.render("abc123")

        names = [item.get_name() for item in result.result_list]
        assert "Resource Usage" not in names
        assert "IP Address" in names  # rest of the view still renders
