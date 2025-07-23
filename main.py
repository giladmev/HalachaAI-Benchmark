import time
from typing import List, Dict
import anthropic
from utils.parsing_utils import parse_questions, parse_model_response, parse_source
from utils.files_utils import load_results_from_csv, save_results_to_json, save_results_to_csv
from utils.vis_utils import plot_model_comparison, plot_part_comparison
from pathlib import Path
import os
import yaml


API_KEY = os.getenv('ANTHROPIC_API_KEY')

def build_prompt(question: str, allowed_answers: list, thinking=False) -> str:
    """
    Builds the full prompt to send to Claude for a given question.
    """
    allowed_answers_text = "רק אחת מהתשובות הבאות מותרת: " + ", ".join(allowed_answers) + "."
    instructions = f"""אתה מומחה להלכה היהודית. עליך לענות על שאלה בהלכה על פי ההנחיות הבאות:
- תשובה קצרה ותמציתית. התשובה יכולה להיות {', '.join(allowed_answers)} בלבד.
- יש להשיב בעברית.
- יש לענות על פי שולחן ערוך בלבד, כולל הגהות הרמ"א.
- יש לציין בתשובה את המקורות עליהם הסתמכת בפורמט מסוים כפי שתראה בדוגמאות.
{"יש לבצע תהליך חשיבה לפני המענה" if thinking else ""}
- {allowed_answers_text}

דוגמא למענה:
תשובה: לא
מקור: שו"ע או"ח תרס"ב:ב

דוגמא למענה:
תשובה: כן
מקור: שו"ע יו"ד ע"ג:ב

כל שאלה עומדת בפני עצמה ללא תלות בשאלות קודמות או הבאות.
"""
    if thinking:
        instructions += "\nאת תהליך החשיבה יש לשים בתוך תג thinking.\n\n"
    return f"{instructions}\n\nשאלה: {question}"

def ask_claude(client, model_name, question, allowed_answers, thinking = False):
    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": build_prompt(question, allowed_answers, thinking)}
            ]
        )
        return response.content[0].text  # Assuming the response has content
    except Exception as e:
        print(f"Error sending question: {e}")
        return None

def compare_sources(true_source: str, model_source: str):
    """Compare true source and model source by siman and saif."""
    true_part, true_siman, true_saif = parse_source(true_source)
    model_part, model_siman, model_saif = parse_source(model_source)

    # If parsing failed
    if not true_siman or not model_siman:
        return False, False, False

    part_match = (true_part == model_part)
    siman_match = (true_siman == model_siman)
    saif_match = (true_saif == model_saif)

    return part_match, siman_match, saif_match

def enrich_result_row(row, allowed_answers):
    """
    Enrich a single result row with evaluation fields:
    - correct_answer: whether model answer matches true answer
    - correct_siman: whether model siman matches true siman
    - correct_saif: whether model saif matches true saif
    - correct_all: whether everything matches (answer + siman + saif)
    """
    # Normalize answers (remove spaces, unify form)
    if row.get("model_answer") is None or row.get("true_answer") is None:
        row["correct_answer"] = False
        row["correct_siman"] = False
        row["correct_saif"] = False
        row["correct_all"] = False
        return row
    true_answer = row.get("true_answer", "").strip()
    model_answer = row.get("model_answer", "").strip()

    row["correct_answer"] = (model_answer in allowed_answers) and (true_answer == model_answer)

    # Compare sources (siman and saif)
    true_source = row.get("true_source", "")
    model_source = row.get("model_source", "")

    part_match, siman_match, saif_match = compare_sources(true_source, model_source)
    row["correct_part"] = part_match
    row["correct_siman"] = siman_match
    row["correct_saif"] = saif_match

    # Overall correctness: everything must be correct
    row["correct_all"] = row["correct_answer"] and row["correct_siman"] and row["correct_saif"]

    return row

def calculate_statistics(results: List[Dict[str, str]], parts) -> Dict[str, float]:
    """
    Calculate statistics for each part separately and overall.
    Returns a dictionary with statistics for each part and a summary for all parts.
    """
    part_results = {part: [result for result in results if result.get("part") == part] for part in parts}
    part_results["all"] = results  # All results

    check_fields = [
        'correct_answer',
        'correct_siman',
        'correct_part',
        'correct_saif',
        'correct_all',
    ]

    # Calculate statistics for each part
    part_statistics = {}
    for part, part_data in part_results.items():
        if not part_data:
            part_statistics[part] = {"total_questions": 0}
            continue

        total = len(part_data)
        stats = {"total_questions": total}

        for field in check_fields:
            correct_count = sum(1 for r in part_data if r.get(field) is True)
            accuracy = (correct_count / total) * 100 if total > 0 else 0
            stats[f"{field}_count"] = correct_count
            stats[f"{field}_accuracy"] = round(accuracy, 2)
        part_statistics[part] = stats
    return part_statistics

def load_config(path="config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    config = load_config()

    skip_api_calls = config['skip_api_calls']
    thinking = config['thinking']

    input_dir = Path(config['input_dir'])
    output_base_dir = Path(config['output_base_dir'])

    questions_file = input_dir / config['questions_file']
    model_names = config['model_names']
    allowed_answers = config['allowed_answers']
    all_models_results = {}
    for model_name in model_names:
        output_dir = output_base_dir / model_name
        output_dir.mkdir(parents=True, exist_ok=True)

        output_csv = output_dir / f"results{'_thinking' if thinking else ''}.csv"
        output_json = output_dir / f"results{'_thinking' if thinking else ''}.json"
        results_summary_json = output_dir / f"results_summary{'_thinking' if thinking else ''}.json"
        if not skip_api_calls:
            client = anthropic.Anthropic(api_key=API_KEY)
            questions = parse_questions(questions_file)

            results = []
            for idx, q in enumerate(questions):
                print(f"Processing question {idx+1}/{len(questions)}...")

                # Try up to 3 times in case of failure
                for retry in range(3):
                    model_response_text = ask_claude(client, model_name, q["question"], allowed_answers,
                                                     thinking=thinking)
                    if model_response_text is not None:
                        break
                    print(f"Retry {retry + 1}/3 for question {idx + 1}...")
                    time.sleep(3)  # Wait between retries

                if model_response_text is None:
                    print(f"Failed to get response for question {idx + 1} after 3 attempts, skipping.")

                    continue
                model_response = parse_model_response(model_response_text)

                results.append({
                    "original_question": q['question'],
                    "true_answer": q['answer'],
                    "true_source": q['source'],
                    "part": next((p for p in config['parts'] if p in q['source']), None),
                    "model_full_response": model_response_text,
                    "model_answer": model_response.get('model_answer'),
                    "model_source": model_response.get('model_source'),
                })

                time.sleep(1)

            enriched_results = [enrich_result_row(row, allowed_answers) for row in results]

        else:
            print("Loading existing results from CSV...")

            results = load_results_from_csv(output_csv)  # Load existing results from the CSV file
            enriched_results = [enrich_result_row(row, allowed_answers) for row in results]

        save_results_to_csv(enriched_results, output_csv)
        save_results_to_json(enriched_results, output_json)

        statistics = calculate_statistics(enriched_results, config['parts'])
        save_results_to_json(statistics, results_summary_json)
        all_models_results[model_name] = statistics.get("all", {})
        plot_part_comparison(statistics, model_name, output_base_dir)

    plot_model_comparison(all_models_results, output_base_dir)

if __name__ == "__main__":
    main()
