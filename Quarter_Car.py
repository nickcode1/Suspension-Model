import pygame
import sys
import math

# ── Configuration ──────────────────────────────────────────────────────────────
SCREEN_W   = 900
SCREEN_H   = 500
FPS        = 60
PHYS_DT    = 0.01
ROAD_SPEED = 250.0

# Physics (Math.py)
M_CAR = 1500.0
C1    = 1500.0
K1    = 15000.0

# 4 wheel x positions (left = rear of car, right = front)
WX           = [160, 310, 540, 690]
N_WHL        = len(WX)
CAR_CENTER_X = (WX[0] + WX[-1]) // 2   # reference x for road sampling

# Layout
ROAD_BASE_Y  = 400
SCALE        = 800.0
WHEEL_R      = 28
BODY_H       = 35
BODY_LEFT    = WX[0] - 35
BODY_W       = (WX[-1] + 35) - BODY_LEFT
EQUIL_SPRING = 110        # spring visual length at equilibrium (px)

WHITE = (255, 255, 255)
BLACK = (  0,   0,   0)
GRAY  = (160, 160, 160)

pygame.init()
screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("4-Wheel Suspension (heave only)")
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
    mid   = (y_top + y_bot) // 2
    cyl_y = mid - cyl_h // 2
    pygame.draw.line(screen, BLACK, (x, y_top),       (x, cyl_y),          2)
    pygame.draw.rect(screen, GRAY,  (x - cyl_w//2, cyl_y, cyl_w, cyl_h))
    pygame.draw.rect(screen, BLACK, (x - cyl_w//2, cyl_y, cyl_w, cyl_h),   2)
    pygame.draw.line(screen, BLACK, (x, cyl_y+cyl_h), (x, y_bot),          2)


# ── State ──────────────────────────────────────────────────────────────────────
h_car_prev = 0.0
h_car_curr = 0.0
h_whl_prev = [0.0] * N_WHL
h_whl_curr = [0.0] * N_WHL

global_x = 0.0
accum    = 0.0

# ── Main loop ──────────────────────────────────────────────────────────────────
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
        h_whl_new  = [road_profile(global_x - CAR_CENTER_X + wx) for wx in WX]

        # Discretised EOM: M*ẍ + 4K*x = Σ(K*h_whl_i + C*ḣ_whl_i)
        sum_damp   = sum(h_whl_new[i] - h_whl_curr[i] for i in range(N_WHL))
        sum_spring = sum(h_whl_new[i]                  for i in range(N_WHL))

        h_car_new = (
            (2*M_CAR + N_WHL*C1*PHYS_DT) * h_car_curr
            - M_CAR * h_car_prev
            + C1 * sum_damp   * PHYS_DT
            + K1 * sum_spring * PHYS_DT**2
        ) / (M_CAR + N_WHL*C1*PHYS_DT + N_WHL*K1*PHYS_DT**2)

        h_car_prev = h_car_curr
        h_car_curr = h_car_new
        h_whl_prev = h_whl_curr
        h_whl_curr = h_whl_new
        accum -= PHYS_DT

    # Road polyline
    road_pts = [
        (sx, int(ROAD_BASE_Y - road_profile(global_x - CAR_CENTER_X + sx) * SCALE))
        for sx in range(0, SCREEN_W + 4, 4)
    ]

    # Car body pixel position (derived from h_car)
    body_equil_y = ROAD_BASE_Y - 2*WHEEL_R - EQUIL_SPRING - BODY_H
    body_y       = body_equil_y - int(h_car_curr * SCALE)

    # ── Render ──
    screen.fill(WHITE)

    # Road
    poly = [(0, SCREEN_H), *road_pts, (SCREEN_W, SCREEN_H)]
    pygame.draw.polygon(screen, GRAY, poly)
    pygame.draw.lines(screen, BLACK, False, road_pts, 2)

    # Per-wheel suspension (drawn before masses so masses sit on top)
    spr_top = body_y + BODY_H   # same for all wheels — bottom of car body
    for wx, hw in zip(WX, h_whl_curr):
        road_y_i  = ROAD_BASE_Y - int(hw * SCALE)
        wheel_y_i = road_y_i  - WHEEL_R
        spr_bot_i = wheel_y_i - WHEEL_R   # top of wheel circle

        if spr_bot_i > spr_top + 4:
            pygame.draw.line(screen, BLACK, (wx-22, spr_top),   (wx+22, spr_top),   2)
            pygame.draw.line(screen, BLACK, (wx-22, spr_bot_i), (wx+22, spr_bot_i), 2)
            draw_spring(spr_top, spr_bot_i, wx - 14)
            draw_damper(spr_top, spr_bot_i, wx + 14)

        # Wheel (filled white so spring doesn't show through)
        pygame.draw.circle(screen, WHITE, (wx, wheel_y_i), WHEEL_R)
        pygame.draw.circle(screen, BLACK, (wx, wheel_y_i), WHEEL_R, 2)

    # Car body (filled white so spring tops don't show through)
    pygame.draw.rect(screen, WHITE, (BODY_LEFT, body_y, BODY_W, BODY_H))
    pygame.draw.rect(screen, BLACK, (BODY_LEFT, body_y, BODY_W, BODY_H), 2)

    # HUD
    lines = [
        f"body  : {h_car_curr*100:+.1f} cm",
        f"W1..4 : " + "  ".join(f"{h*100:+.1f}" for h in h_whl_curr),
    ]
    for i, txt in enumerate(lines):
        screen.blit(font.render(txt, True, BLACK), (10, 10 + i * 18))

    pygame.display.flip()

pygame.quit()
sys.exit()
