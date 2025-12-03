from manim import *
from manim_slides import Slide

# --- FIX: Set background color globally ---
config.background_color = "#1e1e1e"

class WordleHillClimbingSlides(Slide):
    def construct(self):
        title = Text("Hill Climbing Solver: Greedy Local Search", font_size=36).to_edge(UP)
        self.play(Write(title))
        
        y_offset = -0.5
        
        # Structure representing steps in building a word: Root -> 1st Char -> 2nd Char...
        # We visualize building the word "SHARE"
        positions = {
            "root": [0, 3 + y_offset, 0],
            "s": [-2, 2 + y_offset, 0], "t": [2, 2 + y_offset, 0], # Options for 1st char
            "h": [-2, 1 + y_offset, 0], "l": [-0.5, 1 + y_offset, 0], # Options for 2nd char (given 'S')
            "a": [-2, 0 + y_offset, 0], 
            "r": [-3, -1 + y_offset, 0], 
            "e": [-3, -2 + y_offset, 0]
        }
        
        # Heuristic Scores (e.g., Frequency)
        scores = {
            "s": 0.85, "t": 0.40,
            "h": 0.92, "l": 0.33,
            "a": 0.88, 
            "r": 0.75, 
            "e": 1.00
        }

        # Create nodes
        nodes_mobj = {}
        for key, pos in positions.items():
            circle = Circle(radius=0.4, color=WHITE, fill_opacity=1, fill_color=BLACK).move_to(pos)
            char = "Root" if key == "root" else key.upper()
            text = Text(char, font_size=24).move_to(pos)
            
            if key != "root":
                score_val = scores.get(key, 0.0)
                # Label the heuristic score
                score_lbl = Text(f"H={score_val:.2f}", font_size=16, color=YELLOW).next_to(circle, RIGHT, buff=0.1)
                group = VGroup(circle, text, score_lbl)
            else:
                group = VGroup(circle, text)
                
            nodes_mobj[key] = group

        # Start at Root
        self.play(FadeIn(nodes_mobj["root"]))
        
        # Slide 1: Decision at Depth 1
        self.next_slide()
        
        expl = Text("Step 1: Evaluate heuristics for next character", font_size=24).to_edge(DOWN)
        self.play(Write(expl))
        
        # Show candidates 'S' and 'T'
        edge_s = Line(positions["root"], positions["s"], color=GRAY).scale(0.8)
        edge_t = Line(positions["root"], positions["t"], color=GRAY).scale(0.8)
        
        self.play(
            Create(edge_s), FadeIn(nodes_mobj["s"]),
            Create(edge_t), FadeIn(nodes_mobj["t"])
        )
        
        self.next_slide()

        # Highlight selection
        self.play(
            nodes_mobj["s"][0].animate.set_color(GREEN), # Circle turns green
            nodes_mobj["t"].animate.set_opacity(0.3),    # Other fades
            Transform(expl, Text("Select 'S' (Highest Heuristic)", font_size=24, color=GREEN).to_edge(DOWN))
        )
        
        # Slide 2: Decision at Depth 2
        self.next_slide()
        
        # Show candidates 'H' and 'L' under 'S'
        edge_h = Line(positions["s"], positions["h"], color=GRAY).scale(0.8)
        edge_l = Line(positions["s"], positions["l"], color=GRAY).scale(0.8)
        
        self.play(
            Create(edge_h), FadeIn(nodes_mobj["h"]),
            Create(edge_l), FadeIn(nodes_mobj["l"])
        )
        
        self.play(
            nodes_mobj["h"][0].animate.set_color(GREEN),
            nodes_mobj["l"].animate.set_opacity(0.3),
            Transform(expl, Text("Select 'H' (Highest Heuristic)", font_size=24, color=GREEN).to_edge(DOWN))
        )

        # Slide 3: Complete the word
        self.next_slide()
        
        # Fast forward remaining characters A -> R -> E
        path_rest = ["a", "r", "e"]
        prev_key = "h"
        
        for key in path_rest:
            node = nodes_mobj[key]
            edge = Line(positions[prev_key], positions[key], color=GRAY).scale(0.8)
            self.play(Create(edge), FadeIn(node), run_time=0.3)
            self.play(node[0].animate.set_color(GREEN), run_time=0.2)
            prev_key = key
            
        self.play(Transform(expl, Text("Constructed Guess: SHARE", font_size=30, color=YELLOW).to_edge(DOWN)))
        
        self.next_slide()