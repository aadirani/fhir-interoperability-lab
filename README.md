# FHIR Interoperability Lab

![tests](https://github.com/aadirani/fhir-interoperability-lab/actions/workflows/tests.yml/badge.svg)

Convert an export from an (imaginary) old hospital system into **HL7 FHIR R4**, the modern standard for exchanging health data, using **LOINC** codes and **UCUM** units, with every unmappable row rejected and explained. **All data is synthetic.**

## The idea in one paragraph

Old hospital systems each use their own codes: one writes "HR", another "PULSE". FHIR gives everyone the same record structure. LOINC gives every measurement a universal code (heart rate = `8867-4`), and UCUM writes every unit the same way. This lab generates a fake legacy export, translates it to FHIR, **refuses to guess** when a row is wrong (an unknown code, a temperature of 45 °C, glucose in an unexpected unit), and checks the result before it would go to a FHIR server.

## Quick start

Needs Python 3.9+. Nothing to install.

```bash
python -m fhirlab generate --out build/legacy --patients 20 --seed 42
python -m fhirlab transform --in build/legacy --out build/fhir --timezone Asia/Beirut
python -m fhirlab validate build/fhir/bundle.json
```

The transform step prints how many resources it produced and lists every rejected row with its reason, for example:

```
rejected rows: 5 -> build/fhir/rejected.csv
  line ...: value 'abc' is not a number
  line ...: TEMP value 45 outside plausible range 30-43
  line ...: unknown local code 'XYZ'
  line ...: patient SYN-9999 not found in patients.csv
  line ...: blood pressure needs both systolic and diastolic values
```

A small example of the input and output (3 synthetic patients) is in [examples/](examples/).

## What's inside

| Path | What it is |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Standards, design, target integration architecture, 7 decision records, risks, costs |
| [fhirlab/mapping.py](fhirlab/mapping.py) | The terminology map: local codes → LOINC + UCUM, unit conversions, plausible ranges |
| [fhirlab/transform.py](fhirlab/transform.py) | CSV → FHIR transaction Bundle, with rejections |
| [fhirlab/validate.py](fhirlab/validate.py) | Structural checks (not a full conformance validator) |
| [fhirlab/generate.py](fhirlab/generate.py) | Synthetic legacy export, including deliberately broken rows |
| [docs/code-walkthrough.md](docs/code-walkthrough.md) | Plain-language explanation |

## Limitations

- Only `Patient` and `Observation` resources. Encounters, conditions and medications are natural next steps.
- `validate` checks this pipeline's own output. Use the official HL7 FHIR Validator for full conformance before any real use.
