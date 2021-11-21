__all__ = ["Location",]

class Location:
	def __init__(self, locationId:str='', fullName:str='', name:str='', countryCode:str='', localityId:str=None, metroId:str=None, districtId:str=None, provinceId:str=None, **kwargs) -> None:
		self.id = locationId
		self.full_name = fullName
		self.name = name
		self.contry_code = countryCode
		self.metro_id = metroId
		self.locality_id = localityId
		self.province_id = provinceId
		self.district_id = districtId
	
	def __repr__(self) -> str:
		return f'{self.id} -> {self.name} {self.metro_id or self.district_id}'
	
