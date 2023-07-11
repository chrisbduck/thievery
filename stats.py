# ------------------------------------------------------------------------------
# Stats and item functions
# ------------------------------------------------------------------------------

import misc
import pyglet

g_window = None

# Stats
killed_names = []
houses_looted = 0
pockets_picked = 0
loot = None
overall_loot = 0
looting_fraction = None
health_fraction = None
paused = False
won_level = False
won_game = False
intro_screen = False
showing_sound_warning = False

# Items
daggers = 0

# Labels
_dagger_label = None
_loot_label = None
_status_label = None
_chat_label = None
_hp_label = None
_title_label = None
_body_label = None

# Misc
_fades = []
_standard_labels = []
_text_screen_labels = []

# ------------------------------------------------------------------------------
def reset(player_died=False):
	global loot
	loot = 0
	global looting_fraction
	looting_fraction = None
	global health_fraction
	health_fraction = 1
	global _chat_label
	if _chat_label is not None:
		_chat_label.text = ''
	global paused
	paused = False
	global won_level
	won_level = False
	global _status_label
	if _status_label is not None and not won_game:
		_status_label.text = ''
	
	global intro_screen
	if player_died or intro_screen:
		global overall_loot
		overall_loot = 0
	
	intro_screen = False
	
	# Don't reset the following here: won_game, killed_names, daggers

# ------------------------------------------------------------------------------
# Status
# ------------------------------------------------------------------------------
def _showMessage(label, message, col, fade_duration_sec):
	if message is not None:
		label.text = message
	if col is not None:
		label.color = col
	_stopFadingLabel(label)
	if fade_duration_sec is not None:
		_fadeLabel(label, fade_duration_sec)

# ------------------------------------------------------------------------------
def showStatusMessage(message=None, col=None, fade_duration_sec=None):
	global _status_label
	_showMessage(_status_label, message, col, fade_duration_sec)

# ------------------------------------------------------------------------------
def showChatMessage(message, col=None, fade_duration_sec=None):
	global _chat_label
	_showMessage(_chat_label, message, col, fade_duration_sec)

# ------------------------------------------------------------------------------
def setPaused(new_paused):
	global paused
	paused = new_paused
	if paused:
		showStatusMessage('Paused (press P to resume)', col=(255, 128, 0, 255))
	else:
		showStatusMessage('Resumed', col=(128, 64, 0, 255), fade_duration_sec=1)

# ------------------------------------------------------------------------------
# Daggers
# ------------------------------------------------------------------------------
def removeDagger():
	global daggers
	daggers -= 1

haveDagger = lambda: daggers > 0

# ------------------------------------------------------------------------------
def addKill(name):
	killed_names.append(name)

# ------------------------------------------------------------------------------
# Loot
# ------------------------------------------------------------------------------
def setLootingCompletion(fraction):
	global looting_fraction
	looting_fraction = fraction
	showStatusMessage('Looting... {0}%'.format(int(100 * looting_fraction)), col=(255, 128, 0, 255),
						fade_duration_sec=1)

# ------------------------------------------------------------------------------
def stopLooting():
	global looting_fraction
	looting_fraction = None

# ------------------------------------------------------------------------------
def addLoot(amount, pickpocket_target=None):
	global loot
	loot += amount
	global overall_loot
	overall_loot += amount
	if pickpocket_target is not None:
		global pockets_picked
		pockets_picked += 1
		message = 'Picked pocket of {0}!'.format(pickpocket_target.name)
	else:
		global houses_looted 
		houses_looted += 1
		message = 'Looted!'
	showStatusMessage(message, col=(255, 255, 0, 255), fade_duration_sec=2)

# ------------------------------------------------------------------------------
def setWonLevel():
	global won_level
	won_level = True
	showStatusMessage('Town looted!  Press Enter to continue', col=(255, 255, 0, 255))

# ------------------------------------------------------------------------------
def setWonGame():
	global won_game
	global killed_names
	global houses_looted
	global overall_loot
	won_game = True
	_title_label.text = 'Game Complete!'
	
	body_label = _makeLabel(font_size=14, color=(160, 160, 160, 255), x=g_window.width / 2, y=g_window.height / 2,
							anchor_x='center', anchor_y='center', width=int(g_window.width * 0.7), multiline=True)
	
	won_text = \
		"And so it came to pass that Kane, the mass larcenist and occasional murderer, looted the entire world, " \
		"then had nothing left to do.\n\n" \
		"He moved to the Caribbean, and spent the rest of his life lying on a beach in the sun, until he died of " \
		"melanoma.\n\n" \
		+ "His fortune of {0} Thiefbucks was inherited by his pet goat, Roger.\n\n".format(overall_loot) \
		+ "Everyone else lived happily ever after, except for:\n\n"
	if killed_names != []:
		won_text += "; ".join(killed_names) + "\n"
	if houses_looted > 0:
		won_text += "The owners of {0} house{1}".format(houses_looted, '' if houses_looted == 1 else 's')
	body_label.text = won_text
	
	global _text_screen_labels
	_text_screen_labels = [_title_label, _status_label, body_label]
	
	showStatusMessage('Press Enter to exit', col=(128, 128, 128, 255))

# ------------------------------------------------------------------------------
def setUpFirstScreen():
	global showing_sound_warning
	showing_sound_warning = not misc.g_enable_sound
	if not showing_sound_warning:
		setUpIntroScreen()
		return
	
	global intro_screen
	intro_screen = True
	_title_label.text = 'Welcome to Thievery!'
	
	body_label = _makeLabel(font_size=14, color=(160, 160, 160, 255), x=g_window.width / 2, y=360,
							anchor_x='center', anchor_y='center', width=int(g_window.width * 0.7), multiline=True)
	
	body_label.text = \
		"Thievery requires AVBin for its sounds and music, but for some reason it couldn't be loaded correctly.  Sorry!\n\n" \
		"Please see the readme.txt for more details."
	
	controls_label = _makeLabel(font_size=14, color=(160, 160, 255, 255), x=g_window.width / 2, y=200,
								halign='center', anchor_x='center', anchor_y='center',
								width=int(g_window.width * 0.6), multiline=True)
	controls_label.text = \
		"Enter - continue without sounds or music\n" \
		"Esc - quit"
	
	global _text_screen_labels
	_text_screen_labels = [_title_label, body_label, controls_label]

# ------------------------------------------------------------------------------
def setUpIntroScreen():
	global showing_sound_warning
	showing_sound_warning = False
	global intro_screen
	intro_screen = True
	_title_label.text = 'Welcome to Thievery!'
	
	body_label = _makeLabel(font_size=14, color=(160, 160, 160, 255), x=g_window.width / 2, y=360,
							anchor_x='center', anchor_y='center', width=int(g_window.width * 0.7), multiline=True)
	
	body_label.text = \
		"Kane the thief needs your help to relieve dozens of innocent and unsuspecting victims of their " \
		"hard-earned cash.\n\n" \
		"He's up against some stiff competition, with an array of armoured guards on patrol - and those " \
		"guards aren't against a bit of good old-fashioned biffo.  They've even brought in their pet dogs " \
		"for assistance.\n\n" \
		"Use daggers sparingly - Kane can't carry many, and throwing them at guards tends to make them cross.\n\n" \
		"You can loot houses when near the door, or pick the pockets of guards who haven't spotted you yet."
	
	controls_label = _makeLabel(font_size=14, color=(160, 160, 255, 255), x=g_window.width / 2, y=140,
								halign='center', anchor_x='center', anchor_y='center',
								width=int(g_window.width * 0.4), multiline=True)
	controls_label.text = \
		"Controls:\n\n" \
		"Arrow keys / number pad - move\n" \
		"Ctrl - throw dagger\n" \
		"Space - loot / pickpocket\n" \
		"Esc - quit"
	
	global _text_screen_labels
	_text_screen_labels = [_title_label, _status_label, body_label, controls_label]
	
	showStatusMessage('Press Enter to start', col=(192, 192, 192, 255))

# ------------------------------------------------------------------------------
# Health
# ------------------------------------------------------------------------------
def updateHealth(new_hp, max_hp):
	global health_fraction
	health_fraction = float(new_hp) / max_hp

# ------------------------------------------------------------------------------
def reportDeath():
	showStatusMessage('You have died. Press Enter to restart', col=(255, 0, 0, 255))

# ------------------------------------------------------------------------------
def isPlayerDead():
	return health_fraction <= 0

# ------------------------------------------------------------------------------
# General
# ------------------------------------------------------------------------------
def _makeLabel(**kwargs):
	label = pyglet.text.Label('', font_name='Ubuntu Mono', bold=True, **kwargs)
	label.fade_remaining_sec = None
	return label

# ------------------------------------------------------------------------------
def _fadeLabel(label, duration_sec):
	label.fade_duration_sec = duration_sec
	label.fade_remaining_sec = duration_sec

# ------------------------------------------------------------------------------
def setLabelAlpha(label, alpha):
	label.color = (label.color[0], label.color[1], label.color[2], int(alpha))

# ------------------------------------------------------------------------------
def _stopFadingLabel(label):
	label.fade_remaining_sec = None
	setLabelAlpha(label, 255)

# ------------------------------------------------------------------------------
def updateFades(dt):
	for label in _standard_labels:
		if label.fade_remaining_sec is not None:
			label.fade_remaining_sec -= dt
			if label.fade_remaining_sec <= 0:
				label.fade_remaining_sec = None
				alpha = 0
			else:
				alpha = 255 * label.fade_remaining_sec / label.fade_duration_sec
			setLabelAlpha(label, alpha)

# ------------------------------------------------------------------------------
def init():
	reset()
	
	global _hp_label
	_hp_label = _makeLabel(font_size=12, color=(255, 0, 0, 255), x=15, y=10)
	
	global _dagger_label
	_dagger_label = _makeLabel(font_size=12, color=(160, 160, 160, 255), x=785, y=10, anchor_x='right')
	
	global _loot_label
	_loot_label = _makeLabel(font_size=12, color=(255, 255, 0, 255), x=170, y=10, anchor_x='center')
	
	global _status_label
	_status_label = _makeLabel(font_size=12, color=(255, 128, 0, 255), x=g_window.width / 2, y=10, anchor_x='center')
	
	global _chat_label
	_chat_label = _makeLabel(font_size=12, color=(255, 255, 255, 255), x=g_window.width / 2, y=30, anchor_x='center')
	
	global _title_label
	_title_label = _makeLabel(font_size=36, color=(255, 255, 0, 255), x=g_window.width / 2, y=550,
										anchor_x='center')
	
	global _body_label
	_body_label = _makeLabel(font_size=14, color=(160, 160, 160, 255), x=g_window.width / 2,
										y=g_window.height / 2, anchor_x='center', anchor_y='center',
										width=int(g_window.width * 0.7), multiline=True)
	
	global _standard_labels, _text_screen_labels
	_standard_labels = [_hp_label, _dagger_label, _loot_label, _status_label, _chat_label]

# ------------------------------------------------------------------------------
def update(dt):
	updateFades(dt)
	_hp_label.text = 'Health: {0}%'.format(int(health_fraction * 100))
	_dagger_label.text = 'Daggers: {0}'.format(daggers)
	_loot_label.text = 'Loot: {0}'.format(loot)

# ------------------------------------------------------------------------------
def draw():
	labels_to_draw = _text_screen_labels if won_game or intro_screen else _standard_labels
	for label in labels_to_draw:
		if label.color[3] > 0:		# ignore if transparent
			label.draw()

# ------------------------------------------------------------------------------
