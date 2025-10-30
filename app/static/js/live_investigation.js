// static/js/live_investigation.js
document.addEventListener('DOMContentLoaded', function () {
    const livePageContainer = document.querySelector('.live-modal-container');
    
    if (livePageContainer) {
        const investigationId = livePageContainer.dataset.investigationId;

        // Camera and Time Logic
        // const video = document.getElementById('camera-feed');
        // if (video && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        //     navigator.mediaDevices.getUserMedia({ video: true })
        //         .then(stream => { video.srcObject = stream; })
        //         .catch(err => { console.error("Error accessing camera: ", err); });
        // }
        
        const timeElement = document.getElementById('live-time');
        if (timeElement) {
            const updateTime = () => timeElement.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            setInterval(updateTime, 1000);
            updateTime();
        }

        // --- Capture Logic with Fetch API ---
        const captureBtn = document.getElementById('capture-btn');
        const captureCountDisplay = document.getElementById('capture-count-display'); // Get the counter element

        // Initialize a variable to hold the count
        let totalCaptures = parseInt(captureCountDisplay.textContent.replace(/\D/g, ''), 10) || 0;

        if (captureBtn) {
            captureBtn.addEventListener('click', () => {
                const canvas = document.getElementById('canvas');
                const capturesGrid = document.getElementById('captures-grid');
                if (!canvas || !capturesGrid || !video || video.readyState < 3) return;

                const context = canvas.getContext('2d');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const dataUrl = canvas.toDataURL('image/jpeg');
                
                captureBtn.disabled = true;
                captureBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

                fetch(`/investigation/${investigationId}/capture`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_data: dataUrl })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const maxThumbnails = 12;
                        if (capturesGrid.children.length >= maxThumbnails) {
                            capturesGrid.removeChild(capturesGrid.lastChild); // Remove the oldest
                        }
                        const img = document.createElement('img');
                        img.src = data.image_url;
                        img.classList.add('capture-thumbnail');
                        capturesGrid.prepend(img); // Add new capture to the start
                        // ===== START: NEW COUNTER LOGIC =====
                        totalCaptures++; // Increment the count
                        captureCountDisplay.textContent = `(${totalCaptures})`; // Update the display
                        // ===== END: NEW COUNTER LOGIC =====
                    } else {
                        console.error('Failed to save capture:', data.error);
                    }
                })
                .catch(error => console.error('Error during capture:', error))
                .finally(() => {
                    captureBtn.disabled = false;
                    captureBtn.innerHTML = '<i class="fas fa-camera"></i> Capture';
                });
            });
        }

        // Pause/Complete/Close Logic
        // Depends on showConfirmationModal() from the main script.js
        livePageContainer.addEventListener('click', function(e) {
            const pauseButton = e.target.closest('.status-action-btn.pause');
            const completeButton = e.target.closest('.status-action-btn.complete');
            const closeButton = e.target.closest('#live-modal-close-btn');

            if (!pauseButton && !completeButton && !closeButton) return;
            e.preventDefault();

            const id = livePageContainer.dataset.investigationId;
            const title = livePageContainer.dataset.investigationTitle;

            if (pauseButton || closeButton) {
                showConfirmationModal({
                    title: 'Pause Investigation',
                    message: `This will pause the investigation and return you to the main screen. Proceed?`,
                    confirmText: 'Yes, Pause',
                    newStatus: 'Pending',
                    formAction: `/investigation/${id}/update_status`
                });
            } else if (completeButton) {
                showConfirmationModal({
                    title: 'Complete Investigation',
                    message: `Are you sure you want to mark <strong>${title}</strong> as complete?`,
                    confirmText: 'Yes, Complete',
                    newStatus: 'Completed',
                    formAction: `/investigation/${id}/update_status`
                });
            }
        });
        // ===== START: NEW DRONE SPEAKER MODAL LOGIC =====
        const API_URL = "http://10.84.160.98:5000"; // Drone/Pi's IP Address

        // Get modal elements
        const speakerModal = document.getElementById('drone-speaker-modal-overlay');
        const openSpeakerBtn = document.getElementById('open-drone-speaker-modal');
        const closeSpeakerBtn = document.getElementById('drone-speaker-modal-close-btn');
        const uploadForm = document.getElementById('drone-upload-form');
        const stopBtn = document.getElementById('drone-stop-btn');
        const statusDiv = document.getElementById('drone-status');

        if (speakerModal && openSpeakerBtn && closeSpeakerBtn && uploadForm && stopBtn && statusDiv) {
            // Open/Close listeners
            openSpeakerBtn.addEventListener('click', () => speakerModal.classList.add('active'));
            closeSpeakerBtn.addEventListener('click', () => speakerModal.classList.remove('active'));
            speakerModal.addEventListener('click', (e) => {
                if (e.target === speakerModal) {
                    speakerModal.classList.remove('active');
                }
            });

            // Upload & Play Logic
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('drone-music-file');
                const volume = document.getElementById('drone-volume').value;

                if (!fileInput.files.length) {
                    statusDiv.innerText = "Please select an audio file first!";
                    return;
                }

                const formData = new FormData();
                formData.append("file", fileInput.files[0]);
                formData.append("volume", volume);
                statusDiv.innerText = "Uploading and sending command...";

                try {
                    const res = await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
                    const data = await res.json();
                    statusDiv.innerText = data.message || "Success! Music is playing.";
                } catch (err) {
                    statusDiv.innerText = "Error: Could not connect to the drone's audio system.";
                    console.error(err);
                }
            });

            // Stop Music Logic
            stopBtn.addEventListener('click', async () => {
                statusDiv.innerText = "Sending stop command...";
                try {
                    const res = await fetch(`${API_URL}/stop`, { method: "POST" });
                    const data = await res.json();
                    statusDiv.innerText = data.message;
                } catch (err) {
                    statusDiv.innerText = "Error: Could not connect to the drone's audio system.";
                    console.error(err);
                }
            });
        }
        // ===== END: NEW DRONE SPEAKER MODAL LOGIC =====
        
    }
    // ===== START: NEW AI ASSISTANT LOGIC =====
    const aiModal = document.getElementById('ai-assistant-modal-overlay');
    const openAiBtn = document.getElementById('open-ai-assistant-modal');
    const closeAiBtn = document.getElementById('ai-assistant-modal-close-btn');
    const controlBtn = document.getElementById('ai-control-btn');
    const historyContainer = document.getElementById('ai-conversation-history');
    const statusDot = document.querySelector('#ai-status-indicator .status-dot');
    const statusText = document.querySelector('#ai-status-indicator .status-text');

    let isAssistantListening = false;
    let conversationHistory = [{
        role: "system",
        content: "You are a disaster-response assistant. Be extremely concise. Respond in the same language the user speaks and be very concise and to the point and clear speak in same language as user"
    }];
    let mediaRecorder;
    let audioChunks = [];

    // --- Modal Control ---
    openAiBtn.addEventListener('click', () => aiModal.classList.add('active'));
    closeAiBtn.addEventListener('click', stopAssistant);
    aiModal.addEventListener('click', (e) => {
        if (e.target === aiModal) stopAssistant();
    });

    // --- Main Control Button ---
    controlBtn.addEventListener('click', () => {
        isAssistantListening = !isAssistantListening;
        if (isAssistantListening) {
            startAssistant();
        } else {
            stopAssistant();
        }
    });

    function startAssistant() {
        isAssistantListening = true;
        controlBtn.classList.add('active');
        historyContainer.innerHTML = `<div class="chat-bubble ai"><i class="fas fa-robot"></i><p>I'm listening...</p></div>`;
        conversationHistory = conversationHistory.slice(0, 1); // Reset history but keep system prompt
        runAssistantCycle();
    }

    function stopAssistant() {
        isAssistantListening = false;
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
        controlBtn.classList.remove('active');
        setStatus('Inactive', '');
        aiModal.classList.remove('active');
    }

    // --- Main Interaction Loop ---
    async function runAssistantCycle() {
        if (!isAssistantListening) return;
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                stream.getTracks().forEach(track => track.stop()); // Turn off mic
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                processAudio(audioBlob);
            };

            setStatus('Listening...', 'listening');
            mediaRecorder.start();
            setTimeout(() => {
                if (mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                }
            }, 5000); // Record for 5 seconds

        } catch (err) {
            console.error("Microphone access error:", err);
            setStatus('Mic Error', '');
            isAssistantListening = false;
            controlBtn.classList.remove('active');
        }
    }

    // Replace the entire processAudio function with this one
    async function processAudio(audioBlob) {
        if (!isAssistantListening) return;

        setStatus('Processing...', 'processing');
        const formData = new FormData();
        formData.append('audio_data', audioBlob, 'recording.wav');
        formData.append('history', JSON.stringify(conversationHistory));

        try {
            const response = await fetch('/voice-assistant', { method: 'POST', body: formData });
            
            if (!response.ok) {
                // Handle server errors (like 500)
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // SCENARIO 1: Speech was detected and processed
            if (data.user_text) {
                addBubble(data.user_text, 'user');
                conversationHistory.push({ role: 'user', content: data.user_text });
                
                setStatus('Thinking...', 'processing');
                addBubble(data.ai_reply_text, 'ai');
                conversationHistory.push({ role: 'assistant', content: data.ai_reply_text });

                if (data.ai_reply_audio) {
                    setStatus('Speaking...', 'speaking');
                    const audio = new Audio("data:audio/mp3;base64," + data.ai_reply_audio);
                    audio.play();
                    audio.onended = () => {
                        if (isAssistantListening) {
                        setTimeout(runAssistantCycle, 500); // Listen again after speaking
                        }
                    };
                } else {
                    // AI replied with text but no audio, listen again
                    if (isAssistantListening) {
                        setTimeout(runAssistantCycle, 500);
                    }
                }
            // SCENARIO 2: No speech was detected by the backend
            } else {
                // Just listen again immediately without showing any message
                if (isAssistantListening) {
                    runAssistantCycle();
                }
            }

        } catch (error) {
            console.error("AI Assistant Error:", error);
            // Don't show an error bubble, just try listening again
            if (isAssistantListening) {
                setStatus('Retrying...', 'processing');
                setTimeout(runAssistantCycle, 1000); // Wait a second before retrying
            }
        }
    }

    // --- UI Helper Functions ---
    function setStatus(text, className) {
        statusText.textContent = text;
        statusDot.className = 'status-dot'; // Reset classes
        if (className) {
            statusDot.classList.add(className);
        }
    }

    function addBubble(text, role) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;
        const iconClass = role === 'user' ? 'fa-user' : 'fa-robot';
        bubble.innerHTML = `<i class="fas ${iconClass}"></i><p>${text}</p>`;
        historyContainer.appendChild(bubble);
        historyContainer.scrollTop = historyContainer.scrollHeight; // Auto-scroll
    }
    // ===== END: NEW AI ASSISTANT LOGIC =====
});