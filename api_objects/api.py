import json
import os
import pickle
from typing import Dict

import requests
from requests.exceptions import ConnectionError

from .config import RCMS_BASIC_CREDENTIALS, RCMS_REDSALE_MAIN_ENDPOINT_PRIVATE


PATH_SAVE = os.path.dirname(os.path.realpath(__file__))

class PageEnd(Exception):
    pass

class ErrorGet(Exception):
    def __init__(self, status_code:int, text:str) -> None:
        self.status_code = status_code
        self.text = text
        super().__init__(text)
    
    def __str__(self) -> str:
        return f'{self.status_code} -> {self.text}'

class Api:
    def __init__(self, url, **kwargs) -> None:
        self.params:dict = {
            'page':0,
            'size':100,
            'direction':'DESC'
        }
        self.params.update(kwargs)
        self.url = f'{RCMS_REDSALE_MAIN_ENDPOINT_PRIVATE}{url}'
    
    def get(self, i_page:int = 0) -> bool:
        self.params['page'] = i_page
        result = requests.get(self.url, params = self.params, headers={'Authorization':RCMS_BASIC_CREDENTIALS})
        if result.status_code != 200: raise ErrorGet(result.status_code, result.text)
        result = result.json() 
        return result["content"], result['pageNumber'] >= result['totalPages']

    def post(self, data) -> dict:
        result = requests.post(self.url, json=data, headers={'Authorization':RCMS_BASIC_CREDENTIALS})
        if result.status_code != 200: raise ErrorGet(result.status_code, result.text)
        return result.json() 

class BaseElement:
    def __init__(self, id:str) -> None:
        self.id = id
    
    def __eq__(self, o: object) -> bool:
        return isinstance(o, BaseElement) and self.id == o.id

    def __hash__(self) -> int:
        return hash(self.id)

class Base:
    __filename__ = 'не задано'

    def __init__(self, name:str = '') -> None:
        self.name:str = f'_{name}' if name else ''
        self.ids:Dict[str, BaseElement] = dict()

    def add(self, o:BaseElement):
        self.ids.update({o.id:o})

    @property
    def filename(self) -> str:
        return f'{PATH_SAVE}/{self.__filename__}{self.name}.pickle'

    def save(self):
        with open(self.filename, 'wb') as f:
            pickle.dump(self, f)

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                r = pickle.load(f)
                self.__dict__.update(r.__dict__)

class ApiBase(Base):
    __url__ = 'не задано'
    __params__ = dict()

    def collect(self, page_max:int = 5, **kwargs)->None:
        '''
        Собирает с api данные, page_max - страница до которой нужно получить данные
        '''
        api = Api(self.__url__, **kwargs)
        for i_page in range(page_max):
            try:
                result, mode_finish = api.get(i_page)
                for data in result:
                    try:
                        self.add(**data)
                    except TypeError as e:
                        print("Type error", e)
                        raise #break
                    except Exception as e:
                        print(e, data)
                        raise #break
                if mode_finish: 
                    if i_page:print('Страницы кончились', i_page)
                    break
            except ConnectionError:
                print('ConnectionError...')
            except ErrorGet as e:
                print('Error get', e, i_page, str(kwargs))
                raise
