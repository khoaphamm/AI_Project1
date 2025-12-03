"""
Wordle Solvers using Trie-based Search

The search space is represented as a Trie where:
- Root = empty string ""
- Each level adds one letter (depth 1-5)
- Leaves (depth 5) = complete 5-letter words
- All leaves connect to a virtual GOAL node
- Goal = finding a word consistent with feedback history
"""

from collections import Counter, defaultdict
import math
import random
import numpy as np
from scipy.stats import entropy as scipy_entropy
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
        raise NotImplementedError


class DFSSolver(BaseSolver):
    """
    Depth-First Search Solver using an incrementally pruned Trie structure.
    """
    def pick_guess(self, history):
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
        if not self.currently_consistent_words:
            return []
        
        word_scores = []
        for word in self.currently_consistent_words:
            score = sum(self.heuristic_matrix[i].get(char, 0) for i, char in enumerate(word))
            word_scores.append((word, score))
        
        word_scores.sort(key=lambda x: x[1], reverse=True)
        return word_scores[:100]

    def _calculate_heuristic(self):
        freq_matrix = [defaultdict(int) for _ in range(5)]
        for word in self.game.allowed_words:
            for i, char in enumerate(word):
                freq_matrix[i][char] += 1
        print("Hill Climbing heuristic matrix calculated (from allowed_words).")
        return freq_matrix

    def pick_guess(self, history):
        self._update_trie(history)

        current_node = self.trie.root
        guess_word = ""
        nodes_visited = 1

        for i in range(5):
            possible_next_chars = list(current_node.children.keys())
            
            if not possible_next_chars:
                return list(self.currently_consistent_words)[0] if self.currently_consistent_words else "error"

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


class KnowledgeBasedHillClimbingSolver(BaseSolver):
    """
    Knowledge-Based Hill Climbing Solver.
    Recalculates the heuristic at EACH step based only on the remaining possible words (S_t).
    """
    def _calculate_dynamic_heuristic(self, words):
        freq_matrix = [defaultdict(int) for _ in range(5)]
        for word in words:
            for i, char in enumerate(word):
                freq_matrix[i][char] += 1
        return freq_matrix

    def pick_guess(self, history):
        self._update_trie(history)

        # Dynamic Heuristic: Build matrix from only the remaining valid words
        dynamic_matrix = self._calculate_dynamic_heuristic(self.currently_consistent_words)
        
        current_node = self.trie.root
        guess_word = ""
        nodes_visited = 1

        for i in range(5):
            possible_next_chars = list(current_node.children.keys())
            
            if not possible_next_chars:
                return list(self.currently_consistent_words)[0] if self.currently_consistent_words else "error"

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
        if not self.currently_consistent_words:
            return []
        # Build dynamic heuristic from remaining valid words
        dynamic_matrix = self._calculate_dynamic_heuristic(self.currently_consistent_words)

        # Try to construct a single best word by traversing the trie
        # using the same per-position greedy choice as `pick_guess`.
        # If the solver's trie is not available, build a temporary one.
        trie_root = None
        if self.trie is not None:
            trie_root = self.trie.root
        else:
            # Temporary trie for suggestion construction
            tmp_trie = WordleTrie(list(self.currently_consistent_words))
            trie_root = tmp_trie.root

        current_node = trie_root
        guess_word = ""

        for i in range(5):
            possible_next_chars = list(current_node.children.keys())

            if not possible_next_chars:
                # Fallback: return any remaining consistent word
                fallback = list(self.currently_consistent_words)[0] if self.currently_consistent_words else "error"
                if fallback == "error":
                    return []
                fallback_score = sum(dynamic_matrix[j].get(ch, 0) for j, ch in enumerate(fallback))
                return [(fallback, float(fallback_score))]

            best_char = max(
                possible_next_chars,
                key=lambda char: dynamic_matrix[i].get(char, 0)
            )

            guess_word += best_char
            current_node = current_node.children[best_char]

        total_score = sum(dynamic_matrix[i].get(char, 0) for i, char in enumerate(guess_word))
        return [(guess_word, float(total_score))]


class BaseEntropySolver(BaseSolver):
    """
    Base class for all Entropy-based solvers.
    Handles vectorized entropy calculations and game matrix access.
    """
    def __init__(self, game):
        super().__init__(game)
        self.first_guess = "tares"  # 3b1b favorite
        
        # Verify the game has the pattern matrix loaded
        if game._pattern_matrix is None:
            raise RuntimeError(
                "WordleGame does not have pattern matrix loaded.\n"
                "Run: python data/generate_full_matrix.py to create it."
            )
        
        # Cache for candidate indices to avoid recomputing in loop
        self._candidate_indices = None

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
        """Reset solver state."""
        super().reset()
        self._candidate_indices = None

    def _get_entropies_vectorized(self, candidate_indices):
        """
        Calculate entropy for ALL guess words against the given candidates.
        Uses vectorized NumPy operations for massive speedup.
        Returns: numpy array of entropies for each guess word
        """
        n_candidates = len(candidate_indices)
        n_words = self._pattern_matrix.shape[0]
        
        if n_candidates == 0:
            return np.zeros(n_words)
        
        # Get patterns: shape (n_words, n_candidates)
        sub_matrix = self._pattern_matrix[:, candidate_indices]
        
        # Count pattern occurrences (243 possible patterns)
        distributions = np.zeros((n_words, 243), dtype=np.float64)
        for j in range(n_candidates):
            patterns = sub_matrix[:, j]
            np.add.at(distributions, (np.arange(n_words), patterns), 1)
        
        distributions /= n_candidates
        entropies = scipy_entropy(distributions, base=2, axis=1)
        
        return entropies

    def calculate_single_entropy(self, guess_word, candidates):
        """
        Calculates E[I] for a single guess word against candidates.
        Uses vectorization if word is in matrix, otherwise falls back to slow method.
        """
        if guess_word in self._word_to_idx:
            guess_idx = self._word_to_idx[guess_word]
            
            if self._candidate_indices is None:
                self._candidate_indices = np.array([
                    self._word_to_idx[c] for c in candidates if c in self._word_to_idx
                ])
            
            if len(self._candidate_indices) == 0:
                return 0.0

            patterns = self._pattern_matrix[guess_idx, self._candidate_indices]
            counts = np.bincount(patterns, minlength=243)
            probs = counts / len(self._candidate_indices)
            probs = probs[probs > 0]
            
            return -np.sum(probs * np.log2(probs))
        else:
            # Fallback slow method
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


class EntropySolver(BaseEntropySolver):
    """
    Full Entropy Maximization Solver.
    Calculates entropy for ALL allowed words at every step.
    """
    def __init__(self, game):
        super().__init__(game)
        self.already_used = set()

    def reset(self):
        super().reset()
        self.already_used = set()

    def pick_guess(self, history):
        if not history:
            return self.first_guess
        
        self._update_currently_consistent_words(history)
        candidates = list(self.currently_consistent_words)
        
        if not candidates:
            return "error"
        if len(candidates) == 1:
            return candidates[0]

        candidate_indices = np.array([
            self._word_to_idx[c] for c in candidates if c in self._word_to_idx
        ])
        
        print(f"EntropySolver: Calculating entropy for all words against {len(candidates)} candidates (vectorized)...")
        
        all_entropies = self._get_entropies_vectorized(candidate_indices)
        
        # Mask out already used words
        for word in self.already_used:
            if word in self._word_to_idx:
                all_entropies[self._word_to_idx[word]] = -1
        
        best_idx = np.argmax(all_entropies)
        best_entropy = all_entropies[best_idx]
        best_word = self._idx_to_word(best_idx)
        
        # Tie-breaker: Prefer words that are possible candidates
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
        if self.currently_consistent_words == set(self.game.allowed_words):
            return [("tares", 6.1), ("lares", 6.1), ("rales", 6.1), ("rates", 6.1), ("teras", 6.0)]
        
        candidates = list(self.currently_consistent_words)
        if len(candidates) == 1:
            return [(candidates[0], 0.0)]
        
        candidate_indices = np.array([
            self._word_to_idx[c] for c in candidates if c in self._word_to_idx
        ])
        
        all_entropies = self._get_entropies_vectorized(candidate_indices)
        
        word_scores = []
        for idx, entropy_val in enumerate(all_entropies):
            word = self._idx_to_word(idx)
            if word not in self.already_used:
                word_scores.append((word, float(entropy_val)))
        
        word_scores.sort(key=lambda x: x[1], reverse=True)
        return word_scores[:100]


class ProgressiveEntropySolver(BaseEntropySolver):
    """
    Progressive Entropy Sampling Solver (HYBRID behavior).
    Uses a fixed trie for sampling to ensure exploration of the full word space
    while calculating entropy against the pruned set of candidates.
    """
    def __init__(self, game, samples_per_node=400):
        super().__init__(game)
        self.sample_size = samples_per_node
        self._turn_entropy_cache = {} # Maps word -> entropy
        # Fixed trie over the full allowed words for unbiased sampling
        self.fixed_trie = WordleTrie(list(self.game.allowed_words))
        print(f"ProgressiveEntropySolver (hybrid) initialized with {samples_per_node} samples per node.")

    def reset(self):
        super().reset()
        self._turn_entropy_cache = {}

    def calculate_entropy(self, guess_word, candidates):
        """
        Calculates E[I] with caching.
        """
        if guess_word in self._turn_entropy_cache:
            return self._turn_entropy_cache[guess_word]

        entropy = self.calculate_single_entropy(guess_word, candidates)
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
            random.shuffle(children)

            for child in children:
                stack.append(child)
        return samples

    def _compute_entropy_turn(self):
        """
        Greedy entropy construction using the FIXED Trie traversal.
        """
        candidates = list(self.currently_consistent_words)
        self._candidate_indices = None

        if len(candidates) <= 1:
            if candidates:
                self.calculate_entropy(candidates[0], candidates)
                return candidates[0]
            return "error"

        # Use the Fixed Trie's Root
        current_node = self.fixed_trie.root
        current_prefix = ""

        for _ in range(5):
            best_char = None
            max_avg_entropy = -1.0

            possible_chars = list(current_node.children.keys())
            if not possible_chars:
                break

            for char in possible_chars:
                child_node = current_node.children[char]
                samples = self._get_random_samples(child_node, self.sample_size)

                if not samples:
                    continue

                total_entropy = sum(self.calculate_entropy(word, candidates) for word in samples)
                avg_entropy = total_entropy / len(samples)

                if avg_entropy > max_avg_entropy:
                    max_avg_entropy = avg_entropy
                    best_char = char

            if best_char:
                current_prefix += best_char
                current_node = current_node.children[best_char]
            else:
                break

        greedy_guess = current_prefix
        self.calculate_entropy(greedy_guess, candidates)
        return greedy_guess

    def pick_guess(self, history):
        if not history:
            return self.first_guess

        self._turn_entropy_cache = {}

        # No dynamic trie rebuild; just update the set of consistent words
        self._update_currently_consistent_words(history)

        greedy_guess = self._compute_entropy_turn()
        greedy_entropy = self._turn_entropy_cache.get(greedy_guess, 0.0)

        best_cached_word = None
        best_cached_entropy = -1.0

        for word, ent in self._turn_entropy_cache.items():
            if ent > best_cached_entropy:
                best_cached_entropy = ent
                best_cached_word = word

        final_guess = greedy_guess

        if best_cached_word and best_cached_entropy > greedy_entropy:
            print(f"ProgressiveEntropy (hybrid): Switched greedy '{greedy_guess}' ({greedy_entropy:.3f}) "
                  f"for cached optimum '{best_cached_word}' ({best_cached_entropy:.3f})")
            final_guess = best_cached_word
        else:
            print(f"ProgressiveEntropy (hybrid): Stuck with greedy '{greedy_guess}' ({greedy_entropy:.3f})")

        self.search_stats.append({
            'method': 'ProgressiveEntropy',
            'word_found': final_guess,
            'cache_size': len(self._turn_entropy_cache),
            'switched': final_guess != greedy_guess
        })

        return final_guess

    def get_all_suggestions(self):
        if not self.game.attempts:
            return [(self.first_guess, 0.0)]
        
        self._turn_entropy_cache = {}
        self._compute_entropy_turn()
        
        print(f"Number of words left: {len(self.currently_consistent_words)}")

        word_entropy_list = sorted(
            self._turn_entropy_cache.items(),
            key=lambda x: x[1],
            reverse=True
        )

        print("Best entropy suggestions from cache:")
        for word, entropy in word_entropy_list[:10]:
            print(f"  {word}: {entropy:.4f} bits")
        
        return word_entropy_list[:100]
