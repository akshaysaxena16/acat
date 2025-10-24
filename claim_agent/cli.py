from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import pandas as pd
from langchain_openai import ChatOpenAI

from .agent_graph import AgentState, create_graph
from .data_models import PatientRecord, PolicyDocument
from .tools import evaluate_record_against_policy


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_batch(records_path: Path, policy_path: Path, output_csv: Path):
    records_data = load_json(records_path)
    policy_data = load_json(policy_path)

    policy = PolicyDocument.model_validate(policy_data)

    rows = []
    for rd in records_data:
        record = PatientRecord.model_validate(rd)
        # Deterministic rule engine first to guarantee format; LLM optional later
        results = evaluate_record_against_policy(record, policy)
        # For simplicity, aggregate: if any DENY -> DENY; else if any REVIEW -> REVIEW; else APPROVE
        decisions = [r.decision for r in results]
        if "DENY" in decisions:
            final = next(r for r in results if r.decision == "DENY")
        elif "ROUTE FOR REVIEW" in decisions:
            final = next(r for r in results if r.decision == "ROUTE FOR REVIEW")
        else:
            final = results[0]
        rows.append({"patient_id": record.patient_id, "generated_response": final.to_text()})

    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    return df


def main():
    parser = argparse.ArgumentParser(description="Generate submission.csv for claims")
    parser.add_argument("--records", required=True, help="Path to test_records.json")
    parser.add_argument("--policy", required=True, help="Path to policy.json")
    parser.add_argument("--out", default="submission.csv", help="Output CSV path")
    args = parser.parse_args()

    run_batch(Path(args.records), Path(args.policy), Path(args.out))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
