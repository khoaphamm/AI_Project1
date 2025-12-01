// Enhanced Wordle AI Visualizer - v2.1 with Toast Notifications and Chart.js
// Game state
let gameState = {
    solver: null,
    autoPlay: false,
    isPaused: false,
    gameStarted: false,
    currentRow: 0,
    attempts: [],
    gameOver: false,
    won: false,
    visualizationData: {
        tree: [],
        entropy: [],
        searchSpace: []
    }
};

// Visualization state
let currentVizTab = 'tree';
let vizCanvas, vizCtx;
let chartCanvas, activeChart;
let currentInput = '';

// API endpoints
const API_BASE = '';

// DOM elements
const pauseBtn = document.getElementById('pauseBtn');
const nextBtn = document.getElementById('nextBtn');
const restartBtn = document.getElementById('restartBtn');
const themeBtn = document.getElementById('themeBtn');
const algorithmSelector = document.getElementById('algorithmSelector');
const algorithmDropdown = document.getElementById('algorithmDropdown');
const gameBoard = document.getElementById('gameBoard');
const keyboard = document.getElementById('keyboard');
const suggestionsList = document.getElementById('suggestionsList');
const logContainer = document.getElementById('logContainer');
const toastContainer = document.getElementById('toastContainer');
const algorithmLoading = document.getElementById('algorithmLoading');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    initVisualization();
    addPhysicalKeyboardSupport();
    loadThemePreference();

    // Automatically load game on app entry
    initializeGame();
});

// Algorithm Loading Functions
let messageInterval = null;
const loadingMessages = [
    "Analyzing possibilities...",
    "Calculating entropy...",
    "Finding optimal move...",
    "Processing feedback...",
    "Narrowing word list..."
];

function showLoading() {
    if (algorithmLoading) {
        // Clear any existing intervals first
        if (messageInterval) {
            clearInterval(messageInterval);
            messageInterval = null;
        }

        // Hide result component
        hideResult();

        // Reset any previous Done state
        resetLoading();

        algorithmLoading.style.display = 'block';

        // Start cycling through messages
        const messageElement = document.getElementById('loadingMessage');
        let currentIndex = 0;

        if (messageElement) {
            messageElement.textContent = loadingMessages[currentIndex];
        }

        messageInterval = setInterval(() => {
            currentIndex = (currentIndex + 1) % loadingMessages.length;
            if (messageElement) {
                messageElement.textContent = loadingMessages[currentIndex];
            }
        }, 1500);

        console.log('Loading started with interval:', messageInterval); // Debug log
    }
}

function hideLoading() {
    if (algorithmLoading) {
        algorithmLoading.style.display = 'none';

        // Clear message cycling
        if (messageInterval) {
            clearInterval(messageInterval);
            messageInterval = null;
        }

        // Reset to first message
        const messageElement = document.getElementById('loadingMessage');
        if (messageElement) {
            messageElement.textContent = loadingMessages[0];
        }
    }
}

function showResult(message, details, type = 'success') {
    // Hide loading component
    hideLoading();

    // Show result component
    const resultPanel = document.getElementById('algorithmResult');
    const resultIcon = document.getElementById('resultIcon');
    const resultMessage = document.getElementById('resultMessage');
    const resultDetails = document.getElementById('resultDetails');

    if (resultPanel && resultIcon && resultMessage && resultDetails) {
        // Set icon and message based on type
        const icons = {
            success: '🎉',
            error: '❌',
            warning: '⚠️',
            stopped: '⏹️'
        };

        const classes = {
            success: 'result-success',
            error: 'result-error',
            warning: 'result-warning',
            stopped: 'result-success'
        };

        resultIcon.textContent = icons[type] || icons.success;
        resultMessage.textContent = message;
        resultDetails.textContent = details;

        // Apply styling
        resultMessage.className = `result-message ${classes[type]}`;

        // Show the result panel
        resultPanel.style.display = 'block';

        console.log('Result shown:', message, details, type);
    }
}

function hideResult() {
    const resultPanel = document.getElementById('algorithmResult');
    if (resultPanel) {
        resultPanel.style.display = 'none';
    }
}

function showPaused() {
    // Hide result component
    hideResult();

    // Show loading component with pause state
    const resultPanel = document.getElementById('algorithmResult');
    const resultIcon = document.getElementById('resultIcon');
    const resultMessage = document.getElementById('resultMessage');
    const resultDetails = document.getElementById('resultDetails');

    if (resultPanel && resultIcon && resultMessage && resultDetails) {
        resultIcon.textContent = '⏸️';
        resultMessage.textContent = 'Paused';
        resultDetails.textContent = 'Game is paused - click Resume to continue';

        // Apply neutral styling
        resultMessage.className = 'result-message result-success';

        // Show the result panel
        resultPanel.style.display = 'block';
    }
}

function resetLoading() {
    if (algorithmLoading) {
        const spinner = algorithmLoading.querySelector('.loading-spinner');
        const messageElement = document.getElementById('loadingMessage');

        // Reset all elements to default state
        if (spinner) spinner.style.display = 'block';
        if (messageElement) {
            messageElement.style.color = '';
            messageElement.style.fontWeight = '';
            messageElement.style.fontSize = '';
            messageElement.textContent = loadingMessages[0];
        }
    }
}

// Toast Notification System
function showToast(message, type = 'info') {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${message}</span>
    `;

    toastContainer.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'toastFadeOut 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

function setupEventListeners() {
    // Algorithm selector dropdown
    algorithmSelector.addEventListener('click', (e) => {
        if (e.target.closest('.algo-display')) {
            toggleAlgorithmDropdown();
        }
    });

    // Dropdown item selection
    algorithmDropdown.addEventListener('click', (e) => {
        if (e.target.classList.contains('dropdown-item')) {
            selectAlgorithm(e.target.dataset.solver);
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!algorithmSelector.contains(e.target)) {
            closeAlgorithmDropdown();
        }
    });

    pauseBtn.addEventListener('click', togglePause);
    nextBtn.addEventListener('click', showNextStep);
    restartBtn.addEventListener('click', restartGame);
    themeBtn.addEventListener('click', toggleTheme);

    // Menu button removed - algorithm selection now via dropdown panel

    // Algorithm selection
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const solver = e.target.dataset.solver;
            gameState.solver = solver;
            // Default to hint mode
            startGame(solver, false);
            hideModal();
            // Show mode toggle
            document.getElementById('modeToggle').style.display = 'flex';
        });
    });

    // Mode toggle buttons
    document.getElementById('hintModeBtn').addEventListener('click', () => {
        if (gameState.solver) {
            toggleMode(false);
        }
    });

    document.getElementById('autoModeBtn').addEventListener('click', () => {
        if (gameState.solver) {
            toggleMode(true);
        }
    });

    // Suggestion clicks
    suggestionsList.addEventListener('click', (e) => {
        // Find the suggestion-item parent if clicked on child element
        const suggestionItem = e.target.closest('.suggestion-item');
        if (suggestionItem) {
            const word = suggestionItem.dataset.word;
            if (word && gameState.gameStarted && !gameState.autoPlay && !gameState.gameOver) {
                makePlayerGuess(word);
            }
        }
    });

    // Keyboard key clicks
    keyboard.addEventListener('click', (e) => {
        if (e.target.classList.contains('key')) {
            const key = e.target.dataset.key;
            if (key && gameState.gameStarted && !gameState.autoPlay && !gameState.gameOver) {
                handleKeyPress(key);
            }
        }
    });

    // Visualization tabs
    document.querySelectorAll('.viz-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            document.querySelectorAll('.viz-tab').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            currentVizTab = e.target.dataset.tab;
            renderVisualization();
        });
    });

    // Modal removed - algorithm selection now via dropdown panel
}

// Add physical keyboard support
function addPhysicalKeyboardSupport() {
    document.addEventListener('keydown', (e) => {
        if (gameState.gameOver || !gameState.gameStarted || gameState.autoPlay) return;

        const key = e.key.toUpperCase();

        if (/^[A-Z]$/.test(key)) {
            handleKeyPress(key);
        } else if (key === 'BACKSPACE') {
            handleKeyPress('BACK');
        } else if (key === 'ENTER') {
            handleKeyPress('ENTER');
        }
    });
}

function toggleAlgorithmDropdown() {
    const isOpen = algorithmDropdown.style.display === 'block';
    if (isOpen) {
        closeAlgorithmDropdown();
    } else {
        openAlgorithmDropdown();
    }
}

function openAlgorithmDropdown() {
    algorithmDropdown.style.display = 'block';
    document.querySelector('.algo-display').classList.add('active');
}

function closeAlgorithmDropdown() {
    algorithmDropdown.style.display = 'none';
    document.querySelector('.algo-display').classList.remove('active');
}

function selectAlgorithm(solverType) {
    closeAlgorithmDropdown();

    // Hide any existing loading or result components
    hideLoading();
    hideResult();

    // Reset pause button state
    pauseBtn.classList.remove('active');

    // Update algorithm display
    const algorithmName = document.getElementById('algorithmName');
    const algorithmMode = document.getElementById('algorithmMode');

    const solverNames = {
        'dfs': 'DFS Solver',
        'entropy': 'Entropy Solver',
        'kbhillclimbing': 'KB Hill Climbing',
        'progressive': 'Progressive Entropy'
    };

    algorithmName.textContent = solverNames[solverType] || solverType;
    algorithmMode.textContent = 'Ready to start';

    // Show mode toggle
    const modeToggle = document.getElementById('modeToggle');
    modeToggle.style.display = 'flex';

    showToast(`Selected ${solverNames[solverType]}`, 'success');

    // Start the game automatically
    startGame(solverType, false); // Start in hint mode
}

async function startGame(solver, autoPlay) {
    return await startGameInternal(solver, autoPlay, false);
}

async function startGameInternal(solver, autoPlay, suppressToast = false) {
    if (!solver) {
        if (!suppressToast) {
            showToast('Please select an algorithm first', 'warning');
        }
        if (!isInitializing) {
            openAlgorithmDropdown();
        }
        return;
    }

    // Hide all UI components when starting a new game
    hideLoading();
    hideResult();

    // Clear AI choice highlights
    clearAIChoiceHighlight();

    try {
        const response = await fetch(`${API_BASE}/api/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ solver: solver, auto_play: autoPlay })
        });

        const data = await response.json();

        if (data.success) {
            gameState.solver = solver;
            gameState.autoPlay = autoPlay;
            gameState.gameStarted = true;
            gameState.currentRow = 0;
            gameState.attempts = [];
            gameState.gameOver = false;
            gameState.won = false;
            gameState.isPaused = false;
            currentInput = '';

            resetBoard();
            resetKeyboard();
            updateStats(data);
            updateAlgorithmDisplay(solver, autoPlay);

            if (!suppressToast) {
                showToast(`Game started with ${solver.toUpperCase()} solver`, 'success');
            }

            pauseBtn.disabled = false;
            nextBtn.disabled = autoPlay;
            restartBtn.disabled = false;

            // Show/hide suggestions based on mode
            const suggestionsPanel = document.getElementById('suggestionsPanel');
            if (autoPlay) {
                suggestionsPanel.style.display = 'none';
            } else {
                suggestionsPanel.style.display = 'block';
            }

            // Update mode toggle states
            const hintBtn = document.getElementById('hintModeBtn');
            const autoBtn = document.getElementById('autoModeBtn');
            if (autoPlay) {
                hintBtn.classList.remove('active');
                autoBtn.classList.add('active');
            } else {
                hintBtn.classList.add('active');
                autoBtn.classList.remove('active');
            }

            if (autoPlay) {
                showLoading();
                setTimeout(() => startAutoPlay(), 500);
            } else {
                // Load suggestions for hint mode
                await loadSuggestions();
            }
        }
    } catch (error) {
        console.error('Error starting game:', error);
        if (!suppressToast) {
            showToast('Failed to start game', 'error');
        }
    }
}

async function startAutoPlay() {
    if (!gameState.autoPlay || gameState.isPaused || gameState.gameOver) return;

    await makeAIMove();

    if (!gameState.gameOver && gameState.autoPlay && !gameState.isPaused) {
        setTimeout(() => startAutoPlay(), 1500);
    } else if (!gameState.gameOver) {
        // Show result when auto play is manually stopped
        showResult('Stopped', 'Auto-play was manually stopped', 'stopped');
    }
}

async function makeAIMove() {
    if (gameState.gameOver || !gameState.gameStarted) return;

    try {
        const response = await fetch(`${API_BASE}/api/make_move`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            const guess = data.guess;

            updateBoard(guess, data.feedback);
            updateKeyboard(guess, data.feedback);

            gameState.currentRow++;
            gameState.attempts.push({
                guess: guess,
                feedback: data.feedback,
                remainingWords: data.remaining_words
            });

            updateStats(data);
            updateVisualization(data);

            if (data.game_over) {
                gameState.gameOver = true;
                gameState.won = data.won;
                handleGameOver(data.won, data.secret_word);
            } else if (!gameState.autoPlay) {
                await loadSuggestions();
            }
        } else {
            // Handle API error response
            console.error('API returned error:', data.error || 'Unknown error');
            showToast(data.error || 'Failed to make move', 'error');
            // Show error result
            if (gameState.autoPlay) {
                showResult('Error', data.error || 'API request failed', 'error');
            }
        }
    } catch (error) {
        console.error('Error making AI move:', error);
        showToast('Failed to make move', 'error');
        // Show error result
        if (gameState.autoPlay) {
            showResult('Error', 'Network or server error occurred', 'error');
        }
    }
}

async function showNextStep() {
    if (gameState.gameOver || !gameState.gameStarted || gameState.autoPlay) {
        if (gameState.autoPlay) {
            showToast('Use Auto mode or switch to Hint mode', 'warning');
        }
        return;
    }

    try {
        // Load/refresh suggestions first
        await loadSuggestions();

        // Get the top suggestion (AI's best choice) and highlight it
        const suggestionItems = document.querySelectorAll('.suggestion-item');
        if (suggestionItems.length > 0) {
            const topSuggestion = suggestionItems[0];
            const aiChoice = topSuggestion.dataset.word;

            // Highlight the AI's choice
            highlightAIChoice(aiChoice);

            showToast(`AI recommends: ${aiChoice.toUpperCase()}`, 'info');
        } else {
            showToast('No suggestions available', 'warning');
        }
    } catch (error) {
        console.error('Error getting AI suggestion:', error);
        showToast('Failed to get AI suggestion', 'error');
    }
}

function highlightAIChoice(aiWord) {
    // Find and highlight the AI's chosen word in suggestions
    const suggestionItems = document.querySelectorAll('.suggestion-item');

    // Remove any existing highlights
    suggestionItems.forEach(item => {
        item.classList.remove('ai-choice');
    });

    // Find and highlight the AI's choice
    suggestionItems.forEach(item => {
        const word = item.dataset.word;
        if (word && word.toLowerCase() === aiWord.toLowerCase()) {
            item.classList.add('ai-choice');
            item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
}

function clearAIChoiceHighlight() {
    const suggestionItems = document.querySelectorAll('.suggestion-item');
    suggestionItems.forEach(item => {
        item.classList.remove('ai-choice');
    });
}

async function makePlayerGuess(word) {
    if (gameState.gameOver || !gameState.gameStarted) return;

    try {
        const response = await fetch(`${API_BASE}/api/player_guess`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: word })
        });

        const data = await response.json();

        if (data.success) {
            currentInput = ''; // Clear only on success
            updateBoard(word, data.feedback);
            updateKeyboard(word, data.feedback);
            gameState.currentRow++;
            gameState.attempts.push({
                guess: word,
                feedback: data.feedback,
                remainingWords: data.remaining_words
            });

            updateStats(data);
            updateVisualization(data);

            if (data.game_over) {
                gameState.gameOver = true;
                gameState.won = data.won;
                handleGameOver(data.won, data.secret_word);
            } else {
                await loadSuggestions();
            }
        } else {
            const errorMsg = data.message || 'Invalid guess';
            showToast(errorMsg, 'error');
            shakeBoard();
        }
    } catch (error) {
        console.error('Error making player guess:', error);
        showToast('Failed to make guess', 'error');
    }
}

// Handle keyboard key presses
function handleKeyPress(key) {
    if (gameState.gameOver || !gameState.gameStarted || gameState.autoPlay) {
        if (!gameState.gameStarted) {
            showToast('Please start a game first', 'warning');
        } else if (gameState.autoPlay) {
            showToast('Cannot type in Auto Play mode', 'warning');
        }
        return;
    }

    // Add letter to current input
    if (key.length === 1 && /[A-Z]/.test(key)) {
        if (currentInput.length < 5) {
            currentInput += key;
            updateCurrentRowDisplay();
        } else {
            showToast('Maximum 5 letters', 'warning');
        }
    }
    // Handle backspace
    else if (key === 'BACK' && currentInput.length > 0) {
        currentInput = currentInput.slice(0, -1);
        updateCurrentRowDisplay();
    }
    // Handle enter
    else if (key === 'ENTER') {
        if (currentInput.length === 5) {
            const word = currentInput.toLowerCase();
            makePlayerGuess(word);
        } else {
            showToast('Word must be 5 letters', 'warning');
            shakeBoard();
        }
    }
}

function updateCurrentRowDisplay() {
    const rows = gameBoard.querySelectorAll('.row');
    if (gameState.currentRow < rows.length) {
        const currentRowElement = rows[gameState.currentRow];
        const tiles = currentRowElement.querySelectorAll('.tile');

        // First, clear all tiles in current row that aren't locked
        tiles.forEach(tile => {
            if (!tile.classList.contains('green') &&
                !tile.classList.contains('yellow') &&
                !tile.classList.contains('gray')) {
                tile.textContent = '';
                tile.classList.remove('filled');
            }
        });

        // Then update with current input
        for (let i = 0; i < currentInput.length && i < 5; i++) {
            tiles[i].textContent = currentInput[i];
            tiles[i].classList.add('filled');
            // Add bounce animation
            tiles[i].style.animation = 'none';
            setTimeout(() => {
                tiles[i].style.animation = 'pop 0.1s ease';
            }, 10);
        }
    }
}

function clearCurrentRowDisplay() {
    const rows = gameBoard.querySelectorAll('.row');
    if (gameState.currentRow < rows.length) {
        const currentRowElement = rows[gameState.currentRow];
        const tiles = currentRowElement.querySelectorAll('.tile');
        tiles.forEach(tile => {
            if (!tile.classList.contains('green') && !tile.classList.contains('yellow') && !tile.classList.contains('gray')) {
                tile.textContent = '';
                tile.classList.remove('filled');
            }
        });
    }
}

async function loadSuggestions() {
    try {
        // Show loading indicator in suggestions panel
        showSuggestionsLoading();

        const response = await fetch(`${API_BASE}/api/suggestions`);
        const data = await response.json();

        // Hide loading indicator
        hideSuggestionsLoading();

        if (data.success) {
            displaySuggestions(data.suggestions);
        }
    } catch (error) {
        console.error('Error loading suggestions:', error);
        hideSuggestionsLoading();
        suggestionsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 1rem;">Failed to load suggestions</p>';
    }
}

// Suggestions loading indicator
let suggestionsMessageInterval = null;
const suggestionsLoadingMessages = [
    "Analyzing possibilities...",
    "Calculating entropy...",
    "Finding optimal words...",
    "Ranking suggestions..."
];

function showSuggestionsLoading() {
    // Clear any existing interval
    if (suggestionsMessageInterval) {
        clearInterval(suggestionsMessageInterval);
        suggestionsMessageInterval = null;
    }

    suggestionsList.innerHTML = `
        <div class="suggestions-loading">
            <div class="suggestions-spinner">
                <div class="spinner-dots">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>
            <div class="suggestions-loading-text">
                <span class="brain-emoji">🧠</span>
                <span id="suggestionsLoadingMessage">Analyzing possibilities...</span>
            </div>
        </div>
    `;

    // Cycle through loading messages
    const messageElement = document.getElementById('suggestionsLoadingMessage');
    let currentIndex = 0;

    suggestionsMessageInterval = setInterval(() => {
        currentIndex = (currentIndex + 1) % suggestionsLoadingMessages.length;
        if (messageElement) {
            messageElement.style.opacity = '0';
            setTimeout(() => {
                messageElement.textContent = suggestionsLoadingMessages[currentIndex];
                messageElement.style.opacity = '1';
            }, 150);
        }
    }, 1200);
}

function hideSuggestionsLoading() {
    if (suggestionsMessageInterval) {
        clearInterval(suggestionsMessageInterval);
        suggestionsMessageInterval = null;
    }
}

// Initial Game Loading
let isInitializing = false;

async function initializeGame() {
    isInitializing = true;

    // Show initial loading overlay
    showInitialLoading();

    try {
        // Start game with default solver (entropy)
        const defaultSolver = 'entropy';
        await startGameInternal(defaultSolver, false, true); // Start in hint mode by default, suppress toast

        // Update algorithm display to show selected solver
        const algorithmName = document.getElementById('algorithmName');
        const algorithmMode = document.getElementById('algorithmMode');
        const modeToggle = document.getElementById('modeToggle');

        if (algorithmName) {
            algorithmName.textContent = 'Entropy Solver';
        }
        if (algorithmMode) {
            algorithmMode.textContent = 'Ready to play';
        }
        if (modeToggle) {
            modeToggle.style.display = 'flex';
        }

        // Set default mode button as active
        const hintBtn = document.getElementById('hintModeBtn');
        if (hintBtn) {
            hintBtn.classList.add('active');
        }

    } catch (error) {
        console.error('Error initializing game:', error);
        showToast('Failed to initialize game', 'error');
    } finally {
        // Hide initial loading overlay
        hideInitialLoading();
        isInitializing = false;
    }
}

function showInitialLoading() {
    // Create or show initial loading overlay
    let overlay = document.getElementById('initialLoadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'initialLoadingOverlay';
        overlay.className = 'initial-loading-overlay';
        overlay.innerHTML = `
            <div class="initial-loading-content">
                <div class="initial-loading-spinner">
                    <div class="spinner-large"></div>
                </div>
                <div class="initial-loading-text">
                    <h2>🎮 Loading Wordle AI...</h2>
                    <p id="initialLoadingMessage">Initializing game engine...</p>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    overlay.style.display = 'flex';

    // Cycle through initialization messages
    const messageElement = document.getElementById('initialLoadingMessage');
    const initMessages = [
        "Initializing game engine...",
        "Loading word dictionary...",
        "Setting up AI solver...",
        "Preparing suggestions...",
        "Almost ready..."
    ];

    let currentIndex = 0;
    if (messageElement) {
        messageElement.textContent = initMessages[currentIndex];
    }

    const messageInterval = setInterval(() => {
        currentIndex = (currentIndex + 1) % initMessages.length;
        if (messageElement) {
            messageElement.style.opacity = '0';
            setTimeout(() => {
                messageElement.textContent = initMessages[currentIndex];
                messageElement.style.opacity = '1';
            }, 200);
        }
    }, 1000);

    // Store interval ID for cleanup
    overlay.dataset.intervalId = messageInterval;
}

function hideInitialLoading() {
    const overlay = document.getElementById('initialLoadingOverlay');
    if (overlay) {
        // Clear message interval
        const intervalId = overlay.dataset.intervalId;
        if (intervalId) {
            clearInterval(parseInt(intervalId));
        }

        // Fade out animation
        overlay.style.opacity = '0';
        overlay.style.transition = 'opacity 0.5s ease-out';

        setTimeout(() => {
            overlay.style.display = 'none';
        }, 500);
    }
}

function displaySuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) {
        suggestionsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 1rem;">No suggestions available</p>';
        return;
    }

    // Clear any existing AI choice highlights
    clearAIChoiceHighlight();

    suggestionsList.innerHTML = suggestions.slice(0, 10).map((sugg, idx) => {
        // Handle both tuple format [word, score] and object format {word, score}
        let word, score;
        if (Array.isArray(sugg)) {
            word = sugg[0];
            score = sugg[1];
        } else if (typeof sugg === 'object') {
            word = sugg.word || sugg;
            score = sugg.score;
        } else {
            word = sugg;
            score = null;
        }

        // Format score for display
        let scoreText = '';
        if (score !== null && score !== undefined && score !== 0) {
            scoreText = score.toFixed(1);
        }

        return `
            <div class="suggestion-item" data-word="${word}">
                <span class="suggestion-rank">${idx + 1}</span>
                <span class="suggestion-word">${word.toUpperCase()}</span>
                <span class="suggestion-score">${scoreText}</span>
            </div>
        `;
    }).join('');
}

function updateBoard(guess, feedback) {
    const rows = gameBoard.querySelectorAll('.row');
    const currentRowEl = rows[gameState.currentRow];
    const tiles = currentRowEl.querySelectorAll('.tile');

    guess.split('').forEach((letter, i) => {
        const tile = tiles[i];
        tile.textContent = letter.toUpperCase();
        tile.classList.remove('filled');
        tile.classList.add('flip');

        setTimeout(() => {
            if (feedback[i] === 2) {
                tile.classList.add('green');
            } else if (feedback[i] === 1) {
                tile.classList.add('yellow');
            } else {
                tile.classList.add('gray');
            }
        }, i * 100 + 150);
    });
}

function updateKeyboard(guess, feedback) {
    guess.split('').forEach((letter, i) => {
        const key = keyboard.querySelector(`[data-key="${letter.toUpperCase()}"]`);
        if (!key) return;

        const state = feedback[i];

        // Only update if new state is better (green > yellow > gray)
        if (state === 2) {
            key.classList.remove('yellow', 'gray');
            key.classList.add('green');
        } else if (state === 1 && !key.classList.contains('green')) {
            key.classList.remove('gray');
            key.classList.add('yellow');
        } else if (state === 0 && !key.classList.contains('green') && !key.classList.contains('yellow')) {
            key.classList.add('gray');
        }
    });
}

function shakeBoard() {
    const rows = gameBoard.querySelectorAll('.row');
    const currentRowEl = rows[gameState.currentRow];
    currentRowEl.style.animation = 'shake 0.5s ease';
    setTimeout(() => {
        currentRowEl.style.animation = '';
        // Don't clear - just keep the input visible
    }, 500);
}

function resetBoard() {
    const tiles = gameBoard.querySelectorAll('.tile');
    tiles.forEach(tile => {
        tile.textContent = '';
        tile.className = 'tile';
    });
}

function resetKeyboard() {
    const keys = keyboard.querySelectorAll('.key');
    keys.forEach(key => {
        key.classList.remove('gray', 'yellow', 'green');
    });
}

function updateStats(data) {
    document.getElementById('attemptsCount').textContent = data.attempts || gameState.currentRow;
    document.getElementById('remainingWords').textContent = data.remaining_words ?? '-';
    document.getElementById('currentSolver').textContent = gameState.solver ? gameState.solver.toUpperCase() : 'None';
}

function handleGameOver(won, secretWord) {
    // Show result component for both auto and hint modes
    if (won) {
        showResult('Solved!', `You found the word: ${secretWord.toUpperCase()} in ${gameState.attempts.length} attempts!`, 'success');
        showToast(`🎉 You won in ${gameState.attempts.length} attempts!`, 'success');
        celebrateWin();
    } else {
        showResult('Game Over', `The word was: ${secretWord.toUpperCase()}`, 'error');
        showToast(`Game Over. The word was: ${secretWord.toUpperCase()}`, 'error');
    }

    pauseBtn.disabled = true;
    nextBtn.disabled = true;
}

function celebrateWin() {
    const rows = gameBoard.querySelectorAll('.row');
    const winningRow = rows[gameState.currentRow - 1];
    winningRow.classList.add('bounce');
    setTimeout(() => {
        winningRow.classList.remove('bounce');
    }, 1000);
}

function togglePause() {
    if (!gameState.gameStarted) return;

    gameState.isPaused = !gameState.isPaused;
    pauseBtn.classList.toggle('active', gameState.isPaused);

    if (gameState.isPaused) {
        // Show pause state
        hideLoading();
        showPaused();
        showToast('Game paused', 'info');
    } else {
        showToast('Game resumed', 'success');
        if (gameState.autoPlay) {
            showLoading();
            startAutoPlay();
        }
    }
}

async function restartGame() {
    if (!gameState.gameStarted) {
        showToast('Please start a game first', 'warning');
        return;
    }
    // Hide all UI components when restarting
    hideLoading();
    hideResult();

    // Reset pause button state
    pauseBtn.classList.remove('active');

    // Clear AI choice highlights
    clearAIChoiceHighlight();

    // Clear input and display
    currentInput = '';
    clearCurrentRowDisplay();
    showToast('Restarting game...', 'info');
    await startGame(gameState.solver, gameState.autoPlay);
}

function toggleTheme() {
    const body = document.body;
    const isWordleTheme = body.classList.toggle('wordle-theme');

    // Save preference
    localStorage.setItem('wordleTheme', isWordleTheme ? 'light' : 'dark');

    // Update button text
    themeBtn.textContent = isWordleTheme ? '🌙 Dark' : '🎨 Theme';

    showToast(isWordleTheme ? 'Switched to Original Wordle theme' : 'Switched to Dark theme', 'success');

    // Redraw visualizations with new colors
    if (gameState.gameStarted) {
        renderVisualization();
    }
}

function loadThemePreference() {
    const savedTheme = localStorage.getItem('wordleTheme');
    if (savedTheme === 'light') {
        document.body.classList.add('wordle-theme');
        themeBtn.textContent = '🌙 Dark';
    }
}

function toggleMode(autoPlay) {
    // Hide loading and result when switching modes
    hideLoading();
    hideResult();

    // Reset pause button state
    pauseBtn.classList.remove('active');

    if (!gameState.gameStarted) {
        startGame(gameState.solver, autoPlay);
    } else {
        // Restart with new mode
        currentInput = '';
        clearCurrentRowDisplay();
        startGame(gameState.solver, autoPlay);
    }

    // Show/hide suggestions based on mode
    const suggestionsPanel = document.getElementById('suggestionsPanel');
    if (autoPlay) {
        suggestionsPanel.style.display = 'none';
    } else {
        suggestionsPanel.style.display = 'block';
    }

    // Update toggle button states
    const hintBtn = document.getElementById('hintModeBtn');
    const autoBtn = document.getElementById('autoModeBtn');

    if (autoPlay) {
        hintBtn.classList.remove('active');
        autoBtn.classList.add('active');
    } else {
        hintBtn.classList.add('active');
        autoBtn.classList.remove('active');
    }
}

function addLog(message, type = 'info') {
    // Deprecated - Timeline removed
}

function clearLog() {
    // Deprecated - Timeline removed
}

function updateAlgorithmDisplay(solver, autoPlay) {
    const algoName = document.getElementById('algorithmName');
    const algoMode = document.getElementById('algorithmMode');

    const solverNames = {
        'dfs': 'DFS Solver',
        'hillclimbing': 'Hill Climbing'
    };

    algoName.textContent = solverNames[solver] || solver.toUpperCase();
    algoMode.textContent = autoPlay ? 'Auto Play Mode' : 'Hint Mode - Click suggestions or type';
}

// Visualization with Chart.js
function initVisualization() {
    vizCanvas = document.getElementById('vizCanvas');
    chartCanvas = document.getElementById('chartCanvas');

    if (!vizCanvas || !chartCanvas) {
        console.error('Canvas elements not found!');
        return;
    }

    vizCtx = vizCanvas.getContext('2d');

    // Set up viz tab switching
    document.querySelectorAll('.viz-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.viz-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentVizTab = tab.dataset.tab;
            console.log('Switching to viz tab:', currentVizTab);
            renderVisualization();
        });
    });

    console.log('Visualization initialized');
    renderVisualization();
}

function updateVisualization(data) {
    renderVisualization();
}

function renderVisualization() {
    if (!vizCtx) return;

    // Clear both canvases
    vizCtx.clearRect(0, 0, vizCanvas.width, vizCanvas.height);

    // Show/hide appropriate canvas based on viz type
    switch (currentVizTab) {
        case 'entropy':
            vizCanvas.style.display = 'none';
            chartCanvas.style.display = 'block';
            drawEntropyChartJS();
            break;
        case 'search':
            vizCanvas.style.display = 'block';
            chartCanvas.style.display = 'none';
            drawSearchSpace();
            break;
        case 'tree':
            // Tree now uses Chart.js - handled in drawDecisionTree()
            drawDecisionTree();
            break;
    }
}

function drawDecisionTree() {
    if (gameState.attempts.length === 0) {
        // Show placeholder on viz canvas
        vizCanvas.style.display = 'block';
        chartCanvas.style.display = 'none';
        drawPlaceholder('Analysis will appear after first guess');
        return;
    }

    // Use Chart.js for better visualization
    vizCanvas.style.display = 'none';
    chartCanvas.style.display = 'block';

    // Destroy existing chart
    if (activeChart) {
        activeChart.destroy();
        activeChart = null;
    }

    const ctx = chartCanvas.getContext('2d');

    // Prepare data
    const labels = gameState.attempts.map((a, i) => `${i + 1}. ${a.guess.toUpperCase()}`);
    const greenCounts = gameState.attempts.map(a => (a.feedback || []).filter(f => f === 2).length);
    const yellowCounts = gameState.attempts.map(a => (a.feedback || []).filter(f => f === 1).length);
    const remainingWords = gameState.attempts.map(a => a.remainingWords || 0);

    console.log('Drawing decision tree chart with', gameState.attempts.length, 'attempts');
    console.log('Chart data:', { labels, greenCounts, yellowCounts, remainingWords });

    try {
        activeChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    // Put Remaining Words first so its legend entry appears above the others,
                    // but set a higher `order` so the line is drawn on top of the bars.
                    {
                        label: 'Remaining Words',
                        data: remainingWords,
                        type: 'line',
                        backgroundColor: 'rgba(137, 180, 250, 0.2)',
                        borderColor: '#89b4fa',
                        borderWidth: 3,
                        fill: true,
                        yAxisID: 'y1',
                        tension: 0.4,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        order: 3
                    },
                    {
                        label: 'Correct Letters (✓)',
                        data: greenCounts,
                        backgroundColor: 'rgba(166, 227, 161, 0.8)',
                        borderColor: '#a6e3a1',
                        borderWidth: 2,
                        yAxisID: 'y',
                        order: 1
                    },
                    {
                        label: 'Misplaced Letters (~)',
                        data: yellowCounts,
                        backgroundColor: 'rgba(249, 226, 175, 0.8)',
                        borderColor: '#f9e2af',
                        borderWidth: 2,
                        yAxisID: 'y',
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Guess Progress & Feedback Analysis',
                        color: '#89b4fa',
                        font: {
                            size: 18,
                            weight: 'bold'
                        },
                        padding: 20
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#cdd6f4',
                            font: {
                                size: 12
                            },
                            padding: 15,
                            usePointStyle: true,
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 30, 46, 0.95)',
                        titleColor: '#89b4fa',
                        bodyColor: '#cdd6f4',
                        borderColor: '#89b4fa',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            title: function (context) {
                                return 'Attempt ' + context[0].label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        min: 0,
                        max: 5,
                        ticks: {
                            stepSize: 1,
                            color: '#a6adc8'
                        },
                        grid: {
                            color: 'rgba(88, 91, 112, 0.3)'
                        },
                        title: {
                            display: true,
                            text: 'Letter Feedback Count',
                            color: '#89b4fa',
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {
                            color: '#a6adc8'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        title: {
                            display: true,
                            text: 'Remaining Words',
                            color: '#89b4fa',
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        }
                    },
                    x: {
                        ticks: {
                            color: '#a6adc8',
                            font: {
                                size: 11
                            },
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            color: 'rgba(88, 91, 112, 0.2)'
                        }
                    }
                }
            }
        });
        console.log('Chart created successfully!');
    } catch (error) {
        console.error('Error creating Chart.js chart:', error);
        // Fallback to canvas
        vizCanvas.style.display = 'block';
        chartCanvas.style.display = 'none';
        drawPlaceholder('Visualization Error - Try refreshing');
    }
}

function drawEntropyChartJS() {
    if (gameState.attempts.length === 0) {
        chartCanvas.style.display = 'none';
        vizCanvas.style.display = 'block';
        drawPlaceholder('Word reduction chart will appear after guesses');
        return;
    }

    // Destroy existing chart if any
    if (activeChart) {
        activeChart.destroy();
    }

    const ctx = chartCanvas.getContext('2d');

    const labels = ['Start', ...gameState.attempts.map(a => a.guess.toUpperCase())];
    const data = [12953, ...gameState.attempts.map(a => a.remainingWords || 0)];

    activeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Remaining Words',
                data: data,
                borderColor: '#89b4fa',
                backgroundColor: 'rgba(137, 180, 250, 0.2)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#a6e3a1',
                pointBorderColor: '#89b4fa',
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#cdd6f4',
                        font: { size: 14, family: 'Segoe UI' }
                    }
                },
                title: {
                    display: true,
                    text: 'Word Space Reduction',
                    color: '#89b4fa',
                    font: { size: 16, family: 'Segoe UI', weight: 'bold' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#a6adc8',
                        font: { size: 11 }
                    },
                    grid: {
                        color: 'rgba(88, 91, 112, 0.3)'
                    }
                },
                x: {
                    ticks: {
                        color: '#a6adc8',
                        font: { size: 11 }
                    },
                    grid: {
                        color: 'rgba(88, 91, 112, 0.3)'
                    }
                }
            }
        }
    });
}

function drawSearchSpace() {
    if (gameState.attempts.length === 0) {
        vizCanvas.style.display = 'block';
        chartCanvas.style.display = 'none';
        drawPlaceholder('Search space visualization after guesses');
        return;
    }

    // Use Chart.js for better quality
    vizCanvas.style.display = 'none';
    chartCanvas.style.display = 'block';

    // Destroy existing chart
    if (activeChart) {
        activeChart.destroy();
    }

    const ctx = chartCanvas.getContext('2d');

    const labels = gameState.attempts.map((a, i) => `#${i + 1}: ${a.guess.toUpperCase()}`);
    const data = gameState.attempts.map(a => a.remainingWords || 0);

    // Calculate reduction percentage for each step
    const reductionData = gameState.attempts.map((a, i) => {
        const prev = i === 0 ? 12953 : gameState.attempts[i - 1].remainingWords;
        const reduction = ((prev - (a.remainingWords || 0)) / prev * 100).toFixed(1);
        return parseFloat(reduction);
    });

    activeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Words Eliminated (%)',
                    data: reductionData,
                    backgroundColor: 'rgba(166, 227, 161, 0.7)',
                    borderColor: '#a6e3a1',
                    borderWidth: 2,
                    yAxisID: 'y1'
                },
                {
                    label: 'Remaining Words',
                    data: data,
                    type: 'line',
                    borderColor: '#89b4fa',
                    backgroundColor: 'rgba(137, 180, 250, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: '#89b4fa',
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#cdd6f4',
                        font: { size: 12, family: 'Segoe UI' },
                        padding: 15
                    }
                },
                title: {
                    display: true,
                    text: 'Search Space Pruning Efficiency',
                    color: '#89b4fa',
                    font: { size: 16, family: 'Segoe UI', weight: 'bold' },
                    padding: 20
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    beginAtZero: true,
                    ticks: {
                        color: '#a6adc8',
                        font: { size: 11 }
                    },
                    grid: {
                        color: 'rgba(88, 91, 112, 0.3)'
                    },
                    title: {
                        display: true,
                        text: 'Remaining Words',
                        color: '#89b4fa',
                        font: { size: 12 }
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: '#a6adc8',
                        font: { size: 11 },
                        callback: function (value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    title: {
                        display: true,
                        text: 'Elimination Rate',
                        color: '#a6e3a1',
                        font: { size: 12 }
                    }
                },
                x: {
                    ticks: {
                        color: '#a6adc8',
                        font: { size: 10 },
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: 'rgba(88, 91, 112, 0.3)'
                    }
                }
            }
        }
    });
}

function drawPlaceholder(text) {
    vizCtx.fillStyle = '#6c7086';
    vizCtx.font = '14px "Segoe UI"';
    vizCtx.textAlign = 'center';
    vizCtx.fillText(text, vizCanvas.width / 2, vizCanvas.height / 2);
}
