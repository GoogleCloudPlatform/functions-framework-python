import logging
import time

import functions_framework

logger = logging.getLogger(__name__)


@functions_framework.http
def main(request):
    timeout = 2
    for _ in range(timeout * 10):
        time.sleep(0.1)
    logger.info("logging message after timeout elapsed")
    return "Hello, world!"

