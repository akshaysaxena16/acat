from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def compare(generated_csv: Path, reference_csv: Path) -> float:
    gen = pd.read_csv(generated_csv)
    ref = pd.read_csv(reference_csv)
    merged = gen.merge(ref, on="patient_id", suffixes=("_gen", "_ref"))
    if merged.empty:
        print("No overlapping patient_id values.")
        return 0.0
    acc = (merged.generated_response_gen == merged.generated_response_ref).mean()
    print(f"Validation accuracy: {acc:.3f}")
    return float(acc)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gen", required=True)
    p.add_argument("--ref", required=True)
    args = p.parse_args()
    compare(Path(args.gen), Path(args.ref))


if __name__ == "__main__":
    main()
