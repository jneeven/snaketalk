import mattermostdriver


class Driver(mattermostdriver.Driver):
    user_id: str = ""
    username: str = ""

    def login(self, *args, **kwargs):
        super().login(*args, **kwargs)
        self.user_id = self.client._userid
        self.username = self.client._username
