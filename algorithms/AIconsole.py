import os
import time
from game.wordle_logic import WordleGame, MISS, MISPLACED, EXACT
from algorithms.solvers import DFSSolver, HillClimbingSolver, KnowledgeBasedHillClimbingSolver


# ANSI Colors
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_GRAY = '\033[90m'
COLOR_CYAN = '\033[96m'
RESET = '\033[0m'

def print_colored_word(word, feedback_int):
    """
    Decodes the integer feedback back to a tuple for display.
    """
    feedback_tuple = WordleGame.decode_feedback(feedback_int)
    output = ""
    for letter, code in zip(word, feedback_tuple):
        if code == EXACT:
            output += f"{COLOR_GREEN}{letter.upper()}{RESET} "
        elif code == MISPLACED:
            output += f"{COLOR_YELLOW}{letter.upper()}{RESET} "
        else:
            output += f"{COLOR_GRAY}{letter.upper()}{RESET} "
    print(output)

def play_user_mode(game):
    while not game.game_over:
        guess = input(f"\nAttempt {len(game.attempts) + 1}/{game.max_attempts}: ").strip()
        success, result = game.make_guess(guess)
        
        if success:
            os.system('cls' if os.name == 'nt' else 'clear')
            print_header()
            for prev_word, prev_feedback_int in game.attempts:
                print_colored_word(prev_word, prev_feedback_int)
        else:
            print(f"{COLOR_YELLOW}Invalid input: {result}{RESET}")

    finish_game(game)

def play_ai_mode(game, solver_class):
    solver = solver_class(game)
    print(f"\nAI ({solver_class.__name__}) is thinking...")
    
    while not game.game_over:
        time.sleep(1) # Add delay so we can watch it play
        
        # AI picks a guess based on history (history now contains ints for feedback)
        guess = solver.pick_guess(game.attempts)
        print(f"AI guesses: {guess.upper()}")
        
        success, result = game.make_guess(guess)
        if success:
            # Render Board
            os.system('cls' if os.name == 'nt' else 'clear')
            print_header()
            for prev_word, prev_feedback_int in game.attempts:
                print_colored_word(prev_word, prev_feedback_int)
        else:
            print(f"AI Error: Tried invalid word {guess}")
            break

    finish_game(game)

def print_header():
    print("=" * 50)
    print("      WORDLE - TRIE-BASED SEARCH AI SOLVER")
    print("=" * 50)
    print(f"{COLOR_GREEN}■{RESET} Green  = Exact position")
    print(f"{COLOR_YELLOW}■{RESET} Yellow = Wrong position")
    print(f"{COLOR_GRAY}■{RESET} Gray   = Not in word")
    print()
    print(f"{COLOR_CYAN}Search Space:{RESET} Trie structure")
    print(f"{COLOR_CYAN}Start Node:{RESET} Empty string ''")
    print(f"{COLOR_CYAN}Transitions:{RESET} Add one letter (depth 0→1→2→3→4→5)")
    print(f"{COLOR_CYAN}Goal Nodes:{RESET} All 5-letter words (leaves)")
    print("-" * 50)

def finish_game(game):
    print("-" * 50)
    if game.won:
        print(f"{COLOR_GREEN}✓ SUCCESS! Word found in {len(game.attempts)} guesses.{RESET}")
    else:
        print(f"{COLOR_GRAY}✗ FAILED. The word was: {COLOR_GREEN}{game.secret_word.upper()}{RESET}")
    print("=" * 50)

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_header()
    print("\nSelect Mode:")
    print("1. Play Yourself")
    print("2. AI Solver - Depth-First Search (DFS) on Trie")
    print("3. AI Solver - Hill Climbing on Trie")
    print("4. AI Solver - Knowledge Based Hill Climbing on Trie")
    
    choice = input(f"\n{COLOR_CYAN}Enter choice (1-3):{RESET} ").strip()
    
    # You can force a secret word here for testing, e.g., secret_word="apple"
    game = WordleGame() 
    
    if choice == '1':
        play_user_mode(game)
    elif choice == '2':
        play_ai_mode(game, DFSSolver)
    elif choice == '3':
        play_ai_mode(game, HillClimbingSolver)
    elif choice == '4':
        play_ai_mode(game, KnowledgeBasedHillClimbingSolver)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()