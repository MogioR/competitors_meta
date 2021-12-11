import asyncio
import json
import os
import pickle
from typing import Dict
from aiohttp.helpers import NO_EXTENSIONS

import requests
from aiohttp import ClientResponseError, ClientSession
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
		return result

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

	def add(self, **kwargs):
		o = BaseElement()
		self.ids.update({o.id:o})

	@property
	def filename(self) -> str:
		return f'{PATH_SAVE}/{self.__filename__}{self.name}.pickle'

	def get_path(self, path) ->str:
		path = path or PATH_SAVE
		return f'{path}/{self.__filename__}{self.name}.pickle'

	def save(self, path = None):
		with open(self.get_path(path), 'wb') as f:
			pickle.dump(self, f)

	def load(self, path = None):
		path = self.get_path(path)
		if os.path.exists(path):
			with open(path, 'rb') as f:
				r = pickle.load(f)
				self.__dict__.update(r.__dict__)

class ApiBase(Base):
	__url__ = 'не задано'

	def collect_one(self, **kwargs) -> None:
		url = f'{RCMS_REDSALE_MAIN_ENDPOINT_PRIVATE}{self.__url__}'
		data = requests.get(url, kwargs, headers={'Authorization':RCMS_BASIC_CREDENTIALS}).json()
		self.add(**data)

	def collect(self, page_max:int = 5, **kwargs)->None:
		'''
		Собирает с api данные, page_max - страница до которой нужно получить данные
		'''
		api = Api(self.__url__, **kwargs)
		result = api.get(0)
		for data in result["content"]:
			self.add(**data)
		if page_max > result['totalPages']: 
			page_max = result['totalPages']
		for i_page in range(1, page_max):
			try:
				result = api.get(i_page)
				for data in result["content"]:
					self.add(**data)
			except ConnectionError:
				print('ConnectionError...')
			except ErrorGet as e:
				print('Error get', e, i_page, str(kwargs))
				raise
	
	async def get_api(self, session, url, params):
		async with session.get(url, params=params) as resp:
			res = await resp.json()
		content = res.get('content')
		if content is None:
			print('error:', res)
			return 0, 0
		for data in content:
			try:
				self.add(**data)
			except Exception as e:
				print(e, data)
		return res["totalPages"], res['totalElements']

	async def collect2(self, page_max:int=5, **kwargs) -> None:
		url = f'{RCMS_REDSALE_MAIN_ENDPOINT_PRIVATE}{self.__url__}'
		tasks = []
		params = {'page':0, 'size':100}
		params.update(kwargs)
		async with ClientSession(headers = {'Authorization':RCMS_BASIC_CREDENTIALS}) as session:
			page_all_max, elements_max = await self.get_api(session, url, params=params)
			if page_max > page_all_max: page_max = page_all_max
			for i_page_max in range(1, page_max, 3):
				for i_page in range(i_page_max, i_page_max + 3):
					params.update({'page':i_page})
					tasks.append(asyncio.create_task(self.get_api(session, url, params=params.copy())))
				await asyncio.gather(*tasks)
				tasks.clear()
		return elements_max
	
	async def collect3(self, base_elements:list, **kwargs) -> None:
		s = len(base_elements)
		async def get_one(params):
			async with session.get(url, params=params) as resp:
				res = await resp.json()
			if res.get('skillId') is None:
				print('get_one', res)
			else:
				self.add(**res)
		url = f'{RCMS_REDSALE_MAIN_ENDPOINT_PRIVATE}{self.__url__}'
		tasks = []
		params = kwargs
		async with ClientSession(headers = {'Authorization':RCMS_BASIC_CREDENTIALS}) as session:
			while 1:
				try:
					for _ in range(2):
						params.update(base_elements.pop(0))
						tasks.append(asyncio.create_task(get_one(params = params.copy())))
				except IndexError:
					break
				finally:
					await asyncio.gather(*tasks)
					tasks.clear()
		return s
	
	async def collect4(self, base_elements:list, **kwargs) -> None:
		work_queue = asyncio.Queue()
		s = len(base_elements)
		for element in base_elements:
			work_queue.put_nowait(element)

		async def get_elements():
			while not work_queue.empty():
				container_id = await work_queue.get()
				params = {'page':0, 'size':100, 'containerId':container_id}
				page_max, _ = await self.get_api(session, url, params)
				for page in range(1, page_max):
					params['page'] = page
					await self.get_api(session, url, params)
				work_queue.task_done()

		url = f'{RCMS_REDSALE_MAIN_ENDPOINT_PRIVATE}{self.__url__}'
		tasks = []
		params = kwargs
		async with ClientSession(headers = {'Authorization':RCMS_BASIC_CREDENTIALS}) as session:
			await asyncio.gather(
				asyncio.create_task(get_elements()),
				asyncio.create_task(get_elements()),
				asyncio.create_task(get_elements()),
			)
		return s