from manim import *
from manim_slides import Slide

# --- FIX: Set background color globally to avoid the AttributeError ---
config.background_color = "#1e1e1e"

class WordleDFSSlides(Slide):
    def construct(self):
        # We don't need self.camera.background_color anymore since we set it globally
        
        # Title
        title = Text("DFS Solver: Trie Traversal", font_size=40).to_edge(UP)
        self.play(Write(title))
        
        # --- 1. Define Tree Structure ---
        y_offset = -0.5  
        
        positions = {
            "root": [0, 3 + y_offset, 0],
            "s": [-2, 2 + y_offset, 0],
            "h": [-2, 1 + y_offset, 0],
            "a": [-2, 0 + y_offset, 0],
            "r": [-3, -1 + y_offset, 0], 
            "e1": [-3, -2 + y_offset, 0], 
            "v": [-1, -1 + y_offset, 0], 
            "e2": [-1, -2 + y_offset, 0], 
            "t": [2, 2 + y_offset, 0],
            "r_right": [2, 1 + y_offset, 0],
            "a_right": [2, 0 + y_offset, 0]
        }
        
        labels = {
            "root": "Root", "s": "s", "h": "h", "a": "a", 
            "r": "r", "e1": "e", "v": "v", "e2": "e",
            "t": "t", "r_right": "r", "a_right": "a"
        }

        edges = [
            ("root", "s"), ("s", "h"), ("h", "a"),
            ("a", "r"), ("r", "e1"),
            ("a", "v"), ("v", "e2"),
            ("root", "t"), ("t", "r_right"), ("r_right", "a_right")
        ]

        nodes_mobj = {}
        edges_mobj = []
        
        for key, pos in positions.items():
            circle = Circle(radius=0.35, color=WHITE, fill_opacity=1, fill_color=BLACK)
            circle.move_to(pos)
            
            if key == "root":
                text = Text("Root", font_size=20).move_to(pos)
            else:
                text = Text(labels[key], font_size=24).move_to(pos)
            
            group = VGroup(circle, text)
            nodes_mobj[key] = group

        for start, end in edges:
            line = Line(positions[start], positions[end], color=GRAY, stroke_width=2).scale(0.8)
            edges_mobj.append(line)

        # --- 2. Animate Construction ---
        
        self.play(FadeIn(nodes_mobj["root"]))
        
        tree_group = VGroup(*[n for k, n in nodes_mobj.items() if k != "root"] + edges_mobj)
        self.play(Create(tree_group), run_time=1.5)
        
        depth_labels = VGroup()
        for i in range(5):
            lbl = Text(f"Depth {i+1}", font_size=16, color=GRAY)
            lbl.move_to([-5, (2 - i) + y_offset, 0])
            depth_labels.add(lbl)
        
        self.play(Write(depth_labels))
        
        self.next_slide() 
        
        # --- 3. Visualize DFS Algorithm ---
        
        explanation = Text(
            "DFS Logic: Traverse deep (lexicographical order)", 
            font_size=24, color=YELLOW
        ).to_edge(DOWN)
        self.play(Write(explanation))
        
        dfs_path_keys = ["root", "s", "h", "a", "r", "e1"]
        
        for i in range(len(dfs_path_keys)):
            current_key = dfs_path_keys[i]
            current_node = nodes_mobj[current_key]
            
            self.play(
                current_node[0].animate.set_fill(color=BLUE, opacity=0.5),
                current_node[0].animate.set_stroke(color=BLUE),
                run_time=0.5
            )
            
            if i < len(dfs_path_keys) - 1:
                next_key = dfs_path_keys[i+1]
                start_pos = positions[current_key]
                end_pos = positions[next_key]
                active_edge = Line(start_pos, end_pos, color=BLUE, stroke_width=4).scale(0.8)
                self.play(Create(active_edge), run_time=0.3)

        self.next_slide()

        # --- 4. Found Leaf Node ---
        
        leaf_node = nodes_mobj["e1"]
        
        self.play(
            Flash(leaf_node, color=GREEN, flash_radius=0.5),
            leaf_node[0].animate.set_fill(color=GREEN, opacity=0.8)
        )
        
        result_text = Text("Selected Guess: 'SHARE'", font_size=30, color=GREEN)
        result_text.next_to(explanation, UP)
        
        self.play(
            Transform(explanation, Text("First leaf node reached.", font_size=24, color=YELLOW).to_edge(DOWN)),
            Write(result_text)
        )
        
        ignore_group = VGroup(nodes_mobj["v"], nodes_mobj["e2"], nodes_mobj["t"], nodes_mobj["r_right"], nodes_mobj["a_right"])
        self.play(ignore_group.animate.set_opacity(0.2), run_time=1)
        
        self.next_slide()