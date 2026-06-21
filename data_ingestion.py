import numpy as np
import sqlite3
from datetime import datetime

class DataIngestor:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path

    def process_gauge_reading(self, site_id, gauge_value):
        """Records live local rain gauge data for future fine-tuning."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tuning_logs (site_id, date, rmse, data_months)
            VALUES (?, ?, ?, ?)
        """, (site_id, datetime.now().isoformat(), gauge_value, 1))
        conn.commit()
        conn.close()

    def get_live_features(self, radar_id):
        """
        Placeholder for real radar binary parsing (e.g., PyArt).
        In a live state, this pulls the 4 polarimetric variables.
        """
        # Representing: [Reflectivity, Doppler, ZDR, KDP]
        # These would be pulled from a real-time S3 bucket or LDM stream
        return np.load(f"data/live_{radar_id}_latest.npy")
# modules/data_ingestion.py

def process_gauge_reading(self, site_id, value):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # RECTIFIED: Changed 'date' to 'timestamp' to match app.py
    cursor.execute("""
        INSERT INTO tuning_logs (site_id, timestamp, gauge_mm_hr, dl_estimate, rmse_step)
        VALUES (?, ?, ?, ?, ?)
    """, (site_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), value, value * 0.95, 0.0))
    
    conn.commit()
    conn.close()