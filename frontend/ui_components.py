"""
UI Components for Wordle Visualizer
Shared UI elements like buttons
"""

import pygame

# Colors
COLOR_TEXT = (215, 218, 220)
COLOR_BUTTON_BG = (70, 70, 75)
COLOR_BUTTON_HOVER = (90, 90, 95)
COLOR_BUTTON_ACTIVE = (100, 180, 100)


class Button:
    """Simple button class"""
    def __init__(self, x, y, width, height, text, active=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.active = active
        self.hovered = False
        
    def draw(self, screen, font):
        """Draw the button"""
        if self.active:
            color = COLOR_BUTTON_ACTIVE
        elif self.hovered:
            color = COLOR_BUTTON_HOVER
        else:
            color = COLOR_BUTTON_BG
            
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, COLOR_TEXT, self.rect, 2, border_radius=5)
        
        text_surface = font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        """Handle mouse events"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class VisualizationLogger:
    """Tracks algorithm operations for display"""
    def __init__(self, max_logs=15):
        from collections import deque
        import time
        self.logs = deque(maxlen=max_logs)
        self.current_entropy = 0.0
        self.candidates_count = 0
        self.current_word = ""
        self.nodes_visited = 0
        self.time = time
        
    def add_log(self, message):
        """Add a log message"""
        self.logs.append(f"[{self.time.strftime('%H:%M:%S')}] {message}")
    
    def clear(self):
        """Clear all logs"""
        self.logs.clear()
        self.current_entropy = 0.0
        self.candidates_count = 0
        self.current_word = ""
        self.nodes_visited = 0
