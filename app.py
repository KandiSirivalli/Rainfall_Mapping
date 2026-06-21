import sqlite3
import math
import os
import random
import pandas as pd
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

# Internal Modules (Ensuring these remain integrated as per your structure)
# from model_logic import get_initialized_model 
# from modules.dashboard_logic import DashboardMetrics
# from modules.report_generator import ReportGenerator
# from modules.data_ingestion import DataIngestor

base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            static_folder=os.path.join(base_dir, 'static'),
            template_folder=os.path.join(base_dir, 'templates'))

DB_PATH = os.path.join(base_dir, 'database.db')

# --- Database Initialization ---
def init_db():
    """Initializes the 5-column schema required for Section 7.2.2."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Radar Metadata Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS radars 
        (id TEXT PRIMARY KEY, name TEXT, h_ant REAL, tilt REAL, network TEXT, frequency TEXT)''')
    
    # Operational Logs Table (The 5-column core)
    cursor.execute('''CREATE TABLE IF NOT EXISTS tuning_logs 
        (site_id TEXT, timestamp TEXT, gauge_mm_hr REAL, dl_estimate REAL, rmse_step REAL)''')
    
    # Seed Radar Data if empty
    cursor.execute("SELECT count(*) FROM radars")
    if cursor.fetchone()[0] == 0:
        radar_sites = [('KRTX', 'Seattle, WA', 0.49, 0.5, 'NEXRAD', 'S-band'),
                       ('KATX', 'Portland, OR', 0.52, 0.5, 'NEXRAD', 'S-band'),
                       ('MF_PAR', 'Paris, FR', 0.35, 0.5, 'MeteoFrance', 'C-band')]
        cursor.executemany("INSERT INTO radars VALUES (?, ?, ?, ?, ?, ?)", radar_sites)
    
    conn.commit()
    conn.close()

init_db()

# --- Page Routes ---
@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/reports')
def reports_page():
    conn = sqlite3.connect(DB_PATH)
    # Load all logs into a DataFrame for calculation
    df = pd.read_sql_query("SELECT * FROM tuning_logs", conn)
    
    # Default values if table is empty
    stats = {
        "rmse_val": "0.00",
        "bias_val": "0.0%",
        "parity_val": "0.0%",
        "state": "INITIALIZING"
    }

    if not df.empty:
        # 1. RMSE Calculation
        avg_rmse = df['rmse_step'].mean()
        stats["rmse_val"] = f"{avg_rmse:.3f}"

        # 2. Bias Reduction (Comparing Gauge Mean vs AI Mean)
        gauge_mean = df['gauge_mm_hr'].mean()
        ai_mean = df['dl_estimate'].mean()
        bias = ((ai_mean - gauge_mean) / gauge_mean) * 100 if gauge_mean != 0 else 0
        stats["bias_val"] = f"{bias:+.1f}%"

        # 3. Network Parity (Consistency across sites)
        # We define parity as 100% minus the coefficient of variation of RMSE
        if len(df['site_id'].unique()) > 1:
            site_errors = df.groupby('site_id')['rmse_step'].mean()
            parity = 100 - (site_errors.std() / site_errors.mean() * 100 if site_errors.mean() != 0 else 0)
            stats["parity_val"] = f"{max(0, min(100, parity)):.1f}%"
        else:
            stats["parity_val"] = "95.0%" # Baseline for single-site

        # 4. System State Logic
        stats["state"] = "FINE-TUNED" if avg_rmse < 0.5 else "CALIBRATING"

    # Fetch last 30 for the table/chart
    conn.row_factory = sqlite3.Row
    logs = conn.execute("SELECT * FROM tuning_logs ORDER BY timestamp DESC LIMIT 30").fetchall()
    conn.close()
    
    return render_template('reports.html', logs=logs, stats=stats)
# --- API Endpoints ---

@app.route('/api/simulate_data', methods=['POST'])
def simulate_data():
    """Generates a Gaussian Storm Pulse for realistic analytical reporting."""
    site_id = request.json.get('site_id', 'KRTX')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Section 7.6 logic: Mimic a passing storm front (30-hour pulse)
    for i in range(30):
        center, width, peak = 15, 5, 35.0
        # Gaussian distribution formula for intensity
        g_val = peak * math.exp(-(i - center)**2 / (2 * width**2))
        g_val = max(0.1, round(g_val + random.uniform(-1.2, 1.2), 2))
        
        # DL Estimate with simulated high-precision (within 0.5mm/hr variance)
        dl_est = round(g_val + random.uniform(-0.4, 0.4), 2)
        rmse = round(abs(g_val - dl_est), 3)
        ts = (datetime.now() - timedelta(hours=30-i)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("INSERT INTO tuning_logs (site_id, timestamp, gauge_mm_hr, dl_estimate, rmse_step) VALUES (?, ?, ?, ?, ?)", 
                       (site_id, ts, g_val, dl_est, rmse))
    
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Storm Front simulation complete"})

@app.route('/api/calculate_mosaic', methods=['POST'])
def calculate_mosaic():
    """4/3 Earth Radius Model for Section 7.3.1."""
    dist = request.json.get('distance', 75.0)
    RE_EFF = 6371.0 * (4/3) # Atmospheric refraction constant
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    radars = conn.execute("SELECT * FROM radars").fetchall()
    conn.close()
    
    results = []
    for r in radars:
        theta_rad = math.radians(r['tilt'])
        # Precise beam altitude formula
        h_beam = r['h_ant'] + (dist * math.sin(theta_rad)) + (dist**2 / (2 * RE_EFF))
        results.append({
            "id": r['id'], 
            "altitude": round(h_beam, 3),
            "network": r['network']
        })
        
    return jsonify(sorted(results, key=lambda x: x['altitude']))

@app.route('/api/ingest_gauge', methods=['POST'])
def ingest_gauge():
    """Manual Forecaster Override Integration (Section 7.5.1)."""
    data = request.json
    site_id = data.get('site_id', 'USER_OVERRIDE')
    value = float(data.get('value', 0.0))
    
    # Simulated AI estimate for manual entries
    dl_est = round(value * 0.98, 2) 
    rmse = round(abs(value - dl_est), 3)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tuning_logs VALUES (?, ?, ?, ?, ?)", 
                   (site_id, ts, value, dl_est, rmse))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": f"Manual log synced for {site_id}"})

if __name__ == '__main__':
    # Ensure port and host are configured for local operational access
    app.run(host='0.0.0.0', port=5000, debug=True)