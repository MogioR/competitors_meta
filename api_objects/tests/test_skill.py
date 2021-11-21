from object_for_test import base_skill, DATA_SKILLS

def test_skill():
	assert len(base_skill.ids) == len(DATA_SKILLS)
	for skill_params in DATA_SKILLS:
		check_skill = base_skill.get(skill_params['skillId'])
		assert check_skill.id == skill_params['skillId']
		assert check_skill.name == skill_params['name']


if __name__ == '__main__':
    test_skill()