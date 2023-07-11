# ------------------------------------------------------------------------------
# Miscellaneous functionality
# ------------------------------------------------------------------------------

import math
import os
import pyglet
from pyglet.window import key

COS_45_DEG = 0.7071

_g_images = {}
_g_sounds = {}
_g_keys_held = set()
_g_keys_pressed = set()

_g_won_music = None
_g_main_music = None
_g_music_player = None

_g_debug_img = None
_g_debug_sprite = None

g_enable_sound = pyglet.media.have_avbin

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def getResourceName(name):
	if os.path.isfile('data/' + name):
		return name
	return 'placeholders/' + name

# ------------------------------------------------------------------------------
# Images
# ------------------------------------------------------------------------------
def getImage(file_name):
	if not file_name in _g_images:
		_g_images[file_name] = pyglet.resource.image(file_name)
	return _g_images[file_name]

# ------------------------------------------------------------------------------
# Sounds
# ------------------------------------------------------------------------------
def initSounds(name_list):
	for name in name_list:
		_g_sounds[name] = pyglet.resource.media(getResourceName('sfx/{0}.ogg'.format(name)), streaming=False)

# ------------------------------------------------------------------------------
def playSound(name):
	if not g_enable_sound:
		return
	if not name in _g_sounds:
		print 'Sound {0} does not exist'.format(name)
	else:
		_g_sounds[name].play()

# ------------------------------------------------------------------------------
# Keys
# ------------------------------------------------------------------------------
def handleKeyPress(symbol, modifiers):
	#print 'Key pressed: {0} ({1})'.format(symbol, modifiers)
	_g_keys_held.add(symbol)
	_g_keys_pressed.add(symbol)
	if symbol == key.A:
		playSound('Big_Shoot')

# ------------------------------------------------------------------------------
def handleKeyRelease(symbol, modifiers):
	#print 'Key released: {0} ({1})'.format(symbol, modifiers)
	# Note: keys may be released when not pressed (from while in another window, etc)
	if symbol in _g_keys_held:
		_g_keys_held.remove(symbol)
	if symbol in _g_keys_pressed:
		_g_keys_pressed.remove(symbol)
	if symbol == key.A:
		playSound('Big_Shoot')

# ------------------------------------------------------------------------------
def isKeyHeld(symbol):
	return symbol in _g_keys_held

# ------------------------------------------------------------------------------
def isAnyKeyHeld(symbol_list):
	return set(symbol_list).intersection(_g_keys_held)

# ------------------------------------------------------------------------------
def wasKeyPressed(symbol):
	return symbol in _g_keys_pressed

# ------------------------------------------------------------------------------
def wasAnyKeyPressed(symbol_list):
	return set(symbol_list).intersection(_g_keys_pressed)

# ------------------------------------------------------------------------------
def updateKeys():
	_g_keys_pressed.clear()

# ------------------------------------------------------------------------------
# Debugging
# ------------------------------------------------------------------------------
def drawDebugRect(left_x=None, top_y=None, centre_x=None, centre_y=None, scale=None, size=None):
	global _g_debug_img
	if _g_debug_img is None:
		_g_debug_img = getImage('data/textures/rect.png')
	
	if size is not None:
		scale = size / _g_debug_img.width
	elif scale is None:
		scale = 1
	
	assert(left_x is not None or centre_x is not None)
	assert(top_y is not None or centre_y is not None)
	x = left_x if left_x is not None else (centre_x - _g_debug_img.width * scale / 2)
	y = top_y if top_y is not None else (centre_y - _g_debug_img.height * scale / 2)
	
	global _g_debug_sprite
	if _g_debug_sprite is None:
		_g_debug_sprite = pyglet.sprite.Sprite(_g_debug_img, x, y)
	else:
		_g_debug_sprite.set_position(x, y)
	_g_debug_sprite.scale = scale
	_g_debug_sprite.draw()

# ------------------------------------------------------------------------------
# Other
# ------------------------------------------------------------------------------
rectLeft =   lambda rect: rect[0]
rectTop =    lambda rect: rect[1]
rectRight =  lambda rect: rect[2]
rectBottom = lambda rect: rect[3]

# ------------------------------------------------------------------------------
def rectsOverlap(rect1, rect2):
	r1_left, r1_top, r1_right, r1_bottom = rect1
	r2_left, r2_top, r2_right, r2_bottom = rect2
	if r1_right < r2_left or r1_left >= r2_right:
		return False
	if r1_bottom < r2_top or r1_top >= r2_bottom:
		return False
	return True

# ------------------------------------------------------------------------------
def circleSeparation(circle1, circle2):
	"Returns the distance between the edges of the two circles.  May be negative if they overlap."
	centre_x1, centre_y1, radius1 = circle1
	centre_x2, centre_y2, radius2 = circle2
	# Overlap if dist between centres < sum of radii (so separation < 0)
	dist_overall = distBetween(centre_x1, centre_y1, centre_x2, centre_y2)
	sum_of_radii = radius1 + radius2
	return dist_overall - sum_of_radii

# ------------------------------------------------------------------------------
def circlesOverlap(circle1, circle2):
	return circleSeparation(circle1, circle2) < 0

# ------------------------------------------------------------------------------
def distSqBetween(x1, y1, x2, y2):
	offset_x = x2 - x1
	offset_y = y2 - y1
	return offset_x * offset_x + offset_y * offset_y

# ------------------------------------------------------------------------------
def distBetween(x1, y1, x2, y2):
	return math.sqrt(distSqBetween(x1, y1, x2, y2))

# ------------------------------------------------------------------------------
def sign(val):
	if val < 0:
		return -1
	if val > 0:
		return +1
	return 0

# ------------------------------------------------------------------------------
def vecLength(x, y):
	return math.sqrt(x * x + y * y)

# ------------------------------------------------------------------------------
def normalisedDotProduct(vec1_x, vec1_y, vec2_x, vec2_y):
	vec1_length = vecLength(vec1_x, vec1_y)
	vec2_length = vecLength(vec2_x, vec2_y)
	vec1_x /= vec1_length
	vec1_y /= vec1_length
	vec2_x /= vec2_length
	vec2_y /= vec2_length
	return vec1_x * vec2_x + vec1_y * vec2_y

# ------------------------------------------------------------------------------
def linesIntersect(x1, y1, x2, y2,				# first line segment
				   x3, y3, x4, y4):				# second line segment
	"Nabbed from here: http://tog.acm.org/resources/GraphicsGems/gemsii/xlines.c"
	# a1, a2, b1, b2, c1, c2: Coefficients of line eqns
	# r1, r2, r3, r4:         'Sign' values
	# denom, offset, num:     Intermediate values
	
	# Compute a1, b1, c1, where line joining points 1 and 2
	# is "a1 x  +  b1 y  +  c1  =  0".
	a1 = y2 - y1
	b1 = x1 - x2
	c1 = x2 * y1 - x1 * y2
	
	# Compute r3 and r4.
	r3 = a1 * x3 + b1 * y3 + c1
	r4 = a1 * x4 + b1 * y4 + c1
	
	# Check signs of r3 and r4.  If both point 3 and point 4 lie on
	# same side of line 1, the line segments do not intersect.
	if r3 != 0 and r4 != 0 and sign(r3) == sign(r4):
		return False
	
	# Compute a2, b2, c2
	a2 = y4 - y3
	b2 = x3 - x4
	c2 = x4 * y3 - x3 * y4
	
	# Compute r1 and r2
	r1 = a2 * x1 + b2 * y1 + c2
	r2 = a2 * x2 + b2 * y2 + c2
	
	# Check signs of r1 and r2.  If both point 1 and point 2 lie
	# on same side of second line segment, the line segments do
	# not intersect.
	if r1 != 0 and r2 != 0 and sign(r1) == sign(r2):
		return False
	
	# Line segments intersect: compute intersection point. 
	denom = a1 * b2 - a2 * b1
	if denom == 0:
		return True		# collinear
	offset = (- denom / 2) if denom < 0 else (denom / 2);
	
	# The denom/2 is to get rounding instead of truncating.  It
	# is added or subtracted to the numerator, depending upon the
	# sign of the numerator.
	
	""" These intersect values aren't currently used
	num = b1 * c2 - b2 * c1
	nom_val = (num - offset) if num < 0 else (num + offset)
	intersect_x = nom_val / denom
	
	num = a2 * c1 - a1 * c2;
	intersect_y = nom_val / denom
	"""
	
	return True

# ------------------------------------------------------------------------------
def lineIntersectsRect(x1, y1, x2, y2, rect):
	left = rectLeft(rect)
	top = rectTop(rect)
	right = rectRight(rect)
	bottom = rectBottom(rect)
	return 	linesIntersect(x1, y1, x2, y2,   left, top, right, top) or \
			linesIntersect(x1, y1, x2, y2,   left, top, left, bottom) or \
			linesIntersect(x1, y1, x2, y2,   right, top, right, bottom) or \
			linesIntersect(x1, y1, x2, y2,   left, bottom, right, bottom)
	
# ------------------------------------------------------------------------------
def setSpriteRenderPos(sprite, centre_x, centre_y, rotation=0):
	max_x_offset = sprite.width / (2 * COS_45_DEG)
	max_y_offset = sprite.height / (2 * COS_45_DEG)
	
	effective_angle_rad = (225 - rotation) * math.pi / 180
	offset_x = max_x_offset * math.cos(effective_angle_rad)
	offset_y = max_y_offset * math.sin(effective_angle_rad)
	
	sprite.set_position(centre_x + offset_x, centre_y + offset_y)
	sprite.rotation = rotation
	
# ------------------------------------------------------------------------------
def getRotationFromDir(dir_x, dir_y):
	if dir_x == 0 and dir_y == 0:
		return None		# leave as is
	if dir_x == 0:
		return 180 if dir_y < 0 else 0
	if dir_y == 0:
		return 90 if dir_x > 0 else 270
	# x & y both non-zero
	if dir_y > 0:
		rotation = 45
	else:
		rotation = 135
	if dir_x < 0:
		rotation = -rotation
	return rotation

# ------------------------------------------------------------------------------
def playMusic(victory=False):
	if not g_enable_sound:
		return
	music = _g_won_music if victory else _g_main_music
	global _g_music_player
	_g_music_player.queue(music)
	if _g_music_player.playing:
		_g_music_player.next()
	else:
		_g_music_player.play()

# ------------------------------------------------------------------------------
def init():
	pyglet.resource.add_font('data/fonts/UbuntuMono-B.ttf')
	
	if g_enable_sound:
		global _g_main_music
		_g_main_music = pyglet.resource.media('data/music/main.ogg')
		global _g_won_music
		_g_won_music = pyglet.resource.media('data/music/victory.ogg')
		global _g_music_player
		_g_music_player = pyglet.media.Player()
		_g_music_player.eos_action = _g_music_player.EOS_LOOP

# ------------------------------------------------------------------------------
