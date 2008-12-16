#!/usr/bin/python

import Image
import ImageDraw

import pickle
import random

class ImageOrganism:
	"""An organism which attempts to approximate an image via translucent circles. Each element in the DNA consists of a 4-tuple (x, y, radius, (r, g, b, a))."""

	def __init__(self, size, dna):
		self.__score = -1
		self.__size = size 
		self.__dna = dna
		self.__image = None
		self.__mutations = [
			#self.__mutation_add,
			#self.__mutation_del,
			#self.__mutation_rep,
			self.__mutation_xshift,
			self.__mutation_yshift,
			self.__mutation_radshift,
			self.__mutation_rshift,
			self.__mutation_gshift,
			self.__mutation_bshift,
			self.__mutation_ashift,
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

	def mutation_add(self):
		circle = self.__generate_circle()
		return ImageOrganism(self.size, self.dna + [circle])
	
	def __mutation_del(self):
		if len(self.dna) <= 1:
			return self
		which_dna = random.randint(0, len(self.dna) - 1)
		new_dna = list(self.dna)
		new_dna.pop(which_dna)
		return ImageOrganism(self.size, new_dna)

	def __mutation_rep(self):
		if len(self.dna) == 0:
			return self
		which_dna = random.randint(0, len(self.dna) - 1)
		new_dna = list(self.dna)
		new_dna[which_dna] = self.__generate_circle()
		return ImageOrganism(self.size, new_dna)

	def __mutation_shift(self, index, minv, maxv, maxchange):
		if len(self.dna) == 0:
			return self
		which_dna = random.randint(0, len(self.dna) - 1)
		new_dna = list(self.dna)
		curcirc = self.dna[which_dna]
		rmin = -min(maxchange, curcirc[index] - minv)
		rmax = min(maxchange, maxv - curcirc[index])
		change = [0,0,0]
		change[index] = random.randint(rmin + 1, rmax)
		if change[index] <= 0:
			change[index] -= 1
		new_dna[which_dna] = (curcirc[0] + change[0], curcirc[1] + change[1], curcirc[2] + change[2], curcirc[3])
		return ImageOrganism(self.size, new_dna)

	def __mutation_shift_col(self, index, minv, maxv, maxchange):
		if len(self.dna) == 0:
			return self
		which_dna = random.randint(0, len(self.dna) - 1)
		new_dna = list(self.dna)
		curcirc = self.dna[which_dna]
		rmin = -min(maxchange, curcirc[3][index] - minv)
		rmax = min(maxchange, maxv - curcirc[3][index])
		change = [0,0,0,0]
		change[index] = random.randint(rmin + 1, rmax)
		if change[index] <= 0:
			change[index] -= 1
		new_dna[which_dna] = (curcirc[0], curcirc[1], curcirc[2], (curcirc[3][0] + change[0], curcirc[3][1] + change[1], curcirc[3][2] + change[2], curcirc[3][3] + change[3]))
		return ImageOrganism(self.size, new_dna)

	def __mutation_xshift(self):
		return self.__mutation_shift(0, 0, self.size[0], 2)

	def __mutation_yshift(self):
		return self.__mutation_shift(1, 0, self.size[1], 2)
	
	def __mutation_radshift(self):
		return self.__mutation_shift(2, 2, 750, 2)

	def __mutation_rshift(self):
		return self.__mutation_shift_col(0, 0, 255, 5)

	def __mutation_gshift(self):
		return self.__mutation_shift_col(1, 0, 255, 5)

	def __mutation_bshift(self):
		return self.__mutation_shift_col(2, 0, 255, 5)

	def __mutation_ashift(self):
		return self.__mutation_shift_col(3, 15, 191, 5)

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
		r = random.randint(5, 75)
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

target_image = Image.open('target.jpg')
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
	current = current.mutation_add()
current.calc_score(target_dna)
while True:
	x += 1
	print 'Running iteration #' + str(x) + ' (nc: ' + str(nc) + ')'
	candidate = current.mutate()
	if nc >= 25 + 3 * len(current.dna):
		candidate = current.mutation_add()
	candidate.calc_score(target_dna)

	if candidate.score < current.score:
		nc = 0
		current = candidate
		current.image.save('best.png', 'PNG')
		f = open('best.dna', 'w')
		f.write(repr(current.dna) + '\n')
		f.close()
		f = open('best.pickle', 'wb')
		pickle.dump((current.dna, x), f)
		f.close()
		print 'Replaced current with candidate. (Score: ' + str(candidate.score) + ', Num: ' + str(len(candidate.dna)) + ')'
	else:
		nc += 1
