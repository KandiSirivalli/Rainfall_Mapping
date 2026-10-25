/**
 * DeepRain-Ops v7.6.2 | Dashboard Logic
 * Handles 7.3.1 Fusion Math and 7.5.1 Forecaster Decisions
 */

// 1. Radar Priority Calculation (Section 7.3.1)
// Uses the 4/3 Earth Radius Model to rank radars by beam altitude
async function loadRadarPriority() {
    try {
        const response = await fetch('/api/calculate_mosaic', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ distance: 75.0 }) // Standard 75km range test
        });
        const data = await response.json();
        const listContainer = document.getElementById('radar-list');
        
        if (!listContainer) return;

        listContainer.innerHTML = data.map((radar, index) => `
            <div class="p-3 ${index === 0 ? 'bg-blue-900/40 border-l-4 border-blue-500 shadow-lg' : 'bg-slate-800/50 border border-slate-700'} rounded-lg transition-all hover:bg-slate-700/50 mb-2">
                <div class="flex justify-between items-center">
                    <div>
                        <span class="text-[10px] font-bold text-slate-500 uppercase">${index === 0 ? 'Primary' : 'Secondary'}</span>
                        <h4 class="text-sm font-black text-white">${radar.id}</h4>
                    </div>
                    <div class="text-right">
                        <div class="text-[10px] text-blue-400 font-mono">ALT: ${radar.altitude} km</div>
                        <div class="text-[9px] text-slate-500 uppercase">Weight: ${radar.weight || 'AUTO'}</div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error("Radar priority sync failed:", err);
    }
}

// 2. Forecaster Decision Ingestion (Section 7.5.1)
// Records whether the human expert chose DL or traditional Z-R
async function submitDecision(type) {
    const val = document.getElementById('manual-estimate').value;
    const btnText = type === 'DL' ? "Confirming AI..." : "Applying Z-R...";
    
    console.log(`Decision Event: ${type} | Value: ${val} mm/hr`);

    // In a live environment, this sends to the /api/ingest_gauge endpoint
    try {
        const res = await fetch('/api/ingest_gauge', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ site_id: 'USER_OVERRIDE', value: val })
        });
        
        if (res.ok) {
            alert(`DECISION LOGGED\nType: ${type}\nValue: ${val} mm/hr\nStatus: DB Synced`);
        }
    } catch (e) {
        alert("Sync Error: Local database unreachable.");
    }
}

// 3. Dynamic Simulation Trigger (Section 7.2.2)
// Generates 30 days of data to populate the Reports module
async function runSimulation() {
    const btn = document.getElementById('simBtn');
    const originalText = btn.innerText;
    
    btn.innerText = "GENERATING LOGS...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/simulate_data', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ site_id: 'KRTX' })
        });
        
        if (response.ok) {
            alert("SIMULATION SUCCESSFUL\n30 records added to 'tuning_logs'.\nCheck the Reports page for performance metrics.");
            loadRadarPriority(); // Refresh priority list
        }
    } catch (err) {
        alert("Simulation Error: Check Flask terminal for logs.");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// 4. Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadRadarPriority();
    console.log("DeepRain-Ops System Initialized: WebSocket Simulation Ready.");
});