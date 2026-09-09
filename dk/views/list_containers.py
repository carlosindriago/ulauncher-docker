""" List containers """

from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from dk.actions import ACTION_DETAIL_CONTAINER, ACTION_START_CONTAINER
from dk.timeutils import describe_container_activity


class ListContainersView():
    """ List containers view """

    def __init__(self, extension):
        self.extension = extension

    def render(self, query, only_running=True):
        """ Lists the Containers """

        if not self.extension.docker_available:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=self.extension.icon_path,
                    name='Docker is not running',
                    description='Please start the Docker Daemon',
                    on_enter=HideWindowAction())
            ])

        filters = {}

        # SANITIZED: Validate and sanitize query to prevent command injection
        if query:
            import re
            # Only allow alphanumeric, hyphens, underscores, and dots
            if not re.match(r'^[a-zA-Z0-9._-]+$', query):
                # Reject malicious queries
                return RenderResultListAction([
                    ExtensionResultItem(
                        icon=self.extension.icon_path,
                        name='Invalid container name',
                        description='Container names can only contain letters, numbers, hyphens, underscores, and dots',
                        on_enter=HideWindowAction())
                ])
            filters["name"] = query

        if only_running:
            filters["status"] = "running"

        containers = self.extension.docker_client.containers.list(
            filters=filters, limit=8)

        if not containers:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=self.extension.icon_path,
                    name='No containers found that match: {}'.format(query),
                    on_enter=HideWindowAction())
            ])

        items = []
        for container in containers:
            description = container.status
            activity = describe_container_activity(container.attrs)
            if activity:
                description = "%s · %s" % (description, activity)

            details_action = ExtensionCustomAction(
                {
                    'action': ACTION_DETAIL_CONTAINER,
                    'container_id': container.id
                },
                keep_app_open=True)

            if container.status == "running":
                # Enter opens the details view; there is nothing to "start".
                on_enter = details_action
                on_alt_enter = None
            else:
                # Enter starts the container right away; Alt+Enter still
                # opens the details view for anyone who wants more context.
                on_enter = ExtensionCustomAction(
                    {'action': ACTION_START_CONTAINER, 'id': container.short_id})
                on_alt_enter = details_action

            items.append(
                ExtensionResultItem(icon=self.extension.icon_path,
                                    name=container.name,
                                    description=description,
                                    on_enter=on_enter,
                                    on_alt_enter=on_alt_enter))

        return RenderResultListAction(items)
