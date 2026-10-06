"""Generate a SYNTHETIC export from an imaginary legacy hospital system (two CSV files).

Everything is random and reproducible from a seed. No real patients. A few rows are
deliberately broken so the transformer's error handling can be demonstrated.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

FIRST = ["Adam", "Lina", "Omar", "Maya", "Karim", "Nour", "Sami", "Rana",
         "Hadi", "Dana", "Fadi", "Yara", "Ziad", "Hiba", "Tarek", "Reem"]
LAST = ["Haddad", "Khoury", "Saleh", "Nasser", "Fares", "Mansour", "Aziz", "Hamdan", "Rizk", "Sabbagh"]


def generate(n_patients=20, seed=42, visits=3):
    rng = random.Random(seed)
    patients, observations = [], []
    start = datetime(2025, 1, 1)
    for i in range(1, n_patients + 1):
        mrn = f"SYN-{i:04d}"
        sex = rng.choice("MF")
        birth = datetime(1940, 1, 1) + timedelta(days=rng.randint(0, 365 * 65))
        patients.append({"mrn": mrn, "first_name": rng.choice(FIRST), "last_name": rng.choice(LAST),
                         "sex": sex, "birth_date": birth.strftime("%Y-%m-%d")})
        weight = rng.uniform(50, 110)
        for _ in range(visits):
            t = start + timedelta(days=rng.randint(0, 540), minutes=rng.randint(7 * 60, 19 * 60))
            when = t.strftime("%Y-%m-%d %H:%M")
            sbp = rng.randint(100, 160)
            rows = [
                ("HR", rng.randint(55, 110), "bpm"),
                ("SBP", sbp, "mmHg"),
                ("DBP", rng.randint(60, min(100, sbp - 25)), "mmHg"),
                ("TEMP", round(rng.uniform(36.2, 38.5), 1), "C"),
                ("WT", round(weight + rng.uniform(-1.5, 1.5), 1), "kg"),
            ]
            if rng.random() < 0.5:  # lab tests on about half the visits
                if rng.random() < 0.2:  # some labs report glucose in mmol/L
                    rows.append(("GLU", round(rng.uniform(3.9, 11.1), 1), "mmol/L"))
                else:
                    rows.append(("GLU", rng.randint(70, 200), "mg/dL"))
                rows.append(("HGB", round(rng.uniform(10, 16), 1), "g/dL"))
            observations += [{"mrn": mrn, "taken_at": when, "code": c, "value": v, "unit": u}
                             for c, v, u in rows]

    # Deliberately broken rows: the kind of thing real exports contain.
    observations += [
        {"mrn": "SYN-0001", "taken_at": "2025-06-01 10:00", "code": "HR", "value": "abc", "unit": "bpm"},
        {"mrn": "SYN-0002", "taken_at": "2025-06-01 10:00", "code": "TEMP", "value": 45.0, "unit": "C"},
        {"mrn": "SYN-0003", "taken_at": "2025-06-01 10:00", "code": "XYZ", "value": 1, "unit": "x"},
        {"mrn": "SYN-9999", "taken_at": "2025-06-01 10:00", "code": "HR", "value": 80, "unit": "bpm"},
        {"mrn": "SYN-0004", "taken_at": "2025-06-01 10:00", "code": "SBP", "value": 120, "unit": "mmHg"},
    ]
    return patients, observations


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_export(out_dir, n_patients=20, seed=42):
    patients, observations = generate(n_patients, seed)
    out = Path(out_dir)
    write_csv(out / "patients.csv", patients)
    write_csv(out / "observations.csv", observations)
    return len(patients), len(observations)
