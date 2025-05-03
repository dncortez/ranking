
class textbox:
	def __init__(self, module, center, size, color=(255,255,255), text="", numeric=False, pattern=False, num_float=False):
		self.M=module
		self.center=center
		self.size=size
		self.color=color
		self.corner=[int(c-s/2) for c, s in zip(self.center, self.size)]
		self.wrapped, self.wrappedB=["", ""]
		self.numeric=numeric
		self.pattern=pattern
		self.dot=False
		self.float=num_float
		self.ms, self.clicked, self.pclicked, self.pos_coord = 0, False, False, [0,0]
		self.textsize=16
		self.regex=""
		self.reset(text)
	@property
	def number(self):
		if self.numeric:
			return 0 if len(self.text)==0 else (float(self.text) if self.float else int(self.text))
	def reset(self, text=""):
		self.text=text
		self.pos=len(text)
		self.reseted = True
	def move(self, center=None, size=None):
		self.center=self.center if center is None else center
		self.size  =self.size   if size   is None else size
		self.corner=[int(c-s/2) for c, s in zip(self.center, self.size)]
	def show(self, center= None, size = None):
		if not (center is None and size is None):
			self.move(center = self.center if center is None else center, size = self.size if size is None else size)
		pg.draw.rect(self.M.s, self.color, self.corner+self.size)
		pg.draw.rect(self.M.s, (0, 0, 0), self.corner+self.size, width=1)
		if self.M.mouse_clicked[0]:
			if in_rect(pg.mouse.get_pos(), self.center, self.size):
				self.clicked, self.ms= True, time.time()
			else: self.clicked=False
		if self.numeric and self.pclicked and not self.clicked:
			self.reset(str(self.number))
		self.pclicked=self.clicked
		if self.reseted or (self.clicked and (len(self.M.typing)>0 or True in [self.M.k_l, self.M.k_r, self.M.backspace])):
			self.reseted = False
			if   self.M.k_l and self.pos>0: self.pos-=1
			elif self.M.k_r and self.pos<len(self.text): self.pos+=1
			elif self.M.backspace and self.pos>0:
				if self.text[self.pos-1]==".": self.dot=False
				self.text, self.pos= self.text[:self.pos-1]+self.text[self.pos:], self.pos-1
			elif len(self.M.typing)>0:
				for key in self.M.typing:
					if (not key in "´\t\n"):
						if (not self.numeric) or (key in "1234567890." and ((self.float and not self.dot) or key!=".")):
							self.text, self.pos= self.text[:self.pos]+key+self.text[self.pos:], self.pos+1
							if key==".": self.dot=True
						if self.numeric and key=="-":
							if self.pos>0 and self.text[0]=="-": self.text, self.pos= self.text[1:], self.pos-1
							else: self.text, self.pos= "-"+self.text, self.pos+1
			if self.pattern: self.regex=re.sub("[\[\]\(\)\\\{\}\*\?\^\$\+\|]", "", self.text).lower()
			lines = [self.text.split(" ")]
			while True:
				lines+=[[]]
				while self.M.text(" ".join(lines[-2]), [0,0], size=self.textsize, returnmode=True, col=col_bg(self.color))[2]   >self.size[0]-6:
					if len(lines[-2])==1:
						lines[-1]=[""]+lines[-1]
						while self.M.text(lines[-2][0], [0,0], size=self.textsize, returnmode=True, col=col_bg(self.color))[2]   >self.size[0]-6:
							lines[-1][0], lines[-2][0] = lines[-2][0][-1]+lines[-1][0], lines[-2][0][:-1] 
					else: lines[-1], lines[-2] = [lines[-2][-1]]+lines[-1], lines[-2][:-1] 
				if len(lines[-1])==0: break
			self.wrapped= [" ".join(line) for line in lines]
			for l in range(len(self.wrapped)):
				if len(" ".join(self.wrapped[:l+1]))>=self.pos:
					self.pos_coord=[l, self.M.text(self.wrapped[l][: self.pos - len(" ".join(self.wrapped[:l])) - (l>0) +sum([not " " in line for line in self.wrapped[:l]])], [0,0], size=self.textsize, returnmode=True, col=col_bg(self.color))[2] ]
					break
		for l in range(len(self.wrapped)):
			if (l+1)*self.textsize<=self.size[1]-6:
				self.M.text(self.wrapped[l], [self.corner[0]+3, self.corner[1]+3+l*self.textsize], textalign=[0, 0], size=self.textsize, col=col_bg(self.color))
		if (time.time()-self.ms)%1.2<.6 and self.clicked and (self.pos_coord[0]+1)*self.textsize<=self.size[1]-6:
			self.M.text("|", [self.corner[0]+3+self.pos_coord[1], self.corner[1]+3+self.pos_coord[0]*self.textsize], textalign=[0.5, 0], size=self.textsize, col=col_bg(self.color))
		
