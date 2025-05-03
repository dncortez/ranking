import pygame as pg
import numpy as np
import pandas as pd
import sys
import time
import datetime
import copy
import re
import os
import pyperclip
from tqdm.auto import tqdm
from sqlalchemy import create_engine, insert, update, delete
from sqlalchemy.orm import Session
from models import *
import matplotlib.pyplot as plt

CHAR_NAMES = {1:"ken", 2: "makoto", 3: "oro", 4: "yun", 5: "dudley", 6: "gouki", 7: "chun-li", 8: "urien",
			  9: "alex", 10: "elena", 11: "gill", 12: "hugo", 13: "ibuki", 14: "necro", 15: "q", 16: "remy", 
			  17: "ryu", 18: "sean", 19: "twelve", 20: "yang"}

CHAR_IMGS     = {key:pg.image.load("data/"+CHAR_NAMES[key]+    ".png") for key in CHAR_NAMES}
CHAR_IMGS_BIG = {key:pg.image.load("data/"+CHAR_NAMES[key]+"_big.png") for key in CHAR_NAMES}
CHAR_SELECT   = [[ 9, 18, 13, 14,  8,  6],
                 [20, 19,  2,  7, 15, 16,  4],
				 [ 1, 12, 10,  5,  3, 17, 11]]

#TODO: Especificar nombre de Fightcade
#TODO: Statistics: Filtrar por tiempo (historic / 1 año)
#TODO: Statistics: Winrate por posición
#TODO: Statistics: Ver custom MU
#TODO: Make event
#TODO: Auto Tournament

pg.init()

default_font = 'freesansbold.ttf'

# Create the window, saving it to a variable.
screen = pg.display.set_mode((1700, 1000), pg.RESIZABLE)
pg.display.set_caption("Example resizable window")


def plussign(number):
	return f"{'+' if number>0 else ''}{number:.1f}"
def in_rect(coord, c1, c2, corners=0):
	lim_min, lim_max = ([int(c1[0]-c2[0]/2), int(c1[1]-c2[1]/2)], [c1[0]+c2[0]/2, c1[1]+c2[1]/2]) if corners==0 else ((c1, [c1[0]+c2[0], c1[1]+c2[1]]) if corners==1 else (c1, c2))
	return coord[0]>=lim_min[0] and coord[1]>=lim_min[1] and coord[0]<=lim_max[0] and coord[1]<=lim_max[1]
def col_pon(C1, C2, fac):
	return [c1*(1-fac)+c2*fac for c1, c2 in zip(C1, C2)]
def col_bg(bg):
	return (0, 0, 0) if bg[0]*0.3+bg[1]*0.55+bg[2]*0.15>130 else (255, 255, 255)
def paint_plot(ax, col):
	ax.xaxis.label.set_color(col)       
	ax.yaxis.label.set_color(col)  
	ax.tick_params(axis='x', colors=col) 
	ax.tick_params(axis='y', colors=col)

	ax.spines['left'].set_color(col) 
	ax.spines['top'].set_color(col) 
	ax.spines['right'].set_color(col) 
	ax.spines['bottom'].set_color(col) 


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
		

bg1=(20, 30, 35)
bg2=(45, 65, 75)
bg3=(70, 85, 95)
bot0= (90, 130, 140)
white=(255, 255, 255)
black=(0, 0, 0)

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
class Event:
	def __init__(self, P, id, name, league_id, champion_id, timestamp):
		self.P, self.id, self.name, self.league_id, self.champion_id, self.timestamp = P, id, name, league_id, champion_id, timestamp
		self.champion = None if champion_id is None else P.allplayers[champion_id] 
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
		


M=MyModule(screen)
R = Ranker()


M.bg=bg1
M.wheeler=[[[200,500],0], [[500,800],0]] 

#for match in matches[:100]:
#	print(match.p1.name, match.p2.name, match.timestamp)

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

SR = semi_robin()



searchbar=textbox(M, [100, 70], [180, 30], text="", pattern=True, color=bg2)  
filebar  =textbox(M, [100, 860], [180, 30], text="", pattern=False, color=bg2)  
dd=textbox(M, [40, 840],  [30, 25], text=str(datetime.datetime.now().day), numeric=True, color=white)  
mm=textbox(M, [80, 840], [30, 25], text=str(datetime.datetime.now().month), numeric=True, color=white)  
yy=textbox(M, [135, 840], [60, 25], text=str(datetime.datetime.now().year), numeric=True, color=white)
error_time = time.time()-1000

oli=True

etapa=0

start = time.time()

while True:
	M.begin_loop()
	#M.boton((200,200), (300,100), rad=30, txt="Wena")
	M.rect([0,0], [200, M.height], corners=1, color=bg3) #M.s.get_rect()[1]
	
	etapa=0 if M.checkboton(etapa==0, (100,130), (180,40), rad=30, txt=["Ranking", "Ranking"],         color=[bg3, bot0], border=[black, black], clarity=[0, .6], textsize=20) else etapa
	etapa=1 if M.checkboton(etapa==1, (100,190), (180,40), rad=30, txt=["Matches", "Matches"],         color=[bg3, bot0], border=[black, black], clarity=[0, .6], textsize=20) else etapa
	etapa=2 if M.checkboton(etapa==2, (100,250), (180,40), rad=30, txt=["Player", "Player"],           color=[bg3, bot0], border=[black, black], clarity=[0, .6], textsize=20) else etapa
	etapa=3 if M.checkboton(etapa==3, (100,310), (180,40), rad=30, txt=["Tournaments", "Tournaments"], color=[bg3, bot0], border=[black, black], clarity=[0, .6], textsize=20) else etapa
	etapa=4 if M.checkboton(etapa==4, (100,410), (180,40), rad=30, txt=["Seeding", "Seeding"],         color=[bg3, bot0], border=[black, black], clarity=[0, .6], textsize=20) else etapa
	
	
	R.show_ranking(M, fullmode = etapa==0)
	if M.enter and searchbar.clicked and len(searchbar.text)> 0:
		R.selected = R.smallest_shown
		if R.selected is None and etapa==4:
			R.selected = Player(R, -1, searchbar.text, -1000, 0, 3, 0, 0, 180, -1000, 10)
		searchbar.reset()
	if etapa == 0:
		dd.color, mm.color, yy.color = [col_pon(white, (255, 100, 100), max((error_time - time.time())/0.5, 0) )]*3
		dd.show()
		mm.show()
		yy.show()
		if M.boton((100,800), (180,40), rad=30, txt="Update", color = bot0, border = black):
			try:
				current_update = datetime.datetime.strptime(f"{dd.number:0>2} {mm.number:0>2} {yy.number}", "%d %m %Y")
				R.update(current_update)
			except:
				error_time = time.time() + 0.5
		M.text(f"Last update: {R.last_update.date()}", [100, 760], col="white", size=14)
		if R.selected is not None:
			etapa = 2
	if etapa == 1:
		if R.importing:
			R.show_importing(M)
		else:
			R.show_matches(M)
		filebar.show()
		if M.boton((100,800), (180,40), rad=30, txt="Importar", color = bot0, border = black) and os.path.exists(filebar.text):
			R.import_matches(filebar.text)
			filebar.reset()
		if filebar.text and not os.path.exists(filebar.text):
			M.text("Archivo incorrecto", (20, 890), textalign =[0, 0.5], col = (190, 25, 15), size=18)
			
	else:
		R.start_newmatch()
	if etapa == 2:
		if M.boton((100,800), (180,40), rad=30, txt="+ Jugador", color = bot0, border = black):
			R.start_newplayer()
		if R.selected_id is not None:
			R.allplayers[R.selected_id].show(M, posy = 60, posx = 460)
	if etapa == 4:
		if R.selected is not None and R.selected not in SR.players:
			SR.add_player(R.selected)
		R.show_ranking(M, wheel =1, posx=650, posy=120, fullmode=False, players = SR.players)
		M.text("Jugadores Presentes", [670, 40 + M.wheeler[1][1]], textalign=[0, 0.5], col=white, size=32)
		if R.selected is not None:
			SR.delete_player(R.selected)
			
		SR.plot(M, (1300, 600))
		
		if M.boton((100,600), (180,40), rad=30, txt="Copy Players", color = bot0):
			SR.get_players()
		if M.boton((100,660), (180,40), rad=30, txt="Copy Matches", color = bot0):
			SR.get_rounds()
	
	if R.unsaved:
		if M.boton((100,940), (180,40), rad=30, txt="Save Changes", color = (255, 180, 0), textsize = 18):
			R.commit()
	
	M.text("Search box", [100, 40], col=white, size=24)
	psearch=searchbar.text
	searchbar.show()
	if psearch!=searchbar.text: M.wheeler=[[w[0], 0] for w in M.wheeler]
	
	pg.display.update() 
	M.end_loop()




pass

