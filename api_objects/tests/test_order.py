from object_for_test import DATA_ORDERS, base_order


def test_order():
	assert len(base_order.ids) == len(DATA_ORDERS)
	for test_order in DATA_ORDERS:
		check_order = base_order.get(test_order['orderId'])
		assert check_order.number == test_order['number']
		assert check_order.price == test_order.get('price')

		assert test_order['skillId'] in base_order.skill_orders
		assert check_order in base_order.skill_orders[test_order['skillId']]

		assert test_order['location'] in base_order.locations
		assert check_order in base_order.locations[test_order['location']]

		assert test_order['containerId'] in base_order.container_ids
		assert check_order in base_order.container_ids[test_order['containerId']]

		assert test_order['status'] != 'OPEN' or check_order in base_order.status_open
		assert not test_order['hidden'] or check_order in base_order.hiddens

		
	


if __name__ == '__main__':
    test_order()
