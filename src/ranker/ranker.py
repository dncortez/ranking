
class Ranker:
	def __init__(self, db_url = "mariadb://root:wiro2k10@localhost/ranking"):
		self.engine = create_engine(db_url)
		self.session = Session(self.engine)
		self.load_players()
		self.load_events()
		self.load_matches()
		self.new_player = None
		self.selected=None
		self.selected_id=None
		self.smallest_shown = None
		self.selected_match=None
		self.match_toelim = False
		self.importing    = False
		self.import_list, self.denied_list  = None, None
		self.start_newmatch()
		self.unsaved = False
		self.ranking_matrix = None
		self.last_update = self.session.query(AppLeague.last_update).where(AppLeague.id == 3)[0][0]
	def commit(self):
		self.session.commit()
		self.unsaved = False
	def sort_players(self, present_priority=True):
		def by_elo(pl): return [pl.disabled*present_priority, -pl.elo]
		return [pl for pl in sorted(list(self.allplayers.values()), key=by_elo) if pl.league==3]
	def load_players(self):
		query=self.session.query(AppPlayer)
		self.allplayers={row.id:Player(self, row.id, row.nickname, row.ranking, row.main_id, row.league_id, row.country_id, row.disabled, row.days_remaining, row.ranking_alternative, row.positioning) for row in query}
		self.players=self.sort_players()
		self.id_to_rank= {player.id:i for i, player in enumerate(self.players)}
	def sort_matches(self):
		def by_date(ma): return [ma.timestamp, ma.id]
		return [ma for ma in sorted(list(self.allmatches.values()), key=by_date, reverse=True) if ma.league==3]
	def load_matches(self):
		query=self.session.query(AppResult)
		self.allmatches={row.id:Match(self, row.id, [row.challenging_id, row.rival_id], [row.challenging_score, row.rival_score],
					[row.ranking_del_challenging, row.ranking_del_rival], [row.ranking_alt_del_challenging, row.ranking_alt_del_rival], 
					row.league_id, row.mtype_id, row.tournament_id, row.created, row.replay_url) for row in query}
		self.matches=self.sort_matches()
		for ma in self.matches:
			for pl in ma.ids:
				self.allplayers[pl].active_since = ma.timestamp.date()
	def load_events(self):
		query=self.session.query(AppTournament)
		self.allevents={row.id:Event(self, row.id, row.name, row.league_id, row.champion_id, row.tournament_date) for row in query}
		self.events=[ev for ev in sorted(self.allevents.values(), key=lambda X:X.id, reverse=True) if ev.league_id==3]
	def start_newmatch(self, module = None):
		self.newmatch = module is not None
		self.newmatch_toadd = None
		self.newmatch_select  = 0
		self.newmatch_pselect = 0
		self.newmatch_p1 = None
		self.newmatch_p2 = None
		self.newmatch_mtype = 1
		self.newmatch_eventid = 0
		self.event_list = [ev.name for ev in self.events] + ["---sin evento---"]
		if module:
			self.newmatch_box1 = textbox(module, [0,0], [45, 25], color=white, text="", numeric=True, num_float=False)
			self.newmatch_box2 = textbox(module, [0,0], [45, 25], color=white, text="", numeric=True, num_float=False)
	def start_newplayer(self):
		if self.new_player is None:
			self.new_player = Player(self, max(self.allplayers.keys())+1, "Nuevo Jugador", 950, 1, 3, 1, 0, 180, 950, 10)
			self.allplayers[max(self.allplayers.keys())+1] = self.new_player
			self.new_player.editing = True
		self.selected_id = max(self.allplayers.keys())
	def show_ranking(self, M, wheel=0, posx=210, posy=80, fullmode=True, players = None):
		endx=posx+(850 if fullmode else 250)
		M.wheeler[wheel][0]=[posx, endx]
		M.wheeler[wheel][1]=min(M.wheeler[wheel][1], 0)
		base=posy+M.wheeler[wheel][1]
		if fullmode:
			M.text("#", [posx+20, base-45], textalign=[0, 0.5], col=white, size=32)
			M.text("Elo", [posx+370, base-40], textalign=[0, 0.5], col=white, size=32)
			M.text("Bonus", [posx+460, base-40], textalign=[0, 0.5], col=white, size=32)
			M.text("Seeding", [posx+600, base-40], textalign=[0, 0.5], col=white, size=32)
			M.text("Days left", [posx+760, base-40], textalign=[0, 0.5], col=white, size=32)
		M.text("Player", [posx+(120 if fullmode else 20), base-40], textalign=[0, 0.5], col=white, size=32)
		ausentes=False
		self.selected=None
		self.smallest_shown = None
		for pos, player in enumerate(self.players if players is None else players):
			if re.search(searchbar.regex, player.search):
				if base>=-30:
					if player.disabled==1 and fullmode and not ausentes:
						M.text("Ausentes", [posx+70, base+20], textalign=[0, 0.5], col=white, size=32)
						ausentes=True
						base+=55
					if M.boton(((posx+endx)//2, base), (endx-posx, 28), rad=0, color=bg1, clarity=0.2):
						self.selected=player
						self.selected_id = player.id
						player.get_stats(enforce = True)
					if fullmode:
						player.profile(M, (posx+60, base -13), 26)
						if not ausentes: M.text(str(pos+1), [posx+20, base], textalign=[0, 0.5], col=white)
						M.text(f"{player.elo:.1f}", [posx+370, base], textalign=[0, 0.5], col=white)
						M.text(plussign(player.elo - player.elo_alt), [posx+460, base], textalign=[0, 0.5], col=(180, 245, 255) if player.elo >= player.elo_alt else (255, 180, 210))
						M.text("-" if player.positioning ==0 else f"{player.positioning}", [posx+600, base], textalign=[0, 0.5], col= white)
						M.text(f"{player.days_remaining}", [posx+760, base], textalign=[0, 0.5], col=white)
					M.text(player.name, [posx+(120 if fullmode else 20), base], textalign=[0, 0.5], col=white)
				base+=30
				if self.smallest_shown is None or len(player.name) < len(self.smallest_shown.name):
					self.smallest_shown = player
				if base>M.height+30: break
	def show_matches(self, M, wheel=1, posx=500, posy=80):
		endx=posx+740
		M.wheeler[wheel][0]=[posx, endx]
		M.wheeler[wheel][1]=min(M.wheeler[wheel][1], 0)
		base=posy+M.wheeler[wheel][1]
		M.text("Score", [posx + 350, base-40], textalign=[0.5, 0.5], col=white, size=28)
		M.text("Player 1", [posx + 300, base-40], textalign=[1, 0.5], col=white, size=28)
		M.text("Player 2", [posx + 400, base-40], textalign=[0, 0.5], col=white, size=28)
		M.text("Gain", [posx + 50, base-40], textalign=[1, 0.5], col=white, size=28)
		M.text("Gain", [posx + 650, base-40], textalign=[0, 0.5], col=white, size=28)
		if self.selected is not None and not self.newmatch:
			self.start_newmatch(M)
		if self.newmatch:
			self.show_newmatch(M, posx+100, base)
			base+=140
		for match in self.matches:
			if re.search(searchbar.regex, match.search):
				height = 30 if self.selected_match != match.id else (95 if match.event is None else 125)
				if base>=-30:
					if M.boton(((posx+endx)//2, base), (endx-posx, 28), rad=0, color=bg1, clarity=0.2):
						self.selected_match = None if self.selected_match == match.id else match.id
						self.match_toelim = False
					M.text(f"{match.score[0]} - {match.score[1]}", [posx + 350, base], textalign = [0.5, 0.5], col=white)
					M.text(match.p1.name, [posx + 300, base], textalign = [1, 0.5], col=white)
					M.text(match.p2.name, [posx + 400, base], textalign = [0, 0.5], col=white)
					M.text(plussign(match.rdif[0]), [posx + 50,  base], textalign = [1, 0.5], col=(180, 245, 255) if match.rdif[0]>=0 else (255, 180, 210))
					M.text(plussign(match.rdif[1]), [posx + 650, base], textalign = [0, 0.5], col=(180, 245, 255) if match.rdif[1]>=0 else (255, 180, 210))
					#M.text(plussign(match.rdif_alt[0]), [posx - 20,  base], textalign = [1, 0.5], col=(180, 245, 255) if match.rdif_alt[0]>=0 else (255, 180, 210))
					#M.text(plussign(match.rdif_alt[1]), [posx + 750, base], textalign = [0, 0.5], col=(180, 245, 255) if match.rdif_alt[1]>=0 else (255, 180, 210))
					M.text("T" if match.matchtype == 2 else "R", [posx + 720, base], textalign = [0.5, 0.5], col=(255, 180, 0) if match.matchtype == 2 else white)
					if self.selected_match == match.id:
						M.text(f"Match type: {'Tournament' if match.matchtype == 2 else 'Ranked'}", [posx + 20, base+30], textalign = [0, 0.5], col=(255, 180, 0) if match.matchtype == 2 else white)
						M.text(str(match.timestamp), [posx + 20, base+60], textalign = [0, 0.5], col=white)
						if match.event is not None:
							M.text("Event: "+match.event.name, [posx + 20, base+90], textalign = [0, 0.5], col=white)
						if M.boton((posx + 650, base+30), (110, 25), txt="Eliminar", rad = 20, color = (150, 60, 70)):
							self.match_toelim = True
						if self.match_toelim:
							M.text("Seguro?", (posx + 580, base+60), textalign = [1, 0.5], col= white)
							if M.boton((posx + 620, base+60), (50, 25), txt="No", rad = 20, color = bot0):
								self.match_toelim = False
							if M.boton((posx + 680, base+60), (50, 25), txt="Sí", rad = 20, color = (90, 90, 90)):
								match.delete()
				base+= height 
				if base>M.height+30: break
	def show_newmatch(self, M, posx, posy):
		
		M.text("New Match", (posx+160, posy), textalign = [0.5, 0.5], col = white, size = 28)
		
		if M.boton((posx, posy+40), (200, 30), color= (155,15,70) if self.newmatch_select == 0 else (bg1 if self.newmatch_p1 is None else bg3), clarity=0.2, 
				   txt = "Player 1" if self.newmatch_p1 is None else self.newmatch_p1.name, rad = 0):
			self.newmatch_select = 0
		if M.boton((posx, posy+80), (200, 30), color= (155,15,70) if self.newmatch_select == 1 else (bg1 if self.newmatch_p2 is None else bg3), clarity=0.2, 
				   txt = "Player 2" if self.newmatch_p2 is None else self.newmatch_p2.name, rad = 0):
			self.newmatch_select = 1
		
		pscore = [self.newmatch_box1.number, self.newmatch_box2.number]
		self.newmatch_box1.color = (255, 180, 210) if self.newmatch_box1.clicked else white
		self.newmatch_box1.show([posx + 140, posy+40])
		if self.newmatch_box1.clicked:
			self.newmatch_select = 2
		self.newmatch_box2.color = (255, 180, 210) if self.newmatch_box2.clicked else white
		self.newmatch_box2.show([posx + 140, posy+80])
		if self.newmatch_box2.clicked:
			self.newmatch_select = 3
		score = [self.newmatch_box1.number, self.newmatch_box2.number]
		
		pmtype = self.newmatch_mtype
		if self.newmatch_select == 4 and M.enter:
			self.newmatch_mtype = (self.newmatch_mtype % 2) +1
		self.newmatch_mtype = M.numboton(self.newmatch_mtype-1, (posx+360, posy+40), (150, 30), rad=20, txt=["Ranked", "Tournament"], 
					                     color=[(255, 180, 210), (180,60,70)] if self.newmatch_select == 4 else [white, (255, 180, 0)], textsize=20) + 1
		if pmtype != self.newmatch_mtype:
			self.newmatch_select = 4
		
		peventid = self.newmatch_eventid
		if self.newmatch_select == 5 and (M.k_d or M.k_u):
			self.newmatch_eventid = (self.newmatch_eventid + (1 if M.k_d else -1)) % len(self.event_list)
		self.newmatch_eventid = M.numboton(self.newmatch_eventid, (posx+440, posy+80), (380, 30), rad=0, txt=self.event_list,
					                     color=[(255, 180, 210)] if self.newmatch_select == 5 else [bg1], textsize=16, textalign = [0, 0.5])
		if peventid != self.newmatch_eventid:
			self.newmatch_select = 5
		
		if self.newmatch_toadd is not None:
			if M.boton((posx + 550, posy+40), (150, 30), color= (155,15,70) if self.newmatch_select == 6 else bot0, clarity=0.2, txt = "Submit", rad = 20) or (self.newmatch_select == 6 and M.enter):
				self.newmatch_toadd.submit()
				self.start_newmatch()
		
		if "\t" in M.typing:
			self.newmatch_select += 1
		self.newmatch_select = self.newmatch_select % 7
		pplayers = [self.newmatch_p1, self.newmatch_p2]
		if self.newmatch_select < 2:
			searchbar.clicked = True
			if self.selected is not None:
				if self.newmatch_select ==0: self.newmatch_p1 = self.selected
				elif self.newmatch_select ==1: self.newmatch_p2 = self.selected
				self.newmatch_select +=1
		if self.newmatch_select != self.newmatch_pselect:
			if self.newmatch_select == 2:
				self.newmatch_box1.clicked = True
			else:
				self.newmatch_box1.clicked = False
			if self.newmatch_select == 3:
				self.newmatch_box2.clicked = True
			else:
				self.newmatch_box2.clicked = False
				
			if self.newmatch_select > 1:
				searchbar.clicked = False
		self.newmatch_pselect = self.newmatch_select
		
		if None not in [self.newmatch_p1, self.newmatch_p2] and (pmtype != self.newmatch_mtype or score != pscore or pplayers != [self.newmatch_p1, self.newmatch_p2] or peventid != self.newmatch_eventid):
			eventid = self.events[self.newmatch_eventid].id if self.newmatch_eventid < len(self.events) else None
			self.newmatch_toadd = Match(self, max(self.allmatches.keys())+1, [self.newmatch_p1.id, self.newmatch_p2.id], score, [0,0], [0,0], 3, self.newmatch_mtype,
					eventid, datetime.datetime.now() if eventid is None else self.allevents[eventid].timestamp, None)
			self.newmatch_toadd.fight()
		
		rdif = (0,0) if self.newmatch_toadd is None else self.newmatch_toadd.rdif
		M.text(plussign(rdif[0]), [posx + 170, posy + 40], textalign = [0, 0.5], col = (180, 245, 255) if rdif[0]>=0 else (255, 180, 210))
		M.text(plussign(rdif[1]), [posx + 170, posy + 80], textalign = [0, 0.5], col = (180, 245, 255) if rdif[1]>=0 else (255, 180, 210))
		if M.boton((posx+260, posy), (25,25), txt = "X", color = (150, 60, 70)):
			self.start_newmatch()
	def import_matches(self, filename):
		self.importing = True
		df = pd.read_csv(filename, sep="\t")
		self.name_to_id = {pl.name.lower() : pl.id for pl in self.players}
		self.import_list = []
		self.denied_list = []
		for (idx, line) in df.iterrows():
			if line["player_1"].lower() in self.name_to_id and line["player_2"].lower() in self.name_to_id:
				self.import_list.append((
					self.name_to_id[line["player_1"].lower()], self.name_to_id[line["player_2"].lower()], 
					line["score_1"], line["score_2"], line["replay"], 
				))
			else:
				self.denied_list += [name.lower() for name in line[["player_1", "player_2"]] if not name.lower() in self.name_to_id]
					
		self.denied_list = sorted(list(set(self.denied_list)))
		
		self.newmatch_mtype = 1
		self.newmatch_eventid = 0
		self.event_list = [ev.name for ev in self.events] + ["---sin evento---"]
	def import_matches_confirm(self):
		self.importing = False
		eventid = self.events[self.newmatch_eventid].id if self.newmatch_eventid < len(self.events) else None
		print("Importando...")
		bar = tqdm(range(len(self.import_list)))
		for ids in self.import_list:
			match_id = max(self.allmatches.keys())+1
			newmatch_toadd = Match(self, match_id, [ids[0], ids[1]], [ids[2], ids[3]], [0,0], [0,0], 3, self.newmatch_mtype,
					eventid, datetime.datetime.now() if eventid is None else self.allevents[eventid].timestamp, ids[4])
			newmatch_toadd.fight()
			newmatch_toadd.submit()
			bar.update()
	def show_importing(self, M, wheel = 1, posx = 500, posy = 80):
		endx=posx+740
		M.wheeler[wheel][0]=[posx, endx]
		M.wheeler[wheel][1]=min(M.wheeler[wheel][1], 0)
		base=posy+M.wheeler[wheel][1]
		M.text("Importando Matches desde archivo", [posx + 350, base-40], textalign=[0.5, 0.5], col=white, size=28)
		M.text(f"Número de matches a agregar: {len(self.import_list)}", (posx+20, base), textalign = [0.0, 0.5], col = white, size = 20)
		M.text("Los siguientes nombres no se encontraron en la lista de jugadores:", (posx+20, base+30), textalign = [0.0, 0.5], col = white, size = 20)
		
		self.newmatch_mtype = M.numboton(self.newmatch_mtype-1, (posx+100, base+60), (150, 30), rad=20, txt=["Ranked", "Tournament"], 
					                     color=[white, (255, 180, 0)], textsize=20) + 1
		self.newmatch_eventid = M.numboton(self.newmatch_eventid, (posx+380, base+60), (380, 30), rad=0, txt=self.event_list,
					                     color=[bg1], textsize=16, textalign = [0, 0.5])
		if M.k_d or M.k_u:
			self.newmatch_eventid = (self.newmatch_eventid + (1 if M.k_d else -1)) % len(self.event_list)
		
		base += 100
		for name in self.denied_list:
			M.text(name, (posx+60, base), textalign = [0.0, 0.5], col = white, size = 20)
			base += 30
		
		if M.boton((posx + 100, base+30), (150, 40), txt="Cancelar", rad = 20, color = (90, 90, 90)):
			self.importing = False
		if M.boton((posx + 270, base+30), (150, 40), txt="Confirmar", rad = 20, color = (150, 60, 70)):
			self.import_matches_confirm()
	def fill_ranking(self):
		for pl in self.allplayers.values():
			stmt = update(AppPlayer).where(AppPlayer.id == pl.id).values(ranking_alternative = pl.elo)
			result = self.session.execute(stmt)
		self.unsaved = True
		#self.session.commit()
	def historic_ranking(self, enforce = False, min_matches = 10):
		if enforce or self.ranking_matrix is None:
			self.elo_matrix = np.zeros((len(self.players), len(self.matches)+1), dtype = float)
			self.elo_matrix[:, 0] = [pl.elo for pl in self.players]
			self.dates = np.array([ma.timestamp.date() for ma in self.matches])
			for m, match in enumerate(self.matches, 1):
				for p, id in enumerate(match.ids):
					self.elo_matrix[self.id_to_rank[id], m] = -match.rdif[p]
			self.elo_matrix = np.cumsum(self.elo_matrix, axis=1)
			
			unique_dates = np.sort(np.unique(self.dates, return_index = True)[1])
			self.dates = self.dates[unique_dates]
			self.elo_matrix = self.elo_matrix[:, unique_dates]
			
			for p, pl in enumerate(self.players):
				if pl.active_since is None or sum(pl.id in ma.ids for ma in self.matches) < min_matches + 1:
					self.elo_matrix[p, :] = np.nan
				else:
					self.elo_matrix[p, self.dates < pl.active_since] = np.nan
			self.ranking_matrix = np.argsort(np.argsort(-self.elo_matrix, axis=0), axis=0)+1
			self.ranking_matrix = np.where(np.isnan(self.elo_matrix), np.nan, self.ranking_matrix)
	def make_positioning(self):
		for pl in self.allplayers.values():
			stmt = update(AppPlayer).where(AppPlayer.id == pl.id).values(positioning = max(10 - len([1 for match in self.matches if pl.id in match.ids]), 0))
			result = self.session.execute(stmt)
		self.unsaved = True
		#self.session.commit()
	def update(self, current_update = None):
		global_factor = min(max(1.5 + (np.mean([pl.elo for pl in self.players])-1000)/100, 0), 1)
		current_update = datetime.datetime.now() if current_update is None else current_update
		if self.last_update is None:
			self.last_update = datetime.datetime.now() -  datetime.timedelta(days=300)
		def update_player(player):
			alldates = sorted([match.timestamp for match in self.matches if player.id in match.ids])
			dates = [date for date in alldates if date >self.last_update and date < current_update]
			dates.append(current_update)
			bottom = max(self.last_update, alldates[0]) if len(alldates)>0 else self.last_update
			player.days_remaining = 180 if player.days_remaining is None else player.days_remaining
			
			#print("Elo inicial", player.elo, "Fecha inicial", bottom)
			
			while len(dates)>0:
				if player.days_remaining > 0:
					if (dates[0] - bottom).days > player.days_remaining:
						bottom = bottom + datetime.timedelta(player.days_remaining)
						player.days_remaining = 0
						player.disabled = 1
						#print("Days over", bottom)
					else:
						player.days_remaining -= (dates[0] - bottom).days
						bottom = dates[0]
						player.disabled = 0
						#print("Days recovered", bottom, "Días:", player.days_remaining)
						if len(dates) > 1:
							player.days_remaining = min(player.days_remaining + 80, 180)
						dates = dates[1:]
				else:
					player.days_remaining = 0
					player.disabled = 1
					bonus = player.elo - player.elo_alt
					if bonus > -100:
						rate, limit = (0.3*global_factor, -50) if bonus > -50 else (0.2*global_factor, -100)
						if bonus - rate * (dates[0] - bottom).days <= limit:
							bottom = bottom + datetime.timedelta( (bonus-limit)/rate )
							player.elo = player.elo_alt +limit -0.01
							#print(limit, "loss over", bottom, "Bonus:", player.elo - player.elo_alt)
						else:
							player.elo -= rate * (dates[0] - bottom).days
							bottom = dates[0]
							if len(dates) > 1:
								player.days_remaining = 80
								player.disabled = 0
							#print(limit, "loss interrupted", bottom, "Bonus:",player.elo - player.elo_alt)
							dates = dates[1:]
					else:
						bottom = dates[0]
						#print("Bottom pit interrupted", bottom, "Bonus:", player.elo - player.elo_alt)
						if len(dates) > 1:
							player.days_remaining = 80
							player.disabled = 0
						dates = dates[1:]
							
							
		for player in self.players:
			update_player(player)
			stmt = update(AppPlayer).where(AppPlayer.id == player.id).values(ranking = player.elo, disabled = player.disabled, days_remaining = player.days_remaining)
			result = self.session.execute(stmt)
		
		stmt = update(AppLeague).where(AppLeague.id == 3).values(last_update = current_update)
		result = self.session.execute(stmt)
		self.unsaved = True
		
		self.last_update = current_update
		self.load_players()
