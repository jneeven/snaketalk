from typing import Dict


class WebHookEvent(object):
    def __init__(
        self,
        body: Dict,
    ):
        """Wrapper around a webhook post event. Contains cached properties for
        convenient variable access.

        Arguments:
        - body: dictionary, body of the post request.
        """
        self.body = body

    # TODO: implement attributes
