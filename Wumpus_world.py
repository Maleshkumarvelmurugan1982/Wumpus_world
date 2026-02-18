import pygame
import random
import sys
import math
import csv
import os
from datetime import datetime

# ======================
# CONFIG
# ======================
# Grid size will be set dynamically by the user
GRID_SIZE    = 6          # Default, will be overridden
PANEL_HEIGHT = 180

# Get screen info for fullscreen
pygame.init()
screen_info = pygame.display.Info()
SCREEN_WIDTH = screen_info.current_w
SCREEN_HEIGHT = screen_info.current_h

# Calculate max grid dimension based on screen (leave room for panel)
MAX_GRID_DIM = min(SCREEN_WIDTH, SCREEN_HEIGHT - PANEL_HEIGHT - 50)

# These will be calculated based on selected grid size
CELL_SIZE = 90
WIDTH     = SCREEN_WIDTH
HEIGHT    = SCREEN_HEIGHT

# ── Dark Fantasy Palette ──
BG_DARK      = (10,  10,  18)
CELL_DARK    = (18,  20,  35)
CELL_MID     = (24,  27,  48)
GRID_LINE    = (40,  44,  72)

AGENT_COL    = (80, 160, 255)
AGENT_GLOW   = (40,  90, 200)
AGENT_INNER  = (200, 230, 255)

GOLD_COL     = (255, 210,  40)
GOLD_GLOW    = (200, 140,   0)
GOLD_INNER   = (255, 255, 180)

WUMPUS_COL   = (200,  40,  60)
WUMPUS_GLOW  = (140,  10,  25)
WUMPUS_INNER = (255, 100, 120)

PIT_COL      = (15,  15,  30)
PIT_RIM      = (60,  50, 100)
PIT_GLOW     = (80,  20, 120)

START_COL    = (30,  80,  50)
START_BORDER = (60, 160,  90)

PANEL_BG     = (12,  12,  22)
PANEL_BORDER = (50,  55, 100)
TEXT_MAIN    = (200, 210, 255)
TEXT_DIM     = (90, 100, 150)
TEXT_ACCENT  = (120, 200, 255)

WIN_COL      = (60, 220, 120)
LOSE_COL     = (220,  60,  80)
PAUSE_COL    = (255, 180,  40)
AIM_COL      = (255, 120,  30)   # Orange for aim mode

# ── Button colours (normal, hover) ──
BTN_START   = ((25, 110,  55), (45, 175,  85))
BTN_PAUSE   = ((120,  85,  15), (195, 145,  35))
BTN_RESTART = ((110,  25,  25), (185,  50,  50))
BTN_RESUME  = ((20,  80, 150), (45, 130, 215))
BTN_EXIT    = ((60,  20,  60), (120,  35, 120))

# Screen will be initialized in fullscreen after grid size is selected
screen = None
pygame.display.set_caption("⚔  Wumpus World")

try:
    big_font   = pygame.font.SysFont("georgia",  36, bold=True)
    med_font   = pygame.font.SysFont("georgia",  20)
    small_font = pygame.font.SysFont("consolas", 15)
    tiny_font  = pygame.font.SysFont("consolas", 13)
    score_font = pygame.font.SysFont("georgia",  24, bold=True)
    btn_font   = pygame.font.SysFont("georgia",  15, bold=True)
except Exception:
    big_font = med_font = small_font = tiny_font = score_font = btn_font = \
        pygame.font.SysFont(None, 22)

clock = pygame.time.Clock()
tick  = 0


# ======================
# HIGH SCORE PERSISTENCE
# ======================
HIGHSCORE_FILE = "wumpus_highscores.csv"

def load_high_score(grid_size):
    """Load the highest score for a specific grid size from CSV."""
    if not os.path.exists(HIGHSCORE_FILE):
        return 0
    
    try:
        with open(HIGHSCORE_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row['grid_size']) == grid_size:
                    return int(row['score'])
    except Exception as e:
        print(f"Error loading high score: {e}")
    
    return 0


def save_high_score(grid_size, score):
    """Save a new high score for a specific grid size to CSV."""
    scores = {}
    
    # Load existing scores
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    gs = int(row['grid_size'])
                    sc = int(row['score'])
                    dt = row['date']
                    scores[gs] = {'score': sc, 'date': dt}
        except Exception as e:
            print(f"Error reading high scores: {e}")
    
    # Update if new score is higher
    current_high = scores.get(grid_size, {}).get('score', 0)
    if score > current_high:
        scores[grid_size] = {
            'score': score,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Write back to CSV
        try:
            with open(HIGHSCORE_FILE, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['grid_size', 'score', 'date'])
                writer.writeheader()
                for gs, data in sorted(scores.items()):
                    writer.writerow({
                        'grid_size': gs,
                        'score': data['score'],
                        'date': data['date']
                    })
        except Exception as e:
            print(f"Error saving high score: {e}")


def get_all_high_scores():
    """Get all high scores as a dict {grid_size: score}."""
    scores = {}
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scores[int(row['grid_size'])] = int(row['score'])
        except Exception:
            pass
    return scores


# ======================
# HELPERS
# ======================
def draw_glow_circle(surf, color, center, radius, layers=6, alpha_step=18):
    for i in range(layers, 0, -1):
        r = radius + i * 4
        a = max(0, alpha_step - i * 2)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, a), (r, r), r)
        surf.blit(s, (center[0] - r, center[1] - r))


def draw_glow_rect(surf, color, rect, radius=8, layers=4, alpha_step=14):
    for i in range(layers, 0, -1):
        pad = i * 3
        r   = pygame.Rect(rect.x - pad, rect.y - pad,
                          rect.width + pad * 2, rect.height + pad * 2)
        a   = max(0, alpha_step - i * 2)
        s   = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, a), (0, 0, r.width, r.height),
                         border_radius=radius + pad)
        surf.blit(s, (r.x, r.y))


def draw_rrect(surf, color, rect, radius=8, border=0, bcol=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and bcol:
        pygame.draw.rect(surf, bcol, rect, border, border_radius=radius)


def pulse(base, amp, speed=2):
    return base + amp * math.sin(tick * speed * 0.05)


# ======================
# BUTTON CLASS
# ======================
class Button:
    def __init__(self, rect, label, colors, icon=""):
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.icon    = icon
        self.normal  = colors[0]
        self.hover_c = colors[1]
        self.hovered = False

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surf):
        col = self.hover_c if self.hovered else self.normal
        if self.hovered:
            draw_glow_rect(surf, col, self.rect, radius=10, layers=3, alpha_step=16)
        draw_rrect(surf, col, self.rect, radius=10)
        # Sheen on top
        sheen = pygame.Rect(self.rect.x + 3, self.rect.y + 3,
                            self.rect.width - 6, 3)
        pygame.draw.rect(surf, (*[min(c + 70, 255) for c in col], 100),
                         sheen, border_radius=3)
        # Border
        bcol = tuple(min(c + 90, 255) for c in col)
        pygame.draw.rect(surf, bcol, self.rect, 2, border_radius=10)
        # Text
        txt = btn_font.render(
            f"{self.icon}  {self.label}" if self.icon else self.label,
            True, (240, 245, 255))
        surf.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                        self.rect.centery - txt.get_height() // 2))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ======================
# ARROW PROJECTILE
# ======================
class ArrowProjectile:
    """Animates an arrow flying across cells."""
    def __init__(self, start_row, start_col, dr, dc):
        self.row    = start_row
        self.col    = start_col
        self.dr     = dr          # direction row delta
        self.dc     = dc          # direction col delta
        self.frac   = 0.0         # 0→1 progress across the current cell
        self.speed  = 0.18        # fraction per tick
        self.done   = False
        self.hit_wumpus = False

    def pixel_pos(self):
        """Return the current pixel center of the arrow."""
        base_cx, base_cy = grid_to_screen(self.row, self.col)
        px = base_cx + self.dc * self.frac * CELL_SIZE
        py = base_cy + self.dr * self.frac * CELL_SIZE
        return int(px), int(py)

    def draw(self, surf):
        cx, cy = self.pixel_pos()
        angle = math.degrees(math.atan2(self.dr, self.dc))
        # Glow
        draw_glow_circle(surf, AIM_COL, (cx, cy), 8, layers=4, alpha_step=20)
        # Arrow shaft
        cos_a = math.cos(math.radians(angle))
        sin_a = math.sin(math.radians(angle))
        x1 = int(cx - cos_a * 14)
        y1 = int(cy - sin_a * 14)
        x2 = int(cx + cos_a * 14)
        y2 = int(cy + sin_a * 14)
        pygame.draw.line(surf, AIM_COL,   (x1, y1), (x2, y2), 3)
        pygame.draw.line(surf, (255,255,200), (x1, y1), (x2, y2), 1)
        # Arrowhead
        pygame.draw.circle(surf, (255, 200, 80), (x2, y2), 5)


# ======================
# GAME CLASS
# ======================
class WumpusWorld:
    def __init__(self, grid_size=6):
        self.grid_size  = grid_size
        self.num_pits   = grid_size  # Number of pits = grid size
        self.high_score = load_high_score(grid_size)  # Load from CSV
        self.game_state = "MENU"   # MENU | PLAYING | PAUSED | AIM | GAME_OVER | WIN
        self._init_board()

    def _init_board(self):
        self.agent_pos    = (0, 0)
        self.agent_alive  = True
        self.has_gold     = False
        self.wumpus_alive = True
        self.arrow_used   = False
        self.visited      = {(0, 0)}
        self.scored_cells = {(0, 0)}
        self.message      = ""
        self.score        = 0
        self.popups       = []          # [x, y, text, alpha, col]
        self.aim_dir      = None        # (dr, dc) while in AIM mode
        self.arrow        = None        # ArrowProjectile or None

        self.wumpus = self._rand(exclude=[(0, 0)])
        self.gold   = self._rand(exclude=[(0, 0), self.wumpus])
        self.pits   = []
        for _ in range(self.num_pits):
            p = self._rand(exclude=[(0,0), self.wumpus, self.gold] + self.pits)
            self.pits.append(p)

    def _rand(self, exclude=[]):
        while True:
            c = (random.randint(0, self.grid_size-1), random.randint(0, self.grid_size-1))
            if c not in exclude:
                return c

    def adjacent(self, pos):
        x, y = pos
        nb = []
        if x > 0:                  nb.append((x-1, y))
        if x < self.grid_size-1:   nb.append((x+1, y))
        if y > 0:                  nb.append((x, y-1))
        if y < self.grid_size-1:   nb.append((x, y+1))
        return nb

    def percepts(self):
        p = []
        if any(pit in self.adjacent(self.agent_pos) for pit in self.pits):
            p.append("Breeze")
        if self.wumpus_alive and self.wumpus in self.adjacent(self.agent_pos):
            p.append("Stench")
        if self.agent_pos == self.gold and not self.has_gold:
            p.append("Glitter")
        return p

    # ── scoring ──
    def _add_score(self, pts, row, col_idx):
        self.score += pts
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.grid_size, self.score)  # Save to CSV
        cx, cy = grid_to_screen(row, col_idx)
        col = WIN_COL if pts > 0 else LOSE_COL
        lbl = f"+{pts}" if pts > 0 else str(pts)
        self.popups.append([cx, cy - 10, lbl, 255, col])

    def update_popups(self):
        for p in self.popups:
            p[1] -= 0.7
            p[3] = max(0, p[3] - 4)
        self.popups = [p for p in self.popups if p[3] > 0]

    # ── ARROW ANIMATION UPDATE ──
    def update_arrow(self):
        if self.arrow is None or self.arrow.done:
            return
        self.arrow.frac += self.arrow.speed
        if self.arrow.frac >= 1.0:
            # Advance to next cell
            self.arrow.row += self.arrow.dr
            self.arrow.col += self.arrow.dc
            self.arrow.frac = 0.0
            r, c = self.arrow.row, self.arrow.col
            # Check hit
            if self.wumpus_alive and (r, c) == self.wumpus:
                self.arrow.hit_wumpus = True
                self.arrow.done       = True
                self.wumpus_alive     = False
                self._add_score(300, r, c)
                self.message = "Wumpus slain! +300 (-50 arrow)"
                return
            # Check out of bounds
            if not (0 <= r < self.grid_size and 0 <= c < self.grid_size):
                self.arrow.done = True
                self.message    = "Arrow missed! (-50 charged on fire)"

    # ── actions ──
    def enter_aim_mode(self):
        """Enter aim mode so the player can choose a direction."""
        if self.arrow_used or self.game_state != "PLAYING":
            return
        self.game_state = "AIM"
        self.aim_dir    = None
        self.message    = "AIM: Press an arrow key to shoot!"

    def fire_arrow(self, dr, dc):
        """Fire the arrow in direction (dr, dc) from agent pos."""
        if self.arrow_used:
            return
        self.arrow_used = True
        self.game_state = "PLAYING"
        r, c = self.agent_pos
        self._add_score(-50, r, c)   # Always -50 for firing
        # Start arrow one step ahead of the agent
        self.arrow = ArrowProjectile(r, c, dr, dc)

    def cancel_aim(self):
        self.game_state = "PLAYING"
        self.message    = "Aim cancelled."

    def move(self, dx, dy):
        if self.game_state != "PLAYING":
            return
        x, y   = self.agent_pos
        nx, ny = x + dx, y + dy
        if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
            self.agent_pos = (nx, ny)
            self.visited.add((nx, ny))
            safe = ((nx, ny) not in self.pits and
                    not ((nx, ny) == self.wumpus and self.wumpus_alive))
            if safe and (nx, ny) not in self.scored_cells:
                self.scored_cells.add((nx, ny))
                self._add_score(10, nx, ny)
            self._check_danger()
            # Auto-win when carrying gold and stepping back to start
            if self.has_gold and self.agent_pos == (0, 0) and self.game_state == "PLAYING":
                self.game_state = "WIN"
                self.message    = "Escaped with the gold!"

    def _check_danger(self):
        if self.agent_pos in self.pits:
            self.agent_alive = False
            self.game_state  = "GAME_OVER"
            self.message     = "Fell into a pit!"
        elif self.agent_pos == self.wumpus and self.wumpus_alive:
            self.agent_alive = False
            self.game_state  = "GAME_OVER"
            self.message     = "Eaten by the Wumpus!"

    def grab(self):
        if self.game_state != "PLAYING":
            return
        r, c = self.agent_pos
        if (r, c) == self.gold and not self.has_gold:
            self.has_gold = True
            self._add_score(1000, r, c)          # +1000 immediately on grab
            self.message  = "Gold grabbed! +1000 pts! Head to start!"
        if self.has_gold and (r, c) == (0, 0):
            self.game_state = "WIN"
            self.message    = "Escaped with the gold!"

    def restart(self):
        hs = self.high_score
        self._init_board()
        self.high_score = hs
        self.game_state = "PLAYING"


# ======================
# DRAW: BACKGROUND
# ======================
def draw_background():
    screen.fill(BG_DARK)
    for y in range(0, HEIGHT, 4):
        a = 6 if (y // 4) % 3 == 0 else 2
        s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        s.fill((255, 255, 255, a))
        screen.blit(s, (0, y))


def draw_cells(game):
    for row in range(game.grid_size):
        for col in range(game.grid_size):
            rect = pygame.Rect(GRID_OFFSET_X + col * CELL_SIZE, 
                             GRID_OFFSET_Y + row * CELL_SIZE,
                             CELL_SIZE, CELL_SIZE)
            cell = (row, col)
            if cell == (0, 0):
                base = START_COL
            elif cell in game.visited:
                base = CELL_MID
            else:
                base = CELL_DARK
            draw_rrect(screen, base, rect, radius=4)

            if cell in game.visited:
                adj = game.adjacent(cell)
                if any(p in adj for p in game.pits):
                    s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    s.fill((40, 80, 200, 22))
                    screen.blit(s, rect.topleft)
                if game.wumpus_alive and game.wumpus in adj:
                    s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    s.fill((180, 20, 40, 22))
                    screen.blit(s, rect.topleft)

            if cell == (0, 0):
                pygame.draw.rect(screen, START_BORDER, rect, 2, border_radius=4)
            pygame.draw.rect(screen, GRID_LINE, rect, 1, border_radius=4)

    # ── Aim-mode overlay: highlight all shootable cells ──
    if game.game_state == "AIM":
        ar, ac = game.agent_pos
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = ar + dr, ac + dc
            while 0 <= nr < game.grid_size and 0 <= nc < game.grid_size:
                hrect = pygame.Rect(GRID_OFFSET_X + nc * CELL_SIZE, 
                                    GRID_OFFSET_Y + nr * CELL_SIZE,
                                    CELL_SIZE, CELL_SIZE)
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill((AIM_COL[0], AIM_COL[1], AIM_COL[2], 28))
                screen.blit(s, hrect.topleft)
                pygame.draw.rect(screen, AIM_COL, hrect, 2, border_radius=4)
                nr += dr
                nc += dc

    # ── Draw directional arrow indicators in AIM mode ──
    if game.game_state == "AIM":
        ar, ac = game.agent_pos
        cx, cy = grid_to_screen(ar, ac)
        dirs = [(-1,0,0,-28,"↑"),(1,0,0,28,"↓"),(0,-1,-28,0,"←"),(0,1,28,0,"→")]
        for dr, dc, ox, oy, sym in dirs:
            nr = ar + dr
            nc = ac + dc
            if 0 <= nr < game.grid_size and 0 <= nc < game.grid_size:
                tx = cx + ox
                ty = cy + oy
                # Pulsing indicator
                alpha = int(180 + 75 * math.sin(tick * 0.12))
                s = tiny_font.render(sym, True, AIM_COL)
                surf = pygame.Surface(s.get_size(), pygame.SRCALPHA)
                surf.blit(s, (0,0))
                surf.set_alpha(alpha)
                screen.blit(surf, (tx - s.get_width()//2, ty - s.get_height()//2))


def grid_to_screen(row, col):
    """Convert grid coordinates to screen pixel coordinates (center of cell)."""
    cx = GRID_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    cy = GRID_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
    return cx, cy


# ======================
# DRAW: SPRITES
# ======================
def draw_agent(game):
    row, col = game.agent_pos
    cx, cy = grid_to_screen(row, col)

    # In AIM mode, use orange glow
    glow_col  = AIM_COL  if game.game_state == "AIM" else AGENT_GLOW
    inner_col = (255,220,180) if game.game_state == "AIM" else AGENT_INNER
    ring_col  = AIM_COL  if game.game_state == "AIM" else AGENT_COL

    pr = int(pulse(26, 4, speed=3))
    draw_glow_circle(screen, glow_col, (cx, cy), pr, layers=7, alpha_step=20)
    pygame.draw.circle(screen, glow_col,  (cx, cy), pr + 2)
    pygame.draw.circle(screen, ring_col,  (cx, cy), pr)
    pygame.draw.circle(screen, inner_col, (cx, cy), pr - 10)
    pygame.draw.rect(screen, ring_col, (cx-2, cy-14, 4, 28), border_radius=2)
    pygame.draw.rect(screen, ring_col, (cx-10, cy-2, 20, 4), border_radius=2)

    # Aim-mode: draw spinning targeting reticle
    if game.game_state == "AIM":
        for i in range(4):
            a  = math.radians(i * 90 + tick * 4)
            x1 = cx + int(32 * math.cos(a))
            y1 = cy + int(32 * math.sin(a))
            x2 = cx + int(40 * math.cos(a))
            y2 = cy + int(40 * math.sin(a))
            pygame.draw.line(screen, AIM_COL, (x1,y1), (x2,y2), 2)

    if game.has_gold:
        pygame.draw.circle(screen, GOLD_COL,   (cx+16, cy-16), 7)
        pygame.draw.circle(screen, GOLD_INNER, (cx+16, cy-16), 4)


def draw_gold(game):
    if game.has_gold:
        return
    row, col = game.gold
    cx, cy = grid_to_screen(row, col)
    r  = int(pulse(18, 4, speed=2))
    draw_glow_circle(screen, GOLD_GLOW, (cx, cy), r, layers=8, alpha_step=22)
    angle = tick * 2
    pts = [(cx + (r if i % 2 == 0 else r-6) * math.cos(math.radians(a + angle)),
            cy + (r if i % 2 == 0 else r-6) * math.sin(math.radians(a + angle)))
           for i, a in enumerate([90, 180, 270, 0])]
    pygame.draw.polygon(screen, GOLD_COL, pts)
    inner = [(cx + (r-8)*math.cos(math.radians(a+angle)),
              cy + (r-8)*math.sin(math.radians(a+angle)))
             for a in [90, 180, 270, 0]]
    pygame.draw.polygon(screen, GOLD_INNER, inner)


def draw_wumpus(game):
    if not game.wumpus_alive:
        return
    row, col = game.wumpus
    cx, cy = grid_to_screen(row, col)
    r  = int(pulse(24, 5, speed=1.5))
    draw_glow_circle(screen, WUMPUS_GLOW, (cx, cy), r, layers=8, alpha_step=25)
    pygame.draw.circle(screen, WUMPUS_GLOW,  (cx, cy), r + 2)
    pygame.draw.circle(screen, WUMPUS_COL,   (cx, cy), r)
    pygame.draw.circle(screen, WUMPUS_INNER, (cx, cy), r - 12)
    off = int(pulse(0, 2, speed=4))
    for ex in [cx-8, cx+8]:
        pygame.draw.circle(screen, BG_DARK,  (ex, cy-6+off), 5)
        pygame.draw.circle(screen, GOLD_COL, (ex, cy-6+off), 2)
    pygame.draw.line(screen, WUMPUS_INNER, (cx-6, cy+6), (cx-4, cy+14), 2)
    pygame.draw.line(screen, WUMPUS_INNER, (cx+6, cy+6), (cx+4, cy+14), 2)


def draw_dead_wumpus(game):
    """Draw a skull / X where the wumpus was, briefly."""
    row, col = game.wumpus
    cx, cy = grid_to_screen(row, col)
    # Faded X marks the spot
    col_dim = (80, 30, 40)
    pygame.draw.line(screen, col_dim, (cx-14, cy-14), (cx+14, cy+14), 3)
    pygame.draw.line(screen, col_dim, (cx+14, cy-14), (cx-14, cy+14), 3)
    t = tiny_font.render("☠", True, (100, 40, 50))
    screen.blit(t, (cx - t.get_width()//2, cy - t.get_height()//2 + 16))


def draw_pits(game):
    for row, col in game.pits:
        cx, cy = grid_to_screen(row, col)
        for col_r, radius in [(PIT_GLOW, 28), (PIT_RIM, 22), (PIT_COL, 16)]:
            draw_glow_circle(screen, col_r, (cx, cy), radius, layers=3, alpha_step=15)
            pygame.draw.circle(screen, col_r, (cx, cy), radius)
        for i in range(6):
            a  = math.radians(i * 60 + tick * 1.5)
            x1 = cx + 6  * math.cos(a)
            y1 = cy + 6  * math.sin(a)
            x2 = cx + 20 * math.cos(a + 0.6)
            y2 = cy + 20 * math.sin(a + 0.6)
            pygame.draw.line(screen, PIT_RIM, (int(x1), int(y1)), (int(x2), int(y2)), 1)


def draw_arrow_projectile(game):
    if game.arrow and not game.arrow.done:
        game.arrow.draw(screen)


def draw_popups(game):
    for cx, cy, lbl, alpha, col in game.popups:
        s = small_font.render(lbl, True, col)
        surf = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        surf.blit(s, (0, 0))
        surf.set_alpha(int(alpha))
        screen.blit(surf, (int(cx) - s.get_width() // 2, int(cy)))


# ======================
# DRAW: AIM OVERLAY
# ======================
def draw_aim_overlay():
    """Semi-transparent pulsing border around the grid in AIM mode."""
    alpha = int(60 + 40 * math.sin(tick * 0.15))
    grid_w = GRID_SIZE * CELL_SIZE
    grid_h = GRID_SIZE * CELL_SIZE
    border_surf = pygame.Surface((grid_w, grid_h), pygame.SRCALPHA)
    pygame.draw.rect(border_surf, (*AIM_COL, alpha),
                     (0, 0, grid_w, grid_h), 6)
    screen.blit(border_surf, (GRID_OFFSET_X, GRID_OFFSET_Y))


# ======================
# DRAW: OVERLAYS
# ======================
def draw_pause_overlay():
    grid_w = GRID_SIZE * CELL_SIZE
    grid_h = GRID_SIZE * CELL_SIZE
    o = pygame.Surface((grid_w, grid_h), pygame.SRCALPHA)
    o.fill((0, 0, 0, 145))
    screen.blit(o, (GRID_OFFSET_X, GRID_OFFSET_Y))
    cx, cy = WIDTH // 2, GRID_OFFSET_Y + grid_h // 2
    draw_glow_circle(screen, (30, 55, 115), (cx, cy), 80, layers=8, alpha_step=13)
    card = pygame.Rect(cx-155, cy-65, 310, 130)
    draw_rrect(screen, (15, 15, 28), card, radius=16, border=2, bcol=PAUSE_COL)
    draw_glow_rect(screen, PAUSE_COL, card, radius=16, layers=3, alpha_step=9)
    h = big_font.render("PAUSED", True, PAUSE_COL)
    screen.blit(h, (cx - h.get_width()//2, cy - 52))
    s = small_font.render("Click Resume or press  P  to continue", True, TEXT_DIM)
    screen.blit(s, (cx - s.get_width()//2, cy + 8))


def draw_end_screen(game):
    grid_w = GRID_SIZE * CELL_SIZE
    grid_h = GRID_SIZE * CELL_SIZE
    o = pygame.Surface((grid_w, grid_h), pygame.SRCALPHA)
    o.fill((0, 0, 0, 160))
    screen.blit(o, (GRID_OFFSET_X, GRID_OFFSET_Y))
    win     = game.game_state == "WIN"
    col     = WIN_COL   if win else LOSE_COL
    glow    = (20, 100, 50) if win else (100, 20, 30)
    heading = "VICTORY!" if win else "DEFEAT"
    cx, cy  = WIDTH // 2, GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE // 2
    draw_glow_circle(screen, glow, (cx, cy), 90, layers=10, alpha_step=17)
    card = pygame.Rect(cx-190, cy-95, 380, 190)
    draw_rrect(screen, (14, 14, 26), card, radius=16, border=2, bcol=col)
    draw_glow_rect(screen, col, card, radius=16, layers=4, alpha_step=11)
    h = big_font.render(heading, True, col)
    screen.blit(h, (cx - h.get_width()//2, cy - 80))
    s = med_font.render(game.message, True, TEXT_MAIN)
    screen.blit(s, (cx - s.get_width()//2, cy - 30))
    sc = score_font.render(f"Score: {game.score}", True, GOLD_COL)
    screen.blit(sc, (cx - sc.get_width()//2, cy + 12))
    hi = small_font.render(f"High Score: {game.high_score}", True, TEXT_DIM)
    screen.blit(hi, (cx - hi.get_width()//2, cy + 50))
    
    # Show if this is a new high score
    if game.score == game.high_score and game.score > 0:
        new_hs = tiny_font.render("★ NEW HIGH SCORE! ★", True, GOLD_COL)
        screen.blit(new_hs, (cx - new_hs.get_width()//2, cy + 72))
    
    if win:
        ex = tiny_font.render("Exiting automatically...", True, TEXT_DIM)
        screen.blit(ex, (cx - ex.get_width()//2, cy + 92))


def draw_menu_screen():
    screen.fill(BG_DARK)
    for y in range(0, HEIGHT, 4):
        a = 5 if (y//4) % 3 == 0 else 2
        s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        s.fill((255, 255, 255, a))
        screen.blit(s, (0, y))
    cx, cy = WIDTH//2, HEIGHT//2 - 80
    draw_glow_circle(screen, (40, 28, 100), (cx, cy), 130, layers=12, alpha_step=11)
    t = big_font.render("WUMPUS  WORLD", True, TEXT_ACCENT)
    screen.blit(t, (cx - t.get_width()//2, cy - 110))
    sub = med_font.render("Dark Dungeon Edition", True, TEXT_DIM)
    screen.blit(sub, (cx - sub.get_width()//2, cy - 62))
    legend = [
        (AGENT_COL,   "●  Knight — that's you"),
        (WUMPUS_COL,  "●  Wumpus — shoot or avoid"),
        (GOLD_COL,    "◆  Gold — grab & return to start"),
        (PIT_GLOW,    "●  Pit — instant death"),
    ]
    for i, (c, txt) in enumerate(legend):
        l = small_font.render(txt, True, c)
        screen.blit(l, (cx - l.get_width()//2, cy - 18 + i * 26))
    scoring = [
        (WIN_COL,  "+10 pts   per new safe cell visited"),
        (LOSE_COL, "-50 pts   when arrow is fired"),
        (WIN_COL,  "+300 pts  for killing the Wumpus"),
        (GOLD_COL, "+1000 pts   for winning the game"),
    ]
    for i, (c, txt) in enumerate(scoring):
        s = tiny_font.render(txt, True, c)
        screen.blit(s, (cx - s.get_width()//2, cy + 88 + i * 22))
    kb = small_font.render(
        "Arrows: Move   SPACE: Aim & Shoot   G: Grab   P: Pause", True, TEXT_DIM)
    screen.blit(kb, (cx - kb.get_width()//2, cy + 184))


# ======================
# DRAW: PANEL
# ======================
def draw_panel(game, buttons):
    py0  = HEIGHT - PANEL_HEIGHT
    prect = pygame.Rect(0, py0, WIDTH, PANEL_HEIGHT)
    draw_rrect(screen, PANEL_BG, prect, radius=0)
    pygame.draw.line(screen, PANEL_BORDER, (0, py0), (WIDTH, py0), 2)

    row1 = py0 + 12
    row2 = py0 + 44
    row3 = py0 + 76

    # ── Score ──
    sc = score_font.render(f"Score: {game.score}", True, GOLD_COL)
    screen.blit(sc, (14, row1))
    hi = tiny_font.render(f"Best: {game.high_score}", True, TEXT_DIM)
    screen.blit(hi, (14, row1 + 32))

    # ── Percept badges ──
    percepts    = game.percepts() if game.game_state in ("PLAYING","AIM") else []
    perc_info   = [("Breeze", "💨", AGENT_COL),
                   ("Stench", "🦨", WUMPUS_COL),
                   ("Glitter","✨", GOLD_COL)]
    px = WIDTH // 2 - 95
    for key, icon, col in perc_info:
        active = key in percepts
        bg   = (28, 34, 62) if active else (16, 18, 32)
        br   = pygame.Rect(px - 4, row1 - 2, 72, 26)
        draw_rrect(screen, bg, br, radius=6, border=1,
                   bcol=col if active else PANEL_BORDER)
        t = tiny_font.render(f"{icon} {key}", True, col if active else TEXT_DIM)
        screen.blit(t, (px, row1 + 2))
        px += 78

    # ── Arrow / gold / wumpus badges ──
    badges = []
    if game.has_gold:         badges.append(("◆ GOLD",   GOLD_COL))
    if game.arrow_used:       badges.append(("✗ ARROW",  (155,70,70)))
    else:                     badges.append(("↑ ARROW",  (70,155,90)))
    if not game.wumpus_alive: badges.append(("☠ WUMPUS", (115,115,135)))
    bx = WIDTH - 14
    for text, col in reversed(badges):
        t  = tiny_font.render(text, True, col)
        bx -= t.get_width() + 8
        br  = pygame.Rect(bx-6, row1-2, t.get_width()+12, t.get_height()+6)
        draw_rrect(screen, (20, 20, 38), br, radius=6, border=1, bcol=col)
        screen.blit(t, (bx, row1 + 1))
        bx -= 6

    # ── Message ──
    msg_state = game.game_state in ("PLAYING", "AIM")
    if game.message and msg_state:
        good_words = ("gold","slain","return","grabbed")
        bad_words  = ("eaten","pit","missed")
        aim_words  = ("aim","shoot")
        col = (AIM_COL   if any(w in game.message.lower() for w in aim_words)
               else WIN_COL  if any(w in game.message.lower() for w in good_words)
               else LOSE_COL if any(w in game.message.lower() for w in bad_words)
               else TEXT_DIM)
        msg = small_font.render(f"▶  {game.message}", True, col)
        screen.blit(msg, (14, row2 + 14))

    # ── AIM hint in panel ──
    if game.game_state == "AIM":
        hint = tiny_font.render("← ↑ → ↓  to fire   |   ESC to cancel", True, AIM_COL)
        screen.blit(hint, (14, row3 + 10))

    # ── Position ──
    pos = tiny_font.render(
        f"POS ({game.agent_pos[0]},{game.agent_pos[1]})", True, TEXT_DIM)
    screen.blit(pos, (WIDTH - pos.get_width() - 14, row2 + 14))

    # ── Buttons ──
    for btn in buttons:
        btn.draw(screen)


# ======================
# BUILD BUTTONS
# ======================
def build_buttons(state):
    py0 = HEIGHT - PANEL_HEIGHT
    by  = py0 + PANEL_HEIGHT - 50
    bw, bh, gap = 100, 38, 10

    if state == "MENU":
        cx = WIDTH // 2
        return [Button((cx - 75, by, 150, bh), "START GAME", BTN_START, "▶")]

    if state in ("PLAYING", "AIM"):
        # 3 buttons: PAUSE | RESTART | EXIT — centred
        total = 3 * bw + 2 * gap
        sx    = (WIDTH - total) // 2
        return [
            Button((sx,              by, bw, bh), "PAUSE",   BTN_PAUSE,   "⏸"),
            Button((sx + bw+gap,     by, bw, bh), "RESTART", BTN_RESTART, "↺"),
            Button((sx + 2*(bw+gap), by, bw, bh), "EXIT",    BTN_EXIT,    "✕"),
        ]

    if state == "PAUSED":
        # 3 buttons: RESUME | RESTART | EXIT — centred
        total = 3 * bw + 2 * gap
        sx    = (WIDTH - total) // 2
        return [
            Button((sx,              by, bw, bh), "RESUME",  BTN_RESUME,  "▶"),
            Button((sx + bw+gap,     by, bw, bh), "RESTART", BTN_RESTART, "↺"),
            Button((sx + 2*(bw+gap), by, bw, bh), "EXIT",    BTN_EXIT,    "✕"),
        ]

    if state in ("GAME_OVER", "WIN"):
        total = 2 * bw + gap
        sx    = (WIDTH - total) // 2
        return [
            Button((sx,          by, bw, bh), "PLAY AGAIN", BTN_START, "↺"),
            Button((sx + bw+gap, by, bw, bh), "EXIT",       BTN_EXIT,  "✕"),
        ]

    return []


# ======================
# DIMENSION HELPERS
# ======================
GRID_OFFSET_X = 0  # X offset to center grid
GRID_OFFSET_Y = 0  # Y offset to center grid

def calculate_dimensions(grid_size):
    """Calculate cell size and grid position for given grid size in fullscreen."""
    global GRID_SIZE, CELL_SIZE, WIDTH, HEIGHT, GRID_OFFSET_X, GRID_OFFSET_Y
    GRID_SIZE = grid_size
    WIDTH     = SCREEN_WIDTH
    HEIGHT    = SCREEN_HEIGHT
    
    # Calculate cell size to fit the screen
    max_cell_w = (SCREEN_WIDTH - 100) // grid_size
    max_cell_h = (SCREEN_HEIGHT - PANEL_HEIGHT - 100) // grid_size
    CELL_SIZE = min(max_cell_w, max_cell_h, 120)  # Cap at 120px per cell
    
    # Calculate offsets to center the grid
    grid_width = GRID_SIZE * CELL_SIZE
    grid_height = GRID_SIZE * CELL_SIZE
    GRID_OFFSET_X = (SCREEN_WIDTH - grid_width) // 2
    GRID_OFFSET_Y = (SCREEN_HEIGHT - PANEL_HEIGHT - grid_height) // 2


def init_screen():
    """Create/recreate the pygame screen in fullscreen mode."""
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("⚔  Wumpus World")


def draw_grid_size_menu():
    """Draw menu with grid size selection buttons."""
    screen.fill(BG_DARK)
    for y in range(0, HEIGHT, 4):
        a = 5 if (y//4) % 3 == 0 else 2
        s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        s.fill((255, 255, 255, a))
        screen.blit(s, (0, y))
    
    cx, cy = WIDTH//2, HEIGHT//2 - 100
    draw_glow_circle(screen, (40, 28, 100), (cx, cy), 130, layers=12, alpha_step=11)
    
    t = big_font.render("SELECT GRID SIZE", True, TEXT_ACCENT)
    screen.blit(t, (cx - t.get_width()//2, cy - 140))
    
    sub = med_font.render("Choose your dungeon difficulty", True, TEXT_DIM)
    screen.blit(sub, (cx - sub.get_width()//2, cy - 95))
    
    # Load all high scores
    all_scores = get_all_high_scores()
    
    # Grid size options as buttons
    sizes = [4, 6, 8, 10, 16]
    labels = ["Easy", "Normal", "Hard", "Expert", "Insane"]
    btn_w, btn_h = 100, 60
    gap = 20
    total_width = len(sizes) * btn_w + (len(sizes) - 1) * gap
    start_x = (WIDTH - total_width) // 2
    
    size_buttons = []
    for i, (size, label) in enumerate(zip(sizes, labels)):
        x = start_x + i * (btn_w + gap)
        y = cy - 20
        btn = Button((x, y, btn_w, btn_h), f"{size}×{size}", BTN_START)
        btn.grid_size = size  # Store grid size in button
        size_buttons.append(btn)
        
        # Draw difficulty label below button
        diff_label = tiny_font.render(label, True, TEXT_DIM)
        screen.blit(diff_label, (x + btn_w//2 - diff_label.get_width()//2, y + btn_h + 8))
        
        # Draw high score below difficulty
        high = all_scores.get(size, 0)
        if high > 0:
            hs_label = tiny_font.render(f"Best: {high}", True, GOLD_COL)
            screen.blit(hs_label, (x + btn_w//2 - hs_label.get_width()//2, y + btn_h + 26))
    
    return size_buttons


# ======================
# MAIN LOOP
# ======================
def main():
    global tick, screen
    
    # Initial setup with default 6x6
    calculate_dimensions(6)
    init_screen()
    
    # Start with grid size selection
    selecting_grid = True
    grid_size_buttons = draw_grid_size_menu()
    game = None
    buttons = []
    win_timer = 0

    running = True
    while running:
        tick += 1
        mouse = pygame.mouse.get_pos()

        # Grid size selection phase
        if selecting_grid:
            for btn in grid_size_buttons:
                btn.update(mouse)
            
            draw_grid_size_menu()
            for btn in grid_size_buttons:
                btn.draw(screen)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                
                for btn in grid_size_buttons:
                    if btn.clicked(event):
                        # Grid size selected - initialize game
                        selected_size = btn.grid_size
                        calculate_dimensions(selected_size)
                        init_screen()
                        game = WumpusWorld(grid_size=selected_size)
                        game.game_state = "MENU"
                        buttons = build_buttons(game.game_state)
                        selecting_grid = False
                        break
            
            clock.tick(30)
            continue
        
        # Normal game loop (existing code)
        for btn in buttons:
            btn.update(mouse)
        game.update_popups()
        game.update_arrow()

        # Auto-exit 2 seconds (60 frames at 30fps) after WIN
        if game.game_state == "WIN":
            win_timer += 1
            if win_timer >= 60:
                running = False

        # ── Draw ──
        if game.game_state == "MENU":
            draw_menu_screen()
        else:
            draw_background()
            draw_cells(game)
            draw_pits(game)
            draw_gold(game)
            if game.wumpus_alive:
                draw_wumpus(game)
            else:
                draw_dead_wumpus(game)
            draw_arrow_projectile(game)
            draw_agent(game)
            draw_popups(game)

            if game.game_state == "AIM":
                draw_aim_overlay()
            elif game.game_state == "PAUSED":
                draw_pause_overlay()
            elif game.game_state in ("GAME_OVER", "WIN"):
                draw_end_screen(game)

        draw_panel(game, buttons)
        pygame.display.flip()

        # ── Events ──
        prev_state = game.game_state
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Button clicks
            for btn in buttons:
                if btn.clicked(event):
                    lbl = btn.label.strip()
                    if lbl == "START GAME":
                        game._init_board()
                        game.game_state = "PLAYING"
                    elif lbl == "PAUSE":
                        game.game_state = "PAUSED"
                    elif lbl == "RESUME":
                        game.game_state = "PLAYING"
                    elif lbl in ("RESTART", "PLAY AGAIN"):
                        game.restart()
                    elif lbl == "EXIT":
                        running = False

            # Keyboard
            if event.type == pygame.KEYDOWN:

                # ── In AIM mode: arrow keys fire, ESC cancels ──
                if game.game_state == "AIM":
                    if event.key == pygame.K_UP:     game.fire_arrow(-1,  0)
                    elif event.key == pygame.K_DOWN:  game.fire_arrow( 1,  0)
                    elif event.key == pygame.K_LEFT:  game.fire_arrow( 0, -1)
                    elif event.key == pygame.K_RIGHT: game.fire_arrow( 0,  1)
                    elif event.key == pygame.K_ESCAPE: game.cancel_aim()
                    elif event.key == pygame.K_SPACE:  game.cancel_aim()

                # ── Normal movement / actions ──
                elif game.game_state == "PLAYING":
                    if event.key == pygame.K_UP:    game.move(-1,  0)
                    if event.key == pygame.K_DOWN:  game.move( 1,  0)
                    if event.key == pygame.K_LEFT:  game.move( 0, -1)
                    if event.key == pygame.K_RIGHT: game.move( 0,  1)
                    if event.key == pygame.K_SPACE: game.enter_aim_mode()
                    if event.key == pygame.K_g:     game.grab()
                    if event.key == pygame.K_r:     game.restart()
                    if event.key == pygame.K_p:     game.game_state = "PAUSED"
                    if event.key == pygame.K_ESCAPE: running = False

                elif game.game_state == "PAUSED":
                    if event.key == pygame.K_p:     game.game_state = "PLAYING"
                    if event.key == pygame.K_r:     game.restart()
                    if event.key == pygame.K_ESCAPE: running = False

        # Rebuild buttons only when state changes
        if game.game_state != prev_state:
            buttons = build_buttons(game.game_state)

        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
