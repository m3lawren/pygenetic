#!/usr/bin/python

import Image
import ImageDraw

import pickle
import random

MAX_RADIUS = 1e1000
MIN_RADIUS = 3
CHG_RADIUS = 2

CHG_COORD = 2
EDGE_OVERLAP = 5

MIN_ALPHA = 31
MAX_ALPHA = 255
CHG_COLOR = 5

class ImageOrganism:
	"""An organism which attempts to approximate an image via translucent circles. Each element in the DNA consists of a 4-tuple (x, y, radius, (r, g, b, a))."""

	def __init__(self, size, dna):
		self.__score = -1
		self.__size = size 
		self.__dna = dna
		self.__image = None
		self.__mutations = [
			self.__mutation_physshift,
			self.__mutation_colshift,
			self.__mutation_swap,
			]

	def __get_dna(self):
		return self.__dna

	def __get_score(self):
		return self.__score

	def __get_size(self):
		return self.__size

	def __get_image(self):
		self.__render()
		return self.__image

	dna = property(fget=__get_dna, doc="""DNA string.""")
	score = property(fget=__get_score, doc="""Score of the picture.""")
	size = property(fget=__get_size, doc="""Size of the picture. (width, height)""")
	image = property(fget=__get_image, doc="""CIL Image""")

	def __mutation_swap(self):
		src_dna = random.randint(0, len(self.dna) - 1)
		dest_dna = random.randint(0, len(self.dna) - 1)
		if src_dna == dest_dna:
			return self
		new_dna = list(self.dna)
		tmp = new_dna[dest_dna]
		new_dna[dest_dna] = new_dna[src_dna]
		new_dna[src_dna] = tmp
		return ImageOrganism(self.size, new_dna)

	def __mutation_shift(self, which_dna, index, minv, maxv, maxchange):
		if len(self.dna) == 0:
			return self
		new_dna = list(self.dna)
		curcirc = self.dna[which_dna]
		if index == 2:
			rmin = -min(maxchange, curcirc[2] - minv, curcirc[0] + curcirc[2] - EDGE_OVERLAP, curcirc[1] + curcirc[2] - EDGE_OVERLAP)
			rmax = min(maxchange, maxv - curcirc[2], self.size[0] - curcirc[0] + curcirc[2] - EDGE_OVERLAP, self.size[1] - curcirc[1] + curcirc[2] - EDGE_OVERLAP)
		else:
			rmin = -min(maxchange, curcirc[index] + curcirc[2] - minv - EDGE_OVERLAP)
			rmax = min(maxchange, maxv - curcirc[index] + curcirc[2] - EDGE_OVERLAP)
		if rmin > rmax:
			if rmin > 0:
				rmax = rmin
			else:
				rmin = rmax
		change = [0,0,0]
		change[index] = random.randint(rmin, rmax)
		new_dna[which_dna] = (curcirc[0] + change[0], curcirc[1] + change[1], curcirc[2] + change[2], curcirc[3])
		return ImageOrganism(self.size, new_dna)

	def __mutation_shift_col(self, which_dna, index, minv, maxv, maxchange):
		if len(self.dna) == 0:
			return self
		new_dna = list(self.dna)
		curcirc = self.dna[which_dna]
		rmin = -min(maxchange, curcirc[3][index] - minv)
		rmax = min(maxchange, maxv - curcirc[3][index])
		if rmin > rmax:
			if rmin > 0:
				rmax = rmin
			else:
				rmin = rmax
		change = [0,0,0,0]
		change[index] = random.randint(rmin, rmax)
		new_dna[which_dna] = (curcirc[0], curcirc[1], curcirc[2], (curcirc[3][0] + change[0], curcirc[3][1] + change[1], curcirc[3][2] + change[2], curcirc[3][3] + change[3]))
		return ImageOrganism(self.size, new_dna)

	def __mutation_physshift(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		return self.__mutation_xshift(which_dna).__mutation_yshift(which_dna).__mutation_radshift(which_dna)

	def __mutation_colshift(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		return self.__mutation_rshift(which_dna).__mutation_gshift(which_dna).__mutation_bshift(which_dna).__mutation_ashift(which_dna)

	def __mutation_xshift(self, which_dna):
		return self.__mutation_shift(which_dna, 0, 0, self.size[0], CHG_COORD)

	def __mutation_yshift(self, which_dna):
		return self.__mutation_shift(which_dna, 1, 0, self.size[1], CHG_COORD)
	
	def __mutation_radshift(self, which_dna):
		return self.__mutation_shift(which_dna, 2, MIN_RADIUS, MAX_RADIUS, CHG_RADIUS)

	def __mutation_rshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 0, 0, 255, CHG_COLOR)

	def __mutation_gshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 1, 0, 255, CHG_COLOR)

	def __mutation_bshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 2, 0, 255, CHG_COLOR)

	def __mutation_ashift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 3, MIN_ALPHA, MAX_ALPHA, CHG_COLOR)

	def __render_circle(self, circle):
		image = Image.new("RGBA", self.size)
		draw = ImageDraw.Draw(image)

		left = circle[0] - circle[2]
		right = circle[0] + circle[2]
		top = circle[1] - circle[2]
		bottom = circle[1] + circle[2]
		draw.ellipse((left, top, right, bottom), fill=circle[3])

		return image

	def __render(self):
		if self.__image != None:
			return
		self.__image = Image.new("RGB", self.size)
		for circle in self.dna:
			rendered = self.__render_circle(circle)
			self.__image.paste(rendered, (0,0), rendered)

	def mutate(self):
		mutation = random.randint(0, len(self.__mutations) - 1)
		return self.__mutations[mutation]()

	def add_circle(self):
		circle = self.__generate_circle()
		return ImageOrganism(self.size, self.dna + [circle])

	def calc_score(self, target):
		data = list(self.image.getdata())
		assert len(data) == len(target)
		score = 0
		for index in range(len(data)):
			hsl = data[index] #rgb_to_hsl(data[index])
			score += (hsl[0] - target[index][0]) ** 2
			score += (hsl[1] - target[index][1]) ** 2
			score += (hsl[2] - target[index][2]) ** 2
		self.__score = score
		return self.score

	def __generate_circle(self):
		x = random.randint(0, self.size[0] - 1)
		y = random.randint(0, self.size[1] - 1)
		r = random.randint(5, 25)
		col = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(15, 191))
		return (x, y, r, col)

def rgb_to_hsl(rgb):
	norm_rgb = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
	maximum = max(norm_rgb)
	minimum = min(norm_rgb)
	l = (maximum + minimum) / 2.0
	if maximum == minimum:
		s = 0
	elif l <= 0.5:
		s = (maximum - minimum) / 2 * l
	else:
		s = (maximum - minimum) / (2 - 2 * l)
	if maximum == minimum:
		h = 0
	elif maximum == norm_rgb[0]:
		h = (60 * (norm_rgb[1] - norm_rgb[2]) / (maximum - minimum)) % 360
	elif maximum == norm_rgb[1]:
		h = 60 * (norm_rgb[2] - norm_rgb[0]) / (maximum - minimum) + 120
	elif maximum == norm_rgb[2]:
		h = 60 * (norm_rgb[0] - norm_rgb[1]) / (maximum - minimum) + 240
	return (h / 360.0, s, l)

def generator(dict):
	x = random.randint(0, dict['size'][0] - 1)
	y = random.randint(0, dict['size'][1] - 1)
	r = random.randint(dict['min_radius'], dict['max_radius'])
	col = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
	return ImageOrganism(dict['size'], [(x, y, r, col)])

target_image = Image.open('target.jpg').convert('RGB')
target_dna = list(target_image.getdata())

init_dna = []
x = 0
nc = 0
try:
	f = open('best.pickle', 'rb')
	init_dna, x = pickle.load(f)
	f.close()
except:
	pass

current = ImageOrganism(target_image.size, init_dna)
if len(current.dna) == 0:
	current = current.add_circle()
current.calc_score(target_dna)
while True:
	x += 1
	print 'Running iteration #' + str(x) + ' (nc: ' + str(nc) + ')'
	if nc >= 20 + len(current.dna) and len(current.dna) < 50:
		candidate = current.add_circle()
	else:
		candidate = current
		while candidate == current:
			candidate = current.mutate().mutate()
	candidate.calc_score(target_dna)

	if candidate.score < current.score:
		nc = 0
		current = candidate
		current.image.save('best.png', 'PNG')
		current.image.save('best.' + str(len(current.dna)) + '.png', 'PNG')
		f = open('best.dna', 'w')
		f.write(repr(current.dna) + '\n')
		f.close()
		f = open('best.pickle', 'wb')
		pickle.dump((current.dna, x), f)
		f.close()
		f = open('index.html', 'w')
		f.write('<html><body>')
		for index in range(len(current.dna)):
			f.write('<img src=\'best.' + str(index + 1) + '.png\' /><img src=\'target.jpg\' /><br />')
		f.write('</html></body>')
		f.close()
		print 'Replaced current with candidate. (Score: ' + str(candidate.score) + ', Num: ' + str(len(candidate.dna)) + ')'
	else:
		nc += 1
