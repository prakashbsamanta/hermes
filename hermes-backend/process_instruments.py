import csv
import os
from collections import defaultdict

def split_instruments():
    input_path = 'data/instruments/master_instruments.csv'
    output_dir = 'data/instruments'
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    # Use a dictionary to keep file handles open or buffer lines
    # Since the file might be large, let's read once and append to lists, then write.
    # Or cleaner: read line by line, categorize, write to specific files. 
    # To avoid opening too many files, we can group in memory (if fits) or re-open/append.
    # Given 185k lines, memory is fine (~15MB).

    print("Reading master instruments file...")
    data_by_segment = defaultdict(list)
    headers = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return

        # Find segment index
        try:
            segment_idx = headers.index('segment')
        except ValueError:
            print("Error: 'segment' column not found.")
            return

        for row in reader:
            if len(row) > segment_idx:
                segment = row[segment_idx]
                data_by_segment[segment].append(row)

    print(f"Found {len(data_by_segment)} segments.")

    for segment, rows in data_by_segment.items():
        # Sanitize segment name for filename
        filename = "".join([c if c.isalnum() or c in ('-','_') else '_' for c in segment])
        out_file = os.path.join(output_dir, f"{filename}.csv")
        
        print(f"Writing {len(rows)} rows to {out_file}...")
        with open(out_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    print("Done splitting instruments.")

if __name__ == "__main__":
    split_instruments()
