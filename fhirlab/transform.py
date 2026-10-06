"""Transform legacy CSV rows into a FHIR R4 transaction Bundle.

Rows that can't be mapped safely are not guessed at: they go to a rejection list
with the reason, so someone can fix them at the source.
"""

import uuid
from collections import OrderedDict
from datetime import datetime, timezone

from . import mapping as m

# Fixed namespace so the same input always gives the same resource UUIDs (repeatable output).
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://hospital.example.org/fhir")


def _zone(name):
    if name.upper() == "UTC":
        return timezone.utc
    from zoneinfo import ZoneInfo  # handles daylight saving, e.g. "Asia/Beirut"
    return ZoneInfo(name)


def fhir_datetime(local_text, tz="UTC"):
    """'2025-03-01 09:30' in the legacy system's local time -> '2025-03-01T09:30:00+02:00'."""
    local = datetime.strptime(local_text, "%Y-%m-%d %H:%M").replace(tzinfo=_zone(tz))
    text = local.isoformat(timespec="seconds")
    return text.replace("+00:00", "Z")


def full_url(kind, key):
    return f"urn:uuid:{uuid.uuid5(NAMESPACE, f'{kind}/{key}')}"


def quantity(code, value):
    spec = m.OBSERVATIONS[code]
    return {"value": round(value, 2), "unit": spec["unit"], "system": m.UCUM, "code": spec["ucum"]}


def coding(code):
    spec = m.OBSERVATIONS[code]
    return {"system": m.LOINC, "code": spec["loinc"], "display": spec["display"]}


def patient_entry(row):
    mrn = row["mrn"]
    resource = {
        "resourceType": "Patient",
        "meta": {"security": [m.SYNTHETIC_LABEL]},
        "identifier": [{"system": m.MRN_SYSTEM, "value": mrn}],
        "name": [{"family": row["last_name"], "given": [row["first_name"]]}],
        "gender": m.GENDER.get(row["sex"].upper(), "unknown"),
        "birthDate": row["birth_date"],
    }
    # Conditional update: "create or update the patient with this MRN" -> safe to re-send.
    return {"fullUrl": full_url("Patient", mrn), "resource": resource,
            "request": {"method": "PUT", "url": f"Patient?identifier={m.MRN_SYSTEM}|{mrn}"}}


def observation_entry(mrn, code, effective, category, obs_code, value=None, components=None):
    obs_id = f"{mrn}-{code}-{effective[:16].replace('-', '').replace('T', '').replace(':', '')}"
    resource = {
        "resourceType": "Observation",
        "meta": {"security": [m.SYNTHETIC_LABEL]},
        "identifier": [{"system": m.OBS_ID_SYSTEM, "value": obs_id}],
        "status": "final",
        "category": [{"coding": [{"system": m.OBS_CATEGORY, "code": category}]}],
        "code": obs_code,
        "subject": {"reference": full_url("Patient", mrn)},
        "effectiveDateTime": effective,
    }
    if value is not None:
        resource["valueQuantity"] = value
    if components:
        resource["component"] = components
    return {"fullUrl": full_url("Observation", obs_id), "resource": resource,
            "request": {"method": "PUT", "url": f"Observation?identifier={m.OBS_ID_SYSTEM}|{obs_id}"}}


def clean_value(row):
    """Return (code, value in target unit) or raise ValueError with a readable reason."""
    code = row["code"].strip().upper()
    if code not in m.OBSERVATIONS:
        raise ValueError(f"unknown local code '{row['code']}'")
    try:
        value = float(row["value"])
    except (TypeError, ValueError):
        raise ValueError(f"value '{row['value']}' is not a number")
    factor = m.LEGACY_UNITS[code].get(row["unit"].strip())
    if factor is None:
        raise ValueError(f"unit '{row['unit']}' not accepted for {code}")
    value *= factor
    low, high = m.OBSERVATIONS[code]["range"]
    if not low <= value <= high:
        raise ValueError(f"{code} value {value:g} outside plausible range {low}-{high}")
    return code, value


def build_bundle(patient_rows, observation_rows, tz="UTC"):
    """Return (bundle, rejected) where rejected is a list of {line, row, reason}."""
    entries, rejected = [], []
    known = set()
    for row in patient_rows:
        entries.append(patient_entry(row))
        known.add(row["mrn"])

    blood_pressure = OrderedDict()  # (mrn, time) -> {"SBP": (value, line), "DBP": ...}
    for line, row in enumerate(observation_rows, start=2):  # line 1 is the CSV header
        try:
            if row["mrn"] not in known:
                raise ValueError(f"patient {row['mrn']} not found in patients.csv")
            code, value = clean_value(row)
            effective = fhir_datetime(row["taken_at"], tz)
        except ValueError as err:
            rejected.append({"line": line, "row": row, "reason": str(err)})
            continue

        if code in ("SBP", "DBP"):
            blood_pressure.setdefault((row["mrn"], effective), {})[code] = (value, line, row)
            continue
        spec = m.OBSERVATIONS[code]
        entries.append(observation_entry(row["mrn"], code, effective, spec["category"],
                                         {"coding": [coding(code)], "text": spec["display"]},
                                         value=quantity(code, value)))

    for (mrn, effective), parts in blood_pressure.items():
        if set(parts) != {"SBP", "DBP"}:
            for value, line, row in parts.values():
                rejected.append({"line": line, "row": row,
                                 "reason": "blood pressure needs both systolic and diastolic values"})
            continue
        panel = {"coding": [{"system": m.LOINC, "code": m.BP_PANEL["loinc"],
                             "display": m.BP_PANEL["display"]}], "text": "Blood pressure"}
        components = [{"code": {"coding": [coding(c)]}, "valueQuantity": quantity(c, parts[c][0])}
                      for c in ("SBP", "DBP")]
        entries.append(observation_entry(mrn, "BP", effective, "vital-signs", panel, components=components))

    bundle = {"resourceType": "Bundle", "type": "transaction", "entry": entries}
    return bundle, rejected
