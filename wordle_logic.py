import random
from collections import Counter
import os

# Constants matching your provided script
MISS = 0       # Gray
MISPLACED = 1  # Yellow
EXACT = 2      # Green

class WordleGame:
    def __init__(self, allowed_words_path='allowed_words.txt', possible_words_path='possible_words.txt', secret_word=None):
        """
        Initialize the game state.
        :param allowed_words_path: Path to the file containing ALL valid guesses.
        :param possible_words_path: Path to the file containing potential SECRET words (usually a subset of allowed).
        :param secret_word: Optional. Force a specific secret word (good for debugging/AI testing).
        """
        # Get absolute paths relative to this file's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        allowed_path = os.path.join(script_dir, allowed_words_path) if not os.path.isabs(allowed_words_path) else allowed_words_path
        possible_path = os.path.join(script_dir, possible_words_path) if not os.path.isabs(possible_words_path) else possible_words_path
        
        self.allowed_words = self.load_words(allowed_path)
        self.possible_words = self.load_words(possible_path)
        
        # Fallback if files are empty or missing
        if not self.allowed_words:
            self.allowed_words = ["apple", "raise", "stone", "crate", "slate", "trace", "arise"]
        if not self.possible_words:
            self.possible_words = self.allowed_words

        # Ensure consistency
        self.allowed_words = set(self.allowed_words) # Set for O(1) lookup
        
        if secret_word:
            self.secret_word = secret_word.lower()
        else:
            self.secret_word = random.choice(list(self.possible_words))
            
        self.max_attempts = 6
        self.attempts = [] # Stores tuples of (guessed_word, feedback_pattern)
        self.game_over = False
        self.won = False

    def load_words(self, path):
        try:
            with open(path, 'r') as f:
                return [line.strip().lower() for line in f if len(line.strip()) == 5]
        except FileNotFoundError:
            print(f"Warning: {path} not found.")
            return []

    def validate_guess(self, guess):
        guess = guess.lower()
        if len(guess) != 5:
            return False, "Word must be 5 letters long."
        if guess not in self.allowed_words:
            return False, "Word not in dictionary."
        return True, ""

    def evaluate_guess(self, guess, secret_word=None):
        """
        Core logic to generate the Green/Yellow/Gray pattern.
        Returns a list of integers: 0 (MISS), 1 (MISPLACED), 2 (EXACT).
        
        This function is static-like so AI solvers can use it 
        to simulate guesses against hypothetical secrets.
        """
        if secret_word is None:
            secret_word = self.secret_word

        guess = guess.lower()
        secret = list(secret_word)
        guess_list = list(guess)
        feedback = [MISS] * 5
        
        # 1. Green Pass (Exact Matches)
        for i in range(5):
            if guess_list[i] == secret[i]:
                feedback[i] = EXACT
                secret[i] = None # Mark as used in secret
                guess_list[i] = None # Mark as handled

        # 2. Yellow Pass (Misplaced Matches)
        # Count remaining available letters in the secret word
        secret_counter = Counter([s for s in secret if s is not None])

        for i in range(5):
            if feedback[i] == MISS and guess_list[i] is not None: # If not already Green
                if secret_counter[guess_list[i]] > 0:
                    feedback[i] = MISPLACED
                    secret_counter[guess_list[i]] -= 1
        
        return tuple(feedback) # Return as tuple so it's hashable

    def make_guess(self, guess):
        """
        Processes a turn in the actual game.
        Returns: success (bool), message/feedback
        """
        if self.game_over:
            return False, "Game is already over."

        is_valid, message = self.validate_guess(guess)
        if not is_valid:
            return False, message

        guess = guess.lower()
        feedback = self.evaluate_guess(guess)
        self.attempts.append((guess, feedback))

        # Check Win
        if guess == self.secret_word:
            self.won = True
            self.game_over = True
        
        # Check Loss
        elif len(self.attempts) >= self.max_attempts:
            self.game_over = True

        return True, feedback