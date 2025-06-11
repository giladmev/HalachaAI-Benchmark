import re
from typing import List, Dict
from constants import ALLOWED_ANSWERS
import os
def parse_questions(file_path: str) -> List[Dict[str, str]]:
    """
    Parses a text file with questions and answers in a specific format.

    Args:
        file_path (str): Path to the input text file.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, each containing a question, answer, source, and additional text.
    """
    questions = []
    print('the files in file_path directoery', os.listdir(os.path.dirname(file_path)))
    # Read the entire file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split the content into blocks separated by empty lines
    blocks = re.split(r'\n\s*\n', content)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Remove lines that start with "#" (comments)
        block = '\n'.join(line for line in block.split('\n') if not line.strip().startswith('#'))

        # Extract each field using regular expressions
        q_match = re.search(r'שאלה:\s*(.*)', block)
        a_match = re.search(r'תשובה:\s*(.*)', block)
        source_match = re.search(r'מקור:\s*(.*)', block)
        text_match = re.search(r'טקסט:\s*(.*)', block)

        if q_match and a_match and source_match and text_match:
            questions.append({
                'question': q_match.group(1).strip(),
                'answer': a_match.group(1).strip(),
                'source': source_match.group(1).strip(),
                'text': text_match.group(1).strip(),
            })
        else:
            print(f"Warning: Failed to parse block:\n{block}\n")

    return questions

def parse_model_response(response_text: str):
    """
    Parses Claude's response text into answer and source fields,
    validating the answer against allowed answers.

    Args:
        response_text (str): The raw text returned from Claude.

    Returns:
        Dict[str, str]: A dictionary with 'model_answer' and 'model_source'.
    """
    answer_match = re.search(r"תשובה:\s*(.+)", response_text)
    source_match = re.search(r"מקור:\s*(.+)", response_text)

    answer = answer_match.group(1).strip() if answer_match else None
    source = source_match.group(1).strip() if source_match else None

    if answer not in ALLOWED_ANSWERS:
        print(f"Warning: Model answer '{answer}' is not in allowed answers.")
        answer = None  # Not a valid answer

    return {
        "model_answer": answer,
        "model_source": source,
    }


def parse_source(source: str):
    """Parse source into (siman, saif), normalizing quotation marks."""
    if not source:
        return None, None
    phase = next((s for s in ["או״ח", "אה״ע", "יו״ד", "חו״מ"] if s in source), None)

    # Remove quotation marks (׳, ״) from source
    source = re.sub(r"[׳״']", "", source)

    # Find siman:saif structure
    match = re.search(r"([א-ת]+):([א-ת]+)", source)
    if match:
        siman = match.group(1)
        saif = match.group(2)
        return phase, siman, saif
    else:
        return phase, None, None