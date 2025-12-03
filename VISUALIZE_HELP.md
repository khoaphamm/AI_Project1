# Manim Wordle Visualization Guide

This guide will help you generate and run the interactive slideshow visualizations for the Wordle solver algorithms using the Manim library.

## 1. Prerequisites

Before starting, ensure you have Python installed (best if use .env). You will need to install the following libraries via your terminal or command prompt:

```bash
pip install manim manim-slides PyQt6
```

*   `manim`: The mathematical animation engine (developed by 3Blue1Brown).
*   `manim-slides`: A plugin to convert animations into interactive presentations.
*   `PyQt6`: The GUI backend required for the slide viewer window.

---

## 2. Rendering the Slides

Run the following commands in your terminal to render the video files for each algorithm.
(if they don't exist in the directory (/media, /slides) --> run to generate)

*   **-ql**: Quality Low (480p). Use this for fast testing and debugging.
*   **-qh**: Quality High (1080p). Use this for the final presentation.

### DFS Solver
```bash
manim -qh dfs_slideshow.py WordleDFSSlides
```

### Hill Climbing Solver
```bash
manim -qh hill_climbing_slideshow.py WordleHillClimbingSlides
```

### Full Entropy Solver
```bash
manim -qh full_entropy_slideshow.py WordleFullEntropySlides
```

### Progressive Entropy Solver
```bash
manim -qh progressive_entropy_slideshow.py WordleProgressiveEntropySlides
```

---

## 3. Running the Presentation

Once rendering is complete, use the `manim-slides` command followed by the **Class Name** of the scene you want to present.

**DFS:**
```bash
manim-slides WordleDFSSlides
```

**Hill Climbing:**
```bash
manim-slides WordleHillClimbingSlides
```

**Full Entropy:**
```bash
manim-slides WordleFullEntropySlides
```

**Progressive Entropy:**
```bash
manim-slides WordleProgressiveEntropySlides
```

---

## 4. Presentation Controls

When the slide window opens:

*   ➡️ **RIGHT ARROW / SPACEBAR**: Play the next animation step.
*   ⬅️ **LEFT ARROW**: Reverse to the previous animation step.
*   **F**: Toggle Fullscreen.
*   **Q**: Quit the presentation.

---

## 5. Troubleshooting

### `qtpy.QtBindingsNotFoundError: No Qt bindings could be found`
This means the GUI library is missing. Install it by running:
```bash
pip install PyQt6
```

### `AttributeError: 'str' object has no attribute 'to_hex'`
This is a compatibility issue with some versions of Manim when setting background colors inside the `construct` method.
**Fix:** Ensure the background color is set globally at the very top of your Python script (before the class definition):
```python
config.background_color = "#1e1e1e"
```

### `Error: File slides\....json does not exist`
This means the rendering step failed. Scroll up in your terminal to see the Python error message, fix the script, and run the `manim -qh ...` command again before trying `manim-slides`.
```