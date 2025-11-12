// Application state
let selectedFiles = [];
let queueRefreshInterval = null;
let historyVisible = false;

// DOM Elements
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const selectedFilesContainer = document.getElementById('selected-files');
const uploadForm = document.getElementById('upload-form');
const submitBtn = document.getElementById('submit-btn');
const queueContainer = document.getElementById('queue-container');
const historyContainer = document.getElementById('history-container');
const refreshQueueBtn = document.getElementById('refresh-queue-btn');
const toggleHistoryBtn = document.getElementById('toggle-history-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    checkSystemStatus();
    loadQueue();
    startQueueAutoRefresh();
});

// Event Listeners
function initializeEventListeners() {
    // Upload area click
    uploadArea.addEventListener('click', () => fileInput.click());

    // File selection
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // Form submission
    uploadForm.addEventListener('submit', handleFormSubmit);

    // Queue refresh
    refreshQueueBtn.addEventListener('click', loadQueue);

    // History toggle
    toggleHistoryBtn.addEventListener('click', toggleHistory);

    // Prevent default drag behavior
    document.addEventListener('dragover', (e) => e.preventDefault());
    document.addEventListener('drop', (e) => e.preventDefault());
}

// File Selection Handlers
function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');

    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
}

function addFiles(files) {
    // Filter valid files
    const validFiles = files.filter(file => {
        const extension = file.name.split('.').pop().toLowerCase();
        const validExtensions = ['pdf', 'txt', 'jpg', 'jpeg', 'png'];

        if (!validExtensions.includes(extension)) {
            showToast(`${file.name}: Invalid file type`, 'error');
            return false;
        }

        if (file.size > 20 * 1024 * 1024) {
            showToast(`${file.name}: File too large (max 20 MB)`, 'error');
            return false;
        }

        return true;
    });

    selectedFiles = [...selectedFiles, ...validFiles];
    renderSelectedFiles();
    updateSubmitButton();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderSelectedFiles();
    updateSubmitButton();
}

function renderSelectedFiles() {
    if (selectedFiles.length === 0) {
        selectedFilesContainer.innerHTML = '';
        return;
    }

    selectedFilesContainer.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <div class="file-info">
                <svg class="file-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <span class="file-name">${file.name}</span>
                <span class="file-size">(${formatFileSize(file.size)})</span>
            </div>
            <button type="button" class="remove-file" onclick="removeFile(${index})">
                <svg class="remove-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `).join('');
}

function updateSubmitButton() {
    submitBtn.disabled = selectedFiles.length === 0;
}

// Form Submission
async function handleFormSubmit(e) {
    e.preventDefault();

    if (selectedFiles.length === 0) {
        showToast('Please select at least one file', 'error');
        return;
    }

    const formData = new FormData();

    // Add files
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    // Add options
    formData.append('copies', document.getElementById('copies').value);
    formData.append('duplex', document.getElementById('duplex').checked);

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner"></div> Submitting...';

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Show success for each file
            data.results.forEach(result => {
                if (result.success) {
                    showToast(`${result.filename}: ${result.message}`, 'success');
                } else {
                    showToast(`${result.filename}: ${result.error}`, 'error');
                }
            });

            // Clear form
            selectedFiles = [];
            renderSelectedFiles();
            fileInput.value = '';
            document.getElementById('copies').value = 1;
            document.getElementById('duplex').checked = false;

            // Refresh queue
            loadQueue();
        } else {
            showToast(data.error || 'Failed to submit print jobs', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
        console.error('Upload error:', error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
            <svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print
        `;
        updateSubmitButton();
    }
}

// Queue Management
async function loadQueue() {
    try {
        const response = await fetch('/api/queue');
        const data = await response.json();

        if (data.success) {
            renderQueue(data.queue);
        } else {
            queueContainer.innerHTML = `<p class="empty-state">Error loading queue: ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Queue load error:', error);
        queueContainer.innerHTML = '<p class="empty-state">Error loading queue</p>';
    }
}

function renderQueue(queue) {
    if (queue.length === 0) {
        queueContainer.innerHTML = `
            <div class="empty-state">
                <svg class="empty-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>No jobs in queue</p>
            </div>
        `;
        return;
    }

    queueContainer.innerHTML = `
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Job ID</th>
                        <th>Filename</th>
                        <th>Copies</th>
                        <th>Duplex</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${queue.map(job => `
                        <tr>
                            <td>#${job.job_id}</td>
                            <td>${job.filename}</td>
                            <td>${job.copies}</td>
                            <td>${job.duplex ? 'Yes' : 'No'}</td>
                            <td><span class="status-badge status-${job.status}">${capitalizeFirst(job.status)}</span></td>
                            <td>
                                <button class="action-btn danger" onclick="cancelJob('${job.job_id}')">Cancel</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function cancelJob(jobId) {
    if (!confirm(`Cancel job #${jobId}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/cancel/${jobId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            loadQueue();
        } else {
            showToast(data.error || 'Failed to cancel job', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
        console.error('Cancel error:', error);
    }
}

function startQueueAutoRefresh() {
    // Refresh every 5 seconds
    queueRefreshInterval = setInterval(loadQueue, 5000);
}

// History Management
async function toggleHistory() {
    historyVisible = !historyVisible;

    if (historyVisible) {
        historyContainer.classList.remove('collapsed');
        toggleHistoryBtn.innerHTML = `
            <svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
            </svg>
            Hide
        `;
        await loadHistory();
    } else {
        historyContainer.classList.add('collapsed');
        toggleHistoryBtn.innerHTML = `
            <svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            Show
        `;
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();

        if (data.success) {
            renderHistory(data.history);
        } else {
            historyContainer.innerHTML = `<p class="empty-state">Error loading history: ${data.error}</p>`;
        }
    } catch (error) {
        console.error('History load error:', error);
        historyContainer.innerHTML = '<p class="empty-state">Error loading history</p>';
    }
}

function renderHistory(history) {
    if (history.length === 0) {
        historyContainer.innerHTML = `
            <div class="empty-state">
                <svg class="empty-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p>No print history</p>
            </div>
        `;
        return;
    }

    historyContainer.innerHTML = `
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Filename</th>
                        <th>Copies</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.map(job => `
                        <tr>
                            <td>${formatDate(job.submitted_at)}</td>
                            <td>${job.filename}</td>
                            <td>${job.copies}${job.duplex ? ' (Duplex)' : ''}</td>
                            <td><span class="status-badge status-${job.status}">${capitalizeFirst(job.status)}</span></td>
                            <td>
                                <button class="action-btn" onclick="reprintJob('${job.job_id}')">Reprint</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function reprintJob(jobId) {
    try {
        const response = await fetch(`/api/reprint/${jobId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            loadQueue();
        } else {
            showToast(data.error || 'Failed to reprint job', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
        console.error('Reprint error:', error);
    }
}

// System Status
async function checkSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.success && data.status.cups_available) {
            statusDot.classList.add('online');
            statusText.textContent = 'Printer Online';
        } else {
            statusDot.classList.add('offline');
            statusText.textContent = 'Printer Offline';
        }
    } catch (error) {
        statusDot.classList.add('offline');
        statusText.textContent = 'Connection Error';
        console.error('Status check error:', error);
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success'
        ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />'
        : type === 'error'
        ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />'
        : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />';

    toast.innerHTML = `
        <svg class="toast-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            ${icon}
        </svg>
        <div class="toast-message">${message}</div>
    `;

    toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
