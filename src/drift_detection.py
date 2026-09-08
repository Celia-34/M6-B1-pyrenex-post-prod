"""Détection de dérive — PSI, KS, Chi² (SQUELETTE À COMPLÉTER).

Trois méthodes complémentaires. Mini-cours : `01_PSI_KS_Chi2_essentiel.md`.
N'inventez pas vos métriques : PSI (formule ci-dessous), KS et Chi² sont dans
scipy.stats.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ks_2samp

PSI_STABLE = 0.10
PSI_DRIFT = 0.25


def population_stability_index(reference: pd.Series, current: pd.Series, n_bins: int = 10) -> float:
    """PSI entre référence et courant.

    PSI = Σ (p_cur - p_ref) * ln(p_cur / p_ref), bornes des bins = quantiles de
    la référence. ⚠️ pensez au lissage anti-zéro (sinon ln(0) / division par 0).
    """
    epsilon = 1e-4
    quantiles = np.linspace(0, 1, n_bins + 1)
    bin_edges = np.unique(reference.quantile(quantiles).to_numpy())
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    ref_counts, _ = np.histogram(reference, bins=bin_edges)
    cur_counts, _ = np.histogram(current, bins=bin_edges)

    ref_perc = ref_counts / ref_counts.sum() + epsilon
    cur_perc = cur_counts / cur_counts.sum() + epsilon

    return float(np.sum((cur_perc - ref_perc) * np.log(cur_perc / ref_perc)))


def psi_verdict(psi: float) -> str:
    """Traduit un PSI en verdict (stable / à investiguer / dérive)."""
    if psi < PSI_STABLE:
        return "stable"
    if psi <= PSI_DRIFT:
        return "à investiguer"
    return "dérive"


def ks_pvalue(reference: pd.Series, current: pd.Series) -> float:
    """p-value du test de Kolmogorov-Smirnov (2 échantillons)."""
    return float(ks_2samp(reference, current).pvalue)


def chi2_pvalue(reference: pd.Series, current: pd.Series) -> float:
    """p-value du Chi² sur les fréquences de modalités (aligner les modalités)."""
    categories = sorted(set(reference.unique()) | set(current.unique()))
    # table de contingence réindexée sur l'union des modalités, avec lissage +1
    ref_counts = reference.value_counts().reindex(categories, fill_value=0) + 1
    cur_counts = current.value_counts().reindex(categories, fill_value=0) + 1
    table = np.array([ref_counts.to_numpy(), cur_counts.to_numpy()])

    return float(chi2_contingency(table)[1])


def drift_report(
    reference: pd.DataFrame, current: pd.DataFrame,
    numeric_cols: list[str], categorical_cols: list[str],
) -> pd.DataFrame:
    """Tableau de synthèse : feature / type / psi / ks_pvalue / chi2_pvalue / verdict."""
    rows = []
    for col in numeric_cols:
        psi = population_stability_index(reference[col], current[col])
        rows.append({
            "feature": col,
            "type": "numeric",
            "psi": psi,
            "ks_pvalue": ks_pvalue(reference[col], current[col]),
            "chi2_pvalue": np.nan,
            "verdict": psi_verdict(psi),
        })

    for col in categorical_cols:
        p_value = chi2_pvalue(reference[col], current[col])
        rows.append({
            "feature": col,
            "type": "categorical",
            "psi": np.nan,
            "ks_pvalue": np.nan,
            "chi2_pvalue": p_value,
            "verdict": "dérive" if p_value < 0.05 else "stable",
        })

    severity_rank = {"dérive": 0, "à investiguer": 1, "stable": 2}
    report = pd.DataFrame(rows)
    report["_severity"] = report["verdict"].map(severity_rank)
    report = report.sort_values("_severity").drop(columns="_severity").reset_index(drop=True)

    return report
