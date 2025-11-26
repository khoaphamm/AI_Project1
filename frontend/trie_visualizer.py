"""
Trie Visualization Components
Handles visualization of the Trie structure
"""

import pygame

# Colors
COLOR_PANEL = (30, 30, 35)
COLOR_TEXT = (215, 218, 220)
COLOR_TRIE_NODE = (100, 100, 255)
COLOR_TRIE_ACTIVE = (255, 100, 100)
COLOR_TRIE_LINE = (150, 150, 150)


class TrieVisualizer:
    """Handles visualization of the Trie structure"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.active_path = []
        self.nodes_to_draw = []
        self.max_depth = 5
        
    def set_active_path(self, path):
        """Set the currently active path in the trie"""
        self.active_path = path if path else []
        
    def set_trie_root_children(self, root_node):
        """Extract first level nodes from trie for visualization"""
        if root_node:
            self.nodes_to_draw = [(char, child) for char, child in sorted(root_node.children.items())]
            # Calculate positions for all nodes
            if self.nodes_to_draw:
                # Calculate spacing based on number of nodes
                available_width = self.width - 40  # Padding
                node_count = min(len(self.nodes_to_draw), 26)
                nodes_per_row = 13
                spacing_x = available_width // nodes_per_row
                
                for i, (char, node) in enumerate(self.nodes_to_draw[:26]):
                    row = i // nodes_per_row
                    col = i % nodes_per_row
                    
                    # Store calculated position in node metadata
                    if not hasattr(node, 'viz_pos'):
                        node.viz_pos = {}
                    node.viz_pos['x'] = self.x + 20 + col * spacing_x
                    node.viz_pos['y'] = self.y + 90 + row * 45
        else:
            self.nodes_to_draw = []

    def calculate_node_positions(self, root_node, start_x=None, start_y=None):
        """Calculate positions for all nodes in the trie"""
        if not root_node or not self.nodes_to_draw:
            return
        
        # Use provided start position or default
        if start_x is None:
            start_x = self.x + self.width // 2
        if start_y is None:
            start_y = self.y + 90
        
        # Calculate spacing
        available_width = self.width - 40
        node_count = min(len(self.nodes_to_draw), 26)
        nodes_per_row = 13
        spacing_x = available_width // nodes_per_row
        spacing_y = 45
        
        # Position first level nodes
        for i, (char, node) in enumerate(self.nodes_to_draw[:26]):
            row = i // nodes_per_row
            col = i % nodes_per_row
            
            node_x = self.x + 20 + col * spacing_x
            node_y = start_y + row * spacing_y
            
            # Store position
            if not hasattr(node, 'viz_pos'):
                node.viz_pos = {}
            node.viz_pos['x'] = node_x
            node.viz_pos['y'] = node_y

    
    
    def draw(self, screen, font):
        """Draw the trie visualization"""
        # Draw panel background
        pygame.draw.rect(screen, COLOR_PANEL, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, COLOR_TEXT, (self.x, self.y, self.width, self.height), 2)
        
        # Title
        title = font.render("Trie Structure", True, COLOR_TEXT)
        screen.blit(title, (self.x + 10, self.y + 10))
        
        # Draw active path
        if self.active_path:
            path_y = self.y + 50
            path_text = "Active Path: ROOT → " + " → ".join(self.active_path[:5])
            if len(self.active_path) > 5:
                path_text += f" → ... ({len(self.active_path)} nodes)"
            
            path_surface = font.render(path_text, True, COLOR_TRIE_ACTIVE)
            screen.blit(path_surface, (self.x + 10, path_y))
        
        # Draw first level nodes using calculated positions
        node_size = 30
        
        for i, (char, node) in enumerate(self.nodes_to_draw[:26]):  # Limit to 26 letters
            # Use pre-calculated position if available
            if hasattr(node, 'viz_pos') and 'x' in node.viz_pos and 'y' in node.viz_pos:
                node_x = node.viz_pos['x']
                node_y = node.viz_pos['y']
            else:
                # Fallback: calculate on-the-fly (shouldn't happen if calculate_node_positions was called)
                nodes_per_row = 13
                row = i // nodes_per_row
                col = i % nodes_per_row
                available_width = self.width - 40
                spacing_x = available_width // nodes_per_row
                node_x = self.x + 20 + col * spacing_x
                node_y = self.y + 90 + row * 45
            
            # Check if this node is in active path
            is_active = len(self.active_path) > 0 and self.active_path[0].lower() == char.lower()
            color = COLOR_TRIE_ACTIVE if is_active else COLOR_TRIE_NODE
            
            # Draw node circle
            pygame.draw.circle(screen, color, (node_x, node_y), node_size // 2)
            pygame.draw.circle(screen, COLOR_TEXT, (node_x, node_y), node_size // 2, 2)
            
            # Draw character
            char_surface = font.render(char.upper(), True, COLOR_TEXT)
            char_rect = char_surface.get_rect(center=(node_x, node_y))
            screen.blit(char_surface, char_rect)


class InfoPanel:
    """Displays algorithm information"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def draw(self, screen, font, logger):
        """Draw the info panel"""
        # Draw panel background
        pygame.draw.rect(screen, COLOR_PANEL, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, COLOR_TEXT, (self.x, self.y, self.width, self.height), 2)
        
        # Title
        title = font.render("Algorithm Info", True, COLOR_TEXT)
        screen.blit(title, (self.x + 10, self.y + 10))
        
        y_offset = self.y + 50
        
        # Display info
        info_lines = [
            f"Current Word: {logger.current_word.upper()}",
            f"Candidates: {logger.candidates_count}",
            f"Nodes Visited: {logger.nodes_visited}",
            f"Entropy: {logger.current_entropy:.2f}" if logger.current_entropy > 0 else "Entropy: N/A"
        ]
        
        for line in info_lines:
            text_surface = font.render(line, True, COLOR_TEXT)
            screen.blit(text_surface, (self.x + 10, y_offset))
            y_offset += 30


class LogPanel:
    """Displays algorithm execution logs"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def draw(self, screen, font_small, logger):
        """Draw the log panel"""
        # Draw panel background
        pygame.draw.rect(screen, COLOR_PANEL, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, COLOR_TEXT, (self.x, self.y, self.width, self.height), 2)
        
        # Title
        title = font_small.render("Execution Log", True, COLOR_TEXT)
        screen.blit(title, (self.x + 10, self.y + 10))
        
        # Display logs
        y_offset = self.y + 40
        for log in logger.logs:
            log_surface = font_small.render(log, True, COLOR_TEXT)
            screen.blit(log_surface, (self.x + 10, y_offset))
            y_offset += 25
            if y_offset > self.y + self.height - 30:
                break
