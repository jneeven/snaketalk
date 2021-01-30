"""TODO: Run a mattermost server inside a docker container. Ideally there would be two
pre-defined bot accounts with fixed tokens, but if not we can create them here through
the API. We should then run two bots, each in their own process, and have one send a
sequence of messages intended to trigger each of the listeners in the DefaultPlugin.
After some delay, it should check that the responses are as intended (e.g. was an emoji
added, did the other bot respond with an ephemeral message, etc.).

To easily see what's wrong if any if this fails, we should define the sequence bot as
a global inside its own process, so we can then define a bunch of individual pytest
functions that will send a specific message and wait for a response.
"""
