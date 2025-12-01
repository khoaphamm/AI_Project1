"""
Flask Web Application for Wordle AI Visualizer
Modern web-based UI for the Wordle AI game
"""

from flask import Flask, render_template, jsonify, request
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.wordle_logic import WordleGame, MISS, MISPLACED, EXACT
from algorithms.solvers import DFSSolver, EntropySolver, KnowledgeBasedHillClimbingSolver, ProgressiveEntropySolver

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wordle-ai-visualizer-secret'

# Game state (in production, use sessions or database)
game_sessions = {}
current_session_id = 'default'


def get_solver_class(solver_name):
    """Get solver class by name"""
    solvers = {
        'dfs': DFSSolver,
        'entropy': EntropySolver,
        'kbhillclimbing': KnowledgeBasedHillClimbingSolver,
        'progressive': ProgressiveEntropySolver
    }
    return solvers.get(solver_name.lower(), DFSSolver)


def get_or_create_session():
    """Get or create game session"""
    if current_session_id not in game_sessions:
        game_sessions[current_session_id] = {
            'game': WordleGame(),
            'solver': None,
            'auto_play': False
        }
    return game_sessions[current_session_id]


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_game():
    """Start a new game with specified solver and mode"""
    try:
        data = request.json
        solver_name = data.get('solver', 'dfs')
        auto_play = data.get('auto_play', False)
        
        solver_class = get_solver_class(solver_name)
        
        # Check if we have an existing session we can reuse
        existing_session = game_sessions.get(current_session_id)
        
        if existing_session and existing_session.get('solver') is not None:
            existing_solver = existing_session['solver']
            # If same solver type, just reset instead of recreating
            if isinstance(existing_solver, solver_class):
                game = existing_session['game']
                solver = existing_solver
                
                # Reset game and solver state
                game.reset()
                solver.reset()
                
                # Initialize the solver's trie with all words
                solver._update_trie([])
                
                # Update auto_play setting
                existing_session['auto_play'] = auto_play
                
                print(f"Reusing existing {solver_name} solver (reset)")
                
                return jsonify({
                    'success': True,
                    'solver': solver_name,
                    'auto_play': auto_play,
                    'attempts': len(game.attempts),
                    'remaining_words': len(solver.currently_consistent_words) if hasattr(solver, 'currently_consistent_words') else None,
                    'nodes_visited': 0
                })

        # Create new game only if no existing session or different solver type
        if existing_session and existing_session.get('game') is not None:
            # Reuse existing game, just reset it
            game = existing_session['game']
            game.reset()
            print("Reusing existing game instance (reset)")
        else:
            # First time - create new game
            game = WordleGame()
            print("Created new game instance")
        
        # Create new solver for the (possibly reused) game
        solver = solver_class(game)
        
        # Initialize the solver's trie with all words
        solver._update_trie([])

        # Store in session
        game_sessions[current_session_id] = {
            'game': game,
            'solver': solver,
            'auto_play': auto_play
        }

        return jsonify({
            'success': True,
            'solver': solver_name,
            'auto_play': auto_play,
            'attempts': len(game.attempts),
            'remaining_words': len(solver.currently_consistent_words) if hasattr(solver, 'currently_consistent_words') else None,
            'nodes_visited': 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/make_move', methods=['POST'])
def make_move():
    """Make an AI move"""
    try:
        session = get_or_create_session()
        game = session['game']
        solver = session['solver']

        if not solver:
            return jsonify({'success': False, 'error': 'No game started'}), 400

        if game.game_over:
            return jsonify({'success': False, 'error': 'Game is over'}), 400

        # Get AI guess
        guess = solver.pick_guess(game.attempts)

        # Make the guess
        success, result = game.make_guess(guess)

        if not success:
            return jsonify({'success': False, 'error': 'Invalid guess'}), 400

        # Decode feedback
        feedback = game.decode_feedback(result)

        return jsonify({
            'success': True,
            'guess': guess,
            'feedback': feedback,
            'attempts': len(game.attempts),
            'game_over': game.game_over,
            'won': game.won,
            'secret_word': game.secret_word if game.game_over else None,
            'remaining_words': len(solver.currently_consistent_words) if hasattr(solver, 'currently_consistent_words') else None,
            'nodes_visited': solver.search_stats[-1].get('nodes_visited', 0) if hasattr(solver, 'search_stats') and solver.search_stats else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/player_guess', methods=['POST'])
def player_guess():
    """Make a player guess"""
    try:
        data = request.json
        word = data.get('word', '').lower()

        session = get_or_create_session()
        game = session['game']
        solver = session['solver']

        if not solver:
            return jsonify({'success': False, 'error': 'No game started'}), 400

        if game.game_over:
            return jsonify({'success': False, 'error': 'Game is over'}), 400

        # Make the guess
        success, result = game.make_guess(word)

        if not success:
            return jsonify({'success': False, 'message': 'Invalid word'}), 400

        # Update solver with the new guess
        solver._update_trie(game.attempts)

        # Decode feedback
        feedback = game.decode_feedback(result)

        return jsonify({
            'success': True,
            'guess': word,
            'feedback': feedback,
            'attempts': len(game.attempts),
            'game_over': game.game_over,
            'won': game.won,
            'secret_word': game.secret_word if game.game_over else None,
            'remaining_words': len(solver.currently_consistent_words) if hasattr(solver, 'currently_consistent_words') else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get word suggestions for hint mode"""
    try:
        session = get_or_create_session()
        solver = session['solver']

        if not solver:
            return jsonify({'success': False, 'error': 'No game started'}), 400

        # Get suggestions
        if hasattr(solver, 'get_all_suggestions'):
            suggestions = solver.get_all_suggestions()[:50]  # Limit to top 50
        elif hasattr(solver, 'currently_consistent_words'):
            suggestions = [(word, 0.0) for word in solver.currently_consistent_words[:50]]
        else:
            suggestions = []

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/state', methods=['GET'])
def get_state():
    """Get current game state"""
    try:
        session = get_or_create_session()
        game = session['game']
        solver = session['solver']

        return jsonify({
            'success': True,
            'attempts': len(game.attempts),
            'game_over': game.game_over,
            'won': game.won,
            'history': [(guess, game.decode_feedback(feedback)) for guess, feedback in game.attempts],
            'remaining_words': len(solver.currently_consistent_words) if solver and hasattr(solver, 'currently_consistent_words') else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("🎮 Starting Wordle AI Visualizer Web Server...")
    print("📍 Open your browser to: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
