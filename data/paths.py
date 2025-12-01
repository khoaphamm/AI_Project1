import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_WORDS = os.path.join(BASE_DIR, "allowed_words.txt")
POSSIBLE_WORDS = os.path.join(BASE_DIR, "possible_words.txt")
MATRIX_PATH = os.path.join(BASE_DIR, "wordle_matrix.json")
NUMPY_MATRIX_PATH = os.path.join(BASE_DIR, "pattern_matrix.npy")
# Full symmetric matrix (allowed_words x allowed_words) - fair version without cheating
FULL_MATRIX_PATH = os.path.join(BASE_DIR, "full_pattern_matrix.npy")