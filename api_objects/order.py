from collections import defaultdict
from datetime import datetime
from typing import DefaultDict, Dict, List, Set

from .api import ApiBase, BaseElement

__all__ = ['BaseOrder', 'Order']

class Order(BaseElement):
    def __init__(self, orderId, number, createdAt:str, details:list, price:str = None, completionAt:str = None, **kwargs) -> None:
        super().__init__(id = orderId)
        self.number:str = number
        self.price:str = price
        self.details:list = details
        self.created_at:datetime = datetime.fromisoformat(createdAt.replace('Z','+00:00'))
        self.completion_at:datetime = datetime.fromisoformat(completionAt.replace('Z','+00:00')) if completionAt else None

        self.other_params = kwargs

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
        self.skill_orders:DefaultDict[str, Set[Order]] = defaultdict(set)
        self.locations:DefaultDict[str, Set[Order]] = defaultdict(set)

        self.hiddens:Set[Order] = set()
        self.status_open:Set[Order] = set()
       
    def get(self, id:str) -> Order:
        return self.ids.get(id)

    def add(self, skillId:str, status:str, hidden:bool, details:list = None, location:str = None, containerId:str = None, **kwargs):
        if not details: return 
        order_new = Order(details = details,**kwargs)
        self.ids.update({order_new.id:order_new})
        self.container_ids[containerId].add(order_new)
        self.skill_orders[skillId].add(order_new)
        self.locations[location].add(order_new)

        if hidden:self.hiddens.add(order_new)
        if status == 'OPEN':self.status_open.add(order_new)

