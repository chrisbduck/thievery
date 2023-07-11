# ------------------------------------------------------------------------------
# Events: trigger various events and responses to them, including chatter
# ------------------------------------------------------------------------------

import misc
import pyglet
import random
import stats

LOW_PRIORITY_MESSAGE_INTERVAL_SEC = 2

g_chat_events = {}
g_sound_events = {}
g_pending_chat_events = []		# list of [time_from_now_until_trigger_sec, line, entity]
g_time_since_last_event = 0

# ------------------------------------------------------------------------------
# Chatter
# ------------------------------------------------------------------------------
def initChatter():
	src = pyglet.resource.file('data/chatter.txt')
	
	current_name = None
	current_lines = []
	for line in src.readlines():
		hash_pos = line.find('#')
		if hash_pos >= 0:
			line = line[:hash_pos]
		line = line.strip()
		if line == '':
			continue
		
		if line.startswith('['):
			# New chat type
			
			# Add the previous chat line
			insertChat(current_name, current_lines)
			current_name, current_lines = '', []
			
			current_name = line[1:].replace(']', '').strip()
			
		else:
			# Append to current 
			current_lines.append(line)
	
	# Add the last one
	insertChat(current_name, current_lines)

# ------------------------------------------------------------------------------
def insertChat(name, lines):
	if name is None:
		return		# initial null entry
	if name == '':
		print 'Missing chat name'
	else:
		g_chat_events[name] = lines

# ------------------------------------------------------------------------------
# Sounds
# ------------------------------------------------------------------------------
def initSounds():
	if not misc.g_enable_sound:
		return
	
	# Slight laziness: copy sound events from chat events
	from glob import glob
	for event in g_chat_events:
		matching_sounds = []
		for path in pyglet.resource.path:
			pattern = '{0}/data/sfx/{1}*.ogg'.format(path, event)
			#print 'Looking for sounds in', pattern
			for result in glob(pattern):
				result = result[len(path) + 1:].replace('\\', '/')	# remove "path/" and convert backslashes
				matching_sounds.append(result)
		if matching_sounds == []:
			#print 'No matching sounds found for', event
			continue
		#print 'Found', len(matching_sounds), 'matching sounds for', event
		#print '  -', matching_sounds
		g_sound_events[event] = [pyglet.resource.media(sound, streaming=False) for sound in matching_sounds]

# ------------------------------------------------------------------------------
# Events
# ------------------------------------------------------------------------------
def trigger(name, entity, delay_sec=0, low_priority=False, very_low_priority=False):
	triggered = False
	event_trace = '{0} ({1})'.format(name, entity.name if entity is not None else 'None')
	
	if name in g_chat_events:
		_triggerChat(name, entity, delay_sec, low_priority, very_low_priority, event_trace)
		triggered = True
	
	if name in g_sound_events:
		_triggerSound(name, entity, event_trace)
		triggered = True
	
	if not triggered:
		print 'Unknown event:', event_trace
	
# ------------------------------------------------------------------------------
def _triggerChat(name, entity, delay_sec, low_priority, very_low_priority, event_trace):
	# Trigger a random line from the event
	#print 'Triggered chat event:', event_trace
	triggered = True
	lines = g_chat_events[name]
	if lines == []:
		return
	
	num_lines = len(lines)
	chosen_line_num = random.randint(0, num_lines - 1)
	chosen_line = lines[chosen_line_num]
	
	# Delay low-priority messages for a bit
	if g_time_since_last_event < LOW_PRIORITY_MESSAGE_INTERVAL_SEC and delay_sec < LOW_PRIORITY_MESSAGE_INTERVAL_SEC:
		if low_priority:
			delay_sec = LOW_PRIORITY_MESSAGE_INTERVAL_SEC - g_time_since_last_event
		elif very_low_priority:
			return		# skip very low priority messages if there's anything else going on
	
	if delay_sec <= 0:
		triggerLine(chosen_line, entity)
	else:
		g_pending_chat_events.append([delay_sec, chosen_line, entity])
	#delay_sec = 0
	#for line in event:
	#	g_pending_chat_events.append([delay_sec, line])
	#	delay_sec += 2
	
# ------------------------------------------------------------------------------
def _triggerSound(name, entity, event_trace):
	#print 'Triggered sound event:', event_trace
	triggered = True
	sound_options = g_sound_events[name]
	num_sounds = len(sound_options)
	chosen_sound = random.randint(0, num_sounds - 1)
	sound = sound_options[chosen_sound]
	sound.play()

# ------------------------------------------------------------------------------
def triggerLine(line, entity):
	col=None
	if entity is not None:
		line = entity.name + ': ' + line
		col = entity.chat_col
	stats.showChatMessage(line, col=col, fade_duration_sec=2)
	
	global g_time_since_last_event
	g_time_since_last_event = 0

# ------------------------------------------------------------------------------
# General
# ------------------------------------------------------------------------------
def init():
	initChatter()
	initSounds()

# ------------------------------------------------------------------------------
def update(dt):
	global g_pending_chat_events
	for event in g_pending_chat_events:
		time_left_sec, line, entity = event
		time_left_sec -= dt
		event[0] = time_left_sec
		if time_left_sec <= 0:
			triggerLine(line, entity)
	g_pending_chat_events = [event for event in g_pending_chat_events if event[0] > 0]
	
	global g_time_since_last_event
	g_time_since_last_event += dt

# ------------------------------------------------------------------------------
def removeAllEventsForEntity(entity):
	global g_pending_chat_events
	g_pending_chat_events = [event for event in g_pending_chat_events if event[2] is entity]

# ------------------------------------------------------------------------------
