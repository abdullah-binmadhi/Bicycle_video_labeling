import os

path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js"
with open(path, "r") as f:
    text = f.read()

# Make sure we don't duplicate
if "// --- Phase 2 Globals ---" not in text:
    injection = """
// --- Phase 2 Globals ---
let infMap = null;
let threeScene = null, threeCamera = null, threeRenderer = null, threeCube = null;

function initLeaflet(lat=52.5200, lng=13.4050) {
    if(!infMap) {
        const mapContainer = document.getElementById('inf-map');
        if(!mapContainer) return;
        
        infMap = L.map('inf-map').setView([lat, lng], 16);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(infMap);
    }
}

function initThreeJS() {
    if(threeRenderer) return;
    const container = document.getElementById('inf-3d-canvas');
    if(!container) return;
    container.innerHTML = ''; // clear text
    
    threeScene = new THREE.Scene();
    threeCamera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    
    threeRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    threeRenderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(threeRenderer.domElement);
    
    // Create a bike/phone stand-in geometry
    const geometry = new THREE.BoxGeometry(2, 0.5, 4);
    
    // Fancy wireframe + material
    const material = new THREE.MeshBasicMaterial( { color: 0xf59e0b, wireframe: true } );
    threeCube = new THREE.Mesh(geometry, material);
    threeScene.add(threeCube);
    
    threeCamera.position.z = 5;
    threeCamera.position.y = 2;
    threeCamera.lookAt(0,0,0);
    
    // Add grid helper
    const gridHelper = new THREE.GridHelper(10, 10, 0x475569, 0x1e293b);
    threeScene.add(gridHelper);
    
    function animate() {
        requestAnimationFrame(animate);
        threeRenderer.render(threeScene, threeCamera);
    }
    animate();
    
    // Handle resize
    window.addEventListener('resize', () => {
        if(!threeCamera || !container.clientWidth) return;
        threeCamera.aspect = container.clientWidth / container.clientHeight;
        threeCamera.updateProjectionMatrix();
        threeRenderer.setSize(container.clientWidth, container.clientHeight);
    });
}
"""
    # Insert just before window.startAIOverlay
    text = text.replace("window.startAIOverlay = function() {", injection + "\nwindow.startAIOverlay = function() {")

    # Patch startAIOverlay inner logic
    start_str = "showToast('Engaging Physics Array network...', 'success');\n    \n    // Play video automatically"
    text = text.replace(start_str, """showToast('Engaging Physics Array network...', 'success');
    
    // Init Phase 2 components
    setTimeout(() => {
        initLeaflet();
        initThreeJS();
        
        // Add a mock path trace to Leaflet to show concept
        if(infMap) {
            const startLat = 52.5200;
            const startLng = 13.4050;
            const latlngs = [];
            let curl = startLat, curlg = startLng;
            for(let i=0; i<50; i++) {
                latlngs.push([curl, curlg]);
                curl += (Math.random() - 0.5) * 0.001;
                curlg += (Math.random() - 0.5) * 0.001;
            }
            L.polyline(latlngs, {color: '#10b981', weight: 4}).addTo(infMap);
            infMap.fitBounds(L.latLngBounds(latlngs));
            
            // force invalidate size a moment later when dom settles
            setTimeout(() => infMap.invalidateSize(), 500);
        }
    }, 500);
    
    // Play video automatically""")

    # Patch the setInterval logic to animate 3d model
    anim_target = """const s = surfaces[Math.floor(Math.random() * surfaces.length)];
             label.innerText = s.t;
             label.className = `text-2xl font-black tracking-widest transition-colors duration-300 ${s.c}`;"""
             
    anim_replacement = """const s = surfaces[Math.floor(Math.random() * surfaces.length)];
             label.innerText = s.t;
             label.className = `text-2xl font-black tracking-widest transition-colors duration-300 ${s.c}`;
             
             if(threeCube) {
                 threeCube.rotation.x = s.t.includes("ROUGH") ? 0.2 : (s.t.includes("POTHOLE") ? 0.5 : 0);
                 threeCube.rotation.z = (Math.random() - 0.5) * 0.3;
             }"""
    
    if anim_target in text:
        text = text.replace(anim_target, anim_replacement)

    with open(path, "w") as f:
        f.write(text)
    
    print("renderer.js updated successfully.")
else:
    print("Already updated.")