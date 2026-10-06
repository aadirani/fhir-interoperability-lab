"""Command line:
  python -m fhirlab generate --out build/legacy                  synthetic legacy CSV export
  python -m fhirlab transform --in build/legacy --out build/fhir  CSV -> FHIR transaction Bundle
  python -m fhirlab validate build/fhir/bundle.json               structural checks
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from .generate import write_export
from .transform import build_bundle
from .validate import validate_bundle


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cmd_generate(a):
    n_p, n_o = write_export(a.out, a.patients, a.seed)
    print(f"wrote {n_p} patients and {n_o} observation rows to {a.out} (SYNTHETIC)")


def cmd_transform(a):
    src, out = Path(a.input), Path(a.out)
    bundle, rejected = build_bundle(read_csv(src / "patients.csv"), read_csv(src / "observations.csv"),
                                    tz=a.timezone)
    out.mkdir(parents=True, exist_ok=True)
    (out / "bundle.json").write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(out / "rejected.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["line", "mrn", "code", "value", "unit", "reason"])
        for r in rejected:
            row = r["row"]
            w.writerow([r["line"], row["mrn"], row["code"], row["value"], row["unit"], r["reason"]])

    counts = Counter(e["resource"]["resourceType"] for e in bundle["entry"])
    panels = sum(1 for e in bundle["entry"] if "component" in e["resource"])
    print(f"bundle: {counts['Patient']} Patient, {counts['Observation']} Observation "
          f"({panels} blood-pressure panels) -> {out / 'bundle.json'}")
    print(f"rejected rows: {len(rejected)} -> {out / 'rejected.csv'}")
    for r in rejected:
        print(f"  line {r['line']}: {r['reason']}")


def cmd_validate(a):
    bundle = json.loads(Path(a.bundle).read_text(encoding="utf-8"))
    problems = validate_bundle(bundle)
    for p in problems:
        print(p)
    print(f"{len(bundle.get('entry', []))} entries checked, {len(problems)} problem(s)")
    if problems:
        sys.exit(1)


def main(argv=None):
    p = argparse.ArgumentParser(prog="fhirlab", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate")
    g.add_argument("--out", default="build/legacy")
    g.add_argument("--patients", type=int, default=20)
    g.add_argument("--seed", type=int, default=42)
    g.set_defaults(func=cmd_generate)

    t = sub.add_parser("transform")
    t.add_argument("--in", dest="input", default="build/legacy")
    t.add_argument("--out", default="build/fhir")
    t.add_argument("--timezone", default="UTC",
                   help="time zone of the legacy timestamps, e.g. Asia/Beirut (default UTC)")
    t.set_defaults(func=cmd_transform)

    v = sub.add_parser("validate")
    v.add_argument("bundle")
    v.set_defaults(func=cmd_validate)

    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
