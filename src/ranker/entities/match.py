class Match:
	def __init__(self, P, id, ids, score, rdif, rdif_alt, league, matchtype, event_id, timestamp, replay):
		self.P, self.id, self.score, self.rdif, self.rdif_alt, self.ids, self.league = P, id, score, [float(rd) for rd in rdif], [float(rd) for rd in rdif_alt], ids, league,
		self.matchtype, self.event_id, self.timestamp, self.replay = matchtype, event_id, timestamp, replay
		self.timestamp = datetime.datetime.now() if self.timestamp is None else self.timestamp
		self.p1, self.p2 = [P.allplayers[id] for id in self.ids]
		self.search = self.p1.search + " " + self.p2.search + " " + self.p1.search
		self.event = None if event_id is None else P.allevents[event_id]
	@property
	def winner_id(self):
		return self.ids[self.score.index(max(self.score))]
	@property
	def loser_id(self):
		return self.ids[self.score.index(min(self.score))]
	@property
	def winner(self):
		return self.P.allplayers[self.winner_id]
	@property
	def loser(self):
		return self.P.allplayers[self.loser_id]
	def other(self, id, player=False):
		other_i = (self.ids.index(id)+1)%2
		other_id = self.ids[other_i]
		return self.P.allplayers[other_id] if player else other_id
	def fight(self):
		ftx=max(self.score)
		i1=int(self.score[0]>self.score[1])
		kval = min([kv for kv, lim in zip([40, 50, 60, 65, 70], [3, 4, 6, 9, 14]) if ftx<lim] + [75])
		#res_1= ((self.score[0]+i1)*1.0/(sum(self.score)+1)) if self.matchtype==1 else i1*1.0
		res_1= ((self.score[0]+i1*self.matchtype)*1.0/(sum(self.score)+self.matchtype))
		global_factor = min(max(1.5 - (np.mean([pl.elo for pl in self.P.players])-1000)/100, 0), 1)
		
		def calculate_rdifs(elos):
			expect_1= 1.0/(1+ 10**((elos[1] - elos[0])/400.0))
			return np.array((float(kval*(res_1-expect_1)), -float(kval*(res_1-expect_1))))
		def final_rdifs(elo1, elo2, pos1, pos2):
			elos, pos = np.array((elo1, elo2)), np.array((pos1, pos2))
			rdif = calculate_rdifs(elos) * pos/10
			return list(rdif + calculate_rdifs(elos + rdif) * (1 - 0.07*np.flip(pos)*(1-pos/10)))
		self.rdif = final_rdifs(self.p1.elo, self.p2.elo, self.p1.positioning, self.p2.positioning)
		self.rdif_alt = final_rdifs(self.p1.elo_alt, self.p2.elo_alt, self.p1.positioning, self.p2.positioning)
		if self.matchtype == 2:
			lims = max(min(2-(self.p1.elo - self.p1.elo_alt)/50, 1), 0) , max(min(2-(self.p2.elo - self.p2.elo_alt)/50, 1), 0)
			self.rdif = [self.rdif[0] + 1.5*ftx*i1*lims[0]*global_factor, self.rdif[1] + 1.5*ftx*(1-i1*lims[1])*global_factor]
	def submit(self):
		stmt = insert(AppResult).values(id = self.id, challenging_id = self.ids[0], rival_id = self.ids[1], challenging_score = self.score[0], rival_score = self.score[1], tournament_id=self.event_id,
										ranking_del_challenging = self.rdif[0], ranking_del_rival = self.rdif[1], ranking_alt_del_challenging = self.rdif_alt[0], 
										ranking_alt_del_rival = self.rdif_alt[1], mtype_id = self.matchtype, league_id = self.league, created = self.timestamp)
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[0]).values(ranking = self.p1.elo + self.rdif[0])
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[1]).values(ranking = self.p2.elo + self.rdif[1])
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[0]).values(ranking_alternative = self.p1.elo_alt + self.rdif_alt[0])
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[1]).values(ranking_alternative = self.p2.elo_alt + self.rdif_alt[1])
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[0]).values(disabled = 0)
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[1]).values(disabled = 0)
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[0]).values(positioning = max(self.p1.positioning - 1, 0))
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[1]).values(positioning = max(self.p2.positioning - 1, 0))
		result = self.P.session.execute(stmt)
		
		#self.P.session.commit()
		self.P.unsaved = True
		
		self.P.load_players()
		self.P.load_matches()
	def delete(self):
		stmt = delete(AppResult).where(AppResult.id == self.id)
		result = self.P.session.execute(stmt)
		
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[0]).values(ranking = self.p1.elo - self.rdif[0])
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[1]).values(ranking = self.p2.elo - self.rdif[1])
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[0]).values(ranking_alternative = self.p1.elo_alt - self.rdif_alt[0])
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[1]).values(ranking_alternative = self.p2.elo_alt - self.rdif_alt[1])
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[0]).values(positioning = max(10 - len([1 for match in self.P.matches if self.ids[0] in match.ids]) + 1, 0))
		result = self.P.session.execute(stmt)
		stmt = update(AppPlayer).where(AppPlayer.id == self.ids[1]).values(positioning = max(10 - len([1 for match in self.P.matches if self.ids[1] in match.ids]) + 1, 0))
		result = self.P.session.execute(stmt)
		
		#self.P.session.commit()
		self.P.unsaved = True
		
		self.P.load_players()
		self.P.load_matches()
