import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from snaketalk import schedule


def test_once():
    def job(path: str):
        print("job executed!")
        path = Path(path).write_text(str(time.time()))

    with tempfile.NamedTemporaryFile("r") as file:
        # Schedule the above to run once, two seconds from now
        start = time.time()
        schedule.once(datetime.fromtimestamp(start + 2)).do(job, file.name)
        assert file.readline() == ""

        # We trigger this every now and then, but the job should only execute at the
        # specified time.
        while time.time() < start + 3:
            schedule.run_pending()
            time.sleep(0.05)

        file.seek(0)
        # Verify that the written time was within 0.1 seconds of the expected time
        assert float(file.readline()) - 2 == pytest.approx(start, abs=0.1)


def test_recurring():
    def job(path: str):
        path = Path(path)
        # Increment number by one.
        current = path.read_text() or "0"
        new_number = int(current) + 1
        path.write_text(str(new_number))

        # Since this should run in a separate process, this shouldn't block anything.
        time.sleep(5)

    with tempfile.NamedTemporaryFile("r") as file:
        # Schedule the above to run every second
        schedule.every(1).seconds.do(job, file.name)

        # Assert nothing has changed yet
        file.readline() == "0"

        start = time.time()
        end = start + 5.5  # We want to wait just over 5 seconds
        while time.time() < end:
            # Launch job and wait one second
            schedule.run_pending()
            time.sleep(1)

        # Stop all scheduled jobs
        schedule.clear()
        # Nothing should happen from this point, even if we sleep another while
        time.sleep(2)

        # We expect the job to have been launched 5 times, and since the sleep time
        # in the job should not be blocking, the number must have increased 5 times.
        file.seek(0)
        assert file.readline() == "5"
