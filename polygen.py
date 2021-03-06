#!/usr/bin/python

import Image
import ImageDraw

import pickle
import random

MAX_INIT_SIZE = 40
CHG_COORD = 5

MIN_ALPHA = 31
MAX_ALPHA = 255
CHG_COLOR = 15

class ImageOrganism:
	"""An organism which attempts to approximate an image via translucent polyangles. Each element in the DNA consists of a 5-tuple (x, y, width, height, (r, g, b, a))."""

	def __init__(self, size, dna):
		self.__score = -1
		self.__size = size 
		self.__dna = dna
		self.__image = None
		self.__mutations = [
			self.__mutation_swap,
			self.__mutation_del,
			self.__mutation_physshift,
			self.__mutation_colshift,
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
		curpoly = self.dna[which_dna]
		rmin = -min(maxchange, curpoly[1][index] - minv)
		rmax = min(maxchange, maxv - curpoly[1][index])
		if rmin > rmax:
			if rmin > 0:
				rmax = rmin
			else:
				rmin = rmax
		change = random.randint(rmin, rmax)
		new_dna[which_dna] = (new_dna[which_dna][0], list(new_dna[which_dna][1]))
		new_dna[which_dna][1][index] += change
		return ImageOrganism(self.size, new_dna)

	def __mutation_shift_col(self, which_dna, index, minv, maxv, maxchange):
		if len(self.dna) == 0:
			return self
		new_dna = list(self.dna)
		curpoly = self.dna[which_dna]
		rmin = -min(maxchange, curpoly[0][index] - minv)
		rmax = min(maxchange, maxv - curpoly[0][index])
		if rmin > rmax:
			if rmin > 0:
				rmax = rmin
			else:
				rmin = rmax
		change = random.randint(rmin, rmax)
		cols = list(new_dna[which_dna][0])
		cols[index] += change
		new_dna[which_dna] = (tuple(cols), new_dna[which_dna][1])
		return ImageOrganism(self.size, new_dna)

	def __mutation_physshift(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		which_part = random.randint(0, len(self.dna[which_dna][1]) / 2 - 1) * 2
		result = self.__mutation_shift(which_dna, which_part, 0, self.size[0], CHG_COORD)
		result = result.__mutation_shift(which_dna, which_part + 1, 0, self.size[1], CHG_COORD)
		return result

	def __mutation_colshift(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		result = self.__mutation_rshift(which_dna).__mutation_gshift(which_dna).__mutation_bshift(which_dna).__mutation_ashift(which_dna)
		return result

	def __mutation_rshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 0, 0, 255, CHG_COLOR)

	def __mutation_gshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 1, 0, 255, CHG_COLOR)

	def __mutation_bshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 2, 0, 255, CHG_COLOR)

	def __mutation_ashift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 3, MIN_ALPHA, MAX_ALPHA, CHG_COLOR)

	def __render_poly(self, poly):
		image = Image.new("RGBA", self.size)
		draw = ImageDraw.Draw(image)

		draw.polygon(poly[1], fill=poly[0])

		return image

	def __render(self):
		if self.__image != None:
			return
		self.__image = Image.new("RGB", self.size)
		for poly in self.dna:
			rendered = self.__render_poly(poly)
			self.__image.paste(rendered, (0,0), rendered)

	def mutate(self):
		mutation = random.randint(0, len(self.__mutations) - 1)
		result = self.__mutations[mutation]()
		return result

	def add_poly(self):
		poly = self.__generate_poly()
		return ImageOrganism(self.size, self.dna + [poly])

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

	def __generate_poly(self):
		x = random.randint(0, self.size[0] - 1)
		y = random.randint(0, self.size[1] - 1)
		x2 = random.randint(max(0, x - MAX_INIT_SIZE), min(self.size[0] - 1, x + MAX_INIT_SIZE))
		y2 = random.randint(max(0, y - MAX_INIT_SIZE), min(self.size[1] - 1, y + MAX_INIT_SIZE))
		x3 = random.randint(max(0, (x + x2) / 2 - MAX_INIT_SIZE), min(self.size[0] - 1, (x + x2) / 2 + MAX_INIT_SIZE))
		y3 = random.randint(max(0, (y + y2) / 2 - MAX_INIT_SIZE), min(self.size[1] - 1, (y + y2) / 2 + MAX_INIT_SIZE))
		col = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(15, 191))
		return (col, [x, y, x2, y2, x3, y3])

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
	current = current.add_poly()
current.calc_score(target_dna)
while True:
	x += 1
	print 'Running iteration #' + str(x) + ' (nc: ' + str(nc) + ')'
	if nc >= 50 and nc % 2 == 0:
		candidate = current.add_poly()
	else:
		candidate = current
		while candidate == current:
			candidate = current.mutate()
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
