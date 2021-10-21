import requests


class XmlRiver:
    def __init__(self, config):
        self.xml_river_user = config['XMLRiver']['xml_river_user']
        self.xml_river_key = config['XMLRiver']['xml_river_key']
        self.group_by = config['XMLRiver']['group_by']

    # Get report from request with keys
    def get_search_results(self, keys):
        answer = requests.get(self.get_request(keys), timeout=60).text
        return answer

    # Set locale for search
    def set_region(self, locale):
        pass

    # Return request to xml river api with keys
    def get_request(self, keys):
        pass
