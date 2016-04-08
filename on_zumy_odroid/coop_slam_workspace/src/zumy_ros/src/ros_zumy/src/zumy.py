# -*- coding: utf-8 -*-
"""
Created on Wed Oct 29 06:39:30 2014

@author: ajc
"""

from mbedrpc import *
import threading
import time
from serial import SerialException
import numpy as np #just so I can use the np.mean function.  Nothing strange going on here.



class Motor:
    def __init__(self, a1, a2):
        self.a1=a1
        self.a2=a2

    def cmd(self, speed):
        if speed >=0:
            self.a1.write(speed)
            self.a2.write(0)
        else:
            self.a1.write(0)
            self.a2.write(-speed)

imu_names = ['accel_x','accel_y','accel_z','gyro_x','gyro_y','gyro_z']
enc_names = ['r_enc','l_enc']

class Zumy:
    def __init__(self, dev='/dev/ttyACM0'):
        self.mbed=SerialRPC(dev, 115200)
        #don't do any of the motor stuff... b/c the mbed should do it itself.
        #a1=PwmOut(self.mbed, p21)
        #a2=PwmOut(self.mbed, p22)
        #b1=PwmOut(self.mbed, p23)
        #b2=PwmOut(self.mbed, p24)

        #Setting motor PWM frequency
        #pwm_freq = 50.0
        #a1.period(1/pwm_freq)
        #a2.period(1/pwm_freq)
        #b1.period(1/pwm_freq)
        #b2.period(1/pwm_freq)
        
        #self.m_right = Motor(a1, a2)
        #self.m_left = Motor(b1, b2)
        self.an = AnalogIn(self.mbed, p15)
        self.imu_vars = [RPCVariable(self.mbed,name,delete = False) for name in imu_names]
        self.enc_vars = [RPCVariable(self.mbed,name,delete = False) for name in enc_names]
        self.rlock=threading.Lock()

        self.enabled = True #note it's enableD, to avoid namespace collision with the function 'enable'

        self.volts = [8.0 for i in range(0,5)] #5 element long moving average filter, initialized to 8 volts  (it'll quickly change)

        self.battery_lock = False #a boolean to tell me if my battery ever dipped below the battery threshold.

    def cmd(self, left, right):
        self.rlock.acquire()
	      # As of Rev. F, positive command is sent to both left and right
        try:
          if self.enabled: #don't do anything if i'm disabled
            #self.m_left.cmd(left)
            #self.m_right.cmd(right)
            pass
        except SerialException:
          pass
        self.rlock.release()

    def read_voltage(self):
        self.rlock.acquire()
        try:
          ain=self.an.read()*3.3
        except SerialException:
          pass
        self.rlock.release()
        volt=ain*(100+200) / (100)
        self.volts.insert(0,volt)  #add this data to the moving average filter
        self.volts.pop() #remove the last element
        return volt

    def read_enc(self):
      self.rlock.acquire()
      try:
        rval = [int(var.read()) for var in self.enc_vars]
      except SerialException:
        pass
      self.rlock.release()
      return rval

    def read_imu(self):
      self.rlock.acquire()
      try:
        rval = [float(var.read()) for var in self.imu_vars]
      except SerialException:
        pass
      self.rlock.release()
      return rval

    def enable(self):
      #enable the zumy, but only if my battery hasn't been unhappy.
      if not self.battery_lock:
	      self.enabled = True


    def disable(self):
      #first, stop the zumy.
      self.cmd(0,0)
      #second, disable the zumy flag.
      self.enabled = False

    def battery_protection(self):
    	#a function that needs to be called with some regularity
    	#disables the robot if the battery voltage is very low
    	if np.mean(self.volts) < 6.6: #6.6 volts--> 3.3V per cell.
    		#averages over the last 5 battery measurements, because loading effects are :(

    		self.disable()
    		self.battery_lock = True
    
    def battery_unsafe(self):
    	#return true if i think my battery is unsafe.
    	return self.battery_lock

if __name__ == '__main__':
    z=Zumy()
    z.cmd(0.3,0.3)
    time.sleep(0.3)
    z.cmd(0,0) 
