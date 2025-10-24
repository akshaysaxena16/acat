from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator


class PatientRecord(BaseModel):
    patient_id: str
    name: Optional[str] = None
    date_of_birth: str
    gender: Optional[str] = Field(None, description="Male, Female, or Other/Any")
    insurance_policy_id: Optional[str] = None
    diagnosis_codes: List[str] = Field(default_factory=list)
    procedure_codes: List[str] = Field(default_factory=list)
    date_of_service: str
    provider_id: Optional[str] = None
    provider_specialty: Optional[str] = None
    location: Optional[str] = None
    claim_amount: Optional[float] = None
    preauthorization_required: Optional[bool] = None
    preauthorization_obtained: Optional[bool] = None

    # Derived
    age: Optional[int] = None

    @validator("date_of_birth", "date_of_service")
    def _validate_date(cls, v: str) -> str:
        # Accept YYYY-MM-DD
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Expected date in YYYY-MM-DD format, got: {v}") from exc
        return v


class ProcedureRule(BaseModel):
    procedure_code: str
    covered_diagnoses: List[str] = Field(default_factory=list)
    age_range: Optional[Tuple[int, int]] = None
    gender: Optional[str] = None  # 'Any', 'Male', 'Female'
    requires_preauthorization: Optional[bool] = None
    coverage_limit: Optional[float] = None
    notes: Optional[str] = None


class PolicyDocument(BaseModel):
    policy_id: str
    plan_name: Optional[str] = None
    covered_procedures: List[ProcedureRule] = Field(default_factory=list)


class RecordSummary(BaseModel):
    patient_id: str
    age: int
    gender: str
    diagnosis_codes: List[str]
    procedure_code: str
    claim_amount: Optional[float]
    preauthorization_required: Optional[bool] = None
    preauthorization_obtained: Optional[bool] = None


class PolicySummary(BaseModel):
    policy_id: str
    plan_name: Optional[str] = None
    rule: ProcedureRule


class CheckResult(BaseModel):
    decision: str  # APPROVE | DENY | ROUTE FOR REVIEW
    reason: str

    def to_text(self) -> str:
        # Required output format
        return f"Decision: {self.decision}\nReason: {self.reason}"


# Utility

def compute_age(dob: str, on_date: str) -> int:
    dob_dt = datetime.strptime(dob, "%Y-%m-%d").date()
    svc_dt = datetime.strptime(on_date, "%Y-%m-%d").date()
    years = svc_dt.year - dob_dt.year - ((svc_dt.month, svc_dt.day) < (dob_dt.month, dob_dt.day))
    return max(years, 0)
