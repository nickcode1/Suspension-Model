import math
import pygame

# --- Physics (same as Math.py) ---
dt = .01  # Time step
M_car = 300  # kg
C1 = 1000  # N/m
K1 = 150 # N.s/m

CAR_SPEED = 8.0  # m/s, how fast the car drives along the road


def _rand(cell, salt=0):
    """Deterministic pseudo-random value in [0, 1) for a stretch of road."""
    v = math.sin(cell * 12.9898 + salt * 78.233) * 43758.5453
    return v - math.floor(v)


FEATURE_SPACING = 4.0  # m, one possible rock/pothole per stretch of road


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


# Start at steady state so there is no startup transient
h_Wheel = [road(0), road(0)]
h_Car = [road(0), road(0)]
t = 0

# Time histories for the live plot
PLOT_WINDOW = 10.0  # seconds of history shown
t_hist = []
wheel_hist = []
car_hist = []


def step():
    """Advance the simulation by one dt using the equation from Math.py."""
    global t
    h_Wheel.append(road(CAR_SPEED * t))
    h_Car.append(((2*M_car + C1*dt)*h_Car[-1] - M_car*h_Car[-2] + C1*(h_Wheel[-1]-h_Wheel[-2])*dt + K1*h_Wheel[-1]*dt**2)/(M_car+C1*dt+K1*dt**2))
    t += dt
    # Only the last two values are needed by the recurrence
    if len(h_Car) > 4:
        del h_Car[0], h_Wheel[0]

    t_hist.append(t)
    wheel_hist.append(h_Wheel[-1])
    car_hist.append(h_Car[-1])
    while t_hist[0] < t - PLOT_WINDOW:
        del t_hist[0], wheel_hist[0], car_hist[0]


# --- Visualization ---
WIDTH, HEIGHT = 1100, 650
BASELINE = 620   # screen y of road height 0
V_SCALE = 90     # pixels per meter, vertical
H_SCALE = 60     # pixels per meter, horizontal
CAR_X = WIDTH // 2  # car stays centered, road scrolls past

WHEEL_R = 24
SPRING_LEN = 90        # visual rest length of the spring/damper
BODY_W, BODY_H = 180, 75
SUBSTEPS = 2           # sim steps per frame

PLOT_H = 230           # height of the live plot panel below the sim view

SKY = (200, 225, 245)
GROUND = (120, 90, 60)
ROAD_LINE = (50, 50, 50)
BODY_COLOR = (190, 40, 40)
WHEEL_COLOR = (30, 30, 30)
HARDWARE = (70, 70, 70)
WHEEL_TRACE = (30, 90, 200)
CAR_TRACE = (190, 40, 40)


def world_to_screen_y(h):
    return BASELINE - h * V_SCALE


def draw_road(screen):
    points = []
    for sx in range(0, WIDTH + 1, 2):
        wx = CAR_SPEED * t + (sx - CAR_X) / H_SCALE
        points.append((sx, world_to_screen_y(road(wx))))
    pygame.draw.polygon(screen, GROUND, points + [(WIDTH, HEIGHT), (0, HEIGHT)])
    pygame.draw.lines(screen, ROAD_LINE, False, points, 4)


def draw_spring(screen, x, y_top, y_bot, coils=6, half_width=11):
    points = [(x, y_top)]
    n = coils * 2
    for i in range(1, n):
        offset = half_width if i % 2 else -half_width
        points.append((x + offset, y_top + (y_bot - y_top) * i / n))
    points.append((x, y_bot))
    pygame.draw.lines(screen, HARDWARE, False, points, 3)


def draw_damper(screen, x, y_top, y_bot):
    mid = (y_top + y_bot) / 2
    pygame.draw.line(screen, HARDWARE, (x, y_top), (x, mid + 8), 3)          # piston rod
    pygame.draw.rect(screen, HARDWARE, (x - 8, mid, 16, y_bot - mid), 3)     # cylinder
    pygame.draw.line(screen, HARDWARE, (x - 8, mid + 8), (x + 8, mid + 8), 3)  # piston head


def draw_plot(screen, font):
    panel = pygame.Rect(0, HEIGHT, WIDTH, PLOT_H)
    pygame.draw.rect(screen, (250, 250, 250), panel)
    pygame.draw.line(screen, (100, 100, 100), (0, HEIGHT), (WIDTH, HEIGHT), 2)
    if len(t_hist) < 2:
        return

    left, right = 70, WIDTH - 70
    top, bot = HEIGHT + 18, HEIGHT + PLOT_H - 30
    t_end = t_hist[-1]
    t_start = t_end - PLOT_WINDOW

    def series_range(hist):
        """Each trace gets its own scale so both fill the panel and overlap."""
        lo, hi = min(hist), max(hist)
        if hi - lo < 0.02:  # keep a sensible scale when the trace is flat
            mid = (hi + lo) / 2
            lo, hi = mid - 0.01, mid + 0.01
        pad = 0.08 * (hi - lo)
        return lo - pad, hi + pad

    wheel_lo, wheel_hi = series_range(wheel_hist)
    car_lo, car_hi = series_range(car_hist)

    def px(tv):
        return left + (tv - t_start) / PLOT_WINDOW * (right - left)

    def py(h, lo, hi):
        return bot - (h - lo) / (hi - lo) * (bot - top)

    pygame.draw.rect(screen, (170, 170, 170), pygame.Rect(left, top, right - left, bot - top), 1)
    for frac in (0.0, 0.5, 1.0):  # gridlines: wheel scale on left, car scale on right
        y = bot - frac * (bot - top)
        pygame.draw.line(screen, (225, 225, 225), (left + 1, y), (right - 1, y))
        wheel_label = font.render(f"{wheel_lo + frac * (wheel_hi - wheel_lo):6.2f}", True, WHEEL_TRACE)
        screen.blit(wheel_label, (left - wheel_label.get_width() - 6, y - wheel_label.get_height() // 2))
        car_label = font.render(f"{car_lo + frac * (car_hi - car_lo):6.2f}", True, CAR_TRACE)
        screen.blit(car_label, (right + 6, y - car_label.get_height() // 2))
    for tv in (t_start, t_end):
        label = font.render(f"{tv:.1f} s", True, (90, 90, 90))
        screen.blit(label, (px(tv) - label.get_width() // 2, bot + 6))

    for hist, color, lo, hi in ((wheel_hist, WHEEL_TRACE, wheel_lo, wheel_hi),
                                (car_hist, CAR_TRACE, car_lo, car_hi)):
        points = [(px(tv), py(h, lo, hi)) for tv, h in zip(t_hist, hist)]
        pygame.draw.lines(screen, color, False, points, 2)

    legend_wheel = font.render("h_Wheel", True, WHEEL_TRACE)
    legend_car = font.render("h_Car", True, CAR_TRACE)
    screen.blit(legend_wheel, (left + 10, top + 6))
    screen.blit(legend_car, (left + 10 + legend_wheel.get_width() + 20, top + 6))


def draw_car(screen):
    wheel_cy = world_to_screen_y(h_Wheel[-1]) - WHEEL_R
    wheel_top = wheel_cy - WHEEL_R
    body_bottom = world_to_screen_y(h_Car[-1]) - 2 * WHEEL_R - SPRING_LEN

    draw_spring(screen, CAR_X - 18, body_bottom, wheel_top)
    draw_damper(screen, CAR_X + 18, body_bottom, wheel_top)

    pygame.draw.circle(screen, WHEEL_COLOR, (CAR_X, int(wheel_cy)), WHEEL_R)
    pygame.draw.circle(screen, (150, 150, 150), (CAR_X, int(wheel_cy)), WHEEL_R // 2)

    body = pygame.Rect(0, 0, BODY_W, BODY_H)
    body.midbottom = (CAR_X, int(body_bottom))
    pygame.draw.rect(screen, BODY_COLOR, body, border_radius=8)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT + PLOT_H))
    pygame.display.set_caption("Quarter Car Model")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        for _ in range(SUBSTEPS):
            step()

        screen.fill(SKY)
        draw_road(screen)
        draw_car(screen)
        draw_plot(screen, font)

        hud = font.render(
            f"t = {t:6.2f} s    h_Wheel = {h_Wheel[-1]:5.2f} m    h_Car = {h_Car[-1]:5.2f} m",
            True, (20, 20, 20))
        screen.blit(hud, (12, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
