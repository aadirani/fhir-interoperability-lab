"""Terminology mapping: the legacy system's local codes -> LOINC codes and UCUM units.

LOINC identifies *what* was measured; UCUM is the standard syntax for units.
This table is the single place where "HR" in the old system becomes LOINC 8867-4.
"""

LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
OBS_CATEGORY = "http://terminology.hl7.org/CodeSystem/observation-category"

# Fictional organisation namespace (example.org is reserved for documentation).
MRN_SYSTEM = "https://hospital.example.org/fhir/mrn"
LOCAL_CODE_SYSTEM = "https://hospital.example.org/fhir/local-observation-codes"
OBS_ID_SYSTEM = "https://hospital.example.org/fhir/observation-id"

# Every generated resource is labelled as test data (HL7 security label HTEST).
SYNTHETIC_LABEL = {"system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                   "code": "HTEST", "display": "test health data"}

OBSERVATIONS = {
    "HR":   {"loinc": "8867-4", "display": "Heart rate", "ucum": "/min", "unit": "beats/minute",
             "category": "vital-signs", "range": (20, 250)},
    "SBP":  {"loinc": "8480-6", "display": "Systolic blood pressure", "ucum": "mm[Hg]", "unit": "mmHg",
             "category": "vital-signs", "range": (50, 260)},
    "DBP":  {"loinc": "8462-4", "display": "Diastolic blood pressure", "ucum": "mm[Hg]", "unit": "mmHg",
             "category": "vital-signs", "range": (20, 160)},
    "TEMP": {"loinc": "8310-5", "display": "Body temperature", "ucum": "Cel", "unit": "°C",
             "category": "vital-signs", "range": (30, 43)},
    "WT":   {"loinc": "29463-7", "display": "Body weight", "ucum": "kg", "unit": "kg",
             "category": "vital-signs", "range": (0.3, 400)},
    "GLU":  {"loinc": "2339-0", "display": "Glucose [Mass/volume] in Blood", "ucum": "mg/dL",
             "unit": "mg/dL", "category": "laboratory", "range": (10, 1500)},
    "HGB":  {"loinc": "718-7", "display": "Hemoglobin [Mass/volume] in Blood", "ucum": "g/dL",
             "unit": "g/dL", "category": "laboratory", "range": (2, 25)},
}

# FHIR's vital-signs profile records blood pressure as ONE panel with two components.
BP_PANEL = {"loinc": "85354-9", "display": "Blood pressure panel with all children optional"}

# Units the legacy system may send, and the factor to convert to the target unit.
# Glucose: mmol/L x 18.016 = mg/dL (molar mass of glucose ~180.16 g/mol).
LEGACY_UNITS = {
    "HR": {"bpm": 1.0, "/min": 1.0},
    "SBP": {"mmHg": 1.0},
    "DBP": {"mmHg": 1.0},
    "TEMP": {"C": 1.0},
    "WT": {"kg": 1.0},
    "GLU": {"mg/dL": 1.0, "mmol/L": 18.016},
    "HGB": {"g/dL": 1.0},
}

GENDER = {"M": "male", "F": "female", "O": "other", "U": "unknown"}
