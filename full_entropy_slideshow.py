from manim import *
from manim_slides import Slide

config.background_color = "#1e1e1e"

class WordleFullEntropySlides(Slide):
    def construct(self):
        title = Text("Full Entropy: Maximize Information Gain", font_size=36).to_edge(UP)
        self.play(Write(title))
        
        # 1. Visualization of Dictionary
        dict_rect = Rectangle(height=4, width=3, color=BLUE).to_edge(LEFT, buff=1)
        dict_label = Text("Candidate Words\nD_a", font_size=24).next_to(dict_rect, UP)
        
        # List of words
        words = VGroup(
            Text("ARISE", font_size=24),
            Text("ROUTE", font_size=24),
            Text("SHARE", font_size=24),
            Text("...", font_size=24),
            Text("ZEBRA", font_size=24)
        ).arrange(DOWN, buff=0.4).move_to(dict_rect)
        
        self.play(Create(dict_rect), Write(dict_label), Write(words))
        
        expl = Text("Step 1: Calculate Entropy H(F_g) for ALL words", font_size=24, color=YELLOW).to_edge(DOWN)
        self.play(Write(expl))
        
        self.next_slide()
        
        # 2. Calculation Visualization
        # Arrow scanning words
        arrow = Arrow(start=LEFT, end=RIGHT, color=YELLOW).next_to(words[0], LEFT)
        
        # Bar Chart area on right
        axes = Axes(
            x_range=[0, 5, 1], y_range=[0, 6, 1], 
            x_length=6, y_length=4,
            axis_config={"include_numbers": False}
        ).to_edge(RIGHT, buff=1)
        chart_label = Text("Entropy Value", font_size=24).next_to(axes, UP)
        
        self.play(Create(axes), Write(chart_label), FadeIn(arrow))
        
        # Example entropy values
        entropies = [4.1, 3.5, 5.2, 0, 2.8]
        bars = VGroup()
        
        for i, val in enumerate(entropies):
            if i == 3: continue # skip dots
            
            # Move arrow to current word
            self.play(arrow.animate.next_to(words[i], LEFT), run_time=0.2)
            
            # Grow bar
            bar = Rectangle(
                width=0.6, height=val * (4/6), # scale to axes height
                color=BLUE, fill_opacity=0.8
            )
            # Position: axes.c2p converts chart coords to screen coords
            bar.move_to(axes.c2p(i + 0.5, 0), aligned_edge=DOWN)
            
            val_lbl = Text(f"{val}", font_size=16).next_to(bar, UP, buff=0.1)
            
            self.play(GrowFromEdge(bar, DOWN), FadeIn(val_lbl), run_time=0.3)
            bars.add(bar)
            
        self.next_slide()
        
        # 3. Selection
        self.play(Transform(expl, Text("Step 2: Select word with MAXIMUM Entropy", font_size=24, color=GREEN).to_edge(DOWN)))
        
        # SHARE is index 2. Let's highlight it.
        # bars[0]=ARISE, bars[1]=ROUTE, bars[2]=SHARE
        winner_bar = bars[2]
        winner_word = words[2]
        
        self.play(
            winner_bar.animate.set_color(GREEN),
            winner_word.animate.set_color(GREEN).scale(1.2),
            Flash(winner_bar, color=GREEN)
        )
        
        self.next_slide()