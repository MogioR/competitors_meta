import requests
from time import sleep

from bs4 import BeautifulSoup

from Modules.Logger.logger import get_logger

import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/41.0.2228.0 Safari/537.3'}

logger = get_logger(__name__)


class WebpageDetails:
    def __init__(self, title, description, url, h1):
        self.title = title
        self.description = description
        self.url = url
        self.h1 = h1


class RequestsScraper:
    # Get html by url
    @staticmethod
    def open_page(url: str):
        for attempt in range(2):
            logger.info(f'Trying to open {url}')
            response = requests.get(url, headers=headers, timeout=40, verify=False)
            logger.info("Status code response " + str(response.status_code))
            if response.status_code == 200:
                if response.text.find('windows-1251') != -1:
                    response.encoding = 'cp1251'
                else:
                    response.encoding = 'utf-8'
                return response.text
            sleep(2)

        raise Exception('Can not load site: ' + url)

    # Get WebpageDetails by url
    @staticmethod
    def get_page_details(url: str):
        try:
            page = RequestsScraper.open_page(url)
            soup = BeautifulSoup(page, "html.parser")

        except Exception as e:
            logger.error(str(e))
            return WebpageDetails('', '', url, '')

        # Get h1
        h1 = soup.find('h1', {'class': 'page-title-big'})
        if h1 is None:
            h1_str = ''
        else:
            h1_str = h1.string

        # Get title
        title = soup.find('title')
        if title is None:
            title_str = ''
        else:
            title_str = title.string

        # Get description
        description = soup.find('meta', {'name': 'description'})
        if description is None:
            description = soup.find('meta', {'name': 'Description'})
        if description is None:
            description = soup.find('meta', {'property': 'og:description'})
        if description is None:
            description = soup.find('meta', {'property': 'description'})

        if description is None:
            description_str = ''
        else:
            description_str = description['content']

        return WebpageDetails(title_str, description_str, url, h1_str)
