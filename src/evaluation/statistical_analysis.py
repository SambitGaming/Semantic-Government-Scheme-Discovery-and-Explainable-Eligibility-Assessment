
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

FILE = Path("results/per_query_comparison.csv")
df = pd.read_csv(FILE)

rng = np.random.default_rng(42)

pairs = [
    ("BM25", "MINILM"),
    ("BM25", "MPNET"),
    ("MINILM", "MPNET"),
]

for metric in ["nDCG@10", "MRR", "Precision@10"]:
    print(f"\n--- {metric} ---")

    for a, b in pairs:
        x = df[f"{a}_{metric}"].to_numpy(dtype=float)
        y = df[f"{b}_{metric}"].to_numpy(dtype=float)

        valid = np.isfinite(x) & np.isfinite(y)
        x, y = x[valid], y[valid]

        if len(x) == 0:
            print(a, "vs", b, "- no valid paired scores")
            continue

        diff = y - x

        # Paired Wilcoxon signed-rank test
        if np.allclose(diff, 0):
            statistic, p_value = 0.0, 1.0
        else:
            statistic, p_value = wilcoxon(x, y)

        # Bootstrap 95% CI for the mean paired difference
        boot = np.array([
            rng.choice(diff, size=len(diff), replace=True).mean()
            for _ in range(5000)
        ])
        low, high = np.quantile(boot, [0.025, 0.975])

        print(f"{a} vs {b}")
        print("Paired queries:", len(diff))
        print("Mean difference (second - first):", diff.mean())
        print("Wilcoxon statistic:", statistic)
        print("p-value:", p_value)
        print("95% bootstrap CI for difference:", (low, high))