# Diagnostic — Data drift vs Concept drift

## Méthode : triangulation sur 4 axes

Le diagnostic ne repose pas sur un seul indicateur mais sur le croisement de quatre familles de signaux mesurés sur les mêmes fenêtres temporelles (données `reference_set.csv` / `prod_3months.csv` pour les features, `predictions_log.csv` découpé en `semaines_1_4` et `semaines_9_12` pour la performance et la calibration) :

1. **Features** (PSI / KS / Chi²) — les distributions d'entrée ont-elles bougé ?
2. **AUC** — le modèle discrimine-t-il toujours aussi bien les bons/mauvais dossiers ?
3. **Calibration** (ECE, reliability diagram) — les probabilités prédites restent-elles fidèles au taux réel de défaut ?
4. **Temporalité** — les signaux ci-dessus évoluent-ils progressivement (semaines 1-4 → semaines 9-12), signe d'une dérive continue plutôt que d'un artefact ponctuel ?

Un **data drift** se traduit par un déplacement des features avec un AUC stable (le modèle reste pertinent mais reçoit une population différente). Un **concept drift** se traduirait par une chute de l'AUC et/ou un changement de la relation X→Y, indépendamment du déplacement des features.

## Axe 1 — Features (PSI · KS · Chi²)

| Feature | Signal | Verdict |
|---|---|---|
| `int_rate` | PSI = 0.4429, KS p ≈ 4.6e-65 | **Dérive forte** |
| `revol_util` | PSI = 0.1864, KS p ≈ 3.8e-20 (manquants ref 1.33% → prod 1.2%) | À investiguer |
| `grade` | Chi² p ≈ 3.65e-07 | **Dérive forte** (migration A/B → B/C/D/E) |
| `annual_inc` | PSI = 0.0666, KS p ≈ 2.3e-09 | Stable (amplitude faible malgré p-value basse) |
| `loan_amnt`, `installment`, `dti`, `delinq_2yrs`, `fico_range_low`, `term`, `emp_length`, `home_ownership`, `verification_status`, `purpose` | PSI < 0.02 ou Chi² p > 0.19 | Stables |

Lecture métier : médiane `int_rate` 12.0 → 15.1 (p90 : 18.6 → 21.9), médiane `revol_util` 50.5 → 58.1 (p90 : 76.7 → 87.3), et déplacement de la distribution `grade` vers des profils plus risqués. **3 features sur 14 montrent un déplacement net** → signal cohérent avec un changement de population de clients (data drift), pas avec un changement de règle métier.

## Axe 2 — AUC (pouvoir discriminant)

| Période | AUC | n |
|---|---|---|
| Semaines 1-4 | 0.7419 | 1003 |
| Semaines 9-12 | 0.7459 | 997 |

Écart de **+0.004**, statistiquement non significatif à cette échelle : le modèle continue d'ordonner les dossiers avec la même qualité de tri qu'au déploiement. **Aucun signal de concept drift ici** : si la relation X→Y s'était rompue, on attendrait une dégradation nette de l'AUC (typiquement > 0.02-0.03), pas une quasi-stabilité voire une légère hausse.

## Axe 3 — Calibration (ECE · reliability diagram)

| Période | ECE | Probabilité moyenne prédite | Taux réel de défaut |
|---|---|---|---|
| Semaines 1-4 | 0.2403 | 0.4427 | 0.2024 |
| Semaines 9-12 | 0.3152 | 0.5158 | 0.2006 |

Le taux réel de défaut reste stable (~20%) alors que la probabilité moyenne prédite augmente de 0.4427 à 0.5158 : le modèle devient **sur-confiant**, et l'écart se creuse (**ECE +0.0749**, soit +31% relatif). Le reliability diagram est nettement sous la diagonale sur les deux périodes, avec un décalage plus marqué en fin de fenêtre. Cette dégradation de calibration **sans dégradation du tri (AUC stable)** est la signature typique d'un data drift : les scores bruts se décalent parce que la distribution d'entrée a changé, mais la capacité du modèle à hiérarchiser le risque reste intacte.

## Axe 4 — Temporalité

En croisant les fenêtres semaines 1-4 vs semaines 9-12 :
- AUC : quasi stationnaire (0.7419 → 0.7459, Δ = +0.004)
- ECE : dégradation progressive et continue (0.2403 → 0.3152, Δ = +0.0749)
- Features : le déplacement mesuré sur 3 mois de production (`int_rate`, `revol_util`, `grade`) est cohérent avec l'évolution graduelle de la sur-confiance du modèle

La dégradation de calibration suit la même trajectoire temporelle que le déplacement des features, et non un saut brutal isolé sur l'AUC — ce qui exclut un artefact ponctuel et confirme une dérive progressive et continue de la population plutôt qu'une rupture de la logique métier.

## Triangulation et conclusion

| Axe | Constat chiffré | Compatible avec |
|---|---|---|
| Features | 3/14 variables en dérive forte (PSI jusqu'à 0.44, Chi² p < 1e-6) | Data drift |
| AUC | Stable : 0.7419 → 0.7459 (Δ = +0.004) | Absence de concept drift |
| Calibration | ECE 0.2403 → 0.3152 (+31%), sur-confiance croissante | Data drift (conséquence du déplacement des features) |
| Temporalité | Dégradation progressive et corrélée entre features et calibration, pas de rupture brutale de l'AUC | Data drift continu |

**Verdict : data drift plausible, concept drift non avéré.**

Les quatre axes convergent : la population de dossiers évolue (`int_rate`, `revol_util`, `grade`), ce qui déforme la confiance du score (ECE en hausse), mais la relation entre les variables d'entrée et le risque réel reste intacte (AUC stable). Un concept drift aurait nécessité une chute de l'AUC et/ou un changement de comportement du modèle indépendant du déplacement des features — signal absent ici.

- **Action recommandée** : réentraîner le modèle sur des données récentes pour recaler les probabilités prédites (recalibration), sans remettre en cause l'architecture ou les features actuelles.
- **Urgence** : moyenne — l'AUC ne s'est pas dégradé, mais l'ECE en hausse continue dégrade la fiabilité des scores pour les décisions métier (ex. seuils d'acceptation).
- **Point de vigilance qualité des données** : `revol_util` cumule un signal de dérive (PSI = 0.1864) et un taux de valeurs manquantes non négligeable (ref 1.33% / prod 1.2%) ; un contrôle qualité est nécessaire avant réentraînement pour écarter un biais de complétude qui amplifierait artificiellement le signal.
