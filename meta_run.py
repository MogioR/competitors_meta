import os
import json
from Modules.meta_service import MetaService

CONFIG_FILE_PATH = 'Environment/config.json'
# FILE/GOOGLE
OUTPUT_TYPE = 'GOOGLE'    # FILE - импорт из файла в папке, GOOGLE - импорт из Google Sheets
GOOGLE_SHEETS_IN = '1Ad1Az4pfaiaFwVix6btz2bQaJdlfDLzDJhrnCFB7qZg'   # Файл откуда берем инфу
GOOGLE_SHEETS_OUT = '129cmECaDj0FlNif52_0QtTJogbLzDYSv_JeS2Wk5XyM'  # Файл, куда заливаем инфу
SEARCH_ENGINE = 'GOOGLE'   # GOOGLE - гугл, YANDEX - яндекс
SEARCH_REGION = 'MINSK'    # MINSK - Минск, MOSCOW - Москва, KIEV - Киев
SEARCH_DEVICE = 'MOBILE'   # MOBILE - телефон, DESKTOP - компьютер, TABLET - планшет

MIN_URLS = 6                        # Минимум допущеных url
DESCRIPTION_HINT_TOLERANCE = 0.5    # 0.5 == 50%
TITLE_HINT_TOLERANCE = 0.5          # 0.5 == 50%

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

if os.getenv("GOOGLE_API_TOKEN") is not None:
    with open(config['GoogleSheets']['token'], 'w') as f:
        f.write(os.getenv("GOOGLE_API_TOKEN"))

service = MetaService(config)
print(service.get_xml_report('Оцифровка аудиокассет в Минске'))
# service.make_report(type=OUTPUT_TYPE)
