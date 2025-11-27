"""
Wordle Solvers using Trie-based Search

The search space is represented as a Trie where:
- Root = empty string ""
- Each level adds one letter (depth 1-5)
- Leaves (depth 5) = complete 5-letter words
- All leaves connect to a virtual GOAL node
- Goal = finding a word consistent with feedback history
"""

from collections import Counter, deque, defaultdict
import math
import numpy as np
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
    
    def _update_currently_consistent_words(self, history):
        """
        Updates the set of currently consistent words based on the feedback history.
        :param history: List of (guessed_word, feedback_pattern)
        """
        if not history:
            self.currently_consistent_words = set(self.game.allowed_words)
            return
        
        for guessed_word, feedback in history:
            self.currently_consistent_words = {
                word for word in self.currently_consistent_words
                if self.game.evaluate_guess(guessed_word, secret_word=word) == feedback
            }

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
    
class EntropySolver(BaseSolver):
    """
    Entropy-Based Solver (3Blue1Brown Logic).
    Strategy: Guess the word that provides the highest Expected Information (Entropy).
    Formula: E[I] = Sum( -p(pattern) * log2(p(pattern)) )
    """
    def __init__(self, game):
        super().__init__(game)
        self.first_guess = "tares" # 3b1b favorite
        self.already_used = set()

    def calculate_entropy(self, guess_word, candidates):
        """
        Calculates E[I] for a given guess word against the list of possible secrets (candidates).
        """
        counts = Counter()
        
        # 1. Simulate the guess against all remaining candidates to get feedback patterns
        for secret in candidates:
            # evaluate_guess returns a tuple like (0, 2, 1, 0, 0)
            # We use this tuple as the key in our Counter
            pattern = self.game.evaluate_guess(guess_word, secret_word=secret)
            counts[pattern] += 1
            
        entropy = 0.0
        num_candidates = len(candidates)
        
        # 2. Calculate Shannon Entropy over the distribution of patterns
        for count in counts.values():
            if count > 0:
                p = count / num_candidates
                entropy += p * -math.log2(p)
                
        return entropy

    def pick_guess(self, history):
        if not history:
            return self.first_guess
        
        # 1. Update our list of possible answers (candidates)
        self._update_currently_consistent_words(history)
        
        candidates = list(self.currently_consistent_words)
        if not candidates:
            return "error"
        
        # If we have narrowed it down to 1 option, just guess it.
        if len(candidates) == 1:
            return candidates[0]

        best_entropy = -1.0
        best_word = None

        
        # Deterministic iteration order: sort the allowed words
        search_space = sorted(self.game.allowed_words)

        print(f"EntropySolver: Calculating entropy for {len(search_space)} words against {len(candidates)} candidates...")

        for word in search_space:
            if word in self.already_used:
                continue
            
            entropy = self.calculate_entropy(word, candidates)
            
            if entropy > best_entropy:
                best_entropy = entropy
                best_word = word
            
            # Tie-breaker: If entropy is effectively equal, prefer words that are 
            # actually possible answers (Greedy choice)
            elif abs(entropy - best_entropy) < 1e-9:
                if best_word not in self.currently_consistent_words and word in self.currently_consistent_words:
                    best_word = word
        
        if best_word:
            self.already_used.add(best_word)
            print(f"EntropySolver: Best guess '{best_word}' with entropy {best_entropy:.4f} bits")
            return best_word
            
        return candidates[0]

 

        

class KnowledgeBasedHillClimbingSolver(BaseSolver):
    """
    Knowledge-Based Hill Climbing Solver.
    
    Difference from Standard Hill Climbing:
    - Standard: Calculates heuristic ONCE based on the full dictionary (D_a).
    - Knowledge-Based: Recalculates the heuristic at EACH step based only on 
      the remaining possible words (S_t).
      
    This allows the greedy search to adapt its probability distribution 
    to the specific subset of words remaining.
    """
    
    def _calculate_dynamic_heuristic(self, words):
        """
        Calculates character frequency at each position for the provided
        subset of words.
        """
        freq_matrix = [defaultdict(int) for _ in range(5)]
        
        for word in words:
            for i, char in enumerate(word):
                freq_matrix[i][char] += 1
        
        return freq_matrix

    def pick_guess(self, history):
        # 1. Prune the search space and rebuild Trie based on history
        self._update_trie(history)

        # 2. DYNAMIC HEURISTIC: Build matrix from only the remaining valid words
        #    (This represents the "Knowledge" gained so far)
        dynamic_matrix = self._calculate_dynamic_heuristic(self.currently_consistent_words)
        
        current_node = self.trie.root
        guess_word = ""
        nodes_visited = 1

        # 3. Greedy Traversal
        for i in range(5):
            possible_next_chars = list(current_node.children.keys())
            
            if not possible_next_chars:
                return list(self.currently_consistent_words)[0] if self.currently_consistent_words else "error"

            # Choose best char based on the NEW dynamic matrix
            best_char = max(
                possible_next_chars, 
                key=lambda char: dynamic_matrix[i].get(char, 0)
            )
            
            guess_word += best_char
            current_node = current_node.children[best_char]
            nodes_visited += 1

        self.search_stats.append({
            'method': 'KnowledgeBasedHillClimbing',
            'nodes_visited': nodes_visited,
            'word_found': guess_word
        })
        
        print(f"KB-Hill Climbing built word: {guess_word} (traversed {nodes_visited} nodes)")
        return guess_word
