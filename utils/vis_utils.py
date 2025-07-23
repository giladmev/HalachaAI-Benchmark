import matplotlib.pyplot as plt
import matplotlib
import os
from typing import Dict, Any

PART_FULL_NAMES = {
    'או"ח': 'אורח חיים',
    'יו"ד': 'יורה דעה',
    'אה"ע': 'אבן העזר',
    'חו"מ': 'חושן משפט',
    'all': 'סך הכל'
}

def plot_model_comparison(results: dict, output_dir: str):
    """
    Splits metrics into percentage-based (ending with 'accuracy') and absolute metrics.
    Creates and saves a separate bar chart for each type.
    """
    if not isinstance(results, dict):
        raise ValueError("Expected `results` to be a dict of model_name -> metrics dict")

    # Separate metric names
    sample_model = next(iter(results.values()))
    accuracy_metrics = [metric for metric in sample_model if metric.endswith("accuracy")]
    absolute_metrics = [metric for metric in sample_model if not metric.endswith("accuracy")]

    def plot(metrics, title, ylabel, filename, is_percentage=False):
        if not metrics:
            return  # Skip if no metrics of this type

        models = list(results.keys())
        x = range(len(metrics))
        width = 0.8 / len(models)

        fig, ax = plt.subplots(figsize=(10, 6))

        for i, model in enumerate(models):
            bar_positions = [xi - (width * (len(models) - 1) / 2) + i * width for xi in x]
            values = [results[model][metric] for metric in metrics]
            bars = ax.bar(bar_positions, values, width, label=model)

            # Add value labels above bars
            for bar in bars:
                height = bar.get_height()
                label = f'{int(round(height))}%' if is_percentage else f'{int(round(height))}'
                ax.annotate(label,
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9)

        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(list(x))
        ax.set_xticklabels(metrics, rotation=45)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300)
        plt.close()

    # Plot and save percentage-based metrics
    plot(
        metrics=accuracy_metrics,
        title="Model Comparison - Accuracy Metrics",
        ylabel="Accuracy (%)",
        filename="models_accuracy_metrics.png",
        is_percentage=True
    )

    # Plot and save absolute-value metrics
    plot(
        metrics=absolute_metrics,
        title="Model Comparison - Absolute Metrics",
        ylabel="Absolute Values",
        filename="models_absolute_metrics.png",
        is_percentage=False
    )


def plot_part_comparison(part_statistics: Dict[str, Dict[str, Any]], model_name: str, output_dir: str):
    """
    Creates bar charts comparing metrics across different parts for a single model.

    Args:
        part_statistics: Dictionary with part names as keys and metric dictionaries as values
        model_name: Name of the model being analyzed
        output_dir: Directory to save the output charts
    """
    if not isinstance(part_statistics, dict):
        raise ValueError("Expected `part_statistics` to be a dict of part_name -> metrics dict")

    # Skip if no data
    if not part_statistics:
        return

    # Separate metric names from the first part data
    sample_part = next(iter(part_statistics.values()))
    accuracy_metrics = [metric for metric in sample_part if metric.endswith("accuracy")]
    absolute_metrics = [metric for metric in sample_part
                        if not metric.endswith("accuracy") and metric != "total_questions"]
    # Add total_questions separately to ensure it's included
    if "total_questions" in sample_part:
        absolute_metrics = ["total_questions"] + absolute_metrics

    def plot(metrics, title, ylabel, filename, is_percentage=False):
        matplotlib.rcParams['font.family'] = 'Arial'

        if not metrics:
            return  # Skip if no metrics of this type

        parts = [part for part in part_statistics.keys() if part != "all"]
        # Ensure "all" is the last one if it exists
        if "all" in part_statistics:
            parts.append("all")

        x = range(len(metrics))
        width = 0.8 / len(parts)

        fig, ax = plt.subplots(figsize=(12, 7))

        for i, part in enumerate(parts):
            if part not in part_statistics:
                continue

            bar_positions = [xi - (width * (len(parts) - 1) / 2) + i * width for xi in x]
            values = [part_statistics[part].get(metric, 0) for metric in metrics]

            def fix_rtl(text):
                return text[::-1]

            bars = ax.bar(bar_positions, values, width, label=fix_rtl( PART_FULL_NAMES[part]))
            # Add value labels above bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:  # Only label bars with values
                    label = f'{int(round(height))}%' if is_percentage else f'{int(round(height))}'
                    ax.annotate(label,
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9)

        ax.set_ylabel(ylabel)
        ax.set_title(f"{title} - {model_name}")
        ax.set_xticks(list(x))
        ax.set_xticklabels([m.replace("_accuracy", "").replace("_count", "")
                            for m in metrics], rotation=45)
        ax.legend(title="Parts")
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()

        # Create model-specific directory
        model_dir = os.path.join(output_dir, model_name)
        os.makedirs(model_dir, exist_ok=True)

        filepath = os.path.join(model_dir, filename)
        plt.savefig(filepath, dpi=300)
        plt.close()

    # Plot and save percentage-based metrics
    plot(
        metrics=accuracy_metrics,
        title="Part Comparison - Accuracy Metrics",
        ylabel="Accuracy (%)",
        filename="part_accuracy_metrics.png",
        is_percentage=True
    )

    # Plot and save absolute-value metrics
    plot(
        metrics=absolute_metrics,
        title="Part Comparison - Absolute Metrics",
        ylabel="Absolute Values",
        filename="part_absolute_metrics.png",
        is_percentage=False
    )