import socket
import sys
from array import array
import struct
import random
import pyQlearning
import math

address = ('127.0.0.1', 8223)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
s.connect(address)  
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
s.send('') 

ammo_x_array = array('f')
ammo_y_array = array('f')
ammo_vx_array = array('f')
ammo_vy_array = array('f')
ammo_type_array = array('c')
enemy_x_array = array('f')
enemy_y_array = array('f')
enemy_type_array = array('c')
powerUp_x_array = array('f')
powerUp_y_array = array('f')
powerUp_type_array = array('c')

action = None
action_space = ['w', 'a', 's', 'd', '0']
old_state = None
new_state = None
scores = []
ql = pyQlearning.Qlearning()
ql.loadWeight('weight_simple.txt')


iter_n = 0
while 1: 
	# start gaming!
	
	info_cat = struct.unpack("<c", s.recv(1))
	if info_cat[0] is 'o':
		score = struct.unpack("<f", s.recv(4))[0]
		ql.learnEnd(new_state, action)
		print "Iter[" + str(ql.iter_num) + "] game over with score: " + str(score)
		old_state = None
		new_state = None
		'''
		scores.append(score)
		sum1=0.0
		sum2=0.0
		N = len(scores)
		for i in range(N):
		    sum1+=scores[i]
		    sum2+=scores[i]**2
		mean=sum1/N
		var=sum2/N-mean**2
		print str(len(scores)) + ' ' + str(mean) + ' ' + str(math.sqrt(var)) + ' ' + str(min(scores)) + ' ' + str(max(scores))
		'''
	else:
		ammo_info = None
		enemy_info = None
		powerUp_info = None
		hero_info = None
		ammo_x_array = array('f')
		ammo_y_array = array('f')
		ammo_vx_array = array('f')
		ammo_vy_array = array('f')
		ammo_type_array = array('c')
		enemy_x_array = array('f')
		enemy_y_array = array('f')
		enemy_type_array = array('c')
		powerUp_x_array = array('f')
		powerUp_y_array = array('f')
		powerUp_type_array = array('c')

		# Receive the game/state information
		if info_cat[0] is 'a':
			length = struct.unpack("<i", s.recv(4))[0]
			if length > 0:
				tmp = s.recv(length * 4)
				ammo_x_array.fromstring(tmp)
				ammo_y_array.fromstring(s.recv(length * 4))
				ammo_vx_array.fromstring(s.recv(length * 4))
				ammo_vy_array.fromstring(s.recv(length * 4))
				ammo_type_array.fromstring(s.recv(length))
				ammo_info = zip(ammo_x_array, ammo_y_array, ammo_vx_array, ammo_vy_array, ammo_type_array)
		info_cat = struct.unpack("<c", s.recv(1))
		if info_cat[0] is 'e':
			length = struct.unpack("<i", s.recv(4))[0]
			if length > 0:
				enemy_x_array.fromstring(s.recv(length * 4))
				enemy_y_array.fromstring(s.recv(length * 4))
				enemy_type_array.fromstring(s.recv(length))
				enemy_info = zip(enemy_x_array, enemy_y_array, enemy_type_array)
		info_cat = struct.unpack("<c", s.recv(1))
		if info_cat[0] is 'p':
			length = struct.unpack("<i", s.recv(4))[0]
			if length > 0:
				powerUp_x_array.fromstring(s.recv(length * 4))
				powerUp_y_array.fromstring(s.recv(length * 4))
				powerUp_type_array.fromstring(s.recv(length))
				powerUp_info = zip(powerUp_x_array, powerUp_y_array, powerUp_type_array)
		info_cat = struct.unpack("<c", s.recv(1))
		if info_cat[0] is 'h':
			hero_x, hero_y, hero_taken_dmg, hero_lives, hero_gun1, hero_gun2, hero_gun3, hero_shield, hero_score = struct.unpack("<9f", s.recv(36))
			hero_info = [hero_x, hero_y, hero_taken_dmg, hero_lives, hero_gun1, hero_gun2, hero_gun3, hero_shield, hero_score]

		# Create state class
		if iter_n % 5 == 0:
			if new_state == None:
				new_state = pyQlearning.State(ammo_info, enemy_info, powerUp_info, hero_info)
				action = ql.optAction(new_state)
			else:
				old_state = new_state
				new_state = pyQlearning.State(ammo_info, enemy_info, powerUp_info, hero_info)
				action = ql.learn(old_state, action, new_state)
			#action = ql.optAction(new_state)
		iter_n = iter_n + 1

		# Send the chosen action
		info_cat = struct.unpack("<c", s.recv(1))
		if info_cat[0] is 'n':
			s.send(action)

s.close()  

'''
from array import array
from bitstring import BitStream

output_file  = open ("c.bin", "wb")
float_array = array('i', [1, 1, 2, 3, 4])
float_array.tofile(output_file)
output_file.close()

input_file = open('c2.bin', 'rb')
float_array = array('i')
float_array.fromstring(input_file.read())

print float_array
'''
