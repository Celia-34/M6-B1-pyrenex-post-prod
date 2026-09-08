"""Calibration en exploitation (SQUELETTE À COMPLÉTER).

Le modèle annonce une proba : observe-t-on le bon taux réel ?
Mini-cours : `03_Calibration_modele_essentiel.md`. ⚠️ Calibration =
**exploitation** (≠ seuils de rejet de conception, vus en M7-M8).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def reliability_table(proba: pd.Series, true_label: pd.Series, n_bins: int = 10) -> pd.DataFrame:
    """Table du reliability diagram : bin / n / confiance_moyenne / taux_observe / ecart."""
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bins = pd.cut(proba, bins=bin_edges, include_lowest=True)

    df = pd.DataFrame({"proba": proba, "true_label": true_label, "bin": bins})
    grouped = df.groupby("bin", observed=False)

    table = grouped.agg(
        n=("proba", "size"),
        confiance_moyenne=("proba", "mean"),
        taux_observe=("true_label", "mean"),
    ).reset_index()
    table = table[table["n"] > 0].reset_index(drop=True)
    table["ecart"] = (table["confiance_moyenne"] - table["taux_observe"]).abs()

    return table


def expected_calibration_error(proba: pd.Series, true_label: pd.Series, n_bins: int = 10) -> float:
    """ECE = Σ (n_bin/N) * |confiance - taux observé|. 0 = parfaitement calibré."""
    table = reliability_table(proba, true_label, n_bins=n_bins)
    n_total = table["n"].sum()
    return float((table["n"] / n_total * table["ecart"]).sum())
