""" Container Details """

import docker
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from dk.actions import ACTION_START_CONTAINER, ACTION_STOP_CONTAINER, ACTION_RESTART_CONTAINER


class ContainerDetailsView():
    """ Show container details """

    def __init__(self, extension):
        self.extension = extension

    def _build_terminal_cmd(self, terminal_prog, command):
        """
        SENSEI FIX: Detecta si es XFCE para usar la bandera correcta (-x)
        en lugar de la estándar (-e) de Gnome/Tilix.
        """
        if "xfce4-terminal" in terminal_prog:
            # XFCE usa -x para ejecutar el resto de la línea
            return "%s -x %s" % (terminal_prog, command)
        
        # Fallback para Gnome Terminal, Tilix, etc (usan -e)
        return "%s -e %s" % (terminal_prog, command)

    def render(self, container_id):
        """ Show container details """

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

        ip_address = container.attrs['NetworkSettings']['IPAddress']

        if not ip_address:
            # Manejo de redes personalizadas donde la IP está anidada
            networks = attrs['NetworkSettings']['Networks']
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
            shell_cmd_str = "docker exec -it %s sh" % container.short_id
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
            
            # --- SENSEI MOD: Logs Command ---
            logs_cmd_str = "docker logs -f %s" % container.short_id
            final_logs_cmd = self._build_terminal_cmd(default_terminal, logs_cmd_str)

            items.append(
                ExtensionResultItem(icon='images/icon_logs.png',
                                    name="Logs",
                                    description="Show logs of the container",
                                    highlightable=False,
                                    on_enter=RunScriptAction(final_logs_cmd, [])))

        return RenderResultListAction(items)