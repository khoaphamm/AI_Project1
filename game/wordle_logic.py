import random
import os
import numpy as np
from collections import Counter
from data import paths

# Constants
MISS = 0       # Gray
MISPLACED = 1  # Yellow
EXACT = 2      # Green


class WordleGame:
    """
    Wordle game logic with optimized pattern lookup using NumPy matrix.
    
    Uses the full symmetric pattern matrix (allowed_words x allowed_words)
    for O(1) pattern lookups. This benefits ALL solvers that use evaluate_guess().
    """
    
    # Class-level cache for pattern matrix (shared across all game instances)
    _pattern_matrix = None
    _word_to_idx = None
    _word_list = None
    _matrix_loaded = False
    
    def __init__(self, 
                 allowed_words_path=paths.ALLOWED_WORDS, 
                 possible_words_path=paths.POSSIBLE_WORDS, 
                 secret_word=None):
        
        # --- 1. Load Words (Standard Lists) ---
        self.allowed_words = self._load_words(allowed_words_path)
        self.possible_words = self._load_words(possible_words_path)
        
        if not self.allowed_words:
            self.allowed_words = ["apple", "raise", "stone", "crate", "slate", "trace", "arise"]
        if not self.possible_words:
            self.possible_words = self.allowed_words

        self.allowed_words = set(self.allowed_words)
        
        # --- 2. Load Full Pattern Matrix (shared across instances) ---
        if not WordleGame._matrix_loaded:
            self._load_pattern_matrix()

        # --- 3. Game State Setup ---
        self.max_attempts = 6
        self.reset(secret_word)

    def reset(self, secret_word=None):
        """
        Reset game state for a new game without reloading word lists and matrix.
        """
        if secret_word:
            self.secret_word = secret_word.lower()
        else:
            self.secret_word = random.choice(list(self.possible_words))
        self.attempts = [] 
        self.game_over = False
        self.won = False

    @staticmethod
    def _load_words(path):
        """Load words from file."""
        try:
            with open(path, 'r') as f:
                return [line.strip().lower() for line in f if len(line.strip()) == 5]
        except FileNotFoundError:
            return []

    @classmethod
    def _load_pattern_matrix(cls):
        """
        Load the full symmetric NumPy pattern matrix (allowed_words x allowed_words).
        This is shared across all game instances for efficiency.
        """
        matrix_path = paths.FULL_MATRIX_PATH
        
        if os.path.exists(matrix_path):
            print("Loading full pattern matrix for game...")
            cls._pattern_matrix = np.load(matrix_path)
            
            # Load word list for index mapping
            with open(paths.ALLOWED_WORDS, 'r') as f:
                cls._word_list = [line.strip().lower() for line in f if len(line.strip()) == 5]
            
            cls._word_to_idx = {w: i for i, w in enumerate(cls._word_list)}
            
            print(f"Pattern matrix loaded: {cls._pattern_matrix.shape} (O(1) lookups enabled)")
            cls._matrix_loaded = True
        else:
            print(f"[Warning] Full pattern matrix not found at {matrix_path}")
            print("Run: python data/generate_full_matrix.py to create it.")
            print("Falling back to calculation mode (slower).")
            cls._matrix_loaded = True  # Mark as loaded to prevent retry

    def validate_guess(self, guess):
        guess = guess.lower()
        if len(guess) != 5:
            return False, "Word must be 5 letters long."
        if guess not in self.allowed_words:
            return False, "Word not in dictionary."
        return True, ""

    def evaluate_guess(self, guess, secret_word=None):
        """
        Returns an INTEGER representing the feedback pattern in base-3.
        
        Uses O(1) NumPy matrix lookup when available.
        Matrix layout: pattern_matrix[guess_idx, secret_idx] = pattern
        
        Pattern encoding (base-3 integer):
        - Each position: 0=MISS (gray), 1=MISPLACED (yellow), 2=EXACT (green)
        - pattern = p0 + 3*p1 + 9*p2 + 27*p3 + 81*p4
        """
        if secret_word is None:
            secret_word = self.secret_word
        
        guess = guess.lower()
        secret_word = secret_word.lower()

        # --- OPTIMIZED O(1) LOOKUP ---
        if (self._pattern_matrix is not None and 
            guess in self._word_to_idx and 
            secret_word in self._word_to_idx):
            
            guess_idx = self._word_to_idx[guess]
            secret_idx = self._word_to_idx[secret_word]
            return int(self._pattern_matrix[guess_idx, secret_idx])
        # ------------------------

        # FALLBACK: Manual Calculation (for words not in matrix)
        return self._calculate_pattern(guess, secret_word)
    
    def _calculate_pattern(self, guess, secret_word):
        """
        Manually calculate the feedback pattern.
        Used as fallback when matrix lookup is not available.
        """
        secret = list(secret_word)
        guess_list = list(guess)
        feedback = [MISS] * 5
        
        # 1. Green Pass - exact matches
        for i in range(5):
            if guess_list[i] == secret[i]:
                feedback[i] = EXACT
                secret[i] = None 
                guess_list[i] = None 

        # 2. Yellow Pass - misplaced letters
        secret_counter = Counter([s for s in secret if s is not None])

        for i in range(5):
            if feedback[i] == MISS and guess_list[i] is not None:
                if secret_counter[guess_list[i]] > 0:
                    feedback[i] = MISPLACED
                    secret_counter[guess_list[i]] -= 1
        
        # 3. Convert to Base-3 Integer
        feedback_int = 0
        for f in feedback:
            feedback_int = feedback_int * 3 + f
            
        return feedback_int

    @staticmethod
    def decode_feedback(feedback_int):
        feedback = []
        for _ in range(5):
            feedback.append(feedback_int % 3)
            feedback_int //= 3
        return tuple(reversed(feedback))

    def is_consistent(self, candidate_word, history):
        """
        Checks if 'candidate_word' (as a hypothetical secret) 
        is consistent with the history of guesses.
        """
        for prev_guess, prev_feedback_int in history:
            # Fast lookup here is crucial for AI performance
            simulated_feedback_int = self.evaluate_guess(prev_guess, secret_word=candidate_word)
            if simulated_feedback_int != prev_feedback_int:
                return False
        return True

    def make_guess(self, guess):
        if self.game_over:
            return False, "Game is already over."

        is_valid, message = self.validate_guess(guess)
        if not is_valid:
            return False, message

        guess = guess.lower()
        feedback_int = self.evaluate_guess(guess)
        self.attempts.append((guess, feedback_int))

        if guess == self.secret_word:
            self.won = True
            self.game_over = True
        elif len(self.attempts) >= self.max_attempts:
            self.game_over = True

        return True, feedback_int