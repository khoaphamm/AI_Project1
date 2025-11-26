"""
Wordle AI Visualization with Pygame
Main visualizer - displays game board, keyboard, trie structure, and algorithm progress
"""

import pygame
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.wordle_logic import WordleGame, MISS, MISPLACED, EXACT
from algorithms.solvers import DFSSolver, HillClimbingSolver
from frontend.ui_components import Button, VisualizationLogger
from frontend.game_board import GameBoard, KeyboardVisualizer
from frontend.trie_visualizer import TrieVisualizer, InfoPanel
from frontend.menu import MenuPopup
from frontend.word_suggestions import WordSuggestionsPanel

# Colors
COLOR_BG = (18, 18, 19)
COLOR_TEXT = (215, 218, 220)
COLOR_TILE_GREEN = (83, 141, 78)
COLOR_TILE_GRAY = (58, 58, 60)

# Dimensions
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800


class WordleVisualizer:
    """Main visualizer class"""
    def __init__(self, game=None, solver_class=DFSSolver, auto_play=True):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Wordle AI Visualizer")
        
        self.font_large = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 20)
        
        self.game = game if game else WordleGame()
        self.solver_class = solver_class
        self.solver = solver_class(self.game)
        self.auto_play = auto_play
        self.game_started = False  # Track if game has been started
        
        # Logger for visualization
        self.logger = VisualizationLogger()
        
        # Connect solver logging to visualizer
        self.solver.log_callback = self.logger.add_log
        
        # UI Components
        self.board = GameBoard(50, 80)
        self.keyboard = KeyboardVisualizer(50, 500)
        self.trie_viz = TrieVisualizer(700, 80, 650, 400)
        self.word_suggestions = WordSuggestionsPanel(700, 80, 650, 680)
        self.info_panel = InfoPanel(700, 500, 650, 260)
        
        # Buttons
        self.btn_menu = Button(10, 10, 100, 40, "Menu")
        self.btn_pause = Button(50, 700, 150, 50, "Pause", active=False)
        self.btn_next = Button(220, 700, 150, 50, "Next Step")
        self.btn_restart = Button(390, 700, 150, 50, "Restart")
        
        # Menu popup
        self.menu_popup = MenuPopup(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 - 190)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.step_mode = not auto_play
        self.waiting_for_step = False
        self.paused = False  # Track pause state
        
    def run(self):
        """Main visualization loop"""
        self.logger.add_log(f"Welcome to Wordle AI Visualizer")
        self.logger.add_log(f"Click Menu to select algorithm and mode")
        
        last_auto_time = time.time()
        auto_delay = 2.0  # seconds between auto moves
        
        while self.running:
            self.handle_events()
            
            # Auto play logic (only if game has started and not paused)
            if self.game_started and not self.game.game_over and not self.step_mode and not self.paused:
                if time.time() - last_auto_time > auto_delay:
                    self.make_ai_move()
                    last_auto_time = time.time()
            
            # Step mode logic
            if not self.game.game_over and self.step_mode and self.waiting_for_step:
                self.waiting_for_step = False
            
            self.draw()
            self.clock.tick(30)
        
        pygame.quit()
        
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Check if clicking outside menu to close it
            if event.type == pygame.MOUSEBUTTONDOWN and self.menu_popup.visible:
                mx, my = event.pos
                menu_rect = pygame.Rect(self.menu_popup.x, self.menu_popup.y, 
                                       self.menu_popup.width, self.menu_popup.height)
                if not menu_rect.collidepoint(mx, my):
                    self.menu_popup.visible = False
                    continue
            
            # Menu popup handling
            selected = self.menu_popup.handle_event(event)
            if selected:
                self.reset_game(selected["solver"], selected["auto"])
                self.game_started = True  # Mark game as started
                continue
                
            # Menu button
            if self.btn_menu.handle_event(event):
                self.menu_popup.toggle()
                
            # Button handling (only when menu is not visible)
            if not self.menu_popup.visible:
                # Pause button
                if self.btn_pause.handle_event(event):
                    if not self.game_started:
                        self.logger.add_log("Please select a mode from Menu first")
                    else:
                        self.paused = not self.paused
                        self.btn_pause.active = self.paused
                        if self.paused:
                            self.logger.add_log("Game paused")
                        else:
                            self.logger.add_log("Game resumed")
                
                # Next Step button
                if self.btn_next.handle_event(event):
                    if not self.game_started:
                        self.logger.add_log("Please select a mode from Menu first")
                    elif not self.game.game_over:
                        self.make_ai_move()
                
                # Restart button
                if self.btn_restart.handle_event(event):
                    if not self.game_started:
                        self.logger.add_log("Please select a mode from Menu first")
                    else:
                        # Create new game with same solver and mode
                        self.game = WordleGame()
                        self.solver = self.solver_class(self.game)
                        self.solver.log_callback = self.logger.add_log
                        self.paused = False
                        self.btn_pause.active = False
                        
                        # Update suggestions if in hint mode
                        if self.step_mode:
                            self.word_suggestions.update_suggestions(self.solver)
                        
                        self.logger.clear()
                        self.logger.add_log("Game restarted with new word")
                        self.logger.add_log(f"Solver: {self.solver_class.__name__}")
                        self.logger.add_log(f"Mode: {'Hint Only' if self.step_mode else 'Auto Play'}")
                
                # Handle word suggestion clicks in hint mode
                if event.type == pygame.MOUSEBUTTONDOWN and self.step_mode and self.game_started:
                    clicked_word = self.word_suggestions.handle_click(event.pos)
                    if clicked_word:
                        self.logger.add_log(f"Player selected: {clicked_word.upper()}")
                        success, result = self.game.make_guess(clicked_word)
                        if success:
                            feedback = self.game.decode_feedback(result)
                            feedback_str = ''.join(['🟩' if f == EXACT else '🟨' if f == MISPLACED else '⬜' for f in feedback])
                            self.logger.add_log(f"Feedback: {feedback_str}")
                            
                            # Update solver with the new guess
                            self.solver._update_trie(self.game.attempts)
                            
                            # Update suggestions after guess
                            self.word_suggestions.update_suggestions(self.solver)
                            
                            if self.game.won:
                                self.logger.add_log(f"✓ Won in {len(self.game.attempts)} attempts!")
                            elif self.game.game_over:
                                self.logger.add_log(f"✗ Failed. Word was: {self.game.secret_word.upper()}")
                            else:
                                self.logger.add_log(f"Updated suggestions. {len(self.solver.currently_consistent_words)} words remaining")
                
                # Handle hover for suggestions
                if event.type == pygame.MOUSEMOTION and self.step_mode and self.game_started:
                    self.word_suggestions.handle_hover(event.pos)
    
    def reset_game(self, solver_class, auto_play):
        """Reset the game with new solver and mode"""
        self.game = WordleGame()
        self.solver_class = solver_class
        self.solver = solver_class(self.game)
        self.solver.log_callback = self.logger.add_log
        self.auto_play = auto_play
        self.step_mode = not auto_play
        
        # Update button states
        self.paused = False
        self.btn_pause.active = False
        
        # Update suggestions if in hint mode
        if not auto_play:
            self.word_suggestions.update_suggestions(self.solver)
        
        # Clear logger
        self.logger.clear()
        self.logger.add_log(f"New game started")
        self.logger.add_log(f"Solver: {solver_class.__name__}")
        self.logger.add_log(f"Mode: {'Auto Play' if auto_play else 'Hint Only'}")
    
    def make_ai_move(self):
        """Execute one AI move"""
        self.logger.add_log("AI thinking...")
        
        # Get AI guess
        guess = self.solver.pick_guess(self.game.attempts)
        
        # Update logger with solver info
        if hasattr(self.solver, 'currently_consistent_words'):
            self.logger.candidates_count = len(self.solver.currently_consistent_words)
        
        if hasattr(self.solver, 'search_stats') and self.solver.search_stats:
            last_stat = self.solver.search_stats[-1]
            self.logger.nodes_visited = last_stat.get('nodes_visited', 0)
        
        self.logger.current_word = guess
        self.logger.add_log(f"AI guesses: {guess.upper()}")
        
        # Update trie visualization
        if hasattr(self.solver, 'trie') and self.solver.trie:
            self.trie_viz.set_trie_root_children(self.solver.trie.root)
            self.trie_viz.calculate_node_positions(self.solver.trie.root)
            # Show active path as the guessed word
            self.trie_viz.set_active_path(list(guess.upper()))
        
        # Update suggestions if in hint mode
        if self.step_mode:
            self.word_suggestions.update_suggestions(self.solver)
        
        # Make the guess
        success, result = self.game.make_guess(guess)
        
        if success:
            feedback = self.game.decode_feedback(result)
            feedback_str = ''.join(['🟩' if f == EXACT else '🟨' if f == MISPLACED else '⬜' for f in feedback])
            self.logger.add_log(f"Feedback: {feedback_str}")
            
            if self.game.won:
                self.logger.add_log(f"✓ Won in {len(self.game.attempts)} attempts!")
            elif self.game.game_over:
                self.logger.add_log(f"✗ Failed. Word was: {self.game.secret_word.upper()}")
        else:
            self.logger.add_log(f"Error: Invalid guess")
    
    def draw(self):
        """Draw all UI components"""
        self.screen.fill(COLOR_BG)
        
        # Title
        title = self.font_large.render("WORDLE AI VISUALIZER", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Update components from game state
        self.board.update_from_history(self.game.attempts, self.game)
        self.keyboard.update_from_history(self.game.attempts, self.game)
        
        # Draw all components
        self.board.draw(self.screen, self.font)
        self.keyboard.draw(self.screen, self.font)
        
        # Draw right side based on mode
        if self.step_mode:
            # Hint mode - show word suggestions
            self.word_suggestions.draw(self.screen, self.font, self.font_small)
        else:
            # Auto mode - show trie and info
            self.trie_viz.draw(self.screen, self.font_small)
            self.info_panel.draw(self.screen, self.font_small, self.logger)
        
        # Draw buttons
        self.btn_menu.draw(self.screen, self.font_small)
        self.btn_pause.draw(self.screen, self.font_small)
        self.btn_next.draw(self.screen, self.font_small)
        self.btn_restart.draw(self.screen, self.font_small)
        
        # Draw game status
        if self.game.game_over:
            status_text = f"Game Over - {'Won' if self.game.won else 'Lost'} in {len(self.game.attempts)} attempts"
            status_color = COLOR_TILE_GREEN if self.game.won else COLOR_TILE_GRAY
            status_surface = self.font.render(status_text, True, status_color)
            self.screen.blit(status_surface, (50, 650))
        
        # Draw menu popup (on top of everything)
        self.menu_popup.draw(self.screen, self.font, self.font_small, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        pygame.display.flip()

def main():
    """Main entry point - starts with paused state"""
    # Start with default settings but don't auto-run
    game = WordleGame()
    viz = WordleVisualizer(game, DFSSolver, auto_play=False)
    viz.run()

if __name__ == "__main__":
    main()
