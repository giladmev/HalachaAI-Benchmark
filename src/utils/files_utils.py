import csv
import json


def load_results_from_csv(csv_file):
    """
    Load results from the CSV file.
    """
    results = []
    with open(csv_file, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def save_results_to_csv(results, output_file):
    """
    Save the results to a CSV file.
    """
    if not results:
        print("No results to save.")
        return

    fieldnames = list(results[0].keys())

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} results to {output_file}")

def save_results_to_json(results, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
