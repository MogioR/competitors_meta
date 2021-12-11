from collections import defaultdict
from datetime import datetime
from typing import DefaultDict, Dict, List, Set

from .api import ApiBase, BaseElement
from .skill import Skill, base_skill
from .utils import reversed_dict_values

__all__ = ['BaseOrder', 'Order']

import re

IGNORE_KEYS = (
	'Место выполнения работы',
	'Место ремонта',
	'Место занятий',
	'Адрес',
	'Дата'
)

PRICE_KEYS = set(
	('цена', 'стоимость')
)

class Params:
	def __init__(self, description:str, value:str = '') -> None:
		self.description = description
		self.value = value

	def __repr__(self) -> str:
		return f'{self.description}:{self.value}'

	@classmethod
	def process(cls, details):
		result:List[Params] = list()
		for detail in details:
			new_params = Params(**detail)
			if not new_params.value or new_params.description in IGNORE_KEYS: continue
			#if re.findall('[А-Я]{3,}', new_params.value): return ()
			result.append(new_params)
		return result

def find_price(params:List[Params]):
	for param in params:
		if PRICE_KEYS.intersection(param.description.split()):
			params.remove(param)
			return re.findall('[0-9]{1,}', param.value)
	return ()

class Order(BaseElement):
	def __init__(self, orderId, number, createdAt:str, params:List[Params], details, price:str = None, completionAt:str = None, **kwargs) -> None:
		super().__init__(id = orderId)
		self.number:str = number
		self.price:str = price
		self.created_at:datetime = datetime.fromisoformat(createdAt.replace('Z','+00:00'))
		self.completion_at:datetime = datetime.fromisoformat(completionAt.replace('Z','+00:00')) if completionAt else None

		self.params:List[Params] = params
		self.details = details
		self.user_price = find_price(self.params)
		
		self.other_params = kwargs
	
	def __repr__(self) -> str:
		return self.id

class BaseOrder(ApiBase):
	'''
	Хранилище заказов по id
	'''
	__filename__ = 'base_order'
	__url__ = '/private/orders'

	def __init__(self, name:str = '') -> None:
		super().__init__(name = name)
		self.ids:Dict[str, Order] = dict()
		self.container_ids:DefaultDict[str, Set[Order]] = defaultdict(set)
		self.skill_orders:DefaultDict[Skill, Set[Order]] = defaultdict(set)
		self.locations:DefaultDict[str, Set[Order]] = defaultdict(set)
		
		self.hiddens:Set[Order] = set()
		self.status_open:Set[Order] = set()

		self.count_add = 0
		self.count_add_dublicate = 0
	   
	def get(self, id:str) -> Order:
		return self.ids.get(id)

	def add(self, skillId:str, status:str, hidden:bool, details:list = None, location:str = None, containerId:str = None, **kwargs):
		if not details: return 
		self.count_add += 1
		if details is None: details = ()
		params = Params.process(details)
		#if len(params) < 2: return 
		order_new = Order(params = params, details = details, **kwargs)
		if order_new.id in self.ids:self.count_add_dublicate += 1
		self.ids.update({order_new.id:order_new})
		self.container_ids[containerId].add(order_new)
		self.skill_orders[base_skill.get_or_create(skillId)].add(order_new)
		self.locations[location].add(order_new)

		if hidden:self.hiddens.add(order_new)
		if status == 'OPEN':self.status_open.add(order_new)

	def get_order_location(self) -> Dict[Order, str]:
		return reversed_dict_values(self.locations)
	
	def get_order_skill(self) -> Dict[Order, Skill]:
		return reversed_dict_values(self.skill_orders)
	
def convert_base_old_base_new():
	def get_iso_time(d):
		if d is None: return None
		return d.isoformat()

	base_order = BaseOrder()
	base_order.load()
	base_order_new = BaseOrder('new')
	order_location = dict()
	for order, location in base_order.get_order_location().items():
		order_location.update({order.id:location})
	
	order_skill = dict()
	for order, skill_id in base_order.get_order_skill().items():
		order_skill.update({order.id:skill_id})
	for order in base_order.ids.values():
		status = 'OPEN' if order in base_order.status_open else 'CLOSE'
		base_order_new.add(orderId = order.id, number = order.number, createdAt = get_iso_time(order.created_at), completionAt = get_iso_time(order.completion_at), skillId=order_skill[order.id], status=status, location=order_location[order.id], details = order.details, hidden = order in base_order.hiddens, containerId = None)
		#print(order.params, order.user_price, end = '\n\n')
	base_order_new.save()
	
