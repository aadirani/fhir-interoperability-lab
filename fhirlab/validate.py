"""Lightweight structural checks for the generated Bundle.

This is NOT a full FHIR conformance validator. It catches the mistakes this pipeline
could make (broken references, missing codes, bad dates). For full validation against
the FHIR specification and profiles, use the official HL7 FHIR Validator or a FHIR server.
"""

import re

from .mapping import LOINC, UCUM

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$")
GENDERS = {"male", "female", "other", "unknown"}
OBS_STATUS = {"registered", "preliminary", "final", "amended", "corrected", "cancelled",
              "entered-in-error", "unknown"}


def _check_quantity(q, where, problems):
    if not isinstance(q.get("value"), (int, float)):
        problems.append(f"{where}: quantity value must be a number")
    if q.get("system") != UCUM or not q.get("code"):
        problems.append(f"{where}: quantity must use a UCUM code")


def validate_bundle(bundle):
    problems = []
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "transaction":
        return ["not a transaction Bundle"]

    entries = bundle.get("entry", [])
    urls = [e.get("fullUrl") for e in entries]
    if len(urls) != len(set(urls)):
        problems.append("duplicate fullUrl values")
    patients = {e["fullUrl"] for e in entries if e.get("resource", {}).get("resourceType") == "Patient"}

    for i, e in enumerate(entries):
        r, where = e.get("resource", {}), f"entry[{i}]"
        if not str(e.get("fullUrl", "")).startswith("urn:uuid:"):
            problems.append(f"{where}: fullUrl must be a urn:uuid")
        req = e.get("request", {})
        if req.get("method") not in ("PUT", "POST") or not req.get("url"):
            problems.append(f"{where}: missing or invalid request")

        kind = r.get("resourceType")
        if kind == "Patient":
            ids = r.get("identifier") or [{}]
            if not ids[0].get("system") or not ids[0].get("value"):
                problems.append(f"{where}: Patient needs an identifier with system and value")
            if r.get("gender") not in GENDERS:
                problems.append(f"{where}: invalid gender '{r.get('gender')}'")
            if not DATE.match(str(r.get("birthDate", ""))):
                problems.append(f"{where}: birthDate must be YYYY-MM-DD")
        elif kind == "Observation":
            if r.get("status") not in OBS_STATUS:
                problems.append(f"{where}: invalid status")
            codings = r.get("code", {}).get("coding", [])
            if not codings or codings[0].get("system") != LOINC or not codings[0].get("code"):
                problems.append(f"{where}: Observation.code must have a LOINC coding")
            if r.get("subject", {}).get("reference") not in patients:
                problems.append(f"{where}: subject does not point to a Patient in this Bundle")
            if not DATETIME.match(str(r.get("effectiveDateTime", ""))):
                problems.append(f"{where}: effectiveDateTime needs date, time and time zone")
            if "valueQuantity" in r:
                _check_quantity(r["valueQuantity"], where, problems)
            elif r.get("component"):
                for j, c in enumerate(r["component"]):
                    _check_quantity(c.get("valueQuantity", {}), f"{where}.component[{j}]", problems)
            else:
                problems.append(f"{where}: Observation has no value")
        else:
            problems.append(f"{where}: unexpected resource type {kind}")
    return problems
