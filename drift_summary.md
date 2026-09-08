# Synthèse de dérive — repères PSI

Repères conventionnels :
- PSI < 0.10 : signal faible
- 0.10 ≤ PSI ≤ 0.25 : à investiguer
- PSI > 0.25 : signal fort

| Feature | Type | Calcul | Interprétation |
|---|---|---|---|
| `loan_amnt` | numérique | PSI = 0.0035 ; KS p-value = 0.9891 | Signal faible. Distribution stable ; pas de dérive marquée. |
| `int_rate` | numérique | PSI = 0.4429 ; KS p-value ≈ 4.63e-65 | Signal fort. Déplacement net de distribution vers des taux plus élevés. |
| `installment` | numérique | PSI = 0.0147 ; KS p-value = 0.6626 | Signal faible. Différence marginale, pas d’indice de dérive fort. |
| `annual_inc` | numérique | PSI = 0.0666 ; KS p-value ≈ 2.28e-09 | Signal faible selon PSI, mais p-value KS très faible : différence statistique détectable malgré une amplitude modérée. |
| `dti` | numérique | PSI = 0.0114 ; KS p-value = 0.1104 | Signal faible. Pas de dérive forte selon le PSI. |
| `delinq_2yrs` | numérique | PSI = 0.0018 ; KS p-value = 0.8879 | Signal faible. Très stable. |
| `fico_range_low` | numérique | PSI = 0.0068 ; KS p-value = 0.4893 | Signal faible. Distribution proche entre référence et production. |
| `revol_util` | numérique | PSI = 0.1864 ; KS p-value ≈ 3.82e-20 | Signal à investiguer selon PSI, avec forte différence de distribution. La variable mérite un contrôle qualité, notamment à cause des NaN. |
| `term` | catégoriel | Chi² p-value = 0.3164 | Pas de signal de dérive nette sur la distribution des durées de prêt. |
| `grade` | catégoriel | Chi² p-value ≈ 3.65e-07 | Signal fort. Migration nette vers des grades plus risqués en production. |
| `emp_length` | catégoriel | Chi² p-value = 0.4916 | Signal faible. Distribution globale comparable. |
| `home_ownership` | catégoriel | Chi² p-value = 0.6314 | Signal faible. Pas de rupture claire. |
| `verification_status` | catégoriel | Chi² p-value = 0.5863 | Signal faible. Aucune dérive marquée. |
| `purpose` | catégoriel | Chi² p-value = 0.1993 | Signal faible. Pas de changement majeur des usages de crédit. |

## Conclusion
Les variables les plus critiques pour le diagnostic sont `int_rate`, `revol_util` et `grade` : elles affichent des signaux clairs de dérive et sont cohérentes avec une évolution du profil de risque des dossiers en production. Le portrait global est celui d’un data drift plausible, à surveiller notamment sur la calibration et la qualité des données.
