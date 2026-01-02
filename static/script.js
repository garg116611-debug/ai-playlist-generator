/**
 * MoodTunes - AI Playlist Generator
 * Frontend JavaScript with Language, Genre, Era, and Copy features
 */

// ========== DOM Elements ==========
const naturalInput = document.getElementById('naturalInput');
const quickGenerateBtn = document.getElementById('quickGenerate');
const presetsGrid = document.getElementById('presetsGrid');
const moodForm = document.getElementById('moodForm');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const searchQueryEl = document.getElementById('searchQuery');
const songsGrid = document.getElementById('songsGrid');
const regenerateBtn = document.getElementById('regenerateBtn');
const copyPlaylistBtn = document.getElementById('copyPlaylistBtn');
const copyFeedback = document.getElementById('copyFeedback');
const historySection = document.getElementById('historySection');
const historyList = document.getElementById('historyList');
const clearHistoryBtn = document.getElementById('clearHistory');

// Filter selects
const languageSelect = document.getElementById('languageSelect');
const genreSelect = document.getElementById('genreSelect');
const eraSelect = document.getElementById('eraSelect');
const songCountSelect = document.getElementById('songCountSelect');

// Store current songs for copy feature
let currentSongs = [];

// Audio preview management
let audioPlayer = null;
let currentlyPlayingId = null;

// ========== Activity Presets ==========
const activityPresets = [
    { name: '📚 Studying', value: 'studying' },
    { name: '💻 Coding', value: 'coding' },
    { name: '🏋️ Workout', value: 'workout' },
    { name: '😴 Sleeping', value: 'sleeping' },
    { name: '🧘 Meditation', value: 'meditation' },
    { name: '🎉 Party', value: 'party' },
    { name: '🚗 Driving', value: 'driving' },
    { name: '😢 Sad', value: 'sad' },
    { name: '😊 Happy', value: 'happy' },
    { name: '🍳 Cooking', value: 'cooking' },
    { name: '💑 Romantic', value: 'romantic' },
    { name: '😎 Chill', value: 'chill' }
];

// ========== Initialize ==========
function init() {
    renderPresets();
    loadHistory();
    setupEventListeners();
}

function renderPresets() {
    presetsGrid.innerHTML = activityPresets.map(preset =>
        `<button type="button" class="preset-btn" data-activity="${preset.value}">
            ${preset.name}
        </button>`
    ).join('');
}

function setupEventListeners() {
    // Quick generate from natural language
    quickGenerateBtn.addEventListener('click', handleQuickGenerate);

    // Enter key in natural input
    naturalInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleQuickGenerate();
        }
    });

    // Preset buttons
    presetsGrid.addEventListener('click', (e) => {
        if (e.target.classList.contains('preset-btn')) {
            const activity = e.target.dataset.activity;
            naturalInput.value = activity;
            handleQuickGenerate();
        }
    });

    // Form submission
    moodForm.addEventListener('submit', handleFormSubmit);

    // Regenerate button
    regenerateBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        copyFeedback.classList.add('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Copy playlist button
    if (copyPlaylistBtn) {
        copyPlaylistBtn.addEventListener('click', handleCopyPlaylist);
    }

    // Clear history
    clearHistoryBtn.addEventListener('click', clearHistory);
}

// ========== API Calls ==========
async function generateFromText(text, filters = {}) {
    const payload = {
        text,
        language: filters.language || 'any',
        genre: filters.genre || 'any',
        era: filters.era || 'any',
        song_count: parseInt(filters.song_count) || 5
    };

    const response = await fetch('/api/generate-from-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        throw new Error('Failed to generate playlist');
    }

    return response.json();
}

async function generateFromMood(moodData) {
    const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(moodData)
    });

    if (!response.ok) {
        throw new Error('Failed to generate playlist');
    }

    return response.json();
}

async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        return data.history || [];
    } catch {
        return [];
    }
}

async function deleteHistory() {
    await fetch('/api/history', { method: 'DELETE' });
}

// ========== Handlers ==========
async function handleQuickGenerate() {
    const text = naturalInput.value.trim();
    if (!text) {
        naturalInput.focus();
        return;
    }

    // Get filter values
    const filters = {
        language: languageSelect?.value || 'any',
        genre: genreSelect?.value || 'any',
        era: eraSelect?.value || 'any',
        song_count: songCountSelect?.value || '5'
    };

    showLoading();

    try {
        const result = await generateFromText(text, filters);
        displayResults(result);
    } catch (error) {
        showError(error.message);
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData(moodForm);
    const moodData = {
        mind_speed: formData.get('mind_speed') || 'normal',
        lyrics: formData.get('lyrics') || 'sometimes',
        context: formData.get('context') || 'alone',
        distraction: formData.get('distraction') || 'medium',
        language: formData.get('language') || 'any',
        genre: formData.get('genre') || 'any',
        era: formData.get('era') || 'any',
        song_count: parseInt(formData.get('song_count')) || 5
    };

    showLoading();

    try {
        const result = await generateFromMood(moodData);
        displayResults(result);
    } catch (error) {
        showError(error.message);
    }
}

async function handleCopyPlaylist() {
    if (currentSongs.length === 0) return;

    // Format playlist text
    const playlistText = currentSongs.map((song, i) =>
        `${i + 1}. ${song.name} - ${song.artist}`
    ).join('\n');

    const fullText = `🎵 MoodTunes Playlist:\n\n${playlistText}\n\nGenerated by MoodTunes AI`;

    try {
        await navigator.clipboard.writeText(fullText);

        // Show feedback
        copyFeedback.classList.remove('hidden');
        copyPlaylistBtn.innerHTML = '<span class="btn-icon">✅</span> Copied!';

        // Reset after 2 seconds
        setTimeout(() => {
            copyFeedback.classList.add('hidden');
            copyPlaylistBtn.innerHTML = '<span class="btn-icon">📋</span> Copy Playlist';
        }, 2000);
    } catch (err) {
        alert('Failed to copy to clipboard');
    }
}

// ========== UI Updates ==========
function showLoading() {
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    copyFeedback.classList.add('hidden');
}

function hideLoading() {
    loadingSection.classList.add('hidden');
}

function displayResults(data) {
    hideLoading();

    // Stop any currently playing audio
    stopAudioPreview();

    // Store songs for copy feature
    currentSongs = data.songs;

    // Update search query display
    searchQueryEl.textContent = `Search: "${data.query}"`;

    // Render songs with preview buttons
    songsGrid.innerHTML = data.songs.map((song, index) => `
        <div class="song-card" data-song-id="${song.id}">
            <span class="song-number">${index + 1}</span>
            ${song.preview_url ? `
                <button class="preview-btn" data-preview-url="${song.preview_url}" data-song-id="${song.id}" title="Play preview">
                    <span class="preview-icon">▶</span>
                    <span class="preview-bars hidden">
                        <span class="bar"></span>
                        <span class="bar"></span>
                        <span class="bar"></span>
                    </span>
                </button>
            ` : `
                <span class="no-preview" title="No preview available">🚫</span>
            `}
            <img src="${song.image || 'https://via.placeholder.com/56?text=🎵'}" 
                 alt="${song.name}" class="song-image">
            <div class="song-info">
                <div class="song-name">${escapeHtml(song.name)}</div>
                <div class="song-artist">${escapeHtml(song.artist)}</div>
            </div>
            <span class="song-duration">${formatDuration(song.duration_ms)}</span>
            <a href="${song.spotify_url}" target="_blank" rel="noopener" class="spotify-link" title="Open in Spotify">
                <span class="spotify-icon">🎧</span>
            </a>
        </div>
    `).join('');

    // Add preview button event listeners
    document.querySelectorAll('.preview-btn').forEach(btn => {
        btn.addEventListener('click', handlePreviewClick);
    });

    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });

    // Refresh history
    loadHistory();
}

// ========== Audio Preview ==========
function handlePreviewClick(e) {
    e.stopPropagation();
    e.preventDefault();
    const btn = e.currentTarget;
    const previewUrl = btn.dataset.previewUrl;
    const songId = btn.dataset.songId;

    console.log('Preview clicked:', { songId, previewUrl });

    if (currentlyPlayingId === songId) {
        // Stop if clicking the same song
        console.log('Stopping current song');
        stopAudioPreview();
    } else {
        // Play new song
        console.log('Playing new song:', previewUrl);
        playAudioPreview(previewUrl, songId, btn);
    }
}

function playAudioPreview(url, songId, btn) {
    // Stop any existing audio
    stopAudioPreview();

    // Create new audio
    audioPlayer = new Audio(url);
    audioPlayer.volume = 0.5;
    currentlyPlayingId = songId;

    // Update UI
    btn.classList.add('playing');
    btn.querySelector('.preview-icon').classList.add('hidden');
    btn.querySelector('.preview-bars').classList.remove('hidden');

    // Play
    audioPlayer.play().catch(err => {
        console.log('Playback failed:', err);
        stopAudioPreview();
    });

    // Handle end
    audioPlayer.addEventListener('ended', () => {
        stopAudioPreview();
    });
}

function stopAudioPreview() {
    if (audioPlayer) {
        audioPlayer.pause();
        audioPlayer = null;
    }

    // Reset UI for previously playing button
    if (currentlyPlayingId) {
        const playingBtn = document.querySelector(`.preview-btn[data-song-id="${currentlyPlayingId}"]`);
        if (playingBtn) {
            playingBtn.classList.remove('playing');
            playingBtn.querySelector('.preview-icon').classList.remove('hidden');
            playingBtn.querySelector('.preview-bars').classList.add('hidden');
        }
    }

    currentlyPlayingId = null;
}

function showError(message) {
    hideLoading();
    alert('Error: ' + message);
}

// ========== History ==========
async function loadHistory() {
    const history = await fetchHistory();

    if (history.length === 0) {
        historySection.classList.add('hidden');
        return;
    }

    historySection.classList.remove('hidden');

    historyList.innerHTML = history.reverse().map(item => `
        <div class="history-item">
            <div class="history-query">🎵 ${escapeHtml(item.query)}</div>
            <div class="history-time">${formatTime(item.timestamp)}</div>
        </div>
    `).join('');
}

async function clearHistory() {
    await deleteHistory();
    historySection.classList.add('hidden');
    historyList.innerHTML = '';
}

// ========== Utilities ==========
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDuration(ms) {
    if (!ms) return '';
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function formatTime(isoString) {
    try {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
        return '';
    }
}

// ========== Start ==========
document.addEventListener('DOMContentLoaded', init);
