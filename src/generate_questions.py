from pathlib import Path
import os
import yaml
import anthropic
import time
import re
from typing import List, Dict

API_KEY = os.getenv('ANTHROPIC_API_KEY')

def build_prompt(source_text: str) -> str:
    """
    Builds the prompt to generate a question based on a source text.
    """
    instructions = """אתה מומחה להלכה היהודית. אני אתן לך מקור מהשולחן ערוך עם טקסט הלכתי, ותפקידך לייצר שאלה הלכתית מציאותית שהתשובה עליה מתבססת ישירות על המקור שנתתי. 

הנחיות:
1. השאלה צריכה להיות על מקרה יומיומי שיכול לקרות לאדם רגיל בחיי היומיום
2. יש להתבסס אך ורק על הטקסט מהמקור שנתתי 
3. התשובה לשאלה צריכה להיות אחת מהבאות: "כן", "לא", או "מחלוקת שו"ע-רמ"א" במקרה שיש מחלוקת בהלכה
4. אורך השאלה לא יעלה על 3-4 שורות
5. יש לכתוב את השאלה בגוף ראשון, כאילו האדם השואל מספר על מקרה שקרה לו

פורמט המענה:
שאלה: [כאן תבוא השאלה]
תשובה: [כן/לא/מחלוקת שו"ע-רמ"א]
מקור: [המקור שנתתי לך]
טקסט: [הטקסט שנתתי לך]

דוגמה למענה:
שאלה: הבוקר התלבשתי במהירות ולא שמתי לב שהפכתי את החולצה שלי כך שהתפרים נראים מבחוץ. חבר אמר לי שזה לא ראוי על פי ההלכה. האם הוא צודק?
תשובה: כן
מקור: שו"ע או"ח ב':ג'
טקסט: יְדַקְדֵּק בַּחֲלוּקוֹ לְלָבְשׁוֹ כְּדַרְכּוֹ שֶׁלֹּא יַהֲפֹךְ הַפְּנִימִי לַחוּץ."""
    return f"{instructions}\n\nקלט: {source_text}"

def parse_sources_from_file(file_path: str) -> List[Dict[str, str]]:
    """
    Parses sources from a text file where each source is separated by empty lines.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, each containing source and text.
    """
    sources = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split the content into blocks separated by empty lines
    blocks = re.split(r'\n\s*\n', content)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        source_match = re.search(r'מקור:\s*(.*)', block)
        text_match = re.search(r'טקסט:\s*(.*)', block)

        if source_match and text_match:
            sources.append({
                'source': source_match.group(1).strip(),
                'text': text_match.group(1).strip(),
            })

    return sources

def ask_claude(client, model_name, source_item):
    """
    Send a source to Claude and get a question based on it.
    """
    try:
        source_text = f"מקור: {source_item['source']}\nטקסט: {source_item['text']}"
        prompt = build_prompt(source_text)

        response = client.messages.create(
            model=model_name,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text  # Assuming the response has content
    except Exception as e:
        print(f"Error sending question: {e}")
        return None

def parse_model_response(response_text: str):
    """
    Parses Claude's response to extract the question, answer, source and text.
    """
    question_match = re.search(r"שאלה:\s*(.+?)(?=\n\s*תשובה:)", response_text, re.DOTALL)
    answer_match = re.search(r"תשובה:\s*(.+?)(?=\n\s*מקור:)", response_text)
    source_match = re.search(r"מקור:\s*(.+?)(?=\n\s*טקסט:)", response_text)
    text_match = re.search(r"טקסט:\s*(.+)", response_text, re.DOTALL)

    if question_match and answer_match and source_match and text_match:
        return {
            "question": question_match.group(1).strip(),
            "answer": answer_match.group(1).strip(),
            "source": source_match.group(1).strip(),
            "text": text_match.group(1).strip()
        }
    else:
        print("Warning: Failed to parse model response")
        return None

def save_questions_to_file(questions, output_file):
    """
    Save generated questions to a file in the required format.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, q in enumerate(questions):
            if i > 0:
                f.write("\n\n")
            f.write(f"שאלה: {q['question']}\n")
            f.write(f"תשובה: {q['answer']}\n")
            f.write(f"מקור: {q['source']}\n")
            f.write(f"טקסט: {q['text']}")

def load_config(path="config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    config = load_config()

    input_dir = Path(config['input_dir'])
    output_dir = Path(config['output_base_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Input and output files
    sources_file = input_dir / "all_parts_src.txt"
    output_file = output_dir / "all_parts_questions.txt"

    # Parse sources
    sources = parse_sources_from_file(sources_file)
    print(f"Found {len(sources)} sources in the input file.")

    # Setup Claude client
    client = anthropic.Anthropic(api_key=API_KEY)
    model_name = config['model_names'][0]  # Use the first model in the config

    generated_questions = []

    # Generate a question for each source
    for idx, source_item in enumerate(sources):
        print(f"Processing source {idx+1}/{len(sources)}: {source_item['source']}")

        response_text = ask_claude(client, model_name, source_item)
        if response_text is None:
            print(f"Skipping source {idx+1} due to error.")
            continue

        parsed_response = parse_model_response(response_text)
        if parsed_response:
            generated_questions.append(parsed_response)
            print(f"Generated question: {parsed_response['question'][:50]}...")

        # Sleep to avoid rate limiting
        time.sleep(1)

    # Save all questions to the output file
    save_questions_to_file(generated_questions, output_file)
    print(f"Generated {len(generated_questions)} questions and saved to {output_file}")

if __name__ == "__main__":
    main()