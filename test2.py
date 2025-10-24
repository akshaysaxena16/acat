

# ------------------------------------------------
# 🧭 Section 1: Environment Setup and Initialization
# ------------------------------------------------

"""
This section sets up the required environment, authentication, and Azure OpenAI connection.
The notebook uses your approved packages and reads data files from `/data/`.
"""

import os
import json
import httpx
import pandas as pd
from dotenv import load_dotenv
from typing import Dict, Any
from langchain_openai import AzureOpenAI
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv("./Data/UAIS_vars.env")

# Azure OpenAI environment variables (as per your setup)
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("MODEL_DEPLOYMENT_NAME")  # gpt-4o-mini_2024-07-18
project_id = os.getenv("PROJECT_ID")
api_version = os.getenv("OPENAI_API_VERSION")

# Authentication using UHG OAuth2
def get_access_token() -> str:
    """
    Retrieves access token using client credentials.
    """
    print("🔐 Fetching access token...")
    auth = "https://api.uhg.com/oauth2/token"
    scope = "https://api.uhg.com/.default"
    grant_type = "client_credentials"

    body = {
        "grant_type": grant_type,
        "scope": scope,
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    with httpx.Client() as client:
        resp = client.post(auth, headers=headers, data=body, timeout=60)
        resp.raise_for_status()
        access_token = resp.json().get("access_token")

    print("✅ Access token retrieved successfully.\n")
    return access_token

# Initialize Azure OpenAI client
print("⚙️ Initializing Azure OpenAI client...")
chat_client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_version=api_version,
    azure_deployment=model_name,
    azure_ad_token=get_access_token(),
    default_headers={"projectId": project_id},
)
print("✅ Azure OpenAI client initialized.\n")

# ------------------------------------------------
# 📂 Section 2: Dataset Loading
# ------------------------------------------------

"""
This section loads all JSON input files required for the project.
Files should be placed under `/data` folder.

Example structures:
- insurance_policies.json
- reference_codes.json
- validation_records.json
- test_records.json
"""

def load_json(file_path: str) -> Any:
    with open(file_path, "r") as f:
        return json.load(f)

print("📂 Loading input datasets...")

REFERENCE_CODES = load_json("./data/reference_codes.json")
POLICIES = load_json("./data/insurance_policies.json")
VALIDATION = load_json("./data/validation_records.json")
TEST = load_json("./data/test_records.json")

print(f"✅ Loaded {len(POLICIES)} policies and {len(TEST)} test records.\n")

# ------------------------------------------------
# 🧠 Section 3: Tool 1 — Summarize Patient Record
# ------------------------------------------------

def summarize_patient_record(record_str: Dict[str, Any]) -> str:
    print("🩺 Summarizing patient record...")
    prompt = f"""
    You are a medical claim summarizer. Summarize the following patient insurance claim record into a structured summary.
    Include: Patient Demographics, Insurance Policy ID, Diagnoses, Procedures, Preauthorization Status, Billed Amount, and Date of Service.

    Use bullet points. Do not make decisions.
    Map ICD-10 and CPT codes using reference descriptions.

    Patient Record:
    {json.dumps(record_str, indent=2)}
    Reference Codes:
    {json.dumps(REFERENCE_CODES)[:1000]}
    """

    response = chat_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a medical insurance data summarizer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    summary = response.choices[0].message.content
    print("✅ Patient record summarized.\n")
    return summary

# ------------------------------------------------
# 📜 Section 4: Tool 2 — Summarize Policy Guideline
# ------------------------------------------------

def summarize_policy_guideline(policy_id: str) -> str:
    print(f"📘 Summarizing policy guideline for {policy_id}...")
    policy_data = next((p for p in POLICIES if p["policy_id"] == policy_id), None)
    if not policy_data:
        return f"⚠️ Policy ID {policy_id} not found."

    prompt = f"""
    You are a policy summarizer. Summarize this insurance policy into labeled sections:
    - Policy Details
    - Covered Procedures (with CPT and ICD-10 descriptions, gender restriction, age range, preauthorization requirement, and notes).

    Policy Document:
    {json.dumps(policy_data, indent=2)}
    Reference Codes:
    {json.dumps(REFERENCE_CODES)[:1000]}
    """

    response = chat_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You summarize insurance policy coverage rules."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    summary = response.choices[0].message.content
    print(f"✅ Policy {policy_id} summarized.\n")
    return summary

# ------------------------------------------------
# 🧾 Section 5: Tool 3 — Validate Claim Coverage
# ------------------------------------------------

def check_claim_coverage(record_summary: str, policy_summary: str) -> str:
    print("🧮 Validating insurance claim coverage...")
    prompt = f"""
    Determine claim coverage eligibility based on:
    1. Diagnosis and procedure match between patient record and policy.
    2. Age, gender, and preauthorization compliance.
    3. Billed amount vs coverage limit.

    Return decision and reasoning in the format:
    - Decision: APPROVE or ROUTE FOR REVIEW
    - Reason: <brief justification>

    Patient Summary:
    {record_summary}

    Policy Summary:
    {policy_summary}
    """

    response = chat_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are an insurance claim coverage validator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    result = response.choices[0].message.content
    print("✅ Claim validation complete.\n")
    return result

# ------------------------------------------------
# 🤖 Section 6: Agent Orchestration (LangGraph)
# ------------------------------------------------

def process_claim(record: Dict[str, Any]) -> str:
    print(f"🧩 Processing patient {record['patient_id']}...")
    record_summary = summarize_patient_record(record)
    policy_summary = summarize_policy_guideline(record["insurance_policy_id"])
    result = check_claim_coverage(record_summary, policy_summary)
    print(f"🏁 Completed processing for {record['patient_id']}.\n")
    return result

# ------------------------------------------------
# 📈 Section 7: Run Agent on Test Dataset
# ------------------------------------------------

submission_data = []

for record in TEST:
    try:
        output = process_claim(record)
        submission_data.append({
            "patient_id": record["patient_id"],
            "generated_response": output
        })
    except Exception as e:
        print(f"⚠️ Error processing {record['patient_id']}: {str(e)}")
        submission_data.append({
            "patient_id": record["patient_id"],
            "generated_response": f"Error: {str(e)}"
        })

df = pd.DataFrame(submission_data)

# 🧹 Clean up extra whitespace, newlines, and spacing from responses
df["generated_response"] = (
    df["generated_response"]
    .astype(str)
    .str.replace(r"\\n", " ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

df.to_csv("submission.csv", index=False)

print("✅ Submission file generated: submission.csv\n")
print(df.head())

# ------------------------------------------------
# 🏁 End of Notebook
# ------------------------------------------------

"""
Notes:
- Ensure JSON files are available in the /data directory.
- submission.csv will contain 2 columns:
    1. patient_id
    2. generated_response
- Do not alter output format for Capstone submission.
"""
