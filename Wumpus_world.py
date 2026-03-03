import random
from datetime import datetime
from collections import deque
import time

def get_direction_name(dx, dy):
    """Convert direction vector to readable direction"""
    if dx == -1 and dy == 0:
        return "UP"
    elif dx == 1 and dy == 0:
        return "DOWN"
    elif dx == 0 and dy == -1:
        return "LEFT"
    elif dx == 0 and dy == 1:
        return "RIGHT"
    return "UNKNOWN"


class WumpusAIAgent:
    """AI Agent - MUST find and grab gold - NO SURRENDER - INFINITE MOVES"""
    
    def __init__(self, game):
        self.game = game
        self.confirmed_safe = set()
        self.confirmed_dangerous = set()
        self.explored = set()
        self.pit_locations = set()
        self.wumpus_location = None
        self.move_history = deque(maxlen=4)
        
        self.confirmed_safe.add(game.agent_pos)
        self.explored.add(game.agent_pos)
    
    def perceive_and_update(self, percepts):
        """Update knowledge based on perceptions"""
        current_pos = self.game.agent_pos
        self.confirmed_safe.add(current_pos)
        self.explored.add(current_pos)
        
        adjacent_cells = self.game.adjacent(current_pos)
        
        has_breeze = "Breeze" in percepts
        has_stench = "Stench" in percepts
        
        # If no breeze, adjacent cells are DEFINITELY safe from pits
        if not has_breeze:
            for cell in adjacent_cells:
                self.confirmed_safe.add(cell)
        
        # If no stench, adjacent cells are DEFINITELY safe from wumpus
        if not has_stench:
            for cell in adjacent_cells:
                self.confirmed_safe.add(cell)
    
    def update_pit_knowledge(self, pit_pos):
        """Update when we discover a pit"""
        self.pit_locations.add(pit_pos)
        self.confirmed_dangerous.add(pit_pos)
    
    def find_any_valid_path(self):
        """Find ANY valid path to ANY unexplored safe cell"""
        current_pos = self.game.agent_pos
        
        # Get all unexplored cells
        all_cells = set()
        for x in range(1, self.game.grid_size + 1):
            for y in range(1, self.game.grid_size + 1):
                all_cells.add((x, y))
        
        unexplored = all_cells - self.explored
        
        # First try confirmed safe unexplored
        safe_unexplored = unexplored & self.confirmed_safe
        if safe_unexplored:
            # Pick any one
            target = safe_unexplored.pop()
            safe_unexplored.add(target)  # Add back for later
            return self._bfs_path(current_pos, target)
        
        # If no confirmed safe unexplored, try risky unexplored
        # (not confirmed dangerous)
        risky_unexplored = unexplored - self.confirmed_dangerous
        if risky_unexplored:
            target = risky_unexplored.pop()
            risky_unexplored.add(target)  # Add back
            return self._bfs_path(current_pos, target)
        
        return []
    
    def _bfs_path(self, start, goal):
        """BFS to find path from start to goal"""
        if start == goal:
            return []
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            if current == goal:
                return path[1:] if len(path) > 1 else []
            
            for next_pos in self.game.adjacent(current):
                if (next_pos not in visited and 
                    next_pos not in self.confirmed_dangerous):
                    visited.add(next_pos)
                    queue.append((next_pos, path + [next_pos]))
        
        return []
    
    def detect_loop(self, current_pos):
        """Detect if moving in circles"""
        self.move_history.append(current_pos)
        
        if len(self.move_history) == 4:
            # Check for A-B-A-B pattern
            if (self.move_history[0] == self.move_history[2] and
                self.move_history[1] == self.move_history[3]):
                return True
        return False
    
    def get_next_move(self):
        """AI decision making - MUST FIND GOLD - INFINITE MOVES"""
        current_pos = self.game.agent_pos
        percepts = self.game.percepts()
        
        # Update knowledge
        self.perceive_and_update(percepts)
        
        has_glitter = "Glitter" in percepts
        has_glitter_nearby = "Glitter (nearby)" in percepts
        has_stench = "Stench" in percepts
        
        # Priority 1: Grab gold - INSTANT WIN
        if has_glitter:
            return ('grab', None)
        
        # Priority 2: Move towards gold if nearby
        if has_glitter_nearby:
            path = self._bfs_path(current_pos, self.game.gold)
            if path:
                next_pos = path[0]
                dx = next_pos[0] - current_pos[0]
                dy = next_pos[1] - current_pos[1]
                return ('move', (dx, dy))
        
        # Priority 3: Kill Wumpus if adjacent
        if has_stench and not self.game.arrow_used:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                adj_pos = (current_pos[0] + dx, current_pos[1] + dy)
                if self.game.wumpus_alive and adj_pos == self.game.wumpus:
                    return ('fire', (dx, dy))
        
        # Priority 4: KEEP EXPLORING - NEVER GIVE UP - INFINITE MOVES
        # Try to find unexplored cells
        path = self.find_any_valid_path()
        
        if path:
            next_pos = path[0]
            
            # Check for loop and skip if needed
            if self.detect_loop(next_pos):
                # Try to find alternative path
                all_cells = set()
                for x in range(1, self.game.grid_size + 1):
                    for y in range(1, self.game.grid_size + 1):
                        all_cells.add((x, y))
                
                unexplored = all_cells - self.explored
                unexplored_safe = unexplored - self.confirmed_dangerous
                
                # Find any unexplored that's NOT in our loop
                for target in unexplored_safe:
                    if target not in [self.move_history[0], self.move_history[1]]:
                        alt_path = self._bfs_path(current_pos, target)
                        if alt_path:
                            next_pos = alt_path[0]
                            break
            
            dx = next_pos[0] - current_pos[0]
            dy = next_pos[1] - current_pos[1]
            return ('move', (dx, dy))
        
        # Priority 5: Move to ANY safe adjacent cell to keep exploring
        adjacent = self.game.adjacent(current_pos)
        safe_adjacent = [pos for pos in adjacent 
                        if pos not in self.confirmed_dangerous]
        
        if safe_adjacent:
            next_pos = random.choice(safe_adjacent)
            dx = next_pos[0] - current_pos[0]
            dy = next_pos[1] - current_pos[1]
            return ('move', (dx, dy))
        
        # This should never happen - AI must always find a move
        return ('wait', None)


class WumpusWorld:
    def __init__(self, grid_size=6):
        self.grid_size = grid_size
        self.num_pits = grid_size
        self.game_state = "PLAYING"
        self.score_history = []
        self.last_percepts = []
        self._init_board()
        self.ai_agent = None
        self.move_count = 0
        self.max_moves = float('inf')  # INFINITE MOVES
        self.score = 0

    def _init_board(self):
        self.agent_pos = (random.randint(1, self.grid_size), 
                         random.randint(1, self.grid_size))
        self.agent_alive = True
        self.has_gold = False
        self.wumpus_alive = True
        self.arrow_used = False
        self.visited = {self.agent_pos}
        self.scored_cells = {self.agent_pos}
        self.message = ""
        self.score = 0
        self.score_history = []
        self.last_percepts = []

        self.wumpus = self._rand(exclude=[self.agent_pos])
        self.gold = self._rand(exclude=[self.agent_pos, self.wumpus])
        self.pits = []
        for _ in range(self.num_pits):
            p = self._rand(exclude=[self.agent_pos, self.wumpus, self.gold] + self.pits)
            self.pits.append(p)

    def _rand(self, exclude=[]):
        while True:
            c = (random.randint(1, self.grid_size), random.randint(1, self.grid_size))
            if c not in exclude:
                return c

    def adjacent(self, pos):
        x, y = pos
        nb = []
        if x > 1:
            nb.append((x - 1, y))
        if x < self.grid_size:
            nb.append((x + 1, y))
        if y > 1:
            nb.append((x, y - 1))
        if y < self.grid_size:
            nb.append((x, y + 1))
        return nb

    def percepts(self):
        """Generate perceptions based on current position"""
        p = []
        
        if any(pit in self.adjacent(self.agent_pos) for pit in self.pits):
            p.append("Breeze")
        
        if self.wumpus_alive and self.wumpus in self.adjacent(self.agent_pos):
            p.append("Stench")
        
        if self.agent_pos == self.gold and not self.has_gold:
            p.append("Glitter")
        elif self.gold in self.adjacent(self.agent_pos) and not self.has_gold:
            p.append("Glitter (nearby)")
        
        return p

    def _add_score(self, pts, reason=""):
        old_score = self.score
        self.score += pts
        self.score_history.append((old_score, pts, self.score, reason))

    def fire_arrow(self, dr, dc):
        if self.arrow_used:
            return
        
        self.arrow_used = True
        self._add_score(-50, "Arrow fired")
        
        r, c = self.agent_pos
        hit = False
        while True:
            r += dr
            c += dc
            if not (1 <= r <= self.grid_size and 1 <= c <= self.grid_size):
                self.message = "Arrow missed!"
                break
            if self.wumpus_alive and (r, c) == self.wumpus:
                self.wumpus_alive = False
                self._add_score(300, "Wumpus slain")
                self.message = "Wumpus slain!"
                self.last_percepts = ["SCREAM!!!"]
                hit = True
                break
        
        if not hit:
            self.last_percepts = []

    def move(self, dx, dy):
        """Move to adjacent cell"""
        if self.game_state != "PLAYING":
            return
        
        x, y = self.agent_pos
        nx, ny = x + dx, y + dy
        
        # Check bounds
        if not (1 <= nx <= self.grid_size and 1 <= ny <= self.grid_size):
            self.message = "Out of bounds"
            self.last_percepts = ["BUMP!"]
            return
        
        new_pos = (nx, ny)
        
        # Check for pits and wumpus
        if new_pos in self.pits:
            self.ai_agent.update_pit_knowledge(new_pos)
            self.message = "Found pit - backing up"
            return
        
        if new_pos == self.wumpus and self.wumpus_alive:
            self.ai_agent.wumpus_location = new_pos
            self.ai_agent.confirmed_dangerous.add(new_pos)
            self.message = "Found Wumpus - backing up"
            return
        
        # Safe move
        self.agent_pos = new_pos
        self.visited.add(new_pos)
        
        if new_pos not in self.scored_cells:
            self.scored_cells.add(new_pos)
            self._add_score(10, "New cell visited")
            self.message = f"Moved to ({nx},{ny}). +10"
        else:
            self.message = f"Moved to ({nx},{ny})"
        
        self.last_percepts = self.percepts()

    def grab_gold(self):
        """Grab gold and WIN immediately"""
        if self.game_state != "PLAYING":
            return
        
        if self.agent_pos == self.gold and not self.has_gold:
            self.has_gold = True
            self._add_score(1000, "Gold grabbed - WIN!")
            self.message = "Gold grabbed! VICTORY!"
            self.game_state = "WIN"
            self.last_percepts = []

    def restart(self):
        self._init_board()
        self.game_state = "PLAYING"
        self.ai_agent = WumpusAIAgent(self)
        self.move_count = 0


def display_board(game, show_details=True):
    """Display game board"""
    output = []
    output.append("\n")
    output.append("=" * 70 + "\n")
    output.append(" " * 18 + "WUMPUS WORLD\n")
    output.append("=" * 70 + "\n\n")
    
    # Grid header
    output.append("   ")
    for col in range(1, game.grid_size + 1):
        if col < 10:
            output.append(f"  {col}  ")
        else:
            output.append(f" {col:2} ")
    output.append("\n")
    
    # Grid rows
    for row in range(1, game.grid_size + 1):
        if row < 10:
            output.append(f"{row:2} |")
        else:
            output.append(f"{row:2}|")
        
        for col in range(1, game.grid_size + 1):
            cell = (row, col)
            symbol = "   "
            
            if cell == game.agent_pos:
                symbol = " K "
            elif cell == game.gold and not game.has_gold:
                symbol = " G "
            elif cell == game.wumpus and game.wumpus_alive:
                symbol = " W "
            elif cell == game.wumpus and not game.wumpus_alive:
                symbol = " X "
            elif cell in game.pits:
                symbol = " P "
            elif cell in game.visited:
                symbol = " . "
            else:
                symbol = " ? "
            
            output.append(symbol + "|")
        output.append("\n")
        output.append("  +" + "+".join(["---" for _ in range(game.grid_size)]) + "+\n")
    
    if show_details:
        # Status
        output.append("\n" + "=" * 70 + "\n")
        output.append(f"Position: ({game.agent_pos[0]},{game.agent_pos[1]}) | Score: {game.score}\n")
        output.append("-" * 70 + "\n")
        
        if game.last_percepts:
            output.append(f"PERCEPTS: {', '.join(game.last_percepts)}\n")
        else:
            output.append("PERCEPTS: None\n")
        
        output.append(f"Gold: {'GRABBED' if game.has_gold else 'SEARCHING'} | ")
        output.append(f"Arrow: {'USED' if game.arrow_used else 'READY'} | ")
        output.append(f"Wumpus: {'DEAD' if not game.wumpus_alive else 'ALIVE'}\n")
        output.append("-" * 70 + "\n")
        
        if game.message:
            output.append(f">>> {game.message}\n")
        output.append("-" * 70 + "\n")
    
    return "".join(output)


def show_menu():
    menu = []
    menu.append("\n" * 2)
    menu.append("=" * 70 + "\n")
    menu.append(" " * 18 + "WUMPUS WORLD\n")
    menu.append(" " * 12 + "SAFE AI AUTO-RUN\n")
    menu.append("=" * 70 + "\n\n")
    
    menu.append("PERCEPTIONS (5):\n")
    menu.append("  BREEZE     - Pit nearby\n")
    menu.append("  STENCH     - Wumpus nearby\n")
    menu.append("  GLITTER    - Gold location\n")
    menu.append("  BUMP       - Out of bounds\n")
    menu.append("  SCREAM!!! - Wumpus killed\n\n")
    
    menu.append("AI GOAL:\n")
    menu.append("  MUST find and grab the GOLD\n")
    menu.append("  Explore ALL reachable areas\n")
    menu.append("  INFINITE MOVES - NEVER GIVE UP!\n\n")
    
    menu.append("=" * 70 + "\n")
    menu.append("SELECT DIFFICULTY:\n")
    menu.append("=" * 70 + "\n\n")
    
    menu.append("  1. EASY       (4x4)\n")
    menu.append("  2. MEDIUM     (8x8)\n")
    menu.append("  3. HARD       (16x16)\n")
    
    return "".join(menu)


def main():
    difficulty_levels = {
        1: 4,
        2: 8,
        3: 16
    }
    
    while True:
        menu_text = show_menu()
        
        while True:
            try:
                choice = int(input(menu_text + "\nChoice (1/2/3): "))
                if choice in difficulty_levels:
                    grid_size = difficulty_levels[choice]
                    break
            except ValueError:
                pass
        
        game = WumpusWorld(grid_size=grid_size)
        game.ai_agent = WumpusAIAgent(game)
        
        print("\n" + "=" * 70)
        print("GAME STARTED - AUTO RUN - INFINITE MOVES")
        print("=" * 70)
        print(f"Start: ({game.agent_pos[0]},{game.agent_pos[1]}) | Grid: {game.grid_size}x{game.grid_size}")
        print(f"Gold Location: ({game.gold[0]},{game.gold[1]})")
        print("MISSION: Find and grab the gold - NO TIME LIMIT!")
        print("=" * 70 + "\n")
        
        time.sleep(0.5)
        
        while game.game_state == "PLAYING":  # INFINITE - no max_moves check
            board_display = display_board(game)
            print(board_display)
            
            action, params = game.ai_agent.get_next_move()
            game.move_count += 1
            
            if action == 'move':
                dx, dy = params
                direction = get_direction_name(dx, dy)
                print(f"[Move {game.move_count}] -> Direction: {direction}")
                game.move(dx, dy)
            elif action == 'grab':
                print(f"[Move {game.move_count}] -> Action: GRAB GOLD - WIN!")
                game.grab_gold()
            elif action == 'fire':
                dx, dy = params
                direction = get_direction_name(dx, dy)
                print(f"[Move {game.move_count}] -> Action: FIRE ARROW ({direction})")
                game.fire_arrow(dx, dy)
            
            time.sleep(0.5)
        
        board_display = display_board(game)
        print(board_display)
        
        result = "VICTORY - GOLD FOUND!"
        
        print("\n" + "=" * 70)
        print(result)
        print("=" * 70)
        print(f"Final Score: {game.score}")
        print(f"Total Moves: {game.move_count}")
        print(f"Cells Visited: {len(game.visited)}")
        print(f"Gold Found: YES ✓")
        print(f"Wumpus Status: {'KILLED' if not game.wumpus_alive else 'ALIVE'}")
        print("=" * 70 + "\n")
        
        if input("Play again? (Y/N): ").strip().upper() != 'Y':
            break
    
    print("\nThanks for playing!")


if __name__ == "__main__":
    main()
