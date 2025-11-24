# """
# Demonstration of Trie-based Search for Wordle

# This script visualizes how BFS and DFS traverse the Trie structure
# to find valid Wordle words.
# """

# from trie.trie_structure import WordleTrie
# from game.wordle_logic import WordleGame

# def demonstrate_trie_structure():
#     """Show how the Trie is structured."""
#     print("=" * 60)
#     print("WORDLE TRIE STRUCTURE DEMONSTRATION")
#     print("=" * 60)
    
#     # Create a small example trie
#     small_words = ['apple', 'apply', 'ample', 'aptly', 'arise', 'bread', 'break']
#     trie = WordleTrie(small_words)
    
#     print(f"\nBuilt trie with words: {small_words}")
#     print(f"\nTrie Statistics:")
#     stats = trie.get_statistics()
#     for key, value in stats.items():
#         print(f"  {key}: {value}")
    
#     print("\n" + "-" * 60)
#     print("TRIE STRUCTURE:")
#     print("-" * 60)
#     print("""
#     ROOT ('')
#     ├── 'a' (depth 1)
#     │   ├── 'p' (depth 2)
#     │   │   ├── 'p' (depth 3)
#     │   │   │   ├── 'l' (depth 4)
#     │   │   │   │   ├── 'e' (depth 5) → 'apple' [LEAF→GOAL]
#     │   │   │   │   └── 'y' (depth 5) → 'apply' [LEAF→GOAL]
#     │   │   │   └── 't' (depth 4)
#     │   │   │       └── 'l' (depth 5)
#     │   │   │           └── 'y' → 'aptly' [LEAF→GOAL]
#     │   │   └── 'm' (depth 3)
#     │   │       └── 'p' (depth 4)
#     │   │           └── 'l' (depth 5)
#     │   │               └── 'e' → 'ample' [LEAF→GOAL]
#     │   └── 'r' (depth 2)
#     │       └── 'i' (depth 3)
#     │           └── 's' (depth 4)
#     │               └── 'e' (depth 5) → 'arise' [LEAF→GOAL]
#     └── 'b' (depth 1)
#         └── 'r' (depth 2)
#             └── 'e' (depth 3)
#                 └── 'a' (depth 4)
#                     ├── 'd' (depth 5) → 'bread' [LEAF→GOAL]
#                     └── 'k' (depth 5) → 'break' [LEAF→GOAL]
    
#     All LEAF nodes (depth 5) connect to virtual GOAL node
#     """)
    
#     print("-" * 60)
#     print("SEARCH MECHANICS:")
#     print("-" * 60)
#     print("""
#     START NODE: ROOT (empty string '')
#     TRANSITIONS: Add one letter at a time (traverse down)
#     GOAL TEST: Check if 5-letter word (leaf) satisfies constraints
    
#     BFS Order (level by level):
#       1. All depth-1 nodes: a, b, c, ...
#       2. All depth-2 nodes: aa, ab, ac, ..., ba, bb, ...
#       3. Continue until depth 5 (complete words)
    
#     DFS Order (depth-first):
#       1. Dive deep on first branch: a→p→p→l→e (apple)
#       2. Backtrack and try: a→p→p→l→y (apply)
#       3. Continue exploring all paths to depth 5
#     """)

# def demonstrate_search_with_constraints():
#     """Show how search works with Wordle constraints."""
#     print("\n" + "=" * 60)
#     print("SEARCH WITH CONSTRAINTS DEMONSTRATION")
#     print("=" * 60)
    
#     # Load full word list
#     game = WordleGame()
#     trie = WordleTrie(list(game.allowed_words))
    
#     print(f"\nFull trie built with {trie.word_count} words")
    
#     # Example: Find a word that starts with 'cr'
#     print("\n" + "-" * 60)
#     print("Example 1: Find words starting with 'cr'")
#     print("-" * 60)
    
#     cr_words = trie.get_words_with_prefix('cr')
#     print(f"Found {len(cr_words)} words")
#     print(f"First 10: {cr_words[:10]}")
    
#     # Example: Search for a specific word
#     print("\n" + "-" * 60)
#     print("Example 2: BFS to find first word alphabetically")
#     print("-" * 60)
    
#     def first_word_goal(word):
#         """Goal: just return the first word found (alphabetically first in BFS)"""
#         return True  # Accept first word found
    
#     path, word, nodes = trie.bfs_search(first_word_goal)
#     print(f"BFS found: '{word}' after visiting {nodes} nodes")
    
#     # Example: DFS search
#     print("\n" + "-" * 60)
#     print("Example 3: DFS to find first word (different from BFS)")
#     print("-" * 60)
    
#     path, word, nodes = trie.dfs_search(first_word_goal)
#     print(f"DFS found: '{word}' after visiting {nodes} nodes")
    
#     # Example: Search with constraint (word contains 'xyz')
#     print("\n" + "-" * 60)
#     print("Example 4: Find word containing all letters: a, e, r")
#     print("-" * 60)
    
#     def contains_aer(word):
#         """Goal: word must contain a, e, and r"""
#         return 'a' in word and 'e' in word and 'r' in word
    
#     path, word, nodes = trie.bfs_search(contains_aer)
#     print(f"BFS found: '{word}' after visiting {nodes} nodes")
    
#     path, word, nodes = trie.dfs_search(contains_aer)
#     print(f"DFS found: '{word}' after visiting {nodes} nodes")
#     print(f"(Note: BFS and DFS may find different words)")

# def demonstrate_wordle_solving():
#     """Show how the trie is used for actual Wordle solving."""
#     print("\n" + "=" * 60)
#     print("WORDLE SOLVING WITH TRIE")
#     print("=" * 60)
    
#     game = WordleGame(secret_word='crane')
#     trie = WordleTrie(list(game.allowed_words))
    
#     print(f"\nSecret word (for demo): '{game.secret_word}'")
#     print("Let's simulate some guesses and see how the search space shrinks\n")
    
#     # Simulate first guess
#     guess1 = 'soare'
#     feedback1 = game.evaluate_guess(guess1, 'crane')
#     print(f"Guess 1: {guess1}")
#     print(f"Feedback: {feedback1}")
    
#     # Find all words consistent with this feedback
#     def consistent_with_guess1(word):
#         simulated = game.evaluate_guess(guess1, word)
#         return simulated == feedback1
    
#     # Count consistent words
#     consistent_count = 0
#     for word in trie.get_all_words():
#         if consistent_with_guess1(word):
#             consistent_count += 1
    
#     print(f"Words consistent with feedback: {consistent_count}")
    
#     # Now BFS would search for one of these
#     path, word, nodes = trie.bfs_search(consistent_with_guess1)
#     print(f"BFS found consistent word: '{word}' (visited {nodes} nodes)")
    
#     print("\n" + "=" * 60)

# if __name__ == "__main__":
#     demonstrate_trie_structure()
#     demonstrate_search_with_constraints()
#     demonstrate_wordle_solving()
    
#     print("\n" + "=" * 60)
#     print("KEY CONCEPTS:")
#     print("=" * 60)
#     print("""
#     ✓ Trie represents the search space hierarchically
#     ✓ Root = empty string (starting state)
#     ✓ Each edge = transition (add one letter)
#     ✓ Depth 5 nodes = complete 5-letter words (leaves)
#     ✓ All leaves connect to virtual GOAL node
#     ✓ BFS explores breadth-first (level by level)
#     ✓ DFS explores depth-first (one path at a time)
#     ✓ Goal test = word satisfies Wordle constraints
#     """)
#     print("=" * 60)
