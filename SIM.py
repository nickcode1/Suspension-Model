import pygame
import sys
import math

# ── Configuration ──────────────────────────────────────────────────────────────
SCREEN_W   = 900
SCREEN_H   = 500
FPS        = 60
PHYS_DT    = 0.01
ROAD_SPEED = 250.0        # px / s

# Physics (Math.py)
M_CAR = 1500.0
C1    = 15000.0
K1    = 150000.0

# Layout
WHEEL_X      = 280
ROAD_BASE_Y  = 400
SCALE        = 800.0      # px per metre

WHEEL_R      = 28         # wheel circle radius (px)
BODY_W       = 120
BODY_H       = 35
EQUIL_SPRING = 110        # spring visual length at equilibrium (px)
SPR_X        = WHEEL_X - 18   # spring x
DMP_X        = WHEEL_X + 18   # damper x

WHITE = (255, 255, 255)
BLACK = (  0,   0,   0)
GRAY  = (160, 160, 160)

pygame.init()
screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("1-DOF Suspension")
clock   = pygame.time.Clock()
font    = pygame.font.SysFont("Consolas", 14)


def road_profile(gx):
    x = gx % 2600.0
    if 250 <= x < 420:
        return 0.05 * math.sin(math.pi * (x - 250) / 170)
    if 750 <= x < 1100:
        return 0.03 * math.sin(2 * math.pi * (x - 750) / 175)
    if 1400 <= x < 1440:
        return 0.08 * (x - 1400) / 40
    if 1440 <= x < 1700:
        return 0.08
    if 1700 <= x < 1740:
        return 0.08 * (1.0 - (x - 1700) / 40)
    return 0.0


def draw_spring(y_top, y_bot, x, coils=6, half=10):
    if y_bot <= y_top + 4:
        return
    pts = [(x, y_top)]
    segs = coils * 2
    for i in range(1, segs + 1):
        frac = i / segs
        pts.append((x + (half if i % 2 else -half), int(y_top + frac * (y_bot - y_top))))
    pts.append((x, y_bot))
    pygame.draw.lines(screen, BLACK, False, pts, 2)


def draw_damper(y_top, y_bot, x, cyl_h=26, cyl_w=12):
    if y_bot <= y_top + 4:
        return
    mid     = (y_top + y_bot) // 2
    cyl_y   = mid - cyl_h // 2
    # rod above cylinder
    pygame.draw.line(screen, BLACK, (x, y_top), (x, cyl_y), 2)
    # cylinder body (filled gray + black outline)
    pygame.draw.rect(screen, GRAY,  (x - cyl_w // 2, cyl_y, cyl_w, cyl_h))
    pygame.draw.rect(screen, BLACK, (x - cyl_w // 2, cyl_y, cyl_w, cyl_h), 2)
    # rod below cylinder
    pygame.draw.line(screen, BLACK, (x, cyl_y + cyl_h), (x, y_bot), 2)


# ── State ──────────────────────────────────────────────────────────────────────
h_car_prev = h_car_curr = 0.0
h_whl_prev = h_whl_curr = 0.0
global_x = 0.0
accum    = 0.0

running = True
while running:
    frame_dt = min(clock.tick(FPS) / 1000.0, 0.1)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    accum += frame_dt
    while accum >= PHYS_DT:
        global_x  += ROAD_SPEED * PHYS_DT
        h_whl_new  = road_profile(global_x)

        h_car_new = (
            (2*M_CAR + C1*PHYS_DT) * h_car_curr
            - M_CAR * h_car_prev
            + C1 * (h_whl_new - h_whl_curr) * PHYS_DT
            + K1 * h_whl_new * PHYS_DT**2
        ) / (M_CAR + C1*PHYS_DT + K1*PHYS_DT**2)

        h_car_prev, h_car_curr = h_car_curr, h_car_new
        h_whl_prev, h_whl_curr = h_whl_curr, h_whl_new
        accum -= PHYS_DT

    # ── Pixel positions ────────────────────────────────────────────────────────
    # Wheel center sits WHEEL_R above the road surface
    road_surface_y = ROAD_BASE_Y - int(h_whl_curr * SCALE)
    wheel_y        = road_surface_y - WHEEL_R

    # Spring spans from bottom of car body (spr_top) to top of wheel (spr_bot)
    # so it touches neither mass
    spr_bot        = wheel_y - WHEEL_R
    spring_len     = max(4, EQUIL_SPRING - int((h_whl_curr - h_car_curr) * SCALE))
    spr_top        = spr_bot - spring_len
    body_y         = spr_top - BODY_H   # car rectangle top

    # Road polyline
    road_pts = [
        (sx, int(ROAD_BASE_Y - road_profile(global_x - WHEEL_X + sx) * SCALE))
        for sx in range(0, SCREEN_W + 4, 4)
    ]

    # ── Render ──
    screen.fill(WHITE)

    # Road surface
    poly = [(0, SCREEN_H), *road_pts, (SCREEN_W, SCREEN_H)]
    pygame.draw.polygon(screen, GRAY, poly)
    pygame.draw.lines(screen, BLACK, False, road_pts, 2)

    # Horizontal connector plates at top and bottom of suspension
    pygame.draw.line(screen, BLACK, (WHEEL_X - 22, spr_top), (WHEEL_X + 22, spr_top), 2)
    pygame.draw.line(screen, BLACK, (WHEEL_X - 22, spr_bot), (WHEEL_X + 22, spr_bot), 2)

    # Spring (left) and damper (right) — both anchored at spr_top / spr_bot
    draw_spring(spr_top, spr_bot, SPR_X)
    draw_damper(spr_top, spr_bot, DMP_X)

    # Wheel (circle) — drawn after suspension so the bottom plate sits on top
    pygame.draw.circle(screen, WHITE, (WHEEL_X, wheel_y), WHEEL_R)
    pygame.draw.circle(screen, BLACK, (WHEEL_X, wheel_y), WHEEL_R, 2)

    # Car body (rectangle) — drawn after suspension so the top plate is visible
    pygame.draw.rect(screen, WHITE, (WHEEL_X - BODY_W // 2, body_y, BODY_W, BODY_H))
    pygame.draw.rect(screen, BLACK, (WHEEL_X - BODY_W // 2, body_y, BODY_W, BODY_H), 2)

    # HUD
    lines = [
        f"h_wheel: {h_whl_curr*100:+.1f} cm",
        f"h_car  : {h_car_curr*100:+.1f} cm",
        f"deflect: {(h_car_curr - h_whl_curr)*100:+.1f} cm",
    ]
    for i, txt in enumerate(lines):
        screen.blit(font.render(txt, True, BLACK), (SCREEN_W - 200, 10 + i * 18))

    pygame.display.flip()

pygame.quit()
sys.exit()
