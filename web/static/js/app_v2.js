// Enhanced Wordle AI Visualizer - v2.0
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
let currentInput = '';

// API endpoints
const API_BASE = '';

// DOM elements
const menuBtn = document.getElementById('menuBtn');
const pauseBtn = document.getElementById('pauseBtn');
const nextBtn = document.getElementById('nextBtn');
const restartBtn = document.getElementById('restartBtn');
const menuModal = document.getElementById('menuModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const gameBoard = document.getElementById('gameBoard');
const keyboard = document.getElementById('keyboard');
const suggestionsList = document.getElementById('suggestionsList');
const logContainer = document.getElementById('logContainer');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    initVisualization();
    addPhysicalKeyboardSupport();
});

function setupEventListeners() {
    menuBtn.addEventListener('click', () => showModal());
    closeModalBtn.addEventListener('click', () => hideModal());
    pauseBtn.addEventListener('click', togglePause);
    nextBtn.addEventListener('click', makeAIMove);
    restartBtn.addEventListener('click', restartGame);

    // Mode selection
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const solver = e.target.dataset.solver;
            const autoPlay = e.target.dataset.auto === 'true';
            startGame(solver, autoPlay);
            hideModal();
        });
    });

    // Suggestion clicks
    suggestionsList.addEventListener('click', (e) => {
        if (e.target.classList.contains('suggestion-item')) {
            const word = e.target.dataset.word;
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

    // Close modal on outside click
    menuModal.addEventListener('click', (e) => {
        if (e.target === menuModal) {
            hideModal();
        }
    });
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

function showModal() {
    menuModal.classList.add('active');
}

function hideModal() {
    menuModal.classList.remove('active');
}

async function startGame(solver, autoPlay) {
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
            clearLog();
            updateStats(data);
            
            addLog(`🎮 Game started with ${solver.toUpperCase()} solver`);
            addLog(`Mode: ${autoPlay ? 'Auto Play' : 'Hint Only'}`);

            pauseBtn.disabled = false;
            nextBtn.disabled = !autoPlay;

            if (autoPlay) {
                setTimeout(() => startAutoPlay(), 500);
            } else {
                await loadSuggestions();
            }
        }
    } catch (error) {
        console.error('Error starting game:', error);
        addLog('Error: Failed to start game');
    }
}

async function startAutoPlay() {
    if (!gameState.autoPlay || gameState.isPaused || gameState.gameOver) return;

    await makeAIMove();

    if (!gameState.gameOver && gameState.autoPlay && !gameState.isPaused) {
        setTimeout(() => startAutoPlay(), 1500);
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
            addLog(`AI suggests: ${guess.toUpperCase()}`);
            
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
        }
    } catch (error) {
        console.error('Error making AI move:', error);
        addLog('Error: Failed to make move');
    }
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
            addLog(`You guessed: ${word.toUpperCase()}`);
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
            addLog(`❌ ${data.message || 'Invalid guess'}`);
            shakeBoard();
        }
    } catch (error) {
        console.error('Error making player guess:', error);
        addLog('Error: Failed to make guess');
    }
}

// Handle keyboard key presses
function handleKeyPress(key) {
    if (gameState.gameOver || !gameState.gameStarted || gameState.autoPlay) return;

    // Add letter to current input
    if (key.length === 1 && /[A-Z]/.test(key)) {
        if (currentInput.length < 5) {
            currentInput += key;
            updateCurrentRowDisplay();
        }
    }
    // Handle backspace
    else if (key === 'BACK' && currentInput.length > 0) {
        currentInput = currentInput.slice(0, -1);
        updateCurrentRowDisplay();
    }
    // Handle enter
    else if (key === 'ENTER' && currentInput.length === 5) {
        const word = currentInput.toLowerCase();
        currentInput = '';
        makePlayerGuess(word);
    }
}

function updateCurrentRowDisplay() {
    const rows = gameBoard.querySelectorAll('.row');
    if (gameState.currentRow < rows.length) {
        const currentRowElement = rows[gameState.currentRow];
        const tiles = currentRowElement.querySelectorAll('.tile');
        
        for (let i = 0; i < 5; i++) {
            if (i < currentInput.length) {
                tiles[i].textContent = currentInput[i];
                tiles[i].classList.add('filled');
                // Add bounce animation
                tiles[i].style.animation = 'none';
                setTimeout(() => {
                    tiles[i].style.animation = 'pop 0.1s ease';
                }, 10);
            } else {
                tiles[i].textContent = '';
                tiles[i].classList.remove('filled');
            }
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
        const response = await fetch(`${API_BASE}/api/suggestions`);
        const data = await response.json();
        
        if (data.success) {
            displaySuggestions(data.suggestions);
        }
    } catch (error) {
        console.error('Error loading suggestions:', error);
    }
}

function displaySuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) {
        suggestionsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 1rem;">No suggestions available</p>';
        return;
    }

    suggestionsList.innerHTML = suggestions.slice(0, 10).map((sugg, idx) => {
        const word = sugg.word || sugg;
        const score = sugg.score ? ` (${sugg.score.toFixed(2)})` : '';
        return `
            <div class="suggestion-item" data-word="${word}">
                <span class="suggestion-rank">${idx + 1}</span>
                <span class="suggestion-word">${word.toUpperCase()}</span>
                <span class="suggestion-score">${score}</span>
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
        clearCurrentRowDisplay();
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
    document.getElementById('nodesVisited').textContent = data.nodes_visited || 0;
    document.getElementById('currentSolver').textContent = gameState.solver ? gameState.solver.toUpperCase() : 'None';
}

function handleGameOver(won, secretWord) {
    if (won) {
        addLog(`🎉 Victory in ${gameState.attempts.length} attempts!`);
        celebrateWin();
    } else {
        addLog(`😔 Game Over. The word was: ${secretWord.toUpperCase()}`);
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
        addLog('⏸️ Game paused');
    } else {
        addLog('▶️ Game resumed');
        if (gameState.autoPlay) {
            startAutoPlay();
        }
    }
}

async function restartGame() {
    if (!gameState.gameStarted) return;
    await startGame(gameState.solver, gameState.autoPlay);
}

function addLog(message) {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = message;
    logContainer.insertBefore(entry, logContainer.firstChild);

    // Limit log entries
    while (logContainer.children.length > 50) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

function clearLog() {
    logContainer.innerHTML = '<div class="log-entry">Welcome to Wordle AI Visualizer v2</div>';
}

// Visualization
function initVisualization() {
    vizCanvas = document.getElementById('vizCanvas');
    if (!vizCanvas) return;

    vizCtx = vizCanvas.getContext('2d');
    renderVisualization();
}

function updateVisualization(data) {
    renderVisualization();
}

function renderVisualization() {
    if (!vizCtx) return;

    vizCtx.clearRect(0, 0, vizCanvas.width, vizCanvas.height);

    switch (currentVizTab) {
        case 'tree':
            drawDecisionTree();
            break;
        case 'entropy':
            drawEntropyChart();
            break;
        case 'search':
            drawSearchSpace();
            break;
    }
}

function drawDecisionTree() {
    const width = vizCanvas.width;
    const height = vizCanvas.height;

    if (gameState.attempts.length === 0) {
        drawPlaceholder('Decision tree will appear after first guess');
        return;
    }

    vizCtx.clearRect(0, 0, width, height);
    
    const nodeRadius = 25;
    const levelHeight = 70;
    let y = 40;

    // Draw title
    vizCtx.font = 'bold 14px monospace';
    vizCtx.fillStyle = '#89b4fa';
    vizCtx.textAlign = 'center';
    vizCtx.fillText('Decision Path', width / 2, 20);

    // Root node
    vizCtx.beginPath();
    vizCtx.arc(width / 2, y, nodeRadius, 0, Math.PI * 2);
    const gradient = vizCtx.createRadialGradient(width / 2, y, 0, width / 2, y, nodeRadius);
    gradient.addColorStop(0, '#45475a');
    gradient.addColorStop(1, '#313244');
    vizCtx.fillStyle = gradient;
    vizCtx.fill();
    vizCtx.strokeStyle = '#89b4fa';
    vizCtx.lineWidth = 2;
    vizCtx.stroke();
    
    vizCtx.font = 'bold 11px monospace';
    vizCtx.fillStyle = '#cdd6f4';
    vizCtx.fillText('START', width / 2, y + 4);

    // Draw each guess as a level with branching
    gameState.attempts.forEach((attempt, index) => {
        const prevY = y;
        y += levelHeight;
        const x = width / 2;
        
        // Count green, yellow, gray tiles for visual representation
        const feedback = attempt.feedback || [];
        const greenCount = feedback.filter(f => f === 2).length;
        const yellowCount = feedback.filter(f => f === 1).length;

        // Draw animated connection line
        vizCtx.beginPath();
        vizCtx.moveTo(width / 2, prevY + nodeRadius);
        vizCtx.lineTo(x, y - nodeRadius);
        vizCtx.strokeStyle = '#585b70';
        vizCtx.lineWidth = 2;
        vizCtx.stroke();

        // Draw node with color based on accuracy
        vizCtx.beginPath();
        vizCtx.arc(x, y, nodeRadius, 0, Math.PI * 2);
        
        let nodeColor;
        if (greenCount === 5) {
            nodeColor = '#a6e3a1'; // Win
        } else if (greenCount >= 3) {
            nodeColor = '#f9e2af'; // Close
        } else if (greenCount + yellowCount >= 3) {
            nodeColor = '#fab387'; // Getting there
        } else {
            nodeColor = '#313244'; // Far
        }
        
        const nodeGradient = vizCtx.createRadialGradient(x, y, 0, x, y, nodeRadius);
        nodeGradient.addColorStop(0, nodeColor);
        nodeGradient.addColorStop(1, nodeColor + 'cc');
        vizCtx.fillStyle = nodeGradient;
        vizCtx.fill();
        vizCtx.strokeStyle = '#89b4fa';
        vizCtx.lineWidth = 2;
        vizCtx.stroke();
        
        // Draw word
        vizCtx.font = 'bold 11px monospace';
        vizCtx.fillStyle = greenCount === 5 ? '#1e1e2e' : '#cdd6f4';
        vizCtx.fillText(attempt.guess.toUpperCase(), x, y + 4);
        
        // Draw feedback indicators
        vizCtx.font = '9px monospace';
        vizCtx.fillStyle = '#89b4fa';
        vizCtx.fillText(`${greenCount}🟩 ${yellowCount}🟨`, x, y + nodeRadius + 12);
    });
}

function drawEntropyChart() {
    const width = vizCanvas.width;
    const height = vizCanvas.height;

    if (gameState.attempts.length === 0) {
        drawPlaceholder('Word reduction chart will appear after guesses');
        return;
    }
    
    vizCtx.clearRect(0, 0, width, height);
    
    // Draw title
    vizCtx.font = 'bold 14px monospace';
    vizCtx.fillStyle = '#89b4fa';
    vizCtx.textAlign = 'center';
    vizCtx.fillText('Word Space Reduction', width / 2, 20);
    
    const padding = 50;
    const chartHeight = height - padding - 40;
    const barWidth = Math.min(60, (width - 2 * padding) / (gameState.attempts.length + 1));
    const spacing = 10;
    
    // Initial word count
    const initialWords = 12953;
    
    // Draw bars for each attempt
    gameState.attempts.forEach((attempt, index) => {
        const x = padding + index * (barWidth + spacing);
        const remainingWords = attempt.remainingWords || Math.floor(initialWords / Math.pow(2, index + 1));
        const barHeight = (remainingWords / initialWords) * chartHeight;
        const y = height - 30 - barHeight;
        
        // Create gradient for bar
        const gradient = vizCtx.createLinearGradient(x, y, x, height - 30);
        gradient.addColorStop(0, '#89b4fa');
        gradient.addColorStop(1, '#74c7ec');
        
        // Draw bar
        vizCtx.fillStyle = gradient;
        vizCtx.fillRect(x, y, barWidth, barHeight);
        
        // Draw bar outline
        vizCtx.strokeStyle = '#45475a';
        vizCtx.lineWidth = 1;
        vizCtx.strokeRect(x, y, barWidth, barHeight);
        
        // Draw word count on top of bar
        vizCtx.font = 'bold 10px monospace';
        vizCtx.fillStyle = '#cdd6f4';
        vizCtx.textAlign = 'center';
        vizCtx.fillText(remainingWords, x + barWidth / 2, y - 5);
        
        // Draw guess label
        vizCtx.font = '9px monospace';
        vizCtx.fillStyle = '#89b4fa';
        vizCtx.save();
        vizCtx.translate(x + barWidth / 2, height - 10);
        vizCtx.rotate(-Math.PI / 4);
        vizCtx.fillText(attempt.guess.toUpperCase(), 0, 0);
        vizCtx.restore();
    });
    
    // Draw baseline
    vizCtx.strokeStyle = '#45475a';
    vizCtx.lineWidth = 2;
    vizCtx.beginPath();
    vizCtx.moveTo(padding - 10, height - 30);
    vizCtx.lineTo(width - padding, height - 30);
    vizCtx.stroke();
    
    // Draw y-axis labels
    vizCtx.font = '10px monospace';
    vizCtx.fillStyle = '#6c7086';
    vizCtx.textAlign = 'right';
    vizCtx.fillText('12,953', padding - 15, height - 30 - chartHeight + 5);
    vizCtx.fillText('0', padding - 15, height - 25);
}

function drawSearchSpace() {
    const width = vizCanvas.width;
    const height = vizCanvas.height;

    if (gameState.attempts.length === 0) {
        drawPlaceholder('🔍 Search space visualization after guesses');
        return;
    }

    vizCtx.clearRect(0, 0, width, height);

    // Title
    vizCtx.font = 'bold 14px monospace';
    vizCtx.fillStyle = '#89b4fa';
    vizCtx.textAlign = 'center';
    vizCtx.fillText('🎯 Search Space Pruning', width / 2, 20);

    // Draw concentric circles representing search space
    const centerX = width / 2;
    const centerY = height / 2 + 10;
    const maxRadius = Math.min(width, height) / 2 - 40;

    // Draw outer circle (initial space)
    vizCtx.beginPath();
    vizCtx.arc(centerX, centerY, maxRadius, 0, Math.PI * 2);
    vizCtx.strokeStyle = '#45475a';
    vizCtx.lineWidth = 2;
    vizCtx.stroke();

    // Draw circles for each attempt
    gameState.attempts.forEach((attempt, index) => {
        const remainingWords = attempt.remainingWords || 1000;
        const radius = (remainingWords / 12953) * maxRadius;
        
        vizCtx.beginPath();
        vizCtx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        
        // Gradient fill
        const gradient = vizCtx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
        gradient.addColorStop(0, '#89b4fa44');
        gradient.addColorStop(1, '#89b4fa11');
        vizCtx.fillStyle = gradient;
        vizCtx.fill();
        
        vizCtx.strokeStyle = '#89b4fa';
        vizCtx.lineWidth = 2;
        vizCtx.stroke();
        
        // Label
        vizCtx.font = '10px monospace';
        vizCtx.fillStyle = '#cdd6f4';
        vizCtx.textAlign = 'center';
        vizCtx.fillText(`${remainingWords} words`, centerX, centerY - radius - 5);
    });
}

function drawPlaceholder(text) {
    vizCtx.fillStyle = '#6c7086';
    vizCtx.font = '14px monospace';
    vizCtx.textAlign = 'center';
    vizCtx.fillText(text, vizCanvas.width / 2, vizCanvas.height / 2);
}
