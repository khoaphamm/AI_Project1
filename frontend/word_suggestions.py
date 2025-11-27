"""
Word Suggestions Panel for Hint Mode
Displays top 5 recommended words for the player to choose from
"""

import pygame

# Colors
COLOR_PANEL = (30, 30, 35)
COLOR_TEXT = (215, 218, 220)
COLOR_SUGGESTION_BG = (50, 50, 55)
COLOR_SUGGESTION_HOVER = (70, 70, 75)
COLOR_SUGGESTION_BEST = (100, 180, 100)


class WordSuggestionsPanel:
    """Displays top word suggestions in Hint mode"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.suggestions = []
        self.hovered_index = -1
        
    def update_suggestions(self, solver):
        """Get top 5 word suggestions from solver"""
        self.suggestions = []
        
        if hasattr(solver, 'currently_consistent_words'):
            # Get up to 5 words from the consistent words
            words = list(solver.currently_consistent_words)[:5]
            self.suggestions = words
    
    def draw(self, screen, font, font_small):
        """Draw the suggestions panel"""
        # Draw panel background
        pygame.draw.rect(screen, COLOR_PANEL, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, COLOR_TEXT, (self.x, self.y, self.width, self.height), 2)
        
        # Title
        title = font.render("Suggested Words", True, COLOR_TEXT)
        screen.blit(title, (self.x + 10, self.y + 10))
        
        subtitle = font_small.render("Click a word to play it", True, COLOR_TEXT)
        screen.blit(subtitle, (self.x + 10, self.y + 45))
        
        # Draw suggestions
        start_y = self.y + 80
        suggestion_height = 60
        spacing = 10
        
        for i, word in enumerate(self.suggestions):
            suggestion_y = start_y + i * (suggestion_height + spacing)
            
            # Determine color
            if i == self.hovered_index:
                color = COLOR_SUGGESTION_HOVER
            elif i == 0:
                color = COLOR_SUGGESTION_BEST  # Best suggestion
            else:
                color = COLOR_SUGGESTION_BG
            
            # Draw suggestion box
            pygame.draw.rect(screen, color, 
                           (self.x + 20, suggestion_y, self.width - 40, suggestion_height),
                           border_radius=8)
            pygame.draw.rect(screen, COLOR_TEXT, 
                           (self.x + 20, suggestion_y, self.width - 40, suggestion_height),
                           2, border_radius=8)
            
            # Draw word
            word_surface = font.render(word.upper(), True, COLOR_TEXT)
            word_rect = word_surface.get_rect(center=(self.x + self.width // 2, 
                                                      suggestion_y + suggestion_height // 2))
            screen.blit(word_surface, word_rect)
            
            # Draw rank
            if i == 0:
                rank_text = font_small.render("BEST", True, COLOR_TEXT)
            else:
                rank_text = font_small.render(f"#{i + 1}", True, COLOR_TEXT)
            screen.blit(rank_text, (self.x + 30, suggestion_y + 5))
        
        # If no suggestions
        if not self.suggestions:
            no_words = font_small.render("No suggestions available", True, COLOR_TEXT)
            screen.blit(no_words, (self.x + self.width // 2 - no_words.get_width() // 2, 
                                  start_y + 50))
    
    def handle_click(self, pos):
        """Check if a suggestion was clicked and return the word"""
        if not self.suggestions:
            return None
        
        start_y = self.y + 80
        suggestion_height = 60
        spacing = 10
        
        for i, word in enumerate(self.suggestions):
            suggestion_y = start_y + i * (suggestion_height + spacing)
            rect = pygame.Rect(self.x + 20, suggestion_y, self.width - 40, suggestion_height)
            
            if rect.collidepoint(pos):
                return word
        
        return None
    
    def handle_hover(self, pos):
        """Update hover state"""
        if not self.suggestions:
            self.hovered_index = -1
            return
        
        start_y = self.y + 80
        suggestion_height = 60
        spacing = 10
        
        self.hovered_index = -1
        for i, word in enumerate(self.suggestions):
            suggestion_y = start_y + i * (suggestion_height + spacing)
            rect = pygame.Rect(self.x + 20, suggestion_y, self.width - 40, suggestion_height)
            
            if rect.collidepoint(pos):
                self.hovered_index = i
                break
