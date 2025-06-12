import matplotlib.pyplot as plt
import os

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
        filename="accuracy_metrics.png",
        is_percentage=True
    )

    # Plot and save absolute-value metrics
    plot(
        metrics=absolute_metrics,
        title="Model Comparison - Absolute Metrics",
        ylabel="Absolute Values",
        filename="absolute_metrics.png",
        is_percentage=False
    )
