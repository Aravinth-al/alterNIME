/* static/js/main.js */
let sessionID = null;

// --- STEP 1: UPLOAD ---
async function handleUpload(input) {
    const file = input.files[0];
    if (!file) return;

    // Show Loading State on Upload Box
    const box = document.getElementById('upload-box');
    const originalContent = box.innerHTML;
    box.innerHTML = `<div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-yellow-500"></div>`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        
        if (data.status === 'success') {
            sessionID = data.session_id;
            transitionTo('viz');
            loadVisualization();
        } else {
            alert('Upload failed');
            box.innerHTML = originalContent;
        }
    } catch (e) {
        console.error(e);
        alert('Server Error');
        box.innerHTML = originalContent;
    }
}

// --- STEP 2: VISUALIZATION ---
async function loadVisualization() {
    const img = document.getElementById('graph-img');
    const nodeCount = document.getElementById('viz-node-count');

    try {
        const res = await fetch(`/visualize/${sessionID}`);
        const data = await res.json();
        
        img.src = data.image_url;
        nodeCount.innerText = `${data.node_count} Nodes Detected`;
        
        // Enable Next Button
        document.getElementById('viz-next-btn').disabled = false;
    } catch (e) {
        alert("Failed to visualize workflow");
    }
}

// --- STEP 3: TERMINAL STREAM ---
function startTerminal() {
    transitionTo('terminal');
    
    const terminalBody = document.getElementById('terminal-body');
    const progressBar = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    const eventSource = new EventSource(`/stream_conversion/${sessionID}`);

    eventSource.onmessage = function(e) {
        const data = JSON.parse(e.data);

        // Update Progress
        progressBar.style.width = `${data.progress}%`;
        progressText.innerText = `${data.progress}%`;

        // Check if Done
        if (data.done) {
            eventSource.close();
            setTimeout(() => {
                window.location.href = `/review/${sessionID}`;
            }, 1000);
            return;
        }

        // Add Log
        const p = document.createElement('div');
        let type = 'info';
        if (data.log.includes('AI')) type = 'ai';
        if (data.log.includes('Complete')) type = 'success';
        
        p.className = `log-line ${type}`;
        p.innerHTML = `<span class="opacity-50 text-xs mr-2">[${new Date().toLocaleTimeString()}]</span> ${data.log}`;
        
        terminalBody.appendChild(p);
        terminalBody.scrollTop = terminalBody.scrollHeight; // Auto-scroll
    };
}

// --- UTILS ---
function transitionTo(stageName) {
    document.querySelectorAll('.stage').forEach(el => {
        el.classList.remove('active');
        setTimeout(() => el.classList.add('hidden'), 500); // Wait for fade out
    });
    
    const target = document.getElementById(`stage-${stageName}`);
    target.classList.remove('hidden');
    // Small delay to allow CSS display:block to apply before opacity transition
    setTimeout(() => target.classList.add('active'), 50);
}