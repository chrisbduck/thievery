# ------------------------------------------------------------------------------
# Entities: classes for movement, etc
# 
# All positions are in pixels
# All speeds are in pixels per second
# All accelerations (if I end up adding any) are in pixels per second per second
# ------------------------------------------------------------------------------

import events
import math
import misc
from misc import rectLeft, rectTop, rectRight, rectBottom
import pyglet
from pyglet.window import key
import random
import stats

COS_45_DEG = 0.7071
DEATH_DURATION_SEC = 1
DAMAGE_ANIM_DURATION_SEC = 1
LOOT_DURATION_SEC = 2
STUCK_DIST_SQ_LIMIT = 1
SCREEN_MINIMUM_Y = 50		# Text goes below this
ALERT_MAX_RANGE = 120

g_window = None

# ------------------------------------------------------------------------------
class Entity(object):
	_entities = []
	_new_entities = []
	
	# ------------------------------------------------------------------------------
	def __init__(self, img_fname, x=0, y=0, *args):
		self.name = 'unknown'
		self.x = float(x)		# left x
		self.y = float(y)		# *bottom* y
		self.vx = 0
		self.vy = 0
		self.rotation = 0
		self.alive = True
		self.dying = False
		self.die_off_screen = False
		self.force_on_screen = False
		self.collide_circle_duration = 0
		self.collide_rect_duration = 0
		self.stuck_duration = 0
		self.chat_col = (255, 255, 255, 255)
		
		self.image = misc.getImage(img_fname)
		self.width = self.image.width
		self.height = self.image.height
		self.half_width = self.width / 2
		self.half_height = self.height / 2
		self.sprite_left = 0
		self.sprite_right = self.width
		self.sprite_top = 0
		self.sprite_bottom = self.height
		self.updateRadius()
		self.sprite = pyglet.sprite.Sprite(self.image, 0, 0)
		self.updatePos()
		
		Entity._new_entities.append(self)
		
	# ------------------------------------------------------------------------------
	def updateRadius(self):
		relevant_width = self.sprite_right - self.sprite_left
		relevant_height = self.sprite_bottom - self.sprite_top
		self.radius = (relevant_width + relevant_height) / 4	# /2 for diameter to radius; /2 for average
	
	# ------------------------------------------------------------------------------
	def updatePos(self):
		misc.setSpriteRenderPos(self.sprite, self.x, self.y, self.rotation)
		self.updateBoundaries()
		
	# ------------------------------------------------------------------------------
	def updateBoundaries(self):
		self.circle = (self.x, self.y, self.radius)
		render_left = self.x - self.half_width
		render_top = self.y - self.half_height
		self.rect = (render_left + self.sprite_left,  render_top + self.sprite_top,
					 render_left + self.sprite_right, render_top + self.sprite_bottom)
	
	# ------------------------------------------------------------------------------
	left =   lambda self: rectLeft(self.rect)
	top =    lambda self: rectTop(self.rect)
	right =  lambda self: rectRight(self.rect)
	bottom = lambda self: rectBottom(self.rect)
	
	# ------------------------------------------------------------------------------
	def setSpriteRotationFromDir(self, dir_x, dir_y):
		rotation = misc.getRotationFromDir(dir_x, dir_y)
		if rotation is None:
			return
		
		self.rotation = rotation
		self.updatePos()
	
	# ------------------------------------------------------------------------------
	def circlesCollide(self, entity):
		return misc.circlesOverlap(self.circle, entity.circle)
	
	# ------------------------------------------------------------------------------
	def rectsCollide(self, entity):
		return misc.rectsOverlap(self.rect, entity.rect)
	
	# ------------------------------------------------------------------------------
	def startDying(self):
		self.dying = True
		self.death_timer = DEATH_DURATION_SEC
		self.vx = 0
		self.vy = 0
		
	# ------------------------------------------------------------------------------
	def limitRight(self, right_limit):
		overlap = self.right() - right_limit
		if overlap > 0:
			self.x -= overlap
			self.updateBoundaries()
	
	# ------------------------------------------------------------------------------
	def limitLeft(self, left_limit):
		overlap = left_limit - self.left()
		if overlap > 0:
			self.x += overlap
			self.updateBoundaries()
	
	# ------------------------------------------------------------------------------
	def limitBottom(self, bottom_limit):
		overlap = self.bottom() - bottom_limit
		if overlap > 0:
			self.y -= overlap
			self.updateBoundaries()
	
	# ------------------------------------------------------------------------------
	def limitTop(self, top_limit):
		overlap = top_limit - self.top()
		if overlap > 0:
			self.y += overlap
			self.updateBoundaries()
	
	# ------------------------------------------------------------------------------
	def update(self, dt):
		self.prev_x = self.x
		self.prev_y = self.y
		self.prev_circle = self.circle
		self.prev_rect = self.rect
		
		self.x += self.vx * dt
		self.y += self.vy * dt
		self.updateBoundaries()
		
		if self.dying:
			self.death_timer -= dt
			opacity = 255 * self.death_timer / DEATH_DURATION_SEC
			self.sprite.opacity = opacity
			if hasattr(self, 'vision_sprite'):
				base_col = self.vision_sprite.base_col
				self.vision_sprite.color = tuple([int(float(opacity) * col / 255) for col in base_col])
			if self.death_timer <= 0:
				self.alive = False
			
		else:
			# Kill some things when they're off-screen
			if self.die_off_screen:
				if self.x >= g_window.width or self.x < 0 or self.y >= g_window.height or self.y < SCREEN_MINIMUM_Y:
					self.alive = False
			
			# Lock some things on screen
			if self.force_on_screen:
				self.limitRight(g_window.width)
				self.limitLeft(0)
				self.limitBottom(g_window.height)
				self.limitTop(SCREEN_MINIMUM_Y)
			
			if not self.dying:
				self.checkCollisions(dt)
		
		self.updatePos()
		
	# ------------------------------------------------------------------------------
	def draw(self):
		self.sprite.draw()
		
	# ------------------------------------------------------------------------------
	def checkCollisions(self, dt):
		# Check for collisions if moving
		stuck = False
		if self.vx != 0 or self.vy != 0:
			for entity in Entity._entities:
				if entity is self:
					continue
				if isinstance(self, LivingEntity) and isinstance(entity, LivingEntity):
					if self.circlesCollide(entity):
						#print self.name, 'collided with', entity.name
						# It's much easier to just stop the moving entity than limiting it
						self.x = self.prev_x
						self.y = self.prev_y
						self.collide_circle_duration += dt
					else:
						self.collide_circle_duration = 0
				else:
					if self.rectsCollide(entity):
						#print '%s (%.1f, %.1f, %.1f, %.1f) overlaps with %s (%.1f, %.1f, %.1f, %.1f)' % \
						#		(self.name, self.rect[0], self.rect[1], self.rect[2], self.rect[3],
						#		 entity.name, entity.rect[0], entity.rect[1], entity.rect[2], entity.rect[3])
						if self.vx > 0 and rectRight(self.prev_rect) <= entity.left():
							self.limitRight(entity.left())
						elif self.vx < 0 and rectLeft(self.prev_rect) >= entity.right():
							self.limitLeft(entity.right())
						if self.vy > 0 and rectBottom(self.prev_rect) <= entity.top():
							self.limitBottom(entity.top())
						elif self.vy < 0 and rectTop(self.prev_rect) >= entity.bottom():
							self.limitTop(entity.bottom())
						
						self.collide_rect_duration += dt
					else:
						self.collide_rect_duration = 0
				
			if misc.distSqBetween(self.x, self.y, self.prev_x, self.prev_y) < STUCK_DIST_SQ_LIMIT:
				stuck = True
		
		if stuck:
			self.stuck_duration += dt
		else:
			self.stuck_duration = 0
	
	# ------------------------------------------------------------------------------
	def alertGuardsInRange(self):
		# Work out which guards are within a short distance of this entity
		for entity in Entity._entities:
			if entity is self or not isinstance(entity, GuardEntity):
				continue
			dist = misc.distBetween(self.x, self.y, entity.x, entity.y)
			if dist < ALERT_MAX_RANGE:
				# Alert the guard and make them come to this location
				entity.alertTo(self.x, self.y)
	
	# ------------------------------------------------------------------------------
	@classmethod
	def updateAll(cls, dt):
		[entity.update(dt) for entity in cls._entities]
		cls._entities = [entity for entity in cls._entities if entity.alive]
		cls._entities.extend(cls._new_entities)
		cls._new_entities = []
		
	# ------------------------------------------------------------------------------
	@classmethod
	def drawAll(cls):
		[entity.draw() for entity in cls._entities]
	
	# ------------------------------------------------------------------------------
	@classmethod
	def clearAll(cls):
		cls._entities = []
		cls._new_entities = []

# ------------------------------------------------------------------------------
class HouseEntity(Entity):
	_index = 1
	# ------------------------------------------------------------------------------
	def __init__(self, x, y, size, loot_amount=-1, loot_difficulty=1):
		col = random.randint(1, 4)
		super(HouseEntity, self).__init__('data/textures/house{0}-{1}.jpg'.format(col, size), x, y)
		self.name = 'house ' + str(HouseEntity._index)
		HouseEntity._index += 1
		self.chest = ChestEntity(float(x), float(y) + self.height * 0.2)
		loot_half_width = self.width / 8
		self.loot_rect = [self.x - loot_half_width, self.top() - 32,
						  self.x + loot_half_width, self.top()]
		self.loot_difficulty = loot_difficulty
		self.loot_timer = None
		if loot_amount > 0:
			self.loot_amount = int(loot_amount * (0.9 + random.random() * 0.2))		# 10% variance on specified
		else:
			self.loot_amount = random.randint(90, 110)
		
	# ------------------------------------------------------------------------------
	def lootingDuration(self):
		return LOOT_DURATION_SEC * self.loot_difficulty
	
	# ------------------------------------------------------------------------------
	def startLooting(self):
		if self.chest is None:
			return
		if self.loot_timer is None:
			self.loot_timer = self.lootingDuration()	# otherwise leave as previous adjusted value
		stats.setLootingCompletion(0)
	
	# ------------------------------------------------------------------------------
	def stopLooting(self):
		self.loot_timer = (self.loot_timer + self.lootingDuration()) / 2
		stats.stopLooting()
	
	# ------------------------------------------------------------------------------
	def updateLooting(self, dt):
		"Returns True iff looting was completed."
		self.loot_timer -= dt
		if self.loot_timer > 0:
			stats.setLootingCompletion(1 - self.loot_timer / self.lootingDuration())
			return False
		self.chest.startDying()
		self.chest = None
		stats.addLoot(self.loot_amount)
		self.loot_amount = 0
		return True

# ------------------------------------------------------------------------------
class ChestEntity(Entity):
	_index = 1
	# ------------------------------------------------------------------------------
	def __init__(self, x, y):
		super(ChestEntity, self).__init__('data/textures/chest.png', x, y)
		self.name = 'chest ' + str(ChestEntity._index)
		ChestEntity._index += 1

# ------------------------------------------------------------------------------
class SpinnerEntity(Entity):
	# ------------------------------------------------------------------------------
	def __init__(self):
		super(SpinnerEntity, self).__init__('placeholders/textures/arrow.png', 200, 200)
		self.name = 'spinner'
		self.rotation = 0
		self.sprite.scale = 1.5
		
	# ------------------------------------------------------------------------------
	def update(self, dt):
		self.rotation += 90 * dt
		super(SpinnerEntity, self).update(dt)

# ------------------------------------------------------------------------------
class DaggerEntity(Entity):
	_index = 1
	# ------------------------------------------------------------------------------
	def __init__(self, x, y, dir_x, dir_y):
		"dir_x and dir_y should be -1, 0, or +1 to give a direction for the dagger."
		super(DaggerEntity, self).__init__('data/textures/dagger.png', x, y)
		self.name = 'dagger ' + str(DaggerEntity._index)
		DaggerEntity._index += 1
		self.die_off_screen = True
		self.move_speed = 300
		self.vx = dir_x * self.move_speed
		self.vy = dir_y * self.move_speed
		if dir_x != 0 and dir_y != 0:
			self.vx *= COS_45_DEG
			self.vy *= COS_45_DEG
		
		self.setSpriteRotationFromDir(dir_x, dir_y)
		
	# ------------------------------------------------------------------------------
	def update(self, dt):
		super(DaggerEntity, self).update(dt)
		if self.dying:
			return
		
	# ------------------------------------------------------------------------------
	def checkCollisions(self, dt):
		# Check collision with everything (except itself)
		for entity in Entity._entities:
			if entity is self:
				continue
			if self.rectsCollide(entity):
				if isinstance(entity, GuardEntity):
					entity.damage(1)
					self.startDying()
				elif isinstance(entity, HouseEntity):
					self.startDying()
					events.trigger('dagger_hit_house', self, very_low_priority=True)
					self.alertGuardsInRange()

# ------------------------------------------------------------------------------
class LivingEntity(Entity):
	# ------------------------------------------------------------------------------
	def __init__(self, img_fname, x=0, y=0):
		super(LivingEntity, self).__init__(img_fname, x, y)
		self.hp = 1		# anything above zero
		self.damage_timer = 0
	
	# ------------------------------------------------------------------------------
	def damage(self, amount):
		self.hp -= amount
		if self.hp <= 0 and not self.dying:
			self.startDying()
		else:
			self.damage_timer = DAMAGE_ANIM_DURATION_SEC
		
	# ------------------------------------------------------------------------------
	def startDying(self):
		super(LivingEntity, self).startDying()
		events.removeAllEventsForEntity(self)
		self.damage_timer = 0
		self.sprite.color = (255, 64, 64)
	
	# ------------------------------------------------------------------------------
	def update(self, dt):
		# Test the movement
		super(LivingEntity, self).update(dt)
		if self.damage_timer > 0:
			# Go red, then fade back to white
			self.damage_timer = max(self.damage_timer - dt, 0)
			damaged_col = 255 - 192 * self.damage_timer / DAMAGE_ANIM_DURATION_SEC
			self.sprite.color = (255, damaged_col, damaged_col)

# ------------------------------------------------------------------------------
class GuardEntity(LivingEntity):
	
	DECISION_INTERVAL_SEC = 0.5
	ALERT_PAUSE_SEC = 2.5
	
	PATROL_STATE = 0
	CHASE_STATE = 1
	ALERT_STATE = 2
	
	# ------------------------------------------------------------------------------
	def __init__(self, img_name, start_x, start_y, *args):
		super(GuardEntity, self).__init__(img_name, start_x, start_y)
		self.chat_col = (192, 192, 192, 255)
		self.hp = 2
		self.force_on_screen = True
		self.seen_player = False
		self.view_dist = 150
		self.patrol_speed = 60
		self.chase_speed = 100
		self.attack_recharge_timer = None
		self.min_time_between_attacks = 2
		self.dir_x = +1
		self.dir_y = 0
		self.type_name = 'guard'
		self.close_range_vision_min_cos = 0
		
		self.patrol_points = [(start_x, start_y)]
		self.next_patrol_point = 1
		self.patrol_point_direction = +1
		self.patrol_is_loop = False
		prev_coord = None
		next_coord_is_dir = False
		for coord in args:
			if coord == 'dir':
				next_coord_is_dir = True
				continue
			coord = int(coord)
			if prev_coord is not None:
				if next_coord_is_dir:
					self.dir_x = misc.sign(prev_coord)
					self.dir_y = misc.sign(coord)
					next_coord_is_dir = False
				else:
					self.patrol_points.append((prev_coord, coord))
				prev_coord = None
			elif not next_coord_is_dir and coord < 0:
				self.patrol_is_loop = True
			else:
				prev_coord = coord
		
		self.alert_x = None
		self.alert_y = None
		self.alert_timer = None
		self.decision_timer = 0
		self.decided_dir_x = 0
		self.decided_dir_y = 0
		self.decided_move_diagonally = False
		self.state = GuardEntity.PATROL_STATE
		
		self.vision_img = misc.getImage('data/textures/vision.jpg')
		self.vision_sprite = pyglet.sprite.Sprite(self.vision_img, 0, 0,
								blend_src=pyglet.gl.GL_SRC_COLOR, blend_dest=pyglet.gl.GL_ONE_MINUS_SRC_COLOR)
		self.vision_sprite.base_col = (255, 255, 255)
		self.vision_half_width = self.vision_img.width / 2
		self.vision_half_height = self.vision_img.height / 2
		self.updateVisionDisplay()
		
	# ------------------------------------------------------------------------------
	def updateVisionDisplay(self):
		offset_dist = self.half_width + self.vision_half_width
		diagonal = self.dir_x != 0 and self.dir_y != 0
		if diagonal:
			offset_dist *= COS_45_DEG
		
		rotation = misc.getRotationFromDir(self.dir_x, self.dir_y)
		if rotation is not None:
			self.vision_sprite.rotation = rotation
		
		vision_centre_x = self.x + self.dir_x * offset_dist
		vision_centre_y = self.y + self.dir_y * offset_dist
		misc.setSpriteRenderPos(self.vision_sprite, vision_centre_x, vision_centre_y, self.vision_sprite.rotation)
	
	# ------------------------------------------------------------------------------
	def setState(self, new_state):
		if new_state == self.state:
			return
		self.state = new_state
		if new_state == GuardEntity.CHASE_STATE:
			self.vision_sprite.base_col = (255, 96, 96)
		elif new_state == GuardEntity.ALERT_STATE:
			self.vision_sprite.base_col = (255, 255, 96)
		else:
			self.vision_sprite.base_col = (255, 255, 255)
		self.vision_sprite.color = self.vision_sprite.base_col
		
		self.alert_timer = None
	
	# ------------------------------------------------------------------------------
	def damage(self, amount):
		prev_hp = self.hp
		super(GuardEntity, self).damage(amount)
		if self.hp > 0:
			events.trigger(self.type_name + '_hit', self)
			self.spotPlayer()
			self.alertGuardsInRange()
		elif prev_hp > 0:		# just died
			events.trigger(self.type_name + '_death', self)
			stats.addKill(self.name)
	
	# ------------------------------------------------------------------------------
	def lookForPlayer(self, dt):
		if self.seen_player:
			return
		player = PlayerEntity.instance
		
		# Look for the player
		dist_to_player = misc.circleSeparation(self.circle, player.circle)
		if dist_to_player >= self.view_dist:
			return
		
		# Check the angle to the player using a dot product of the offset to the player with the facing direction
		offset_to_player_x = player.x - self.x
		offset_to_player_y = player.y - self.y
		offset_dot_facing = misc.normalisedDotProduct(offset_to_player_x, offset_to_player_y, self.dir_x, self.dir_y)
		# Must be the same direction and within 45 degrees - or for very small distances, within 90 degrees
		min_cos_angle = self.close_range_vision_min_cos if dist_to_player < 50 else COS_45_DEG
		if offset_dot_facing < min_cos_angle:
			return
		
		# Check if the player is visible by intersecting the line joining the centres with all of
		# the obstacles
		for entity in Entity._entities:
			if isinstance(entity, HouseEntity):		# can see through everything other than houses
				if misc.lineIntersectsRect(player.x, player.y, self.x, self.y, entity.rect):
					#print self.name, "can't see the player because", entity.name, 'is in the way'
					return
		
		events.trigger(self.type_name + '_saw_player', self)
		self.spotPlayer()
		
	# ------------------------------------------------------------------------------
	def spotPlayer(self):
		PlayerEntity.instance.setSpotted(True)
		self.setState(GuardEntity.CHASE_STATE)
		self.seen_player = True
		
		self.alertGuardsInRange()
	
	# ------------------------------------------------------------------------------
	def think(self, dt):
		last_vx = self.vx
		last_vy = self.vy
		self.vx = 0
		self.vy = 0
		
		player = PlayerEntity.instance
		if player.dying or not player.alive:
			return
		
		self.lookForPlayer(dt)
		
		objective_x = None
		objective_y = None
		move_speed = self.patrol_speed
		chasing_player = False
		if self.seen_player:
			# Chase the player
			chasing_player = True
			objective_x = player.x
			objective_y = player.y
			move_speed = self.chase_speed
			range_to_reach = self.radius + player.radius + 5	# max attack distance
		elif self.alert_x is not None:
			objective_x = self.alert_x
			objective_y = self.alert_y
			range_to_reach = 20		# arbitrary
		else:
			# Patrol
			if self.next_patrol_point < len(self.patrol_points):
				point = self.patrol_points[self.next_patrol_point]
				objective_x = point[0]
				objective_y = point[1]
				range_to_reach = 5
			
		if self.decision_timer > 0:
			self.decision_timer -= dt
		
		if objective_x is not None:
			# Move towards the objective
			offset_to_objective_x = objective_x - self.x
			offset_to_objective_y = objective_y - self.y
			
			move_diagonally = False
			abs_offset_x = abs(offset_to_objective_x)
			abs_offset_y = abs(offset_to_objective_y)
			if abs_offset_x > 0 and abs_offset_y > 0:		# avoid division by zero
				# If the offsets are reasonably similar, go diagonally; otherwise, go straight
				ratio = abs_offset_x / abs_offset_y
				if ratio < 1:
					ratio = 1 / ratio
				if ratio < 1.1:
					move_diagonally = True
			
			desired_dir_x = -1 if offset_to_objective_x < 0 else +1
			desired_dir_y = -1 if offset_to_objective_y < 0 else +1
			
			# Go with the previous decision for a set time
			if self.decision_timer > 0:
				desired_dir_x = self.decided_dir_x
				desired_dir_y = self.decided_dir_y
				move_diagonally = self.decided_move_diagonally
			else:
				# Change the decision if we're stuck
				if self.stuck_duration > 0:
					if self.decision_timer <= 0:
						# Make a decision
						self.decision_timer = GuardEntity.DECISION_INTERVAL_SEC
						if abs_offset_x > 0 and abs_offset_y > 0:
							# Moving diagonally is an option.  If our decision was the same as the current idea,
							# try the opposite
							if move_diagonally == self.decided_move_diagonally:
								move_diagonally = not move_diagonally
							else:
								# We tried changing move_diagonally, or it isn't relevant.
								# Move directly in the direction with the smaller offset (but possibly the other way)
								if abs_offset_x > abs_offset_y:
									desired_dir_x = 0
									if desired_dir_y == 0:
										desired_dir_y = -1 if random.randint(0, 1) == 0 else +1
									elif random.randint(0, 3) == 0:
										desired_dir_y = -desired_dir_y	# randomly switch every now and then
								else:
									desired_dir_y = 0
									if desired_dir_x == 0:
										desired_dir_x = -1 if random.randint(0, 1) == 0 else +1
									elif random.randint(0, 3) == 0:
										desired_dir_x = -desired_dir_x	# randomly switch every now and then
				else:
					# Follow the basic target
					if not move_diagonally:
						# Zero one of the directions
						if abs_offset_x > abs_offset_y:
							desired_dir_y = 0
						else:
							desired_dir_x = 0
				
				self.decided_dir_x = desired_dir_x
				self.decided_dir_y = desired_dir_y
				self.decided_move_diagonally = move_diagonally
			
			if move_diagonally:
				move_speed *= COS_45_DEG
			self.vx = desired_dir_x * move_speed
			self.vy = desired_dir_y * move_speed
			
			# Check if in range of the objective
			if abs_offset_x * abs_offset_x + abs_offset_y * abs_offset_y < range_to_reach * range_to_reach:
				# In range
				if chasing_player:
					# Can hit the player
					if self.attack_recharge_timer is None:
						events.trigger(self.type_name + '_hit_player', self)
						player.damage(1)
						self.attack_recharge_timer = self.min_time_between_attacks
				elif self.alert_x is not None:
					# Reached the objective, but nothing happened
					# Pause for a bit, and then go back to it
					if self.alert_timer is None:
						self.alert_timer = GuardEntity.ALERT_PAUSE_SEC
					else:
						self.alert_timer -= dt
						if self.alert_timer <= 0:
							self.alert_x = None
							self.alert_y = None
							self.setState(GuardEntity.PATROL_STATE)
				else:
					# Reached a patrol point
					self.next_patrol_point += self.patrol_point_direction
					num_patrol_points = len(self.patrol_points)
					patrol_finished = False
					if self.next_patrol_point < 0:
						self.next_patrol_point = (num_patrol_points - 1) if self.patrol_is_loop else 1
						patrol_finished = True
					elif self.next_patrol_point >= num_patrol_points:
						self.next_patrol_point = 0 if self.patrol_is_loop else (num_patrol_points - 2)
						patrol_finished = True
					if patrol_finished and not self.patrol_is_loop:
						self.patrol_point_direction = -self.patrol_point_direction
			
			if self.vx != 0 or self.vy != 0:
				self.dir_x = misc.sign(self.vx)
				self.dir_y = misc.sign(self.vy)
	
	# ------------------------------------------------------------------------------
	def alertTo(self, x, y):
		# Make the guard go towards the location - unless they're already chasing the player
		if self.seen_player:
			return
		self.alert_x = x
		self.alert_y = y
		self.setState(GuardEntity.ALERT_STATE)
	
	# ------------------------------------------------------------------------------
	def update(self, dt):
		if not self.dying:
			self.think(dt)
		
		if self.attack_recharge_timer is not None:
			self.attack_recharge_timer -= dt
			if self.attack_recharge_timer <= 0:
				self.attack_recharge_timer = None
		
		super(GuardEntity, self).update(dt)
		self.updateVisionDisplay()
	
	# ------------------------------------------------------------------------------
	def draw(self):
		self.vision_sprite.draw()
		super(GuardEntity, self).draw()

# ------------------------------------------------------------------------------
class HumanGuardEntity(GuardEntity):
	# ------------------------------------------------------------------------------
	def __init__(self, name, start_x, start_y, *args):
		super(HumanGuardEntity, self).__init__('data/textures/guard.png', start_x, start_y, *args)
		self.name = name + ' the Guard'
		self.loot_amount = random.randint(5, 15)
		
		self.sprite_left = 4
		self.sprite_right = 29
		self.updateRadius()

# ------------------------------------------------------------------------------
class GuardDogEntity(GuardEntity):
	# ------------------------------------------------------------------------------
	def __init__(self, name, start_x, start_y, *args):
		super(GuardDogEntity, self).__init__('data/textures/dog.png', start_x, start_y, *args)
		self.name = name + ' the dog'
		self.type_name = 'dog'
		self.close_range_vision_min_cos = -COS_45_DEG	# dogs can see further at very close range (smell, etc)
		self.loot_amount = 0
		
		self.sprite_left = 3
		self.sprite_right = 30
		self.updateRadius()

# ------------------------------------------------------------------------------
class PlayerEntity(LivingEntity):
	instance = None
	
	LEFT_KEYS =    (key.LEFT, key.NUM_LEFT, key.NUM_4, key.NUM_HOME, key.NUM_7, key.NUM_END, key.NUM_1, key.HOME, key.END)
	RIGHT_KEYS =   (key.RIGHT, key.NUM_RIGHT, key.NUM_6, key.NUM_PAGE_UP, key.NUM_9, key.NUM_PAGE_DOWN, key.NUM_3, key.PAGEUP, key.PAGEDOWN)
	UP_KEYS =      (key.UP, key.NUM_UP, key.NUM_8, key.NUM_HOME, key.NUM_7, key.NUM_PAGE_UP, key.NUM_9, key.HOME, key.PAGEUP)
	DOWN_KEYS =    (key.DOWN, key.NUM_DOWN, key.NUM_2, key.NUM_END, key.NUM_1, key.NUM_PAGE_DOWN, key.NUM_3, key.END, key.PAGEDOWN)
	FIRE_KEYS =    (key.LCTRL, key.RCTRL)
	LOOT_KEY =      key.SPACE
	
	MAX_DIST_TO_PICKPOCKET = 10		# not including entity radii
	
	# ------------------------------------------------------------------------------
	def __init__(self, x, y, initial_daggers=10):
		PlayerEntity.instance = self
		super(PlayerEntity, self).__init__('data/textures/thief.png', x, y)
		self.name = 'Kane'
		self.chat_col = (80, 80, 80, 255)
		self.max_hp = 3
		self.hp = self.max_hp
		self.move_speed = 130
		self.dir_x = +1
		self.dir_y = 0
		self.firing = False
		self.force_on_screen = True
		self.loot_target = None
		self.ever_spotted = False
		
		self.sprite_left = 6
		self.sprite_right = 27
		self.updateRadius()
		
		stats.daggers = initial_daggers
		
	# ------------------------------------------------------------------------------
	def setSpotted(self, spotted):
		if self.ever_spotted == spotted:
			return
		self.ever_spotted = spotted
		if spotted:
			events.trigger('player_spotted', self, low_priority=True)
		
	# ------------------------------------------------------------------------------
	def damage(self, amount):
		prev_hp = self.hp
		super(PlayerEntity, self).damage(amount)
		stats.updateHealth(self.hp, self.max_hp)
		if prev_hp > 0 and (self.dying or not self.alive):
			if self.loot_target is not None:
				self.loot_target.stopLooting()
				self.loot_target = None
			stats.reportDeath()
			events.trigger('player_death', self, low_priority=True)
	
	# ------------------------------------------------------------------------------
	def processInput(self, dt):
		# Movement
		if misc.isAnyKeyHeld(PlayerEntity.LEFT_KEYS):
			self.vx -= self.move_speed
		if misc.isAnyKeyHeld(PlayerEntity.RIGHT_KEYS):
			self.vx += self.move_speed
		if misc.isAnyKeyHeld(PlayerEntity.UP_KEYS):
			self.vy += self.move_speed
		if misc.isAnyKeyHeld(PlayerEntity.DOWN_KEYS):
			self.vy -= self.move_speed
		# Scale diagonal movement so it's the same speed
		if self.vx != 0 and self.vy != 0:
			self.vx *= COS_45_DEG
			self.vy *= COS_45_DEG
		
		# Direction: only stored when moving in some direction
		if self.vx != 0 or self.vy != 0:
			if self.vx == 0:
				self.dir_x = 0
			else:
				self.dir_x = -1 if self.vx < 0 else +1
			if self.vy == 0:
				self.dir_y = 0
			else:
				self.dir_y = -1 if self.vy < 0 else +1
		
		# Firing
		if misc.isAnyKeyHeld(PlayerEntity.FIRE_KEYS):
			if not self.firing and stats.haveDagger():
				self.firing = True
				events.trigger('threw_dagger', self)
				stats.removeDagger()
				dagger = DaggerEntity(self.x, self.y, self.dir_x, self.dir_y)
				dagger.x += (self.half_width + dagger.half_width - 4) * self.dir_x	# -4 for width in texture
				dagger.y += (self.half_height + dagger.half_height) * self.dir_y
				dagger.updatePos()
		else:
			self.firing = False
		
		self.checkLooting(dt)
		
	# ------------------------------------------------------------------------------
	def checkLooting(self, dt):
		loot_target = None
		if misc.isKeyHeld(PlayerEntity.LOOT_KEY):
			for entity in Entity._entities:
				if isinstance(entity, HouseEntity):
					if entity.chest is not None and misc.rectsOverlap(self.rect, entity.loot_rect):
						loot_target = entity
				elif isinstance(entity, HumanGuardEntity):
					if entity.loot_amount > 0 and not entity.seen_player:
						dist_to_guard = misc.distBetween(self.x, self.y, entity.x, entity.y)
						dist_to_guard -= self.radius + entity.radius
						if dist_to_guard <= PlayerEntity.MAX_DIST_TO_PICKPOCKET:
							# Pickpocket the guard
							events.trigger('pickpocketed_guard', self)
							stats.addLoot(entity.loot_amount, pickpocket_target=entity)
							entity.loot_amount = 0
							return
						
		if loot_target != self.loot_target:
			# Loot target changed
			if self.loot_target is not None:
				self.loot_target.stopLooting()
			self.loot_target = loot_target
			if self.loot_target is not None:
				self.loot_target.startLooting()
		elif loot_target is not None:
			if self.loot_target.updateLooting(dt):
				# Checking only for chests on houses, as they may be fading out ("dying")
				won = not any((isinstance(entity, HouseEntity) and entity.chest is not None \
								for entity in Entity._entities))
				if won:
					events.trigger('won_level', self)
					stats.setWonLevel()
				else:
					events.trigger('looted_chest', self)
				self.loot_target = None
	
	# ------------------------------------------------------------------------------
	def update(self, dt):
		self.vx = 0
		self.vy = 0
		if not self.dying and self.alive:
			self.processInput(dt)
		
		super(PlayerEntity, self).update(dt)

# ------------------------------------------------------------------------------

updateAll = Entity.updateAll
drawAll = Entity.drawAll
clearAll = Entity.clearAll

# ------------------------------------------------------------------------------
