import math
import pygame
import matplotlib.pyplot as plt
import random

h_Car = [0,0]  # Car height history
h_Wheel = [0,0]  # Wheel height history
g = 9.81  # Gravity
dt = .01  # Time step
t = 0  # Initial time
M_car = 1500/4  # kg
C1 = 2000  # N/m
K1 = 15000  # N.s/m

# Simulation loop
while t<=10:

   
    h_Wheel.append(random.uniform(-.05,.05))

    h_Car.append(((2*M_car + C1*dt)*h_Car[-1] - M_car*h_Car[-2] + C1*(h_Wheel[-1]-h_Wheel[-2])*dt + K1*h_Wheel[-1]*dt**2)/(M_car+C1*dt+K1*dt**2))
   
    t+=dt

plt.plot(range(0, 1003), h_Wheel, label='Wheel Height')
plt.plot(range(0, 1003), h_Car, label='Car Height')
plt.legend()                                
plt.show()





