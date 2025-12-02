"""
Statistical comparison of Wordle solvers across all possible games.
Compares: DFSSolver, KnowledgeBasedHillClimbingSolver, EntropySolver, ProgressiveEntropySolver
Tracks: win rate, attempts, time, nodes visited, and memory usage.
"""

import argparse
import json
import os
import sys
import time
import tracemalloc
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from game.wordle_logic import WordleGame
from algorithms.solvers import (
    DFSSolver,
    KnowledgeBasedHillClimbingSolver,
    EntropySolver,
    ProgressiveEntropySolver,
    HybridProgressiveEntropySolver,
)
from data import paths

# Define solvers to compare
SOLVERS = [
    ("HybridEntropy-10", lambda g, s=10: HybridProgressiveEntropySolver(g, samples_per_node=s)),
    ("HybridEntropy-30", lambda g, s=30: HybridProgressiveEntropySolver(g, samples_per_node=s)),
    ("HybridEntropy-50", lambda g, s=50: HybridProgressiveEntropySolver(g, samples_per_node=s)),
    ("HybridEntropy-80", lambda g, s=80: HybridProgressiveEntropySolver(g, samples_per_node=s)),
    ("HybridEntropy-100", lambda g, s=100: HybridProgressiveEntropySolver(g, samples_per_node=s)),
]


def play_game(solver, secret_word, max_attempts=20, verbose=False, quiet=True):
    """
    Play a single game with the given solver and secret word.
    Returns game statistics.
    """
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
        # Reset solver-specific state if available
        if hasattr(solver, 'reset'):
            solver.reset()
    
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
    Includes memory tracking.
    """
    print(f"\n{'='*60}")
    print(f"Testing {solver_name}")
    print(f"{'='*60}")
    
    # Start memory tracking
    tracemalloc.start()
    
    # Create game and solver once, reuse for all tests
    game = WordleGame()
    game.max_attempts = 20
    solver = solver_class(game)
    
    # Measure initial memory after solver creation
    current, peak_init = tracemalloc.get_traced_memory()
    init_memory_mb = peak_init / 1024 / 1024
    
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
    
    # Get peak memory usage
    current, peak = tracemalloc.get_traced_memory()
    peak_memory_mb = peak / 1024 / 1024
    tracemalloc.stop()
    
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
        'init_memory_mb': init_memory_mb,
        'peak_memory_mb': peak_memory_mb,
        'attempts_distribution': dict(attempts_distribution),
        'results': results,
        'avg_consistency_by_attempt': {k: (sum(v)/len(v) if v else 0) for k, v in per_attempt_consistency.items()}
    }
    
    return stats




def print_summary(all_stats):
    """Print comparison summary for all solvers."""
    print(f"\n{'='*80}")
    print("SUMMARY COMPARISON - ALL SOLVERS")
    print(f"{'='*80}")
    
    # Header
    header = f"{'Metric':<25}"
    for stats in all_stats:
        header += f"{stats['solver']:<14}"
    print(header)
    print("-" * 80)
    
    # Metrics rows
    metrics = [
        ('Total Games', 'total_games', '{:<14}'),
        ('Wins', 'wins', '{:<14}'),
        ('Losses', 'losses', '{:<14}'),
        ('Win Rate (%)', 'win_rate', '{:<14.2f}'),
        ('Avg Attempts', 'avg_attempts', '{:<14.2f}'),
        ('Avg Nodes', 'avg_nodes_visited', '{:<14.1f}'),
        ('Avg Time/Game (s)', 'avg_time_per_game', '{:<14.4f}'),
        ('Total Time (s)', 'total_time', '{:<14.2f}'),
        ('Init Memory (MB)', 'init_memory_mb', '{:<14.1f}'),
        ('Peak Memory (MB)', 'peak_memory_mb', '{:<14.1f}'),
    ]
    
    for label, key, fmt in metrics:
        row = f"{label:<25}"
        for stats in all_stats:
            value = stats.get(key, 0)
            row += fmt.format(value)
        print(row)
    
    # Print attempts distribution for each solver
    for stats in all_stats:
        print(f"\n{'Attempts Distribution'} ({stats['solver']}):")
        dist = stats['attempts_distribution']
        for attempt in sorted([k for k in dist.keys() if k != 'failed']):
            count = dist[attempt]
            pct = count / stats['total_games'] * 100
            bar = '█' * int(pct / 2)
            print(f"  {attempt} attempts: {count:>4} ({pct:>5.1f}%) {bar}")
        if 'failed' in dist:
            count = dist['failed']
            pct = count / stats['total_games'] * 100
            print(f"  Failed:    {count:>4} ({pct:>5.1f}%)")


def print_memory_comparison(all_stats):
    """Print memory usage comparison."""
    print(f"\n{'='*60}")
    print("MEMORY USAGE COMPARISON")
    print(f"{'='*60}")
    
    # Sort by peak memory
    sorted_stats = sorted(all_stats, key=lambda x: x['peak_memory_mb'])
    
    print(f"{'Solver':<20} {'Init (MB)':<12} {'Peak (MB)':<12} {'Delta (MB)':<12}")
    print("-" * 56)
    
    for stats in sorted_stats:
        init_mem = stats['init_memory_mb']
        peak_mem = stats['peak_memory_mb']
        delta = peak_mem - init_mem
        print(f"{stats['solver']:<20} {init_mem:<12.1f} {peak_mem:<12.1f} {delta:<12.1f}")


def print_performance_ranking(all_stats):
    """Print performance rankings."""
    print(f"\n{'='*60}")
    print("PERFORMANCE RANKINGS")
    print(f"{'='*60}")
    
    # Rank by win rate
    print("\nBy Win Rate (highest first):")
    sorted_by_wins = sorted(all_stats, key=lambda x: x['win_rate'], reverse=True)
    for i, stats in enumerate(sorted_by_wins, 1):
        print(f"  {i}. {stats['solver']:<20} {stats['win_rate']:.2f}%")
    
    # Rank by avg attempts (lower is better)
    print("\nBy Avg Attempts (lowest first):")
    sorted_by_attempts = sorted(all_stats, key=lambda x: x['avg_attempts'])
    for i, stats in enumerate(sorted_by_attempts, 1):
        print(f"  {i}. {stats['solver']:<20} {stats['avg_attempts']:.2f}")
    
    # Rank by speed (fastest first)
    print("\nBy Speed (fastest first):")
    sorted_by_time = sorted(all_stats, key=lambda x: x['avg_time_per_game'])
    for i, stats in enumerate(sorted_by_time, 1):
        print(f"  {i}. {stats['solver']:<20} {stats['avg_time_per_game']:.4f}s/game")
    
    # Rank by memory (lowest first)
    print("\nBy Memory (lowest first):")
    sorted_by_mem = sorted(all_stats, key=lambda x: x['peak_memory_mb'])
    for i, stats in enumerate(sorted_by_mem, 1):
        print(f"  {i}. {stats['solver']:<20} {stats['peak_memory_mb']:.1f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="Compare Wordle solvers: DFS, KB-HillClimb, Entropy, ProgEntropy"
    )
    parser.add_argument("--limit", type=int, default=None, 
                        help="Limit number of games to test (for quick testing)")
    parser.add_argument("--verbose", action="store_true", 
                        help="Print detailed game logs")
    parser.add_argument("--output", type=str, default="solver_comparison.json", 
                        help="Output JSON file for detailed results")
    parser.add_argument("--seed", type=int, default=None, 
                        help="Random seed for shuffling test order")
    parser.add_argument("--solvers", type=str, default=None,
                        help="Comma-separated list of solvers to test (dfs,kb,entropy,prog)")
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
    
    # Determine which solvers to run
    solvers_to_run = SOLVERS
    if args.solvers:
        solver_map = {
            'dfs': ("DFS", DFSSolver),
            'kb': ("KB-HillClimb", KnowledgeBasedHillClimbingSolver),
            'entropy': ("Entropy", EntropySolver),
            'prog': ("ProgEntropy", ProgressiveEntropySolver),
            'hybrid': ("HybridProgEntropy", HybridProgressiveEntropySolver)
        }
        requested = [s.strip().lower() for s in args.solvers.split(',')]
        solvers_to_run = [solver_map[s] for s in requested if s in solver_map]
    
    print(f"\nSolvers to compare: {[s[0] for s in solvers_to_run]}")
    
    # Run benchmarks for all solvers
    all_stats = []
    quiet = not args.verbose
    
    for solver_name, solver_class in solvers_to_run:
        stats = run_solver_benchmark(
            solver_class, solver_name, secret_words, 
            verbose=args.verbose, quiet=quiet
        )
        all_stats.append(stats)
    
    # Print summaries
    print_summary(all_stats)
    print_memory_comparison(all_stats)
    print_performance_ranking(all_stats)
    
    # Save detailed results
    output_data = {
        'config': {
            'total_games': len(secret_words),
            'solvers': [s['solver'] for s in all_stats],
        },
        'results': {s['solver']: s for s in all_stats},
        'rankings': {
            'by_win_rate': [s['solver'] for s in sorted(all_stats, key=lambda x: x['win_rate'], reverse=True)],
            'by_avg_attempts': [s['solver'] for s in sorted(all_stats, key=lambda x: x['avg_attempts'])],
            'by_speed': [s['solver'] for s in sorted(all_stats, key=lambda x: x['avg_time_per_game'])],
            'by_memory': [s['solver'] for s in sorted(all_stats, key=lambda x: x['peak_memory_mb'])],
        }
    }
    
    # Remove detailed game-by-game results to keep file size manageable
    for solver_stats in output_data['results'].values():
        solver_stats.pop('results', None)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Detailed results saved to: {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()