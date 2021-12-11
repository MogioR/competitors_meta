from .api import ApiBase, BaseElement

__all__ = ["BaseSkill", "Skill", 'base_skill']

class Skill(BaseElement):
	def __init__(self, skillId:str = '', name:str = '', **kwargs) -> None:
		super().__init__(id = skillId)
		self.name = name
		self.update()
	
	def update(self, count = 0, average = 0.0, median = 0.0, p99 = 0.0, p90 = 0.0, p95 = 0.0, p75 = 0.0, p25 = 0.0):
		self.count = count
		self.average = average
		self.median = median
		self.p99 = p99
		self.p90 = p90
		self.p95 = p95
		self.p75 = p75
		self.p25 = p25

	def __repr__(self) ->str:
		return self.id

class BaseSkill(ApiBase):
	__filename__ = 'base_skill'
	__url__ = '/private/ctx/skills/stats'

	def __init__(self, name:str = '') -> None:
		super().__init__(name = name)

	def add(self, skillId, **kwargs):
		skill = self.get(id = skillId)
		skill.update(kwargs)

	def get(self, id:str) -> Skill:
		return self.ids.get(id)

	def get_or_create(self, skillId:str='', name:str=''):
		skill = self.get(skillId)
		if skill is None:
			skill = Skill(skillId = skillId, name = name)
			self.ids.update({skill.id:skill})
		elif name and skill.name != name:
			skill.name = name
		return skill
	
	def collect(self, skill_id:str, locality_id, page_max: int = 5, **kwargs) -> None:
		return super().collect(skillId = skill_id, localityId = locality_id, **kwargs)
	
	async def collect2(self, **kwargs) -> None:
		base_elements = list()
		for skill_id in self.ids.keys():
			base_elements.append({'skillId':skill_id})
		return await self.collect3(base_elements, **kwargs)
		

base_skill = BaseSkill()
base_skill.load()
print('load base skills')
