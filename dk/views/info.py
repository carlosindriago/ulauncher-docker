"""
Displays information about Docker Daemon
"""
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction


class InfoView():
    """ Displays some information about the Docker daemon """

    def __init__(self, extension):
        self.extension = extension

    def render(self):
        """ Show docker info """
        if not self.extension.docker_available:
             return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Docker is not running',
                    description='Please start the Docker Daemon',
                    on_enter=HideWindowAction())
            ])

        info = self.extension.docker_client.version()

        items = []
        data = [
            {
                'name': 'Docker Version',
                'description': info['Version'],
                'action': HideWindowAction()
            },
            {
                'name': 'Documentation',
                'description': 'Open Docker documentation',
                'action': OpenUrlAction("https://docs.docker.com/")
            },
            {
                'name':
                'Awesome Docker',
                'description':
                'Awesome Docker',
                'action':
                OpenUrlAction(
                    "https://list.community/veggiemonk/awesome-docker")
            },
        ]

        for item in data:
            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=item['name'],
                                    highlightable=False,
                                    description=item['description'],
                                    on_enter=item['action']))

        return RenderResultListAction(items)
