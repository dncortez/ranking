
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
