class TestFunction:
    def test_listen_to(self):
        # TODO: create a Function by using the listen_to decorator, and verify that
        # the regexp and regexp flags of the Function are correct
        pass

    def test_is_coroutine(self):
        # TODO: create two Functions, one wrapping a coroutine and one wrapping a normal
        # function.
        pass

    def test_wrap_function(self):
        # TODO: test whether a wrapped function is called correctly
        # TODO: test whether wrapping an already wrapped function also works
        pass

    def test_needs_mention(self):
        # Can use the test message from message_handler_test.py
        pass

    def test_direct_only(self):
        # Can use the test message from message_handler_test.py
        pass

    def test_allowed_users(self):
        # Can use the test message from message_handler_test.py
        pass


class TestPlugin:
    def test_initialize(self):
        # TODO: test whether the listeners are registered correctly. Can either create
        # a special testing Plugin or use DefaultPlugin.

        # TODO: verify that on_start is called.
        pass

    def test_call_function(self):
        # TODO: test whether async functions are called with await and other functions
        # are executed with the threadpool.
        # TODO: test whether the underlying function actually got executed by mocking
        pass
