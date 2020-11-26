from PyQt5 import QtCore, QtGui, uic, QtWidgets
from petronas_gui import Ui_MainWindow
from time import sleep
import serial
from serial.tools import list_ports
#import socket
#import sys
import json
import traceback
import numpy as np
from surface_measurment_analysis import Orientation
from data_logger import dataLogger
import paho.mqtt.client as mqtt
#from time import sleep
import sys, os, stat, subprocess


# Create a class for our main window

#global initialization
global shouldrun
global kraf_connect
global distance
global height
global text
global status
global ipaddress
global port
global running

text = []
status = True
kraf_connect = False
connectrun = True
shouldrun=True
running = True

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Growth and Tilt Measurement of Single Wellhead")
        #Set default value for input
        self.input_distance.setText("[0.87, 0.87]")
        self.input_height.setText("[0.82, 0.80]")
        self.input_ipaddress.setText("192.168.0.164")
        self.input_port.setText("1885")
        #Setup connection to check_kraf thread
        self.kraf_connection_status = kraf_connection_status()
        self.kraf_connection_status.kraf_connect_signal.connect(self.kraf_check)
        self.kraf_connection_status.start()
        #Setup connection to mqpub thread
        self.run_mqpub=mqpub()
        self.run_mqpub.mqpub_signal.connect(self.label_preprocess)
        self.run_mqpub.mqpub_connect_error_signal.connect(self.connect_error)

        self.button_run.clicked.connect(self.process)
        self.button_run.clicked.connect(self.run_mqpub.stop)
        

    @QtCore.pyqtSlot(bool)
    def kraf_check(self,status):
        if status:
            self.status_klaf.setStyleSheet("background-color: green;")
            self.input_distance.setEnabled(True)
            self.input_height.setEnabled(True)
            self.input_ipaddress.setEnabled(True)
            self.input_port.setEnabled(True)
            self.button_run.setEnabled(True)
        else:
            self.status_klaf.setStyleSheet("background-color: grey;")
            self.input_distance.setEnabled(False)
            self.input_height.setEnabled(False)
            self.input_ipaddress.setEnabled(False)
            self.input_port.setEnabled(False)
            self.button_run.setEnabled(False)
    
    @QtCore.pyqtSlot(str,bool)
    def label_preprocess(self,data,stop):
        global text
        global running

        text.insert(0,data)
        if len(text) > 30:
            text.pop()
        test = '\n'.join(map(str, text)) 
        self.output.setText("{}".format(test))

        if stop:
            self.run_mqpub.continuous = False
            running = True
            self.button_run.setText("Run")

    
    @QtCore.pyqtSlot(str)
    def connect_error(self,e):
        global text
        instruct = "If the error is 'Permission denied: '/dev/ttyUSB0', you can follow the step below.\n    1.Close the application.\n    2.Run 'sudo chmod a+rw /dev/ttyUSB0' in the terminal.\n    3.Restart the application."
        text.append("Error: {}\n{}\nIf you encountered other errors, please contact the admin.".format(e,instruct))
        test = '\n'.join(map(str, text)) 
        self.output.setText("{}".format(test))
        self.run_mqpub.continuous = False
        running = True

    def process(self):
        global distance
        global height
        global ipaddress
        global port
        global running
        
        if running:
            self.output.clear()
            self.run_mqpub.continuous = True
            distance = self.input_distance.text()
            height = self.input_height.text()
            ipaddress = self.input_ipaddress.text()
            port = self.input_port.text()
            self.button_run.setText("Cancel")
            self.output.setText(" ")
            running = False
            self.run_mqpub.start()
        else:
            self.run_mqpub.continuous = False
            running = True
            self.button_run.setText("Run")


class mqpub(QtCore.QThread):
    mqpub_signal = QtCore.pyqtSignal(str,bool)
    mqpub_connect_error_signal = QtCore.pyqtSignal(str)
    mqpub_test = QtCore.pyqtSignal()


    def __init__(self, continuous=False, parent=None):
        super(mqpub,self).__init__(parent)
        self._stopped = True
        self.continuous = continuous
    
    def __del__(self):
        self.wait()
        
    def stop(self):
        self._stopped = True
    
    def run(self):
        self._stopped = False
        global lora_connect
        global kraf_connect
        global shouldrun
        global ipaddress
        global port
        global text 

        text = []

        try:
            ser = serial.Serial(port='/dev/ttyUSB0',baudrate=9600)
        except Exception as e:      
            self.mqpub_connect_error_signal.emit(str(e))
            self._stopped = True

        encoding = 'utf-8'
        d_logger = dataLogger()
        verbose = 0
        data =  {
                "x":
                    {"distance":0.0,"rssi":0.0,"degree":0.0},
                "y":
                    {"distance":0.0 ,"rssi":0.0,"degree":0.0},
                "z":
                    {"distance":0.0,"rssi":0.0,"growth":0.0}
                }
        coordinate = ("x","y","z")

        #h =  [0.87, 0.87]   # the hight of the sensor from the floor
        #d = [0.82, 0.80]     # the distance between the sensor and the wellhe
        
        d, h = self.preprocess()

        orient = Orientation(h, d, verbose=verbose)

        socket_timeout_conter = 0
        try:
            client = mqtt.Client()
            client.connect(ipaddress, port=int(port), keepalive=60)
        except:
            client.loop_start()
            self._stopped = True

        lora_connect = True
        a2_laser_x = "a2/laser/x"
        a2_laser_y = "a2/laser/y"
        a2_laser_z = "a2/laser/z"
        a2_rssi_x = "a2/rssi/x"
        a2_rssi_y = "a2/rssi/y"
        a2_rssi_z = "a2/rssi/z"
        a2_degree_x = "a2/degree/x"
        a2_degree_y = "a2/degree/y"
        a2_degree_z = "a2/degree/z"

        while shouldrun :
            try:
                if self._stopped:
                    out = "[INFO] PROCESS CANCELLED !!!"
                    self.mqpub_signal.emit(out,self._stopped)
                    break

                ser_decode = str(ser.readline(),encoding)
                ser_decode = ser_decode.replace("\r","")
                ser_decode = ser_decode.replace("\n","")

                ser_decode = ser_decode.split(",")
                if ser_decode[0]  == '0':
                    if float(ser_decode[1]) >1500:
                        continue
                    else:           # x -axis
                        data["x"]["distance"] = float(ser_decode[1])
                        data["x"]["rssi"] = float(ser_decode[2])
                        m1 = data["x"]["distance"] /(10.0*100.0 )         # measurment of the sensor on the x axis
                        d_x_angle = orient.delta_x_angle(m1)
                        data["x"]["degree"] = round(np.rad2deg(d_x_angle), 5)
                elif ser_decode[0]  == '1':         # y -axis
                    if int(ser_decode[1]) >1500:
                        continue
                    else:
                        data["y"]["distance"] = float(ser_decode[1])
                        data["y"]["rssi"] = float(ser_decode[2])
                        m2 = data["y"]["distance"] /(10.0*100.0 )             # measurment of the sensor on the y axis
                        d_y_angle = orient.delta_y_angle(m2)
                        data["y"]["degree"] = round(np.rad2deg(d_y_angle), 5)

                elif ser_decode[0]  == '2':         # z -axis
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

                client.publish(a2_laser_x, payload=data["x"]["distance"], retain=True)
                client.publish(a2_laser_y, payload=data["y"]["distance"], retain=True)
                client.publish(a2_laser_z, payload=data["z"]["distance"], retain=True)
                client.publish(a2_rssi_x, payload=data["x"]["rssi"], retain=True)
                client.publish(a2_rssi_y, payload=data["y"]["rssi"], retain=True)
                client.publish(a2_rssi_z, payload=data["z"]["rssi"], retain=True)
                client.publish(a2_degree_x, payload=data["x"]["degree"], retain=True)
                client.publish(a2_degree_y, payload=data["y"]["degree"], retain=True)
                client.publish(a2_degree_z, payload=data["z"]["growth"], retain=True)
                #print(data)
                self.mqpub_signal.emit(str(data),self._stopped)
                d_logger.write_csv_row(data)
                socket_timeout_conter = 0

                if self.continuous:
                    QtCore.QThread.sleep(1)
                else:
                    break

            except Exception as e:
                client.disconnect()   

        
    def preprocess(self):
        global distance
        global height

        #Get rid the square bracket
        temp1 = distance.replace("]","")
        temp1 = temp1.replace("[","")
        temp2 = height.replace("]","")
        temp2 = temp2.replace("[","")

        #String to list
        final_dis = temp1.split(",")
        final_height = temp2.split(",")
        final_dis = list(map(float, final_dis))
        final_height = list(map(float, final_height)) 
        #print(final_dis,final_height)
        return final_dis,final_height

class kraf_connection_status(QtCore.QThread):
    kraf_connect_signal = QtCore.pyqtSignal(bool)


    def __init__(self):
        super(kraf_connection_status,self).__init__()

    def run(self):
        global kraf_connect
        while connectrun:
            ports = list_ports.comports()
            if not ports:
                self.kraf_connect_signal.emit(False)
            for i,p in enumerate(ports):
                cond = str(p)[:12]
                if cond == "/dev/ttyUSB0":
                    self.kraf_connect_signal.emit(True)
                    break
                print("{}|{}".format(i,len(ports)))
                if (i+1) == len(ports):
                    self.kraf_connect_signal.emit(False)
            sleep(10)


if __name__ == '__main__':
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    app.aboutToQuit.connect(app.deleteLater)
    app.exec_()