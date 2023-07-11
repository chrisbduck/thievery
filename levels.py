# ------------------------------------------------------------------------------
# Levels: Loads levels, etc
# ------------------------------------------------------------------------------

import entities
import pyglet
import stats

_current_name = None

_all_levels = ['1', '2', '3']

# ------------------------------------------------------------------------------
def load(level_name):
	global _current_name
	_current_name = level_name
	file_name = 'data/levels/{0}.txt'.format(level_name)
	src = pyglet.resource.file(file_name)
	
	entities.clearAll()
	
	for line in src.readlines():
		# Trim comments
		hash_pos = line.find('#')
		if hash_pos >= 0:
			line = line[:hash_pos]
		line = line.strip()
		if line == '':
			continue
		
		tokens = line.split()
		obj_type = tokens[0].lower()
		
		params = []
		for tok in tokens[1:]:
			if tok != '' and tok[0].isdigit():
				if '.' in tok:
					params.append(float(tok))
				else:
					params.append(int(tok))
			else:
				params.append(tok)
		
		if obj_type == 'player':
			entities.PlayerEntity(*params)
		elif obj_type == 'house':
			entities.HouseEntity(*params)
		elif obj_type == 'guard':
			entities.HumanGuardEntity(*params)
		elif obj_type == 'dog':
			entities.GuardDogEntity(*params)
	
	#spinner = entities.SpinnerEntity()

# ------------------------------------------------------------------------------
def reload():
	load(_current_name)

# ------------------------------------------------------------------------------
def next():
	try:
		current_index = _all_levels.index(_current_name) + 1
	except ValueError:
		print 'Current level not found'
		current_index = 0
	
	if current_index >= len(_all_levels):
		print 'Game complete!'
		entities.clearAll()
		stats.setWonGame()
		return False	# no more levels
	
	load(_all_levels[current_index])
	return True

# ------------------------------------------------------------------------------
def start():
	load(_all_levels[0])

# ------------------------------------------------------------------------------
