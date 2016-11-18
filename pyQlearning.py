import socket
import sys
from array import array
import struct
import random
import math

class State(object):
	def __init__(self, ammo_info, enemy_info, powerUp_info, hero_info):
		self.ammo_info = ammo_info
		self.enemy_info = enemy_info
		self.powerUp_info = powerUp_info
		self.hero_info = hero_info

class Qlearning(object):
	def __init__(self, tp = 'simple'):
		self.iter_num = 0
		self.actions = ['w', 'a', 's', 'd', '0']
		self.eta = 0.000001
		self.extractor = Feature_extractor(tp)
		self.feature_num = self.extractor.feature_num
		self.weight = {act:[0 for _ in range(self.feature_num)] for act in self.actions}

	def learn(self, old_state, action, new_state):
		old_feature = self.extractor.extract(old_state)
		new_feature = self.extractor.extract(new_state)
		reward = self.extractor.reward(old_feature, new_feature, old_state, new_state, action)
		old_Q = dotProduct(self.weight[action], old_feature)
		new_opt_Q = float('-inf')
		new_opt_action = '0'
		for act in self.actions:
			new_Q = dotProduct(self.weight[act], new_feature)
			if new_opt_Q < new_Q:
				new_opt_action = act
				new_opt_Q = new_Q

		# Update weight
		delta = self.eta * (old_Q -reward - new_opt_Q)
		if self.iter_num % 1000 == 0:
			print '============'
			print reward
			print(str(old_Q) + ' + ' + str(old_state.hero_info[8]) + ' = ' + str(old_Q + old_state.hero_info[8]))
			print(str(new_opt_Q) + ' + ' + str(new_state.hero_info[8]) + ' = ' + str(new_opt_Q + new_state.hero_info[8]))
		for i in range(self.feature_num):
			self.weight[action][i] = self.weight[action][i] - delta * old_feature[i]

		# Return chosen action
		epsilon = self.epsilon()
		self.iter_num = self.iter_num + 1
		if self.iter_num % 1000 == 0:
			file_object = open('weight_simple.txt', 'w')
			for act in self.actions:
				file_object.writelines((act) + '\r\n')
				for i in range(self.feature_num):
					file_object.writelines(str(self.weight[act][i]) + '\r\n')
			file_object.close()
		if random.random() <= epsilon:
			return random.choice(self.actions)
		else:
			return new_opt_action

	def learnEnd(self, old_state, action):
		old_feature = self.extractor.extract(old_state)
		old_Q = dotProduct(self.weight[action], old_feature)

		# Update weight
		delta = self.eta * (old_Q - 30 - 0)
		for i in range(self.feature_num):
			self.weight[action][i] = self.weight[action][i] - delta * old_feature[i]

	def loadWeight(self, filePath):
		file_object = open(filePath, 'r')
		for i in range(len(self.actions)):
			act = file_object.readline()
			act = act[0]
			for j in range(self.feature_num):
				self.weight[act][j] = float(file_object.readline())
		file_object.close()

	def optAction(self, state):
		feature = self.extractor.extract(state)
		opt_Q = float('-inf')
		opt_action = '0'
		for act in self.actions:
			Q = dotProduct(self.weight[act], feature)
			if opt_Q < Q:
				opt_action = act
				opt_Q = Q
		return opt_action

	def epsilon(self):
		if self.iter_num % 10000 < 3000:
			return 0.9
		elif self.iter_num % 10000 < 6000:
			return 0.3
		elif self.iter_num % 10000 < 8000:
			return 0.02
		else:
			return 0.0

		
class Feature_extractor(object):
	def __init__(self, tp = 'simple'):
		if tp == 'simple':
			self.extract = self.extract_simple
			self.feature_num = 193
			self.reward = self.reward_simple

	def extract_simple(self, state):
		feature = [0 for _ in range(self.feature_num)]
		hero_x = state.hero_info[0]
		hero_y = state.hero_info[1]

		# Ammo features: 8 + 64 = 72 (0:72)
		if state.ammo_info != None:
			bias = 0
			bias2 = 8
			for ammo in state.ammo_info:
				ammo_x = ammo[0]
				ammo_y = ammo[1]
				ammo_vx = ammo[2]
				ammo_vy = ammo[3]

				# Ammo position features: 8 (0:8)
				x = ammo_x - hero_x
				y = ammo_y - hero_y
				if x * x + y * y > 49:
					continue
				if x == 0:
					x = 0.00000001
				tan = y / x
				region = self.calculateRegion(tan, x, y)
				feature[bias + region] = feature[bias + region] + 1

				# Ammo speed features: 64 (8:72)
				if ammo_vx == 0:
					ammo_vx = 0.00000001
				tan_v = ammo_vy / ammo_vx
				direction = self.calculateRegion(tan_v, ammo_vx, ammo_vy)
				feature[bias2 + direction + region * 8] = feature[bias2 + direction + region * 8] + 1

		# Enemy features: 5 + 56 = 61 (72:133)
		if state.enemy_info != None:
			bias = 72
			bias2 = 77
			for enemy in state.enemy_info:
				enemy_x = enemy[0]
				enemy_y = enemy[1]
				enemy_tp = enemy[2]

				# Foward enemy position features: 5 (72:77)
				x = enemy_x - hero_x
				y = enemy_y - hero_y
				if y > 1:
					if x < 1 and x > -1:
						feature[bias] = feature[bias] + 1
					elif x >= 1 and x < 4:
						feature[bias + 1] = feature[bias + 1] + 1
					elif x <= -1 and x > -4:
						feature[bias + 2] = feature[bias + 2] + 1
					elif x >= 4 and x < 8:
						feature[bias + 3] = feature[bias + 3] + 1
					elif x <= -4 and x > -8:
						feature[bias + 4] = feature[bias + 4] + 1

				# Nearby enemy position features: 56 (77:133)
				if x * x + y * y > 49:
					continue
				if x == 0:
					x = 0.00000001
				tan = y / x
				region = self.calculateRegion(tan, x, y)
				slot = region * 7 + ord(enemy_tp)
				feature[bias2 + slot] = feature[bias2 + slot] + 1

		# PowerUp features: 48 (133:181)
		if state.powerUp_info != None:
			bias = 133
			for powerUp in state.powerUp_info:
				powerUp_x = powerUp[0]
				powerUp_y = powerUp[1]
				powerUp_tp = powerUp[2]

				# PowerUp position features: 5 (72:77)
				x = powerUp_x - hero_x
				y = powerUp_y - hero_y
				if x * x + y * y > 36:
					continue
				if x == 0:
					x = 0.00000001
				tan = y / x
				region = self.calculateRegion(tan, x, y)
				slot = region * 6 + ord(powerUp_tp)
				feature[bias + slot] = feature[bias + slot] + 1

		# Hero features: 1+1+3+1+1+4+3 = 11 (181:195)
		bias = 181
		feature[bias] = 0 # Hero damage taken: 1 (181:182)
		feature[bias + 1] = 0 # Hero lives: 1 (182:183)

		# Hero 3 types of powerful guns: 3 (183:186)
		feature[bias + 2] = state.hero_info[4]
		feature[bias + 3] = state.hero_info[5]
		feature[bias + 4] = state.hero_info[6]

		feature[bias + 5] = 0 # Hero shields: 1 (186:187)
		feature[bias + 6] = 0 # Hero scores: 1 (187:188)

		# Hero is near map boundary: 4 (188:192)
		feature[bias + 7] = int(hero_x > 9)
		feature[bias + 8] = int(hero_x < -9)
		feature[bias + 9] = int(hero_y > 7)
		feature[bias + 10] = int(hero_y < -7)

		# Hero is near center X feature: 1 (192:193)
		feature[bias + 11] = int(hero_x < 3 and hero_x > -3)

		return feature

	def calculateRegion(self, tan, x, y):
		if tan <= 1 and tan >= 0 and x >= 0:
			region = 0
		elif tan >= 1 and y >= 0:
			region = 1
		elif tan <= -1 and y >= 0:
			region = 2
		elif tan >= -1 and tan <= 0 and x <= 0:
			region = 3
		elif tan <= 1 and tan >= 0 and x <= 0:
			region = 4
		elif tan >= 1 and y <= 0:
			region = 5
		elif tan <= -1 and y <= 0:
			region = 6
		elif tan >= -1 and tan <= 0 and x >= 0:
			region = 7
		else:
			region = 7
		return region

	def reward_naive(self, old_feature, new_feature, old_state, new_state, action):
		return new_feature[187] - old_feature[187]

	def reward_simple(self, old_feature, new_feature, old_state, new_state, action):
		reward = 0

		taken_damage = 0
		# Hero taken damage reward:
		taken_damage = taken_damage + old_feature[181] - new_feature[181]
		# Hero shields reward:
		if old_feature[186] > 500:
			taken_damage = taken_damage + (new_feature[186] - old_feature[186] + 0.75) * 2
		else:
			taken_damage = taken_damage + (new_feature[186] - old_feature[186]) * 2
		if taken_damage < -10:
			reward = reward + taken_damage * 0.5
			#print 'damage reward: ' + str(reward)
			return reward
		elif taken_damage > 10:
			reward = reward + taken_damage * 4
			#print 'damage reward: ' + str(reward)
			return reward

		# Hero gaining gun reward:
		reward = reward + (new_feature[183] - old_feature[183]) * 2000
		reward = reward + (new_feature[184] - old_feature[184]) * 2000
		reward = reward + (new_feature[185] - old_feature[185]) * 2000
		# Hero gaining life reward:
		reward = reward + (new_feature[182] - old_feature[182]) * 10000

		if reward > 0:
			#print 'powerUp reward: ' + str(reward)
			return reward

		# Hero approaching powerUp reward:
		old_distMin = float('inf')
		new_distMin = float('inf')
		if old_state.powerUp_info != None:
			for powerUp in old_state.powerUp_info:
				powerUp_x = powerUp[0]
				powerUp_y = powerUp[1]
				powerUp_tp = powerUp[2]
				if ord(powerUp_tp) >= 3 and ord(powerUp_tp) <= 5:
					if old_feature[183 + ord(powerUp_tp) - 3] > 0.5:
						continue
				x = powerUp_x - old_state.hero_info[0]
				y = powerUp_y - old_state.hero_info[1]
				dist = math.sqrt(x * x + y * y)
				if dist < 10:
					old_distMin = min(old_distMin, dist)
		if new_state.powerUp_info != None:
			for powerUp in new_state.powerUp_info:
				powerUp_x = powerUp[0]
				powerUp_y = powerUp[1]
				powerUp_tp = powerUp[2]
				if ord(powerUp_tp) >= 3 and ord(powerUp_tp) <= 5:
					if new_feature[183 + ord(powerUp_tp) - 3] > 0.5:
						continue
				x = powerUp_x - new_state.hero_info[0]
				y = powerUp_y - new_state.hero_info[1]
				dist = math.sqrt(x * x + y * y)
				if dist < 10:
					new_distMin = min(new_distMin, dist)
		if old_distMin != float('inf') and new_distMin != float('inf') and old_distMin > 1.25:
			reward = reward + (old_distMin - new_distMin) * 40
			return reward

		reward = 0

		# Hero dodging ammo/enemy reward:
		old_distSum = 0
		new_distSum = 0
		if old_state.enemy_info != None and new_state.enemy_info != None:
			for enemy in old_state.enemy_info:
				enemy_x = enemy[0]
				enemy_y = enemy[1]
				x = enemy_x - old_state.hero_info[0]
				y = enemy_y - old_state.hero_info[1]
				dist = math.sqrt(x * x + y * y)
				if dist < 4 and y >= -1:
					old_distSum = old_distSum + (4 - dist) / 4.0
			for enemy in new_state.enemy_info:
				enemy_x = enemy[0]
				enemy_y = enemy[1]
				x = enemy_x - new_state.hero_info[0]
				y = enemy_y - new_state.hero_info[1]
				dist = math.sqrt(x * x + y * y)
				if dist < 4 and y >= -1:
					new_distSum = new_distSum + (4 - dist) / 4.0
		if old_state.ammo_info != None and new_state.ammo_info != None:
			for ammo in old_state.ammo_info:
				ammo_x = ammo[0]
				ammo_y = ammo[1]
				vx = ammo[2]
				vy = ammo[2]
				x = ammo_x - old_state.hero_info[0]
				y = ammo_y - old_state.hero_info[1]
				if x == 0:
					x = 0.00000001
				tan = y / x
				if vx == 0:
					vx = 0.00000001
				tan_v = vy / vx
				region = self.calculateRegion(tan, x, y)
				direction = self.calculateRegion(tan_v, vx, vy)
				dist = math.sqrt(x * x + y * y)
				if dist < 4 and (abs(region - direction) == 4 or dist < 2):
					old_distSum = old_distSum + (4 - dist) / 4.0
			for ammo in new_state.ammo_info:
				ammo_x = ammo[0]
				ammo_y = ammo[1]
				vx = ammo[2]
				vy = ammo[2]
				x = ammo_x - new_state.hero_info[0]
				y = ammo_y - new_state.hero_info[1]
				if x == 0:
					x = 0.00000001
				tan = y / x
				if vx == 0:
					vx = 0.00000001
				tan_v = vy / vx
				region = self.calculateRegion(tan, x, y)
				direction = self.calculateRegion(tan_v, vx, vy)
				dist = math.sqrt(x * x + y * y)
				if dist < 4 and (abs(region - direction) == 4 or dist < 2):
					new_distSum = new_distSum + (4 - dist) / 4.0
		if old_distSum >= 0.2:
			reward = reward + (int(old_distSum - new_distSum >= 0) * 2 - 1) * min(40, abs(old_distSum - new_distSum) * 20)
			#print '[' + action + '] ' + 'avoid reward: ' + str(reward)
			return reward

		# Hero shooting enemy rewad:
		if action in ['a', 'd', '0', 'w', 's']:
			Y_score = 0
			X_score = 0
			if abs(old_state.hero_info[1] - new_state.hero_info[1]) < 0.1:
				Y_score = Y_score - (2.5 + new_state.hero_info[1]) * 3
				#print 'Y reward: ' + str(Y_score)
			else:
				Y_score = Y_score + (old_state.hero_info[1] - new_state.hero_info[1]) * 5
				#print 'DY reward: ' + str(Y_score)
			old_dx = float('inf')
			new_dx = float('inf')
			if old_state.enemy_info != None and new_state.enemy_info != None:
				for enemy in old_state.enemy_info:
					enemy_x = enemy[0]
					enemy_y = enemy[1]
					x = enemy_x - old_state.hero_info[0]
					y = enemy_y - old_state.hero_info[1]
					if y > 1:
						old_dx = min(old_dx, abs(x))
				for enemy in new_state.enemy_info:
					enemy_x = enemy[0]
					enemy_y = enemy[1]
					x = enemy_x - new_state.hero_info[0]
					y = enemy_y - new_state.hero_info[1]
					if y > 1:
						new_dx = min(new_dx, abs(x))

				if old_dx != float('inf') and new_dx != float('inf'):
					if new_dx < old_dx or (new_dx < 0.5 and old_dx < 0.5):
						X_score = X_score + 15
						#print 'positive attack reward: ' + str(X_score)
					elif new_state.hero_info[8] - old_state.hero_info[8] > 0:
						X_score = X_score + (new_state.hero_info[8] - old_state.hero_info[8]) * 0.5
						#print 'defeat enemy reward: ' + str(X_score)
					else:
						X_score = X_score -15
						#print 'negative attack reward: ' + str(X_score)
				else:
					if abs(abs(old_state.hero_info[0]) - abs(new_state.hero_info[0])) < 0.1:
						X_score = X_score + (5 - abs(new_state.hero_info[0])) * 3
						#print 'X reward: ' + str(X_score)
					else:
						X_score = X_score + (abs(old_state.hero_info[0]) - abs(new_state.hero_info[0])) * 5
						#print 'DX reward: ' + str(X_score)
				reward = reward + X_score + Y_score

		return reward

def dotProduct(a, b):
	if len(a) != len(b):
		return None
	return sum(i[0] * i[1] for i in zip(a, b))