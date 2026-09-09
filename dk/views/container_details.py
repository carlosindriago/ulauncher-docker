""" Container Details """

import logging

import docker
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from dk.actions import ACTION_START_CONTAINER, ACTION_STOP_CONTAINER, ACTION_RESTART_CONTAINER
from dk.timeutils import compute_cpu_percent, humanize_bytes, humanize_timedelta, \
    parse_docker_timestamp, utcnow

logger = logging.getLogger(__name__)


class ContainerDetailsView():
    """ Show container details """

    def __init__(self, extension):
        self.extension = extension

    def _build_terminal_cmd(self, terminal_prog, command):
        """
        Builds the terminal command based on the terminal program.
        """
        # Terminals that use -x
        if terminal_prog in ["xfce4-terminal", "terminator"]:
            return "%s -x %s" % (terminal_prog, command)

        # Terminals that use -- (like kitty)
        if terminal_prog in ["kitty"]:
            return "%s -- %s" % (terminal_prog, command)

        # Default to -e (gnome-terminal, tilix, alacritty, konsole, xterm, etc)
        return "%s -e %s" % (terminal_prog, command)

    def _resource_usage_items(self, container):
        """
        Builds the "Uptime" and "Resource Usage" items for a running
        container. `container.stats(stream=False)` is a blocking call that
        takes about a second, so failures are logged and swallowed rather
        than breaking the rest of the details view.
        """
        items = []

        started_at = parse_docker_timestamp(
            container.attrs.get('State', {}).get('StartedAt'))
        if started_at:
            items.append(
                ExtensionResultItem(
                    icon=self.extension.icon_path,
                    name="Uptime",
                    description=humanize_timedelta(utcnow() - started_at),
                    highlightable=False,
                    on_enter=HideWindowAction()))

        try:
            usage_parts = self._describe_resource_usage(container)
        except Exception as e:
            # `stats()` payload shape isn't guaranteed across platforms/
            # daemon versions - never let it break the rest of the details.
            logger.warning("Could not compute resource usage for container %s: %s",
                           container.short_id, e)
            usage_parts = []

        if usage_parts:
            items.append(
                ExtensionResultItem(
                    icon=self.extension.icon_path,
                    name="Resource Usage",
                    description=" · ".join(usage_parts),
                    highlightable=False,
                    on_enter=HideWindowAction()))

        return items

    def _describe_resource_usage(self, container):
        """
        Returns a list of "CPU x%" / "Mem x / y (z%)" strings from a single
        `stats(stream=False)` snapshot. May raise - callers should expect
        that and treat it as "usage unavailable".
        """
        stats = container.stats(stream=False)
        parts = []

        cpu_percent = compute_cpu_percent(stats)
        if cpu_percent is not None:
            parts.append("CPU %.1f%%" % cpu_percent)

        memory_stats = stats.get('memory_stats') or {}
        mem_usage = memory_stats.get('usage')
        mem_limit = memory_stats.get('limit')
        if mem_usage is not None and mem_limit:
            parts.append("Mem %s / %s (%.1f%%)" % (
                humanize_bytes(mem_usage), humanize_bytes(mem_limit),
                mem_usage / mem_limit * 100.0))

        return parts

    def render(self, container_id):
        """ Show container details """

        if not self.extension.docker_available:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=self.extension.icon_path,
                    name='Docker is not running',
                    description='Please start the Docker Daemon',
                    on_enter=HideWindowAction())
            ])

        try:
            container = self.extension.docker_client.containers.get(
                container_id)
        except docker.errors.NotFound:
            return RenderResultListAction([
                ExtensionResultItem(icon=self.extension.icon_path,
                                    name="No container found with id %s" %
                                    container_id,
                                    highlightable=False,
                                    on_enter=HideWindowAction())
            ])

        default_terminal = self.extension.preferences["default_terminal"]
        items = []

        attrs = container.attrs

        # Safety check for ports
        ports = container.attrs['NetworkSettings'].get('Ports') or {}

        ports_list = []
        for container_port, host_mapping in ports.items():
            if host_mapping is not None:
                ports_str = "%s -> %s" % (
                    container_port, "%s:%s" %
                    (host_mapping[0]['HostIp'], host_mapping[0]['HostPort']))
                ports_list.append(ports_str)

        # Some Docker Engine versions omit the top-level IPAddress key
        # entirely (rather than leaving it empty) when only custom networks
        # are attached, so use .get() instead of indexing directly.
        ip_address = container.attrs['NetworkSettings'].get('IPAddress', '')

        if not ip_address:
            # Manejo de redes personalizadas donde la IP está anidada
            networks = attrs['NetworkSettings'].get('Networks') or {}
            if networks:
                ip_address = list(networks.values())[0].get('IPAddress', 'Unknown')
            else:
                ip_address = "No IP"

        items.append(
            ExtensionResultItem(icon=self.extension.icon_path,
                                name=container.name,
                                description=attrs['Config']['Image'],
                                highlightable=False,
                                on_enter=HideWindowAction()))

        if container.status != 'running':
            items.append(
                ExtensionResultItem(
                    icon='images/icon_start.png',
                    name="Start",
                    description="Start the specified container",
                    highlightable=False,
                    on_enter=ExtensionCustomAction({
                        'action': ACTION_START_CONTAINER,
                        'id': container.short_id
                    })))

        if container.status == 'running':
            items.append(
                ExtensionResultItem(
                    icon='images/icon_ip.png',
                    name="IP Address",
                    description=ip_address,
                    highlightable=False,
                    on_enter=OpenUrlAction(ip_address),
                    on_alt_enter=CopyToClipboardAction(ip_address)))

            items.extend(self._resource_usage_items(container))

            if ports_list:
                items.append(
                    ExtensionResultItem(
                        icon='images/icon_ip.png',
                        name="Ports",
                        description='\n'.join(ports_list),
                        highlightable=False,
                        on_enter=HideWindowAction(),
                    ))

            # --- SENSEI MOD: Shell Command ---
            # SANITIZED: Use shlex.quote to prevent command injection
            import shlex
            shell_cmd_str = "docker exec -it %s sh" % shlex.quote(container.short_id)
            final_shell_cmd = self._build_terminal_cmd(default_terminal, shell_cmd_str)

            items.append(
                ExtensionResultItem(
                    icon='images/icon_terminal.png',
                    name="Open container shell",
                    description="Opens a new sh shell in the container (%s)" % default_terminal,
                    highlightable=False,
                    on_enter=RunScriptAction(final_shell_cmd, [])))

            items.append(
                ExtensionResultItem(icon='images/icon_stop.png',
                                    name="Stop",
                                    description="Stops The container",
                                    highlightable=False,
                                    on_enter=ExtensionCustomAction({
                                        'action':
                                        ACTION_STOP_CONTAINER,
                                        'id':
                                        container.short_id
                                    })))

            items.append(
                ExtensionResultItem(icon='images/icon_restart.png',
                                    name="Restart",
                                    description="Restarts the container",
                                    highlightable=False,
                                    on_enter=ExtensionCustomAction({
                                        'action':
                                        ACTION_RESTART_CONTAINER,
                                        'id':
                                        container.short_id
                                    })))

            # SANITIZED: Use shlex.quote to prevent command injection
            import shlex
            logs_cmd_str = "docker logs -f %s" % shlex.quote(container.short_id)
            final_logs_cmd = self._build_terminal_cmd(default_terminal, logs_cmd_str)

            items.append(
                ExtensionResultItem(icon='images/icon_logs.png',
                                    name="Logs",
                                    description="Show logs of the container",
                                    highlightable=False,
                                    on_enter=RunScriptAction(final_logs_cmd, [])))

        return RenderResultListAction(items)
