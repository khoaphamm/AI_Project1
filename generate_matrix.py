import json
import os
import time
from game.wordle_logic import WordleGame


"""
RUN ONLY ONCE TO GET PATTERN MATRIX 
"""

def generate_matrix():
    print("Initializing Game to load word lists...")
    game = WordleGame()
    
    # 1. Define Axes
    # ROW = Goal / Secret Word (from Possible Words)
    # COL = User Guess (from Allowed Words)
    secrets = sorted(list(game.possible_words))
    guesses = sorted(list(game.allowed_words))
    
    s_count = len(secrets)
    g_count = len(guesses)
    
    print(f"Matrix Dimensions: {s_count} (Secrets) x {g_count} (Guesses)")
    print(f"Total Cells: {s_count * g_count:,}")
    
    matrix = []
    start_time = time.time()
    
    # 2. Generate Matrix
    # matrix[secret_index][guess_index]
    for r, secret in enumerate(secrets):
        row = []
        # For this specific secret, precompute feedback for EVERY valid guess
        for guess in guesses:
            # evaluate_guess calculates the base-3 int (0-242)
            # We pass secret_word explicitly to bypass the game's current state
            val = game.evaluate_guess(guess, secret_word=secret)
            row.append(val)
        
        matrix.append(row)
        
        # Progress Tracker
        if (r + 1) % 50 == 0:
            elapsed = time.time() - start_time
            percent = (r + 1) / s_count * 100
            print(f"Progress: {percent:.1f}% ({r+1}/{s_count}) - {elapsed:.0f}s")

    # 3. Save Data
    print("Calculation complete. Saving to JSON...")
    
    output_data = {
        "possible_words": secrets,  # Keys for Rows
        "allowed_words": guesses,   # Keys for Columns
        "matrix": matrix            # The 2D Data
    }
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "data", "wordle_matrix.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        # Separators remove whitespace to minimize file size
        json.dump(output_data, f, separators=(',', ':'))
        
    print(f"Successfully saved to {output_path}")

if __name__ == "__main__":
    generate_matrix()