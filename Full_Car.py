import math
import matplotlib.pyplot as plt


def road(x):
    """Dirt road height (m) at position x (m). Replaces the random h_Wheel."""
    # Gently rolling base surface, a few cm of undulation
    h = (3
         + 0.06 * math.sin(0.4 * x)
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




l  = 1
L1 = 1
L2 = 1



k1 = 1
k2 = 1
k3 = 1
k4 = 1

c1 = 1
c2 = 1
c3 = 1
c4 = 1

zu1 = []
zu2 = []
zu3 = []
zu4 = []

zs = []

phiS = []
thetaS = []

dt = 0.01
t = 0

while t <= 100:

    if t  == 20:

        zu1.append(5)
        zu2.append(5)
        zu3.append(5)
        zu4.append(5)
    
    zs.append(k1*zu1[-1] + k2*zu2[-1] + k3*zu3[-1] + k4*zu4[-1]) - k1*(l*phiS[-1]-L1*phiS[-1]) - k2*(l*phiS[-1]+L2*thetaS[-1]) + k3*(l*phiS[-1]+L1*thetaS[-1]) + k4*(l*phiS[-1]-L2*thetaS[-1]) + c1*(zu1[-1]-zu1[-2])/dt + c2*(zu2[-1]-zu2[-2])/dt + c3*(zu3[-1]-zu3[-2])/dt + c4*(zu4[-1]-zu4[-2])/dt - c1*((l*phiS[-1]-L1*thetaS[-1])-(zs[-1]+l*phiS[-1]-L1*thetaS[-1]))/dt 




    