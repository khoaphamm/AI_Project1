# Tests

## Compare Solvers (DFS vs Hill Climbing)

```powershell
# Quick test (50 games)
python tests/compare_solvers.py --limit 50

# Full test (~2300 games)
python tests/compare_solvers.py

# Unlimited Wordle mode (no 6-guess limit)
python tests/compare_solvers.py --limit 50 --unlimited

# With verbose output
python tests/compare_solvers.py --limit 10 --verbose
```

**Result:**
```
============================================================
Metric                         DFS             Hill Climbing
------------------------------------------------------------
Total Games                    2309            2309
Wins                           1933            2123
Win Rate (%)                   83.72           91.94
Avg Attempts (when won)        4.97            4.53
Avg Nodes Visited              29.8            21.2
Avg Time/Game (s)              0.2723          0.1209
Total Time (s)                 628.84          279.18
```

---

## Evaluate Matrix Performance

```powershell
# Default (1M pairs)
python tests/evaluate.py

# Custom size
python tests/evaluate.py --pairs 100000
```

**Result:**
```
Pairs: 1,000,000
Lookup (matrix): 4.09 s
Manual compute:  7.68 s
Speedup: 1.88x
```
