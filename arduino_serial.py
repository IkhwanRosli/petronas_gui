from time import sleep
import serial
import socket
import sys
import json
import traceback
import numpy as np
from surface_measurment_analysis import Orientation
from data_logger import dataLogger

HOST, PORT = "192.168.0.164", 8884
ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600)
#ser = b"x:100' with RSSI -54\r\n"
encoding = 'utf-8'
d_logger = dataLogger()
verbose = 0
data = 	{
		"x":
			{"distance":0.0,"rssi":0.0,"degree":0.0},
		"y":
			{"distance":0.0 ,"rssi":0.0,"degree":0.0},
		"z":
			{"distance":0.0,"rssi":0.0,"growth":0.0}
		}

coordinate = ("x","y","z")

h =  [0.87, 0.87]   # the hight of the sensor from the floor
d = [0.82, 0.80]     # the distance between the sensor and the wellhead
orient = Orientation(h, d, verbose=verbose)

socket_timeout_conter = 0

# Create a socket (SOCK_STREAM means a TCP socket)

while True:

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



	 # start with a socket at 5-second timeout
	print("Creating the socket")
	sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout( 5.0)

	# check and turn on TCP Keepalive

	x = sock.getsockopt( socket.SOL_SOCKET, socket.SO_KEEPALIVE)
	if( x == 0):
		print('Socket Keepalive off, turning on')
		x = sock.setsockopt( socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		print('setsockopt=', x)
	else:
		print('Socket Keepalive already on')

	try:
		sock.bind(('',PORT))     #bind ip and socket
		sock.listen(5)

	except socket.error:
		print('Socket connect failed! Loop up and try socket again')
		traceback.print_exc()
		sleep( 5.0)
		continue

	print('Socket connect worked!')

	while 1:
		try:
			clientsocket, address = sock.accept()
			print(f"Connection from {address} has been established.")
			while True:
				ser_decode = str(ser.readline(),encoding)

				ser_decode = ser_decode.replace("\r","")
				ser_decode = ser_decode.replace("\n","")

				ser_decode = ser_decode.split(",")
				if ser_decode[0]  == '0':
					if int(ser_decode[1]) >1500:
						continue
					else:			# x -axis
						data["x"]["distance"] = float(ser_decode[1])
						data["x"]["rssi"] = float(ser_decode[2])
						m1 = data["x"]["distance"] /(10.0*100.0 )         # measurment of the sensor on the x axis
						d_x_angle = orient.delta_x_angle(m1)
						data["x"]["degree"] = round(np.rad2deg(d_x_angle), 5)
				elif ser_decode[0]  == '1':			# y -axis
					if int(ser_decode[1]) >1500:
						continue
					else:
						data["y"]["distance"] = float(ser_decode[1])
						data["y"]["rssi"] = float(ser_decode[2])
						m2 = data["y"]["distance"] /(10.0*100.0 )             # measurment of the sensor on the y axis
						d_y_angle = orient.delta_y_angle(m2)
						data["y"]["degree"] = round(np.rad2deg(d_y_angle), 5)

				elif ser_decode[0]  == '2':			# z -axis
					if int(ser_decode[1]) >1500:
						continue
					else:
						data["z"]["distance"] = float(ser_decode[1])
						data["z"]["rssi"] = float(ser_decode[2])
						m3 = data["z"]["distance"] /(10.0*100.0 )
						d_z_dist = orient.delta_z_distance(m3)
						data["z"]["growth"] = round(d_z_dist*1000, 5)
				else:
					continue

				data_json = json.dumps(data)
				print(data_json)
				clientsocket.send(data_json.encode('utf-8'))   #encode msg into utf-8 and send to client through socket
				d_logger.write_csv_row(data)
				socket_timeout_conter = 0
				sleep(1)

		except socket.timeout:
			print('Socket timeout, loop and try recv() again')
			socket_timeout_conter = socket_timeout_conter + 1
			if socket_timeout_conter >= 10:
				print('Number of consecutive socket timeouts is 10 which is high, exit and try creating socket again')
				sock.close()
				socket_timeout_conter = 0
				break
			else:
				sleep( 5.0)
				continue

		except ValueError :
			print('Bad reading, loop again')
			sleep( 5.0)
			continue

		except Exception as e:
			print(e)
			traceback.print_exc()
			print('Other Socket err, exit and try creating socket again')
			sock.close()
			# break from loop
			break


	try:
		sock.close()
	except:
		pass
