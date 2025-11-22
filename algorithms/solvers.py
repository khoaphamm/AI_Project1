"""
Wordle Solvers using Trie-based Search

The search space is represented as a Trie where:
- Root = empty string ""
- Each level adds one letter (depth 1-5)
- Leaves (depth 5) = complete 5-letter words
- All leaves connect to a virtual GOAL node
- Goal = finding a word consistent with feedback history
"""

from collections import deque
from trie.trie_structure import WordleTrie

class BaseSolver:
    def __init__(self, game):
        self.game = game
        # Build the trie from allowed words
        self.trie = WordleTrie(list(game.allowed_words))
        print(f"Trie built with {self.trie.word_count} words")
        print(f"Trie statistics: {self.trie.get_statistics()}")
        
        # First guess heuristics
        self.first_guess = "crane"  # Common strong opener
        self.search_stats = []

    def pick_guess(self, history):
        """
        Abstract method to be implemented by solvers.
        :param history: List of (guessed_word, feedback_pattern)
        :return: The next string to guess
        """
        raise NotImplementedError


class BFSSolver(BaseSolver):
    """
    Breadth-First Search Solver using Trie structure.
    
    Search Strategy:
    1. Start at root (empty string)
    2. Explore level by level: depth 1, 2, 3, 4, 5
    3. At depth 5 (leaves), check if word is consistent with history
    4. First consistent word found = GOAL reached
    
    Transition: Adding one letter at a time (traverse down trie)
    """
    
    def pick_guess(self, history):
        # First guess optimization
        if not history:
            return self.first_guess

        # Define goal test: word must be consistent with all previous feedback
        def is_goal(word):
            return self.game.is_consistent(word, history)
        
        # Perform BFS on the trie
        path, word, nodes_visited = self.trie.bfs_search(is_goal)
        
        # Track statistics
        self.search_stats.append({
            'method': 'BFS',
            'nodes_visited': nodes_visited,
            'word_found': word
        })
        
        if word:
            print(f"BFS found: {word} (visited {nodes_visited} nodes)")
            return word
        
        # Fallback (should not happen)
        return list(self.game.allowed_words)[0]


class DFSSolver(BaseSolver):
    """
    Depth-First Search Solver using Trie structure.
    
    Search Strategy:
    1. Start at root (empty string)
    2. Dive deep: explore one branch completely before backtracking
    3. Go depth 0->1->2->3->4->5 on each path
    4. At depth 5 (leaves), check if word is consistent with history
    5. Backtrack if not goal, explore next branch
    
    Transition: Adding one letter at a time (traverse down trie)
    """
    
    def pick_guess(self, history):
        # First guess optimization
        if not history:
            return self.first_guess

        # Define goal test: word must be consistent with all previous feedback
        def is_goal(word):
            return self.game.is_consistent(word, history)
        
        # Perform DFS on the trie
        path, word, nodes_visited = self.trie.dfs_search(is_goal)
        
        # Track statistics
        self.search_stats.append({
            'method': 'DFS',
            'nodes_visited': nodes_visited,
            'word_found': word
        })
        
        if word:
            print(f"DFS found: {word} (visited {nodes_visited} nodes)")
            return word
        
        # Fallback (should not happen)
        return list(self.game.allowed_words)[0]


class RecursiveDFSSolver(BaseSolver):
    """
    Recursive Depth-First Search using Trie structure.
    
    Same as DFS but implemented recursively for educational purposes.
    Shows the natural recursive structure of DFS on trees.
    """
    
    def pick_guess(self, history):
        # First guess optimization
        if not history:
            return self.first_guess

        # Define goal test
        def is_goal(word):
            return self.game.is_consistent(word, history)
        
        # Perform recursive DFS
        path, word, nodes_visited = self.trie.dfs_recursive_search(is_goal)
        
        # Track statistics
        self.search_stats.append({
            'method': 'Recursive DFS',
            'nodes_visited': nodes_visited,
            'word_found': word
        })
        
        if word:
            print(f"Recursive DFS found: {word} (visited {nodes_visited} nodes)")
            return word
        
        return list(self.game.allowed_words)[0]