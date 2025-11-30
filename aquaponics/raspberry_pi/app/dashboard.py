from flask import Blueprint, render_template_string

dashboard_bp = Blueprint('dashboard', __name__)

# 간단한 HTML 템플릿 (CSS/JS 포함 for 실시간 그래프 및 상태 표시)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aquaponics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { margin: 0; color: #2c3e50; font-size: 1.5rem; }
        .status-badge { background: #e0e0e0; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: transform 0.2s; }
        .card:hover { transform: translateY(-2px); }
        .card h3 { margin-top: 0; color: #7f8c8d; font-size: 1rem; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        
        .value-display { display: flex; align-items: baseline; margin: 15px 0; }
        .value { font-size: 2.5rem; font-weight: bold; color: #2c3e50; margin-right: 5px; }
        .unit { font-size: 1rem; color: #95a5a6; }
        
        .status-indicator { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
        .status-ok { background: #d4edda; color: #155724; }
        .status-warning { background: #fff3cd; color: #856404; }
        .status-critical { background: #f8d7da; color: #721c24; }

        canvas { max-height: 150px; width: 100%; margin-top: 10px; }
        .footer { text-align: center; margin-top: 40px; color: #bdc3c7; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌊 Aquaponics Monitor</h1>
            <div id="system-status" class="status-badge">System: Connecting...</div>
        </div>

        <div class="grid" id="sensor-grid">
            <!-- Sensors will be injected here by JS -->
            <div class="card"><h3>Loading Sensors...</h3></div>
        </div>
        
        <div class="footer">
            Aquaponics Smart Farm v1.1.0
        </div>
    </div>

    <script>
        const sensors = ['pH', 'EC', 'Temp', 'DO', 'Level', 'Turbidity'];
        // Chart instances
        const charts = {};
        
        // Initialize UI
        function initDashboard() {
            const grid = document.getElementById('sensor-grid');
            grid.innerHTML = '';
            
            sensors.forEach(sensor => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <h3>${sensor} Sensor</h3>
                    <div class="value-display">
                        <span id="val-${sensor}" class="value">--</span>
                        <span id="unit-${sensor}" class="unit"></span>
                    </div>
                    <span id="stat-${sensor}" class="status-indicator status-ok">WAITING</span>
                    <canvas id="chart-${sensor}"></canvas>
                `;
                grid.appendChild(card);
                
                // Init Chart
                const ctx = document.getElementById(`chart-${sensor}`).getContext('2d');
                charts[sensor] = new Chart(ctx, {
                    type: 'line',
                    data: { labels: [], datasets: [{ label: sensor, data: [], borderColor: '#3498db', tension: 0.4, fill: false }] },
                    options: { 
                        responsive: true, 
                        plugins: { legend: { display: false } }, 
                        scales: { x: { display: false } } 
                    }
                });
            });
        }

        // Fetch Data
        async function updateData() {
            try {
                const res = await fetch('/api/current');
                const data = await res.json();
                
                if (data.status === 'success') {
                    document.getElementById('system-status').innerText = 'Last Update: ' + new Date(data.timestamp).toLocaleTimeString();
                    
                    const readings = data.readings;
                    const health = data.sensor_health || {};

                    sensors.forEach(sensor => {
                        // Key matching (API vs UI)
                        let apiInfo = health[sensor];
                        if (!apiInfo && sensor === 'Temp') apiInfo = health['temperature'];
                        if (!apiInfo && sensor === 'Level') apiInfo = health['water_level'];
                        
                        // Value & Unit
                        let val = 0; 
                        let unit = '';
                        
                        if (apiInfo && apiInfo.last_reading) {
                            val = apiInfo.last_reading.value;
                            unit = apiInfo.last_reading.unit;
                        } else {
                            // Fallback if health info missing
                            val = readings[sensor] !== undefined ? readings[sensor] : 
                                  (readings[sensor.toLowerCase()] || 0);
                        }

                        // Update DOM
                        const valEl = document.getElementById(`val-${sensor}`);
                        if (valEl) valEl.innerText = typeof val === 'number' ? val.toFixed(1) : val;
                        
                        const unitEl = document.getElementById(`unit-${sensor}`);
                        if (unitEl) unitEl.innerText = unit;

                        // Update Chart
                        const chart = charts[sensor];
                        if (chart) {
                            const now = new Date().toLocaleTimeString();
                            if (chart.data.labels.length > 20) {
                                chart.data.labels.shift();
                                chart.data.datasets[0].data.shift();
                            }
                            chart.data.labels.push(now);
                            chart.data.datasets[0].data.push(val);
                            chart.update();
                        }
                    });
                }
            } catch (err) {
                console.error("Fetch error:", err);
                document.getElementById('system-status').innerText = 'System: Offline';
            }
        }

        initDashboard();
        setInterval(updateData, 5000); // Update every 5s
        updateData();
    </script>
</body>
</html>
"""

@dashboard_bp.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)