"""Logique de recommandation de remédiation (SQUELETTE À COMPLÉTER).

La remédiation doit être **proportionnée** au diagnostic : réentraîner coûte
cher, on ne le propose que quand ça vaut le coup. Mini-cours :
`02_Data_drift_vs_concept_drift_essentiel.md` (matrice features × AUC).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DriftDiagnosis:
    """Synthèse du diagnostic pour décider de la remédiation."""

    n_features_drift: int  # nb de features en "dérive" (PSI > 0.25)
    auc_stable: bool  # le pouvoir discriminant tient-il ?
    calibration_degraded: bool  # la confiance a-t-elle dérivé ?
    f1_drop: float  # baisse de F1 macro (early → late)


def diagnose_drift_type(d: DriftDiagnosis) -> str:
    """Oriente vers "data drift" / "concept drift" / "mixte".

    ⚠️ Heuristique d'orientation, pas une preuve : elle formalise la matrice
    du mini-cours 02 (features × AUC) pour produire une hypothèse principale.
    Le verdict final se construit en croisant features, AUC, calibration et
    temporalité — et doit énoncer ce qui manquerait pour trancher.
    """
    if d.n_features_drift > 0 and d.auc_stable:
        return "data drift"
    if d.n_features_drift == 0 and not d.auc_stable:
        return "concept drift"
    return "mixte"


def recommend(d: DriftDiagnosis) -> dict[str, str]:
    """Recommande une action proportionnée au diagnostic.

    Returns:
        dict avec les clés : action / justification / urgence / drift_type.
    """
    drift_type = diagnose_drift_type(d)

    if drift_type == "concept drift":
        action = "réentraîner en urgence"
        justification = (
            "la relation entre les features et la cible semble avoir changé "
            "(AUC dégradée alors que les features restent stables) : le modèle risque d'être mal calibré sur le risque réel"
        )
        urgence = "haute"
    elif drift_type == "data drift":
        if d.calibration_degraded:
            action = "réentraîner sur données récentes"
            justification = (
                "les features dérivent et la calibration s'est dégradée : recaler le modèle sur la distribution actuelle"
            )
            urgence = "moyenne"
        else:
            action = "surveiller"
            justification = (
                "les features dérivent mais l'AUC et la calibration restent stables : pas d'impact démontré sur la performance"
            )
            urgence = "basse"
    else:
        action = "ajuster (recalibrer et investiguer)"
        justification = (
            "les signaux ne convergent pas clairement vers un seul type de dérive : "
            "investiguer la cause avant d'engager un réentraînement coûteux"
        )
        urgence = "moyenne"

    return {
        "action": action,
        "justification": justification,
        "urgence": urgence,
        "drift_type": drift_type,
    }
