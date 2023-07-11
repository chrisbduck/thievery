# ------------------------------------------------------------------------------
# Thievery game
# Written for Ludum Dare 25, by Chris Bevan ("schnerble" on the site")
# ------------------------------------------------------------------------------

# On Windows, try to load the AVBin dll first.  Having it in memory should
# hopefully make Pyglet find it without hassle
import sys
if 'win' in sys.platform:
	import ctypes
	import os
	try:
		path = os.path.abspath(os.path.split(sys.argv[0])[0])
		avbin_dll = ctypes.CDLL(os.path.join(path, 'avbin.dll'))
	except WindowsError:
		print 'Failed to load avbin.dll!'

# ------------------------------------------------------------------------------

import entities
import events
import levels
import misc
import pyglet
from pyglet.window import key
import stats

# ------------------------------------------------------------------------------

window = pyglet.window.Window(width=800, height=600, caption='Thievery', vsync=False)
entities.g_window = window
stats.g_window = window

grass = pyglet.resource.image('data/textures/grass.jpg')

g_paused = False

# ------------------------------------------------------------------------------
@window.event
def on_key_press(symbol, modifiers):
	misc.handleKeyPress(symbol, modifiers)
	# Stop escape from exiting immediately
	#if misc.isKeyHeld(key.ESCAPE):
	#	return pyglet.event.EVENT_HANDLED

# ------------------------------------------------------------------------------
@window.event
def on_key_release(symbol, modifiers):
	misc.handleKeyRelease(symbol, modifiers)

# ------------------------------------------------------------------------------
@window.event
def on_draw():
	#window.clear()
	grass.blit(0, 0)
	entities.drawAll()
	stats.draw()

# ------------------------------------------------------------------------------
def update(dt):
	global g_paused
	
	if not g_paused and not stats.won_level:
		entities.updateAll(dt)
	events.update(dt)
	stats.update(dt)
	
	# Special input
	if misc.wasAnyKeyPressed((key.ENTER, key.RETURN)):
		if stats.isPlayerDead():
			#print 'reloading'
			levels.reload()
			stats.reset(player_died=True)
			g_paused = False
		elif stats.won_game:
			#print 'finished'
			pyglet.app.exit()
		elif stats.intro_screen:
			if stats.showing_sound_warning:
				stats.setUpIntroScreen()
			else:
				#print 'starting'
				levels.start()
				misc.playMusic()
				stats.reset()
		elif stats.won_level:
			#print 'next level'
			if not levels.next():
				misc.playMusic(victory=True)
			stats.reset()
			g_paused = False
	if misc.wasKeyPressed(key.P):
		if not stats.won_game and not stats.intro_screen:
			g_paused = not g_paused
			stats.setPaused(g_paused)
	
	# Do this at the end, because it clears the keys pressed
	misc.updateKeys()

# ------------------------------------------------------------------------------

misc.init()
stats.init()
events.init()
stats.setUpFirstScreen()

pyglet.clock.schedule_interval(update, 0.02)

while True:
	try:
		pyglet.app.run()
		break
	except ValueError as exc:
		# Catch and discard the Pyglet exception for unrecognised characters
		if 'unichr() arg not in range' not in str(exc).lower():
			raise
