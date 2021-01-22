import queue
import threading

import mattermostdriver


class ThreadPool(object):
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.alive = True
        self._queue = queue.Queue()
        self._busy_workers = queue.Queue()

        # Spawn num_workers threads that will wait for work to be added to the queue
        self._threads = []
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self.handle_work)
            self._threads.append(worker)
            worker.start()

    def add_task(self, *args):
        self._queue.put(args)

    def get_busy_workers(self):
        return self._busy_workers.qsize()

    def stop(self):
        """Signals all threads that they should stop and waits for them to finish."""
        self.alive = False
        for thread in self._threads:
            self._queue.put((self._stop_thread, tuple()))
            thread.join()

    def _stop_thread(self):
        """Used to stop individual threads."""
        return

    def handle_work(self):
        while self.alive:
            # Wait for a new task (blocking)
            function, arguments = self._queue.get()
            # Notify the pool that we started working
            self._busy_workers.put(1)
            # TODO: how does this work with keyword args?
            function(*arguments)
            # Notify the pool that we finished working
            self._queue.task_done()
            self._busy_workers.get()


class Driver(mattermostdriver.Driver):
    user_id: str = ""
    username: str = ""

    def __init__(self, *args, num_threads=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.threadpool = ThreadPool(num_workers=num_threads)

    def login(self, *args, **kwargs):
        super().login(*args, **kwargs)
        self.user_id = self.client._userid
        self.username = self.client._username
