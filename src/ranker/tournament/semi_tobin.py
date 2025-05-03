class semi_robin:
	def __init__(self):
		self.players_pos = []
		self.players = []
		self.players_ordered = []
	def add_player(self, player):
		self.players.append(player)
		if len(self.players_pos) == 0:
			self.players_pos = [0]
		else:
			sums = [this + next for this, next in zip(self.players_pos, self.players_pos[1:]+[self.players_pos[0]])]
			self.players_pos.insert(sums.index(min(sums))+1, len(self.players_pos))
		self.players.sort(reverse = True, key = lambda X: X.elo)
		self.players_ordered = [self.players[i] for i in self.players_pos]
		self.get_players()
	def delete_player(self, player):
		self.players.remove(player)
		self.players_pos.remove(max(self.players_pos))
		self.players_ordered = [self.players[i] for i in self.players_pos]
	def plot(self, M, center, radius = 160):
		for i, player in enumerate(self.players_ordered):
			angle = 2 * np.pi * i/len(self.players)
			if (angle +np.pi/2) % (2*np.pi) < np.pi:
				M.text(player.name, (center[0] + radius*np.cos(angle), center[1] + radius*np.sin(angle)), textalign = [0, 0.5], col = white, angle = -angle*180/np.pi)
			else:
				M.text(player.name, (center[0] + radius*np.cos(angle), center[1] + radius*np.sin(angle)), textalign = [1, 0.5], col = white, angle = 180-angle*180/np.pi)
	def get_players(self):
		pyperclip.copy("\n".join(player.name for player in self.players_ordered))
	def fill_scheme_1(self, list, start=0):
		for st in range(start, start + len(list)):
			I = (np.arange(4) + st) % len(list)
			if np.all(list[I] == None):
				list[I] = np.flip(I)
		return list
	def fill_scheme_2(self, list, start=0):
		for st in range(start, start + len(list)):
			I = (np.arange(4) + st) % len(list)
			if np.all(list[I] == None):
				list[I] = I[2], I[3], I[0], I[1]
		return list
	def get_rounds(self):
		L = len(self.players)
		matches = np.full((L, 7), None)
		if L%4 == 0:
			matches[np.arange(L), 0] = self.fill_scheme_1(np.full(L, None), 0)
			matches[np.arange(L), 1] = self.fill_scheme_1(np.full(L, None), 1)
			matches[np.arange(L), 2] = self.fill_scheme_1(np.full(L, None), 2)
			matches[np.arange(L), 3] = self.fill_scheme_1(np.full(L, None), 3)
			matches[np.arange(L), 4] = self.fill_scheme_2(np.full(L, None), 0)
			matches[np.arange(L), 5] = self.fill_scheme_2(np.full(L, None), 2)
		elif L%4 == 1:
			matches[np.arange(L), 0] = self.fill_scheme_1(np.full(L, None), 1)
			matches[np.arange(L), 1] = self.fill_scheme_1(np.full(L, None), 2)
			matches[np.arange(L), 2] = self.fill_scheme_1(np.full(L, None), 3)
			matches[np.arange(L), 3] = self.fill_scheme_1(np.full(L, None), 4)
			matches[np.arange(L), 4] = self.fill_scheme_2(np.full(L, None), 5)
			matches[np.arange(L), 5] = self.fill_scheme_2(np.full(L, None), 7)
			matches[:7, 6] = 3, 2, 1, 0, 6, None, 4
		elif L%4 == 2:
			lst = np.full(L, None)
			lst[[1,2]] = 2, 1
			matches[np.arange(L), 0] = self.fill_scheme_1(lst, 3)
			lst = np.full(L, None)
			lst[[2,3]] = 3, 2
			matches[np.arange(L), 1] = self.fill_scheme_1(lst, 4)
			lst = np.full(L, None)
			lst[[3,4]] = 4, 3
			matches[np.arange(L), 2] = self.fill_scheme_1(lst, 5)
			lst = np.full(L, None)
			lst[:6] = 3, 4, 5, 0, 1, 2
			matches[np.arange(L), 3] = self.fill_scheme_1(lst, 6)
			matches[np.arange(L), 4] = self.fill_scheme_2(np.full(L, None), 2)
			matches[np.arange(L), 5] = self.fill_scheme_2(np.full(L, None), 4)
			matches[:4, 6] = 2, 3, 0, 1
		elif L%4 == 3:
			lst = np.full(L, None)
			lst[[1,2]] = 2, 1
			matches[np.arange(L), 0] = self.fill_scheme_1(lst, 8)
			lst = np.full(L, None)
			lst[[2,3]] = 3, 2
			matches[np.arange(L), 1] = self.fill_scheme_1(lst, 9)
			lst = np.full(L, None)
			lst[[3,4]] = 4, 3
			matches[np.arange(L), 2] = self.fill_scheme_1(lst, 10)
			lst = np.full(L, None)
			lst[:6] = 3, 4, 5, 0, 1, 2
			matches[np.arange(L), 3] = self.fill_scheme_1(lst, 11)
			lst = np.full(L, None)
			lst[[3, 5]] = 5, 3
			matches[np.arange(L), 4] = self.fill_scheme_2(lst, 6)
			lst = np.full(L, None)
			lst[[5, 7]] = 7, 5
			matches[np.arange(L), 5] = self.fill_scheme_2(lst, 8)
			matches[4:11, 6] = 6, None, 4, 10, 9, 8, 7
		tocopy = "\n".join("\t".join("---" if m is None else self.players_ordered[m].name for m in M) for M in matches)
		pyperclip.copy(tocopy)