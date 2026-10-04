"""
Generate SYNTHETIC datasets for the IR / hepatology workflow audit notebook.

All values are random numbers drawn from made-up distributions. No patient-level
or procedure-level record was copied, sampled or used to fit them; the
distribution parameters are rough, invented values chosen only so the notebook
runs and the charts look plausible. Results from these files illustrate how the
notebook works and say nothing about any real service.

Usage:
    python generate_synthetic_data.py
Output:
    data/Retrospective_Data.xlsx   (19 columns, as the notebook expects)
    data/Prospective_Data.xlsx     (27 columns, as the notebook expects)
"""
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

SEED = 7
rng = np.random.default_rng(SEED)
N_RETRO, N_PROS = 80, 200
START = datetime(2025, 1, 6)

PROCEDURES = ["Therapeutic Paracentesis", "Therapeutic Thoracentesis"]
INDICATIONS = {"Therapeutic Paracentesis": ["Ascites"],
               "Therapeutic Thoracentesis": ["Left Pleural Effusion", "Right Pleural Effusion"]}


def hhmm(minutes):
    minutes = int(minutes)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def common(n):
    dates = [START + timedelta(days=int(d)) for d in np.sort(rng.integers(0, 90, size=n))]
    proc = rng.choice(PROCEDURES, size=n)
    ind = [rng.choice(INDICATIONS[p]) for p in proc]
    loc = rng.choice(["Ward", "Daycare"], size=n, p=[0.7, 0.3])
    coag = rng.choice(["yes", "no"], size=n, p=[0.55, 0.45])
    return dates, proc, ind, loc, coag


# ---------------------------------------------------------------- retrospective (19 columns)
dates, proc, ind, loc, coag = common(N_RETRO)
rows = []
for i in range(N_RETRO):
    c = coag[i] == "yes"
    strat = int(rng.choice([1, 2])) if c else "no"
    n_prod = float(rng.choice([0, 1, 2, 3], p=[0.3, 0.2, 0.3, 0.2])) if c else 0.0
    ffp = float(rng.integers(0, 3)) if n_prod else 0.0
    cryo = float(rng.integers(0, 2)) if n_prod else 0.0
    plt_ = float(max(n_prod - ffp - cryo, 0)) if n_prod else 0.0
    rows.append([
        i + 1, dates[i], loc[i], proc[i], ind[i],
        f"{dates[i]:%d/%m/%Y} {hhmm(rng.integers(480, 900))}",
        coag[i], strat,
        float(rng.choice([0, 1, 2])), n_prod, ffp, cryo, plt_,
        float(rng.choice([1, 2, 3, 4])) if c and rng.random() < 0.3 else np.nan,
        float(rng.choice([1, 2, 3, 4])) if (not c) and rng.random() < 0.3 else np.nan,
        float(rng.choice([1, 2, 3, 4], p=[0.6, 0.25, 0.1, 0.05])) if rng.random() < 0.55 else np.nan,
        float(rng.choice([1, 2, 3], p=[0.5, 0.35, 0.15])) if rng.random() < 0.55 else np.nan,
        float(rng.choice([0, 1, 2], p=[0.85, 0.1, 0.05])),
        np.nan,
    ])
retro_cols = ["S.No", "Date", "Daycare/Ward", "Procedure", "Indication", "Date and Time of decision",
              "Coagulopathy", "Transfusion based on (1=ROTEM, 2=RANDOM)", "ROTEM result (0=NO, 1=YES, 2=ROTEM normal)",
              "No. of Products", "FFP", "CRYO", "Platelet",
              "Timing of informing IR team after coagulopathy correction (1=0-30 min, 2=30-60, 3=60-120, 4=>120)",
              "Timing of informing IR team without coagulopathy correction (1-4)",
              "Timing of shifting to procedure after IR gave permission (1=0-2 h, 2=2-4 h, 3=4-6 h, 4=>6 h)",
              "Time interval between shifting from ward and receiving back to ward (1=0-2 h, 2=2-4 h, 3=>4 h)",
              "Post procedure complications (0=None)", "Other complications"]
retro = pd.DataFrame(rows, columns=retro_cols)

# ---------------------------------------------------------------- prospective (27 columns)
dates, proc, ind, loc, coag = common(N_PROS)
rows = []
for i in range(N_PROS):
    c = coag[i] == "yes"
    review = int(rng.integers(480, 900))
    t = review
    na = "NO"
    if c:
        strat = int(rng.choice([1, 2]))
        if strat == 1:  # ROTEM-guided pathway
            rotem_req = t + int(rng.integers(5, 30)); rotem_rep = rotem_req + int(rng.integers(25, 90))
            t = rotem_rep
            rotem_req_s, rotem_rep_s, rotem_res = hhmm(rotem_req), hhmm(rotem_rep), int(rng.choice([1, 2]))
        else:
            rotem_req_s = rotem_rep_s = na; rotem_res = na
        n_prod = int(rng.choice([0, 1, 2, 3], p=[0.2, 0.2, 0.35, 0.25]))
        if n_prod:
            order = t + int(rng.integers(5, 25)); recv = order + int(rng.integers(35, 105))
            tstart = recv + int(rng.integers(5, 40)); tend = tstart + int(rng.integers(20, 85))
            t = tend
            ffp = int(rng.integers(0, 3)); cryo = int(rng.integers(0, 2)); pl = max(n_prod - ffp - cryo, 0)
            prod = [hhmm(order), hhmm(recv), hhmm(tstart), hhmm(tend)]
        else:
            ffp = cryo = pl = 0; prod = [na] * 4
        inform_with = hhmm(t + int(rng.integers(3, 30))); inform_without = na
        t = int(inform_with[:2]) * 60 + int(inform_with[3:])
    else:
        strat = na
        rotem_req_s = rotem_rep_s = na; rotem_res = na
        n_prod = 0; ffp = cryo = pl = 0; prod = [na] * 4
        inform_with = na
        t = t + int(rng.integers(5, 40)); inform_without = hhmm(t)
    shift = t + int(rng.integers(5, 40))
    start = shift + int(rng.choice([8, 12, 20, 25, 35, 55, 80], p=[0.2, 0.25, 0.2, 0.15, 0.1, 0.07, 0.03]))
    to_recovery = start + int(rng.integers(10, 30))
    to_ward = to_recovery + int(rng.integers(15, 60))
    rows.append([i + 1, dates[i], loc[i], proc[i], ind[i], hhmm(review),
                 coag[i], strat, rotem_req_s, rotem_rep_s, rotem_res,
                 n_prod, ffp, cryo, pl] + prod +
                [inform_with, inform_without, hhmm(shift), hhmm(start), hhmm(to_recovery), hhmm(to_ward),
                 int(rng.choice([0, 1, 2], p=[0.9, 0.07, 0.03])), na])
pros_cols = ["S.No", "Date", "Daycare/Ward", "Procedure", "Indication", "Hepatology Review Time", "Coagulopathy",
             "Transfusion based on (1=ROTEM-guided, 2=Clinician-directed)", "ROTEM Request Time", "ROTEM Report Time",
             "ROTEM report (0=NO, 1=YES, 2=ROTEM normal)", "No. of Products", "FFP", "CRYO", "Platelet",
             "Blood Product Ordering Time", "Blood Product Receiving Time", "Blood Product Transfusion Start time",
             "Blood Product Transfusion End Time", "Time of informing IR team (with coagulopathy correction)",
             "Time of informing IR team (without coagulopathy correction)",
             "Time of shifting to procedure after IR gave permission", "Procedure start time",
             "Shift to recovery time", "Shifted to ward time", "Post procedure complications (0=None)",
             "Other complications"]
pros = pd.DataFrame(rows, columns=pros_cols)
assert retro.shape[1] == 19 and pros.shape[1] == 27

os.makedirs("data", exist_ok=True)
retro.to_excel(os.path.join("data", "Retrospective_Data.xlsx"), index=False)
pros.to_excel(os.path.join("data", "Prospective_Data.xlsx"), index=False)
print(f"Wrote data/Retrospective_Data.xlsx ({N_RETRO} rows) and data/Prospective_Data.xlsx ({N_PROS} rows), seed {SEED}.")
