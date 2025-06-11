import time
from typing import List, Dict
import anthropic
from utils.parsing_utils import parse_questions, parse_model_response, parse_source
from utils.files_utils import load_results_from_csv, save_results_to_json, save_results_to_csv
from pathlib import Path
import os
import yaml


API_KEY = os.getenv('ANTHROPIC_API_KEY')

# os.environ["http_proxy"] =""
# os.environ["https_proxy"] =""
# os.environ["no_proxy"] =".openai.azure.com, 10.*, .intel.com, 127.*,localhost"

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
    true_phase, true_siman, true_saif = parse_source(true_source)
    model_phase, model_siman, model_saif = parse_source(model_source)

    # If parsing failed
    if not true_siman or not model_siman:
        return False, False, False

    phase_match = (true_phase == model_phase)
    siman_match = (true_siman == model_siman)
    saif_match = (true_saif == model_saif)

    return phase_match, siman_match, saif_match

def enrich_result_row(row, allowed_answers):
    """
    Enrich a single result row with evaluation fields:
    - correct_answer: whether model answer matches true answer
    - correct_siman: whether model siman matches true siman
    - correct_saif: whether model saif matches true saif
    - correct_all: whether everything matches (answer + siman + saif)
    """
    # Normalize answers (remove spaces, unify form)
    true_answer = row.get("true_answer", "").strip()
    model_answer = row.get("model_answer", "").strip()

    row["correct_answer"] = (model_answer in allowed_answers) and (true_answer == model_answer)

    # Compare sources (siman and saif)
    true_source = row.get("true_source", "")
    model_source = row.get("model_source", "")

    phase_match, siman_match, saif_match = compare_sources(true_source, model_source)
    row["correct_phase"] = phase_match
    row["correct_siman"] = siman_match
    row["correct_saif"] = saif_match

    # Overall correctness: everything must be correct
    row["correct_all"] = row["correct_answer"] and row["correct_siman"] and row["correct_saif"]

    return row

def calculate_statistics(results: List[Dict[str, str]]) -> Dict[str, float]:
    total = len(results)
    if total == 0:
        print("No results to evaluate.")
        return {}

    stats = {"total_questions": total}

    check_fields = [
        'correct_answer',
        'correct_siman',
        'correct_phase',
        'correct_saif',
        'correct_all',
    ]

    for field in check_fields:
        correct_count = sum(1 for r in results if r.get(field) is True)
        accuracy = (correct_count / total) * 100
        stats[f"{field}_count"] = correct_count
        stats[f"{field}_accuracy"] = round(accuracy, 2)

    print(f"Total Questions: {stats['total_questions']}")
    for field in check_fields:
        print(f"{field} - Correct: {stats[f'{field}_count']}/{stats['total_questions']} ({stats[f'{field}_accuracy']:.2f}%)")

    return stats

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

                model_response_text = ask_claude(client, model_name, q["question"], allowed_answers, thinking=thinking)
                if model_response_text is None:
                    continue
                model_response = parse_model_response(model_response_text)

                results.append({
                    "original_question": q['question'],
                    "true_answer": q['answer'],
                    "true_source": q['source'],
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

        statistics = calculate_statistics(enriched_results)
        save_results_to_json(statistics, results_summary_json)


if __name__ == "__main__":
    main()
