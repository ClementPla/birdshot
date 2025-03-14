import numpy as np
import pandas as pd


def extract_scoto_rod_score(gt, pred):
    gt_patients = gt.keys()
    pred_patients = pred.keys()
    patients = set(gt_patients).intersection(pred_patients)
    results = {"amp pred": [], "time pred": [], "amp gt": [], "time gt": []}

    for patient in patients:
        df_gt = gt[patient]
        df_pred = pred[patient]
        for date in df_pred.columns:
            year = date.year
            if year not in df_gt.columns:
                print(f"Year {year} not in gt of patient {patient}")
                continue
            for laterality in ["OD", "OS"]:
                for technique in ["amp", "time"]:
                    val_gt = df_gt.loc[
                        ("Scotopic (rod function)", "b-wave", laterality, technique)
                    ].squeeze()
                    val_pred = df_pred.loc[
                        ("Scotopic (rod function)", "b-wave", laterality, technique)
                    ].squeeze()

                    val_pred_d = val_pred[date]
                    val_gt_y = val_gt[year]

                    if np.isnan(val_pred_d) or np.isnan(val_gt_y):
                        continue
                    results[f"{technique} pred"].append(val_pred_d)
                    results[f"{technique} gt"].append(val_gt_y)
    return pd.DataFrame(results)


def extract_scoto_cone_rod_score(gt, pred):
    gt_patients = gt.keys()
    pred_patients = pred.keys()
    patients = set(gt_patients).intersection(pred_patients)
    cols = ["amp b-wave", "amp a-wave", "time b-wave", "time a-wave"]
    results = dict()
    for c in ["gt", "pred"]:
        for col in cols:
            results[f"{col} {c}"] = []

    for patient in patients:
        df_gt = gt[patient]
        df_pred = pred[patient]
        for date in df_pred.columns:
            year = date.year
            if year not in df_gt.columns:
                print(f"Year {year} not in gt of patient {patient}")
                continue
            for wave in ["b-wave", "a-wave"]:
                for laterality in ["OD", "OS"]:
                    for technique in ["amp", "time"]:
                        val_gt = df_gt.loc[
                            (
                                "Scotopic (rod-cone function)",
                                wave,
                                laterality,
                                technique,
                            )
                        ].squeeze()
                        val_pred = df_pred.loc[
                            (
                                "Scotopic (rod-cone function)",
                                wave,
                                laterality,
                                technique,
                            )
                        ].squeeze()
                        val_pred_d = val_pred[date]
                        val_gt_y = val_gt[year]

                        if not isinstance(val_pred_d, (int, float)):
                            continue

                        if not isinstance(val_gt_y, (int, float)):
                            continue

                        if np.isnan(val_pred_d) or np.isnan(val_gt_y):
                            continue

                        results[f"{technique} {wave} pred"].append(val_pred_d)
                        results[f"{technique} {wave} gt"].append(val_gt_y)

    return results


def extract_f30_score(gt, pred):
    gt_patients = gt.keys()
    pred_patients = pred.keys()
    patients = set(gt_patients).intersection(pred_patients)
    results = {"F30 amp pred": [], "F30 amp gt": []}

    for patient in patients:
        df_gt = gt[patient]
        df_pred = pred[patient]
        for date in df_pred.columns:
            year = date.year
            if year not in df_gt.columns:
                print(f"Year {year} not in gt of patient {patient}")
                continue
            for laterality in ["OD", "OS"]:
                try:
                    val_gt = df_gt.loc[
                        (
                            "Photopic Flicker30HZ (cone function)",
                            "b-wave",
                            laterality,
                        )
                    ].squeeze()
                    val_pred = df_pred.loc[
                        (
                            "Photopic Flicker30HZ (cone function)",
                            "b-wave",
                            laterality,
                        )
                    ].squeeze()
                except KeyError:
                    continue

                val_pred_d = val_pred[date]
                val_gt_y = val_gt[year]
                indices = ["amp" in c for c in val_pred_d.index]
                val_pred_d = val_pred_d[indices]
                indices = ["amp" in c for c in val_gt_y.index]
                val_gt_y = val_gt_y[indices]
                val_pred_d = val_pred_d.mean()
                try:
                    val_gt_y = val_gt_y.mean()
                except TypeError:
                    continue
                if np.isnan(val_pred_d) or np.isnan(val_gt_y):
                    continue
                results[f"F30 amp pred"].append(val_pred_d)
                results[f"F30 amp gt"].append(val_gt_y)
    return pd.DataFrame(results)
