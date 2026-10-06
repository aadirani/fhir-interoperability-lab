# Example input and output (synthetic)

Produced by CI with:

```bash
python -m fhirlab generate --out build/example/legacy --patients 3 --seed 7
python -m fhirlab transform --in build/example/legacy --out build/example/fhir --timezone Asia/Beirut
```

| File | What it is |
|---|---|
| [legacy/patients.csv](legacy/patients.csv) | The "old system" patient export (3 synthetic patients) |
| [legacy/observations.csv](legacy/observations.csv) | Vital signs and lab results, including 5 deliberately broken rows |
| [fhir/bundle.json](fhir/bundle.json) | The FHIR R4 transaction Bundle: 3 Patients, 48 Observations (9 blood-pressure panels) |
| [fhir/rejected.csv](fhir/rejected.csv) | The 5 rows that couldn't be mapped safely, with reasons |

With only 3 patients, the broken row for `SYN-0004` is rejected as an unknown patient. In the 20-patient run it's rejected for having a systolic value without a diastolic one.
