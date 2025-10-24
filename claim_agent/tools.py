from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel

from .data_models import (
    CheckResult,
    PatientRecord,
    PolicyDocument,
    PolicySummary,
    ProcedureRule,
    RecordSummary,
    compute_age,
)


class ToolError(Exception):
    pass


def build_record_summaries(record: PatientRecord) -> List[RecordSummary]:
    age = compute_age(record.date_of_birth, record.date_of_service)
    summaries: List[RecordSummary] = []
    for code in record.procedure_codes:
        summaries.append(
            RecordSummary(
                patient_id=record.patient_id,
                age=age,
                gender=(record.gender or "Any"),
                diagnosis_codes=record.diagnosis_codes,
                procedure_code=code,
                claim_amount=record.claim_amount,
                preauthorization_required=record.preauthorization_required,
                preauthorization_obtained=record.preauthorization_obtained,
            )
        )
    return summaries


def find_policy_summaries(policy: PolicyDocument, procedure_code: str) -> List[PolicySummary]:
    results: List[PolicySummary] = []
    for rule in policy.covered_procedures:
        if rule.procedure_code == procedure_code:
            results.append(
                PolicySummary(policy_id=policy.policy_id, plan_name=policy.plan_name, rule=rule)
            )
    return results


def check_claim_coverage(record_summary: RecordSummary, policy_summary: PolicySummary) -> CheckResult:
    r = record_summary
    rule = policy_summary.rule

    # 1) Procedure must match is implied by selection; continue checks

    # 2) Diagnosis code coverage
    if rule.covered_diagnoses:
        if not any(code in rule.covered_diagnoses for code in r.diagnosis_codes):
            return CheckResult(
                decision="DENY",
                reason=(
                    f"Diagnosis codes {r.diagnosis_codes} are not covered for procedure "
                    f"{r.procedure_code} under policy {policy_summary.policy_id}."
                ),
            )

    # 3) Age range
    if rule.age_range is not None:
        min_age, max_age = rule.age_range
        if not (min_age <= r.age <= max_age):
            return CheckResult(
                decision="ROUTE FOR REVIEW",
                reason=(
                    f"Patient age {r.age} is outside allowed range {min_age}-{max_age} "
                    f"for procedure {r.procedure_code}."
                ),
            )

    # 4) Gender
    if rule.gender and rule.gender not in ("Any", "any", None):
        if (r.gender or "Any").lower() != rule.gender.lower():
            return CheckResult(
                decision="ROUTE FOR REVIEW",
                reason=(
                    f"Patient gender {r.gender} does not meet requirement {rule.gender} "
                    f"for procedure {r.procedure_code}."
                ),
            )

    # 5) Preauthorization
    if rule.requires_preauthorization:
        if not r.preauthorization_obtained:
            return CheckResult(
                decision="ROUTE FOR REVIEW",
                reason=(
                    "Preauthorization is required by policy but was not obtained for this claim."
                ),
            )

    # 6) Coverage limit vs claim amount
    if rule.coverage_limit is not None and r.claim_amount is not None:
        if r.claim_amount > rule.coverage_limit:
            return CheckResult(
                decision="ROUTE FOR REVIEW",
                reason=(
                    f"Claim amount ${r.claim_amount:,.2f} exceeds coverage limit "
                    f"${rule.coverage_limit:,.2f}."
                ),
            )

    # If all checks pass
    return CheckResult(
        decision="APPROVE",
        reason=(
            f"Procedure {r.procedure_code} is covered for diagnoses {r.diagnosis_codes}; "
            f"age {r.age} and gender {r.gender} meet requirements; "
            f"preauthorization {'obtained' if r.preauthorization_obtained else 'not required'}; "
            f"claim amount within allowable limit."
        ),
    )


# Convenience runner used by the agent

def evaluate_record_against_policy(record: PatientRecord, policy: PolicyDocument) -> List[CheckResult]:
    results: List[CheckResult] = []
    summaries = build_record_summaries(record)
    for rs in summaries:
        matching_rules = find_policy_summaries(policy, rs.procedure_code)
        if not matching_rules:
            results.append(
                CheckResult(
                    decision="DENY",
                    reason=(
                        f"Procedure {rs.procedure_code} is not covered under policy {policy.policy_id}."
                    ),
                )
            )
            continue
        # If multiple rules, approve if any rule fully passes; otherwise take the first non-approve as reason
        approved = False
        first_non_approve: Optional[CheckResult] = None
        for ps in matching_rules:
            res = check_claim_coverage(rs, ps)
            if res.decision == "APPROVE":
                results.append(res)
                approved = True
                break
            if first_non_approve is None:
                first_non_approve = res
        if not approved:
            results.append(first_non_approve or CheckResult(decision="ROUTE FOR REVIEW", reason="No matching rule fully satisfied."))
    return results
