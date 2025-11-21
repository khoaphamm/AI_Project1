import os
from wordle_logic import WordleGame, MISS, MISPLACED, EXACT

# ANSI Colors for terminal
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_GRAY = '\033[90m'
COLOR_WHITE = '\033[97m'
RESET = '\033[0m'

def print_colored_word(word, feedback):
    """
    Prints the word colored based on feedback codes.
    """
    output = ""
    for letter, code in zip(word, feedback):
        if code == EXACT:
            output += f"{COLOR_GREEN}{letter.upper()}{RESET} "
        elif code == MISPLACED:
            output += f"{COLOR_YELLOW}{letter.upper()}{RESET} "
        else:
            output += f"{COLOR_GRAY}{letter.upper()}{RESET} "
    print(output)

def main():
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 40)
    print("         WELCOME TO WORDLE!")
    print("=" * 40)
    print(f"\nYou have 6 attempts to guess a 5-letter word.")
    print(f"{COLOR_GREEN}■{RESET} Green  = Correct letter in correct position")
    print(f"{COLOR_YELLOW}■{RESET} Yellow = Correct letter in wrong position")
    print(f"{COLOR_GRAY}■{RESET} Gray   = Letter not in word")
    print("-" * 40)

    # Initialize Game
    game = WordleGame()

    while not game.game_over:
        guess = input(f"\nAttempt {len(game.attempts) + 1}/{game.max_attempts}: ").strip()
        
        success, result = game.make_guess(guess)
        
        if success:
            # 'result' is the feedback tuple (e.g., (0, 2, 1, 0, 0))
            # Clear screen and reprint entire board for clean UI
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 40)
            print("         WELCOME TO WORDLE!")
            print("=" * 40)
            print()
            
            # Print history
            for prev_word, prev_feedback in game.attempts:
                print_colored_word(prev_word, prev_feedback)
        else:
            # 'result' is an error string
            print(f"{COLOR_YELLOW}⚠ Invalid input: {result}{RESET}")

    print("-" * 40)
    if game.won:
        print(f"{COLOR_GREEN}🎉 Congratulations! You guessed the word in {len(game.attempts)} attempts!{RESET}")
    else:
        print(f"😢 Game Over! The word was: {COLOR_GREEN}{game.secret_word.upper()}{RESET}")
    print("=" * 40)

if __name__ == "__main__":
    main()