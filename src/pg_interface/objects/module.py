class MyModule:
	def __init__(self, screen, fps=60):
		self.s=screen
		self.mouse_pressed=[False]*2
		self.mouse_clicked=[False]*2
		self.typing=""
		self.enter, self.backspace, self.lshift, self.lctrl, self.k_d, self.k_u, self.k_l, self.k_r =[False]*8
		self.key={key:False for key in "QWERTYUIOPASDFGHJKLÑZXCVBNMqwertyuiopasdfghjklñzxcvbnm <>,;.:-_|1234567890áéíóúäëïöüÁÉÍÓÚÄËÏÖÜ'¿¬°!\"\@#$%&/()=?\\¡\t\n´+}{¨*][~`^"}
		self.bg=(255, 255, 255)
		self.fonts={}
		self.pframe_time=time.time()
		self.frame_time=time.time()
		self.fps=fps
		self.width, self.height=self.s.get_rect()[2:]
		self.wheeler=[]
		self.wheel_sensitivity=30
	def text(self, txt, center, textalign=[0.5, 0.5], font=default_font, col=(0,0,0), size=20, returnmode=False, angle = 0):
		dic=self.fonts
		if not font in self.fonts:
			dic[font]={}
		dic=dic[font]
		if not size in dic:
			font=pg.font.Font(font, size)
			dic[size]=[font, {}]
		dic=dic[size]
		font=dic[0]
		if not col in dic[1]:
			dic[1][col]={}
		dic=dic[1][col]
		if txt in dic:
			text_render=dic[txt][0]
			dic[txt][1]=True
		else:
			text_render=font.render(txt, True, col_bg(self.s.get_at(center)) if col is None else col) 
			dic[txt]=[text_render, True]
		if angle != 0:
			text_render = pg.transform.rotate(text_render, angle)
		textRect=text_render.get_rect()
		textalign = [(textalign[0]-0.5) * font.size(txt)[0], (textalign[1]-0.5)*font.size(txt)[1]]
		textalign = [ textalign[0] * np.cos(-np.pi*angle/180) - textalign[1] * np.sin(-np.pi*angle/180), textalign[1] * np.cos(-np.pi*angle/180) + textalign[0] * np.sin(-np.pi*angle/180)]
		center=(center[0] - textalign[0], center[1] - textalign[1])
		textRect.center=(center)
		return textRect if returnmode else self.s.blit(text_render, textRect)
	def boton(self, coord, size, center=True, rad=10, txt="", color=(110, 130, 160), border=None, clarity=0.6, textsize=None, textalign = [0.5, 0.5]):
		coord=(coord[0]-size[0]/2, coord[1]-size[1]/2) if center else coord
		pg.draw.rect(self.s, color, coord+size, border_radius=rad)
		mouse_over=in_rect(pg.mouse.get_pos(), coord, size, corners=1) and self.s.get_at(pg.mouse.get_pos())==color 
		color_f=col_pon(color, (255, 255, 255), clarity) if mouse_over else color
		pg.draw.rect(self.s, color_f, coord+size, border_radius=rad)
		if not border is None: pg.draw.rect(self.s, border, coord+size, border_radius=rad, width=1)
		self.text(txt, (int(coord[0]+size[0]*(0.05+0.9*textalign[0])), int(coord[1]+size[1]*(0.05+0.9*textalign[1]))), 
						size=(int(size[1]*0.6)) if textsize is None else textsize, textalign=textalign, col=col_bg(color))
		return mouse_over and self.mouse_clicked[0]
	def checkboton(self, ret, coord, size, center=True, rad=10, txt=["", ""], color=[black, black], border=[None,None], clarity=[0.6, 0.6], textsize=None, textalign=[0.5, 0.5]):
		for r, t, c, b, cl in zip([True, False], txt, color, border, clarity):
			if ret==r and self.boton(coord, size, center=center, rad=rad, txt=t, color=c, border=b, clarity=cl, textsize=textsize, textalign=textalign):
				ret=not r
				break
		return ret
	def numboton(self, ret, coord, size, center=True, rad=10, txt=["", ""], color=[black, black], border=[None,None], clarity=[0.6, 0.6], textsize=None, textalign=[0.5, 0.5]):
		if self.boton(coord, size, center=center, rad=rad, txt =txt[ret%len(txt)], color=color[ret%len(color)], border=border[ret%len(border)], clarity=clarity[ret%len(clarity)], textsize=textsize, textalign=textalign):
			ret = (ret+1) % len(txt)
		return ret
	def image_boton(self, image, coord, size = None, center=True, clarity = 0.6):
		if size is not None:
			size[0] = round(image.get_size()[0]*size[1]/image.get_size()[1]) if size[0] is None else size[0]
			size[1] = round(image.get_size()[1]*size[0]/image.get_size()[0]) if size[1] is None else size[1]
			image = pg.transform.scale(image, size)
		image_white = image.copy()
		image_white.fill((255, 255, 255), special_flags=pg.BLEND_RGB_ADD)
		image_white.set_alpha(255*clarity)
		size = image.get_size()
		coord=(coord[0]-size[0]/2, coord[1]-size[1]/2) if center else coord
		self.s.blit(image, coord)
		img_mouse = (int(pg.mouse.get_pos()[0]-coord[0]), int(pg.mouse.get_pos()[1]-coord[1]))
		mouse_over=in_rect(img_mouse, [0,0], (size[0]-2, size[1]-2), corners=1) and self.s.get_at(pg.mouse.get_pos()) in (image.get_at(img_mouse), 
		             image.get_at((img_mouse[0], img_mouse[1]+1)), image.get_at((img_mouse[0]+1, img_mouse[1]+1)), image.get_at((img_mouse[0]+1, img_mouse[1])))
		if mouse_over:
			self.s.blit(image_white, coord)
		return mouse_over and self.mouse_clicked[0]
	def rect(self, c1, c2, color=(0, 0, 0), linewidth=0, corners=0, rad=0):
		low, size=([int(c1[0]-c2[0]/2), int(c1[1]-c2[1]/2)], c2) if corners==0 else ((c1, c2) if corners==1 else (c1, [c2[0]-c1[0], c2[1]-c1[1]]))
		pg.draw.rect(self.s, color, low+size, width=linewidth, border_radius=rad)
	def phase(self, cycle, delay=0):
		return int((self.frame_time-delay)/cycle)>int((self.pframe_time-delay)/cycle)
	def begin_loop(self):
		self.pframe_time=self.frame_time
		self.frame_time=time.time()
		self.s.fill(self.bg)
		self.width, self.height=self.s.get_rect()[2:]
		self.mouse_clicked=pg.mouse.get_pressed()[0] and not M.mouse_pressed[0], pg.mouse.get_pressed()[2] and not M.mouse_pressed[1]
		self.mouse_pressed= pg.mouse.get_pressed()[0], pg.mouse.get_pressed()[2]
		if self.phase(5, 2.5):
			for font in self.fonts: 
				for size in self.fonts[font]:
					for col in self.fonts[font][size][1]:
						for txt in self.fonts[font][size][1][col]: self.fonts[font][size][1][col][txt][1]=False
		for event in pg.event.get():
			if event.type == pg.QUIT:
				pg.quit()
				sys.exit()
			elif event.type == pg.KEYDOWN:
				if event.key == pg.K_ESCAPE:
					pg.quit()
					sys.exit()
				elif event.key == pg.K_RETURN:
					self.enter=True
				elif event.key == pg.K_BACKSPACE:
					self.backspace=True
				elif event.key == pg.K_LSHIFT:
					self.lshift=True
				elif event.key == pg.K_LCTRL:
					self.lctrl=True
				elif event.key == pg.K_UP:
					self.k_u=True
				elif event.key == pg.K_DOWN:
					self.k_d=True
				elif event.key == pg.K_LEFT:
					self.k_l=True
				elif event.key == pg.K_RIGHT:
					self.k_r=True
				elif len(event.unicode)>0:
					self.typing+= event.unicode
					self.key[event.unicode]=True
			elif event.type==pg.MOUSEWHEEL:
				for window in self.wheeler:
					if window[0][0] <= pg.mouse.get_pos()[0] <= window[0][1]:
						window[1]+=event.y*self.wheel_sensitivity
			elif event.type==pg.KEYUP:
				if len(event.unicode)>0:
					self.key[event.unicode]=True
			elif event.type == pg.VIDEORESIZE:
				# There's some code to add back window content here.
				self.s = pg.display.set_mode((event.w, event.h), pg.RESIZABLE)
	def end_loop(self):
		self.typing=""
		self.backspace=False
		self.lshift=False
		self.lctrl=False
		self.enter=False
		self.k_u=False
		self.k_d=False
		self.k_l=False
		self.k_r=False
		if self.phase(5):
			for font in self.fonts: 
				for size in self.fonts[font]:
					for col in self.fonts[font][size][1]:
						to_del=[]
						for txt in self.fonts[font][size][1][col]:
							if not self.fonts[font][size][1][col][txt][1]:
								to_del.append(txt)
						for txt in to_del:
							del self.fonts[font][size][1][col][txt]
		time.sleep(max(1.0/self.fps-(time.time()-self.frame_time), 0))

