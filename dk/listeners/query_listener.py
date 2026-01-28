from ulauncher.api.client.EventListener import EventListener


class KeywordQueryEventListener(EventListener):
    """ Listener that handles the user input """

    # pylint: disable=unused-argument,no-self-use
    def on_event(self, event, extension):
        """ Handles the event """
        
        # SANITIZED: Validate and sanitize query to prevent command injection
        import re
        query = event.get_argument() or ""
        
        # Only allow alphanumeric, spaces, and basic punctuation
        if query and not re.match(r'^[a-zA-Z0-9\s._-]+$', query):
            # Reject malicious queries
            from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
            from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
            from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=extension.icon_path,
                    name='Invalid query',
                    description='Query contains invalid characters',
                    on_enter=HideWindowAction())
            ])
        
        kw = self.get_keyword_id(extension, event.get_keyword())

        if kw == "kw_info":
            return extension.show_docker_info()

        if kw == "kw_prune":
            return extension.prune()

        if kw == "kw_documentation":
            return extension.search_documentation(query)

        return extension.list_containers(query)

    def get_keyword_id(self, extension, keyword):
        """ Returns the keyword ID from the keyword name """
        kw_id = None
        for key, value in extension.preferences.items():
            if value == keyword:
                kw_id = key
                break

        return kw_id
