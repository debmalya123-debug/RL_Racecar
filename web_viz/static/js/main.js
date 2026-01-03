const canvas = document.getElementById('raceCanvas');
const ctx = canvas.getContext('2d');
const socket = io();

// UI Elements
const genEl = document.getElementById('gen-count');
const aliveEl = document.getElementById('alive-count');
const speedRange = document.getElementById('speedRange');
const speedVal = document.getElementById('speedVal');
const pauseBtn = document.getElementById('pauseBtn');
const restartBtn = document.getElementById('restartBtn');
const logBody = document.getElementById('logBody');

let cars = [];
let generation = 1;
const trails = {}; // Store paths: {id: [{x,y}, ...]}
let particles = []; // Explosion particles

// --- SOCKET EVENTS ---
socket.on('connect', () => {
    console.log('Connected');
    document.title = "Connected - Race Sim Pro";
});

socket.on('update', (data) => {
    cars = data.cars;
    aliveEl.innerText = data.alive;
    
    // Process Updates (Trails & FX)
    cars.forEach(car => {
        // 1. Trails
        if (!trails[car.id]) trails[car.id] = [];
        
        if (car.alive) {
            trails[car.id].push({x: car.x, y: car.y});
            if (trails[car.id].length > 100) trails[car.id].shift(); // Limit trail length
        }
        
        // 2. Explosions
        if (car.crashed) {
            spawnExplosion(car.x, car.y, car.color);
        }
    });

    draw();
});

socket.on('reset', (data) => {
    generation = data.generation;
    genEl.innerText = generation;
    // Clear trails on new gen
    for (let key in trails) trails[key] = [];
    particles = [];
});

socket.on('hard_reset', (data) => {
    generation = data.generation;
    genEl.innerText = generation;
    // Clear trails
    for (let key in trails) trails[key] = [];
    particles = [];
    // Clear Log
    logBody.innerHTML = ''; 
});

socket.on('pause_state', (data) => {
    if (data.paused) {
        pauseBtn.classList.add('paused');
        pauseBtn.innerText = '▶'; // Play icon
    } else {
        pauseBtn.classList.remove('paused');
        pauseBtn.innerText = '⏸'; // Pause icon
    }
});

socket.on('gen_log', (data) => {
    // 1. Update Table
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${data.generation}</td>
        <td>${data.distance}</td>
        <td>${data.epsilon}</td>
    `;
    logBody.insertBefore(row, logBody.firstChild);
    
    // 2. Update Chart
    if (perfChart) {
        perfChart.data.labels.push(data.generation);
        perfChart.data.datasets[0].data.push(data.distance);
        perfChart.data.datasets[1].data.push(data.epsilon);
        perfChart.update();
    }
});

socket.on('hard_reset', (data) => {
    generation = data.generation;
    genEl.innerText = generation;
    // Clear trails
    for (let key in trails) trails[key] = [];
    particles = [];
    // Clear Log
    logBody.innerHTML = ''; 
    // Clear Chart
    if (perfChart) {
        perfChart.data.labels = [];
        perfChart.data.datasets[0].data = [];
        perfChart.data.datasets[1].data = [];
        perfChart.update();
    }
});

// --- CHART INIT ---
const perfChartCtx = document.getElementById('perfChart').getContext('2d');
const perfChart = new Chart(perfChartCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Best Distance',
            borderColor: '#ff7675',
            backgroundColor: 'rgba(255, 118, 117, 0.2)',
            data: [],
            yAxisID: 'y',
            tension: 0.3
        }, {
            label: 'Epsilon (Exploration)',
            borderColor: '#74b9ff',
            backgroundColor: 'rgba(116, 185, 255, 0.2)',
            data: [],
            yAxisID: 'y1',
            tension: 0.3,
            borderDash: [5, 5]
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                grid: { color: '#f1f2f6' }
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                grid: { drawOnChartArea: false }
            }
        }
    }
});

// --- CONTROLS ---
pauseBtn.addEventListener('click', () => {
    socket.emit('toggle_pause');
});

restartBtn.addEventListener('click', () => {
    if(confirm("Are you sure you want to Hard Reset the simulation? All learning progress will be lost.")) {
        socket.emit('restart_sim');
    }
});

speedRange.addEventListener('input', (e) => {
    const val = e.target.value;
    speedVal.innerText = val + 'x';
    socket.emit('set_speed', {speed: val});
});

// --- 3D / ISO CONSTANTS ---
const WALL_HEIGHT = 12; // Slightly lower for clean look
const CAR_HEIGHT = 6;
const CENTER_L = {x: 200, y: 300};
const CENTER_R = {x: 600, y: 300};
const R_OUT = 200;
const R_IN = 100;

function drawPseudo3DTrack() {
    // 1. Draw "Walls" (Extrusion)
    // We draw bottom-up
    
    for (let h = 0; h < WALL_HEIGHT; h++) {
        let isTop = (h === WALL_HEIGHT - 1);
        let yOffset = -h; 
        
        ctx.lineCap = 'round';
        
        if (isTop) {
            ctx.shadowBlur = 0;
            ctx.strokeStyle = '#b2bec3'; // Light Grey Top
        } else {
            // Side of wall (Darker gradient)
            let shade = 100 + (h * 5); 
            ctx.strokeStyle = `rgb(${shade}, ${shade}, ${shade})`;
        }
        
        ctx.lineWidth = 2; // Thinner, crisper lines
        
        // Outer Path
        ctx.beginPath();
        ctx.arc(CENTER_R.x, CENTER_R.y + yOffset, R_OUT, -Math.PI/2, Math.PI/2); 
        ctx.arc(CENTER_L.x, CENTER_L.y + yOffset, R_OUT, Math.PI/2, 3*Math.PI/2);
        ctx.closePath();
        ctx.stroke();

        // Inner Path
        ctx.beginPath();
        ctx.arc(CENTER_R.x, CENTER_R.y + yOffset, R_IN, -Math.PI/2, Math.PI/2);
        ctx.arc(CENTER_L.x, CENTER_L.y + yOffset, R_IN, Math.PI/2, 3*Math.PI/2);
        ctx.closePath();
        ctx.stroke();
    }
    
    // Fill the Track Surface (Ground) at Base Level
    ctx.globalCompositeOperation = 'destination-over'; 
    
    // Outer Fill (Asphalt)
    ctx.fillStyle = '#2d3436'; // Dark Asphalt
    ctx.beginPath();
    ctx.arc(CENTER_R.x, CENTER_R.y, R_OUT, -Math.PI/2, Math.PI/2);
    ctx.arc(CENTER_L.x, CENTER_L.y, R_OUT, Math.PI/2, 3*Math.PI/2);
    ctx.closePath();
    ctx.fill();

    // -- TRACK MARKINGS (Lane Lines) --
    // We draw a dashed line in the center (Radius = 150)
    ctx.globalCompositeOperation = 'source-over'; // Draw ON TOP of asphalt
    
    ctx.beginPath();
    ctx.arc(CENTER_R.x, CENTER_R.y, 150, -Math.PI/2, Math.PI/2);
    ctx.arc(CENTER_L.x, CENTER_L.y, 150, Math.PI/2, 3*Math.PI/2);
    ctx.closePath();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 2;
    ctx.setLineDash([15, 15]); // Dashed line
    ctx.stroke();
    ctx.setLineDash([]); // Reset
    
    // -- SOLID EDGES (White Lines) --
    // Outer Edge (White Line)
    ctx.beginPath();
    ctx.arc(CENTER_R.x, CENTER_R.y, R_OUT - 5, -Math.PI/2, Math.PI/2);
    ctx.arc(CENTER_L.x, CENTER_L.y, R_OUT - 5, Math.PI/2, 3*Math.PI/2);
    ctx.closePath();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Inner Edge (White Line)
    ctx.beginPath();
    ctx.arc(CENTER_R.x, CENTER_R.y, R_IN + 5, -Math.PI/2, Math.PI/2);
    ctx.arc(CENTER_L.x, CENTER_L.y, R_IN + 5, Math.PI/2, 3*Math.PI/2);
    ctx.closePath();
    ctx.stroke();

    // Inner Hole (Clear/Bg) - Fill with Canvas BG
    ctx.globalCompositeOperation = 'source-over'; 
    ctx.fillStyle = '#e0e5ec'; // Match page background
    
    ctx.beginPath();
    ctx.arc(CENTER_R.x, CENTER_R.y, R_IN, -Math.PI/2, Math.PI/2);
    ctx.arc(CENTER_L.x, CENTER_L.y, R_IN, Math.PI/2, 3*Math.PI/2);
    ctx.closePath();
    ctx.fill();
    
    // Finish Line (Checkerboard)
    let fx = 400;
    let fy_start = 100; // Top Straight Y range: 100-200 (Center 150)
    
    // Draw 3 rows of checks
    for(let r=0; r<3; r++) {
         for(let i=0; i<10; i++) { // 100px width / 10px = 10 cols
             let y = fy_start + i*10;
             let x = fx + r*6 - 9; // Width of line
             let isWhite = (i+r)%2===0;
             ctx.fillStyle = isWhite ? '#fff' : '#000';
             ctx.fillRect(x, y, 6, 10);
         }
    }
}

function drawPseudo3DCar(car) {
    if (!car.alive) return;

    // --- SENSOR FOV (Active RADAR) ---
    // Remove fake cone, draw functional beams
    
    if (car.sensors && car.sensors.length > 0) {
        ctx.save();
        ctx.translate(car.x, car.y);
        ctx.rotate(car.angle);
        
        car.sensors.forEach(sensor => {
           let dist = sensor[0];
           let angle = sensor[1];
           let maxDist = 200;
           
           let endX = Math.cos(angle) * dist;
           let endY = Math.sin(angle) * dist;
           
           // Color Logic: HSL transition
           // 100% (200px) = 120 (Green)
           // 0% (0px) = 0 (Red)
           let normalized = Math.max(0, Math.min(1, dist / maxDist));
           let hue = normalized * 120; 
           let color = `hsla(${hue}, 100%, 50%, 0.8)`;
           
           // Ray (Gradient)
           let grd = ctx.createLinearGradient(0, 0, endX, endY);
           grd.addColorStop(0, `hsla(${hue}, 100%, 50%, 0.1)`); // Faint at car
           grd.addColorStop(1, color); // Bright at wall
           
           ctx.beginPath();
           ctx.moveTo(0,0);
           ctx.lineTo(endX, endY);
           ctx.strokeStyle = grd;
           ctx.lineWidth = 1.5;
           ctx.stroke();
           
           // Hit Marker (If hit wall)
           if (dist < maxDist - 5) {
                // Glow
                ctx.shadowBlur = 10;
                ctx.shadowColor = color;
                
                // Outer Ring
                ctx.beginPath();
                ctx.arc(endX, endY, 3, 0, Math.PI*2);
                ctx.strokeStyle = color;
                ctx.stroke();
                
                // Inner Dot
                ctx.fillStyle = '#fff';
                ctx.beginPath();
                ctx.arc(endX, endY, 1.5, 0, Math.PI*2);
                ctx.fill();
                
                ctx.shadowBlur = 0; // Reset
           }
        });
        
        ctx.restore();
    }

    // --- 3D CAR BODY ---
    // Minimalist, Clean Shading
    
    let carColor = car.color;
    
    ctx.save();
    ctx.translate(car.x, car.y);
    ctx.rotate(car.angle);

    // Casting Shadow (Drop shadow on ground)
    ctx.fillStyle = 'rgba(0,0,0,0.2)';
    ctx.beginPath();
    ctx.moveTo(12, 0); ctx.lineTo(-10, 8); ctx.lineTo(-10, -8);
    ctx.closePath();
    ctx.fill();

    // Car Layers
    for(let h=0; h<CAR_HEIGHT; h++) {
        let isTop = (h === CAR_HEIGHT - 1);
        let scale = 1.0 - (h*0.03); 
        
        ctx.save();
        ctx.translate(0, -h); 
        ctx.scale(scale, scale);
        
        ctx.fillStyle = carColor;
        
        if (!isTop) {
            // Darken sides
            ctx.filter = 'brightness(70%)';
        } else {
             ctx.filter = 'brightness(110%)'; // Highlight top
        }

        ctx.beginPath();
        // Slightly more distinct F1 shape
        ctx.moveTo(14, 0); // Nose
        ctx.lineTo(-6, 8); // Rear R
        ctx.lineTo(-6, -8); // Rear L
        ctx.closePath();
        ctx.fill();
        
        ctx.restore();
    }
    
    // Cockpit
    ctx.translate(0, -CAR_HEIGHT);
    ctx.fillStyle = '#2d3436';
    ctx.beginPath();
    ctx.moveTo(4, 0); ctx.lineTo(-2, 3); ctx.lineTo(-2, -3);
    ctx.fill();
    
    ctx.restore();
}

function spawnExplosion(x, y, color) {
    for (let i = 0; i < 20; i++) {
        particles.push({
            x: x,
            y: y,
            vx: (Math.random() - 0.5) * 8, // Random velocity
            vy: (Math.random() - 0.5) * 8,
            life: 1.0,
            color: color
        });
    }
}

function drawParticles() {
    for (let i = particles.length - 1; i >= 0; i--) {
        let p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.05; // Fade out
        
        if (p.life <= 0) {
            particles.splice(i, 1);
            continue;
        }
        
        ctx.globalAlpha = p.life;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4 * p.life, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1.0;
    }
}

function drawTrail(carId, color) {
    const path = trails[carId];
    if (!path || path.length < 2) return;
    
    ctx.beginPath();
    ctx.moveTo(path[0].x, path[0].y);
    for (let i = 1; i < path.length; i++) {
       ctx.lineTo(path[i].x, path[i].y);
    }
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.5; // Transparent trails
    ctx.stroke();
    ctx.globalAlpha = 1.0;
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    drawPseudo3DTrack();
    
    // Draw Trails (Below cars)
    cars.forEach(car => {
        drawTrail(car.id, car.color);
    });
    
    // Sort cars for Z-order
    let sortedCars = [...cars].sort((a,b) => a.y - b.y);
    sortedCars.forEach(drawPseudo3DCar);
    
    // Draw Explosions (Top layer)
    drawParticles();
}
