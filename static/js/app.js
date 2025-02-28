// static/js/app.js
// Add language mapping after DOM elements
const LANGUAGE_MAPPING = {
    'en-US': { assembly: 'en_us', openai: 'en', display: 'EN-US' },
    'en-GB': { assembly: 'en_uk', openai: 'en', display: 'EN-GB' },
    'en-AU': { assembly: 'en_au', openai: 'en', display: 'EN-AU' },
    'en-CA': { assembly: 'en_ca', openai: 'en', display: 'EN-CA' },
    'ja': { assembly: 'ja', openai: 'ja', display: 'JA' },
    'zh': { assembly: 'zh', openai: 'zh', display: 'ZH' },
    'de': { assembly: 'de', openai: 'de', display: 'DE' },
    'hi': { assembly: 'hi', openai: 'hi', display: 'HI' },
    'fr-FR': { assembly: 'fr_fr', openai: 'fr', display: 'FR-FR' },
    'fr-CA': { assembly: 'fr_ca', openai: 'fr', display: 'FR-CA' },
    'ko': { assembly: 'ko', openai: 'ko', display: 'KO' },
    'pt-BR': { assembly: 'pt_br', openai: 'pt', display: 'PT-BR' },
    'pt-PT': { assembly: 'pt_pt', openai: 'pt', display: 'PT-PT' },
    'it': { assembly: 'it', openai: 'it', display: 'IT' },
    'es-ES': { assembly: 'es_es', openai: 'es', display: 'ES-ES' },
    'es-MX': { assembly: 'es_mx', openai: 'es', display: 'ES-MX' },
    'nl': { assembly: 'nl', openai: 'nl', display: 'NL' },
    'tr': { assembly: 'tr', openai: 'tr', display: 'TR' },
    'pl': { assembly: 'pl', openai: 'pl', display: 'PL' },
    'fi': { assembly: 'fi', openai: 'fi', display: 'FI' },
    'uk': { assembly: 'uk', openai: 'uk', display: 'UK' },
    'ru': { assembly: 'ru', openai: 'ru', display: 'RU' }
};

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const speakButton = document.getElementById('speakButton');
    const transcriptOutput = document.getElementById('transcriptOutput');
    const translationOutput = document.getElementById('translationOutput');
    const statusIndicator = document.getElementById('statusIndicator');
    const sourceLanguage = document.getElementById('sourceLanguage');
    const targetLanguage = document.getElementById('targetLanguage');
    const sourceTag = document.getElementById('sourceTag');
    const targetTag = document.getElementById('targetTag');
    
    // Application state
    let socket = null;
    let isConnected = false;
    let isListening = false;
    let currentTranslation = '';
    
    // Update the updateLanguageTags function
    function updateLanguageTags() {
        const sourceLang = LANGUAGE_MAPPING[sourceLanguage.value];
        const targetLang = LANGUAGE_MAPPING[targetLanguage.value];
        
        sourceTag.textContent = sourceLang.display;
        targetTag.textContent = targetLang.display;
        
        if (isConnected) {
            socket.send(JSON.stringify({
                command: 'update_languages',
                source_language: sourceLang.assembly,
                target_language: targetLang.openai
            }));
        }
    }
        
    // Event listeners for language selectors
    sourceLanguage.addEventListener('change', updateLanguageTags);
    targetLanguage.addEventListener('change', updateLanguageTags);
    
    // Initialize language tags
    updateLanguageTags();
    
    // Connect to WebSocket
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/medical-translator`;
        
        socket = new WebSocket(wsUrl);
        
        socket.onopen = function() {
            console.log('WebSocket connected');
            isConnected = true;
            updateStatus('Connected', 'success');
            
            // Send initial configuration
            socket.send(JSON.stringify({
                source_language: sourceLanguage.value,
                target_language: targetLanguage.value
            }));
            
            // Enable start button
            startButton.disabled = false;
        };
        
        socket.onclose = function() {
            console.log('WebSocket disconnected');
            isConnected = false;
            isListening = false;
            updateStatus('Disconnected. Reconnecting...', 'error');
            
            // Disable buttons
            startButton.disabled = true;
            stopButton.disabled = true;
            speakButton.disabled = true;
            
            // Try to reconnect after a delay
            setTimeout(connectWebSocket, 3000);
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
            updateStatus('Connection error', 'error');
        };
        
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
            
            switch(data.type) {
                case 'config_received':
                    console.log('Configuration received');
                    break;
                    
                case 'listening_started':
                    isListening = true;
                    startButton.disabled = true;
                    stopButton.disabled = false;
                    updateStatus('Listening...', 'listening');
                    break;
                    
                case 'listening_stopped':
                    isListening = false;
                    startButton.disabled = false;
                    stopButton.disabled = true;
                    updateStatus('Stopped listening', 'success');
                    break;
                
                case 'transcript':
                    if (data.text) {
                        // Remove placeholder if present
                        const placeholder = transcriptOutput.querySelector('.placeholder-text');
                        if (placeholder) {
                            transcriptOutput.removeChild(placeholder);
                        }
                        
                        // For interim transcripts, update or create single interim element
                        if (!data.is_final) {
                            let interimElement = transcriptOutput.querySelector('.transcript.interim');
                            if (!interimElement) {
                                interimElement = document.createElement('div');
                                interimElement.className = 'transcript interim';
                                transcriptOutput.appendChild(interimElement);
                            }
                            interimElement.innerHTML = `<span class="timestamp">[${new Date().toLocaleTimeString()}]</span> ${data.text}`;
                        } else {
                            // For final transcripts, replace interim with final
                            const interimElement = transcriptOutput.querySelector('.transcript.interim');
                            if (interimElement) {
                                transcriptOutput.removeChild(interimElement);
                            }
                            
                            const finalElement = document.createElement('div');
                            finalElement.className = 'transcript final';
                            finalElement.innerHTML = `<span class="timestamp">[${new Date().toLocaleTimeString()}]</span> ${data.text}`;
                            transcriptOutput.appendChild(finalElement);
                        }
                        
                        // Auto-scroll to bottom
                        transcriptOutput.scrollTop = transcriptOutput.scrollHeight;
                    }
                    break;
                    
                case 'translation':
                    // Update translation area
                    if (data.text) {
                        // Remove placeholder if present
                        const placeholder = translationOutput.querySelector('.placeholder-text');
                        if (placeholder) {
                            translationOutput.removeChild(placeholder);
                        }
                        
                        // Store current translation for speak button
                        currentTranslation = data.text;
                        
                        // Create new translation element with timestamp
                        const translationElement = document.createElement('div');
                        translationElement.className = 'translation';
                        
                        const timestamp = new Date().toLocaleTimeString();
                        translationElement.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${data.text}`;
                        
                        // Add to translation output
                        translationOutput.appendChild(translationElement);
                        
                        // Auto-scroll to bottom
                        translationOutput.scrollTop = translationOutput.scrollHeight;
                        
                        // Enable speak button
                        speakButton.disabled = false;
                        
                        // Log to console
                        console.log(`Translation: ${data.text}`);
                    }
                    break;
                    
                case 'audio_starting':
                    updateStatus('Playing audio...', 'info');
                    speakButton.disabled = true;
                    break;
                    
                case 'audio_completed':
                    updateStatus('Audio completed', 'success');
                    speakButton.disabled = false;
                    setTimeout(() => {
                        if (isListening) {
                            updateStatus('Listening...', 'listening');
                        } else {
                            updateStatus('Ready', '');
                        }
                    }, 2000);
                    break;
                    
                case 'error':
                    console.error('Error from server:', data.message);
                    updateStatus(`Error: ${data.message}`, 'error');
                    break;
                    
                case 'languages_updated':
                    console.log(`Languages updated: ${data.source_language} → ${data.target_language}`);
                    break;
                    
                case 'pong':
                    // Keep-alive response, no action needed
                    break;
                    
                default:
                    console.log('Unknown message type:', data.type);
            }
        };
    }
    
    // Update status indicator
    function updateStatus(message, className) {
        statusIndicator.textContent = message;
        statusIndicator.className = 'status-indicator';
        if (className) {
            statusIndicator.classList.add(className);
        }
    }
    
    // Button event listeners
    startButton.addEventListener('click', function() {
        if (!isConnected) {
            updateStatus('Not connected. Reconnecting...', 'error');
            connectWebSocket();
            return;
        }
        
        socket.send(JSON.stringify({
            command: 'start_listening'
        }));
    });
    
    stopButton.addEventListener('click', function() {
        socket.send(JSON.stringify({
            command: 'stop_listening'
        }));
    });
    
    speakButton.addEventListener('click', function() {
        if (!currentTranslation) {
            updateStatus('No translation to speak', 'error');
            return;
        }
        
        socket.send(JSON.stringify({
            command: 'speak',
            text: currentTranslation
        }));
    });
    
    // Keep-alive function to prevent connection timeout
    function sendPing() {
        if (isConnected) {
            socket.send(JSON.stringify({
                command: 'ping'
            }));
        }
    }
    
    // Send ping every 30 seconds
    setInterval(sendPing, 30000);
    
    // Connect on page load
    connectWebSocket();
    
    // Page visibility change handling
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            // Reconnect if needed when page becomes visible
            if (!isConnected) {
                connectWebSocket();
            }
        }
    });
    
    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        if (socket) {
            socket.close();
        }
    });
});