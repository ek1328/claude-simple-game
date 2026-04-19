### 💻 Example 1: Working with CSV Files + Threading (`csv` and `threading` modules)

import csv
from concurrent.futures import ThreadPoolExecutor

# Function to read a CSV file and process its data with conditional checks
def process_csv():
    try:
        # Read from a sample CSV file — using 'with' context manager for safe handling
        with open('data.csv', mode='r') as file:
            csv_reader = csv.reader(file)
            data_list = []
            for row in csv_reader:
                try:
                    # Convert to float if possible — showing handling of mixed data
                    num = float(row[0])
                    data_list.append(num)
                except (ValueError, IndexError):
                    print("⚠️ Skipping invalid row:", row)

        # Filter data (showing list comprehensions — functional in flavor)
        filtered = [x for x in data_list if 0 < x <= 100]
        print("📊 Processed successfully:", len(filtered), "rows")
        return filtered

    except Exception as e:
        print("🚨 Error reading CSV:", str(e))
        