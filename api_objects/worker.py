from collections import defaultdict
from typing import DefaultDict, Dict, List

from .api import ApiBase, BaseElement

__all__ = ['BaseWorker', 'Worker', 'Statistic', 'Education', 'Picture']

class Picture:
    def __init__(self, pictureId = None, title = None, skillId = None, **kwargs) -> None:
        self.id:str = pictureId
        self.title:str = title
        self.skill_id:str = skillId

class Education:
    def __init__(self, educationId = None, institution = None, course = None, degree = None, **kwargs) -> None:
        self.id:str = educationId
        self.institution:str = institution
        self.course:str = course
        self.degree:str = degree

class Statistic:
    def __init__(self, numberOfFeedbacks = 0, avgGrade = 0, **kwargs):
        self.number_feedbacks = numberOfFeedbacks # по скиллу
        self.avg_grade = avgGrade # по скиллу
    
    def __repr__(self) -> str:
        return f'grade|number -> {self.avg_grade}|{self.number_feedbacks}'

class Worker(BaseElement):
    def __init__(self, worker:Dict[str, str], educations:list=None, **kwargs) -> None:
        super().__init__(id = worker.get('workerId'))

        self.avatar_id = worker.get('avatarId')
        self.base_pictures:defaultdict[str, List[Picture]] = defaultdict(list)
        
        self.base_education:List[Education] = list()
        if educations:
            for education in educations:
                self.base_education.append(Education(**education))
        
        self.base_state:Dict[str, Statistic] = dict()
    
    def __repr__(self) -> str:
        return f'{self.id} {self.avatar_id}'

    @property
    def state_total(self) ->Statistic:
        return self.base_state[None]

    def add_picture(self, container_id:str, pictures:list):
        if not pictures: return 
        for picture in pictures:
            self.base_pictures[container_id].append(Picture(**picture))
    
    def add_state(self, container_id:str, numberOfFeedbacks:int = 0, avgGrade:float= 0.0, **kwargs):
        self.base_state.update({container_id:Statistic(numberOfFeedbacks, avgGrade)})
    
    def add_state_total(self, totalNumberOfFeedbacks:int = 0, totalAvgGrade:float = 0.0, **kwargs):
        self.base_state.update({None:Statistic(totalNumberOfFeedbacks, totalAvgGrade)})

class BaseWorker(ApiBase):
    '''
    Хранилище работников по id, при парсинге нужно указывать container_id в который будут отправляться workers!
    '''
    __filename__ = 'base_worker'
    __url__ = '/private/suite-workers'
    def __init__(self, name:str = '') -> None:
        super().__init__(name = name)
        self.ids:Dict[str, Worker] = dict()
        self.container_ids:DefaultDict[str, set[Worker]] = defaultdict(set)
        self.container_id = None # контейнер ид в который добавляется текущий воркер
        self.dublicate_workers = 0

    def get(self, id:str) ->Worker:
        return self.ids.get(id)

    def add(self, worker:dict, pictures:list, statistic:dict={}, **kwargs):
        worker_new = self.ids.get(worker.get('workerId'))
        if worker_new is None:
            worker_new = Worker(worker = worker, **kwargs)
            worker_new.add_state_total(**statistic)
        worker_new.add_picture(self.container_id, pictures)
        worker_new.add_state(self.container_id, **statistic)
        self.ids.update({worker_new.id:worker_new})
        self.container_ids[self.container_id].add(worker_new)
        
    def collect(self, container_id:str, page_max: int = 5, **kwargs) -> None:
        self.container_id = container_id
        return super().collect(page_max=page_max, containerId = container_id, **kwargs)
