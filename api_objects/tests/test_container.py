from api_objects.container import Container

from object_for_test import DATA_CONTAINERS, base_container

def test_collect_container():
    assert len(base_container.ids) == len(DATA_CONTAINERS)

    assert len(base_container.skill_containers) > 0

    for test_container in DATA_CONTAINERS:
        check_container = base_container.get(test_container['containerId'])
        assert isinstance(check_container, Container)

        assert isinstance(check_container.hidden, bool)
        assert check_container.hidden == test_container['hidden']
        
        assert isinstance(check_container.domain, str)
        assert check_container.domain == test_container['domain']

        assert isinstance(check_container.path, str)
        assert check_container.path == test_container['path']

        assert isinstance(check_container.name, str)
        assert check_container.name == test_container['name']

        assert isinstance(check_container.page_type, str)
        assert check_container.page_type == test_container['pageType']

        assert isinstance(check_container.weight, float)
        assert check_container.weight == test_container['weight']

    c= base_container.get('test_container_id1')
    assert len(base_container.get('test_container_id1').fake_skills) == 10
    assert len(base_container.get('test_container_id2').fake_skills) == 10
        
    for check_container in base_container.get_containers(geo=False):
        assert check_container.location in base_container.index_locations
        assert not (check_container.location.district_id or check_container.location.metro_id)

    for check_container in base_container.get_containers(geo=True):
        assert not check_container.location in base_container.index_locations
        assert check_container.location.district_id or check_container.location.metro_id
    
if __name__ == '__main__':
    test_collect_container()
