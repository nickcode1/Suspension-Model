import math
import pygame
import matplotlib.pyplot as plt

def _rand(cell, salt=0):
    """Deterministic pseudo-random value in [0, 1) for a stretch of road."""
    v = math.sin(cell * 12.9898 + salt * 78.233) * 43758.5453
    return v - math.floor(v)


def road(x):
    """Dirt road height (m) at position x (m). Replaces the random h_Wheel."""
    # Gently rolling base surface, a few cm of undulation
    h = (0.06 * math.sin(0.4 * x)
     + 0.03 * math.sin(1.3 * x + 2.0)
     + 0.015 * math.sin(3.1 * x + 0.7))
    
    # Small rocks (bumps) and potholes (dips) at deterministic spots
    cell = math.floor(x / FEATURE_SPACING)
    for c in (cell - 1, cell, cell + 1):
        if _rand(c) < 0.35:
            continue  # smooth stretch, no feature here
        center = (c + 0.15 + 0.7 * _rand(c, 1)) * FEATURE_SPACING
        if _rand(c, 2) < 0.55:  # rock
            amp = 0.03 + 0.05 * _rand(c, 3)
            half_width = 0.15 + 0.15 * _rand(c, 4)
        else:  # pothole
            amp = -(0.06 + 0.09 * _rand(c, 3))
            half_width = 0.35 + 0.35 * _rand(c, 4)
        d = x - center
        if abs(d) < half_width:
            h += amp * 0.5 * (1 + math.cos(math.pi * d / half_width))
    return h


h_Car = [0,0]  # Car height history
h_Wheel = [0,0]  # Wheel height history
g = 9.81  # Gravity
dt = .01  # Time step
t = 0  # Initial time
M_car = 1500/4  # kg
C1 = 2000  # N/m
K1 = 15000  # N.s/m

V = 14 # m/s, how fast the car drives along the road
X = 0 # Initial position of the car along the road
FEATURE_SPACING = 4.0  # m, one possible rock/pothole per stretch of road


# Simulation loop
while t<=10:

   
    h_Wheel.append(road(X))

    h_Car.append(((2*M_car + C1*dt)*h_Car[-1] - M_car*h_Car[-2] + C1*(h_Wheel[-1]-h_Wheel[-2])*dt + K1*h_Wheel[-1]*dt**2)/(M_car+C1*dt+K1*dt**2))
   
    t+=dt
    X+=V*dt

plt.plot(range(0, 1003), h_Wheel, label='Wheel Height')
plt.plot(range(0, 1003), h_Car, label='Car Height')
plt.legend()                                
plt.show()





