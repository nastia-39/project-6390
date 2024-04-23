from radon.complexity import cc_rank, cc_visit
from radon.raw import analyze
from radon.metrics import mi_visit

def calculate_metrics(code):
    #cyclomatic complexity
    complexity = cc_visit(code)
    average_complexity = sum([func.complexity for func in complexity]) / len(complexity) if complexity else 0

    #lines of code
    raw_metrics = analyze(code)
    loc = raw_metrics.lloc

    #maintainability index
    maintainability_index = mi_visit(code, True)

    return {
        'Average Complexity': average_complexity,
        'Lines of Code': loc,
        'Maintainability Index': maintainability_index,
    }