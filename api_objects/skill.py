from .api import Base, BaseElement

__all__ = ["BaseSkill", "Skill", 'base_skill']

class Skill(BaseElement):
	def __init__(self, skillId:str = '', name:str = '', **kwargs) -> None:
		super().__init__(id = skillId)
		self.name = name

	def __repr__(self) ->str:
		return self.id

class BaseSkill(Base):
	__filename__ = 'base_skill'

	def __init__(self, name:str = '') -> None:
		super().__init__(name = name)

	def add(self, o:Skill):
		self.ids.update({o.id:o})
	
	def get(self, id:str) -> Skill:
		return self.ids.get(id)

	def get_or_create(self, **skill_params):
		skill_new = Skill(**skill_params)
		skill = self.get(skill_new.id)
		if skill is None:
			skill = skill_new
			self.add(skill)
		return skill

base_skill = BaseSkill()
base_skill.load()
print('load base skills')
