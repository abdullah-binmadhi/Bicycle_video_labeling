import os

path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js"
with open(path, "r") as f:
    text = f.read()

analytics_injection = """

// --- Phase 1: Analytics & Reports ---
let confChart = null, radarChart = null, driftChart = null;
let scrubberInterval = null;

function initAnalytics() {
    // 1. Confusion Matrix
    const ctxConf = document.getElementById('confusion-canvas');
    if(ctxConf && !confChart) {
        // Simple mock of a confusion matrix using a scatter/bubble or bar 
        // For actual matrix we usually use a specialized plugin or a table, but a generic bar chart works for mockup
        confChart = new Chart(ctxConf, {
            type: 'bar',
            data: {
                labels: ['Tarmac', 'Gravel', 'Cobble', 'Pothole'],
                datasets: [{
                    label: 'True Positives',
                    data: [98, 85, 92, 76],
                    backgroundColor: 'rgba(16, 185, 129, 0.6)'
                }, {
                    label: 'False Negatives',
                    data: [2, 15, 8, 24],
                    backgroundColor: 'rgba(244, 63, 94, 0.6)'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { stacked: true }, x: { stacked: true } }
            }
        });
    }

    // 2. Radar Chart (Precision/Recall)
    const ctxRadar = document.getElementById('radar-canvas');
    if(ctxRadar && !radarChart) {
        radarChart = new Chart(ctxRadar, {
            type: 'radar',
            data: {
                labels: ['F1-Score', 'Precision', 'Recall', 'Latency', 'Robustness'],
                datasets: [{
                    label: 'CoreML Export (iOS)',
                    data: [0.91, 0.88, 0.94, 0.99, 0.85],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)'
                }, {
                    label: 'TorchScript (Android)',
                    data: [0.89, 0.90, 0.86, 0.90, 0.88],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.2)'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { r: { angleLines: { color: 'rgba(255,255,255,0.1)' }, grid: { color: 'rgba(255,255,255,0.1)' } } }
            }
        });
    }

    // 3. Drift Canvas
    const ctxDrift = document.getElementById('drift-canvas');
    if(ctxDrift && !driftChart) {
        driftChart = new Chart(ctxDrift, {
            type: 'line',
            data: {
                labels: Array.from({length: 50}, (_, i) => i),
                datasets: [{
                    label: 'Run A',
                    data: Array.from({length: 50}, () => Math.random() * 2 + 1),
                    borderColor: '#8b5cf6', borderWidth: 2, tension: 0.4
                }, {
                    label: 'Run B',
                    data: Array.from({length: 50}, () => Math.random() * 2.2 + 0.8),
                    borderColor: '#f43f5e', borderWidth: 2, tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
}

// Ensure it initializes when switching tabs
const oldSwitchView = window.switchView;
window.switchView = function(viewId) {
    oldSwitchView(viewId);
    if(viewId === 'view-analytics') {
        setTimeout(initAnalytics, 100);
    }
}

window.generatePDFReport = function() {
    showToast('Compiling analytical snapshot...', 'info');
    const elem = document.getElementById('view-analytics');
    
    // HTML2PDF settings
    const opt = {
      margin:       1,
      filename:     'CycleSafe_Report.pdf',
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(elem).save().then(() => {
        showToast('PDF Exported Successfully!', 'success');
    });
};

// --- Scrubber & FFT Mock ---
function initScrubber(videoPlayer) {
    const scrubber = document.getElementById('inf-scrubber');
    const fftCanvas = document.getElementById('fft-canvas');
    if(!scrubber || !fftCanvas) return;
    
    const ctx = fftCanvas.getContext('2d');
    
    // Mock FFT Bars
    function drawFFT() {
        if(videoPlayer.paused) return;
        ctx.clearRect(0, 0, fftCanvas.width, fftCanvas.height);
        const barWidth = 4;
        const totalBars = Math.floor(fftCanvas.width / (barWidth + 1));
        
        ctx.fillStyle = '#10b981'; // Emerald
        for(let i = 0; i < totalBars; i++) {
            const h = Math.random() * fftCanvas.height;
            ctx.fillRect(i * (barWidth + 1), fftCanvas.height - h, barWidth, h);
        }
    }
    
    if(scrubberInterval) clearInterval(scrubberInterval);
    scrubberInterval = setInterval(() => {
        if(!videoPlayer.paused && videoPlayer.duration) {
            const progress = (videoPlayer.currentTime / videoPlayer.duration) * 100;
            scrubber.value = progress;
            drawFFT();
        }
    }, 100);
    
    scrubber.addEventListener('input', (e) => {
        if(videoPlayer.duration) {
            videoPlayer.currentTime = (e.target.value / 100) * videoPlayer.duration;
        }
    });
}
"""

if "// --- Phase 1: Analytics & Reports ---" not in text:
    text += "\n" + analytics_injection
    
    # Hook initScrubber into startAIOverlay
    text = text.replace("vidPlayer.play();", "vidPlayer.play();\n    initScrubber(vidPlayer);")
    
    with open(path, "w") as f:
        f.write(text)
    print("Analytics & Scrubber logic injected into renderer.js!")
else:
    print("Analytics already injected.")
