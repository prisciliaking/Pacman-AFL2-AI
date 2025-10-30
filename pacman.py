import pygame
import heapq
import sys
import random
import time

# === CONFIG ===
TILE = 28
COLS = 15
FPS = 12

# Colors
WALL_COL = (0, 0, 150)
BG_COL = (0, 0, 0)
PAC_COL = (255, 255, 0)
GHOST_BASE_COLS = [(255, 0, 0), (255, 128, 255), (0, 255, 255), (255, 165, 0)]
FRIGHTENED_COL = (50, 100, 255)
EATEN_COL = (180, 180, 180)
PELLET_COL = (200, 200, 200)
TEXT_COL = (255, 255, 255)
READY_COL = (255, 255, 0)

# Frightened & timings
FRIGHTENED_DURATION = 7.0
FRIGHTENED_SPEED_MULT = 2    # larger -> ghosts slower when frightened
GHOST_BASE_COOLDOWN = 1      # ticks between ghost moves (1 => every tick)

# --- 15x15 Map (keep layout you provided) ---
RAW_MAP = [
"###############",
"#.............#",
"#.###.###.###.#",
"#.#...#.#...#.#",
"#.#.#.#.#.#.#.#",
"#.............#",
"#.###.#G#.###.#",
"#.#...GGG...#.#",
"#.###.###.###.#",
"#......P......#",
"#.#.#.#.#.#.#.#",
"#.#...#.#...#.#",
"#.###.###.###.#",
"#.............#",
"###############",
]

# Normalize RAW_MAP rows to exactly COLS characters
MAP = []
for r in RAW_MAP:
    row = list(r)
    if len(row) < COLS:
        row += [' '] * (COLS - len(row))
    elif len(row) > COLS:
        row = row[:COLS]
    MAP.append(row)

ROWS = len(MAP)
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE

# === UTILITIES ===
def in_bounds(pos):
    x, y = pos
    return 0 <= x < COLS and 0 <= y < ROWS

def is_wall(pos):
    x, y = pos
    if not (0 <= y < ROWS): return True
    if not (0 <= x < COLS): return True
    return MAP[y][x] == '#'

def passable(pos):
    # treat any non-wall as passable; support horizontal warp
    x, y = pos
    if not (0 <= y < ROWS):
        return False
    if 0 <= x < COLS:
        return MAP[y][x] != '#'
    if x < 0:
        return MAP[y][COLS - 1] != '#'
    if x >= COLS:
        return MAP[y][0] != '#'
    return False

def wrap_pos(pos):
    x, y = pos
    if x < 0: x = COLS - 1
    if x >= COLS: x = 0
    return (x, y)

def neighbors(pos):
    x, y = pos
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = x + dx, y + dy
        if 0 <= ny < ROWS:
            if nx < 0:
                wx = COLS - 1
                if MAP[ny][wx] != '#':
                    yield (wx, ny)
            elif nx >= COLS:
                wx = 0
                if MAP[ny][wx] != '#':
                    yield (wx, ny)
            else:
                if MAP[ny][nx] != '#':
                    yield (nx, ny)

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# === A* IMPLEMENTATION ===
def a_star(start, goal):
    # If goal not passable, return empty path
    if not passable(goal):
        return []
    open_heap = [(manhattan(start, goal), 0, start)]
    came_from = {start: None}
    gscore = {start: 0}
    visited = set()
    while open_heap:
        f, g, current = heapq.heappop(open_heap)
        if current == goal:
            # rebuild path (start exclusive -> goal inclusive)
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        if current in visited:
            continue
        visited.add(current)
        for n in neighbors(current):
            tentative_g = gscore[current] + 1
            if n not in gscore or tentative_g < gscore[n]:
                gscore[n] = tentative_g
                heapq.heappush(open_heap, (tentative_g + manhattan(n, goal), tentative_g, n))
                came_from[n] = current
    return []

# === ENTITIES ===
class PacMan:
    def __init__(self, pos):
        self.start = pos
        self.pos = pos
        self.desired = pos
        self.lives = 3
        self.score = 0

    def update(self):
        if self.pos != self.desired:
            self.pos = wrap_pos(self.desired)

    def reset(self):
        self.pos = self.start
        self.desired = self.start
        self.lives = 3
        self.score = 0

class Ghost:
    def __init__(self, pos, idx, corner, name):
        self.start = pos
        self.pos = pos
        self.idx = idx
        self.name = name
        self.base_color = GHOST_BASE_COLS[idx % len(GHOST_BASE_COLS)]
        self.corner = corner
        self.path = []
        self.cached_target = None
        self.recalc_counter = 0
        self.mode = "scatter"   # scatter, chase, frightened, eaten
        self.cooldown = 0
        self.eaten = False

    def compute_path(self, target):
        path = a_star(self.pos, target)
        if path:
            self.path = path
            self.cached_target = target
            return True
        return False

    def step(self):
        if self.path:
            self.pos = self.path.pop(0)
            self.pos = wrap_pos(self.pos)

    def random_move(self):
        opts = list(neighbors(self.pos))
        if opts:
            self.pos = random.choice(opts)

    def reset(self):
        self.pos = self.start
        self.path.clear()
        self.cached_target = None
        self.mode = "scatter"
        self.cooldown = 0
        self.eaten = False
        self.recalc_counter = 0

    def color(self):
        if self.mode == "frightened":
            return FRIGHTENED_COL
        if self.mode == "eaten":
            return EATEN_COL
        return self.base_color

# === PYGAME SETUP ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man (15x15) - A* Ghosts (Scatter/Chase/Frightened)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18, bold=True)
big_font = pygame.font.SysFont("Arial", 28, bold=True)

# === PARSE MAP & SETUP GAME ===
def setup_game():
    pac_start = None
    ghost_positions = []
    for y in range(ROWS):
        for x in range(COLS):
            ch = MAP[y][x]
            if ch == 'P':
                pac_start = (x, y)
                MAP[y][x] = '.'   # mark underlying as pellet/ground
            if ch == 'G':
                ghost_positions.append((x, y))
                MAP[y][x] = '.'
    if pac_start is None:
        pac_start = (COLS//2, ROWS//2)

    # ensure at most 4 ghosts (or fewer if map has fewer G)
    if not ghost_positions:
        midy = ROWS//2
        gx = COLS//2
        ghost_positions = [(gx-1, midy), (gx, midy), (gx+1, midy)]
    corners = [(COLS-2,1), (1,1), (COLS-2, ROWS-2), (1, ROWS-2)]
    names = ["Blinky","Pinky","Inky","Clyde"]
    ghosts = []
    for i,pos in enumerate(ghost_positions[:4]):
        name = names[i] if i < len(names) else f"Ghost{i}"
        corner = corners[i % len(corners)]
        ghosts.append(Ghost(pos, i, corner, name))

    pellets = {(x,y) for y in range(ROWS) for x in range(COLS) if MAP[y][x] == '.'}
    # choose power pellets locations (approx): near corners of inner area
    guess_power = {(1,1),(COLS-2,1),(1,ROWS-2),(COLS-2,ROWS-2)}
    power_pellets = {p for p in guess_power if p in pellets}
    return PacMan(pac_start), ghosts, pellets, power_pellets

# Mode cycle: shortened for testing as requested
CYCLE = [("scatter",5.0), ("chase",10.0), ("scatter",5.0), ("chase",10.0), ("scatter",3.0), ("chase",9999.0)]
cycle_index = 0
cycle_start = time.time()

def global_mode_now():
    global cycle_index, cycle_start
    # advance cycle if current duration elapsed
    while True:
        mode, dur = CYCLE[cycle_index]
        if time.time() - cycle_start >= dur:
            cycle_start += dur
            cycle_index = min(len(CYCLE)-1, cycle_index+1)
            continue
        return mode

# Target functions (ghost personalities)
def target_blinky(pac, ghosts): return pac.pos

def target_pinky(pac, ghosts):
    dx = pac.desired[0] - pac.pos[0]
    dy = pac.desired[1] - pac.pos[1]
    tx = pac.pos[0] + 4 * dx
    ty = pac.pos[1] + 4 * dy
    tx = max(0, min(COLS-1, tx))
    ty = max(0, min(ROWS-1, ty))
    return (tx, ty)

def target_inky(pac, ghosts):
    blinky = next((g for g in ghosts if g.name == "Blinky"), None)
    if not blinky:
        return pac.pos
    dx = pac.desired[0] - pac.pos[0]
    dy = pac.desired[1] - pac.pos[1]
    ahead = (pac.pos[0] + 2*dx, pac.pos[1] + 2*dy)
    vx = ahead[0] - blinky.pos[0]
    vy = ahead[1] - blinky.pos[1]
    tx = blinky.pos[0] + 2*vx
    ty = blinky.pos[1] + 2*vy
    tx = max(0, min(COLS-1, tx))
    ty = max(0, min(ROWS-1, ty))
    return (tx, ty)

def target_clyde(pac, ghosts):
    clyde = next((g for g in ghosts if g.name == "Clyde"), None)
    if clyde is None:
        return pac.pos
    d = manhattan(clyde.pos, pac.pos)
    return pac.pos if d > 8 else clyde.corner

CHASE_TARGET_FN = {
    "Blinky": target_blinky,
    "Pinky": target_pinky,
    "Inky": target_inky,
    "Clyde": target_clyde,
}

# === DRAW ===
def draw(status_text=""):
    screen.fill(BG_COL)
    # draw map + pellets
    for y in range(ROWS):
        for x in range(COLS):
            rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
            ch = MAP[y][x]
            if ch == '#':
                pygame.draw.rect(screen, WALL_COL, rect)
            else:
                if (x,y) in pellets:
                    pygame.draw.circle(screen, PELLET_COL, rect.center, 3)
                if (x,y) in power_pellets:
                    pygame.draw.circle(screen, PELLET_COL, rect.center, 6)
    # Pac-Man
    px, py = pacman.pos
    pygame.draw.circle(screen, PAC_COL, (px*TILE + TILE//2, py*TILE + TILE//2), TILE//2 - 2)
    # Ghosts
    for g in ghosts:
        gx, gy = g.pos
        pygame.draw.circle(screen, g.color(), (gx*TILE + TILE//2, gy*TILE + TILE//2), TILE//2 - 2)
    # HUD
    info = f"Lives: {pacman.lives}   Score: {pacman.score}   Pellets: {len(pellets)}"
    screen.blit(font.render(info, True, TEXT_COL), (8, 6))
    if status_text:
        msg = big_font.render(status_text, True, READY_COL)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 36))
    mode_txt = "FRIGHTENED" if frightened else global_mode_now().upper()
    screen.blit(font.render(f"Mode: {mode_txt}", True, TEXT_COL), (8, HEIGHT-24))
    pygame.display.flip()

# === GAME STATE INIT ===
pacman, ghosts, pellets, power_pellets = setup_game()
started = False
game_over = False
win = False
frightened = False
frightened_end = 0.0

# === RESET HELPER ===
def reset_game():
    global pacman, ghosts, pellets, power_pellets, started, game_over, win, frightened, frightened_end, cycle_index, cycle_start
    pacman, ghosts, pellets, power_pellets = setup_game()
    started = False
    game_over = False
    win = False
    frightened = False
    frightened_end = 0.0
    cycle_index = 0
    cycle_start = time.time()

# === MAIN LOOP ===
running = True
while running:
    clock.tick(FPS)
    draw("GAME OVER" if game_over else "YOU WIN!" if win else "")
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                running = False
            elif ev.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                started = True
                dx = dy = 0
                if ev.key == pygame.K_UP: dy = -1
                elif ev.key == pygame.K_DOWN: dy = 1
                elif ev.key == pygame.K_LEFT: dx = -1
                elif ev.key == pygame.K_RIGHT: dx = 1
                nx, ny = pacman.pos[0] + dx, pacman.pos[1] + dy
                # allow wrap horizontally
                if nx < 0:
                    wx = COLS - 1
                    if passable((wx, ny)):
                        pacman.desired = (wx, ny)
                elif nx >= COLS:
                    wx = 0
                    if passable((wx, ny)):
                        pacman.desired = (wx, ny)
                elif passable((nx, ny)):
                    pacman.desired = (nx, ny)
            elif ev.key == pygame.K_s:
                # manual mode advance (for testing) — we keep this but no console logs
                cycle_index = min(len(CYCLE)-1, cycle_index + 1)
                cycle_start = time.time()

    if not started:
        draw("PRESS ARROW TO START")
        continue

    if game_over or win:
        pygame.time.delay(1500)
        running = False
        continue

    # Pac update
    pacman.update()

    # collect pellets
    if pacman.pos in pellets:
        pellets.remove(pacman.pos)
        pacman.score += 10
        # check power pellet
        if pacman.pos in power_pellets:
            power_pellets.discard(pacman.pos)
            frightened = True
            frightened_end = time.time() + FRIGHTENED_DURATION
            for g in ghosts:
                if not g.eaten:
                    g.mode = "frightened"

    # win?
    if not pellets:
        win = True
        continue

    # frightened timeout
    if frightened and time.time() >= frightened_end:
        frightened = False
        for g in ghosts:
            if not g.eaten:
                g.mode = global_mode_now()

    # update mode and ghost states (respawn handling included)
    curr_global = global_mode_now()
    for g in ghosts:
        if g.eaten and g.pos == g.start:
            # respawn into normal mode
            g.eaten = False
            g.mode = curr_global
            g.reset()
        elif not g.eaten:
            if frightened:
                g.mode = "frightened"
            else:
                g.mode = curr_global

    # ghosts movement & collision
    for g in ghosts:
        if g.cooldown > 0:
            g.cooldown -= 1
            continue

        # determine target based on mode
        if g.mode == "eaten":
            target = g.start
        elif g.mode == "frightened":
            # frightened: random-ish movement; target chosen as far corner from pacman to bias away
            corners = [(1,1),(COLS-2,1),(1,ROWS-2),(COLS-2,ROWS-2)]
            # but we'll prefer random movement when compute_path fails
            best = max(corners, key=lambda c: manhattan(c, pacman.pos))
            target = best
        elif g.mode == "scatter":
            target = g.corner
        else:  # chase
            fn = CHASE_TARGET_FN.get(g.name, lambda p, gs: p.pos)
            target = fn(pacman, ghosts)

        # compute path if needed or step along existing path
        if g.mode == "frightened":
            # frightened: try compute path to a far corner occasionally, else random_move
            if g.cached_target != target or not g.path or g.recalc_counter % 8 == 0:
                ok = g.compute_path(target)
                if not ok:
                    g.random_move()
                else:
                    g.step()
            else:
                # sometimes deviate randomly to be less predictable
                if random.random() < 0.25:
                    g.random_move()
                else:
                    g.step()
        else:
            # chase / scatter / eaten use A* primary
            if g.cached_target != target or not g.path or g.recalc_counter % 6 == 0:
                ok = g.compute_path(target)
                if not ok:
                    g.random_move()
                else:
                    g.step()
            else:
                g.step()

        g.recalc_counter += 1

        # set cooldown for next move depending on mode
        if g.mode == "frightened":
            g.cooldown = max(1, int(round(GHOST_BASE_COOLDOWN * FRIGHTENED_SPEED_MULT)))
        elif g.mode == "eaten":
            g.cooldown = max(0, int(round(GHOST_BASE_COOLDOWN * 0.5)))
        else:
            g.cooldown = GHOST_BASE_COOLDOWN

        # collision handling
        if g.pos == pacman.pos:
            if g.mode == "frightened" and not g.eaten:
                # Pac eats ghost
                pacman.score += 200
                g.eaten = True
                g.mode = "eaten"
                g.path.clear()
                g.cached_target = None
            elif not g.eaten and g.mode != "frightened":
                # pac loses life
                pacman.lives -= 1
                if pacman.lives <= 0:
                    game_over = True
                else:
                    # reset pac & ghosts positions (preserve pellets)
                    pacman.pos = pacman.start
                    pacman.desired = pacman.start
                    for gg in ghosts:
                        gg.reset()
                break

# clean exit
pygame.quit()
sys.exit()
