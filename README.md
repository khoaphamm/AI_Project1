# Wordle Game - Trie-Based Search

A Python implementation of Wordle with AI solvers using Trie data structure and search algorithms (BFS/DFS).

## How to Run


**Play the game yourself:**
```bash
python -m game.game_console
```

**Watch AI solve with BFS/DFS on Trie:**

## Note
Before running any AI algorithms, we need to check if the pattern matrix npy file exists: data/full_pattern_matrix.
If it has not existed, then run:
```bash
python data/generate_full_matrix.py
```

Then, run the following command to let AI play:

```bash
python -m algorithms.AIconsole
```

**See Trie structure demonstration:**
```bash
python demo_trie.py
```

## Trie Representation

The Wordle search space is represented as a **Trie (prefix tree)**:

- **Start Node**: Empty string `''` (root)
- **Transitions**: Add one letter at a time (traverse down the trie)
- **Depth**: 0 (root) → 1 → 2 → 3 → 4 → 5 (complete words)
- **Goal Nodes**: All 5-letter words (leaf nodes at depth 5)
- **Search**: BFS and DFS traverse the trie to find valid words

### Structure Example
```
ROOT ('')
├── 'a' → 'p' → 'p' → 'l' → 'e' → GOAL ('apple')
├── 'a' → 'p' → 'p' → 'l' → 'y' → GOAL ('apply')
└── 'b' → 'r' → 'e' → 'a' → 'd' → GOAL ('bread')
```

## Search Algorithms

- **DFS (Depth-First Search)**: Explores one branch completely before backtracking
- **Knowledge Based Hill Climbing**: Use character frequency heuristic to improve quality of the guess
- **Full Entropy Solver**: Making guess based on the Entropy of each word's feedback distribution
- **Progressive Entropy Sampling**: Stochastic, speed-optimized version of the previous Entropy Solver

## Rules

- Guess the 5-letter word in 6 attempts
- 🟩 Green = correct letter, correct position
- 🟨 Yellow = correct letter, wrong position  
- ⬛ Gray = letter not in word


## For Developers:

Please add more solvers in solvers.py 
