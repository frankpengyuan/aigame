import socket
import sys
from array import array
import struct
import random
import math
import numpy as np
import sys
import math
caffe_root = '../../'  # this file should be run from {caffe_root}/examples (otherwise change this line)
sys.path.insert(0, caffe_root + 'python')
import caffe
'''
class Qtest(object):
	def __init__(self, net_path, weights_path):
		self.trained_net = caffe.Net(net_path, weights_path, caffe.TEST)

	def getQ(self,)

	def optAction(self, Feature_map):
		Qs = self.getQ(Feature_map)
		return self.actions[np.argmax(Qs)]
'''
class Featuremap(object):
	def __init__(self, image_height, image_width, feature_height, feature_width):
		self.image_height = image_height
		self.image_width = image_width
		self.height = feature_height
		self.width = feature_width
		self.score = 0
		self.iter = 0
		self.info = []
		#ammo,enemy,hero
		self.feature_dic = {}
		self.feature_dic['ammo'] = np.zeros((5, self.width, self.height))
		self.feature_dic['enemy'] = np.zeros((5, self.width, self.height))
		self.feature_dic['hero'] = np.zeros((5, self.width, self.height))
		self.feature_dic['power'] = np.zeros((5, self.width, self.height))

	def update_feature(self, ammo_info, enemy_info, powerUp_info, hero_info):
		if(self.iter > 4):
			self.iter = 0
			#ammo,enemy,hero
			self.feature_dic = {}
			self.feature_dic['ammo'] = np.zeros((5,self.width,self.height))
			self.feature_dic['enemy'] = np.zeros((5,self.width,self.height))
			self.feature_dic['hero'] = np.zeros((5,self.width,self.height))
			self.feature_dic['power'] = np.zeros((5, self.width, self.height))		
		if ammo_info != None:
			for ammo in ammo_info:
				ammo_x = int(math.floor((ammo[0]+self.image_width/2)* (self.width) / (self.image_width)))
				ammo_y = int(math.floor((ammo[1]+self.image_height/2) * (self.height) / (self.image_height)))
				if ammo_x < 0 or ammo_y < 0 or ammo_x > self.width - 1 or ammo_y > self.height - 1:
					continue
				#no speed information
				self.feature_dic['ammo'][self.iter][ammo_x][ammo_y] += 1
		if enemy_info != None:
			for enemy in enemy_info:
				enemy_x = int(math.floor((enemy[0]+self.image_width/2)* (self.width) / (self.image_width)))
				enemy_y = int(math.floor((enemy[1]+self.image_height/2) * (self.height) / (self.image_height)))
				if enemy_x < 0 or enemy_y < 0 or enemy_x > self.width - 1 or enemy_y > self.height - 1:
					continue
				self.feature_dic['enemy'][self.iter][enemy_x][enemy_y] = 1
		if powerUp_info != None:
			for power in powerUp_info:
				#if not ord(power[2]) in [3,4,5]:
				#	continue
				power_x = int(math.floor((power[0]+self.image_width/2)* (self.width) / (self.image_width)))
				power_y = int(math.floor((power[1]+self.image_height/2)* (self.height) / (self.image_height)))
				if power_x < 0 or power_y < 0 or power_y < self.width - 1 or power_y > self.height - 1:
					continue
				self.feature_dic['power'][self.iter][power_x][power_y] += 10
		hero_x = int(math.floor((hero_info[0]+self.image_width/2)* (self.width) / (self.image_width)))
		hero_y = int(math.floor((hero_info[1]+self.image_height/2) * (self.height) / (self.image_height)))
		if hero_x < 0:
			hero_x = 0
		if hero_y < 0:
			hero_y = 0
		if hero_x > self.width - 1:
			hero_x = self.width - 1
		if hero_y > self.height - 1:
			hero_y = self.height - 1
		self.feature_dic['hero'][self.iter][hero_x][hero_y] = 10
		if(self.iter == 4):
			self.hero_info = hero_info[:]
			self.ammo_info = ammo_info
			self.enemy_info = enemy_info
			self.powerUp_info = powerUp_info
		self.iter = self.iter + 1

class trainData(object):
	def __init__(self, N, frac):
		self.N_none0 = int(N * frac)
		self.N_0 = N - int(N * frac)
		#the fraction of (# of data that reward != 0) / N
		self.frac = frac		
		self.ready = False
		self.num_none0 = 0
		self.num_0 = 0
		self.none0_set = []
		self.zero_set = []

	def input(self, new_data, is_0):
		if is_0:
			if self.num_0 < self.N_0:
				self.zero_set.append(new_data)
				self.num_0 += 1
			else:
				self.zero_set.pop(0)
				self.zero_set.append(new_data)
		else:
			if self.num_none0 < self.N_none0:
				self.none0_set.append(new_data)
				self.num_none0 +=1
			else:
				self.none0_set.pop(0)
				self.none0_set.append(new_data)
		if not self.ready:
			if(self.num_0 == self.N_0 and self.num_none0 == self.N_none0):
				self.ready = True
			

	def get_minibatch(self, batch_size):
		x = random.sample(self.zero_set, batch_size - int(batch_size * self.frac))
		x.extend(random.sample(self.none0_set, int(batch_size * self.frac)))
		return x
	
class DQlearning(object):
	def __init__(self, tp = 'simple'):
		# caffe settings
		caffe.set_device(0)
		caffe.set_mode_gpu()
		# load the solver and create train and test nets
		self.solver = None  # ignore this workaround for lmdb data (can't instantiate two solvers on the same data)
		self.solver = caffe.SGDSolver('aitrain.solver')
		self.solver.net.copy_from('new_iter_100000.caffemodel')
		self.iter_num = 0
		self.actions = ['w', 'a', 's', 'd', '0']
		self.data_set = trainData(500, 0.5);

	def getQ(self, Feature_map):
		features = np.vstack((Feature_map.feature_dic['ammo'], Feature_map.feature_dic['enemy'], Feature_map.feature_dic['power'], Feature_map.feature_dic['hero']))
		#make it to four dims[1, 20, width, height]
		self.solver.net.blobs['features'].data[...] = np.array([features])
		self.solver.net.blobs['filter'].data[...] = np.ones((1,5))
		self.solver.net.blobs['label'].data[...] = np.zeros((1,5))
		self.solver.net.forward()
		filtered_q = self.solver.net.blobs['filtered_q_values'].data[...]
		return filtered_q[0]		

	def train_net(self):
		batch_size = 64
		raw_batch = self.data_set.get_minibatch(batch_size)
		for i in range(batch_size):		
			features = np.vstack((raw_batch[i][0].feature_dic['ammo'], raw_batch[i][0].feature_dic['enemy'], raw_batch[i][0].feature_dic['power'], raw_batch[i][0].feature_dic['hero']))
			self.solver.net.blobs['features'].data[i] = np.array([features])
			self.solver.net.blobs['filter'].data[i] = np.zeros((1,5))
			self.solver.net.blobs['label'].data[i] = np.zeros((1,5))
			self.solver.net.blobs['filter'].data[i][raw_batch[i][1]] = 1
			self.solver.net.blobs['label'].data[i][raw_batch[i][1]] = raw_batch[i][2]
		self.solver.step(1)
	
	def ammo_enemy_around(self, feature):
		x_start = max(0, int(math.floor((feature.hero_info[0]+feature.image_width/2)* (feature.width) / (feature.image_width)))-5)
		x_end = min(feature.width - 1, int(math.floor((feature.hero_info[0]+feature.image_width/2)* (feature.width) / (feature.image_width)))+5)
		y_start = max(0, int(math.floor((feature.hero_info[1]+feature.image_height/2)* (feature.height) / (feature.image_height)))-5)
		y_end = min(feature.height - 1, int(math.floor((feature.hero_info[1]+feature.image_height/2)* (feature.height) / (feature.image_height)))+5)
		sum_ = 0
		for i in range(x_start, x_end + 1):
			for j in range(y_start, y_end + 1):
				if feature.feature_dic['ammo'][4][i][j] == 1:
					sum_ = sum_ + 1
				if feature.feature_dic['enemy'][4][i][j] == 1:
					sum_ = sum_ + 1
		return sum_
	
	def getreward(self, old_feature, action, new_feature):
		#score_increase = new_feature.hero_info[8] - old_feature.hero_info[8]
		damage_taken = old_feature.hero_info[2] - new_feature.hero_info[2]
		doge_reward = - self.ammo_enemy_around(new_feature) + self.ammo_enemy_around(old_feature)
		power_up = new_feature.hero_info[4] + new_feature.hero_info[5] + new_feature.hero_info[6] - old_feature.hero_info[4] - old_feature.hero_info[5] - old_feature.hero_info[6]
		#approach power up:
		#power_up reward should be greater than approach power reward if we get power_up
		old_dis_power = 5
		if old_feature.powerUp_info:
			for power in old_feature.powerUp_info:
				if(power[0] < -10 or power[0] > 10 or power[1] < -7.5 or power[1] > 7.5):
					continue
				#if not ord(power[2]) in [3,4,5]:
				#	continue
				dis = abs(power[0] - old_feature.hero_info[0]) + abs(power[1] - old_feature.hero_info[1])
				if dis < old_dis_power:
					old_dis_power = dis
		new_dis_power = 5
		if new_feature.powerUp_info: 		
			for power in new_feature.powerUp_info:
				if(power[0] < -10 or power[0] > 10 or power[1] < -7.5 or power[1] > 7.5):
					continue
				#if not ord(power[2]) in [3,4,5]:
				#	continue
				dis = abs(power[0] - new_feature.hero_info[0]) + abs(power[1] - new_feature.hero_info[1])
				if dis < new_dis_power:
					new_dis_power = dis
		#shoot enemy reward
		shoot_old = 0
		if(old_feature.enemy_info != None):
			for enemy in old_feature.enemy_info:
				if(old_feature.hero_info[1] < enemy[1] and abs(old_feature.hero_info[0] - enemy[0]) < 1):
					shoot_old = 0.5
		shoot_new = 0
		if(new_feature.enemy_info != None):
			for enemy in new_feature.enemy_info:
				if(new_feature.hero_info[1] < enemy[1] and abs(new_feature.hero_info[0] - enemy[0]) < 1):
					shoot_new = 1.5
		shoot_reward = shoot_new - shoot_old
		#position reward
		px = abs(old_feature.hero_info[0]) - abs(new_feature.hero_info[0])
		py = abs(old_feature.hero_info[1]) - abs(new_feature.hero_info[1])
		p_reward = px + py
		x = old_feature.hero_info[0]
		y = old_feature.hero_info[1]
		action_reward = 0
		if(x == 10 and action == 3):
			action_reward = -10
		if(x == -10 and action == 1):
			action_reward = -10
		if(y == -7.5 and action == 2):
			action_reward = -10
		if(y == 7.5 and action == 0):
			action_reward = -10
		apporach_power = old_dis_power - new_dis_power
		reward = 1000 * power_up + 5 * apporach_power + damage_taken + 0.5 * doge_reward + 2 * shoot_reward
		if reward >= 1:
			reward = 1
		elif reward <= -1:
			reward = -1
		else:
			reward = 0
		return reward
		#doge_enemy_ammo = 
		


	def learn(self):
		if(self.data_set.ready):
			self.train_net()

	def learnEnd(self, old_feature, action):
		#reward = old_feature.hero_info[2] * 0.1
		#self.train_net(old_feature,action, reward)
		print "end"

	def optAction(self, Feature_map):
		Qs = self.getQ(Feature_map)
		# Return chosen action
		epsilon = self.epsilon()
		self.iter_num = self.iter_num + 1
		print self.actions[np.argmax(Qs)], max(Qs)
		if random.random() <= epsilon:
			return (random.choice(self.actions), max(Qs))
		else:
			return (self.actions[np.argmax(Qs)], max(Qs))

	def epsilon(self):
		if self.iter_num % 200000 < 100000:
			return 1.0
		elif self.iter_num % 200000 < 110000:
			return 0.9
		elif self.iter_num % 200000 < 120000:
			return 0.8
		elif self.iter_num % 200000 < 150000:
			return 0.02
		else:
			return 0.0

