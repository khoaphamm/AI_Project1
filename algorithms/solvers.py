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
import random
import os
import json
import numpy as np
from scipy.stats import entropy as scipy_entropy
from trie.trie_structure import WordleTrie
from data import paths

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

    def reset(self):
        """
        Reset solver state for a new game without recreating the solver.
        Subclasses should override this to reset any additional state.
        """
        self.currently_consistent_words = set(self.game.allowed_words)
        self.trie = None
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

    def get_all_suggestions(self):
        """
        Get all currently consistent words as suggestions.
        Returns a list of tuples (word, score).
        """
        # Return consistent words sorted alphabetically with neutral score
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
    
    def get_all_suggestions(self):
        suggestions = sorted(list(self.currently_consistent_words))[:100]
        return [(word, 0.0) for word in suggestions]

class HillClimbingSolver(BaseSolver):
    """
    Hill Climbing Solver using a character-position frequency heuristic.
    The heuristic is fairly calculated only from the general allowed_words list.
    """
    def __init__(self, game):
        super().__init__(game)
        self.heuristic_matrix = self._calculate_heuristic()

    def get_all_suggestions(self):
        """
        Get all currently consistent words as suggestions with heuristic scores.
        Returns a list of tuples (word, score) sorted by score descending.
        """
        if not self.currently_consistent_words:
            return []
        
        # Calculate score for each word based on character frequency heuristic
        word_scores = []
        for word in self.currently_consistent_words:
            score = sum(self.heuristic_matrix[i].get(char, 0) for i, char in enumerate(word))
            word_scores.append((word, score))
        
        # Sort by score descending, limit to top 100
        word_scores.sort(key=lambda x: x[1], reverse=True)
        return word_scores[:100]

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
    Optimized Entropy-Based Solver (3Blue1Brown Logic).
    Uses NumPy vectorization for ~100x speedup over naive implementation.
    
    FAIR VERSION: Uses full symmetric matrix (allowed_words x allowed_words).
    The solver does NOT know which words are "possible answers" - it treats
    all allowed words equally as potential secrets. This is the non-cheating approach.
    
    Strategy: Guess the word that provides the highest Expected Information (Entropy).
    Formula: E[I] = Sum( -p(pattern) * log2(p(pattern)) )
    
    MEMORY EFFICIENT: Reuses the pattern matrix from WordleGame instead of loading its own copy.
    """
    
    def __init__(self, game):
        super().__init__(game)
        self.first_guess = "tares"  # 3b1b favorite
        self.already_used = set()
        self.suggestions = []
        
        # Verify the game has the pattern matrix loaded
        if game._pattern_matrix is None:
            raise RuntimeError(
                "WordleGame does not have pattern matrix loaded.\n"
                "Run: python data/generate_full_matrix.py to create it."
            )
    
    @property
    def _pattern_matrix(self):
        """Reuse pattern matrix from WordleGame."""
        return self.game._pattern_matrix
    
    @property
    def _word_to_idx(self):
        """Reuse word-to-index mapping from WordleGame."""
        return self.game._word_to_idx
    
    @property
    def _word_list(self):
        """Reuse word list from WordleGame."""
        return self.game._word_list
    
    def _idx_to_word(self, idx):
        """Convert index to word using game's word list."""
        return self._word_list[idx]

    def reset(self):
        """Reset solver state for a new game."""
        super().reset()
        self.already_used = set()
        self.suggestions = []

    def _get_entropies_vectorized(self, candidate_indices):
        """
        Calculate entropy for ALL guess words against the given candidates.
        Uses vectorized NumPy operations for massive speedup.
        
        Matrix layout: pattern_matrix[guess_idx, secret_idx] = pattern
        So pattern_matrix[:, candidate_indices] gives patterns for all guesses against candidates.
        
        Returns: numpy array of entropies for each guess word
        """
        n_candidates = len(candidate_indices)
        n_words = self._pattern_matrix.shape[0]
        
        if n_candidates == 0:
            return np.zeros(n_words)
        
        # Get patterns for all guesses against candidates: shape (n_words, n_candidates)
        # pattern_matrix[i, j] = pattern when word[i] is guessed and word[j] is secret
        sub_matrix = self._pattern_matrix[:, candidate_indices]
        
        # Count pattern occurrences for each guess (vectorized)
        # We have 243 possible patterns (3^5)
        distributions = np.zeros((n_words, 243), dtype=np.float64)
        
        # Use numpy's advanced indexing to count patterns
        for j in range(n_candidates):
            patterns = sub_matrix[:, j]  # Pattern for each guess against this candidate
            np.add.at(distributions, (np.arange(n_words), patterns), 1)
        
        # Normalize to get probabilities
        distributions /= n_candidates
        
        # Calculate entropy using scipy (vectorized, handles zeros automatically)
        entropies = scipy_entropy(distributions, base=2, axis=1)
        
        return entropies

    def calculate_entropy(self, guess_word, candidates):
        """
        Calculates E[I] for a single guess word against candidates.
        (Kept for backward compatibility, but prefer vectorized version)
        """
        if guess_word not in self._word_to_idx:
            # Fallback to slow method if word not in matrix
            return self._calculate_entropy_slow(guess_word, candidates)
        
        guess_idx = self._word_to_idx[guess_word]
        candidate_indices = [self._word_to_idx[c] for c in candidates if c in self._word_to_idx]
        
        if not candidate_indices:
            return 0.0
        
        # Get patterns for this guess against all candidates
        # pattern_matrix[guess_idx, candidate_indices]
        patterns = self._pattern_matrix[guess_idx, candidate_indices]
        
        # Count pattern occurrences
        counts = np.bincount(patterns, minlength=243)
        
        # Calculate entropy
        probs = counts / len(candidate_indices)
        probs = probs[probs > 0]  # Remove zeros
        
        return -np.sum(probs * np.log2(probs))
    
    def _calculate_entropy_slow(self, guess_word, candidates):
        """Fallback slow entropy calculation for words not in matrix."""
        counts = Counter()
        for secret in candidates:
            pattern = self.game.evaluate_guess(guess_word, secret_word=secret)
            counts[pattern] += 1
        
        entropy = 0.0
        num_candidates = len(candidates)
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

        # Get candidate indices for vectorized computation
        candidate_indices = np.array([
            self._word_to_idx[c] for c in candidates if c in self._word_to_idx
        ])
        
        print(f"EntropySolver: Calculating entropy for all words against {len(candidates)} candidates (vectorized)...")
        
        # Calculate entropy for ALL guesses at once (vectorized)
        all_entropies = self._get_entropies_vectorized(candidate_indices)
        
        # Find the best guess
        # First, mask out already used words
        for word in self.already_used:
            if word in self._word_to_idx:
                all_entropies[self._word_to_idx[word]] = -1
        
        # Get the index of max entropy
        best_idx = np.argmax(all_entropies)
        best_entropy = all_entropies[best_idx]
        best_word = self._idx_to_word(best_idx)
        
        # Tie-breaker: If multiple words have same entropy, prefer candidates (possible answers)
        tied_indices = np.where(np.abs(all_entropies - best_entropy) < 1e-9)[0]
        if len(tied_indices) > 1:
            for idx in tied_indices:
                word = self._idx_to_word(idx)
                if word in self.currently_consistent_words:
                    best_word = word
                    break
        
        self.already_used.add(best_word)
        print(f"EntropySolver: Best guess '{best_word}' with entropy {best_entropy:.4f} bits")
        return best_word
    
    def get_all_suggestions(self):
        """
        Get all word suggestions with their entropy scores.
        Returns a list of tuples (word, entropy) sorted by entropy descending.
        """
        if self.currently_consistent_words == set(self.game.allowed_words):
            return [("tares", 6.1), ("lares", 6.1), ("rales", 6.1), ("rates", 6.1), ("teras", 6.0)]
        
        candidates = list(self.currently_consistent_words)
        
        # If only one candidate remains, return it
        if len(candidates) == 1:
            return [(candidates[0], 0.0)]
        
        # Get candidate indices
        candidate_indices = np.array([
            self._word_to_idx[c] for c in candidates if c in self._word_to_idx
        ])
        
        # Calculate entropy for ALL words at once (vectorized)
        all_entropies = self._get_entropies_vectorized(candidate_indices)
        
        # Create list of (word, entropy) tuples
        word_scores = []
        for idx, entropy_val in enumerate(all_entropies):
            word = self._idx_to_word(idx)
            if word not in self.already_used:
                word_scores.append((word, float(entropy_val)))
        
        # Sort by entropy descending, limit to top 100
        word_scores.sort(key=lambda x: x[1], reverse=True)
        return word_scores[:100]


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
    def get_all_suggestions(self):
        """
        Get suggestions for the Knowledge-Based Hill Climbing solver.
        Recalculates the dynamic heuristic from `self.currently_consistent_words`
        and scores each word accordingly. Returns a list of tuples
        (word, score) sorted by score descending (top 100).
        """
        # If no pruning has occurred yet, default to empty or allowed words
        if not self.currently_consistent_words:
            return []

        dynamic_matrix = self._calculate_dynamic_heuristic(self.currently_consistent_words)

        word_scores = []
        for word in self.currently_consistent_words:
            score = sum(dynamic_matrix[i].get(char, 0) for i, char in enumerate(word))
            word_scores.append((word, score))

        word_scores.sort(key=lambda x: x[1], reverse=True)
        return word_scores[:100]

class ProgressiveEntropySolver(BaseSolver):
    """
    Progressive Entropy Sampling Solver with Caching & Best-in-Cache Check.
    
    MEMORY EFFICIENT: Reuses the pattern matrix from WordleGame for fast entropy calculation.
    """
    
    def __init__(self, game, samples_per_node=100):
        super().__init__(game)
        self.sample_size = samples_per_node
        self.first_guess = "tares" # 3b1b favorite
        self._turn_entropy_cache = {} # Maps word -> entropy
        self._candidate_indices = None  # Cached candidate indices for current turn

    def reset(self):
        """Reset solver state for a new game."""
        super().reset()
        self._turn_entropy_cache = {}
        self._candidate_indices = None

    @property
    def _pattern_matrix(self):
        """Reuse pattern matrix from WordleGame."""
        return self.game._pattern_matrix
    
    @property
    def _word_to_idx(self):
        """Reuse word-to-index mapping from WordleGame."""
        return self.game._word_to_idx

    def calculate_entropy(self, guess_word, candidates):
        """
        Calculates E[I] with caching.
        Uses vectorized NumPy lookup when pattern matrix is available.
        """
        if guess_word in self._turn_entropy_cache:
            return self._turn_entropy_cache[guess_word]

        num_candidates = len(candidates)
        if num_candidates == 0:
            return 0.0

        # Try vectorized calculation using game's pattern matrix
        if (self._pattern_matrix is not None and 
            guess_word in self._word_to_idx):
            
            guess_idx = self._word_to_idx[guess_word]
            
            # Build candidate indices if not cached
            if self._candidate_indices is None:
                self._candidate_indices = np.array([
                    self._word_to_idx[c] for c in candidates if c in self._word_to_idx
                ])
            
            # Vectorized pattern lookup
            patterns = self._pattern_matrix[guess_idx, self._candidate_indices]
            
            # Count pattern occurrences
            counts = np.bincount(patterns, minlength=243)
            
            # Calculate entropy
            probs = counts / len(self._candidate_indices)
            probs = probs[probs > 0]
            entropy = -np.sum(probs * np.log2(probs))
        else:
            # Fallback: manual calculation
            counts = Counter()
            for secret in candidates:
                pattern = self.game.evaluate_guess(guess_word, secret_word=secret)
                counts[pattern] += 1
                
            entropy = 0.0
            for count in counts.values():
                if count > 0:
                    p = count / num_candidates
                    entropy += p * -math.log2(p)

        self._turn_entropy_cache[guess_word] = entropy
        return entropy

    def _get_random_samples(self, start_node, k):
        """Randomized DFS with Early Stopping to get k samples efficiently."""
        samples = []
        stack = [start_node]
        
        while stack and len(samples) < k:
            node = stack.pop()
            
            if node.is_word:
                samples.append(node.word)
                if len(samples) >= k:
                    break
            
            children = list(node.children.values())
            random.shuffle(children) # Randomize traversal order
            
            for child in children:
                stack.append(child)
                
        return samples

    def _compute_entropy_turn(self):
        """
        Performs the greedy entropy construction and populates the turn cache.
        Returns the greedy_guess word constructed from the Trie traversal.
        Assumes: self._turn_entropy_cache is reset, self.trie is updated, 
                 and self.currently_consistent_words is set.
        """
        candidates = list(self.currently_consistent_words)
        
        # Reset candidate indices cache for new candidate set
        self._candidate_indices = None
        if len(candidates) <= 1:
            if candidates:
                self.calculate_entropy(candidates[0], candidates)
                return candidates[0]
            return "error"

        current_node = self.trie.root
        current_prefix = ""
        
        # Greedy Construction Loop (Depth 0 to 4)
        for depth in range(5):
            best_char = None
            max_avg_entropy = -1.0
            
            possible_chars = list(current_node.children.keys())
            if not possible_chars:
                break

            for char in possible_chars:
                child_node = current_node.children[char]
                
                # Get random samples from this branch
                samples = self._get_random_samples(child_node, self.sample_size)
                
                if not samples:
                    continue
                
                total_entropy = 0.0
                for word in samples:
                    # Entropy is computed and CACHED here
                    total_entropy += self.calculate_entropy(word, candidates)
                
                avg_entropy = total_entropy / len(samples)
                
                # We pick the path based on AVERAGE entropy (Greedy approach)
                if avg_entropy > max_avg_entropy:
                    max_avg_entropy = avg_entropy
                    best_char = char
            
            if best_char:
                current_prefix += best_char
                current_node = current_node.children[best_char]
            else:
                break # Should not happen if tree is valid

        greedy_guess = current_prefix
        
        # Ensure the greedy guess is calculated and in the cache
        self.calculate_entropy(greedy_guess, candidates)
        
        return greedy_guess

    def pick_guess(self, history):
        if not history:
            return self.first_guess
        # 1. Initialization
        self._turn_entropy_cache = {} # Reset cache for new turn
        self._candidate_indices = None  # Reset candidate indices for new turn
        self._update_trie(history)
        
        # 2. Compute greedy guess via entropy sampling
        greedy_guess = self._compute_entropy_turn()
        
        # 3. Final Selection: Greedy vs Best Cached
        # Ensure the greedy guess is calculated and in the cache
        greedy_entropy = self._turn_entropy_cache.get(greedy_guess, 0.0)
        
        # Find the single best word we encountered during the entire sampling process
        best_cached_word = None
        best_cached_entropy = -1.0
        
        for word, ent in self._turn_entropy_cache.items():
            if ent > best_cached_entropy:
                best_cached_entropy = ent
                best_cached_word = word

        # Decision: Did we stumble upon a word better than our greedy construction?
        final_guess = greedy_guess
        
        if best_cached_word and best_cached_entropy > greedy_entropy:
            print(f"ProgressiveEntropy: Switched greedy '{greedy_guess}' ({greedy_entropy:.3f}) "
                  f"for cached optimum '{best_cached_word}' ({best_cached_entropy:.3f})")
            final_guess = best_cached_word
        else:
            print(f"ProgressiveEntropy: Stuck with greedy '{greedy_guess}' ({greedy_entropy:.3f})")

        self.search_stats.append({
            'method': 'ProgressiveEntropy',
            'word_found': final_guess,
            'cache_size': len(self._turn_entropy_cache),
            'switched': final_guess != greedy_guess
        })
        
        return final_guess

    def get_all_suggestions(self):
        """
        Get all suggestions from the progressive entropy sampling cache.
        Calls _compute_entropy_turn() to populate the cache if needed.
        Returns a list of tuples (word, entropy) sorted by entropy descending.
        Limited to top 100 suggestions.
        """
        if not self.game.attempts:
            # First try: return the canonical first guess as the single suggestion
            return [(self.first_guess, 0.0)]
        
        
        # Compute entropy turn to populate cache if not already done
        self._turn_entropy_cache = {} # Reset cache for new turn
        self._candidate_indices = None  # Reset candidate indices for new turn
        # no need update trie, since already updated in web.app.player_Guess 
        self._compute_entropy_turn()

        
        
        
        print("Number of words left: ")
        print(len(self.currently_consistent_words))

        # Sort cache entries by entropy (highest first) and limit to top 100
        word_entropy_list = sorted(
            self._turn_entropy_cache.items(),
            key=lambda x: x[1],
            reverse=True
        )

        print("Best entropy suggestions from cache:")
        for word, entropy in word_entropy_list[:10]:
            print(f"  {word}: {entropy:.4f} bits")
        
        return word_entropy_list[:100]
