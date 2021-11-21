from object_for_test import (DATA_FEEDBACKS, base_container,
                             base_feedback, base_worker)

def test_collect_feedback():
	assert len(base_feedback.ids) == len(DATA_FEEDBACKS)

	assert len(base_feedback.skill_feedbacks) > 0

	assert len(base_feedback.worker_ids) == len(base_worker.ids)

	for test_feedback in DATA_FEEDBACKS:
		check_feedback = base_feedback.get(test_feedback['feedbackId'])
		assert check_feedback.comment == test_feedback['comment']
		assert check_feedback.grade == test_feedback['grade']
	check_feedback = set()
	for skill, feedbacks in base_feedback.skill_feedbacks.items():
		containers = base_container.skill_containers.get(skill)
		for container in containers:
			for worker in base_worker.container_ids[container.id]:
				check_feedback.update(base_feedback.filter_worker(feedbacks, worker.id))
	assert len(check_feedback) == len(DATA_FEEDBACKS)



if __name__ == '__main__':
	test_collect_feedback()
