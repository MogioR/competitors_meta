import math
import re
import json
from datetime import date
from concurrent.futures.thread import ThreadPoolExecutor

import numpy as np
from bs4 import BeautifulSoup
from tqdm import tqdm

from Modules.Logger.logger import get_logger
from Modules.Xml_river import GoogleXmlRiver
from Modules.Xml_river import YandexXmlRiver
from Modules.natasha_tokenizer import NatashaTokenizer
from Modules.google_sheets_api import GoogleSheetsApi
from Modules.request_scraper import RequestsScraper

logger = get_logger(__name__)

# Maximum url in query
BROWSER_POOL_SIZE = 10
# Colors for formatting rules in google sheets
RED_COLORIZING = [230 / 255, 184 / 255, 175 / 255]
GREEN_COLORIZING = [217 / 255, 234 / 255, 211 / 255]


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

        self.tolerance_hint_title = config['Main']['default_title_tolerance_hint']
        self.tolerance_hint_desc = config['Main']['default_description_tolerance_hint']
        self.min_urls = config['Main']['default_minimum_urls']

        self.file_in = config['Main']['default_input_file']
        self.file_out = config['Main']['output_json_path']

        self.google_token = config['GoogleSheets']['token']
        self.google_document_in_id = config['GoogleSheets']['document_in_id']
        self.google_in_sheet = config['GoogleSheets']['input_sheet_name']
        self.google_document_out_id = config['GoogleSheets']['document_out_id']

        self.tokenizer = NatashaTokenizer()
        self.parser = RequestsScraper()

    def __del__(self):
        pass

    # Return xml_report from query
    def get_xml_report(self, query):
        errors = ''
        report = ''
        for i in range(3):
            report = self.searchEngine.get_search_results(query)
            errors = BeautifulSoup(report, 'lxml')
            if errors.yandexsearch.response.error is not None:
                pass
            else:
                break

        if errors.yandexsearch.response.error is not None:
            raise Exception('Xml river error: ', errors.yandexsearch.response.error.string)
        return report

    # Return urls from xml_report
    @staticmethod
    def get_content_by_get_xml_report(xml_report):
        soup = BeautifulSoup(xml_report, "html.parser")
        docs = soup.findAll('doc')

        query_urls = []
        query_titles = []
        query_descriptions = []

        for doc in docs:
            query_urls.append(doc.url.text)
            title = doc.title.text.replace('![CDATA[', '')
            title = title.replace(']]', '')
            title = title.replace('\xa0', '')
            query_titles.append(title)
            desc = doc.passages.passage.text.replace('![CDATA[', '')
            desc = desc.replace(']]', '')
            desc = desc.replace('\xa0', '')
            query_descriptions.append(desc)

        return query_urls, query_titles, query_descriptions

    # Return titles and descriptions from urls
    def get_meta_by_urls(self, urls):
        titles = []
        descriptions = []
        results = []
        try:
            with ThreadPoolExecutor(BROWSER_POOL_SIZE) as executor:
                for current_progress, result in enumerate(executor.map(self.parser.get_page_details, urls)):
                    results.append(result)
                    logger.info("Received source of: {0}".format(urls[current_progress]))

            for result in results:
                titles.append(result.title)
                descriptions.append(result.description)

        except Exception as e:
            logger.error(e)

        return titles, descriptions

    # Return url item for export
    def get_export_url_item(self, url: str, title: str, description: str, query_title: str, query_description: str):
        return {'url': url, 'title': title, 'description': description,
                'query_title': query_title, 'query_desc': query_description, 'hint_title': self.get_hints(title),
                'hint_desc': self.get_hints(description), 'hint_query_title': self.get_hints(query_title),
                'hint_query_desc': self.get_hints(query_description)}

    # Return query item for export
    def get_export_query_item(self, query: str, urls: list, titles: list, descriptions: list,
                              query_titles: list, query_descriptions: list,
                              url='', title='', description='', query_title='', query_description=''):
        # Gen url items
        export_url_items = []
        for i in range(len(urls)):
            export_url_items.append(self.get_export_url_item(urls[i], titles[i], descriptions[i], query_titles[i],
                                                             query_descriptions[i]))

        # Gen hints
        hint_title, hint_desc, hint_query_title, hint_query_desc = self.make_query_hints(export_url_items)
        return {'query': query, 'search_engine': self.searchEngineType, 'url': url,
                'title': title, 'description': description, 'query_title': query_title,
                'query_description': query_description, 'urls': export_url_items,
                'hint_title': hint_title, 'hint_desc': hint_desc, 'hint_query_title': hint_query_title,
                'hint_query_desc': hint_query_desc}

    # Return hints by data string
    def get_hints(self, data: str):
        try:
            lema = self.tokenizer.lemma(data)
            vectors, tokens = self.tokenizer.vectorize([lema])

            hints = {}
            for i in range(len(tokens)):
                hints[tokens[i]] = vectors[0][i]
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
        descriptions_hints_list = []
        titles_hints_list = []
        query_descriptions_hints_list = []
        query_titles_hints_list = []
        for item in export_url_items:
            descriptions_hints_list.append(item['hint_desc'])
            titles_hints_list.append(item['hint_title'])
            query_descriptions_hints_list.append(item['hint_query_desc'])
            query_titles_hints_list.append(item['hint_query_title'])

        descriptions_hints = MetaService.sum_hints(descriptions_hints_list)
        titles_hints = MetaService.sum_hints(titles_hints_list)
        query_descriptions_hints = MetaService.sum_hints(query_descriptions_hints_list)
        query_titles_hints = MetaService.sum_hints(query_titles_hints_list)

        descriptions_hints = {key: int(val) for key, val in descriptions_hints.items() if val > 1}
        titles_hints = {key: int(val) for key, val in titles_hints.items() if val > 1}
        query_descriptions_hints = {key: int(val) for key, val in query_descriptions_hints.items() if val > 1}
        query_titles_hints = {key: int(val) for key, val in query_titles_hints.items() if val > 1}

        sorted_descriptions_hints = dict(sorted(descriptions_hints.items(), key=lambda x: x[1], reverse=True))
        sorted_titles_hints = dict(sorted(titles_hints.items(), key=lambda x: x[1], reverse=True))
        query_descriptions_hints = dict(sorted(query_descriptions_hints.items(), key=lambda x: x[1], reverse=True))
        query_titles_hints = dict(sorted(query_titles_hints.items(), key=lambda x: x[1], reverse=True))

        return sorted_titles_hints, sorted_descriptions_hints, query_titles_hints, query_descriptions_hints

    # Return site H1
    def get_h1_by_url(self, url):
        return self.parser.get_page_details(url)

    # Make report
    def make_report(self, type='GOOGLE'):
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
        for i, query in enumerate(tqdm(queries)):
            # Если это не ссылка
            if re.search(r"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$", query) \
                    is None:
                try:
                    results = self.get_xml_report(query)
                except Exception as e:
                    print(e)
                    print('Stopped in: ', i, ' Query is ', query)
                    break

                urls, query_titles, query_descriptions = self.get_content_by_get_xml_report(results)

                # Del urls with red_sale
                urls_new = []
                query_titles_new = []
                query_descriptions_new = []
                for i in range(len(urls)):
                    if urls[i].find('redsale.by') == -1:
                        urls_new.append(urls[i])
                        query_titles_new.append(query_titles[i])
                        query_descriptions_new.append(query_descriptions[i])

                titles, descriptions = self.get_meta_by_urls(urls_new)
                if len(urls_new) >= self.min_urls:
                    export_list.append(self.get_export_query_item(query, urls_new, titles, descriptions,
                                                                  query_titles_new, query_descriptions_new))
            else:
                red_sale_site = self.get_h1_by_url(query)
                if len(red_sale_site.h1) != 0:
                    red_sale_site.h1 = red_sale_site.h1.strip()
                    try:
                        results = self.get_xml_report(red_sale_site.h1)
                    except Exception as e:
                        print(e)
                        print('Stopped in: ', i, ' Query is ', red_sale_site.h1)
                        break

                    urls, query_titles, query_descriptions = self.get_content_by_get_xml_report(results)

                    # Del urls with red_sale
                    redsale_query_title = ''
                    redsale_query_desc = ''

                    urls_new = []
                    query_titles_new = []
                    query_descriptions_new = []
                    for i in range(len(urls)):
                        if urls[i].find('redsale.by') == -1:
                            urls_new.append(urls[i])
                            query_titles_new.append(query_titles[i])
                            query_descriptions_new.append(query_descriptions[i])
                        elif urls[i] == query:
                            redsale_query_title = query_titles[i]
                            redsale_query_desc = query_descriptions[i]

                            # redsale_query_title = re.sub(r' –[A-Za-z. ]{0,}$', '', query_titles[i])

                    titles, descriptions = self.get_meta_by_urls(urls_new)
                    if len(urls_new) >= self.min_urls:
                        export_list.append(self.get_export_query_item(red_sale_site.h1, urls_new, titles, descriptions,
                                                                      query_titles_new, query_descriptions_new,
                                                                      red_sale_site.url, red_sale_site.title,
                                                                      red_sale_site.description, redsale_query_title,
                                                                      redsale_query_desc))
                else:
                    print('Bad url: ', query)

        print('Отчет в файл ' + self.file_out)
        self.report_to_file(self.file_out, export_list)
        print('Отчет в гугл документ')
        self.report_to_google_sheets(export_list)

    # Export report to file
    @staticmethod
    def report_to_file(export_file, export_list):
        class NpEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super(NpEncoder, self).default(obj)

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_list, f, ensure_ascii=False, cls=NpEncoder)

    # Get str hints, with self.tolerance_hint
    @staticmethod
    def get_str_hints(hints: dict, tolerance: int):
        hints = {key: int(val) for key, val in hints.items() if val > tolerance}
        return ', '.join(hints.keys())

    # Get average len of items urls_items[key] without zero elements
    @staticmethod
    def get_average_len(urls_items, key: str):
        all_len = 0.0
        cont = 0
        for url in urls_items:
            len_ = len(url[key])
            if len_ != 0:
                cont += 1
                all_len += len_

        return all_len / cont

    # Return hints without repeat with string
    def delete_not_unique_hints(self, hints: dict, string: str):
        not_unique_hints = self.get_hints(string)
        for key in not_unique_hints.keys():
            if key in hints:
                del hints[key]

        return hints

    # Export report to google sheets
    def report_to_google_sheets(self, export_list):
        current_date = str(date.today()).split('-')
        name_of_sheet = current_date[2] + '/' + current_date[1]

        sheets = GoogleSheetsApi(self.google_token)

        header_new = [
            'domain+path', 'name', 'title', 'title_len', 'compare_title', 'description', 'desc_len', 'compare_disc',
            'query_title_hints', 'query_desc_hints', 'title_hints', 'desc_hints', 'all_query_title_hints',
            'all_query_desc_hints', 'all_title_hints', 'all_desc_hints'
        ]

        data = []
        row = 2
        for query in export_list:
            all_title_hints_str = self.get_str_hints(query['hint_title'],
                                                     math.ceil(len(query['urls']) * self.tolerance_hint_title))
            all_description_hints_str = self.get_str_hints(query['hint_desc'],
                                                           math.ceil(len(query['urls']) * self.tolerance_hint_desc))

            all_query_title_hints_str = self.get_str_hints(query['hint_query_title'],
                                                           math.ceil(len(query['urls']) * self.tolerance_hint_title))
            all_query_description_hints_str = self.get_str_hints(query['hint_query_desc'],
                                                           math.ceil(len(query['urls']) * self.tolerance_hint_desc))

            title_unique_hints = self.delete_not_unique_hints(query['hint_title'], query['title'])
            desc_unique_hints = self.delete_not_unique_hints(query['hint_desc'], query['description'])
            query_title_unique_hints = self.delete_not_unique_hints(query['hint_query_title'], query['title'])
            query_esc_unique_hints = self.delete_not_unique_hints(query['hint_query_desc'], query['description'])

            title_unique_hints_str = self.get_str_hints(title_unique_hints, self.tolerance_hint_title)
            desc_unique_hints_str = self.get_str_hints(desc_unique_hints, self.tolerance_hint_desc)
            query_title_unique_hints_str = self.get_str_hints(query_title_unique_hints, self.tolerance_hint_title)
            query_desc_unique_hints_str = self.get_str_hints(query_esc_unique_hints, self.tolerance_hint_desc)

            if query['url'] == '':
                data.append([query['url'], query['query'], query['title'], '=LEN(C' + str(row) + ')',
                             '', query['description'], '=LEN(F' + str(row) + ')', '',
                             query_title_unique_hints_str, query_desc_unique_hints_str, title_unique_hints_str,
                             desc_unique_hints_str, '', '', '', ''])
            else:
                data.append([query['url'], query['query'], query['title'], '=LEN(C' + str(row) + ')',
                             str(query['title'] == query['query_title']), query['description'],
                             '=LEN(F' + str(row) + ')',
                             str(query['description'][:100] == query['query_description'][:100]),
                             query_title_unique_hints_str, query_desc_unique_hints_str, title_unique_hints_str,
                             desc_unique_hints_str, all_query_title_hints_str, all_query_description_hints_str,
                             all_title_hints_str, all_description_hints_str])
            row += 1
        try:
            sheets.create_sheet(self.google_document_out_id, name_of_sheet, 1 + len(data), len(header_new))
            logger.info("Created new sheet with name: " + name_of_sheet)
        except:
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
