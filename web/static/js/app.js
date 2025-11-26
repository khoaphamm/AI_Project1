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
            body: JSON.stringify({ solver, auto_play: autoPlay })
        });

        const data = await response.json();
        
        if (data.success) {
            gameState = {
                ...gameState,
                solver: solver,
                autoPlay: autoPlay,
                gameStarted: true,
                isPaused: false,
                currentRow: 0,
                attempts: [],
                gameOver: false,
                won: false
            };

            // Enable buttons
            pauseBtn.disabled = false;
            nextBtn.disabled = false;
            restartBtn.disabled = false;

            // Reset UI
            resetBoard();
            resetKeyboard();
            clearLog();

            addLog(`New game started`);
            addLog(`Solver: ${solver.toUpperCase()}`);
            addLog(`Mode: ${autoPlay ? 'Auto Play' : 'Hint Only'}`);

            updateStats(data);

            if (!autoPlay) {
                await loadSuggestions();
            }

            if (autoPlay) {
                startAutoPlay();
            }
        }
    } catch (error) {
        console.error('Error starting game:', error);
        addLog('Error: Failed to start game');
    }
}

async function makeAIMove() {
    if (gameState.gameOver || !gameState.gameStarted) return;

    try {
        const response = await fetch(`${API_BASE}/api/make_move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        
        if (data.success) {
            addLog(`AI guesses: ${data.guess.toUpperCase()}`);
            updateBoard(data.guess, data.feedback);
            updateKeyboard(data.guess, data.feedback);
            gameState.currentRow++;
            gameState.attempts.push({ guess: data.guess, feedback: data.feedback });

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
            addLog(`Player selected: ${word.toUpperCase()}`);
            updateBoard(word, data.feedback);
            updateKeyboard(word, data.feedback);
            gameState.currentRow++;
            gameState.attempts.push({ guess: word, feedback: data.feedback });

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
            addLog(`Error: ${data.message || 'Invalid guess'}`);
        }
    } catch (error) {
        console.error('Error making player guess:', error);
        addLog('Error: Failed to make guess');
    }
}

// Handle keyboard key presses
let currentInput = '';
function handleKeyPress(key) {
    if (gameState.gameOver || !gameState.gameStarted || gameState.autoPlay) return;

    // Add letter to current input
    if (key.length === 1 && /[A-Z]/.test(key)) {
        if (currentInput.length < 5) {
            currentInput += key;
            updateCurrentRowDisplay();
        }
    }
    // Handle backspace (if we add a backspace button)
    else if (key === 'BACK' && currentInput.length > 0) {
        currentInput = currentInput.slice(0, -1);
        updateCurrentRowDisplay();
    }
    // Handle enter (if we add an enter button)
    else if (key === 'ENTER' && currentInput.length === 5) {
        const word = currentInput.toLowerCase();
        currentInput = '';
        clearCurrentRowDisplay();
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
        suggestionsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No suggestions available</p>';
        return;
    }

    suggestionsList.innerHTML = suggestions.map(([word, score]) => `
        <div class="suggestion-item" data-word="${word}">
            <span class="suggestion-word">${word.toUpperCase()}</span>
            ${score > 0 ? `<span class="suggestion-score">${score.toFixed(2)}</span>` : ''}
        </div>
    `).join('');
}

function updateBoard(guess, feedback) {
    const rows = gameBoard.querySelectorAll('.row');
    const currentRowEl = rows[gameState.currentRow];
    const tiles = currentRowEl.querySelectorAll('.tile');

    guess.split('').forEach((letter, i) => {
        const tile = tiles[i];
        tile.textContent = letter.toUpperCase();
        tile.classList.add('flip');
        
        setTimeout(() => {
            if (feedback[i] === 2) {
                tile.classList.add('green');
            } else if (feedback[i] === 1) {
                tile.classList.add('yellow');
            } else {
                tile.classList.add('gray');
            }
        }, 150);
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
    document.getElementById('attemptsCount').textContent = data.attempts || 0;
    document.getElementById('remainingWords').textContent = data.remaining_words ?? '-';
    document.getElementById('nodesVisited').textContent = data.nodes_visited || 0;
    document.getElementById('currentSolver').textContent = gameState.solver ? gameState.solver.toUpperCase() : '-';
}

function handleGameOver(won, secretWord) {
    if (won) {
        addLog(`✓ Won in ${gameState.attempts.length} attempts!`);
    } else {
        addLog(`✗ Failed. Word was: ${secretWord.toUpperCase()}`);
    }

    pauseBtn.disabled = true;
    nextBtn.disabled = true;
}

function togglePause() {
    if (!gameState.gameStarted) return;

    gameState.isPaused = !gameState.isPaused;
    pauseBtn.classList.toggle('active', gameState.isPaused);

    if (gameState.isPaused) {
        addLog('Game paused');
    } else {
        addLog('Game resumed');
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
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLog() {
    logContainer.innerHTML = '';
}

// Auto play functionality
let autoPlayInterval = null;

function startAutoPlay() {
    if (autoPlayInterval) clearInterval(autoPlayInterval);

    autoPlayInterval = setInterval(async () => {
        if (!gameState.isPaused && !gameState.gameOver && gameState.autoPlay) {
            await makeAIMove();
        } else {
            clearInterval(autoPlayInterval);
        }
    }, 2000);
}

// ===== VISUALIZATION FUNCTIONS =====

function initVisualization() {
    vizCanvas = document.getElementById('vizCanvas');
    if (vizCanvas) {
        vizCtx = vizCanvas.getContext('2d');
        // Set canvas size
        vizCanvas.width = 600;
        vizCanvas.height = 300;
        renderVisualization();
    }
}

function renderVisualization() {
    if (!vizCtx) return;

    // Clear canvas
    vizCtx.clearRect(0, 0, vizCanvas.width, vizCanvas.height);

    switch(currentVizTab) {
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
        vizCtx.fillText(`${greenCount}G ${yellowCount}Y`, x, y + nodeRadius + 12);
    });
}

function drawEntropyChart() {
    const width = vizCanvas.width;
    const height = vizCanvas.height;

    if (gameState.attempts.length === 0) {
        drawPlaceholder('Entropy chart will show information gain per guess');
        return;
    }
    
    vizCtx.clearRect(0, 0, width, height);
    
    // Draw title
    vizCtx.font = 'bold 14px monospace';
    vizCtx.fillStyle = '#89b4fa';
    vizCtx.textAlign = 'center';
    vizCtx.fillText('Word Space Reduction', width / 2, 20);

    vizCtx.fillStyle = '#cdd6f4';
    vizCtx.font = '14px monospace';

    // Draw axes
    const margin = 40;
    const chartWidth = width - margin * 2;
    const chartHeight = height - margin * 2;

    vizCtx.strokeStyle = '#585b70';
    vizCtx.beginPath();
    vizCtx.moveTo(margin, margin);
    vizCtx.lineTo(margin, height - margin);
    vizCtx.lineTo(width - margin, height - margin);
    vizCtx.stroke();

    // Draw bars
    const barWidth = Math.min(60, chartWidth / gameState.attempts.length);
    const maxEntropy = Math.max(...gameState.attempts.map((_, i) => 
        Math.log2(Math.max(1, 12953 / Math.pow(2, i + 1)))));

    gameState.attempts.forEach((attempt, index) => {
        const entropy = Math.log2(Math.max(1, 12953 / Math.pow(2, index + 1)));
        const barHeight = (entropy / maxEntropy) * chartHeight;
        const x = margin + (index * (chartWidth / gameState.attempts.length)) + 10;
        const y = height - margin - barHeight;

        vizCtx.fillStyle = '#89b4fa';
        vizCtx.fillRect(x, y, barWidth - 10, barHeight);

        vizCtx.fillStyle = '#cdd6f4';
        vizCtx.font = '10px monospace';
        vizCtx.textAlign = 'center';
        vizCtx.fillText(attempt.guess.toUpperCase().substring(0, 3), x + barWidth / 2 - 5, height - margin + 15);
    });

    // Labels
    vizCtx.fillStyle = '#a6adc8';
    vizCtx.font = '12px monospace';
    vizCtx.textAlign = 'center';
    vizCtx.fillText('Information Gain per Guess', width / 2, 20);
}

function drawSearchSpace() {
    const width = vizCanvas.width;
    const height = vizCanvas.height;

    if (gameState.attempts.length === 0) {
        drawPlaceholder('Search space visualization - shows pruning progress');
        return;
    }

    vizCtx.fillStyle = '#cdd6f4';
    vizCtx.font = '14px monospace';

    // Simulate search space reduction
    const totalWords = 12953;
    let remaining = totalWords;

    const barHeight = 30;
    const maxWidth = width - 80;

    vizCtx.fillStyle = '#a6adc8';
    vizCtx.textAlign = 'left';
    vizCtx.fillText('Search Space Reduction', 40, 30);

    gameState.attempts.forEach((attempt, index) => {
        const y = 60 + index * 50;
        
        // Background bar
        vizCtx.fillStyle = '#313244';
        vizCtx.fillRect(40, y, maxWidth, barHeight);

        // Remaining words bar
        const ratio = remaining / totalWords;
        vizCtx.fillStyle = index === gameState.attempts.length - 1 ? '#a6e3a1' : '#89b4fa';
        vizCtx.fillRect(40, y, maxWidth * ratio, barHeight);

        // Text
        vizCtx.fillStyle = '#cdd6f4';
        vizCtx.font = '11px monospace';
        vizCtx.fillText(`${attempt.guess.toUpperCase()}: ${remaining} words`, 45, y + 19);

        // Reduce for next iteration (simulation)
        remaining = Math.max(1, Math.floor(remaining / 2.5));
    });
}

function drawPlaceholder(text) {
    vizCtx.fillStyle = '#6c7086';
    vizCtx.font = '14px sans-serif';
    vizCtx.textAlign = 'center';
    vizCtx.fillText(text, vizCanvas.width / 2, vizCanvas.height / 2);
}

function updateVisualization(data) {
    if (data.guess && data.feedback) {
        gameState.visualizationData.entropy.push({
            guess: data.guess,
            remaining: data.remaining_words || 0
        });
        renderVisualization();
    }
}
