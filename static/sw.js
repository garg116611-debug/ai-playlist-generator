// MoodTunes Service Worker for PWA
const CACHE_NAME = 'moodtunes-v1';
const OFFLINE_URL = '/';

// Assets to cache on install
const ASSETS_TO_CACHE = [
    '/',
    '/static/style.css',
    '/static/script.js',
    '/static/favicon.png',
    '/static/manifest.json'
];

// Install event - cache essential assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('MoodTunes: Caching app shell');
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('MoodTunes: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // Skip API requests (always fetch fresh)
    if (event.request.url.includes('/api/')) return;

    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    // Return cached version, but fetch update in background
                    event.waitUntil(
                        fetch(event.request)
                            .then((response) => {
                                if (response && response.status === 200) {
                                    const responseClone = response.clone();
                                    caches.open(CACHE_NAME).then((cache) => {
                                        cache.put(event.request, responseClone);
                                    });
                                }
                            })
                            .catch(() => { })
                    );
                    return cachedResponse;
                }

                // Not in cache, fetch from network
                return fetch(event.request)
                    .then((response) => {
                        // Cache successful responses
                        if (response && response.status === 200) {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(event.request, responseClone);
                            });
                        }
                        return response;
                    })
                    .catch(() => {
                        // If fetch fails, return cached homepage for navigation
                        if (event.request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }
                    });
            })
    );
});
