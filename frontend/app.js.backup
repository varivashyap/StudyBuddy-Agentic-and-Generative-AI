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

// Check for OAuth callback
checkOAuthCallback();

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
    // Calendar mode doesn't require file upload
    if (selectedModes.has('calendar') && selectedModes.size === 1) {
        processBtn.disabled = false;
        processBtn.textContent = 'Open Calendar';
    } else if (selectedModes.has('calendar')) {
        processBtn.disabled = !uploadedFileId;
        processBtn.textContent = 'Generate Study Materials & Open Calendar';
    } else {
        processBtn.disabled = !(uploadedFileId && selectedModes.size > 0);
        processBtn.textContent = 'Generate Study Materials';
    }
}

async function processDocument() {
    // Check if calendar mode is selected
    if (selectedModes.has('calendar')) {
        // Calendar mode doesn't require file upload
        showCalendar();
        return;
    }

    if (!uploadedFileId || selectedModes.size === 0) {
        return;
    }

    showStatus('info', 'Processing document... This may take a few minutes.');
    showSpinner(true);
    processBtn.disabled = true;
    results.style.display = 'none';

    try {
        // Build requests array (exclude calendar mode)
        const requests = Array.from(selectedModes)
            .filter(mode => mode !== 'calendar')
            .map(mode => ({
                type: mode,
                parameters: getDefaultParameters(mode)
            }));

        if (requests.length === 0) {
            showStatus('info', 'No processing modes selected.');
            return;
        }

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

// Calendar functionality
function showCalendar() {
    // Check if user is authenticated
    checkAuthAndShowCalendar();
}

async function checkAuthAndShowCalendar() {
    try {
        // Check if backend calendar API is available
        const response = await fetch(`${API_URL}/calendar/events`, {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });

        console.log('Calendar auth check response:', response.status);

        if (response.status === 401) {
            // Not authenticated - show login prompt (this is expected)
            console.log('User not authenticated, showing login');
            showCalendarLogin();
            return;
        } else if (response.status === 503) {
            // Calendar integration not configured
            showStatus('error', 'Google Calendar integration is not configured. Please see GOOGLE_CALENDAR_SETUP.md for setup instructions.');
            return;
        } else if (response.ok) {
            // Authenticated - show calendar
            console.log('User authenticated, showing calendar');
            displayCalendar();
            return;
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Calendar service unavailable');
        }
    } catch (error) {
        // Network error or other issue
        console.error('Calendar error:', error);

        // If it's a network error, show a more helpful message
        if (error.message === 'Failed to fetch') {
            showStatus('error', 'Cannot connect to MCP server. Please ensure the server is running at ' + API_URL);
        } else {
            showStatus('error', `Calendar error: ${error.message}`);
        }
    }
}

function showCalendarLogin() {
    results.innerHTML = `
        <div class="result-section">
            <div class="result-title">📅 Google Calendar Integration</div>
            <div class="result-content">
                <p style="margin-bottom: 15px;">To use the calendar feature, you need to sign in with your Google account.</p>
                <button onclick="loginWithGoogle()" style="
                    padding: 12px 24px;
                    background: #4285f4;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 1em;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin: 0 auto;
                ">
                    <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd"><path d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853"/><path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z" fill="#EA4335"/></g></svg>
                    Sign in with Google
                </button>
                <p style="margin-top: 15px; font-size: 0.9em; color: #666;">
                    This will allow the app to access your Google Calendar to display and manage events.
                </p>
            </div>
        </div>
    `;
    results.style.display = 'block';
}

function loginWithGoogle() {
    // Redirect to Google OAuth
    window.location.href = `${API_URL}/auth/google`;
}

async function displayCalendar() {
    console.log('=== displayCalendar called ===');
    showStatus('info', 'Loading calendar events...');
    showSpinner(true);

    try {
        // Fetch calendar events
        console.log('Fetching calendar events from:', `${API_URL}/calendar/events`);
        const response = await fetch(`${API_URL}/calendar/events`, {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });

        console.log('Calendar events response status:', response.status);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Calendar fetch failed:', response.status, errorData);

            if (response.status === 401) {
                // Not authenticated - show login
                console.log('Not authenticated, showing login');
                showCalendarLogin();
                return;
            }

            throw new Error(errorData.error || 'Failed to fetch calendar events');
        }

        const events = await response.json();
        console.log('Received events:', events.length);

        // Display calendar view
        results.innerHTML = `
            <div class="result-section">
                <div class="result-title">📅 Your Calendar</div>
                <div class="result-content">
                    <div id="calendarView" style="min-height: 400px;">
                        ${renderCalendarEvents(events)}
                    </div>
                </div>
            </div>
        `;
        results.style.display = 'block';
        showStatus('success', `Loaded ${events.length} calendar events`);

    } catch (error) {
        console.error('Calendar display error:', error);
        showStatus('error', `Failed to load calendar: ${error.message}`);
    } finally {
        showSpinner(false);
    }
}

function renderCalendarEvents(events) {
    if (!events || events.length === 0) {
        return '<p style="text-align: center; color: #666; padding: 40px;">No upcoming events found.</p>';
    }

    // Sort events by start time
    events.sort((a, b) => new Date(a.start) - new Date(b.start));

    let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';

    events.forEach(event => {
        const startDate = new Date(event.start);
        const endDate = new Date(event.end);
        const isToday = startDate.toDateString() === new Date().toDateString();

        html += `
            <div style="
                background: white;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid ${isToday ? '#667eea' : '#e0e0e0'};
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            ">
                <div style="font-weight: 600; color: #333; margin-bottom: 5px;">
                    ${event.title || 'Untitled Event'}
                </div>
                <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">
                    📅 ${startDate.toLocaleDateString()} ${startDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    ${event.allDay ? '(All day)' : `- ${endDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`}
                </div>
                ${event.location ? `<div style="font-size: 0.9em; color: #666;">📍 ${event.location}</div>` : ''}
                ${event.description ? `<div style="font-size: 0.9em; color: #555; margin-top: 8px;">${event.description}</div>` : ''}
            </div>
        `;
    });

    html += '</div>';
    return html;
}

// Check for OAuth callback parameters
function checkOAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const authStatus = urlParams.get('auth');
    const mode = urlParams.get('mode');
    const errorMessage = urlParams.get('message');

    console.log('=== checkOAuthCallback ===');
    console.log('URL:', window.location.href);
    console.log('Auth status:', authStatus);
    console.log('Mode:', mode);
    console.log('Error message:', errorMessage);

    if (authStatus === 'success' && mode === 'calendar') {
        console.log('✅ OAuth authentication successful, showing calendar');

        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);

        // Select calendar mode
        modeOptions.forEach(option => {
            if (option.dataset.mode === 'calendar') {
                option.classList.add('selected');
                selectedModes.add('calendar');
            } else {
                option.classList.remove('selected');
            }
        });

        // Show calendar after a short delay
        setTimeout(() => {
            console.log('Calling displayCalendar...');
            displayCalendar();
        }, 500);

    } else if (authStatus === 'error') {
        console.error('❌ OAuth authentication failed:', errorMessage);

        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);

        // Show error
        showStatus('error', `Authentication failed: ${errorMessage || 'Unknown error'}`);
    } else if (authStatus || mode) {
        console.log('⚠️ Unexpected OAuth callback state');
    }
}
