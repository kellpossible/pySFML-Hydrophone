import sfml as sf
import time
from Vector import Vector3, Rotation
from ecs.models import Entity, Component, System
from ecs.managers import EntityManager, SystemManager
from math import *

def doppler_test():
	try: buffer = sf.SoundBuffer.from_file("engine_idle_freesound_loop.wav")
	except IOError: exit(1)

	sound = sf.Sound()
	sound.buffer = buffer
	sound.loop = True
	sound.attenuation = 0.05
	sound.play()

	speed_sound = 150
	base_pitch = 1.0
	pos = Vector3(-500, 40, 0)
	old_distance = pos.mag()
	vel = Vector3(40, 0, 0)

	old_time = time.clock()

	def to_sf_vector(v):
		return sf.Vector3(v.x, v.y, v.z)


	while True:
		new_time = time.clock()
		dt = new_time - old_time
		pos = pos.add(vel.fmul(dt))
		new_distance = pos.mag()
		sound.position = to_sf_vector(pos)

		rel_vel = (old_distance - new_distance)/dt

		new_pitch = speed_sound/(speed_sound - rel_vel)
		#print(new_pitch)
		#print(pos, rel_vel)
		sound.pitch = new_pitch
		old_time = new_time
		old_distance = new_distance


class SoundComponent(Component):
	def __init__(self, soundfile):
		self.soundfile = soundfile

		self.sound = sf.Sound()
		try: buffer = sf.SoundBuffer.from_file(soundfile)
		except IOError: exit(1)
		self.sound.buffer = buffer

class PositionSoundComponent(SoundComponent):
	def __init__(self, soundfile, attenuation=0.1):
		super(PositionSoundComponent, self).__init__(soundfile)
		self.sound.attenuation = attenuation
		self.distance = 0.0

class ScanSoundComponent(SoundComponent):
	pass

class VectorComponent(Component):
	def __init__(self, x, y, z):
		super(VectorComponent, self).__init__()
		self.x = x
		self.y = y
		self.z = z

	def toSFMLVector3(self):
		return sf.Vector3(self.x, self.y, self.z)

	def toSFMLVector2(self):
		return sf.Vector2(self.x, self.y)

	def toVector3(self):
		return Vector3(self.x, self.y, self.z)

	def applyVector3(self, v):
		self.x = v.x
		self.y = v.y
		self.z = v.z

	def __repr__(self):
		return str(type(self)) + "(x: {0} y: {1} z: {2})".format(self.x, self.y, self.z)

class PositionComponent(VectorComponent):
	pass

class VelocityComponent(VectorComponent):
	pass

class DirectionComponent(Component):
	def __init__(self, angle):
		super(DirectionComponent, self).__init__()
		self.angle = angle

	def getDirectionVec(self):
		rot = Rotation.aroundZ(self.angle)
		return Vector3.Y().rotate(rot)

class DrawableComponent(Component):
	def __init__(self, draw_obj):
		super(DrawableComponent, self).__init__()
		self.draw_obj = draw_obj

def vec_to_tuple(v):
	return (v.x, v.y)

def vec_to_SFMLVector3(v):
	return sf.Vector3(v.x, v.y, v.z)

def vec_to_SFMLVector2(v):
	return sf.Vector2(v.x, v.y)

class Line(sf.VertexArray):
	@staticmethod
	def fromAngle(start_point, angle, length, color=sf.Color.WHITE):
		start_point_vec = Vector3(start_point.x, start_point.y, 0)
		rot = Rotation.aroundZ(angle)
		line_vec = Vector3.Y().rotate(rot).fmul(length)
		end_point_vec = start_point_vec.add(line_vec)
		return Line(start_point_vec,end_point_vec, color)
	def __init__(self, start_point, end_point, color=sf.Color.WHITE):
		super(Line, self).__init__(sf.PrimitiveType.LINES, 2)
		self.color = color
		self.set_start_point(start_point)
		self.set_end_point(end_point)
		

	def set_start_point(self, p):
		self[0] = sf.Vertex((p.x, p.y), self.color)

	def get_start_point(self):
		return self[0]

	def set_end_point(self, p):
		self[1] = sf.Vertex((p.x, p.y), self.color)

	def get_end_point(self):
		return self[1]

	def __repr__(self):
		return "Start: " + str(self.get_start_point()) + " End: " + str(self.get_end_point())

class HydrophoneComponent(Component):
	def __init__(self, angle):
		super(HydrophoneComponent, self).__init__()
		self.angle = angle

	def getDirectionVec(self):
		rot = Rotation.aroundZ(self.angle)
		return Vector3.Y().rotate(rot)

class AudioListenerComponent(Component):
	pass

class MovementControlComponent(Component):
	pass


class RenderSystem(System):
	def __init__(self, window):
		super(RenderSystem, self).__init__()
		self.window = window

	def update(self, dt):
		self.window.clear(sf.Color.BLACK)

		em = self.entity_manager
		drawable_dic = em.match_component_types(PositionComponent, DrawableComponent)
		drawable_direction_dic = em.match_component_types(PositionComponent, DrawableComponent, DirectionComponent)

		hydrophone_dic = em.match_component_types(PositionComponent,
			DrawableComponent,
			HydrophoneComponent)

		for entity, component_dic in drawable_dic.items():
			pos_component = component_dic[PositionComponent]
			drawable_component = component_dic[DrawableComponent]
			draw_obj = drawable_component.draw_obj
			if type(draw_obj) == sf.CircleShape:
				init_pos = pos_component.toVector3()
				final_pos = init_pos.sub(Vector3(draw_obj.radius, draw_obj.radius))
				draw_obj.position = vec_to_SFMLVector2(final_pos)
			else:
				draw_obj.position = pos_component.toSFMLVector2()

			self.window.draw(draw_obj)

		#Hydrophone
		for entity, component_dic in hydrophone_dic.items():
			pos_component = component_dic[PositionComponent]
			angle = component_dic[HydrophoneComponent].angle
			line = Line.fromAngle(pos_component.toSFMLVector2(), angle, 50)
			draw_obj.position = pos_component.toSFMLVector2()
			draw_obj.rotation = angle
			self.window.draw(line)

		#Direction Line
		for entity, component_dic in drawable_direction_dic.items():
			pos_component = component_dic[PositionComponent]
			angle = component_dic[DirectionComponent].angle
			line = Line.fromAngle(pos_component.toSFMLVector2(), angle, 20, sf.Color.RED)
			draw_obj.position = pos_component.toSFMLVector2()
			draw_obj.rotation = angle
			self.window.draw(line)


class AudioSystem(System):
	def __init__(self):
		super(AudioSystem, self).__init__()
		self.first_loop = True
		self.speed_sound = 250.3 #used in doppler effect

	def update(self, dt):
		em = self.entity_manager
		listeners = em.match_component_types(PositionComponent, AudioListenerComponent, DirectionComponent)
		listener_entity = None
		listener_pos = None
		for entity, component_dic in listeners.items():
			pos_component = component_dic[PositionComponent]
			dir_component = component_dic[DirectionComponent]
			listener_pos = pos_component.toVector3()
			sf.Listener.set_position(sf.Vector3(listener_pos.x, 0, listener_pos.y))
			dir_vec = dir_component.getDirectionVec()
			sf.Listener.set_direction(sf.Vector3(dir_vec.x, 0, dir_vec.y)) #is this correct???
			listener_entity = entity


		position_sounds = em.match_component_types(PositionSoundComponent, PositionComponent)
		for entity, component_dic in position_sounds.items():
			sound_component = component_dic[PositionSoundComponent]
			pos_component = component_dic[PositionComponent]
			pos_vec = pos_component.toVector3()
			sound_component.sound.position = sf.Vector3(pos_vec.x, 0, pos_vec.y)
			#sound_component.sound.position = vec_to_SFMLVector3(listener_pos)

			if self.first_loop:
				sound_component.sound.play()
				#setup for doppler effect
				sound_component.distance = pos_vec.sub(listener_pos).mag()
			
			#doppler effect
			if not self.first_loop:
				old_distance = sound_component.distance
				new_distance = pos_vec.sub(listener_pos).mag()
				dt_float = dt_as_float(dt)
				rel_vel = (old_distance - new_distance)/dt_float
				new_pitch = self.speed_sound/(self.speed_sound - rel_vel)
				sound_component.sound.pitch = new_pitch
				sound_component.distance = new_distance

		self.first_loop = False

def dt_as_float(dt):
	return dt.microseconds * 1.0e-6
class PhysicsSystem(System):
	def update(self, dt):
		em = self.entity_manager
		moving_entities = em.match_component_types(MovementControlComponent, VelocityComponent, PositionComponent)

		for entity, component_dic in moving_entities.items():
			vel_component = component_dic[VelocityComponent]
			pos_component = component_dic[PositionComponent]
			pos_vec = pos_component.toVector3()
			vel_vec = vel_component.toVector3()
			dt_float = dt_as_float(dt)
			pos_vec_new = pos_vec.add(vel_vec.fmul(dt_float))
			pos_component.applyVector3(pos_vec_new)

class InputSystem(System):
	def __init__(self, window):
		super(InputSystem, self).__init__()
		self.window = window
		self.movement_speed = 50

	def update(self, dt):
		em = self.entity_manager
		movement_entities = em.match_component_types(MovementControlComponent, VelocityComponent)

		for entity, component_dic in movement_entities.items():
			vel_component = component_dic[VelocityComponent]
			vel_dir = Vector3()

			if sf.Keyboard.is_key_pressed(sf.Keyboard.LEFT):
				vel_dir = vel_dir.add(Vector3(-1, 0, 0))

			if sf.Keyboard.is_key_pressed(sf.Keyboard.RIGHT):
				vel_dir = vel_dir.add(Vector3(1, 0, 0))

			if sf.Keyboard.is_key_pressed(sf.Keyboard.UP):
				vel_dir = vel_dir.add(Vector3(0, -1, 0))

			if sf.Keyboard.is_key_pressed(sf.Keyboard.DOWN):
				vel_dir = vel_dir.add(Vector3(0, 1, 0))

			vel_component.applyVector3(vel_dir.fmul(self.movement_speed))

class MyEntityManager(EntityManager):
	def match_component_types(self, *component_type_list):
		entity_dic = {}
		n_components = len(component_type_list)
		for component_type, components in self._database.items():
			if component_type not in component_type_list:
				continue

			for entity, component in components.items():
				if entity not in entity_dic.keys():
					entity_dic[entity] = {}

				entity_dic[entity][component_type] = component

		remove_entity_list = []
		for entity, component_dic in entity_dic.items():
			if len(component_dic) != n_components:
				remove_entity_list.append(entity)

		for entity in remove_entity_list:
			entity_dic.pop(entity)

		return entity_dic

	def entity_get_component(self, entity, component_type):
		if entity in self._database[component_type]:
			return self._database[component_type][entity]
		else:
			return None

def scanner_test():
	w = sf.RenderWindow(sf.VideoMode(400, 400), "Scanner Test")
	clock = sf.Clock()

	em = MyEntityManager()
	sm = SystemManager(em)

	car1 = em.create_entity()
	em.add_component(car1, PositionComponent(0,0,0))
	em.add_component(car1, VelocityComponent(0,0,0))
	car1_circle = sf.CircleShape()
	car1_circle.radius = 10
	car1_circle.fill_color = sf.Color.RED
	em.add_component(car1, DrawableComponent(car1_circle))
	em.add_component(car1, MovementControlComponent())
	em.add_component(car1, ScanSoundComponent("engine_idle_freesound_loop.wav"))
	car1_engine_sound = PositionSoundComponent("engine_idle_freesound_loop.wav")
	car1_engine_sound.sound.loop = True
	em.add_component(car1, car1_engine_sound)


	player = em.create_entity()
	em.add_component(player, PositionComponent(100,100,0))
	em.add_component(player, VelocityComponent(0,0,0))
	em.add_component(player, DirectionComponent(radians(180)))
	player_circle = sf.CircleShape()
	player_circle.radius = 10
	player_circle.fill_color = sf.Color.WHITE
	em.add_component(player, DrawableComponent(player_circle))
	#em.add_component(player, MovementControlComponent())
	em.add_component(player, AudioListenerComponent())
	em.add_component(player, HydrophoneComponent(radians(0)))
	
	sm.add_system(InputSystem(w))
	sm.add_system(PhysicsSystem())
	sm.add_system(AudioSystem())
	sm.add_system(RenderSystem(w))

	while w.is_open:
		sm.update(clock.restart())

		for event in w.events:
			if type(event) is sf.CloseEvent:
				w.close()

		#
		w.display()

if __name__ == "__main__":
	scanner_test()