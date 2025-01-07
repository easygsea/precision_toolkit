from tabulate import tabulate
from docx import Document
from clinical_tools.analysis.compute_variant_metrics import process_variant_metrics


def save_concordance_markdown(results, output_file):
    """Save variant concordance results in Markdown format."""
    headers = [
        "Variant Type",
        "Variant Filter",
        "True Positive",
        "False Negative",
        "False Positive",
        "Concordance",
        "CI Lower",
        "CI Upper",
    ]
    data = [
        [
            variant_type,
            variant_filter,
            true_positive,
            false_negative,
            false_positive,
            f"{concordance:.4f}",
            f"{ci_lower:.4f}",
            f"{ci_upper:.4f}",
        ]
        for (variant_type, variant_filter), (
            true_positive,
            false_negative,
            false_positive,
            concordance,
            ci_lower,
            ci_upper,
        ) in results.items()
    ]

    markdown_table = tabulate(data, headers, tablefmt="github")

    summary = (
        "The table below summarizes the concordance metrics calculated for each "
        "variant type and filter."
    )

    with open(output_file, "w") as f:
        f.write("# Variant Concordance\n\n")
        f.write(f"{summary}\n\n")
        f.write(markdown_table)
    print(f"Variant concordance results saved to {output_file}")


def save_concordance_word(results, output_file):
    """Save variant concordance results in Word format."""
    doc = Document()
    doc.add_heading("Variant Concordance", level=1)

    summary = (
        "The table below summarizes the concordance metrics calculated for each "
        "variant type and filter."
    )
    doc.add_paragraph(summary)

    headers = [
        "Variant Type",
        "Variant Filter",
        "True Positive",
        "False Negative",
        "False Positive",
        "Concordance",
        "CI Lower",
        "CI Upper",
    ]
    table = doc.add_table(rows=len(results) + 1, cols=len(headers))

    for j, header in enumerate(headers):
        table.cell(0, j).text = header

    for i, ((variant_type, variant_filter), metrics) in enumerate(results.items(), 1):
        true_positive, false_negative, false_positive = metrics[:3]
        concordance, ci_lower, ci_upper = metrics[3:]
        row_cells = table.rows[i].cells
        table.cell(i, 0).text = variant_type
        table.cell(i, 1).text = variant_filter
        table.cell(i, 2).text = str(true_positive)
        table.cell(i, 3).text = str(false_negative)
        table.cell(i, 4).text = str(false_positive)
        table.cell(i, 5).text = f"{concordance:.4f}"
        table.cell(i, 6).text = f"{ci_lower:.4f}"
        table.cell(i, 7).text = f"{ci_upper:.4f}"

    doc.save(output_file)
    print(f"Variant concordance results saved to {output_file}")
