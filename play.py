import csv
import json
from main import enrich_result_row  # Import the function from main.py


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


def save_results_to_csv(results, output_csv):
    """
    Save the results to a CSV file.
    """
    if not results:
        print("No results to save.")
        return

    fieldnames = list(results[0].keys())

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} results to {output_csv}")


def save_results_to_json(results, output_json):
    """
    Save the results to a JSON file.
    """
    if not results:
        print("No results to save.")
        return

    with open(output_json, mode="w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Saved {len(results)} results to {output_json}")


def main():
    """
    Load the results from CSV, enrich the results, and save back to CSV and JSON.
    """
    output_csv = "results.csv"
    output_json = "results.json"
    from constants import ALLOWED_ANSWERS
    # Load existing results from the CSV
    results = load_results_from_csv(output_csv)

    # Enrich results with evaluation fields
    enriched_results = [enrich_result_row(row, ALLOWED_ANSWERS) for row in results]

    # Save the enriched results to CSV and JSON
    save_results_to_csv(enriched_results, output_csv)
    save_results_to_json(enriched_results, output_json)

if __name__ == "__main__":
    main()
