import ctypes
import logging
import threading

from .exceptions import RequestTimeoutException

logger = logging.getLogger(__name__)


class ThreadingTimeout(object):  # pragma: no cover
    def __init__(self, seconds):
        self.seconds = seconds
        self.target_tid = threading.current_thread().ident
        self.timer = None

    def __enter__(self):
        self.timer = threading.Timer(self.seconds, self._raise_exc)
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.timer.cancel()
        if exc_type is RequestTimeoutException:
            logger.warning(
                "Request handling exceeded {0} seconds timeout; terminating request handling...".format(
                    self.seconds
                ),
                exc_info=(exc_type, exc_val, exc_tb),
            )
        return False

    def _raise_exc(self):
        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.target_tid), ctypes.py_object(RequestTimeoutException)
        )
        if ret == 0:
            raise ValueError("Invalid thread ID {}".format(self.target_tid))
        elif ret > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.target_tid), None
            )
            raise SystemError("PyThreadState_SetAsyncExc failed")
