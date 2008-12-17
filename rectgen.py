#!/usr/bin/python

import Image
import ImageDraw

import pickle
import random

MIN_SIZE = 2
CHG_SIZE = 2

CHG_COORD = 2
EDGE_OVERLAP = 5

MIN_ALPHA = 31
MAX_ALPHA = 255
CHG_COLOR = 5

class ImageOrganism:
	"""An organism which attempts to approximate an image via translucent rectangles. Each element in the DNA consists of a 5-tuple (x, y, width, height, (r, g, b, a))."""

	def __init__(self, size, dna):
		self.__score = -1
		self.__size = size 
		self.__dna = dna
		self.__image = None
		self.__mutations = [
			self.__mutation_physshift,
			self.__mutation_colshift,
			self.__mutation_swap,
			self.__mutation_del,
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

	def __mutation_del(self):
		if len(self.dna) <= 1:
			return self
		which_dna = random.randint(0, len(self.dna) - 1)
		new_dna = list(self.dna)
		new_dna.pop(which_dna)
		return ImageOrganism(self.size, new_dna)

	def __mutation_shift(self, which_dna, index, minv, maxv, maxchange):
		if len(self.dna) == 0:
			return self
		new_dna = list(self.dna)
		currect = self.dna[which_dna]
		rmin = -min(maxchange, currect[index] - minv)
		rmax = min(maxchange, maxv - currect[index])
		if rmin > rmax:
			if rmin > 0:
				rmax = rmin
			else:
				rmin = rmax
		change = [0,0,0,0]
		change[index] = random.randint(rmin, rmax)
		new_dna[which_dna] = (currect[0] + change[0], currect[1] + change[1], currect[2] + change[2], currect[3] + change[3], currect[4])
		return ImageOrganism(self.size, new_dna)

	def __mutation_shift_col(self, which_dna, index, minv, maxv, maxchange):
		if len(self.dna) == 0:
			return self
		new_dna = list(self.dna)
		currect = self.dna[which_dna]
		rmin = -min(maxchange, currect[4][index] - minv)
		rmax = min(maxchange, maxv - currect[4][index])
		if rmin > rmax:
			if rmin > 0:
				rmax = rmin
			else:
				rmin = rmax
		change = [0,0,0,0]
		change[index] = random.randint(rmin, rmax)
		new_dna[which_dna] = (currect[0], currect[1], currect[2], currect[3], (currect[4][0] + change[0], currect[4][1] + change[1], currect[4][2] + change[2], currect[4][3] + change[3]))
		return ImageOrganism(self.size, new_dna)

	def __mutation_physshift(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		return self.__mutation_leftshift(which_dna).__mutation_topshift(which_dna).__mutation_bottomshift(which_dna).__mutation_rightshift(which_dna)

	def __mutation_colshift(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		return self.__mutation_rshift(which_dna).__mutation_gshift(which_dna).__mutation_bshift(which_dna).__mutation_ashift(which_dna)

	def __mutation_leftshift(self, which_dna):
		return self.__mutation_shift(which_dna, 0, 0, self.dna[which_dna][2] - MIN_SIZE, CHG_COORD)

	def __mutation_topshift(self, which_dna):
		return self.__mutation_shift(which_dna, 1, 0, self.dna[which_dna][3] - MIN_SIZE, CHG_COORD)
	
	def __mutation_rightshift(self, which_dna):
		return self.__mutation_shift(which_dna, 2, self.dna[which_dna][0] + MIN_SIZE, self.size[0], CHG_SIZE)
	
	def __mutation_bottomshift(self, which_dna):
		return self.__mutation_shift(which_dna, 3, self.dna[which_dna][1] + MIN_SIZE, self.size[1], CHG_SIZE)

	def __mutation_rshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 0, 0, 255, CHG_COLOR)

	def __mutation_gshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 1, 0, 255, CHG_COLOR)

	def __mutation_bshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 2, 0, 255, CHG_COLOR)

	def __mutation_ashift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 3, MIN_ALPHA, MAX_ALPHA, CHG_COLOR)

	def __render_rect(self, rect):
		image = Image.new("RGBA", self.size)
		draw = ImageDraw.Draw(image)

		draw.rectangle([(rect[0], rect[1]), (rect[2], rect[3])], fill=rect[4])

		return image

	def __render(self):
		if self.__image != None:
			return
		self.__image = Image.new("RGB", self.size)
		for rect in self.dna:
			rendered = self.__render_rect(rect)
			self.__image.paste(rendered, (0,0), rendered)

	def mutate(self):
		mutation = random.randint(0, len(self.__mutations) - 1)
		return self.__mutations[mutation]()

	def add_rect(self):
		rect = self.__generate_rect()
		return ImageOrganism(self.size, self.dna + [rect])

	def calc_score(self, target):
		data = list(self.image.getdata())
		assert len(data) == len(target)
		score = 0
		for index in range(len(data)):
			hsl = data[index] 
			score += (hsl[0] - target[index][0]) ** 2
			score += (hsl[1] - target[index][1]) ** 2
			score += (hsl[2] - target[index][2]) ** 2
		self.__score = score
		return self.score

	def __generate_rect(self):
		x = random.randint(0, self.size[0] - 1 - MIN_SIZE)
		y = random.randint(0, self.size[1] - 1 - MIN_SIZE)
		x2 = random.randint(x + MIN_SIZE, self.size[0])
		y2 = random.randint(y + MIN_SIZE, self.size[1])
		col = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(15, 191))
		return (x, y, x2, y2, col)

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
	current = current.add_rect()
current.calc_score(target_dna)
while True:
	x += 1
	print 'Running iteration #' + str(x) + ' (nc: ' + str(nc) + ')'
	if nc >= 20 + len(current.dna) and len(current.dna) < 50:
		candidate = current.add_rect()
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
