import socket
import sys
from array import array
import struct
import random

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

while 1: 
	# start gaming!
	del ammo_x_array[:]
	del ammo_y_array[:]
	del ammo_vx_array[:]
	del ammo_vy_array[:]
	del ammo_type_array[:]
	del enemy_x_array[:]
	del enemy_y_array[:]
	del enemy_type_array[:]


	action_space = ['w', 'a', 's', 'd', '0']
	info_cat = struct.unpack("<c", s.recv(1))
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
	elif info_cat[0] is 'e':
		length = struct.unpack("<i", s.recv(4))[0]
		if length > 0:
			enemy_x_array.fromstring(s.recv(length * 4))
			enemy_y_array.fromstring(s.recv(length * 4))
			enemy_type_array.fromstring(s.recv(length))
			enemy_info = zip(enemy_x_array, enemy_y_array, enemy_type_array)
	elif info_cat[0] is 'h':
		hero_x, hero_y, hero_taken_dmg, hero_shield, hero_score = struct.unpack("<5f", s.recv(20))
		hero_info = [hero_x, hero_y, hero_taken_dmg, hero_shield, hero_score]
	elif info_cat[0] is 'o':
		score = struct.unpack("<f", s.recv(4))[0]
		print "game over with score: " + str(score)
		break
	elif info_cat[0] is 'n':
		s.send(random.choice(action_space))

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