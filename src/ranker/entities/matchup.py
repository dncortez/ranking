class Matchup:
	def __init__(self, player, rival):
		self.player, self.rival = player, rival
		self.victorias = 0
		self.matches  = []
		self.elo_diff = []
	@property
	def partidas(self):
		return len(self.matches)
	@property
	def derrotas(self):
		return self.partidas - self.victorias
	@property
	def winrate(self):
		if self.partidas >0:
			return self.victorias / self.partidas
	@property
	def winrate1(self):
		return self.victorias / (self.partidas + 1)
	@property
	def lossrate1(self):
		return self.derrotas / (self.partidas + 1)
