#!/usr/bin/python

import Image
import ImageDraw

import getopt
import locale
import pickle
import random
import shutil
import sys

class ImageOrganism:
	"""An organism which attempts to approximate an image via translucent polyangles. Each element in the DNA consists of a 5-tuple (x, y, width, height, (r, g, b, a))."""

	def __init__(self, config, size, dna):
		self.__score = -1
		self.__config = config
		self.__size = size 
		self.__dna = dna
		self.__image = None
		self.__mutation = -1
		self.__mutations = [
			self.__mutation_swap,
			self.__mutation_del,
			self.__mutation_physshift,
			self.__mutation_colshift,
			self.__mutation_vertswap,
			self.__mutation_vertdel,
			self.__mutation_vertadd,
			self.__mutation_vertrep,
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

	def __get_mutation_name(self):
		if self.__mutation >= 0:
			return self.__mutations[self.__mutation].__name__
		return ''

	dna = property(fget=__get_dna, doc="""DNA string.""")
	score = property(fget=__get_score, doc="""Score of the picture.""")
	size = property(fget=__get_size, doc="""Size of the picture. (width, height)""")
	image = property(fget=__get_image, doc="""CIL Image""")
	mutation_name = property(fget=__get_mutation_name, doc="""Last mutation name.""")

	def __mutation_swap(self):
		src_dna = random.randint(0, len(self.dna) - 1)
		dest_dna = random.randint(0, len(self.dna) - 1)
		if src_dna == dest_dna:
			return self
		new_dna = list(self.dna)
		tmp = new_dna[dest_dna]
		new_dna[dest_dna] = new_dna[src_dna]
		new_dna[src_dna] = tmp
		result = ImageOrganism(self.__config, self.size, new_dna)
		return result

	def __mutation_vertswap(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		if len(self.dna[which_dna][1]) <= 3:
			return self
		new_dna = list(self.dna)
		new_verts = list(self.dna[which_dna][1])
		src_vert = random.randint(0, len(new_verts) / 2 - 1) * 2
		dest_vert = random.randint(0, len(new_verts) / 2 - 1) * 2
		if src_vert == dest_vert:
			dest_vert = (src_vert + 2) % len(new_verts)
		tmp = new_verts[src_vert]
		new_verts[src_vert] = new_verts[dest_vert]
		new_verts[dest_vert] = tmp
		tmp = new_verts[src_vert + 1]
		new_verts[src_vert + 1] = new_verts[dest_vert + 1]
		new_verts[dest_vert + 1] = tmp
		new_dna[which_dna] = (new_dna[which_dna][0], new_verts)
		result = ImageOrganism(self.__config, self.size, new_dna)
		return result

	def __mutation_vertdel(self):
		which_dna = random.randint(0, len(self.dna) - 1) 
		if len(self.dna[which_dna][1]) <= 3 * 2:
			return self
		new_dna = list(self.dna)
		new_verts = list(self.dna[which_dna][1])
		which_vert = random.randint(0, len(new_verts) / 2 - 1) * 2
		new_verts.pop(which_vert)
		new_verts.pop(which_vert)
		new_dna[which_dna] = (new_dna[which_dna][0], new_verts)
		result = ImageOrganism(self.__config, self.size, new_dna)
		return result

	def __mutation_vertadd(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		if len(self.dna[which_dna][1]) >= self.__config['MAX_DEGREE'] * 2:
			return self
		new_dna = list(self.dna)
		new_verts = list(self.dna[which_dna][1])
		location = random.random()
		which_vert = random.randint(0, len(new_verts) / 2 - 1) * 2
		x = location * new_verts[which_vert] + (1 - location) * new_verts[(which_vert + 2) % len(new_verts)] + random.randint(-1, 1)
		y = location * new_verts[which_vert + 1] + (1 - location) * new_verts[(which_vert + 3) % len(new_verts)] + random.randint(-1, 1)
		new_verts.insert(which_vert + 2, int(y))
		new_verts.insert(which_vert + 2, int(x))
		new_dna[which_dna] = (new_dna[which_dna][0], new_verts)
		result = ImageOrganism(self.__config, self.size, new_dna)
		return result

	def __mutation_vertrep(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		result = self.__mutation_vertdel()
		if result == self:
			result = self.__mutation_vertadd()
			result = self.__mutation_vertdel()
		else:
			result = self.__mutation_vertadd()
		return result

	def __mutation_del(self):
		if len(self.dna) <= 1:
			return self
		which_dna = random.randint(0, len(self.dna) - 1)
		new_dna = list(self.dna)
		new_dna.pop(which_dna)
		return ImageOrganism(self.__config, self.size, new_dna)

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
		return ImageOrganism(self.__config, self.size, new_dna)

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
		return ImageOrganism(self.__config, self.size, new_dna)

	def __mutation_physshift(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		which_part = random.randint(0, len(self.dna[which_dna][1]) / 2 - 1) * 2
		result = self.__mutation_shift(which_dna, which_part, 0, self.size[0], self.__config['CHG_COORD'])
		result = result.__mutation_shift(which_dna, which_part + 1, 0, self.size[1], self.__config['CHG_COORD'])
		return result

	def __mutation_colshift(self):
		which_dna = random.randint(0, len(self.dna) - 1)
		result = self.__mutation_rshift(which_dna).__mutation_gshift(which_dna).__mutation_bshift(which_dna).__mutation_ashift(which_dna)
		return result

	def __mutation_rshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 0, 0, 255, self.__config['CHG_COLOR'])

	def __mutation_gshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 1, 0, 255, self.__config['CHG_COLOR'])

	def __mutation_bshift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 2, 0, 255, self.__config['CHG_COLOR'])

	def __mutation_ashift(self, which_dna):
		return self.__mutation_shift_col(which_dna, 3, self.__config['MIN_ALPHA'], self.__config['MAX_ALPHA'], self.__config['CHG_COLOR'])

	def __render_poly(self, poly):
		image = Image.new("RGBA", self.size)
		draw = ImageDraw.Draw(image)

		draw.polygon(poly[1], fill=poly[0])

		return image

	def __render(self):
		if self.__image != None:
			return
		self.__image = Image.new("RGB", self.size)
		if self.__config['WHITE_BG']:
			d = ImageDraw.Draw(self.__image)
			d.rectangle(((0,0),self.size), fill=(255,255,255,255))
		for poly in self.dna:
			rendered = self.__render_poly(poly)
			self.__image.paste(rendered, (0,0), rendered)

	def mutate(self):
		num_mutations = random.randint(1, 3)
		result = self
		for x in range(num_mutations):
			mutation = random.randint(0, len(self.__mutations) - 1)
			nresult = result.__mutations[mutation]()
			if nresult != result:
				nresult.__mutation = mutation
				result = nresult
		return result

	def add_poly(self):
		poly = self.__generate_poly()
		return ImageOrganism(self.__config, self.size, self.dna + [poly])

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
		x2 = random.randint(max(0, x - self.__config['MAX_INIT_SIZE']), min(self.size[0] - 1, x + self.__config['MAX_INIT_SIZE']))
		y2 = random.randint(max(0, y - self.__config['MAX_INIT_SIZE']), min(self.size[1] - 1, y + self.__config['MAX_INIT_SIZE']))
		x3 = random.randint(max(0, (x + x2) / 2 - self.__config['MAX_INIT_SIZE']), min(self.size[0] - 1, (x + x2) / 2 + self.__config['MAX_INIT_SIZE']))
		y3 = random.randint(max(0, (y + y2) / 2 - self.__config['MAX_INIT_SIZE']), min(self.size[1] - 1, (y + y2) / 2 + self.__config['MAX_INIT_SIZE']))
		col = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(15, 191))
		return (col, [x, y, x2, y2, x3, y3])

def main(argv):
	locale.setlocale(locale.LC_ALL, '')

	target_image = Image.open('target.jpg').convert('RGB')
	target_dna = list(target_image.getdata())

	config = {}

	config['MAX_INIT_SIZE'] = 40
	config['CHG_COORD'] = 5

	config['MAX_DEGREE'] = 20
	config['MAX_POLYGONS'] = 150

	config['MIN_ALPHA'] = 31
	config['MAX_ALPHA'] = 255
	config['CHG_COLOR'] = 15

	config['WHITE_BG'] = False

	init_dna = []
	x = 0
	nc = 0
	history = {}
	try:
		f = open('best.pickle', 'rb')
		init_dna, x, history, newconfig = pickle.load(f)
		f.close()
		config.update(newconfig)
	except:
		pass

	try:
		opts, args = getopt.getopt(argv, 'd:p:wb', ['max-degree=', 'max-polygons=', 'white-bg', 'black-bg'])
	except getopt.GetoptError:
		print 'invalid arg'
		sys.exit(1)
	if len(args) > 0:
		print 'invalid args'
		sys.exit(1)

	for opt, arg in opts:
		if opt in ('-d', '--max-degree'):
			val = int(arg)
			if val < 3:
				print 'invalid args'
				sys.exit(1)
			config['MAX_DEGREE'] = val
		elif opt in ('-p', '--max-polygons'):
			val = int(arg)
			if val < 1:
				print 'invalid args'
				sys.exit(1)
			config['MAX_POLYGONS'] = val
		elif opt in ('-w', '--white-bg'):
			config['WHITE_BG'] = True
		elif opt in ('-b', '--black-bg'):
			config['WHITE_BG'] = False
	
	if config.get('generation') == None:
		config['generation'] = len(init_dna)

	print 'Dumping configuration:'
	for item in config:
		print str(item) + ': ' + str(config[item])
	print ''

	for item in history:
		org = ImageOrganism(config, target_image.size, history[item][2])
		org.image.save('best.' + str(len(org.dna)) + '.png', 'PNG')

	current = ImageOrganism(config, target_image.size, init_dna)
	if len(current.dna) == 0:
		current = current.add_poly()
		config['generation'] += 1
	current.calc_score(target_dna)
	while True:
		x += 1
		#print 'Running iteration #' + locale.format('%d', x, True) + ' (nc: ' + locale.format('%d', nc, True) + ')'
		if nc >= 30 + len(current.dna) / 2 and nc % 2 == 0 and len(current.dna) < config['MAX_POLYGONS']:
			candidate = current.add_poly()
		else:
			candidate = current
			while candidate == current:
				candidate = current.mutate()
		candidate.calc_score(target_dna)

		if candidate.score < current.score or (candidate.score <= current.score and candidate.mutation_name in ('__mutation_del', '__mutation_vertdel')):
			current = candidate
			if len(current.dna) != len(candidate.dna):
				config['generation'] += 1
			history[config['generation']] = [current.score, x, current.dna]
			current.image.save('best.' + str(config['generation']) + '.png', 'PNG')
			shutil.copy('best.' + str(config['generation']) + '.png', 'best.png')
			f = open('best.dna', 'w')
			f.write(repr(current.dna) + '\n')
			f.close()
			f = open('best.pickle.tmp', 'wb')
			pickle.dump((current.dna, x, history, config), f)
			f.close()
			shutil.move('best.pickle.tmp', 'best.pickle')
			f = open('index.html', 'w')
			f.write('<html><style><!-- body {font-family: sans; } img { border: 1px dashed #7f7f7f; } td { font-size: 10pt; padding: 5px; } --> </style><body><table cellspacing=\'0\' cellpadding=\'0\'>')
			for index in range(config['generation']):
				hist_node = history.get(index + 1)
				polystr = '???'
				iterstr = '???'
				scorestr = '???'
				if hist_node != None:
					genstr = locale.format('%d', index + 1, True)
					polystr = locale.format('%d', len(hist_node[2]), True)
					iterstr = locale.format('%d', hist_node[1], True)
					scorestr = locale.format('%d', hist_node[0], True)
				f.write('<tr><td><img src=\'best.' + str(index + 1) + '.png\' /></td><td><img src=\'target.jpg\' /></td>' + \
						  '<td><b>Generation:</b> ' + genstr + '<br />' + \
						  '<b>Polygons:</b> ' + polystr + '<br />' + \
						  '<b>Iteration:</b> ' + iterstr + '<br />' + \
						  '<b>Score:</b> ' + scorestr + '</td></tr>')
			f.write('</table></body></html>')
			f.close()
			print 'Replaced current with candidate. (NC: ' + locale.format('%3d', nc, True) + ', Score: ' + locale.format('%d', current.score, True) + ', Iter: ' + locale.format('%d', x, True) + ', Poly: ' + locale.format('%d', len(current.dna), True) + ', Mut: ' + current.mutation_name + ')'
			nc = 0
		else:
			nc += 1

if __name__ == '__main__':
	main(sys.argv[1:])
