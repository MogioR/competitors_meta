from threading import Lock

from Modules.Logger.logger import get_logger
from .selenium_service import Browser

logger = get_logger(__name__)


class BrowserState(Browser):
    def __init__(self):
        super().__init__()
        self.busy = False
        self.lock = Lock()

    def try_lock_browser(self):
        if not self.busy:
            self.lock.acquire()
            try:
                if not self.busy:
                    self.busy = True
                else:
                    logger.error("Trying to lock busy browser")
                    raise RuntimeError("Trying to lock a busy browser")
            finally:
                self.lock.release()
            return self
        else:
            logger.error("Trying to lock busy browser")
            raise RuntimeError("Trying to lock a busy browser")

    def try_release_browser(self):
        if self.busy:
            self.lock.acquire()
            try:
                if self.busy:
                    self.busy = False
                else:
                    logger.error("Trying to acquire a not busy browser")
                    raise RuntimeError("Trying to acquire a not busy browser")
            finally:
                self.lock.release()
        else:
            logger.error("Trying to acquire a not busy browser")
            raise RuntimeError("Trying to acquire a not busy browser")


class BrowserPool:  # при использовании BrowserPool ОБЯЗАТЕЛЬНО использовать try ... finally: BrowserPool.close_all()
    def __init__(self, pool_size: int):
        browsers = []
        for progress, index in enumerate(range(pool_size)):
            browsers.append(BrowserState())
            logger.info("Creating browser pool: {:.2f}".format(round(((progress + 1) / pool_size) * 100, 2)) + "%")
        self.browsers = browsers

    def close_all(self):
        for browser in self.browsers:
            if browser.busy:
                logger.error("Trying to close a busy browser")
                raise RuntimeError("Trying to close a busy browser")
            browser.close_session()

