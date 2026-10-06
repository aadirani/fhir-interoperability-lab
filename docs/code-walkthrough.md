# Code walkthrough

A plain-language guide for explaining this project in an interview.

## Vocabulary

- **FHIR** (pronounced "fire"): a standard from HL7 for health records as JSON "resources" with a REST API. A `Patient` is one resource, and each measurement is an `Observation`.
- **Bundle**: a package of resources. A **transaction** Bundle is applied all-or-nothing by the server.
- **LOINC**: universal codes for measurements and lab tests.
- **UCUM**: a precise way to write units (`mm[Hg]` for millimetres of mercury, `Cel` for degrees Celsius).
- **MRN**: medical record number, the hospital's patient ID.

## `mapping.py`: the translation table

One dictionary says, for each local code, which LOINC code, display name, unit and category (vital sign or lab) it maps to, and what range of values is physically plausible. `LEGACY_UNITS` lists which units the old system may send and how to convert them. Glucose in mmol/L is multiplied by 18.016 to get mg/dL. Keeping all of this in one place means a clinician can review the mapping without reading any logic.

## `generate.py`: fake data that behaves like real data

It creates patients with random names, sexes and birth dates, plus 3 visits each with heart rate, blood pressure, temperature and weight, and lab results on about half the visits. Some glucose results are in mmol/L. A fixed **seed** makes it reproducible. At the end it adds **5 deliberately broken rows**, so the error handling is always exercised.

## `transform.py`: the core

1. **Patients:** each CSV row becomes a `Patient` with an identifier (system + MRN), name, gender (`M` → `male`) and birth date, labelled `HTEST` (test data).
2. **Each observation row** goes through `clean_value()`: known code? numeric value? accepted unit, converted if needed? plausible range? If any check fails, the row goes to the **rejected** list with a readable reason.
3. **Blood pressure:** systolic and diastolic rows with the same patient and time are combined into **one** panel Observation with two components. That's how FHIR's vital-signs profile expects it.
4. **Every entry** has a `fullUrl` (a UUID worked out from the identifiers, so it's the same every run) and a request `PUT Patient?identifier=…`, which means *create or update*, so re-loading never duplicates.
5. **Observations point to their patient** through `subject.reference` = the patient's `fullUrl`. The FHIR server resolves that link when it processes the transaction.

`fhir_datetime()` adds the time zone that FHIR requires: `2025-03-01 09:30` + `Asia/Beirut` → `2025-03-01T09:30:00+02:00`, and daylight saving is handled automatically.

## `validate.py`

It checks the Bundle for mistakes this pipeline could make: duplicate IDs, references that point nowhere, missing LOINC codes, units that aren't UCUM, dates without time zones, invalid gender values. It says clearly that it is *not* a full FHIR validator.

## Likely interview questions

- **"Why not just fix bad values automatically?"** In healthcare a wrong number is dangerous. Rejecting with a reason lets the data owner fix it at the source (ADR-004).
- **"How do you avoid duplicate patients when the job runs twice?"** Conditional `PUT` on the MRN identifier (ADR-002). In a multi-system setting, a master patient index matches patients across systems.
- **"Why one Observation for blood pressure?"** The FHIR vital-signs profile defines it that way (LOINC 85354-9 with two components), so other systems recognise it (ADR-003).
- **"How would this connect to a real system?"** Same mapping logic inside an integration layer, feeding a FHIR server that apps access through SMART on FHIR with OAuth 2.0 (ARCHITECTURE.md §3).
- **"Is the data real?"** No, it's entirely synthetic and labelled `HTEST`.
