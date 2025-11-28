"""
Statistical comparison of DFS and Hill Climbing solvers across all possible Wordle games.
Tests both solvers against all ~2300 possible secret words and reports aggregate statistics.
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
from algorithms.solvers import DFSSolver, HillClimbingSolver, EntropySolver, ProgressiveEntropySolver
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
def run_solver_benchmark(solver_class, solver_name, secret_words, verbose=False, quiet=True, solver_kwargs=None):
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




def print_summary(dfs_stats, hc_stats):
    """Print comparison summary."""
    print(f"\n{'='*60}")
    print("SUMMARY COMPARISON")
    print(f"{'='*60}")
    print(f"{'Metric':<30} {'DFS':<15} {'Hill Climbing':<15}")
    print(f"{'-'*60}")
    print(f"{'Total Games':<30} {dfs_stats['total_games']:<15} {hc_stats['total_games']:<15}")
    print(f"{'Wins':<30} {dfs_stats['wins']:<15} {hc_stats['wins']:<15}")
    print(f"{'Win Rate (%)':<30} {dfs_stats['win_rate']:<15.2f} {hc_stats['win_rate']:<15.2f}")
    print(f"{'Avg Attempts (when won)':<30} {dfs_stats['avg_attempts']:<15.2f} {hc_stats['avg_attempts']:<15.2f}")
    print(f"{'Avg Nodes Visited':<30} {dfs_stats['avg_nodes_visited']:<15.1f} {hc_stats['avg_nodes_visited']:<15.1f}")
    print(f"{'Avg Time/Game (s)':<30} {dfs_stats['avg_time_per_game']:<15.4f} {hc_stats['avg_time_per_game']:<15.4f}")
    print(f"{'Total Time (s)':<30} {dfs_stats['total_time']:<15.2f} {hc_stats['total_time']:<15.2f}")
    
    print(f"\n{'Attempts Distribution (DFS)':}")
    for attempt in sorted([k for k in dfs_stats['attempts_distribution'].keys() if k != 'failed']):
        count = dfs_stats['attempts_distribution'][attempt]
        print(f"  {attempt} attempts: {count} games ({count/dfs_stats['total_games']*100:.1f}%)")
    if 'failed' in dfs_stats['attempts_distribution']:
        count = dfs_stats['attempts_distribution']['failed']
        print(f"  Failed: {count} games ({count/dfs_stats['total_games']*100:.1f}%)")
    
    print(f"\n{'Attempts Distribution (Hill Climbing)':}")
    for attempt in sorted([k for k in hc_stats['attempts_distribution'].keys() if k != 'failed']):
        count = hc_stats['attempts_distribution'][attempt]
        print(f"  {attempt} attempts: {count} games ({count/hc_stats['total_games']*100:.1f}%)")
    if 'failed' in hc_stats['attempts_distribution']:
        count = hc_stats['attempts_distribution']['failed']
        print(f"  Failed: {count} games ({count/hc_stats['total_games']*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Compare DFS vs Hill Climbing solvers across all possible games.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of games to test (for quick testing)")
    parser.add_argument("--verbose", action="store_true", help="Print detailed game logs")
    parser.add_argument("--output", type=str, default="solver_comparison.json", help="Output JSON file for detailed results")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for shuffling test order (optional)")
    # Single-core only; no worker flags
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
    
    # Run benchmarks
    quiet = not args.verbose
    dfs_stats = run_solver_benchmark(DFSSolver, "DFS", secret_words, verbose=args.verbose, quiet=quiet)
   # hc_stats = run_solver_benchmark(HillClimbingSolver, "Hill Climbing", secret_words, verbose=args.verbose, quiet=quiet)
    # Include Entropy solver (single-core only)
   # ent_stats = run_solver_benchmark(EntropySolver, "Entropy", secret_words, verbose=args.verbose, quiet=quiet)
    

    """ #NOTE: HARD CODE, NEED TO CHANGE IN CLASS OF PROG_ENTROPY """ 
    sampling_parameter = 100


    prog_ent_stats = run_solver_benchmark(ProgressiveEntropySolver, "Progressive Entropy", secret_words, verbose=args.verbose, quiet=quiet)

    # Print summary
    print_summary(dfs_stats, prog_ent_stats)
    print("\nProgressive Entropy Solver Summary")
    print("-"*60)
    print(f"Sampling Parameter:                    {sampling_parameter}")
    print(f"Total Games                    {prog_ent_stats['total_games']}")
    print(f"Wins                           {prog_ent_stats['wins']}")
    print(f"Win Rate (%)                   {prog_ent_stats['win_rate']:.2f}")
    print(f"Avg Attempts (when won)        {prog_ent_stats['avg_attempts']:.2f}")
    print(f"Avg Nodes Visited              {prog_ent_stats['avg_nodes_visited']:.1f}")
    print(f"Avg Time/Game (s)              {prog_ent_stats['avg_time_per_game']:.4f}")
    print(f"Total Time (s)                 {prog_ent_stats['total_time']:.2f}")
    # Print average consistency sizes by attempt index
    if 'avg_consistency_by_attempt' in prog_ent_stats:
        print("\nConsistency Size (avg by attempt)")
        for attempt_idx in sorted(prog_ent_stats['avg_consistency_by_attempt'].keys()):
            avg_sz = prog_ent_stats['avg_consistency_by_attempt'][attempt_idx]
            print(f"  Attempt {attempt_idx}: {avg_sz:.1f} candidates on average")
    # No workers in single-thread mode
    # Print attempts distribution for Entropy solver
    print("\nAttempts Distribution (Entropy)")
    for attempt in sorted([k for k in prog_ent_stats['attempts_distribution'].keys() if k != 'failed']):
        count = prog_ent_stats['attempts_distribution'][attempt]
        print(f"  {attempt} attempts: {count} games ({count/prog_ent_stats['total_games']*100:.1f}%)")
    if 'failed' in prog_ent_stats['attempts_distribution']:
        count = prog_ent_stats['attempts_distribution']['failed']
        print(f"  Failed: {count} games ({count/prog_ent_stats['total_games']*100:.1f}%)")
    
    # Save detailed results
    output_data = {
        'dfs': dfs_stats,
        'progressive entropy': prog_ent_stats,
        'comparison': {
            'total_games': len(secret_words),
            'dfs_win_rate': dfs_stats['win_rate'],
            'progressive_entropy_win_rate': prog_ent_stats['win_rate'],
            'dfs_faster_than_prog_entropy': dfs_stats['total_time'] < prog_ent_stats['total_time']
        }
    }
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {args.output}")


if __name__ == "__main__":
    main()