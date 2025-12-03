# Wordle Game - Trie-Based Search

A Python implementation of Wordle with AI solvers using Trie data structure and search algorithms (BFS/DFS).

## How to Run

**Play the game (web app):**
```powershell
python web/app.py
```
This launches the web-based Wordle app defined in `web/app.py`. The application will start on `http://localhost:5001`.

## Note

Please install all the requirements from requirements.txt beforehand:

```bash
pip install requirements.txt
```

Before running any AI algorithms, we need to check if the pattern matrix npy file exists: data/full_pattern_matrix.npy
If it has not existed, then run:
```bash
python data/generate_full_matrix.py
```

## Rules

- Guess the 5-letter word in 6 attempts
- 🟩 Green = correct letter, correct position
- 🟨 Yellow = correct letter, wrong position  
- ⬛ Gray = letter not in word


## For Developers:

Please add more solvers in solvers.py 