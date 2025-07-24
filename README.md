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
```
data/ 
  input/ 
    questions.txt # List of questions for evaluation 
  output/ 
    model-name/ # Separate directory for each model 
      results.csv # Detailed per-question results 
      results.json # JSON format of results 
      results_summary.json # Performance summary 
      comparison_plots # Visual comparisons between parts per each model
src/ 
    main.py # Main script for running the evaluation
    generate_questions.py # Script to generate questions from input sources
    utils/ # Utility functions for processing and evaluation
config.yaml # Configuration file for model parameters and API settings
```

## Key Results
We've evaluated models across all four parts of Shulchan Aruch (או"ח, יו"ד, אה"ע, חו"מ), with a total of 94 questions (approximately 20-30 questions per part):

**The average accuracy across both tested models in answering halachic questions correctly is approximately 68.62%.**

### Model Performance Comparison

**Claude 3.7 Sonnet (February 2025)**:
- Overall accuracy: 70% correct answers
- Source citation accuracy: 72% correct Siman, 69% correct Saif

**Claude Sonnet 4 (May 2025)**:
- Overall accuracy: 67% correct answers
- Source citation accuracy: 61% correct Siman, 56% correct Saif

### Part-Specific Performance
Performance varies across different parts of Shulchan Aruch:

- **או"ח (Orach Chaim)**: Highest source citation accuracy (75.76%)
- **יו"ד (Yoreh Deah)**: Lowest answer accuracy (52-57%)
- In all parts, both models correctly identified the appropriate section of Shulchan Aruch with very high accuracy (91-95% overall)

### Detailed Findings
- Claude 3.7 Sonnet outperforms Claude Sonnet 4 in most metrics, especially in source citation
- Saif (paragraph) identification is more challenging than Siman (chapter) identification
- The models struggle more with Yoreh Deah questions compared to other sections
- Full correctness (correct answer + acuurate source Saif and Siman) is achieved in less than half of all cases

## Usage
- By default, the project runs full evaluation (including API calls).
- You can switch to analysis-only mode (without new API calls) if you already have `results.csv`.
- Results are automatically enriched with multiple accuracy checks.
- Visual comparisons between models and parts are generated.

## Notes
- Designed for flexible integration with any model that supports API calls (Anthropic Claude, OpenAI, custom models, etc.).
- Based on strict Halachic sources: only Shulchan Aruch and Rema's annotations are accepted.
- The AI model is instructed to answer shortly and to cite sources exactly.