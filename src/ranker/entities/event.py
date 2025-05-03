class Event:
	def __init__(self, P, id, name, league_id, champion_id, timestamp):
		self.P, self.id, self.name, self.league_id, self.champion_id, self.timestamp = P, id, name, league_id, champion_id, timestamp
		self.champion = None if champion_id is None else P.allplayers[champion_id] 
