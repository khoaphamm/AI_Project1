import argparse
import json
import os
import random
import subprocess
import sys
import time

# Ensure project root on sys.path so `data` and `game` imports work when running from tests/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data import paths


def _load_word_lists_from_txt():
    """Load word lists from text files (memory efficient, no matrix load)."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    allowed_path = os.path.join(here, paths.ALLOWED_WORDS)
    possible_path = os.path.join(here, paths.POSSIBLE_WORDS)

    if not os.path.exists(allowed_path) or not os.path.exists(possible_path):
        raise SystemExit("Word list files not found.")

    with open(allowed_path, "r", encoding="utf-8") as f:
        guesses = [line.strip().lower() for line in f if len(line.strip()) == 5]
    
    with open(possible_path, "r", encoding="utf-8") as f:
        secrets = [line.strip().lower() for line in f if len(line.strip()) == 5]

    if not guesses or not secrets:
        raise SystemExit("Word lists are empty.")

    return guesses, secrets


def _load_word_lists_from_matrix():
    """Load word lists from matrix JSON (only for lookup worker that needs matrix anyway)."""
    matrix_path = paths.MATRIX_PATH
    matrix_abs = matrix_path
    if not os.path.isabs(matrix_abs):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        matrix_abs = os.path.join(here, matrix_path)

    if not os.path.exists(matrix_abs):
        raise SystemExit("Matrix not found. Run `python generate_matrix.py` first.")

    with open(matrix_abs, "r", encoding="utf-8") as f:
        data = json.load(f)

    guesses = data["allowed_words"]
    secrets = data["possible_words"]

    if not guesses or not secrets:
        raise SystemExit("Matrix contains empty word lists.")

    return guesses, secrets


def worker_lookup(num_pairs: int, seed: int):
    from game.wordle_logic import WordleGame

    game = WordleGame()
    if not game.matrix_data:
        print(json.dumps({"mode": "lookup", "error": "matrix_not_loaded"}))
        return

    # Use matrix-based word lists since we already loaded the matrix
    guesses, secrets = _load_word_lists_from_matrix()
    rng = random.Random(seed)
    eval_fn = game.evaluate_guess

    t0 = time.perf_counter()
    for _ in range(num_pairs):
        g_idx = rng.randint(0, len(guesses) - 1)
        s_idx = rng.randint(0, len(secrets) - 1)
        _ = eval_fn(guesses[g_idx], secret_word=secrets[s_idx])
    t1 = time.perf_counter()

    print(json.dumps({"mode": "lookup", "seconds": t1 - t0, "pairs": num_pairs}))


def worker_manual(num_pairs: int, seed: int):
    # Avoid loading matrix entirely by monkeypatching before instantiation
    from game.wordle_logic import WordleGame

    def _no_load_matrix(self, path):
        self.matrix_data = None
        self.secret_map = {}
        self.guess_map = {}

    WordleGame.load_matrix = _no_load_matrix  # type: ignore[attr-defined]

    game = WordleGame()
    # Load only lightweight text files (no 418MB JSON)
    guesses, secrets = _load_word_lists_from_txt()
    rng = random.Random(seed)
    eval_fn = game.evaluate_guess

    t0 = time.perf_counter()
    for _ in range(num_pairs):
        g_idx = rng.randint(0, len(guesses) - 1)
        s_idx = rng.randint(0, len(secrets) - 1)
        _ = eval_fn(guesses[g_idx], secret_word=secrets[s_idx])
    t1 = time.perf_counter()

    print(json.dumps({"mode": "manual", "seconds": t1 - t0, "pairs": num_pairs}))


def orchestrate(num_pairs: int, seed: int):
    # Launch lookup worker
    lookup_proc = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--mode", "lookup-worker", "--pairs", str(num_pairs), "--seed", str(seed)],
        capture_output=True,
        text=True,
    )
    # Launch manual worker
    manual_proc = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--mode", "manual-worker", "--pairs", str(num_pairs), "--seed", str(seed)],
        capture_output=True,
        text=True,
    )

    def _parse(out: subprocess.CompletedProcess):
        # Find last JSON line in stdout
        for line in (out.stdout or "").splitlines()[::-1]:
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    return json.loads(line)
                except Exception:
                    continue
        return {"error": "no_json", "stdout": out.stdout, "stderr": out.stderr}

    lookup_res = _parse(lookup_proc)
    manual_res = _parse(manual_proc)

    if "seconds" not in lookup_res or "seconds" not in manual_res:
        print("Lookup output:", lookup_res)
        print("Manual output:", manual_res)
        raise SystemExit("Failed to parse worker outputs.")

    lookup_sec = float(lookup_res["seconds"])
    manual_sec = float(manual_res["seconds"])
    speedup = manual_sec / lookup_sec if lookup_sec > 0 else float("inf")

    print("=== Wordle Feedback Benchmark (Fresh Processes) ===")
    print(f"Pairs: {num_pairs:,}")
    print(f"Lookup (matrix): {lookup_sec:.4f} s")
    print(f"Manual compute:  {manual_sec:.4f} s")
    print(f"Speedup (manual/lookup): {speedup:.2f}x")
def main():
    parser = argparse.ArgumentParser(description="Benchmark matrix lookup vs manual evaluation in fresh processes.")
    parser.add_argument("--pairs", type=int, default=1_000_000, help="Number of guess/secret pairs to evaluate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for pair generation")
    parser.add_argument("--mode", choices=["orchestrate", "lookup-worker", "manual-worker"], default="orchestrate")
    args = parser.parse_args()

    if args.mode == "lookup-worker":
        worker_lookup(num_pairs=args.pairs, seed=args.seed)
        return
    if args.mode == "manual-worker":
        worker_manual(num_pairs=args.pairs, seed=args.seed)
        return

    orchestrate(num_pairs=args.pairs, seed=args.seed)


if __name__ == "__main__":
    main()