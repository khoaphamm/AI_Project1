# Wordle AI Visualizer - Web Version

A modern, responsive web-based UI for the Wordle AI game using Flask, HTML, CSS, and JavaScript.

## Features

- 🎨 Modern, responsive design with Catppuccin color theme
- 🤖 Multiple AI solvers (DFS, Hill Climbing)
- 🎮 Two modes: Auto Play and Hint Only
- 📊 Real-time statistics and activity log
- 💡 Interactive word suggestions in hint mode
- 📱 Mobile-friendly responsive layout

## Installation

1. Install Flask (if not already installed):
```bash
pip install flask
```

Or install from requirements.txt:
```bash
pip install -r web/requirements.txt
```

## Running the Application

From the project root directory:

```bash
python web/app.py
```

Or from the web directory:

```bash
cd web
python app.py
```

The application will start on `http://localhost:5000`

Open your browser and navigate to the URL to play!

## How to Play

1. Click the **Menu** button to select a game mode:
   - **Auto Play**: Watch the AI solve the puzzle automatically
   - **Hint Only**: Get word suggestions and choose your own guesses

2. Choose your solver:
   - **DFS**: Depth-First Search algorithm
   - **Hill Climbing**: Hill Climbing optimization algorithm

3. In Hint mode:
   - Click on suggested words to make your guess
   - Watch the board update with colored feedback

4. Use the control buttons:
   - **Pause**: Pause auto-play mode
   - **Next Step**: Make the next AI move manually
   - **Restart**: Start a new game with the same settings

## Project Structure

```
web/
├── app.py                 # Flask backend server
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Styles and responsive design
    └── js/
        └── app.js        # Frontend JavaScript logic
```

## API Endpoints

- `POST /api/start` - Start a new game
- `POST /api/make_move` - Make an AI move
- `POST /api/player_guess` - Make a player guess
- `GET /api/suggestions` - Get word suggestions
- `GET /api/state` - Get current game state

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Design**: Catppuccin Macchiato color theme
- **Game Logic**: Existing Wordle game and solver classes

## Benefits Over Pygame Version

- ✅ Better responsive design
- ✅ Easier to maintain and modify
- ✅ Works on any device with a browser
- ✅ No pygame dependencies needed
- ✅ Cleaner, more modern UI
- ✅ Better accessibility
