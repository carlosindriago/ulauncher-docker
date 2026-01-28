""" List containers """

from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from dk.actions import ACTION_DETAIL_CONTAINER


class ListContainersView():
    """ List containers view """

    def __init__(self, extension):
        self.extension = extension

    def render(self, query, only_running=True):
        """ Lists the Containers """

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
            items.append(
                ExtensionResultItem(icon=self.extension.icon_path,
                                    name=container.name,
                                    description=container.status,
                                    on_enter=ExtensionCustomAction(
                                        {
                                            'action': ACTION_DETAIL_CONTAINER,
                                            'container_id': container.id
                                        },
                                        keep_app_open=True)))

        return RenderResultListAction(items)
