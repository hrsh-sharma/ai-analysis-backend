from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from analyzers.seo import analyze_seo
from analyzers.accessibility import analyze_accessibility
from analyzers.performance import analyze_performance
from analyzers.security import analyze_security
from analyzers.ux import analyze_ux

# Hard timeout per analyzer (seconds)
ANALYZER_TIMEOUT = 50


def run_all_analyzers(url: str) -> dict:
    analyzers = {
        "seo":           analyze_seo,
        "accessibility": analyze_accessibility,
        "performance":   analyze_performance,
        "security":      analyze_security,
        "ux":            analyze_ux,
    }

    results = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fn, url): name for name, fn in analyzers.items()}
        for future in as_completed(futures, timeout=ANALYZER_TIMEOUT * 2):
            name = futures[future]
            try:
                results[name] = future.result(timeout=ANALYZER_TIMEOUT)
            except TimeoutError:
                results[name] = {"error": f"timed out after {ANALYZER_TIMEOUT}s"}
            except Exception as e:
                results[name] = {"error": str(e)}

    # Ensure every category is present even if a future never completed
    for name in analyzers:
        if name not in results:
            results[name] = {"error": "did not complete in time"}

    return results
