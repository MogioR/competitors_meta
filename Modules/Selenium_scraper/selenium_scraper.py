from time import sleep
from Modules.Logger.logger import get_logger

from Modules.Errors import TooManyAttemptsError
from Modules.Selenium_scraper.browser_pool_service import BrowserPool

logger = get_logger(__name__)


class WebpageDetails:
    def __init__(self, title, description, url, h1):
        self.title = title
        self.description = description
        self.url = url
        self.h1 = h1


class BrowserPoolWebpageDetails(BrowserPool):
    def __init__(self, pool_size: int):
        super().__init__(pool_size)

    def get_webpage_details(self, url):
        for attempt in range(1):
            for browser in self.browsers:
                if not browser.busy:
                    browser.try_lock_browser()
                    try:
                        browser.open_page(url)
                        return WebpageDetails(browser.get_page_title(), browser.get_page_description(), url,
                                              browser.get_page_h1())
                    finally:
                        browser.try_release_browser()
            sleep(2)
        logger.error("To many attempts to get a browser")

        raise TooManyAttemptsError