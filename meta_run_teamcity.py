import os
import sys
import json
from Modules.meta_service import MetaService

# Fix containers
API_PATH = os.getenv("API_PATH")
if API_PATH is None or API_PATH == '':
    API_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(str(API_PATH))
CONFIG_FILE_PATH = 'Environment/config.json'
print('Api path:', API_PATH)
from api_objects.container import BaseContainer

# FILE/GOOGLE/BASE_CONTAINER
# FILE - импорт из файла в папке, GOOGLE - импорт из Google Sheets, BASE_CONTAINER - из base_container.pickle
INPUT_TYPE = os.getenv("INPUT_TYPE")
GOOGLE_SHEETS_IN = os.getenv("GOOGLE_SHEETS_IN")    # Файл откуда берем инфу
GOOGLE_SHEETS_OUT = os.getenv("GOOGLE_SHEETS_OUT")  # Файл, куда заливаем инфу
SEARCH_ENGINE = os.getenv("SEARCH_ENGINE")          # GOOGLE - гугл, YANDEX - яндекс
SEARCH_REGION = os.getenv("SEARCH_REGION")          # MINSK - Минск, MOSCOW - Москва, KIEV - Киев
SEARCH_DEVICE = os.getenv("SEARCH_DEVICE")          # MOBILE - телефон, DESKTOP - компьютер, TABLET - планшет

MIN_URLS = int(os.getenv("MINIMUM_URLS"))                                      # Минимум допущеных url
DESCRIPTION_HINT_TOLERANCE = float(os.getenv("DESCRIPTION_HINT_TOLERANCE"))    # 0.5 == 50%
TITLE_HINT_TOLERANCE = float(os.getenv("TITLE_HINT_TOLERANCE"))                # 0.5 == 50%

with open(CONFIG_FILE_PATH, 'r') as f:
    config = json.load(f)

config['Main']['default_search_engine'] = SEARCH_ENGINE
config['Main']['default_region'] = SEARCH_REGION
config['Main']['default_title_tolerance_hint'] = TITLE_HINT_TOLERANCE
config['Main']['default_description_tolerance_hint'] = DESCRIPTION_HINT_TOLERANCE
config['Main']['default_minimum_urls'] = MIN_URLS

config['GoogleSheets']['document_in_id'] = GOOGLE_SHEETS_IN
config['GoogleSheets']['document_out_id'] = GOOGLE_SHEETS_OUT

config['XMLRiver']['Google']['default_device'] = SEARCH_DEVICE.lower()
config['XMLRiver']['Yandex']['default_device'] = SEARCH_DEVICE.lower()

config['XMLRiver']['xml_river_user'] = os.getenv("XMLRIVER_USER")
config['XMLRiver']['xml_river_key'] = os.getenv("XMLRIVER_TOKEN")

if os.getenv("GOOGLE_API_TOKEN") is not None:
    with open(config['GoogleSheets']['token'], 'w') as f:
        f.write(os.getenv("GOOGLE_API_TOKEN"))


service = MetaService(config)
if INPUT_TYPE == 'BASE_CONTAINER':
    base_container = BaseContainer()
    base_container.load()
    base_containers = base_container.get_containers(None, False)
    service.make_report_by_containers(base_containers)
else:
    service.make_report_by_list(type=INPUT_TYPE)