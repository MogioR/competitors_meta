import os
from time import sleep

from selenium import webdriver, common
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchWindowException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from Modules.Logger.logger import get_logger
logger = get_logger(__name__)

max_loading_time = 40  # TimeoutException, если страница грузится дольше


class Browser:
    options = Options()
    options.headless = True

    def __init__(self):
        self.driver = self._create_webdriver()

    def _create_webdriver(self):
        driver = webdriver.Chrome(options=self.options,
                                  executable_path=ChromeDriverManager(print_first_line=False).install())
        driver.set_page_load_timeout(max_loading_time)
        return driver

    def open_page(self, url):
        for attempt in range(3):
            try:
                logger.info(f'Trying to open {url}')
                self.driver.get(url)
                return self
            except TimeoutException:
                logger.warning("Can't load " + url + " under " + str(max_loading_time) + " seconds, trying again")
                sleep(5)
            except WebDriverException:
                logger.warning(f'WebDriverException, can\'t open site {url}')
                return self
        logger.error("Too many attempts to load " + url + " , restarting browser")
        self._restart()

    def close_session(self):
        try:
            self.driver.close()
        except NoSuchWindowException:
            pass
        self.driver.quit()

    def _restart(self):
        self.driver.delete_all_cookies()
        self.close_session()
        self.driver = self._create_webdriver()

    def get_page_title(self):
        try:
            return self.driver.title
        except:
            return '-'

    def get_page_body(self):
        try:
            return self.driver.find_element_by_tag_name("body").get_attribute('innerHTML')
        except common.exceptions.NoSuchElementException:
            return ""

    def get_page_h1(self):
        try:
            return self.driver.find_element_by_xpath("//h1[@class='page-title-big']").text
        except:
            return ""

    def get_page_description(self):
        try:
            return self.driver.find_element_by_xpath("//meta[@name='description']").get_attribute("content")
        except common.exceptions.NoSuchElementException:
            try:
                return self.driver.find_element_by_xpath("//meta[@property='og:description']").get_attribute("content")
            except common.exceptions.NoSuchElementException:
                try:
                    return self.driver.find_element_by_xpath("//meta[@name='Description']").get_attribute(
                        "content")
                except common.exceptions.NoSuchElementException:
                    try:
                        return self.driver.find_element_by_xpath("//meta[@property='description']").get_attribute(
                            "content")
                    except common.exceptions.NoSuchElementException:
                        return ""

    def get_id_cont(self):
        try:
            return self.driver.find_element_by_xpath("//div[@class='org-heading-right']").get_attribute("data-con")
        except common.exceptions.NoSuchElementException:
            return ""