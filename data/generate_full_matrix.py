"""
Generate full pattern matrix for all allowed_words x allowed_words combinations.
This creates a "fair" matrix where the solver doesn't know which words are possible answers.

Matrix shape: (12953, 12953) = ~168 million entries
Storage: ~160MB as uint8 NumPy array

FIXED: Proper handling of duplicate letters in yellow pass.
"""

import os
import sys
import numpy as np
from collections import Counter

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data import paths

# Pattern constants
MISS = 0       # Gray
MISPLACED = 1  # Yellow  
EXACT = 2      # Green


def calculate_pattern(guess, secret):
    """
    Calculate pattern for a single guess/secret pair.
    This is the reference implementation that handles duplicates correctly.
    """
    guess_list = list(guess)
    secret_list = list(secret)
    feedback = [MISS] * 5
    
    # Green pass
    for i in range(5):
        if guess_list[i] == secret_list[i]:
            feedback[i] = EXACT
            secret_list[i] = None
            guess_list[i] = None
    
    # Yellow pass - use counter for remaining letters
    secret_counter = Counter([s for s in secret_list if s is not None])
    
    for i in range(5):
        if feedback[i] == MISS and guess_list[i] is not None:
            if secret_counter[guess_list[i]] > 0:
                feedback[i] = MISPLACED
                secret_counter[guess_list[i]] -= 1
    
    # Convert to integer (MSB first)
    pattern = 0
    for f in feedback:
        pattern = pattern * 3 + f
    
    return pattern


def generate_pattern_matrix(words, chunk_size=500):
    """
    Generate pattern matrix using the correct reference implementation.
    Processes in chunks for progress reporting.
    """
    n = len(words)
    print(f"Generating {n} x {n} pattern matrix...")
    
    result = np.zeros((n, n), dtype=np.uint8)
    
    for i in range(0, n, chunk_size):
        i_end = min(i + chunk_size, n)
        if i % 1000 == 0:
            print(f"  Processing rows {i} to {i_end}...")
        
        for gi in range(i, i_end):
            guess = words[gi]
            for si in range(n):
                secret = words[si]
                result[gi, si] = calculate_pattern(guess, secret)
    
    return result


def main():
    print("=" * 60)
    print("Generating Full Pattern Matrix (allowed_words x allowed_words)")
    print("=" * 60)
    
    # Load allowed words
    with open(paths.ALLOWED_WORDS, 'r') as f:
        allowed_words = [line.strip().lower() for line in f if len(line.strip()) == 5]
    
    print(f"Loaded {len(allowed_words)} allowed words")
    
    # Generate the full matrix
    pattern_matrix = generate_pattern_matrix(allowed_words)
    
    print(f"\nMatrix shape: {pattern_matrix.shape}")
    print(f"Matrix size: {pattern_matrix.nbytes / 1024 / 1024:.1f} MB")
    
    # Save the matrix
    output_path = paths.FULL_MATRIX_PATH
    np.save(output_path, pattern_matrix)
    print(f"Saved to: {output_path}")
    
    # Verification
    print("\nVerification:")
    
    # Test ABACK vs TARES (the case that was failing)
    aback_idx = allowed_words.index('aback')
    tares_idx = allowed_words.index('tares')
    
    matrix_val = pattern_matrix[aback_idx, tares_idx]
    expected = calculate_pattern('aback', 'tares')
    
    print(f"  ABACK vs TARES: matrix={matrix_val}, expected={expected}", 
          "✓" if matrix_val == expected else "✗ MISMATCH!")
    
    # Test a few more
    tests = [
        ('tares', 'aback'),
        ('crane', 'slate'),
        ('aalii', 'aback'),  # duplicate letters
    ]
    
    for guess, secret in tests:
        gi = allowed_words.index(guess)
        si = allowed_words.index(secret)
        matrix_val = pattern_matrix[gi, si]
        expected = calculate_pattern(guess, secret)
        print(f"  {guess.upper()} vs {secret.upper()}: matrix={matrix_val}, expected={expected}",
              "✓" if matrix_val == expected else "✗ MISMATCH!")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
