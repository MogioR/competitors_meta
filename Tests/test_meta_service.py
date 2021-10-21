import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from Modules.meta_service import MetaService
from Modules.Xml_river import GoogleXmlRiver
from Modules.Xml_river import YandexXmlRiver
from Modules.natasha_tokenizer import NatashaTokenizer

CONFIGS = [
{
    "Main": {
        "default_search_engine": "GOOGLE",
        "default_region": "MINSK",
        "output_json_path": "export.json",
        "default_input_file": "queries.txt",
        "default_title_tolerance_hint": 0.5,
        "default_description_tolerance_hint": 0.5,
        "default_minimum_urls": 6
    },
    "GoogleSheets": {
        "token": "",
        "document_in_id": "",
        "input_sheet_name": "",
        "document_out_id": ""
    },
    "XMLRiver": {
        "xml_river_user": "",
        "xml_river_key": "",
        "group_by": 10,
        "Google": {
            "default_country_id": 2112,
            "default_loc_id": 1001493,
            "default_language_id": "RU",
            "default_device": "desktop",
            "default_use_language": False
        },
        "Yandex": {
            "default_loc_id": 4,
            "default_language_id": "ru",
            "default_device": "desktop",
            "default_use_language": False
        }
    }
},
{
    "Main": {
        "default_search_engine": "YANDEX",
        "default_region": "MINSK",
        "output_json_path": "export.json",
        "default_input_file": "queries.txt",
        "default_title_tolerance_hint": 0.5,
        "default_description_tolerance_hint": 0.5,
        "default_minimum_urls": 6
    },
    "GoogleSheets": {
        "token": "",
        "document_in_id": "",
        "input_sheet_name": "",
        "document_out_id": ""
    },
    "XMLRiver": {
        "xml_river_user": "",
        "xml_river_key": "",
        "group_by": 10,
        "Google": {
            "default_country_id": 2112,
            "default_loc_id": 1001493,
            "default_language_id": "RU",
            "default_device": "desktop",
            "default_use_language": False
        },
        "Yandex": {
            "default_loc_id": 4,
            "default_language_id": "ru",
            "default_device": "desktop",
            "default_use_language": False
        }
    }
}
]


def test_competitors_meta_service():
    for config in CONFIGS:
        service = MetaService(config)

        assert type(service.searchEngineType) is str
        if config['Main']['default_search_engine'] == 'GOOGLE':
            assert type(service.searchEngine) is GoogleXmlRiver
            assert service.searchEngineType == 'GOOGLE'
        elif config['Main']['default_search_engine'] == 'YANDEX':
            assert type(service.searchEngine) is YandexXmlRiver
            assert service.searchEngineType == 'YANDEX'

        assert type(service.tolerance_hint_title) is float
        assert service.tolerance_hint_title == config['Main']['default_title_tolerance_hint']
        assert type(service.tolerance_hint_desc) is float
        assert service.tolerance_hint_desc == config['Main']['default_description_tolerance_hint']
        assert type(service.min_urls) is int
        assert service.min_urls == config['Main']['default_minimum_urls']

        assert type(service.file_in) is str
        assert service.file_in == config['Main']['default_input_file']
        assert type(service.file_out) is str
        assert service.file_out == config['Main']['output_json_path']

        assert type(service.google_token) is str
        assert service.google_token == config['GoogleSheets']['token']
        assert type(service.google_document_out_id) is str
        assert service.google_document_out_id == config['GoogleSheets']['document_out_id']
        assert type(service.google_document_in_id) is str
        assert service.google_document_in_id == config['GoogleSheets']['document_in_id']
        assert type(service.google_in_sheet) is str
        assert service.google_in_sheet == config['GoogleSheets']['input_sheet_name']

        assert type(service.tokenizer) is NatashaTokenizer

        del service


class TestCompetitorsMetaService:
    @classmethod
    def setup_class(cls):
        cls.test_service = MetaService(CONFIGS[0])

    def test_get_urls_by_get_xml_report(self):
        xml_report = '<?xml version="1.0"><yandexsearch version="1.0"><response date="20211014T173320">' \
                     '<url>url1</url>https://www.mebelminsk.by/categories/remont-mebeli<url>url2</url>'

        assert self.test_service.get_urls_by_get_xml_report(xml_report) == ['url1', 'url2']

    def test_get_export_url_item(self):
        assert self.test_service.get_export_url_item('url', 'Some title', 'Some description') ==\
               {'url': 'url', 'title': 'Some title', 'description': 'Some description',
                'hint_title': self.test_service.get_hints('Some title'),
                'hint_desc': self.test_service.get_hints('Some description')}

    def test_export_query_item(self):
        url_item_1 = self.test_service.get_export_url_item('url1', 'title one', 'disc1')
        url_item_2 = self.test_service.get_export_url_item('url2', 'title two', '')
        hint_title, hint_desc = self.test_service.make_query_hints([url_item_1, url_item_2])
        export_query_1 = {
            'query': 'query',
            'search_engine': self.test_service.searchEngineType,
            'query_url': '',
            'query_title': '',
            'query_description': '',
            'urls': [url_item_1, url_item_2],
            'hint_title': hint_title,
            'hint_desc': hint_desc}

        export_query_2 = {
            'query': 'query',
            'search_engine': self.test_service.searchEngineType,
            'query_url': 'url',
            'query_title': 'title',
            'query_description': 'description',
            'urls': [url_item_1, url_item_2],
            'hint_title': hint_title,
            'hint_desc': hint_desc}

        assert self.test_service.get_export_query_item('query', ['url1', 'url2'], ['title one', 'title two'],
                                                       ['disc1', '']) == export_query_1
        assert self.test_service.get_export_query_item('query', ['url1', 'url2'], ['title one', 'title two'],
                                                       ['disc1', ''], 'url', 'title', 'description') == export_query_2

    def test_get_hints(self):
        title = 'Шла Саша по шоссе и купила сушку. Сушки купить. Шоссе до Красноярска'
        assert self.test_service.get_hints(title) == \
        {'идти': 1, 'красноярск': 1, 'купить': 2, 'саша': 1, 'сушка': 2, 'шоссе': 2}

    def test_make_query_hints(self):
        url_item_1 = self.test_service.get_export_url_item('url1', 'title one one one', 'disc disc')
        url_item_2 = self.test_service.get_export_url_item('url2', 'title two', 'disc selenium selenium')
        export_items = [url_item_1, url_item_2]

        sorted_titles_hints, sorted_descriptions_hints = self.test_service.make_query_hints(export_items)

        assert sorted_titles_hints == {'title': 2}
        assert sorted_descriptions_hints == {'disc': 2}

    def test_get_str_hints(self):
        hints = {"сантехник": 17, "минск": 9, "услуга": 9, "цена": 5, "дом": 5, "работа": 5, "сантехника": 4,
                 "сантехнический": 4, "вызов": 3, "заказать": 3, "низкий": 3, "by": 3, "выезд": 2, "спектр": 2,
                 "профессионал": 2, "мастер": 2, "любой": 2, "слесарь": 2}

        assert self.test_service.get_str_hints(hints, 4) == "сантехник, минск, услуга, цена, дом, работа"

    def test_get_average_len(self):
        url_item_1 = self.test_service.get_export_url_item('url1', 'title one', 'disc1')
        url_item_2 = self.test_service.get_export_url_item('url2', 'title t', '')
        url_item_3 = self.test_service.get_export_url_item('url2', '', '')
        items = [url_item_1, url_item_2, url_item_3]
        assert self.test_service.get_average_len(items, 'title') == 8.0

    def delete_not_unique_hints(self):
        hints = {"сантехник": 17, "минск": 9, "услуга": 9, "цена": 5, "дом": 5, "работа": 5}

        some_original_title = 'сантехник предлагает услуги в городе минск'

        assert self.test_service.delete_not_unique_hints(hints, some_original_title) == {'цена': 5, 'дом': 5,
                                                                                         'работа': 5}
