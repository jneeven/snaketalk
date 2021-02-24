import logging
import queue
import threading
import time

from snaketalk.scheduler import default_scheduler
from snaketalk.webhook_server import WebhookServer


class ThreadPool(object):
    def __init__(self, num_workers: int):
        """Threadpool class to easily specify a number of worker threads and assign work
        to any of them.

        Arguments:
        - num_workers: int, how many threads to run simultaneously.
        """
        self.num_workers = num_workers
        self.webhook_server = WebhookServer()
        self.alive = False
        self._queue = queue.Queue()
        self._busy_workers = queue.Queue()
        self._threads = []

    def add_task(self, function, *args):
        self._queue.put((function, args))

    def get_busy_workers(self):
        return self._busy_workers.qsize()

    def start(self):
        self.alive = True
        # Spawn num_workers threads that will wait for work to be added to the queue
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self.handle_work)
            self._threads.append(worker)
            worker.start()

    def stop(self):
        """Signals all threads that they should stop and waits for them to finish."""
        self.alive = False
        # Signal every thread that it's time to stop
        for _ in range(self.num_workers):
            self._queue.put((self._stop_thread, tuple()))
        # Wait for each of them to finish
        print("Stopping threadpool, waiting for threads...")
        for thread in self._threads:
            thread.join()
        print("Threadpool stopped.")

    def _stop_thread(self):
        """Used to stop individual threads."""
        return

    def handle_work(self):
        while self.alive:
            # Wait for a new task (blocking)
            function, arguments = self._queue.get()
            # Notify the pool that we started working
            self._busy_workers.put(1)
            function(*arguments)
            # Notify the pool that we finished working
            self._queue.task_done()
            self._busy_workers.get()

    def start_scheduler_thread(self, trigger_period: float):
        def run_pending():
            logging.info("Scheduler thread started.")
            while self.alive:
                time.sleep(trigger_period)
                default_scheduler.run_pending()

        self.add_task(run_pending)

    def start_webhook_server_thread(self):
        def start_server():
            logging.info("Webhook server thread started.")
            while self.alive:
                self.webhook_server.start()

        self.add_task(start_server)