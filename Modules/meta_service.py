import math
import re
import os
import json
from datetime import date
from multiprocessing import Pool

from multiprocessing_logging import install_mp_handler
from tqdm import tqdm

from Modules.Logger.logger import get_logger
from Modules.Xml_river import GoogleXmlRiver
from Modules.Xml_river import YandexXmlRiver
from Modules.Tokenizer.pymorphy2_tokenizer import Pymorphy2Tokenizer
from Modules.GoogleApi.google_sheets_api import GoogleSheetsApi
from Modules.GoogleApi.google_drive_api import GoogleDriveApi
from Modules.request_scraper import RequestsScraper

logger = get_logger(__name__)
install_mp_handler()

# River threads (max=8)
RIVER_THREADS = 8

# Colors for formatting rules in google sheets
RED_COLORIZING = [230 / 255, 184 / 255, 175 / 255]
GREEN_COLORIZING = [217 / 255, 234 / 255, 211 / 255]

if os.environ['DEBUG'] is not None:
    DEBUG = os.environ['DEBUG']
else:
    DEBUG = 'FALSE'


class MetaService:
    def __init__(self, config):

        if config['Main']['default_search_engine'] == 'GOOGLE':
            self.searchEngine = GoogleXmlRiver(config)
            self.searchEngineType = 'GOOGLE'
        elif config['Main']['default_search_engine'] == 'YANDEX':
            self.searchEngine = YandexXmlRiver(config)
            self.searchEngineType = 'YANDEX'
        else:
            logger.error('Incorrect default_search_engine, use Google or Yandex')
            raise Exception('Incorrect default_search_engine, use Google or Yandex')
        self.searchEngine.set_region(config['Main']['default_region'])

        self.tolerance_hint_title = float(config['Main']['default_title_tolerance_hint'])
        self.tolerance_hint_desc = float(config['Main']['default_description_tolerance_hint'])
        self.min_urls = config['Main']['default_minimum_urls']

        self.file_in = config['Main']['default_input_file']
        self.file_out = config['Main']['output_json_path']
        self.drive_folder = config['Main']['default_drive_folder']

        self.google_token = config['GoogleSheets']['token']
        self.google_document_in_id = config['GoogleSheets']['document_in_id']
        self.google_in_sheet = config['GoogleSheets']['input_sheet_name']
        self.google_document_out_id = config['GoogleSheets']['document_out_id']

        self.tokenizer = Pymorphy2Tokenizer()
        self.parser = RequestsScraper()

    def __del__(self):
        pass

    # Return query items by key
    def get_content_by_key(self, key: str):
        try:
            query_items = self.searchEngine.get_query_items(key)
        except Exception as e:
            raise e

        return query_items

    # Return url item for export
    def get_export_url_item(self, url: str, query_title: str, query_description: str):
        return {
            'url': url,
            'query_title': query_title,
            'query_desc': query_description,
            'hint_query_title': self.get_hints(query_title),
            'hint_query_desc': self.get_hints(query_description)
        }

    # Return query item for export
    def get_export_query_item(self, query: str, urls: list, query_titles: list, query_descriptions: list,
                              url='', title='', description='', query_title='', query_description=''):
        # Gen url items
        export_url_items = []
        for i in range(len(urls)):
            export_url_items.append(self.get_export_url_item(urls[i], query_titles[i], query_descriptions[i]))

        # Gen hints
        hint_query_title, hint_query_desc = self.make_query_hints(export_url_items)
        return {
            'query': query,
            'search_engine': self.searchEngineType,
            'url': url,
            'title': title,
            'description': description,
            'query_title': query_title,
            'query_description': query_description,
            'urls': export_url_items,
            'hint_query_title': hint_query_title,
            'hint_query_desc': hint_query_desc
        }

    # Return hints by data string
    def get_hints(self, data: str):
        try:
            lema = self.tokenizer.lemma(data)
            vectors, tokens = self.tokenizer.vectorize([lema])

            hints = {}
            for i in range(len(tokens)):
                hints[tokens[i]] = int(vectors[0][i])
            return hints
        except:
            return {}

    # Return dict with counting including hint in hints_list items
    @staticmethod
    def sum_hints(hints_list):
        sum_hints = {}
        for hints in hints_list:
            for key in hints.keys():
                if key in sum_hints:
                    sum_hints[key] += 1
                else:
                    sum_hints[key] = 1
        return sum_hints

    # Return sorted sum of items descriptions_hints and titles_hints with tolerance 2
    @staticmethod
    def make_query_hints(export_url_items):
        query_descriptions_hints_list = []
        query_titles_hints_list = []
        for item in export_url_items:
            query_descriptions_hints_list.append(item['hint_query_desc'])
            query_titles_hints_list.append(item['hint_query_title'])

        query_descriptions_hints = MetaService.sum_hints(query_descriptions_hints_list)
        query_titles_hints = MetaService.sum_hints(query_titles_hints_list)

        query_descriptions_hints = {key: int(val) for key, val in query_descriptions_hints.items() if val > 1}
        query_titles_hints = {key: int(val) for key, val in query_titles_hints.items() if val > 1}

        query_descriptions_hints = dict(sorted(query_descriptions_hints.items(), key=lambda x: x[1], reverse=True))
        query_titles_hints = dict(sorted(query_titles_hints.items(), key=lambda x: x[1], reverse=True))

        return query_titles_hints, query_descriptions_hints

    # Return site H1
    def get_h1_by_url(self, url):
        return self.parser.get_page_details(url)

    # Make report by list
    def make_report_by_list(self, type: str = 'GOOGLE'):
        print('Получение списка для обработки')

        if type == 'FILE':
            with open(self.file_in, 'r', encoding='utf-8-sig') as f:
                data = f.read()
            queries = data.split('\n')
        else:
            sheets = GoogleSheetsApi(self.google_token)
            data = sheets.get_data_from_sheets(self.google_document_in_id, self.google_in_sheet, 'A1',
                                               'A' + str(sheets.get_list_size(self.google_document_in_id,
                                                                              self.google_in_sheet)[1]), 'ROWS')
            queries = [item for sublist in data for item in sublist]

        print('Обработка')
        export_list = []
        pool = Pool(RIVER_THREADS)
        for export_item_str in tqdm(pool.imap(self.make_str_query, queries), total=len(queries)):
            if export_item_str is not None:
                if len(export_item_str) > 0:
                    export_list.append(json.loads(export_item_str))
            else:
                break

        print('Отчет в файл ' + self.file_out)
        self.report_to_file(self.file_out, export_list)
        print('Отчет в гугл документ')
        self.report_to_google_sheets(export_list)

    # Make query by str
    def make_str_query(self, query: str):
        # It's not url
        if re.search(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$", query) \
                is None:
            try:
                query_items = self.get_content_by_key(query)
            except Exception as e:
                logger.error('Stopped query is ' + query)
                logger.error(str(e))
                return None

            # Del urls with red_sale
            urls = []
            query_titles = []
            query_descriptions = []

            for item in query_items:
                if item.url.find('redsale.by') == -1:
                    urls.append(item.url)
                    query_titles.append(item.title)
                    query_descriptions.append(item.description)

            if len(urls) >= self.min_urls:
                return json.dumps(self.get_export_query_item(query, urls, query_titles, query_descriptions))
        # It's url
        else:
            red_sale_site = self.get_h1_by_url(query)
            if len(red_sale_site.h1) != 0:
                red_sale_site.h1 = red_sale_site.h1.strip()
                try:
                    query_items = self.get_content_by_key(red_sale_site.h1)
                except Exception as e:
                    logger.error('Stopped query is ' + red_sale_site.h1 + ' url is ' + query)
                    logger.error(str(e))
                    return None

                # Del urls with red_sale
                red_sale_query_title = ''
                red_sale_query_desc = ''
                urls = []
                query_titles = []
                query_descriptions = []
                for item in query_items:
                    if item.url.find('redsale.by') == -1:
                        urls.append(item.url)
                        query_titles.append(item.title)
                        query_descriptions.append(item.description)
                    elif item.url == query:
                        red_sale_query_title = item.title
                        red_sale_query_desc = item.description

                if len(urls) >= self.min_urls:
                    return json.dumps(self.get_export_query_item(red_sale_site.h1, urls,
                                                                 query_titles, query_descriptions,
                                                                 red_sale_site.url, red_sale_site.title,
                                                                 red_sale_site.description, red_sale_query_title,
                                                                 red_sale_query_desc))
            else:
                logger.warn('Bad url: ' + query)

        return ''

    # Make report by containers
    def make_report_by_containers(self, containers):
        print('Получение списка для обработки')

        queries = []
        for container in containers:
            query = list()
            query.append(container.name)  # H1
            query.append(container.domain + container.path)  # Url
            query.append(container.title)  # Title
            query.append(container.description)  # Description
            query.append(container.domain)  # Just domain
            queries.append(query)

        if DEBUG == 'TRUE':
            queries = queries[:25]

        print('Обработка')
        export_list = []
        pool = Pool(RIVER_THREADS)
        for export_item_str in tqdm(pool.imap(self.make_container_query, queries), total=len(queries)):
            if export_item_str is not None:
                if len(export_item_str) > 0:
                    export_list.append(json.loads(export_item_str))
            else:
                break

        print('Отчет в файл ' + self.file_out)
        print('Отчет в гугл драйв')
        self.report_to_drive(export_list)
        print('Отчет в гугл документ')
        self.report_to_google_sheets(export_list)

    # Make query by container data
    def make_container_query(self, query: list):
        # Get search results
        try:
            query_items = self.get_content_by_key(query[0])
        except Exception as e:
            logger.error('Stopped query is ' + query[0])
            logger.error(str(e))
            return None

        # Del urls with red_sale
        query_title = ''
        query_desc = ''
        urls = []
        query_titles = []
        query_descriptions = []
        for item in query_items:
            # if it's not some domain add to export
            if item.url.find(query[4]) == -1:
                urls.append(item.url)
                query_titles.append(item.title)
                query_descriptions.append(item.description)
            # if it's some url mark self data
            elif item.url == query[1]:
                query_title = item.title
                query_desc = item.description

        if len(urls) >= self.min_urls:
            return json.dumps(self.get_export_query_item(query[0], urls, query_titles, query_descriptions,
                                                         query[1], query[2], query[3], query_title, query_desc))
        return ''

    # Get str hints, with self.tolerance_hint
    @staticmethod
    def get_str_hints(hints: dict, tolerance: int):
        hints = {key: int(val) for key, val in hints.items() if val > tolerance}
        return ', '.join(hints.keys())

    # Return hints without repeat with string
    def delete_not_unique_hints(self, hints: dict, string: str):
        not_unique_hints = self.get_hints(string)
        for key in not_unique_hints.keys():
            if key in hints:
                del hints[key]

        return hints

    # Export report to file
    @staticmethod
    def report_to_file(export_file, export_list):
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_list, f, ensure_ascii=False)

    # Export report to google drive (and make report to out_file)
    def report_to_drive(self, export_list):
        drive = GoogleDriveApi(self.google_token)
        self.report_to_file(self.file_out, export_list)
        current_date = str(date.today()).split('-')
        name_of_file = current_date[2] + '/' + current_date[1]+'/'+current_date[0]
        drive.upload_file(self.file_out, self.drive_folder, name_of_file)

    # Export report to google sheets
    def report_to_google_sheets(self, export_list):
        current_date = str(date.today()).split('-')
        name_of_sheet = current_date[2] + '/' + current_date[1]

        sheets = GoogleSheetsApi(self.google_token)

        header_new = [
            'domain+path',
            'name',
            'title',
            'title_len',
            'compare_title',
            'description',
            'desc_len',
            'compare_disc',
            'подсказка title',
            'подсказка desc',
            'all_query_title_hints',
            'all_query_desc_hints'
        ]

        data = []
        row = 2
        for query in export_list:
            # Hints 1+ strings
            all_query_title_hints_str = self.get_str_hints(query['hint_query_title'],
                                                           math.ceil(len(query['urls']) * self.tolerance_hint_title))
            all_query_description_hints_str = self.get_str_hints(query['hint_query_desc'],
                                                                 math.ceil(
                                                                     len(query['urls']) * self.tolerance_hint_desc))

            # Unique hints dicts
            query_title_unique_hints = self.delete_not_unique_hints(query['hint_query_title'], query['title'])
            query_esc_unique_hints = self.delete_not_unique_hints(query['hint_query_desc'], query['description'])

            # Unique hints str
            query_title_unique_hints_str = self.get_str_hints(query_title_unique_hints,
                                                              math.ceil(len(query['urls']) * self.tolerance_hint_title))
            query_desc_unique_hints_str = self.get_str_hints(query_esc_unique_hints,
                                                             math.ceil(len(query['urls']) * self.tolerance_hint_title))

            len_title = '=LEN(C' + str(row) + ')'
            len_desc = '=LEN(F' + str(row) + ')'
            if query['url'] == '':
                compare_title = ''
                compare_desc = ''
            else:
                if query['query_title'] != '' and query['query_title'].find(query['query_title']) == -1:
                    compare_title = ' false'
                elif query['query_title'] != '':
                    compare_title = ' true'
                else:
                    compare_title = ' none'

                if (query['query_description'] != '' and query['query_description'] != ' ') \
                        and query['description'][:100] != query['query_description'][:100]:
                    compare_desc = ' false'
                elif query['query_description'] != '' and query['query_description'] != ' ':
                    compare_desc = ' true'
                else:
                    compare_desc = ' none'

            data.append([
                query['url'],
                query['query'],
                query['title'],
                len_title,
                compare_title,
                query['description'],
                len_desc,
                compare_desc,
                query_title_unique_hints_str,
                query_desc_unique_hints_str,
                all_query_title_hints_str,
                all_query_description_hints_str
            ])
            row += 1
        try:
            sheets.create_sheet(self.google_document_out_id, name_of_sheet, 1 + len(data), len(header_new))
            logger.info("Created new sheet with name: " + name_of_sheet)
        except Exception as e:
            logger.info("Sheet " + name_of_sheet + " already created, recreate")
            sheets.delete_sheet(self.google_document_out_id, name_of_sheet)
            sheets.create_sheet(self.google_document_out_id, name_of_sheet, 1 + len(data), len(header_new))

        sheets.put_row_to_sheets(self.google_document_out_id, name_of_sheet, 1, 'A', header_new)
        sheets.put_data_to_sheets(self.google_document_out_id, name_of_sheet,
                                  'A2', 'P' + str(2 + len(data)), 'ROWS', data)

        # Title len rules
        sheets.add_colorizing_conditional_formatting(self.google_document_out_id, name_of_sheet,
                                                     4, 2, 4, 2 + len(data), RED_COLORIZING, 'NUMBER_GREATER', '56')
        sheets.add_colorizing_conditional_formatting(self.google_document_out_id, name_of_sheet,
                                                     4, 2, 4, 2 + len(data), GREEN_COLORIZING, 'NUMBER_LESS', '57')
        # Descriptions len rules
        sheets.add_colorizing_conditional_formatting(self.google_document_out_id, name_of_sheet,
                                                     7, 2, 7, 2 + len(data), RED_COLORIZING, 'NUMBER_GREATER', '155')
        sheets.add_colorizing_conditional_formatting(self.google_document_out_id, name_of_sheet,
                                                     7, 2, 7, 2 + len(data), GREEN_COLORIZING, 'NUMBER_LESS', '156')
