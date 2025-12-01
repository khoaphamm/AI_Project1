"""
Statistical benchmark for Knowledge-Based Hill Climbing Solver.
Tests the solver against all possible Wordle secret words and reports statistics.
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from game.wordle_logic import WordleGame
from algorithms.solvers import KnowledgeBasedHillClimbingSolver
from data import paths


def play_game(solver, secret_word, max_attempts=20, verbose=False, quiet=True):
    """
    Play a single game with the given solver and secret word.
    Returns game statistics.
    """
    # Suppress print output from solver if quiet mode
    import io
    import contextlib
    
    if quiet and not verbose:
        ctx = contextlib.redirect_stdout(io.StringIO())
    else:
        ctx = contextlib.nullcontext()
    
    with ctx:
        # Reset solver state for new game
        solver.currently_consistent_words = set(solver.game.allowed_words)
        solver.search_stats = []
    
    game = solver.game
    history = []
    attempts = 0
    won = False
    total_nodes_visited = 0
    consistency_sizes = []
    
    start_time = time.perf_counter()
    
    while attempts < max_attempts:
        guess = solver.pick_guess(history)
        attempts += 1
        
        success, feedback = game.make_guess(guess)
        
        if not success:
            if verbose:
                print(f"Invalid guess: {guess}")
            break
        
        history.append((guess, feedback))
        # Record current consistent set size from solver (updated inside pick_guess)
        try:
            consistency_sizes.append(len(solver.currently_consistent_words))
        except Exception:
            consistency_sizes.append(None)
        
        if verbose:
            feedback_decoded = game.decode_feedback(feedback)
            print(f"Attempt {attempts}: {guess} -> {feedback_decoded}")
        
        if guess == secret_word:
            won = True
            break
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    # Aggregate nodes visited from search stats
    for stat in solver.search_stats:
        total_nodes_visited += stat.get('nodes_visited', 0)
    
    return {
        'secret_word': secret_word,
        'won': won,
        'attempts': attempts,
        'nodes_visited': total_nodes_visited,
        'time_seconds': elapsed,
        'guesses': [g for g, _ in history],
        'consistency_sizes': consistency_sizes
    }


def run_solver_benchmark(solver_class, solver_name, secret_words, verbose=False, quiet=True):
    """
    Run a solver against all secret words and collect statistics.
    """
    print(f"\n{'='*60}")
    print(f"Testing {solver_name}")
    print(f"{'='*60}")
    
    # Create game and solver once, reuse for all tests
    game = WordleGame()
    game.max_attempts = 20  # Unlimited attempts for testing
    solver = solver_class(game)
    
    results = []
    wins = 0
    total_attempts = 0
    total_nodes = 0
    total_time = 0
    attempts_distribution = defaultdict(int)
    per_attempt_consistency = defaultdict(list)  # attempt_index -> list of sizes
    
    for idx, secret in enumerate(secret_words):
        if (idx + 1) % 100 == 0:
            print(f"Progress: {idx + 1}/{len(secret_words)} games...")
        
        # Reset game state for new secret word
        game.secret_word = secret.lower()
        game.attempts = []
        game.game_over = False
        game.won = False
        
        result = play_game(solver, secret, verbose=verbose, quiet=quiet)
        results.append(result)
        
        if result['won']:
            wins += 1
            attempts_distribution[result['attempts']] += 1
        else:
            attempts_distribution['failed'] += 1
        
        total_attempts += result['attempts']
        total_nodes += result['nodes_visited']
        total_time += result['time_seconds']
        # Aggregate consistency sizes by attempt index
        for i, sz in enumerate(result.get('consistency_sizes', []), start=1):
            if sz is not None:
                per_attempt_consistency[i].append(sz)
    
    num_games = len(secret_words)
    win_rate = (wins / num_games * 100) if num_games > 0 else 0
    avg_attempts = (total_attempts / num_games) if num_games > 0 else 0
    avg_nodes = (total_nodes / num_games) if num_games > 0 else 0
    avg_time = (total_time / num_games) if num_games > 0 else 0
    
    stats = {
        'solver': solver_name,
        'total_games': num_games,
        'wins': wins,
        'losses': num_games - wins,
        'win_rate': win_rate,
        'avg_attempts': avg_attempts,
        'avg_nodes_visited': avg_nodes,
        'avg_time_per_game': avg_time,
        'total_time': total_time,
        'attempts_distribution': dict(attempts_distribution),
        'results': results,
        'avg_consistency_by_attempt': {k: (sum(v)/len(v) if v else 0) for k, v in per_attempt_consistency.items()}
    }
    
    return stats


def print_summary(stats):
    """Print solver summary statistics."""
    print(f"\n{'='*60}")
    print(f"{stats['solver']} SUMMARY")
    print(f"{'='*60}")
    print(f"Total Games:                    {stats['total_games']}")
    print(f"Wins:                           {stats['wins']}")
    print(f"Losses:                         {stats['losses']}")
    print(f"Win Rate (%):                   {stats['win_rate']:.2f}")
    print(f"Avg Attempts (when won):        {stats['avg_attempts']:.2f}")
    print(f"Avg Nodes Visited:              {stats['avg_nodes_visited']:.1f}")
    print(f"Avg Time/Game (s):              {stats['avg_time_per_game']:.4f}")
    print(f"Total Time (s):                 {stats['total_time']:.2f}")
    
    # Print average consistency sizes by attempt index
    if 'avg_consistency_by_attempt' in stats:
        print("\nConsistency Size (avg by attempt)")
        for attempt_idx in sorted(stats['avg_consistency_by_attempt'].keys()):
            avg_sz = stats['avg_consistency_by_attempt'][attempt_idx]
            print(f"  Attempt {attempt_idx}: {avg_sz:.1f} candidates on average")
    
    # Print attempts distribution
    print("\nAttempts Distribution")
    for attempt in sorted([k for k in stats['attempts_distribution'].keys() if k != 'failed']):
        count = stats['attempts_distribution'][attempt]
        print(f"  {attempt} attempts: {count} games ({count/stats['total_games']*100:.1f}%)")
    if 'failed' in stats['attempts_distribution']:
        count = stats['attempts_distribution']['failed']
        print(f"  Failed: {count} games ({count/stats['total_games']*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Knowledge-Based Hill Climbing Solver across all possible games."
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Limit number of games to test (for quick testing)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Print detailed game logs"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="kb_hillclimbing_results.json", 
        help="Output JSON file for detailed results"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=None, 
        help="Random seed for shuffling test order (optional)"
    )
    args = parser.parse_args()
    
    # Load all possible secret words
    possible_path = paths.POSSIBLE_WORDS
    if not os.path.isabs(possible_path):
        possible_path = os.path.join(PROJECT_ROOT, possible_path)
    
    with open(possible_path, "r", encoding="utf-8") as f:
        secret_words = [line.strip().lower() for line in f if len(line.strip()) == 5]
    
    print(f"Loaded {len(secret_words)} possible secret words")
    
    if args.seed is not None:
        import random
        random.seed(args.seed)
        random.shuffle(secret_words)
        print(f"Shuffled with seed {args.seed}")
    
    if args.limit:
        secret_words = secret_words[:args.limit]
        print(f"Limited to {len(secret_words)} games")
    
    # Run benchmark
    quiet = not args.verbose
    kb_hc_stats = run_solver_benchmark(
        KnowledgeBasedHillClimbingSolver, 
        "Knowledge-Based Hill Climbing", 
        secret_words, 
        verbose=args.verbose, 
        quiet=quiet
    )
    
    # Print summary
    print_summary(kb_hc_stats)
    
    # Save detailed results
    output_data = {
        'solver': kb_hc_stats['solver'],
        'statistics': {
            'total_games': kb_hc_stats['total_games'],
            'wins': kb_hc_stats['wins'],
            'losses': kb_hc_stats['losses'],
            'win_rate': kb_hc_stats['win_rate'],
            'avg_attempts': kb_hc_stats['avg_attempts'],
            'avg_nodes_visited': kb_hc_stats['avg_nodes_visited'],
            'avg_time_per_game': kb_hc_stats['avg_time_per_game'],
            'total_time': kb_hc_stats['total_time'],
            'attempts_distribution': kb_hc_stats['attempts_distribution'],
            'avg_consistency_by_attempt': kb_hc_stats['avg_consistency_by_attempt']
        },
        'detailed_results': kb_hc_stats['results']
    }
    
    # Ensure output directory exists
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(PROJECT_ROOT, output_path)
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()

