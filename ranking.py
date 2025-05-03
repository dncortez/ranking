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


bg1=(20, 30, 35)
bg2=(45, 65, 75)
bg3=(70, 85, 95)
bot0= (90, 130, 140)
white=(255, 255, 255)
black=(0, 0, 0)


		


M=MyModule(screen)
R = Ranker()


M.bg=bg1
M.wheeler=[[[200,500],0], [[500,800],0]] 

#for match in matches[:100]:
#	print(match.p1.name, match.p2.name, match.timestamp)



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

