from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, Set, Tuple

from utils.tokens import Tokens
from utils.url import get_url_level

from .api import ApiBase, BaseElement
from .location import Location
from .skill import Skill, base_skill

__all__ = ["BaseContainer", "Container"]

VALID_TYPES = ('WORKERS', 'VACANCIES')#, 'INDEX_WORKERS', 'INDEX_VACANCIES')

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
			'VACANCIES':self.vacancies,
			'INDEX_WORKERS':self.index_workers,
			'INDEX_VACANCIES':self.index_vacancies,
		}

	def __repr__(self) -> str:
		return f"{len(self.ids)}"
	
	def get(self, id:str) -> Container:
		return self.ids.get(id)

	def get_container_skill(self):
		container_skill = dict()
		for skill, containers in self.skill_containers.items():
			container_skill.update(dict.fromkeys(containers, skill))
		return container_skill

	def get_containers(self, domain:str=None, level_mode:bool= None, level:int=0, hidden:bool=None, geo:bool=None, workers:bool=None, landings:bool=None, vacancy:bool=None) -> Set[Container]:
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


if __name__ == '__main__':
	b = BaseContainer(name='')
	b.load()
	d = b.get_containers()
