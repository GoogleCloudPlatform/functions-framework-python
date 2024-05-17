import logging
import time

logger = logging.getLogger(__name__)


def function(request):
    # sleep for 1200 total ms (1.8 sec)
    for _ in range(12):
        time.sleep(0.1)
    logger.info("some extra logging message")
    return "success", 200
