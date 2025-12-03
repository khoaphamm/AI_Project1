from manim import *
from manim_slides import Slide
import random
import numpy as np

config.background_color = "#1e1e1e"

class WordleProgressiveEntropySlides(Slide):
    def construct(self):
        title = Text("Progressive Entropy: Monte Carlo Sampling", font_size=36).to_edge(UP)
        self.play(Write(title))
        
        y_offset = -0.5
        
        # Root node
        root = Circle(radius=0.4, color=WHITE, fill_opacity=1, fill_color=BLACK).move_to([0, 3 + y_offset, 0])
        root_txt = Text("Root", font_size=20).move_to(root)
        
        self.play(FadeIn(root), Write(root_txt))
        
        # Child nodes (representing next character choices)
        children_pos = {
            "c1": [-3, 1 + y_offset, 0],
            "c2": [-1, 1 + y_offset, 0],
            "c3": [1, 1 + y_offset, 0],
            "c4": [3, 1 + y_offset, 0]
        }
        
        nodes = {}
        lines = VGroup()
        
        for k, pos in children_pos.items():
            c = Circle(radius=0.4, color=BLUE, fill_opacity=1, fill_color=BLACK).move_to(pos)
            # "?" indicates entropy is unknown and needs estimation
            t = Text("?", font_size=24).move_to(pos)
            nodes[k] = VGroup(c, t)
            lines.add(Line(root.get_center(), c.get_center(), color=GRAY).scale(0.8))
            
        self.play(Create(lines), FadeIn(VGroup(*nodes.values())))
        
        expl = Text("Idea: Estimate entropy by sampling 's' random words.", font_size=24, color=YELLOW).to_edge(DOWN)
        self.play(Write(expl))
        
        self.next_slide()
        
        # 2. Sampling Animation
        # We visualize 'particles' flowing from Root to C2 to represent sampling
        target_node = nodes["c2"]
        
        sampling_lbl = Text("Sampling s=50...", font_size=20, color=BLUE).next_to(target_node, UP)
        self.play(Write(sampling_lbl))
        
        particles = VGroup()
        for _ in range(15):
            d = Dot(color=YELLOW, radius=0.06).move_to(root.get_center())
            # Random jitter at destination
            dest = target_node.get_center() + np.array([random.uniform(-0.3,0.3), random.uniform(-0.3,0.3), 0])
            particles.add(d)
            self.play(d.animate.move_to(dest), run_time=0.05)
            
        self.play(FadeOut(particles), FadeOut(sampling_lbl))
        
        # Update value for C2
        self.play(target_node[1].animate.become(Text("4.8", font_size=20).move_to(target_node.get_center())))
        
        # Quickly reveal others
        self.play(
            nodes["c1"][1].animate.become(Text("2.1", font_size=20).move_to(nodes["c1"].get_center())),
            nodes["c3"][1].animate.become(Text("3.5", font_size=20).move_to(nodes["c3"].get_center())),
            nodes["c4"][1].animate.become(Text("1.9", font_size=20).move_to(nodes["c4"].get_center()))
        )
        
        self.next_slide()
        
        # 3. Selection
        self.play(Transform(expl, Text("Select path with Highest Estimated Entropy", font_size=24, color=GREEN).to_edge(DOWN)))
        
        self.play(
            target_node[0].animate.set_color(GREEN),
            nodes["c1"].animate.set_opacity(0.3),
            nodes["c3"].animate.set_opacity(0.3),
            nodes["c4"].animate.set_opacity(0.3)
        )
        
        # Zoom in/Reset for next depth
        self.play(
            FadeOut(lines), FadeOut(root), FadeOut(root_txt),
            FadeOut(nodes["c1"]), FadeOut(nodes["c3"]), FadeOut(nodes["c4"]),
            target_node.animate.move_to([0, 3 + y_offset, 0])
        )
        
        self.play(Write(Text("Repeat...", font_size=24).next_to(target_node, RIGHT)))
        
        self.next_slide()