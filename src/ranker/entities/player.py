class Player:
	def __init__(self, P, id, name, elo, char, league, country, disabled, days_remaining, elo_alt, positioning):
		self.P, self.id, self.name, self.elo, self.char = P, id, name, float(elo), char
		self.league, self.country, self.disabled = league, country, disabled
		self.elo_alt, self.days_remaining, self.positioning = float(elo_alt), days_remaining, positioning
		self.search=name.lower()
		self.editing, self.stats, self.name_already_exists = False, False, False
		self.new_name, self.new_char = None, self.char
		self.allmatches, self.active_since = None, None
	@property
	def image(self):
		return CHAR_IMGS[self.char]
	def profile(self, M, center, height = 26):
		width = height * 2.115
		profile = pg.transform.flip(pg.transform.scale(
			self.image, [round(self.image.get_size()[0]*width/self.image.get_size()[1]), width]), True, False)
		M.s.blit(profile, center, (0, height/2, 2*width, height))
	def get_stats(self, enforce = False):
		if self.allmatches is None or enforce:
			self.allmatches = [match for match in self.P.allmatches.values() if self.id in match.ids]
			self.n_wins = len([match for match in self.allmatches if match.ids[match.score.index(max(match.score))]==self.id ])
			self.n_loss = len(self.allmatches) - self.n_wins
			self.win_rate = self.n_wins / len(self.allmatches) if len(self.allmatches) >0 else 0
			self.tormatches = [match for match in self.allmatches if match.matchtype == 2]
			self.n_wins_t = len([match for match in self.tormatches if match.ids[match.score.index(max(match.score))]==self.id])
			self.n_loss_t = len(self.tormatches) - self.n_wins_t
			self.win_rate_t = (self.n_wins_t / len(self.tormatches)) if len(self.tormatches) >0 else 0
	def get_superstats(self):
		self.get_stats(enforce = True)
		
		self.allmatches.sort(key = lambda X: X.timestamp, reverse = True)
		dates = [match.timestamp for match in self.allmatches]
		elos = [self.elo]
		for match in self.allmatches[:-1]:
			elos.append(elos[-1] - match.rdif[match.ids.index(self.id)])
		
		self.P.historic_ranking()
		ranks = self.P.ranking_matrix[self.P.id_to_rank[self.id]]
		dates2 = self.P.dates[~np.isnan(ranks)]
		ranks  =        ranks[~np.isnan(ranks)]
		
		fig, ax = plt.subplots(figsize = (10,2.5))
		ax.set_title("Ranking histórico", color="w")
		ax.plot(dates, elos, color = (0.5, 1, 0.6), marker = "o", markersize = 3, label = "Elo")
		ax.set_ylabel("Elo")
		ax2 = ax.twinx()
		ax2.plot(dates2, ranks, color = (0.4, 0.7, 0.9), marker = "o", markersize=3, label = "Posición")
		ax2.set_ylabel("Posición")
		ax2.invert_yaxis()
		paint_plot(ax, "w")
		paint_plot(ax2, "w")
		handles, labels =np.squeeze(list(zip(ax.get_legend_handles_labels(), ax2.get_legend_handles_labels())))
		legend = plt.legend(handles, labels, )
		legend.get_frame().set_color("black")
		legend.get_frame().set_alpha(0.6)
		[text.set_color("w") for text in legend.get_texts()]
		plt.xticks(rotation = 30)
		#fig.canvas.draw()
		#grafico = pg.image.frombuffer(fig.canvas.tostring_argb(), (fig.canvas.width(), fig.canvas.height()), "ARGB")
		fig.savefig("plot.png", transparent = True, bbox_inches = "tight")
		self.grafico = pg.image.load("plot.png")
		
		self.rivals = {}
		for match in self.allmatches:
			other = match.other(self.id, player=True)
			index = match.ids.index(self.id)
			if other.name not in self.rivals:
				self.rivals[other.name] = Matchup(self, other)
			mu = self.rivals[other.name]
			mu.matches.append(match)
			mu.elo_diff.append(match.rdif[index])
			mu.victorias += int(self.id == match.winner_id)
			
		self.panas      = [(mu, mu.partidas) for mu in self.rivals.values()]
		self.is_counter = [(mu, float(np.mean(mu.elo_diff))) for mu in self.rivals.values() if mu.partidas >=3]
		self.nemesis    = [(mu, mu.lossrate1*100, mu.winrate*100) for mu in self.rivals.values()]
		self.hijos      = [(mu, mu.winrate1*100, mu.winrate*100) for mu in self.rivals.values()]
		self.verdugos   = [(mu, mu.derrotas) for mu in self.rivals.values()]
		self.masacrados = [(mu, mu.victorias) for mu in self.rivals.values()]
		for rivals in (self.panas, self.is_counter, self.nemesis, self.hijos, self.verdugos, self.masacrados):
			rivals.sort(key = lambda x: x[1], reverse = True)
		self.counters = list(reversed(self.is_counter))
	def show(self, M, posx = 410, posy=80):
		self.get_stats()
		M.text(self.name, [posx+20, posy+20], textalign=[0, 0.5], col=white, size=32) 
		M.s.blit(pg.transform.flip(self.image, True, False), (posx+20, posy+50))
		M.text("Main: "+CHAR_NAMES[self.char].capitalize(), [posx+20, posy+200], textalign =[0, 0.5], col=white, size=18)
		M.text(f"ID: {self.id}", [posx+300, posy+50], textalign =[0, 0.5], col=white, size=18)
		M.text(f"Ranking: {self.elo:.1f}", [posx+300, posy+80], textalign =[0, 0.5], col=white, size=18)
		M.text(f"Bonus: {plussign(self.elo - self.elo_alt)}", [posx+300, posy+110], textalign =[0, 0.5], col=(180, 245, 255) if self.elo >= self.elo_alt else (255, 180, 210), size=18)
		M.text(f"Posicionamiento: {self.positioning}", [posx+300, posy+140], textalign =[0, 0.5], col=white, size=18)
		M.text("Jugador " +("Activo" if self.disabled == 0 else "Ausente"), [posx+300, posy+170], textalign =[0, 0.5], col = (130, 240, 170) if self.disabled == 0 else (150,150,150), size=18)
		
		M.text(f"N° Partidas: {len(self.allmatches)}",                            [posx+580, posy+50],  textalign =[0, 0.5], col=white, size=18)
		M.text(f"Victorias / Derrotas: {self.n_wins} / {self.n_loss}",            [posx+580, posy+80],  textalign =[0, 0.5], col=white, size=18)
		M.text(f"% Victorias: {self.win_rate*100:.1f}%",                          [posx+580, posy+110], textalign =[0, 0.5], col=white, size=18)
		M.text(f"N° Partidas torneo: {len(self.tormatches)}",                     [posx+580, posy+140], textalign =[0, 0.5], col=white, size=18)
		M.text(f"Victorias / Derrotas torneo: {self.n_wins_t} / {self.n_loss_t}", [posx+580, posy+170], textalign =[0, 0.5], col=white, size=18)
		M.text(f"% Victorias torneo: {self.win_rate_t*100:.1f}%",                 [posx+580, posy+200], textalign =[0, 0.5], col=white, size=18)
		
		if self.disabled == 0:
			M.text(f"Días para ausente: {self.days_remaining}", [posx+300, posy+200], textalign =[0, 0.5], col = white, size=18)
		self.editing = M.checkboton(self.editing, (posx+ 110, posy + 240), (180,35), rad=30, txt=["Editar", "Editar"], color=[bg3, bot0], border=[black, black], clarity=[0, .6], textsize=20)
		if self.editing:
			self.stats = False
			if self.new_name is None:
				self.new_name = textbox(M, [0,0], [300, 30], color=white, text=self.name)
			M.text("Nuevo Nick:", [posx+20, posy+290], textalign =[0, 0.5], col = white, size=18)
			self.new_name.show(center = [posx+300, posy + 290])
			
			M.text("Nuevo Main:", [posx+20, posy+340], textalign =[0, 0.5], col = white, size=18)
			M.s.blit(pg.transform.flip(pg.transform.scale(CHAR_IMGS[self.new_char], [100, round(self.image.get_size()[1]*100/self.image.get_size()[0])]), True, False), (posx+20, posy+355))
			M.text(CHAR_NAMES[self.new_char].capitalize(), [posx+70, posy+470], textalign =[0.5, 0.5], col = white, size=18)
			
			base_csx, base_csy = posx+160, posy+350
			for r, row in enumerate(CHAR_SELECT):
				for c, char in enumerate(row):
					shift = ((r+1)%2) * 25
					if M.image_boton(CHAR_IMGS[char], [base_csx + c*50 + shift, base_csy + r*50], [50, None]):
						self.new_char = char
			
			if self.new_name.text != self.name or self.char != self.new_char:
				if M.boton((posx+100, posy+520), (160, 40), txt = "Guardar", rad=30, color=bot0, clarity=0.3):
					if self.new_name.text in [pl.name for pl in self.P.allplayers.values()]:
						self.name_already_exists = self.new_name.text
					else:
						if self == self.P.new_player:
							stmt = insert(AppPlayer).values(id = self.id, nickname = self.new_name.text, ranking = self.elo, main_id = self.new_char, league_id = 3,
															country_id = 1, disabled = 0, days_remaining = 180, ranking_alternative = self.elo, positioning = 10)
							self.P.new_player = None
						else:
							stmt = update(AppPlayer).where(AppPlayer.id == self.id).values(nickname = self.new_name.text, main_id = self.new_char)
						result = self.P.session.execute(stmt)
						self.P.load_players()
						self.P.unsaved = True
				if self.new_name.text == self.name_already_exists:
					M.text("El nombre ya existe!", [posx+20, posy+552], textalign =[0, 0.5], col = (190, 25, 15), size=18)
		if len(self.allmatches)>0:
			if M.boton((posx+310, posy+240), (180, 35), txt = "+ Estadísticas", rad=30, color=bot0, clarity=0.3):
				self.stats = True
				self.editing = False
				self.get_superstats()
		if self.stats:
			M.s.blit(self.grafico, (posx+20, posy+260))
			
			for r, (titulo, unit, rivals, color) in enumerate(zip(
				["Más jugado", "Némesis", "Hijos", "Verdugos", "Masacrados", "Counters", "Counter de"],
				["#", "%WR", "%WR", "#Loss", "#Wins", "Elo/n", "Elo/n"],
				[self.panas, self.nemesis, self.hijos, self.verdugos, self.masacrados, self.counters, self.is_counter],
				[white, (255, 180, 210), (180, 245, 255), (255, 180, 210), (180, 245, 255), (255, 180, 210), (180, 245, 255)]
			)):
				posx_r = posx + 20 + 230 * (r%4)
				posy_r = posy + 540 + 180 * (r//4)
				M.text(titulo, [posx_r+40,  posy_r], textalign = [0, 0.5], col = white, size = 20)
				M.text(unit,   [posx_r+180, posy_r], textalign = [0, 0.5], col = white, size = 15)
				for i, mu_metric in enumerate(rivals[:5]):
					mu = mu_metric[0]
					metric = mu_metric[-1]
					mu.rival.profile(M,[posx_r, posy_r + 30 + i*25 -11], 22)
					M.text(mu.rival.name, [posx_r+60, posy_r + 30 + i*25], textalign = [0, 0.5], col = white, size = 16)
					M.rect([posx_r+170, posy_r + 12 + i*25], [posx_r + 220, posy_r + 43 + i*25], corners=1, color=bg1) 
					M.text(f"{metric:.1f}" if type(metric) is float else str(metric), [posx_r+ 180, posy_r + 30 + i*25], textalign = [0, 0.5], col = color, size = 16)
