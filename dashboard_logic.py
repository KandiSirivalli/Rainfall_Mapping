import sqlite3

class DashboardMetrics:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path

    def get_live_kpis(self):
        """Fetches real metrics recorded during operations."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Pull the latest tuning results (Section 7.6)
        cursor.execute("SELECT * FROM tuning_logs ORDER BY date DESC LIMIT 10")
        logs = cursor.fetchall()
        conn.close()
        
        if not logs:
            return {"status": "No operational data yet"}

        # Calculate real-time average RMSE from the last 10 events
        avg_rmse = sum([log['rmse'] for log in logs]) / len(logs)
        
        return {
            "current_avg_rmse": round(avg_rmse, 2),
            "total_events_logged": len(logs),
            "system_state": "Active - Fine Tuned"
        }