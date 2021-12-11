from collections import defaultdict
from typing import DefaultDict, Dict, List, Set

from utils.tokens import Tokens

from .api import ApiBase, BaseElement
from .skill import Skill, base_skill
from .utils import reversed_dict_values

__all__ = ["BaseFeedback", "Feedback"]

class Feedback(BaseElement):
	def __init__(self, feedbackId:str, comment:str='', grade=5.0, **kwargs) -> None: 
		super().__init__(id = feedbackId)
		self.comment:str = comment
		self.grade:float = grade
		self.tokens:Tokens = Tokens(self.comment)
		self.use_worker = False
        
	def __repr__(self) -> str:
		return f'ID = {self.id} Comment = {self.comment}'

	@property
	def base_tokens(self):
		return self.tokens.base_tokens

class BaseFeedback(ApiBase):
	'''
	Хранилище отзывов по id, worker_id
	'''
	__filename__ = 'base_feedback'
	__url__ = '/private/feedbacks'

	def __init__(self, name:str = '') -> None:
		super().__init__(name = name)
		self.worker_ids = defaultdict(set)
		self.skill_feedbacks:DefaultDict[Skill, Set[Feedback]] = defaultdict(set)

	def get_feedback_skill(self) -> Dict[Feedback, Skill]:
		return reversed_dict_values(self.skill_feedbacks)

	def get_feedbacks(self, skill:Skill) -> Set[Feedback]:
		return self.skill_feedbacks[skill]

	def filter_worker(self, base:Set[Feedback], worker_id:str) -> Set[Feedback]:
		return base.intersection(self.worker_ids[worker_id])

	def get(self, id:str)->Feedback:
		return self.ids.get(id)

	def add(self, recipient, order, **kwargs): 
		feedback = Feedback(**kwargs)
		self.ids.update({feedback.id:feedback})
		self.worker_ids[recipient['userId']].add(feedback)
		skill = base_skill.get_or_create(**order['skill'])
		self.skill_feedbacks[skill].add(feedback)

if __name__ == '__main__':
	pass
