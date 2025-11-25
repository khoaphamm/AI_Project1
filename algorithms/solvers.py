"""
Wordle Solvers using Trie-based Search

The search space is represented as a Trie where:
- Root = empty string ""
- Each level adds one letter (depth 1-5)
- Leaves (depth 5) = complete 5-letter words
- All leaves connect to a virtual GOAL node
- Goal = finding a word consistent with feedback history
"""

from collections import deque, defaultdict
from trie.trie_structure import WordleTrie

class BaseSolver:
    def __init__(self, game):
        self.game = game
        # The solver's search space is the full set of allowed words.
        # This set is pruned at each step based on feedback.
        self.currently_consistent_words = set(game.allowed_words)
        self.trie = None  # Trie will be built on the first guess
        
        # First guess heuristics
        self.first_guess = "crane"  # Common strong opener
        self.search_stats = []

    def _update_trie(self, history):
        """
        Filters the list of consistent words based on history and rebuilds the Trie.
        """
        if not history:
            # On the first turn, the trie contains all allowed words
            self.trie = WordleTrie(list(self.currently_consistent_words))
        else:
            # Filter words based on the last guess and rebuild
            last_guess, last_feedback = history[-1]
            
            # The solver checks consistency against its own (large) list of words
            self.currently_consistent_words = {
                word for word in self.currently_consistent_words
                if self.game.evaluate_guess(last_guess, secret_word=word) == last_feedback
            }
            self.trie = WordleTrie(list(self.currently_consistent_words))

        print(f"Trie updated. Valid words remaining: {len(self.currently_consistent_words)}")
        if len(self.currently_consistent_words) <= 10:
            print(f"Remaining words: {list(self.currently_consistent_words)}")
        print(f"Trie statistics: {self.trie.get_statistics()}")


    def pick_guess(self, history):
        """
        Abstract method to be implemented by solvers.
        :param history: List of (guessed_word, feedback_pattern)
        :return: The next string to guess
        """
        raise NotImplementedError


class DFSSolver(BaseSolver):
    """
    Depth-First Search Solver using an incrementally pruned Trie structure.
    """
    def pick_guess(self, history):
        # if not history:
        #     return self.first_guess

        self._update_trie(history)
        
        path, word, nodes_visited = self.trie.dfs_search()
        
        self.search_stats.append({
            'method': 'DFS',
            'nodes_visited': nodes_visited,
            'word_found': word
        })
        
        if word:
            print(f"DFS found: {word} (visited {nodes_visited} nodes in pruned trie)")
            return word
        
        return list(self.currently_consistent_words)[0] if self.currently_consistent_words else "error"

class HillClimbingSolver(BaseSolver):
    """
    Hill Climbing Solver using a character-position frequency heuristic.
    The heuristic is fairly calculated only from the general allowed_words list.
    """
    def __init__(self, game):
        super().__init__(game)
        self.heuristic_matrix = self._calculate_heuristic()

    def _calculate_heuristic(self):
        """
        Calculates the frequency of each character at each position based on
        the full set of allowed guessable words.
        :return: A list of dictionaries, where list index = position and
                 the dict maps a character to its frequency at that position.
        """
        freq_matrix = [defaultdict(int) for _ in range(5)]
        
        # Heuristic is built from the general 'allowed_words' to be fair.
        for word in self.game.allowed_words:
            for i, char in enumerate(word):
                freq_matrix[i][char] += 1
        
        print("Hill Climbing heuristic matrix calculated (from allowed_words).")
        return freq_matrix

    def pick_guess(self, history):
        # if not history:
        #     return self.first_guess

        # Prune the word list and rebuild the Trie with currently valid words
        self._update_trie(history)

        current_node = self.trie.root
        guess_word = ""
        nodes_visited = 1

        for i in range(5):
            possible_next_chars = list(current_node.children.keys())
            
            if not possible_next_chars:
                return list(self.currently_consistent_words)[0] if self.currently_consistent_words else "error"

            # Greedily choose the best next character based on the heuristic
            best_char = max(
                possible_next_chars, 
                key=lambda char: self.heuristic_matrix[i].get(char, 0)
            )
            
            guess_word += best_char
            current_node = current_node.children[best_char]
            nodes_visited += 1

        self.search_stats.append({
            'method': 'HillClimbing',
            'nodes_visited': nodes_visited,
            'word_found': guess_word
        })
        
        print(f"Hill Climbing built word: {guess_word} (traversed {nodes_visited} nodes)")
        return guess_word