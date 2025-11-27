"""
Game Board Components for Wordle Visualizer
Includes the 5x6 grid and keyboard visualization
"""

import pygame

# Colors
COLOR_BG = (18, 18, 19)
COLOR_TILE_EMPTY = (58, 58, 60)
COLOR_TILE_GRAY = (58, 58, 60)
COLOR_TILE_YELLOW = (181, 159, 59)
COLOR_TILE_GREEN = (83, 141, 78)
COLOR_TEXT = (215, 218, 220)
COLOR_KEY_UNUSED = (129, 131, 132)
COLOR_KEY_GRAY = (58, 58, 60)
COLOR_KEY_YELLOW = (181, 159, 59)
COLOR_KEY_GREEN = (83, 141, 78)

# Dimensions
TILE_SIZE = 60
TILE_GAP = 5
KEY_WIDTH = 40
KEY_HEIGHT = 50
KEY_GAP = 5


class GameBoard:
    """Visualizes the 5x6 Wordle grid"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.grid = [['' for _ in range(5)] for _ in range(6)]
        self.colors = [[COLOR_TILE_EMPTY for _ in range(5)] for _ in range(6)]
        
    def update_from_history(self, history, game):
        """Update grid based on game history"""
        from game.wordle_logic import MISS, MISPLACED, EXACT
        
        self.grid = [['' for _ in range(5)] for _ in range(6)]
        self.colors = [[COLOR_TILE_EMPTY for _ in range(5)] for _ in range(6)]
        
        for row_idx, (guess, feedback_int) in enumerate(history):
            feedback = game.decode_feedback(feedback_int)
            for col_idx, (letter, state) in enumerate(zip(guess.upper(), feedback)):
                self.grid[row_idx][col_idx] = letter
                if state == EXACT:
                    self.colors[row_idx][col_idx] = COLOR_TILE_GREEN
                elif state == MISPLACED:
                    self.colors[row_idx][col_idx] = COLOR_TILE_YELLOW
                else:
                    self.colors[row_idx][col_idx] = COLOR_TILE_GRAY
    
    def draw(self, screen, font):
        """Draw the game board"""
        for row in range(6):
            for col in range(5):
                tile_x = self.x + col * (TILE_SIZE + TILE_GAP)
                tile_y = self.y + row * (TILE_SIZE + TILE_GAP)
                
                # Draw tile
                pygame.draw.rect(screen, self.colors[row][col], 
                               (tile_x, tile_y, TILE_SIZE, TILE_SIZE), 
                               border_radius=5)
                pygame.draw.rect(screen, COLOR_TEXT, 
                               (tile_x, tile_y, TILE_SIZE, TILE_SIZE), 
                               2, border_radius=5)
                
                # Draw letter
                if self.grid[row][col]:
                    letter_surface = font.render(self.grid[row][col], True, COLOR_TEXT)
                    letter_rect = letter_surface.get_rect(center=(tile_x + TILE_SIZE // 2, 
                                                                  tile_y + TILE_SIZE // 2))
                    screen.blit(letter_surface, letter_rect)


class KeyboardVisualizer:
    """Visualizes the on-screen keyboard with color feedback"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rows = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        ]
        self.key_states = {}  # letter -> state (0=unused, 1=gray, 2=yellow, 3=green)
        
    def update_from_history(self, history, game):
        """Update keyboard colors based on guess history"""
        from game.wordle_logic import MISS, MISPLACED, EXACT
        
        self.key_states = {}
        
        for guess, feedback_int in history:
            feedback = game.decode_feedback(feedback_int)
            for letter, state in zip(guess.upper(), feedback):
                letter = letter.upper()
                current_state = self.key_states.get(letter, 0)
                # Green > Yellow > Gray
                if state == EXACT:
                    self.key_states[letter] = 3
                elif state == MISPLACED and current_state < 3:
                    self.key_states[letter] = 2
                elif state == MISS and current_state == 0:
                    self.key_states[letter] = 1
    
    def draw(self, screen, font):
        """Draw the keyboard"""
        for row_idx, row in enumerate(self.rows):
            row_width = len(row) * (KEY_WIDTH + KEY_GAP)
            start_x = self.x + (10 * (KEY_WIDTH + KEY_GAP) - row_width) // 2
            
            for col_idx, letter in enumerate(row):
                key_x = start_x + col_idx * (KEY_WIDTH + KEY_GAP)
                key_y = self.y + row_idx * (KEY_HEIGHT + KEY_GAP)
                
                # Determine key color
                state = self.key_states.get(letter, 0)
                if state == 3:
                    color = COLOR_KEY_GREEN
                elif state == 2:
                    color = COLOR_KEY_YELLOW
                elif state == 1:
                    color = COLOR_KEY_GRAY
                else:
                    color = COLOR_KEY_UNUSED
                
                # Draw key
                pygame.draw.rect(screen, color, (key_x, key_y, KEY_WIDTH, KEY_HEIGHT), border_radius=4)
                
                # Draw letter
                letter_surface = font.render(letter, True, COLOR_TEXT)
                letter_rect = letter_surface.get_rect(center=(key_x + KEY_WIDTH // 2, key_y + KEY_HEIGHT // 2))
                screen.blit(letter_surface, letter_rect)
