import sqlite3
import csv
import io

class ReportGenerator:
    @staticmethod
    def generate_csv_report():
        """Generates a CSV of international performance (Section 7.4.3)."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers based on International Performance Results table
        writer.writerow(['Network', 'Country', 'Local Z-R RMSE', 'DeepRain RMSE', 'Improvement'])
        
        # Static data from Section 7.4.3 documentation
        data = [
            ['MeteoFrance', 'France', '1.9', '1.6', '+16%'],
            ['JMA', 'Japan', '1.7', '1.4', '+18%'],
            ['DWD', 'Germany', '1.5', '1.3', '+13%'],
            ['INMET', 'Brazil', '2.2', '1.8', '+18%']
        ]
        writer.writerows(data)
        return output.getvalue()