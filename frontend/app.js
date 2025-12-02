// Study Assistant Frontend - Modern Dark Theme
const API_URL = 'http://localhost:5000';

// State
let uploadedFileId = null;
let selectedFeature = null;
let isAuthenticated = false;
let chatHistory = [];

// DOM Elements
const loginPage = document.getElementById('loginPage');
const mainApp = document.getElementById('mainApp');
const uploadSection = document.getElementById('uploadSection');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusMessage = document.getElementById('statusMessage');
const resultsSection = document.getElementById('resultsSection');
const resultTitle = document.getElementById('resultTitle');
const resultContent = document.getElementById('resultContent');
const spinner = document.getElementById('spinner');

// Initialize
checkAuthStatus();

// Authentication
function checkAuthStatus() {
    // Check if user is authenticated via URL params or stored token
    const urlParams = new URLSearchParams(window.location.search);
    const authStatus = urlParams.get('auth');
    
    if (authStatus === 'success') {
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
        showMainApp();
    } else {
        // Check if we have a stored auth token
        fetch(`${API_URL}/calendar/events`, { credentials: 'include' })
            .then(response => {
                if (response.ok || response.status === 200) {
                    showMainApp();
                } else {
                    showLoginPage();
                }
            })
            .catch(() => showLoginPage());
    }
}

function showLoginPage() {
    loginPage.style.display = 'flex';
    mainApp.style.display = 'none';
    isAuthenticated = false;
}

function showMainApp() {
    loginPage.style.display = 'none';
    mainApp.style.display = 'block';
    isAuthenticated = true;
}

function loginWithGoogle() {
    window.location.href = `${API_URL}/auth/google`;
}

// File Upload
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

async function handleFileSelect(file) {
    // Display file info
    fileName.textContent = `📄 ${file.name}`;
    fileSize.textContent = `Size: ${(file.size / 1024 / 1024).toFixed(2)} MB`;
    fileInfo.classList.add('show');
    
    // Show progress
    progressContainer.classList.add('show');
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading...';
    
    // Upload file
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = `${progress}%`;
            }
        }, 200);
        
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        const data = await response.json();
        uploadedFileId = data.file_id;
        
        progressFill.style.width = '100%';
        progressText.textContent = 'Upload complete!';
        
        showStatus('success', '✅ File uploaded successfully! Select a feature to continue.');
        
        setTimeout(() => {
            progressContainer.classList.remove('show');
        }, 2000);
        
    } catch (error) {
        console.error('Upload error:', error);
        showStatus('error', '❌ Upload failed. Please try again.');
        progressContainer.classList.remove('show');
    }
}

// Feature Selection
function selectFeature(feature) {
    if (!uploadedFileId) {
        showStatus('error', '⚠️ Please upload a file first!');
        return;
    }
    
    selectedFeature = feature;
    
    // Update UI
    document.querySelectorAll('.feature-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-feature="${feature}"]`).classList.add('active');

    // Process based on feature
    if (feature === 'chatbot') {
        showChatbot();
    } else {
        processFeature(feature);
    }
}

// Process Feature (Summary, Quiz, Flashcards)
async function processFeature(feature) {
    showSpinner(true);
    showStatus('info', `⏳ Generating ${feature}...`);
    resultsSection.classList.remove('show');

    try {
        const response = await fetch(`${API_URL}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: uploadedFileId,
                request_type: feature,
                model_name: 'default'
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to generate ${feature}`);
        }

        const data = await response.json();
        displayResults(feature, data);
        showStatus('success', `✅ ${feature.charAt(0).toUpperCase() + feature.slice(1)} generated successfully!`);

    } catch (error) {
        console.error(`${feature} error:`, error);
        showStatus('error', `❌ Failed to generate ${feature}. Please try again.`);
    } finally {
        showSpinner(false);
    }
}

// Display Results
function displayResults(feature, data) {
    resultsSection.classList.add('show');

    const icons = {
        summary: '📝',
        quiz: '❓',
        flashcards: '🎴'
    };

    resultTitle.innerHTML = `${icons[feature]} ${feature.charAt(0).toUpperCase() + feature.slice(1)}`;

    // Extract result from response (handle both data.result and direct data)
    const result = data.result || data;

    if (feature === 'summary') {
        const summaryText = result.summary || result || 'No summary generated';
        resultContent.innerHTML = `
            <div style="background: var(--bg-primary); padding: 20px; border-radius: 12px; line-height: 1.8;">
                ${summaryText.replace(/\n/g, '<br>')}
            </div>
        `;
    } else if (feature === 'quiz') {
        const questions = result.questions || result || [];
        resultContent.innerHTML = renderQuiz(questions);
    } else if (feature === 'flashcards') {
        const flashcards = result.flashcards || result || [];
        resultContent.innerHTML = renderFlashcards(flashcards);
    }

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Render Quiz
function renderQuiz(questions) {
    let html = '<div style="display: flex; flex-direction: column; gap: 20px;">';

    questions.forEach((q, index) => {
        html += `
            <div style="background: var(--bg-primary); padding: 20px; border-radius: 12px;">
                <div style="font-weight: 600; margin-bottom: 15px; font-size: 1.1em;">
                    ${index + 1}. ${q.question}
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px;">
        `;

        q.options.forEach((option, optIndex) => {
            html += `
                <div style="background: var(--bg-tertiary); padding: 12px; border-radius: 8px; cursor: pointer;"
                     onclick="checkAnswer(${index}, ${optIndex}, '${q.correct_answer}')">
                    ${option}
                </div>
            `;
        });

        html += `
                </div>
                <div id="answer-${index}" style="margin-top: 15px; display: none;"></div>
            </div>
        `;
    });

    html += '</div>';
    return html;
}

function checkAnswer(questionIndex, selectedIndex, correctAnswer) {
    const answerDiv = document.getElementById(`answer-${questionIndex}`);
    const isCorrect = String.fromCharCode(65 + selectedIndex) === correctAnswer;

    answerDiv.style.display = 'block';
    answerDiv.innerHTML = isCorrect
        ? '<div style="color: var(--success); font-weight: 600;">✅ Correct!</div>'
        : `<div style="color: var(--error); font-weight: 600;">❌ Incorrect. Correct answer: ${correctAnswer}</div>`;
}

// Render Flashcards
function renderFlashcards(flashcards) {
    let html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;">';

    flashcards.forEach((card, index) => {
        html += `
            <div class="flashcard" style="background: var(--bg-primary); padding: 25px; border-radius: 12px; cursor: pointer; transition: transform 0.3s;"
                 onclick="flipCard(${index})">
                <div id="card-front-${index}">
                    <div style="font-weight: 600; margin-bottom: 10px; color: var(--accent-primary);">Question</div>
                    <div>${card.front}</div>
                </div>
                <div id="card-back-${index}" style="display: none;">
                    <div style="font-weight: 600; margin-bottom: 10px; color: var(--accent-secondary);">Answer</div>
                    <div>${card.back}</div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    return html;
}

function flipCard(index) {
    const front = document.getElementById(`card-front-${index}`);
    const back = document.getElementById(`card-back-${index}`);

    if (front.style.display === 'none') {
        front.style.display = 'block';
        back.style.display = 'none';
    } else {
        front.style.display = 'none';
        back.style.display = 'block';
    }
}

// Chatbot
function showChatbot() {
    resultsSection.classList.add('show');
    resultTitle.innerHTML = '💬 Chatbot';

    resultContent.innerHTML = `
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="chat-message assistant">
                    <div class="message-avatar assistant">🤖</div>
                    <div class="message-content">
                        Hello! I'm your study assistant. Ask me anything about the material you uploaded!
                    </div>
                </div>
            </div>
            <div class="chat-input-container">
                <input type="text" class="chat-input" id="chatInput" placeholder="Ask a question..."
                       onkeypress="if(event.key==='Enter') sendMessage()">
                <button class="chat-send-btn" onclick="sendMessage()">Send</button>
            </div>
        </div>
    `;

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const message = chatInput.value.trim();

    if (!message) return;

    // Add user message to chat
    chatMessages.innerHTML += `
        <div class="chat-message user">
            <div class="message-avatar user">👤</div>
            <div class="message-content">${message}</div>
        </div>
    `;

    chatInput.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Add loading indicator
    const loadingId = 'loading-' + Date.now();
    chatMessages.innerHTML += `
        <div class="chat-message assistant" id="${loadingId}">
            <div class="message-avatar assistant">🤖</div>
            <div class="message-content">
                <div class="spinner" style="width: 20px; height: 20px; margin: 0;"></div>
            </div>
        </div>
    `;
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: uploadedFileId,
                request_type: 'chatbot',
                model_name: 'default',
                parameters: {
                    message: message,
                    session_id: uploadedFileId
                }
            })
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        const data = await response.json();

        // Remove loading indicator
        document.getElementById(loadingId).remove();

        // Extract response from result object
        const botResponse = data.result?.response || data.response || 'No response received';

        // Add assistant response
        chatMessages.innerHTML += `
            <div class="chat-message assistant">
                <div class="message-avatar assistant">🤖</div>
                <div class="message-content">${botResponse}</div>
            </div>
        `;

        chatMessages.scrollTop = chatMessages.scrollHeight;

    } catch (error) {
        console.error('Chat error:', error);
        document.getElementById(loadingId).remove();
        chatMessages.innerHTML += `
            <div class="chat-message assistant">
                <div class="message-avatar assistant">🤖</div>
                <div class="message-content" style="color: var(--error);">
                    Sorry, I encountered an error. Please try again.
                </div>
            </div>
        `;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Calendar
function openCalendar() {
    // Check authentication and show calendar
    fetch(`${API_URL}/calendar/events`, { credentials: 'include' })
        .then(response => {
            if (response.status === 401) {
                // Not authenticated - redirect to Google OAuth
                window.location.href = `${API_URL}/auth/google`;
            } else if (response.ok) {
                return response.json();
            } else {
                throw new Error('Calendar not available');
            }
        })
        .then(events => {
            if (events) {
                displayCalendar(events);
            }
        })
        .catch(error => {
            console.error('Calendar error:', error);
            showStatus('error', '❌ Calendar not available. Please ensure Google Calendar is set up.');
        });
}

function displayCalendar(events) {
    resultsSection.classList.add('show');
    resultTitle.innerHTML = '📅 Your Calendar';

    let html = '<div style="display: flex; flex-direction: column; gap: 15px;">';

    if (events.length === 0) {
        html += '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">No upcoming events</div>';
    } else {
        events.forEach(event => {
            const startDate = new Date(event.start);
            const endDate = new Date(event.end);
            const isToday = startDate.toDateString() === new Date().toDateString();

            html += `
                <div style="background: var(--bg-primary); padding: 20px; border-radius: 12px;
                            border-left: 4px solid ${isToday ? 'var(--accent-primary)' : 'var(--border-color)'};">
                    <div style="font-weight: 600; font-size: 1.2em; margin-bottom: 8px;">
                        ${event.summary || 'Untitled Event'}
                    </div>
                    <div style="color: var(--text-secondary); margin-bottom: 5px;">
                        📅 ${startDate.toLocaleDateString()} ${startDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        ${event.allDay ? '(All day)' : `- ${endDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`}
                    </div>
                    ${event.location ? `<div style="color: var(--text-secondary);">📍 ${event.location}</div>` : ''}
                    ${event.description ? `<div style="color: var(--text-secondary); margin-top: 8px;">${event.description}</div>` : ''}
                </div>
            `;
        });
    }

    html += '</div>';
    resultContent.innerHTML = html;
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Utility Functions
function showStatus(type, message) {
    statusMessage.className = `status-message ${type} show`;
    statusMessage.textContent = message;

    setTimeout(() => {
        statusMessage.classList.remove('show');
    }, 5000);
}

function showSpinner(show) {
    spinner.classList.toggle('hidden', !show);
}

