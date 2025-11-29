// Study Assistant Frontend JavaScript

const API_URL = 'http://localhost:5000';

let uploadedFileId = null;
let selectedModes = new Set();

// DOM Elements
const uploadSection = document.getElementById('uploadSection');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const processBtn = document.getElementById('processBtn');
const spinner = document.getElementById('spinner');
const status = document.getElementById('status');
const results = document.getElementById('results');
const serverStatus = document.getElementById('serverStatus');
const modeOptions = document.querySelectorAll('.mode-option');

// Check server status on load
checkServerStatus();

// File upload handlers
uploadSection.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// Drag and drop
uploadSection.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadSection.classList.add('dragover');
});

uploadSection.addEventListener('dragleave', () => {
    uploadSection.classList.remove('dragover');
});

uploadSection.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadSection.classList.remove('dragover');
    
    if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

// Mode selection
modeOptions.forEach(option => {
    option.addEventListener('click', () => {
        const mode = option.dataset.mode;
        
        if (selectedModes.has(mode)) {
            selectedModes.delete(mode);
            option.classList.remove('selected');
        } else {
            selectedModes.add(mode);
            option.classList.add('selected');
        }
        
        updateProcessButton();
    });
});

// Process button
processBtn.addEventListener('click', processDocument);

// Functions
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            serverStatus.textContent = '✓ Server Online';
            serverStatus.className = 'server-status online';
        } else {
            throw new Error('Server not responding');
        }
    } catch (error) {
        serverStatus.textContent = '✗ Server Offline - Please start the MCP server';
        serverStatus.className = 'server-status offline';
    }
}

async function handleFileSelect(file) {
    // Validate file type
    const allowedTypes = ['application/pdf', 'audio/mpeg', 'audio/wav', 'audio/x-m4a', 'video/mp4'];
    const allowedExtensions = ['.pdf', '.mp3', '.wav', '.m4a', '.mp4'];
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showStatus('error', 'Invalid file type. Please upload PDF, MP3, WAV, M4A, or MP4 files.');
        return;
    }
    
    // Validate file size (100MB)
    if (file.size > 100 * 1024 * 1024) {
        showStatus('error', 'File too large. Maximum size is 100MB.');
        return;
    }
    
    // Upload file
    showStatus('info', 'Uploading file...');
    showSpinner(true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }
        
        const data = await response.json();
        uploadedFileId = data.file_id;
        
        fileInfo.textContent = `✓ ${file.name} uploaded successfully`;
        fileInfo.style.display = 'block';
        
        showStatus('success', 'File uploaded successfully! Select modes and click Generate.');
        updateProcessButton();
        
    } catch (error) {
        showStatus('error', `Upload failed: ${error.message}`);
        uploadedFileId = null;
    } finally {
        showSpinner(false);
    }
}

function updateProcessButton() {
    processBtn.disabled = !(uploadedFileId && selectedModes.size > 0);
}

async function processDocument() {
    if (!uploadedFileId || selectedModes.size === 0) {
        return;
    }
    
    showStatus('info', 'Processing document... This may take a few minutes.');
    showSpinner(true);
    processBtn.disabled = true;
    results.style.display = 'none';
    
    try {
        // Build requests array
        const requests = Array.from(selectedModes).map(mode => ({
            type: mode,
            parameters: getDefaultParameters(mode)
        }));
        
        const response = await fetch(`${API_URL}/batch-process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: uploadedFileId,
                requests: requests,
                model: 'default'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Processing failed');
        }

        const data = await response.json();

        showStatus('success', 'Processing complete!');
        displayResults(data.results);

    } catch (error) {
        showStatus('error', `Processing failed: ${error.message}`);
    } finally {
        showSpinner(false);
        updateProcessButton();
    }
}

function getDefaultParameters(mode) {
    const params = {
        summary: {
            scale: 'paragraph'
        },
        flashcards: {
            max_cards: 20,
            card_type: 'definition'
        },
        quiz: {
            num_questions: 10,
            question_type: 'mcq'
        }
    };

    return params[mode] || {};
}

function displayResults(resultsData) {
    results.innerHTML = '';

    // Display summary
    if (resultsData.summary && resultsData.summary.success) {
        const summarySection = document.createElement('div');
        summarySection.className = 'result-section';
        summarySection.innerHTML = `
            <div class="result-title">📝 Summary</div>
            <div class="result-content">${resultsData.summary.data.summary}</div>
        `;
        results.appendChild(summarySection);
    }

    // Display flashcards
    if (resultsData.flashcards && resultsData.flashcards.success) {
        const flashcardsSection = document.createElement('div');
        flashcardsSection.className = 'result-section';

        let flashcardsHTML = `
            <div class="result-title">🎴 Flashcards (${resultsData.flashcards.data.count})</div>
        `;

        resultsData.flashcards.data.flashcards.forEach((card, index) => {
            flashcardsHTML += `
                <div class="flashcard">
                    <div class="flashcard-front">Q: ${card.front}</div>
                    <div class="flashcard-back">A: ${card.back}</div>
                </div>
            `;
        });

        flashcardsSection.innerHTML = flashcardsHTML;
        results.appendChild(flashcardsSection);
    }

    // Display quiz
    if (resultsData.quiz && resultsData.quiz.success) {
        const quizSection = document.createElement('div');
        quizSection.className = 'result-section';

        let quizHTML = `
            <div class="result-title">❓ Quiz Questions (${resultsData.quiz.data.count})</div>
        `;

        resultsData.quiz.data.questions.forEach((q, index) => {
            quizHTML += `
                <div class="question">
                    <div class="question-text">${index + 1}. ${q.question}</div>
            `;

            if (q.options) {
                quizHTML += '<div class="question-options">';
                q.options.forEach((opt, i) => {
                    const letter = String.fromCharCode(65 + i);
                    quizHTML += `<div class="question-option">${letter}. ${opt}</div>`;
                });
                quizHTML += '</div>';
            }

            quizHTML += `<div style="margin-top: 10px; color: #388e3c;"><strong>Answer:</strong> ${q.answer}</div>`;
            quizHTML += '</div>';
        });

        quizSection.innerHTML = quizHTML;
        results.appendChild(quizSection);
    }

    results.style.display = 'block';
}

function showStatus(type, message) {
    status.className = `status ${type}`;
    status.textContent = message;
    status.style.display = 'block';

    // Auto-hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            status.style.display = 'none';
        }, 5000);
    }
}

function showSpinner(show) {
    spinner.style.display = show ? 'block' : 'none';
}

