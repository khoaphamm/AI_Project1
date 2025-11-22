import random
import os
import json
from collections import Counter
from data import paths

# Constants
MISS = 0       # Gray
MISPLACED = 1  # Yellow
EXACT = 2      # Green

class WordleGame:
    def __init__(self, 
                 allowed_words_path=paths.ALLOWED_WORDS, 
                 possible_words_path=paths.POSSIBLE_WORDS, 
                 matrix_path="data/wordle_matrix.json", 
                 secret_word=None):
        
        # --- 1. Setup Paths ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        def get_full_path(p):
            return os.path.join(script_dir, p) if not os.path.isabs(p) else p

        allowed_path = get_full_path(allowed_words_path)
        possible_path = get_full_path(possible_words_path)
        matrix_full_path = get_full_path(matrix_path)
        
        # --- 2. Load Words (Standard Lists) ---
        self.allowed_words = self.load_words(allowed_path)
        self.possible_words = self.load_words(possible_path)
        
        if not self.allowed_words:
            self.allowed_words = ["apple", "raise", "stone", "crate", "slate", "trace", "arise"]
        if not self.possible_words:
            self.possible_words = self.allowed_words

        self.allowed_words = set(self.allowed_words)
        
        # --- 3. Load Optimization Matrix ---
        self.matrix_data = None
        self.secret_map = {} # Maps secret_word -> row_index
        self.guess_map = {}  # Maps guess_word -> col_index
        self.load_matrix(matrix_full_path)

        # --- 4. Game State Setup ---
        if secret_word:
            self.secret_word = secret_word.lower()
        else:
            self.secret_word = random.choice(list(self.possible_words))
            
        self.max_attempts = 6
        self.attempts = [] 
        self.game_over = False
        self.won = False

    def load_words(self, path):
        try:
            with open(path, 'r') as f:
                return [line.strip().lower() for line in f if len(line.strip()) == 5]
        except FileNotFoundError:
            return []

    def load_matrix(self, path):
        """
        Loads the asymmetric matrix (Possible x Allowed).
        """
        if not os.path.exists(path):
            print(f"[Info] Matrix not found at {path}. Running in calculation mode.")
            return

        try:
            print("Loading optimization matrix...")
            with open(path, 'r') as f:
                data = json.load(f)
                
            # We must build maps based on the JSON content to ensure index alignment
            # Row Map: Possible Words (Secrets)
            self.secret_map = {w: i for i, w in enumerate(data["possible_words"])}
            
            # Col Map: Allowed Words (Guesses)
            self.guess_map = {w: i for i, w in enumerate(data["allowed_words"])}
            
            self.matrix_data = data["matrix"]
            print(f"Matrix loaded: {len(self.secret_map)} secrets x {len(self.guess_map)} guesses.")
        except Exception as e:
            print(f"[Warning] Failed to load matrix: {e}")
            self.matrix_data = None
            self.secret_map = {}
            self.guess_map = {}

    def validate_guess(self, guess):
        guess = guess.lower()
        if len(guess) != 5:
            return False, "Word must be 5 letters long."
        if guess not in self.allowed_words:
            return False, "Word not in dictionary."
        return True, ""

    def evaluate_guess(self, guess, secret_word=None):
        """
        Returns an INTEGER representing the feedback in base-3.
        Lookup Order: matrix[secret_index][guess_index]
        """
        if secret_word is None:
            secret_word = self.secret_word
        
        guess = guess.lower()
        secret_word = secret_word.lower()

        # --- OPTIMIZED LOOKUP ---
        # We check if the specific pairing exists in our precomputed maps
        if (self.matrix_data and 
            secret_word in self.secret_map and 
            guess in self.guess_map):
            
            row = self.secret_map[secret_word]
            col = self.guess_map[guess]
            return self.matrix_data[row][col]
        # ------------------------

        # FALLBACK: Manual Calculation
        secret = list(secret_word)
        guess_list = list(guess)
        feedback = [MISS] * 5
        
        # 1. Green Pass
        for i in range(5):
            if guess_list[i] == secret[i]:
                feedback[i] = EXACT
                secret[i] = None 
                guess_list[i] = None 

        # 2. Yellow Pass
        secret_counter = Counter([s for s in secret if s is not None])

        for i in range(5):
            if feedback[i] == MISS and guess_list[i] is not None:
                if secret_counter[guess_list[i]] > 0:
                    feedback[i] = MISPLACED
                    secret_counter[guess_list[i]] -= 1
        
        # 3. Convert to Base-3 Int
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