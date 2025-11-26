"""
Menu System for Wordle Visualizer
Popup menu for selecting algorithm and mode
"""

import pygame
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms.solvers import DFSSolver, HillClimbingSolver
from frontend.ui_components import Button

# Colors
COLOR_PANEL = (30, 30, 35)
COLOR_TEXT = (215, 218, 220)


class MenuPopup:
    """Popup menu for selecting algorithm and mode"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 400
        self.height = 380
        self.visible = False
        
        # Menu options
        self.options = [
            {"text": "DFS - Auto Play", "solver": DFSSolver, "auto": True},
            {"text": "DFS - Hint Only", "solver": DFSSolver, "auto": False},
            {"text": "Hill Climb - Auto", "solver": HillClimbingSolver, "auto": True},
            {"text": "Hill Climb - Hint", "solver": HillClimbingSolver, "auto": False},
        ]
        
        # Create buttons
        button_width = 360
        button_height = 60
        start_y = y + 80
        spacing = 70
        
        self.buttons = []
        for i, option in enumerate(self.options):
            btn_x = x + 20
            btn_y = start_y + i * spacing
            btn = Button(btn_x, btn_y, button_width, button_height, option["text"])
            self.buttons.append(btn)
    
    def toggle(self):
        """Toggle menu visibility"""
        self.visible = not self.visible
    
    def handle_event(self, event):
        """Handle events and return selected option or None"""
        if not self.visible:
            return None
        
        for i, btn in enumerate(self.buttons):
            if btn.handle_event(event):
                self.visible = False
                return self.options[i]
        
        return None
    
    def draw(self, screen, font, font_small, window_width, window_height):
        """Draw the popup menu"""
        if not self.visible:
            return
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((window_width, window_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Draw menu background
        pygame.draw.rect(screen, COLOR_PANEL, (self.x, self.y, self.width, self.height), border_radius=10)
        pygame.draw.rect(screen, COLOR_TEXT, (self.x, self.y, self.width, self.height), 3, border_radius=10)
        
        # Title
        title = font.render("Select Mode", True, COLOR_TEXT)
        screen.blit(title, (self.x + self.width // 2 - title.get_width() // 2, self.y + 20))
        
        # Draw buttons
        for btn in self.buttons:
            btn.draw(screen, font_small)
        
        # Close instruction
        close_text = font_small.render("Click outside to close", True, COLOR_TEXT)
        screen.blit(close_text, (self.x + self.width // 2 - close_text.get_width() // 2, self.y + self.height - 30))
