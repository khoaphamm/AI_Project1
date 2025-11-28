# Algorithm Visualization Guide

## Overview

This enhanced Wordle AI Visualizer provides real-time visualization of how the AI algorithms make decisions, showing the search process, information theory concepts, and optimization strategies.

## Visualization Tabs

### 🌳 Decision Tree
**Purpose**: Shows the decision path the algorithm takes through the solution space.

**What you see**:
- **Root Node**: Starting point (all possible words)
- **Branch Nodes**: Each guess made by the algorithm
- **Connections**: Show the path of decision-making
- **Color Coding**:
  - Blue outline: Active nodes
  - Green fill: Winning guess
  - Gray fill: Intermediate guesses

**Insights**:
- Visualizes the depth-first search or hill climbing path
- Shows how many steps it took to solve
- Demonstrates the algorithm's decision sequence

### 📊 Entropy Chart
**Purpose**: Displays information gain from each guess using information theory concepts.

**What you see**:
- **Bar Chart**: Height represents information gained per guess
- **X-axis**: Each guess made (abbreviated to 3 letters)
- **Y-axis**: Information gain (bits of entropy reduced)
- **Blue bars**: Information gained by each guess

**Insights**:
- Higher bars = more informative guesses
- Shows which guesses were most effective at narrowing down possibilities
- Demonstrates optimal vs suboptimal guesses
- Based on the formula: `I = log2(N_before / N_after)` where N is number of possible words

### 🔍 Search Space
**Purpose**: Visualizes how the algorithm prunes the search space with each guess.

**What you see**:
- **Horizontal Bars**: Width represents remaining possible words
- **Color Progression**: 
  - Blue: Active searching
  - Green: Final guess/solution
- **Word Count**: Shows exact number of remaining possibilities

**Insights**:
- Dramatic reduction in search space with good guesses
- Shows exponential pruning with optimal strategies
- Visualizes the "narrowing down" process
- Start: ~12,953 possible words → End: 1 word

## Algorithm Comparison

### DFS (Depth-First Search)
- **Strategy**: Explores one path deeply before backtracking
- **Visualization Shows**: 
  - Linear path in decision tree
  - Consistent information gain in entropy chart
  - Steady pruning in search space
- **Best For**: Finding any valid solution quickly

### Hill Climbing
- **Strategy**: Always picks the locally best option (most frequent letters)
- **Visualization Shows**:
  - Greedy path selection in decision tree
  - Variable information gain (sometimes high, sometimes low)
  - Rapid initial pruning, then slower refinement
- **Best For**: Getting close to optimal solution fast

## Performance Metrics

### Nodes Visited
- Shows computational cost
- Lower = more efficient
- Displayed in stats panel

### Remaining Words
- Current size of solution space
- Should decrease each turn
- Target: 1 (solved)

### Attempts Count
- Number of guesses made
- Lower is better
- Max allowed: 6

## Tips for Demos

1. **Start with Auto Mode**: Watch the algorithm work automatically
2. **Compare Solvers**: Try both DFS and Hill Climbing on same word
3. **Use Hint Mode**: See suggested words ranked by algorithm
4. **Watch Visualizations**: Switch between tabs to see different aspects
5. **Pause and Step**: Use pause/next to examine each decision

## Technical Details

### Information Theory
The entropy calculations use Shannon's information theory:
- **Entropy**: Measures uncertainty in the system
- **Information Gain**: Reduction in entropy from a guess
- **Formula**: `H = -Σ p(x) * log2(p(x))`

### Search Space Pruning
- Uses feedback patterns (🟩🟨⬜) to eliminate impossible words
- Trie data structure for efficient filtering
- Average branching factor reduces exponentially

### Optimization Strategies
- **DFS**: Complete systematic exploration
- **Hill Climbing**: Heuristic-based greedy selection
- **Frequency Matrix**: Pre-computed letter position statistics

## Use Cases

### Educational
- Teach search algorithms
- Demonstrate information theory
- Show optimization techniques

### Research
- Compare algorithm performance
- Test heuristic improvements
- Analyze search efficiency

### Entertainment
- Watch AI solve puzzles
- Challenge the AI with hard words
- Learn optimal guessing strategies
