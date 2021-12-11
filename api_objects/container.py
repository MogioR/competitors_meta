from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, Set, Tuple

from utils.tokens import Tokens
from utils.url import get_url_level

from .api import Api, ApiBase, BaseElement
from .location import Location
from .skill import Skill, base_skill
from .utils import reversed_dict_values

__all__ = ["BaseContainer", "Container"]

VALID_TYPES = ('WORKERS', 'VACANCIES')#, 'INDEX_WORKERS', 'INDEX_VACANCIES')
# location выделить отдельно в хранилище, как skills

PREDLOGS = ('д.','п.','аг.','ст.','гп.','м.','р-н', 'мкр.', 'деревне', 'посёлке', 'агрогородке', 'садоводческом товариществе', 'городском посёлке', 'районе', 'микрорайоне')

class Container(BaseElement):
	def __init__(self, base:BaseContainer, containerId:str, title:str = '', description:str = '', name:str = '', domain:str = '', path:str = '', hidden:bool = False, pageType:str = 'WORKERS', weight:float = 0.0, context:dict = {}, parent:dict={}, location:dict={}, **kwargs) -> None:
		super().__init__(id = containerId)
		self.name = name
		self.hidden = hidden
		self.domain = domain
		self.path = path
		self.page_type = pageType
		self.weight = weight
		self.title = title
		self.description = description
		self.anchor_name = []#context#.get('context', [])#['anchor_name']
		self.fake_skills = context.get('context', {}).get('skills')
		self.parent_id = parent.get('containerId')
		self.location = base.get_or_create_location(location)
		self.level:int = get_url_level(self.path)
		if self.page_type == 'VACANCIES':self.level -= 1
		self.kwargs_all = kwargs

		self.tokens:Tokens = Tokens(' '.join([self.name, *self.anchor_name]))

		self.extract_name = None
		self.extract_geo = None
	
	@property
	def base_tokens(self):
		return self.tokens.base_tokens

	def __repr__(self) -> str:
		return f'{self.id}'
	
	@property
	def url(self):
		return f'{self.domain}{self.path}'
	
	def __hash__(self) -> int:
		return hash(self.id)

def extract_name_geo(name:str, location_name:str, predlogs:Tuple[str]) -> Tuple[str, str]:
	extract_name = None
	extract_geo = None
	# у метро отдельно обработаем...
	if location_name in name:
		if ' в городе' in name:
			i = name.find(' в городе')
		elif ' в ' in name: 
			i = name.rfind(' в ')
		else:
			i = name.find(location_name) - 1
		extract_name = name[:i]
		#if extract_name[-1] == 'в': extract_name = extract_name[:-1]
		extract_geo = name[i:].strip()
	else:
		if 'у м.' in name:
			i = name.find('у м.')
			extract_geo = name[i - 2:]
			extract_name = name.replace(extract_geo, '').strip()
		elif 'м.' in name:
			i = name.find('м.')
			extract_geo = name[i:]
			extract_name = name.replace(extract_geo, '').strip()
		elif 'у метро' in name:
			i = name.find('у метро')
			extract_geo = name[i:]
			extract_name = name.replace(extract_geo, '').strip()
		else:
			for p in predlogs:
				if p in name:
					i = name.rfind(p)
					if name.rfind(' в ') == i-3:
						extract_geo = name[i - 2:]
						extract_name = name.replace(extract_geo, '').strip()
						break
					extract_geo = name[i:]
					extract_name = name.replace(extract_geo, '').strip()
					break
	return extract_name, extract_geo

class BaseContainer(ApiBase):
	'''
	Хранилище контейнеров
	'''
	__filename__ = 'base_container'
	__url__ = '/private/containers'

	geo_types = ('INDEX_WORKERS', 'INDEX_VACANCIES')

	def __init__(self, name:str = '') -> None:
		super().__init__(name = name)
		self.ids:Dict[Container] = dict()
		self.locations:Dict[Location] = dict()
		self.index_locations:Set[Location] = set()
		self.workers:Set[Container] = set()
		self.landings:Set[Container] = set()
		self.prices:Set[Container] = set()
		self.vacancies:Set[Container] = set()
		self.index_workers:Set[Container] = set()
		self.index_vacancies:Set[Container] = set()
		self.domains:DefaultDict[str, Set[Container]] = defaultdict(set)
		self.paths:DefaultDict[str, Set[Container]] = defaultdict(set)
		self.hiddens:Set[Container] = set()
		self.no_geo:Set[Container] = set()
		self.base_parents:DefaultDict[str, Set[Container]] = defaultdict(set)

		self.levels:Tuple[int, Set[Container]]  = tuple([set() for _ in range(6)])

		self.skill_containers:DefaultDict[Skill, Set[Container]] = defaultdict(set)

		self.base_type = {
			'WORKERS':self.workers,
			'LANDING':self.landings,
			'PRICES':self.prices,
			'VACANCIES':self.vacancies,
			'INDEX_WORKERS':self.index_workers,
			'INDEX_VACANCIES':self.index_vacancies,
		}
		self.count_add = 0

	def __repr__(self) -> str:
		return f"{len(self.ids)}"
	
	def get(self, id:str) -> Container:
		return self.ids.get(id)

	def get_container_skill(self) -> Dict[Container, Skill]:
		return reversed_dict_values(self.skill_containers)

	def get_containers(self, domain:str=None, level_mode:bool= None, level:int=0, hidden:bool=None, geo:bool=None, workers:bool=None, landings:bool=None, prices:bool=None, vacancy:bool=None) -> Set[Container]:
		'''
		level_mode
		True - выводит только контейнеры заданного уровня в параметре level
		False - исключает из результатов контейнеры заданного уровня
		Domain - строка, возвращает контейнеры относящиеся к этому домену\n
		None - параметр никак не задействован\n
		True - включает выбранные элементы в результате\n
		False - исключает выбранные элементы в результате
		'''
		if domain:
			base = self.domains[domain]
		else:
			base = set(self.ids.values())
		if hidden:
			base = base.intersection(self.hiddens)
		elif hidden is False:
			base = base.difference(self.hiddens)
		if level_mode:
			base = base.intersection(self.levels[level])
		elif level_mode is False:
			base = base.difference(self.levels[level])
		if geo:
			base = base.difference(self.no_geo) # no_geo это контейнеры БЕЗ гео...
		elif geo is False:
			base = base.intersection(self.no_geo)
		if vacancy:
			base = base.intersection(self.vacancies)
		elif vacancy is False:
			base = base.difference(self.vacancies)
		if workers:
			base = base.intersection(self.workers)
		elif workers is False:
			base = base.difference(self.workers)
		if landings:
			base = base.intersection(self.landings)
		elif landings is False:
			base = base.difference(self.landings)
		if prices:
			base = base.intersection(self.prices)
		elif prices is False:
			base = base.difference(self.prices)

		base = base.difference(self.index_workers, self.index_vacancies)
		return base
	
	def get_or_create_location(self, location_params:dict) -> Location:
		location_new = Location(**location_params)
		location = self.locations.get(location_new.id)
		if location is None:
			location = location_new
			self.locations.update({location.id:location})
		return location

	def add(self,  skill:dict={}, **kwargs) ->Container:
		self.count_add += 1
		container = Container(self, **kwargs)
		if not container.page_type in self.base_type: return None
		if container.page_type in self.geo_types: 
			self.index_locations.add(container.location) 
		self.ids.update({container.id:container})
		self.base_type[container.page_type].add(container)
		self.domains[container.domain].add(container)

		if container.hidden: self.hiddens.add(container)
		if skill.get('skillId'):
			skill = base_skill.get_or_create(**skill)
			self.skill_containers[skill].add(container)

		self.levels[container.level].add(container)

		self.base_parents[container.parent_id].add(container)
		return container
		
	def collect(self, page_max:int = 5)->None:
		'''
		Собирает с api данные по контейнерам, page_max - страница до которой нужно получить данные
		'''
		super().collect(page_max)

		for container in self.get_containers():
			path_normal = container.path.replace('/vacancies', '')
			if container.location in self.index_locations:
				self.no_geo.add(container)
				self.paths[container.path].add(container)
			else:
				path_normal = path_normal.rsplit('/', maxsplit=1)[0]
			self.paths[path_normal].add(container)
	
	async def collect2(self, page_max: int = 5, **kwargs) -> None:
		predlogs = PREDLOGS
		res = await super().collect2(page_max=page_max, **kwargs)
		for container in self.get_containers():
			path_normal = container.path.replace('/vacancies', '').replace('/prices', '').replace('/landings', '')
			if container.location in self.index_locations:
				self.no_geo.add(container)
				self.paths[container.path].add(container)
				container.extract_name, container.extract_geo = extract_name_geo(container.name, container.location.name, predlogs)
			else:
				path_normal = path_normal.rsplit('/', maxsplit=1)[0]
			self.paths[path_normal].add(container)

		return res
	
	def post_interlinks(self, container_id, data):
		api = Api(f'/private/containers/{container_id}/interlinks')
		return api.post(data)

if __name__ == '__main__':
	b = BaseContainer(name='')
	b.load()
	d = b.get_containers()
