import pygame
import sys
import math

# --- CONFIGURATION & CONSTANTS ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 650
FPS = 120

# Color Palette
SKY_TOP    = (30,  50,  90)
SKY_BOT    = (80, 120, 180)
ASPHALT    = (45,  45,  50)
ROAD_LINE  = (220, 200, 60)
ROAD_EDGE  = (180, 180, 180)
BODY_COL   = (41, 128, 185)
BODY_DARK  = (21,  82, 130)
GLASS_COL  = (130, 190, 230)
WHEEL_RIM  = (200, 200, 210)
WHEEL_TIRE = (35,  35,  40)
SPRING_COL = (220, 180,  50)
DAMPER_COL = (160, 160, 175)
HUD_BG     = (10,  15,  25, 180)
HUD_TEXT   = (220, 235, 255)
HUD_ACCENT = (70, 180, 255)
DARK_LINE  = (20,  20,  30)

# --- PHYSICS PARAMETERS ---
M_s = 250.0
M_u = 35.0
K_s = 15000.0
C_s = 1500.0
K_t = 100000.0

EQUILIBRIUM_SU = 100.0
EQUILIBRIUM_UR = 80.0
SCALE = 300.0

# --- INITIAL STATE ---
x_s = 0.0
x_u = 0.0
v_s = 0.0
v_u = 0.0
a_s = 0.0
a_u = 0.0

road_y_base = 480.0
road_speed  = 150.0
road_history = []
global_time_x = 0.0

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Quarter-Car Suspension Simulation")
clock = pygame.time.Clock()
font_lg = pygame.font.SysFont("Consolas", 17, bold=True)
font_sm = pygame.font.SysFont("Consolas", 14)


# ── Drawing helpers ────────────────────────────────────────────────────────────

def draw_sky():
    for y in range(int(road_y_base)):
        t = y / road_y_base
        r = int(SKY_TOP[0] + t * (SKY_BOT[0] - SKY_TOP[0]))
        g = int(SKY_TOP[1] + t * (SKY_BOT[1] - SKY_TOP[1]))
        b = int(SKY_TOP[2] + t * (SKY_BOT[2] - SKY_TOP[2]))
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))


def draw_road(road_points):
    if len(road_points) < 2:
        return
    poly = [(0, SCREEN_HEIGHT), *road_points, (SCREEN_WIDTH, SCREEN_HEIGHT)]
    pygame.draw.polygon(screen, ASPHALT, poly)
    # Edge highlight
    pygame.draw.lines(screen, ROAD_EDGE, False, road_points, 3)


def draw_road_markings(road_history):
    """Dashed centre-line that follows the road profile."""
    dash_len = 40
    gap_len  = 30
    total    = dash_len + gap_len
    for x_pos, r_val in road_history:
        phase = int(x_pos) % total
        if phase < dash_len:
            y = road_y_base - (r_val * SCALE) + 8
            pygame.draw.line(screen, ROAD_LINE, (int(x_pos), int(y)), (int(x_pos), int(y)), 2)


def draw_spring(surface, x, y_top, y_bot, color, coils=8, width=18):
    """Draws a zigzag coil spring."""
    length = y_bot - y_top
    if length < 4:
        return
    half = width // 2
    pts = [(x, y_top)]
    segs = coils * 2
    for i in range(1, segs + 1):
        frac = i / segs
        yy = y_top + frac * length
        xx = x + (half if i % 2 == 1 else -half)
        pts.append((xx, yy))
    pts.append((x, y_bot))
    pygame.draw.lines(surface, color, False, pts, 2)


def draw_damper(surface, x, y_top, y_bot, color):
    """Draws a cylinder + rod damper."""
    rod_top  = y_top
    cyl_h    = 30
    cyl_w    = 14
    mid      = (y_top + y_bot) / 2
    cyl_top  = mid - cyl_h / 2
    cyl_bot  = mid + cyl_h / 2

    # Rod (top half)
    pygame.draw.line(surface, color, (x, rod_top), (x, int(cyl_top)), 3)
    # Cylinder body
    cyl_rect = pygame.Rect(x - cyl_w // 2, int(cyl_top), cyl_w, cyl_h)
    pygame.draw.rect(surface, color, cyl_rect, border_radius=4)
    pygame.draw.rect(surface, DARK_LINE, cyl_rect, 1, border_radius=4)
    # Rod (bottom half)
    pygame.draw.line(surface, color, (x, int(cyl_bot)), (x, int(y_bot)), 3)


def draw_wheel(surface, cx, cy, radius=34):
    """Draws a tyre + rim + spokes."""
    # Tyre
    pygame.draw.circle(surface, WHEEL_TIRE, (cx, cy), radius)
    # Rim
    rim_r = int(radius * 0.65)
    pygame.draw.circle(surface, WHEEL_RIM, (cx, cy), rim_r)
    # Spokes
    for angle_deg in range(0, 360, 60):
        angle = math.radians(angle_deg)
        sx = cx + int(rim_r * 0.9 * math.cos(angle))
        sy = cy + int(rim_r * 0.9 * math.sin(angle))
        pygame.draw.line(surface, DARK_LINE, (cx, cy), (sx, sy), 2)
    # Hub
    pygame.draw.circle(surface, DARK_LINE, (cx, cy), 6)
    # Tyre outline
    pygame.draw.circle(surface, DARK_LINE, (cx, cy), radius, 2)


def draw_car_body(surface, cx, by):
    """Draws a stylised car body silhouette."""
    # --- Main chassis rectangle ---
    chassis_w, chassis_h = 140, 44
    chassis_x = cx - chassis_w // 2
    chassis_rect = pygame.Rect(chassis_x, by, chassis_w, chassis_h)
    pygame.draw.rect(surface, BODY_COL, chassis_rect, border_radius=6)

    # --- Cabin / greenhouse on top ---
    cabin_pts = [
        (cx - 50, by),
        (cx - 35, by - 30),
        (cx + 35, by - 30),
        (cx + 50, by),
    ]
    pygame.draw.polygon(surface, BODY_COL, cabin_pts)

    # Windshield glass
    glass_pts = [
        (cx - 28, by - 2),
        (cx - 18, by - 26),
        (cx + 18, by - 26),
        (cx + 28, by - 2),
    ]
    pygame.draw.polygon(surface, GLASS_COL, glass_pts)
    pygame.draw.polygon(surface, DARK_LINE, glass_pts, 1)

    # --- Dark underside stripe ---
    stripe_rect = pygame.Rect(chassis_x + 4, by + chassis_h - 10, chassis_w - 8, 8)
    pygame.draw.rect(surface, BODY_DARK, stripe_rect, border_radius=3)

    # --- Outline ---
    pygame.draw.rect(surface, DARK_LINE, chassis_rect, 2, border_radius=6)
    pygame.draw.polygon(surface, DARK_LINE, cabin_pts, 2)


def draw_hud(surface, x_s, x_u, x_r, a_s, v_s):
    """Semi-transparent HUD panel in the top-right corner."""
    panel_w, panel_h = 310, 200
    panel_x = SCREEN_WIDTH - panel_w - 16
    panel_y = 16

    # Background
    hud_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    hud_surf.fill(HUD_BG)
    pygame.draw.rect(hud_surf, (*HUD_ACCENT, 200), hud_surf.get_rect(), 1, border_radius=6)
    surface.blit(hud_surf, (panel_x, panel_y))

    title = font_lg.render("SUSPENSION  TELEMETRY", True, HUD_ACCENT)
    surface.blit(title, (panel_x + 10, panel_y + 8))

    rows = [
        ("Sprung  disp  xs", f"{x_s:+.4f} m",  abs(x_s)  / 0.15),
        ("Unsprung disp xu", f"{x_u:+.4f} m",  abs(x_u)  / 0.15),
        ("Road input    xr", f"{x_r:+.4f} m",  abs(x_r)  / 0.10),
        ("Body accel    as", f"{a_s:+.2f} m/s²", min(abs(a_s) / 20.0, 1.0)),
        ("Body velocity vs", f"{v_s:+.3f} m/s",  min(abs(v_s) / 2.0, 1.0)),
    ]

    bar_w = 100
    for i, (label, value, ratio) in enumerate(rows):
        y = panel_y + 38 + i * 30
        # Label
        lbl_surf = font_sm.render(label, True, HUD_TEXT)
        surface.blit(lbl_surf, (panel_x + 10, y + 4))
        # Value
        val_surf = font_sm.render(value, True, HUD_ACCENT)
        surface.blit(val_surf, (panel_x + panel_w - 95, y + 4))
        # Minibar
        bar_x = panel_x + 160
        bar_rect = pygame.Rect(bar_x, y + 8, bar_w, 10)
        pygame.draw.rect(surface, (50, 60, 80), bar_rect, border_radius=3)
        fill_w = int(ratio * bar_w)
        if fill_w > 0:
            color = (
                int(50 + 200 * min(ratio * 2, 1)),
                int(180 - 130 * min(ratio * 2, 1)),
                80
            )
            pygame.draw.rect(surface, color,
                             pygame.Rect(bar_x, y + 8, fill_w, 10), border_radius=3)

    # Controls hint at bottom of HUD
    hint = font_sm.render("[SPACE] manual kick", True, (140, 150, 170))
    surface.blit(hint, (panel_x + 10, panel_y + panel_h - 22))


def get_road_height(global_x):
    if 400 <= global_x <= 550:
        return -0.08 * math.sin(math.pi * (global_x - 400) / 150)
    elif 800 <= global_x <= 1400:
        return -0.02 * math.sin(2 * math.pi * (global_x - 800) / 100)
    return 0.0


# ── Main Loop ─────────────────────────────────────────────────────────────────
running = True

while running:
    dt = clock.tick(FPS) / 1000.0
    if dt > 0.1:
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                v_s = -1.5

    # Physics
    global_time_x += road_speed * dt
    x_r = get_road_height(global_time_x + 300)

    F_suspension = -K_s * (x_s - x_u) - C_s * (v_s - v_u)
    F_tire       = -K_t * (x_u - x_r)

    a_s = F_suspension / M_s
    a_u = (-F_suspension + F_tire) / M_u

    v_s += a_s * dt
    v_u += a_u * dt
    x_s += v_s * dt
    x_u += v_u * dt

    # Road history
    road_history.append((SCREEN_WIDTH, x_r))
    updated_history = []
    road_points = []
    for x_pos, r_val in road_history:
        new_x = x_pos - (road_speed * dt)
        if new_x > -60:
            updated_history.append((new_x, r_val))
            road_points.append((int(new_x), int(road_y_base - r_val * SCALE)))
    road_history = updated_history

    # --- Render ---
    draw_sky()
    draw_road(road_points)
    draw_road_markings(road_history)

    # Component positions
    wheel_x = 300
    road_y_current = road_y_base - (x_r * SCALE)
    wheel_y  = road_y_base - EQUILIBRIUM_UR - (x_u * SCALE)
    body_y   = wheel_y - EQUILIBRIUM_SU - (x_s * SCALE)

    # Suspension spring (left) and damper (right)
    spring_x = wheel_x - 22
    damper_x = wheel_x + 22
    spring_top = int(body_y + 10)      # well inside the chassis
    spring_bot = int(wheel_y)          # wheel hub centre

    if spring_bot > spring_top + 4:
        draw_spring(screen, spring_x, spring_top, spring_bot, SPRING_COL, coils=7)
        draw_damper(screen, damper_x, spring_top, spring_bot, DAMPER_COL)

    # Wheel
    draw_wheel(screen, wheel_x, int(wheel_y))

    # Car body
    draw_car_body(screen, wheel_x, int(body_y))

    # HUD
    draw_hud(screen, x_s, x_u, x_r, a_s, v_s)

    pygame.display.flip()

pygame.quit()
sys.exit()
