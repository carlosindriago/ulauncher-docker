"""
Ulauncher Docker Extension
Manage your Docker containers from Ulauncher
"""

import logging
import gi

gi.require_version('Notify', '0.7')

import docker  # noqa: E402
import subprocess  # noqa: E402
from gi.repository import Notify  # noqa: E402
from ulauncher.api.client.Extension import Extension  # noqa: E402
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent  # noqa: E402
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction  # noqa: E402
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction  # noqa: E402
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction  # noqa: E402
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction  # noqa: E402
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem  # noqa: E402

from dk.actions import ACTION_CONFIRM_PRUNE  # noqa: E402
from dk.listeners.query_listener import KeywordQueryEventListener  # noqa: E402
from dk.listeners.item_enter_listener import ItemEnterEventListener  # noqa: E402
from dk.views.container_details import ContainerDetailsView  # noqa: E402
from dk.views.info import InfoView  # noqa: E402
from dk.views.list_containers import ListContainersView  # noqa: E402

logger = logging.getLogger(__name__)


class DockerExtension(Extension):
    """ Extension entry point """

    def __init__(self):
        """ Initializes the extension """
        super(DockerExtension, self).__init__()

        # SECURE: Initialize with error handling for Docker not running.
        # The actual availability is re-checked on every access via the
        # `docker_available` property below, so this only creates the client.
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning("Could not initialize Docker client: %s", e)
            self.docker_client = None

        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

        self.icon_path = 'images/icon.png'
        self.list_containers_view = ListContainersView(self)
        self.container_details_view = ContainerDetailsView(self)
        self.info_view = InfoView(self)

        # SECURITY: Initialize notifications with error handling
        try:
            Notify.init("DockerExtension")
        except Exception as e:
            logger.error("Failed to initialize notifications: %s", e)

    @property
    def docker_available(self):
        """
        Re-checks Docker daemon availability on every access, so the extension
        recovers automatically if the daemon starts (or stops) after Ulauncher
        has already launched, without requiring a restart.
        """
        try:
            if self.docker_client is None:
                self.docker_client = docker.from_env()
            self.docker_client.ping()
            return True
        except Exception as e:
            logger.warning("Docker Daemon not available: %s", e)
            return False

    def show_notification(self, text):
        """
        Shows a notification
        Args:
          text (str): The text to display on the notification
        """
        # SECURITY: Validate and sanitize notification text
        if not isinstance(text, str):
            text = str(text)

        # Limit length to prevent notification overflow
        if len(text) > 200:
            text = text[:200] + "..."

        # Escape HTML characters to prevent XSS
        from html import escape
        safe_text = escape(text)

        try:
            Notify.Notification.new("Docker", safe_text).show()
        except Exception as e:
            logger.error("Failed to show notification: %s", e)

    def show_docker_info(self):
        """ Shows Docker daemon information"""
        return self.info_view.render()

    def list_containers(self, query):
        """
        Lists containers matching the query. Only running containers are
        shown by default; prefix the query with "-a" (e.g. "dk -a nginx")
        to include stopped containers too.
        """
        show_all = False
        if query:
            parts = query.split()
            if parts[0] == "-a":
                show_all = True
                query = " ".join(parts[1:])

        return self.list_containers_view.render(query, only_running=not show_all)

    def show_container_details(self, container_id):
        """ Show the details of the container with the specified id"""
        return self.container_details_view.render(container_id)

    def start_container(self, container_id):
        """
        Starts the container with the specified id
        Args:
          container_id (str): The container id
        """
        # SECURITY: Validate container_id format
        import re
        if not re.match(r'^[a-f0-9]{12,64}$', container_id):
            logger.error("Invalid container_id format: %s", container_id)
            self.show_notification("Invalid container ID format")
            return

        if not self.docker_available:
            logger.error("Docker not available")
            self.show_notification("Docker daemon is not running")
            return

        try:
            self.docker_client.containers.get(container_id).start()
            self.show_notification("Container %s started successfully" %
                                   container_id[:12])
        except docker.errors.NotFound:
            logger.error("Container not found: %s", container_id)
            self.show_notification("Container not found")
        except Exception as e:
            logger.error("Failed to start container %s: %s", container_id, e)
            self.show_notification("Failed to start container %s" %
                                   container_id[:12])

    def stop_container(self, container_id):
        """
        Stops the container with the specified id
        Args:
          container_id (str): The container id
        """
        if not self.docker_available:
            logger.error("Docker not available")
            self.show_notification("Docker daemon is not running")
            return

        try:
            self.docker_client.containers.get(container_id).stop()
            self.show_notification("Container %s stopped with success" %
                                   container_id[:12])
        except Exception as e:
            logger.error("Failed to stop container %s: %s", container_id, e)
            self.show_notification("Failed to stop container %s" %
                                   container_id[:12])

    def restart_container(self, container_id):
        """
        Restarts the container with the specified id
        Args:
          container_id (str): The container id
        """
        if not self.docker_available:
            logger.error("Docker not available")
            self.show_notification("Docker daemon is not running")
            return

        try:
            self.docker_client.containers.get(container_id).restart()
            self.show_notification("Container %s restarted with success" %
                                   container_id[:12])
        except Exception as e:
            logger.error("Failed to restart container %s: %s", container_id, e)
            self.show_notification("Failed to restart container %s" %
                                   container_id[:12])

    def confirm_prune(self):
        """
        Shows a confirmation prompt before running the destructive prune
        command, instead of running it immediately on `dk:prune`.
        """
        return RenderResultListAction([
            ExtensionResultItem(
                icon=self.icon_path,
                name="Confirm: remove ALL unused containers, networks and images",
                description="This action is irreversible. Press Enter to proceed.",
                highlightable=False,
                on_enter=ExtensionCustomAction({'action': ACTION_CONFIRM_PRUNE},
                                               keep_app_open=False))
        ])

    def prune(self):
        """ Run docker system prune command"""
        try:
            output = subprocess.run(
                ["docker", "system", "prune", "-a", "-f"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.show_notification("Prune completed successfully: %s" %
                                   output.stdout)
            return HideWindowAction()
        except Exception as e:
            self.show_notification("Prune command failed with error: %s" % e)

    def search_documentation(self, query):
        """ Searches on https://docs.docker.com """
        return RenderResultListAction([
            ExtensionResultItem(
                icon=self.icon_path,
                name="Press enter to search for %s" % query,
                highlightable=False,
                on_enter=OpenUrlAction("https://docs.docker.com/search/?q=%s" %
                                       str(query)))
        ])
