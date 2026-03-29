"""Generate production-grade synthetic demo datasets for PHARMA-OS.

Creates relationally consistent CSV datasets under data/demo/:
- patients
- trials
- drug_exposures
- adverse_events
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
REFERENCE_DATE = date(2026, 3, 1)

PATIENT_COUNT = 2000
TRIAL_COUNT = 60
EXPOSURE_COUNT = 7000
EVENT_COUNT = 6000

CONDITIONS = ["cancer", "diabetes", "cardiovascular", "respiratory", "neurological"]
CONDITION_PROBS = np.array([0.17, 0.28, 0.24, 0.16, 0.15])

REGIONS = ["US", "EU", "ASIA"]
REGION_PROBS = np.array([0.55, 0.27, 0.18])

EVENT_TYPES_BY_CLASS: dict[str, list[str]] = {
    "oncology": ["nausea", "fatigue", "neutropenia", "liver_toxicity", "rash"],
    "antidiabetic": ["hypoglycemia", "headache", "nausea", "dizziness"],
    "antihypertensive": ["hypotension", "dizziness", "arrhythmia", "fatigue"],
    "respiratory": ["cough", "bronchospasm", "headache", "nausea"],
    "neurology": ["sedation", "dizziness", "headache", "cognitive_fog"],
    "lipid_lowering": ["myalgia", "liver_toxicity", "headache", "fatigue"],
    "anticoagulant": ["bleeding", "bruising", "headache", "nausea"],
}

CLASS_BASE_RISK = {
    "oncology": 0.32,
    "anticoagulant": 0.24,
    "antihypertensive": 0.16,
    "antidiabetic": 0.15,
    "respiratory": 0.14,
    "neurology": 0.18,
    "lipid_lowering": 0.12,
}

DOSE_RANGES_MG = {
    "oncology": (20, 250),
    "antidiabetic": (250, 2000),
    "antihypertensive": (2, 160),
    "respiratory": (50, 500),
    "neurology": (5, 400),
    "lipid_lowering": (5, 80),
    "anticoagulant": (1, 20),
}


@dataclass(frozen=True)
class DrugSpec:
    drug_name: str
    drug_class: str
    indications: tuple[str, ...]


DRUG_CATALOG: tuple[DrugSpec, ...] = (
    DrugSpec("Pembrolizumab", "oncology", ("cancer",)),
    DrugSpec("Trastuzumab", "oncology", ("cancer",)),
    DrugSpec("Imatinib", "oncology", ("cancer",)),
    DrugSpec("Metformin", "antidiabetic", ("diabetes", "cardiovascular")),
    DrugSpec("Insulin Glargine", "antidiabetic", ("diabetes",)),
    DrugSpec("Empagliflozin", "antidiabetic", ("diabetes", "cardiovascular")),
    DrugSpec("Lisinopril", "antihypertensive", ("cardiovascular", "diabetes")),
    DrugSpec("Amlodipine", "antihypertensive", ("cardiovascular",)),
    DrugSpec("Losartan", "antihypertensive", ("cardiovascular", "renal")),
    DrugSpec("Atorvastatin", "lipid_lowering", ("cardiovascular", "diabetes")),
    DrugSpec("Rosuvastatin", "lipid_lowering", ("cardiovascular",)),
    DrugSpec("Apixaban", "anticoagulant", ("cardiovascular",)),
    DrugSpec("Warfarin", "anticoagulant", ("cardiovascular",)),
    DrugSpec("Budesonide", "respiratory", ("respiratory",)),
    DrugSpec("Fluticasone", "respiratory", ("respiratory",)),
    DrugSpec("Montelukast", "respiratory", ("respiratory",)),
    DrugSpec("Levetiracetam", "neurology", ("neurological",)),
    DrugSpec("Gabapentin", "neurology", ("neurological",)),
    DrugSpec("Donepezil", "neurology", ("neurological",)),
    DrugSpec("Duloxetine", "neurology", ("neurological", "respiratory")),
)


def _clip_int(values: np.ndarray, lo: int, hi: int) -> np.ndarray:
    return np.clip(np.rint(values), lo, hi).astype(int)


def _sample_truncated_normal_int(
    rng: np.random.Generator,
    *,
    mean: float,
    sd: float,
    low: int,
    high: int,
    size: int,
) -> np.ndarray:
    vals = rng.normal(mean, sd, size)
    return _clip_int(vals, low, high)


def generate_patients(rng: np.random.Generator, n: int = PATIENT_COUNT) -> pd.DataFrame:
    patient_ids = [f"PAT{idx:05d}" for idx in range(1, n + 1)]
    ages = _sample_truncated_normal_int(rng, mean=52, sd=14, low=18, high=85, size=n)
    sex = rng.choice(["F", "M"], size=n, p=[0.53, 0.47])
    region = rng.choice(REGIONS, size=n, p=REGION_PROBS)
    condition = rng.choice(CONDITIONS, size=n, p=CONDITION_PROBS)

    age_risk = np.clip((ages - 30) / 16, 0, 4.2)
    condition_risk = np.array([
        1.3 if c == "cardiovascular" else 1.15 if c == "diabetes" else 0.9 for c in condition
    ])
    comorbidity_raw = rng.poisson(lam=0.6 + 0.58 * age_risk + 0.45 * condition_risk)
    comorbidity_count = np.clip(comorbidity_raw, 0, 5)

    medication_noise = rng.poisson(lam=1.1, size=n)
    medication_base = comorbidity_count * 1.25 + medication_noise
    condition_med_bonus = np.array([
        1.1 if c in {"diabetes", "cardiovascular"} else 0.7 if c == "cancer" else 0.4 for c in condition
    ])
    medication_count = np.clip(np.rint(medication_base + condition_med_bonus), 0, 8).astype(int)

    bmi = np.clip(rng.normal(loc=27.0, scale=5.0, size=n), 16.0, 50.0)

    smoker_base = np.array([
        0.28 if c == "respiratory" else 0.22 if c == "cardiovascular" else 0.16 if c == "cancer" else 0.12
        for c in condition
    ])
    smoker_regional_adjust = np.array([0.03 if r == "EU" else -0.02 if r == "ASIA" else 0.0 for r in region])
    smoker_prob = np.clip(smoker_base + smoker_regional_adjust, 0.04, 0.45)
    smoker = rng.random(n) < smoker_prob

    renal_prob = np.clip(0.03 + 0.0036 * ages + 0.055 * comorbidity_count, 0.02, 0.72)
    renal_impairment = rng.random(n) < renal_prob

    liver_prob = np.clip(
        0.02
        + 0.0018 * ages
        + 0.06 * smoker.astype(float)
        + np.where(condition == "cancer", 0.08, 0.0),
        0.01,
        0.52,
    )
    liver_impairment = rng.random(n) < liver_prob

    pregnancy_eligible = (sex == "F") & (ages >= 18) & (ages <= 45)
    pregnancy_prob = np.where(pregnancy_eligible, 0.045, 0.0)
    pregnancy_flag = rng.random(n) < pregnancy_prob

    days_since_visit = _clip_int(rng.gamma(shape=2.2, scale=75.0, size=n), 0, 730)
    last_visit = [REFERENCE_DATE - timedelta(days=int(d)) for d in days_since_visit]

    patients = pd.DataFrame(
        {
            "patient_id": patient_ids,
            "age": ages,
            "sex": sex,
            "region": region,
            "condition": condition,
            "comorbidity_count": comorbidity_count.astype(int),
            "medication_count": medication_count.astype(int),
            "bmi": np.round(bmi, 1),
            "smoker": smoker,
            "renal_impairment": renal_impairment,
            "liver_impairment": liver_impairment,
            "pregnancy_flag": pregnancy_flag,
            "last_visit_date": pd.to_datetime(last_visit).date.astype(str),
        }
    )
    return patients


def generate_trials(rng: np.random.Generator, patients: pd.DataFrame, n: int = TRIAL_COUNT) -> pd.DataFrame:
    trial_ids = [f"TRL{idx:04d}" for idx in range(1, n + 1)]

    condition_freq = (
        patients["condition"].value_counts(normalize=True).reindex(CONDITIONS).fillna(0.0).to_numpy()
    )
    indication = rng.choice(CONDITIONS, size=n, p=condition_freq)

    phase = rng.choice(["Phase 1", "Phase 2", "Phase 3"], size=n, p=[0.22, 0.36, 0.42])

    recruiting_status: list[str] = []
    for ph in phase:
        if ph == "Phase 1":
            recruiting_status.append(rng.choice(["recruiting", "paused", "completed"], p=[0.66, 0.22, 0.12]))
        elif ph == "Phase 2":
            recruiting_status.append(rng.choice(["recruiting", "paused", "completed"], p=[0.60, 0.18, 0.22]))
        else:
            recruiting_status.append(rng.choice(["recruiting", "paused", "completed"], p=[0.48, 0.14, 0.38]))

    min_age = _sample_truncated_normal_int(rng, mean=30, sd=10, low=18, high=70, size=n)
    age_span = _sample_truncated_normal_int(rng, mean=26, sd=10, low=12, high=45, size=n)
    max_age = np.minimum(min_age + age_span, 85)

    excludes_smokers = rng.random(n) < np.where(indication == "respiratory", 0.58, 0.34)
    excludes_renal = rng.random(n) < np.where(np.isin(indication, ["cardiovascular", "diabetes"]), 0.54, 0.33)
    excludes_liver = rng.random(n) < np.where(indication == "cancer", 0.62, 0.31)

    max_comorbidity = np.where(
        phase == "Phase 1",
        rng.integers(0, 3, size=n),
        np.where(phase == "Phase 2", rng.integers(1, 4, size=n), rng.integers(2, 6, size=n)),
    ).astype(int)

    region = rng.choice(REGIONS, size=n, p=REGION_PROBS)

    slots_open = np.where(
        np.array(recruiting_status) == "recruiting",
        rng.integers(10, 201, size=n),
        0,
    )

    start_offsets = _clip_int(rng.uniform(90, 4 * 365, size=n), 90, 4 * 365)
    start_dates = [REFERENCE_DATE - timedelta(days=int(d)) for d in start_offsets]

    end_dates: list[date] = []
    for i in range(n):
        start = start_dates[i]
        status = recruiting_status[i]
        if status == "completed":
            duration = int(rng.uniform(180, 900))
            end = min(start + timedelta(days=duration), REFERENCE_DATE - timedelta(days=int(rng.uniform(5, 60))))
        elif status == "paused":
            duration = int(rng.uniform(120, 700))
            end = start + timedelta(days=duration)
            if end < REFERENCE_DATE - timedelta(days=20):
                end = REFERENCE_DATE + timedelta(days=int(rng.uniform(30, 180)))
        else:
            end = REFERENCE_DATE + timedelta(days=int(rng.uniform(120, 900)))

        if end <= start:
            end = start + timedelta(days=30)
        end_dates.append(end)

    trials = pd.DataFrame(
        {
            "trial_id": trial_ids,
            "indication": indication,
            "phase": phase,
            "recruiting_status": recruiting_status,
            "min_age": min_age.astype(int),
            "max_age": max_age.astype(int),
            "excludes_smokers": excludes_smokers,
            "excludes_renal": excludes_renal,
            "excludes_liver": excludes_liver,
            "max_comorbidity": max_comorbidity,
            "region": region,
            "slots_open": slots_open.astype(int),
            "start_date": pd.to_datetime(start_dates).date.astype(str),
            "end_date": pd.to_datetime(end_dates).date.astype(str),
        }
    )
    return trials


def _drug_candidates_for_condition(condition: str) -> list[DrugSpec]:
    candidates = [spec for spec in DRUG_CATALOG if condition in spec.indications]
    return candidates if candidates else list(DRUG_CATALOG)


def _dose_for_class(rng: np.random.Generator, drug_class: str) -> int:
    lo, hi = DOSE_RANGES_MG[drug_class]
    val = rng.lognormal(mean=np.log((lo + hi) / 2), sigma=0.34)
    return int(np.clip(np.rint(val), lo, hi))


def generate_drug_exposures(
    rng: np.random.Generator,
    patients: pd.DataFrame,
    n: int = EXPOSURE_COUNT,
) -> pd.DataFrame:
    patient_weights = (1.0 + patients["medication_count"].to_numpy() + 0.4 * patients["comorbidity_count"].to_numpy())
    patient_weights = patient_weights / patient_weights.sum()

    sampled_idx = rng.choice(patients.index.to_numpy(), size=n, p=patient_weights)
    sampled_patients = patients.loc[sampled_idx].reset_index(drop=True)

    exposure_ids = [f"EXP{idx:06d}" for idx in range(1, n + 1)]

    indication: list[str] = []
    drug_name: list[str] = []
    drug_class: list[str] = []
    dose_mg: list[int] = []
    start_dates: list[date] = []
    end_dates: list[date | None] = []
    active_flag: list[bool] = []

    for i, row in sampled_patients.iterrows():
        patient_condition = str(row["condition"])
        condition_for_exposure = patient_condition if rng.random() < 0.82 else rng.choice(CONDITIONS)
        candidates = _drug_candidates_for_condition(condition_for_exposure)

        spec = candidates[rng.integers(0, len(candidates))]
        start_ago_days = int(np.clip(rng.gamma(shape=2.4, scale=180), 7, 1200))
        start = REFERENCE_DATE - timedelta(days=start_ago_days)

        active_prob = np.clip(0.68 - 0.00022 * start_ago_days + (0.06 if patient_condition == "cardiovascular" else 0.0), 0.15, 0.88)
        is_active = bool(rng.random() < active_prob)

        if is_active:
            end = None
        else:
            duration_days = int(np.clip(rng.gamma(shape=2.2, scale=90), 14, 900))
            proposed_end = start + timedelta(days=duration_days)
            if proposed_end >= REFERENCE_DATE:
                proposed_end = REFERENCE_DATE - timedelta(days=int(rng.uniform(1, 30)))
            end = proposed_end

        indication.append(condition_for_exposure)
        drug_name.append(spec.drug_name)
        drug_class.append(spec.drug_class)
        dose_mg.append(_dose_for_class(rng, spec.drug_class))
        start_dates.append(start)
        end_dates.append(end)
        active_flag.append(is_active)

    exposures = pd.DataFrame(
        {
            "exposure_id": exposure_ids,
            "patient_id": sampled_patients["patient_id"].to_numpy(),
            "drug_name": drug_name,
            "drug_class": drug_class,
            "dose_mg": dose_mg,
            "start_date": pd.to_datetime(start_dates).date.astype(str),
            "end_date": [e.isoformat() if isinstance(e, date) else "" for e in end_dates],
            "active_flag": active_flag,
            "indication": indication,
        }
    )
    return exposures


def generate_adverse_events(
    rng: np.random.Generator,
    patients: pd.DataFrame,
    exposures: pd.DataFrame,
    n: int = EVENT_COUNT,
) -> pd.DataFrame:
    exposures_join = exposures.merge(
        patients[["patient_id", "medication_count", "comorbidity_count", "renal_impairment", "liver_impairment"]],
        on="patient_id",
        how="left",
    )

    base_class_risk = exposures_join["drug_class"].map(CLASS_BASE_RISK).fillna(0.15).to_numpy()
    meds = exposures_join["medication_count"].to_numpy(dtype=float)
    renal = exposures_join["renal_impairment"].to_numpy(dtype=bool).astype(float)
    liver = exposures_join["liver_impairment"].to_numpy(dtype=bool).astype(float)

    sampling_weight = 1.0 + base_class_risk * 5.0 + meds * 0.3 + renal * 0.8 + liver * 0.7
    sampling_weight = sampling_weight / sampling_weight.sum()

    sampled_exposure_idx = rng.choice(exposures_join.index.to_numpy(), size=n, p=sampling_weight)
    sampled = exposures_join.loc[sampled_exposure_idx].reset_index(drop=True)

    event_ids = [f"AE{idx:06d}" for idx in range(1, n + 1)]

    event_type: list[str] = []
    severity: list[str] = []
    serious_flag: list[bool] = []
    onset_date: list[str] = []
    resolved_flag: list[bool] = []
    related_to_drug: list[bool] = []

    for _, row in sampled.iterrows():
        dclass = str(row["drug_class"])
        types = EVENT_TYPES_BY_CLASS.get(dclass, ["headache", "nausea", "fatigue"])
        event_type.append(types[rng.integers(0, len(types))])

        base_risk = CLASS_BASE_RISK.get(dclass, 0.15)
        risk_adj = (
            base_risk
            + 0.02 * float(row["comorbidity_count"])
            + 0.08 * float(bool(row["renal_impairment"]))
            + 0.09 * float(bool(row["liver_impairment"]))
        )
        severe_p = np.clip(0.03 + risk_adj * 0.42, 0.04, 0.32)
        moderate_p = np.clip(0.32 + risk_adj * 0.25, 0.35, 0.66)
        mild_p = max(0.02, 1.0 - severe_p - moderate_p)

        sev = rng.choice(["mild", "moderate", "severe"], p=np.array([mild_p, moderate_p, severe_p]))
        severity.append(sev)

        serious_prob = 0.04 if sev == "mild" else 0.22 if sev == "moderate" else 0.72
        serious_prob = np.clip(serious_prob + 0.06 * float(bool(row["renal_impairment"])), 0.02, 0.93)
        serious_flag.append(bool(rng.random() < serious_prob))

        start = pd.to_datetime(row["start_date"]).date()
        end_raw = str(row["end_date"]).strip()
        if end_raw:
            end = pd.to_datetime(end_raw).date()
        else:
            end = REFERENCE_DATE
        if end <= start:
            end = start + timedelta(days=1)

        window = max(1, (end - start).days)
        onset_offset = int(rng.integers(1, window + 1))
        onset = start + timedelta(days=onset_offset)
        onset_date.append(onset.isoformat())

        resolve_prob = 0.86 if sev == "mild" else 0.67 if sev == "moderate" else 0.38
        if bool(row["active_flag"]):
            resolve_prob -= 0.1
        resolved_flag.append(bool(rng.random() < np.clip(resolve_prob, 0.12, 0.95)))

        related_prob = np.clip(0.46 + base_risk * 0.9, 0.3, 0.86)
        related_to_drug.append(bool(rng.random() < related_prob))

    adverse_events = pd.DataFrame(
        {
            "event_id": event_ids,
            "patient_id": sampled["patient_id"].to_numpy(),
            "drug_name": sampled["drug_name"].to_numpy(),
            "event_type": event_type,
            "severity": severity,
            "serious_flag": serious_flag,
            "onset_date": onset_date,
            "resolved_flag": resolved_flag,
            "related_to_drug": related_to_drug,
        }
    )
    return adverse_events


def run_sanity_checks(
    patients: pd.DataFrame,
    trials: pd.DataFrame,
    exposures: pd.DataFrame,
    events: pd.DataFrame,
) -> None:
    patient_ids = set(patients["patient_id"])

    exposure_fk_ok = exposures["patient_id"].isin(patient_ids).all()
    event_fk_ok = events["patient_id"].isin(patient_ids).all()

    recruiting_slots_ok = (
        trials.loc[trials["recruiting_status"] == "recruiting", "slots_open"] > 0
    ).all() and (trials.loc[trials["recruiting_status"] != "recruiting", "slots_open"] == 0).all()

    active_date_ok = exposures.apply(
        lambda row: (row["active_flag"] and row["end_date"] == "")
        or ((not row["active_flag"]) and row["end_date"] != ""),
        axis=1,
    ).all()

    exposure_min_start = exposures[["exposure_id", "start_date"]].copy()
    exposure_min_start["start_date"] = pd.to_datetime(exposure_min_start["start_date"])
    first_exposure = (
        exposures[["patient_id", "drug_name", "start_date"]]
        .assign(start_date=lambda d: pd.to_datetime(d["start_date"]))
        .groupby(["patient_id", "drug_name"], as_index=False)
        .agg(min_start=("start_date", "min"))
    )
    event_join = events.merge(first_exposure, on=["patient_id", "drug_name"], how="left")
    event_onset_ok = (pd.to_datetime(event_join["onset_date"]) >= event_join["min_start"]).all()

    events_per_patient = events.groupby("patient_id").size().rename("event_count")
    med_event_corr = (
        patients.set_index("patient_id")["medication_count"].to_frame().join(events_per_patient, how="left").fillna(0)
    )

    age_comorb_corr = np.corrcoef(patients["age"], patients["comorbidity_count"])[0, 1]
    comorb_meds_corr = np.corrcoef(patients["comorbidity_count"], patients["medication_count"])[0, 1]
    meds_events_corr = np.corrcoef(med_event_corr["medication_count"], med_event_corr["event_count"])[0, 1]

    print("\n=== DATASET ROW COUNTS ===")
    print(f"patients: {len(patients)}")
    print(f"trials: {len(trials)}")
    print(f"drug_exposures: {len(exposures)}")
    print(f"adverse_events: {len(events)}")

    print("\n=== PATIENT DISTRIBUTIONS ===")
    print("condition distribution:")
    print((patients["condition"].value_counts(normalize=True) * 100).round(1).astype(str) + "%")
    print("\nregion distribution:")
    print((patients["region"].value_counts(normalize=True) * 100).round(1).astype(str) + "%")
    print("\nsex distribution:")
    print((patients["sex"].value_counts(normalize=True) * 100).round(1).astype(str) + "%")

    print("\n=== TRIAL DISTRIBUTIONS ===")
    print("recruiting status:")
    print(trials["recruiting_status"].value_counts())
    print("phase distribution:")
    print(trials["phase"].value_counts())

    print("\n=== SAFETY DISTRIBUTIONS ===")
    print("event severity distribution:")
    print((events["severity"].value_counts(normalize=True) * 100).round(1).astype(str) + "%")
    print("serious flag rate:", round(events["serious_flag"].mean() * 100, 2), "%")

    print("\n=== SANITY CHECKS ===")
    print("exposure patient FK valid:", exposure_fk_ok)
    print("event patient FK valid:", event_fk_ok)
    print("trial slots_open vs recruiting_status consistent:", recruiting_slots_ok)
    print("exposure active_flag vs end_date consistent:", active_date_ok)
    print("event onset_date after exposure start_date:", event_onset_ok)

    print("\n=== CORRELATION CHECKS ===")
    print("age vs comorbidity_count:", round(float(age_comorb_corr), 3))
    print("comorbidity_count vs medication_count:", round(float(comorb_meds_corr), 3))
    print("medication_count vs event_count:", round(float(meds_events_corr), 3))



def generate_datasets(output_dir: Path, seed: int = SEED) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    patients = generate_patients(rng, PATIENT_COUNT)
    trials = generate_trials(rng, patients, TRIAL_COUNT)
    exposures = generate_drug_exposures(rng, patients, EXPOSURE_COUNT)
    events = generate_adverse_events(rng, patients, exposures, EVENT_COUNT)

    patients.to_csv(output_dir / "patients.csv", index=False)
    trials.to_csv(output_dir / "trials.csv", index=False)
    exposures.to_csv(output_dir / "drug_exposures.csv", index=False)
    events.to_csv(output_dir / "adverse_events.csv", index=False)

    print(f"\nGenerated datasets at: {output_dir.resolve()}")
    run_sanity_checks(patients, trials, exposures, events)



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic PHARMA-OS demo datasets"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/demo"),
        help="Output directory for generated CSV files",
    )
    parser.add_argument("--seed", type=int, default=SEED, help="Deterministic random seed")
    args = parser.parse_args()

    generate_datasets(output_dir=args.output_dir, seed=args.seed)


if __name__ == "__main__":
    main()
