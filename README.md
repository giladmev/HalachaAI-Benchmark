# Halacha AI Benchmark

This project evaluates the performance of an AI model (such as Claude or others) via API calls, specifically on Jewish law (Halacha) questions based on the Shulchan Aruch.

## Project Purpose
- To benchmark the accuracy of an AI model in answering Halachic questions.
- To check the correctness at multiple levels:
  - Whether the AI answered "Yes" or "No" correctly.
  - Whether the AI cited the correct Siman (chapter) and Saif (paragraph) from Shulchan Aruch.
  - Full correctness (answer + source match).

## How it works

### Input file (`questions.txt`)
Contains a list of Halachic questions, expected answers, and sources.

### API calls
The project sends each question to the AI model through its API.

### Evaluation
Compares the AI's response to the ground truth:
- Answer correctness.
- Siman and Saif correctness.

### Output files:
- `results.csv` — Detailed results for each question.
- `results.json` — Structured results.
- `results_summary.json` — Overall performance statistics.

## Project Structure
data/
  input/
    questions.txt       # List of questions for evaluation
  output/
    results.csv          # Detailed per-question results
    results.json         # JSON format of results
    results_summary.json # Performance summary

main.py                  # Main script: run the full evaluation
postprocess.py           # Tools for enriching and analyzing existing results
README.md                # Project description

## Usage
- By default, the project runs full evaluation (including API calls).
- You can switch to analysis-only mode (without new API calls) if you already have `results.csv`.
- Results are automatically enriched with multiple accuracy checks.

## Notes
- Designed for flexible integration with any model that supports API calls (Anthropic Claude, OpenAI, custom models, etc.).
- Based on strict Halachic sources: only Shulchan Aruch and Rema's annotations are accepted.
- The AI model is instructed to answer shortly and to cite sources exactly.