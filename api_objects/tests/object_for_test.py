from api_objects.container import BaseContainer
from mock import patch
from api_objects.order import BaseOrder
from api_objects.skill import BaseSkill, base_skill

from api_objects.worker import BaseWorker
from api_objects.feedback import BaseFeedback

DATA_SKILLS = [
    {
        "skillId":"test_skill_id1",
        "name":"test_skill_name"
    },
    {
        "skillId":"test_skill_id2",
        "name":"test_skill_name"
    },
    {
        "skillId":"test_skill_id3",
        "name":"test_skill_name"
    }
]

DATA_LOCATIONS = [
    {
        "locationId":"test_location1",
        "fullName":"test_fullname_location1",
        "name":"no_geo",
        "countryCode":"BY",
        "metroId @null":"",
        "localityId @null":"",
        "provinceId @null":"",
        "districtId @null":""
    }, 
    {
        "locationId":"test_location2",
        "fullName":"test_fullname_location2",
        "name":"geo_metro",
        "countryCode":"BY",
        "metroId":"test_metro_id1",
        "localityId @null":"",
        "provinceId @null":"",
        "districtId @null":""
    }, 
    {
        "locationId":"test_location3",
        "fullName":"test_fullname_location3",
        "name":"geo_district",
        "countryCode":"BY",
        "metroId @null":"",
        "localityId @null":"",
        "provinceId @null":"",
        "districtId":"test_district_id1"
    }, 
]

def get_context_fake_skill(prefix = '', i_max = 10):
    context = list()
    for i in range(1, i_max + 1):
        context.append(f'fake-skill_{prefix}_{i}')
    return {'skills':context}

DATA_CONTAINERS = [
    {
        "containerId":"test_index_container1",
        "name":"new_name",
        "path":"/new_path",
        "domain":'test_domain',
        "pageType":"INDEX_WORKERS",
        "lang":"RU",
        "title":"new_title",
        "description":"new_description",
        "weight":1.0000000,
        "hidden":False,
        "context":{
            "features":[
                "hide_about_me", 
                "hide_education"
            ],
            "context":{}
        },
        "skill":DATA_SKILLS[2],
        "parent @null":None,
        "location":DATA_LOCATIONS[0],
        "features":[
            "a3709185-79ed-4f49-a113-ef8e6928c0d0"
        ]
    },
    {
        "containerId":"test_container_id1",
        "name":"new_name",
        "path":"/new_path",
        "domain":'test_domain',
        "pageType":"WORKERS",
        "lang":"RU",
        "title":"new_title",
        "description":"new_description",
        "weight":1.0000000,
        "hidden":False,
        "context":{
        "features":[
            "hide_about_me", 
            "hide_education"
        ],
        "context":get_context_fake_skill('ct1')
        },
        "skill":DATA_SKILLS[0],
        "parent":{
            "containerId":"c60b7f67-3be3-44dc-ac91-a565d8a95f84",
            "name":"ZCaGAOtLLH"
        },
        "location":DATA_LOCATIONS[0],
        "features":[
            "a3709185-79ed-4f49-a113-ef8e6928c0d0"
        ]
    },
    {
        "containerId":"test_container_id2",
        "name":"new_name",
        "path":"/new_path",
        "domain":'test_domain',
        "pageType":"WORKERS",
        "lang":"RU",
        "title":"new_title",
        "description":"new_description",
        "weight":1.0000000,
        "hidden":False,
        "context":{
        "features":[
            "hide_about_me", 
            "hide_education"
        ],
        "context":get_context_fake_skill('ct2')
        },
        "skill":DATA_SKILLS[1],
        "parent":{
            "containerId":"c60b7f67-3be3-44dc-ac91-a565d8a95f84",
            "name":"ZCaGAOtLLH"
        },
        "location":DATA_LOCATIONS[1],
        "features":[
            "a3709185-79ed-4f49-a113-ef8e6928c0d0"
        ]
    }
]

DATA_WORKERS = {
    DATA_CONTAINERS[1]['containerId']:[
        {
            "worker":{
                "workerId":"test_worker_id1",
                "avatarId":"avatars/test_worker1"
            },
            "pictures":[
                {
                    "title":"description",
                    "pictureId":"pictures/test_picture1",
                    "skillId":DATA_SKILLS[0]['skillId']
                }
            ],
            "educations":[
                {
                    "educationId":"test_education_id1",
                    "institution":"fZjmAcFBqg",
                    "course":"rEqEmLsdhW",
                    "degree":"HIGH"
                }
            ],
            "statistics":{
                "totalNumberOfFeedbacks":2,
                "totalAvgGrade":5.0,
                "numberOfFeedbacks":1,
                "avgGrade":5.0
            }
        },
        {
            "worker":{
                "workerId":"test_worker_id2",
                "avatarId":"avatars/test_worker2"
            },
            "pictures":[
                {
                    "title":"description",
                    "pictureId":"pictures/test_picture3",
                    "skillId":DATA_SKILLS[0]['skillId']
                }
            ],
            "educations":[
                {
                    "educationId":"test_education_id2",
                    "institution":"fZjmAcFBqg",
                    "course":"rEqEmLsdhW",
                    "degree":"HIGH"
                }
            ],
            "statistics":{
                "totalNumberOfFeedbacks":1,
                "totalAvgGrade":5.0,
                "numberOfFeedbacks":1,
                "avgGrade":5.0
            }
        }
    ],
    DATA_CONTAINERS[2]['containerId']:[
        {
            "worker":{
                "workerId":"test_worker_id1",
                "avatarId":"avatars/test_worker1"
            },
            "pictures":[
                {
                    "title":"description",
                    "pictureId":"pictures/test_picture2",
                    "skillId":DATA_SKILLS[1]['skillId']
                }
            ],
            "educations":[
                {
                    "educationId":"test_education_id1",
                    "institution":"fZjmAcFBqg",
                    "course":"rEqEmLsdhW",
                    "degree":"HIGH"
                }
            ],
            "statistics":{
                "totalNumberOfFeedbacks":1,
                "totalAvgGrade":5.0,
                "numberOfFeedbacks":1,
                "avgGrade":5.0
            }
        }
    ]
}
'''
1 и 2 отзыв относятся к разным контейнерам, но к одному воркеру.
'''
DATA_FEEDBACKS = [
	{
		"feedbackId":"test_feedbackId1",
		"grade":2.0,
		"comment":"lmyTcByOhZ",
		"sender":{
			"firstName":"f01ff513-e769-453c-9543-bf65424c0648"
		},
		"recipient":{
			"userId":'test_worker_id1',
			"fullName":"JZVMIwpxoy EhODghiMCX"
		},
		"order":{
			"orderId":"test_order_id1",
			"number":"ZIxHfqm",
            "skill":DATA_SKILLS[0]
		}
	},
	{
		"feedbackId":"test_feedbackId2",
		"grade":2.0,
		"comment":"lmyTcByOhZ",
		"sender":{
		    "firstName":"f01ff513-e769-453c-9543-bf65424c0648"
		},
		"recipient":{
            "userId":'test_worker_id1',
            "fullName":"JZVMIwpxoy EhODghiMCX"
		},
		"order":{
            "orderId":"test_order_id2",
            "number":"qweqewe",
            "skill":DATA_SKILLS[1]
		}
	},
	{
		"feedbackId":"test_feedbackId3",
		"grade":2.0,
		"comment":"lmyTcByOhZ",
		"sender":{
		    "firstName":"f01ff513-e769-453c-9543-bf65424c0648"
		},
		"recipient":{
            "userId":'test_worker_id2',
            "fullName":"JZVMIwpxoy EhODghiMCX"
		},
		"order":{
            "orderId":"test_order_id3",
            "number":"qweqewe",
            "skill":DATA_SKILLS[0]
		}
	}
]

DATA_ORDERS = [
   {
      "orderId":"test_order_id1",
      "containerId":"test_container1",
      "number":"IgoURGr",
      "status":"CLOSE",
      "hidden":False,
      "requester":"first name",
      "skillId":"test_skill_id1",
      "closeReason":"NOT_RELEVANT",
      "performerId":"test_performer_id1", # скорее всего это worker_id, может быть, если заказ выполнен, а если нет, то будет отсутствовать
      "completionAt":"2000-01-01T12:00:00",
      "location":"Минск",
      "details":[
        {
        "description":"description",
        "value":"value"
        }
      ],
      "createdAt":"2000-01-01T12:00:00" 
   },
    {
      "orderId":"test_order_id2",
      "containerId":"test_container1",
      "number":"IgoURGr",
      "status":"OPEN",
      "hidden":True,
      "requester":"first name",
      "skillId":"test_skill_id1",
      "closeReason":"NOT_RELEVANT",
      "price":"15.0000 руб",
      "location":"Минск",
      "details":[
        {
        "description":"description",
        "value":"value"
        }
      ],
      "createdAt":"2000-01-01T12:00:00"
   }
]


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

def init_base_container():
    base_container = BaseContainer()
    with patch('requests.get') as perm_mock:
        mock_resp = MockResponse({'content':DATA_CONTAINERS, 'pageNumber':0, 'totalPages':1}, 200)
        perm_mock.return_value = mock_resp
        base_container.collect()
    return base_container

def init_base_feedback():
    base_feedback = BaseFeedback()
    with patch('requests.get') as perm_mock:
        mock_resp = MockResponse({'content':DATA_FEEDBACKS, 'pageNumber':0, 'totalPages':1}, 200)
        perm_mock.return_value = mock_resp
        base_feedback.collect()
    return base_feedback

def init_base_worker():
    base_worker = BaseWorker()
    with patch('requests.get') as perm_mock:
        for container_id in base_container.ids.keys():
            mock_resp = MockResponse({'content':DATA_WORKERS.get(container_id, []), 'pageNumber':0, 'totalPages':1}, 200)
            perm_mock.return_value = mock_resp
            base_worker.collect(container_id)
    return base_worker

def init_base_order():
    base_order = BaseOrder()
    with patch('requests.get') as perm_mock:
        mock_resp = MockResponse({'content':DATA_ORDERS, 'pageNumber':0, 'totalPages':1}, 200)
        perm_mock.return_value = mock_resp
        base_order.collect()
    return base_order
    
base_skill.ids.clear()
base_container = init_base_container()
base_worker = init_base_worker()
base_order = init_base_order()
base_feedback = init_base_feedback()





