"""
Trie Data Structure for Wordle Word Space Representation

The Trie represents the search space where:
- Root node = empty string ""
- Each edge = adding one letter to the prefix
- Leaf nodes (depth 5) = complete 5-letter words
- All leaf nodes connect to a virtual GOAL node
- Transitions: traversing down the trie by appending letters
"""

from collections import deque

class TrieNode:
    def __init__(self, char='', depth=0):
        self.char = char          # Character at this node
        self.depth = depth        # Depth in trie (0=root, 5=leaf)
        self.children = {}        # Maps char -> TrieNode
        self.is_word = False      # True if this node completes a valid word
        self.word = None          # The complete word if is_word=True
        
    def __repr__(self):
        return f"TrieNode(char='{self.char}', depth={self.depth}, is_word={self.is_word})"


class WordleTrie:
    """
    Trie structure for representing the Wordle search space.
    
    Structure:
    - Root (empty string) at depth 0
    - Level 1: All first letters (a, b, c, ...)
    - Level 2: All two-letter prefixes (aa, ab, ac, ...)
    - ...
    - Level 5: All five-letter words (leaves)
    - Virtual GOAL node that all leaves connect to
    """
    
    def __init__(self, word_list):
        """
        Build the trie from a list of 5-letter words.
        
        :param word_list: List of valid 5-letter words
        """
        self.root = TrieNode('', 0)  # Start node (empty string)
        self.word_count = 0
        self.leaf_nodes = []  # All complete words (connect to GOAL)
        
        # Build the trie
        for word in word_list:
            if len(word) == 5:
                self.insert(word)
    
    def insert(self, word):
        """
        Insert a 5-letter word into the trie.
        Each character is a transition (edge) down the trie.
        """
        word = word.lower()
        node = self.root
        
        for i, char in enumerate(word):
            depth = i + 1
            
            if char not in node.children:
                node.children[char] = TrieNode(char, depth)
            
            node = node.children[char]
        
        # Mark as complete word (leaf node)
        node.is_word = True
        node.word = word
        self.word_count += 1
        self.leaf_nodes.append(node)
    
    def search(self, word):
        """Check if a complete word exists in the trie."""
        node = self._traverse(word)
        return node is not None and node.is_word
    
    def starts_with(self, prefix):
        """Check if any word starts with this prefix."""
        return self._traverse(prefix) is not None
    
    
    def get_all_words(self):
        """Get all complete 5-letter words in the trie."""
        return [node.word for node in self.leaf_nodes]
    
    def get_words_with_prefix(self, prefix):
        """Get all words that start with the given prefix."""
        node = self._traverse(prefix)
        if node is None:
            return []
        
        # Collect all words in the subtree
        words = []
        self._collect_words(node, words)
        return words
    

    """ SEARCHING ALGORITHMS """
    
    def dfs_search(self):
        """
        Depth-First Search on the trie.
        
        Search process:
        1. Start at root (empty string)
        2. Dive deep down one branch before exploring siblings
        3. When reaching depth 5 (complete word), test if it reaches GOAL
        4. Backtrack if not found
        
        :return: (path, word) if found, else (None, None)
        """
        stack = [(self.root, [])]  # (node, path taken)
        nodes_visited = 0
        
        while stack:
            node, path = stack.pop()
            nodes_visited += 1
            
            # If we've reached a complete word (leaf node -> GOAL transition)
            if node.is_word:
                return path + [node.word], node.word, nodes_visited
            
            # Expand children in reverse order for DFS (so 'a' is processed last/deepest)
            for char, child in sorted(node.children.items(), reverse=True):
                new_path = path + [child.char] if node.depth > 0 else [child.char]
                stack.append((child, new_path))
        
        return None, None, nodes_visited
    

    """ STATISTICS AND VISUALIZATION """

    def get_statistics(self):
        """Get statistics about the trie structure."""
        stats = {
            'total_words': self.word_count,
            'total_nodes': self._count_nodes(self.root),
            'depth': 5,
            'leaf_nodes': len(self.leaf_nodes)
        }
        return stats

    def visualize_path(self, path):
        """
        Visualize a search path through the trie.
        
        :param path: List of characters/words forming the path
        :return: String representation
        """
        if not path:
            return "Empty path"
        
        visualization = "ROOT('')"
        current = ""
        
        for i, step in enumerate(path):
            if len(step) == 1:  # Character transition
                current += step
                visualization += f" -> '{current}'"
            else:  # Complete word
                visualization += f" -> GOAL('{step}')"
        
        return visualization

    """   HELPERS  """
    def _traverse(self, prefix):
        """Traverse the trie following the prefix. Return the node or None."""
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return None
            node = node.children[char]
        return node   
    
    def _count_nodes(self, node):
        """Count total nodes in the trie."""
        count = 1
        for child in node.children.values():
            count += self._count_nodes(child)
        return count

    def _collect_words(self, node, words):
        """Recursively collect all complete words from a subtree."""
        if node.is_word:
            words.append(node.word)
        
        for child in node.children.values():
            self._collect_words(child, words)

