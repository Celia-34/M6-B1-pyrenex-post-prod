# Note de recommandation — Dérive `pyrenex_risk_v2`

**Pour :** Sophie Léger (Lead Data, Pyrenex)  **De :** FastIA — _Théo Célia_

## Constat (chiffré)
Sur les 3 derniers mois de production, 3 variables d'entrée sur 14 dérivent nettement par rapport au jeu de référence :
- `int_rate` : dérive forte (PSI = 0,44) — médiane 12,0 % → 15,1 % (p90 : 18,6 % → 21,9 %) ;
- `grade` : dérive forte (Chi² p ≈ 3,65e-07) — migration des dossiers du grade A/B vers B/C/D/E ;
- `revol_util` : à surveiller (PSI = 0,19) — médiane 50,5 % → 58,1 % (p90 : 76,7 % → 87,3 %), avec un taux de valeurs manquantes non négligeable à contrôler avant réentraînement.

Une dérive plus légère mais réelle est également identifiée sur `annual_inc` (PSI = 0,0666, KS p ≈ 2,3e-09). Ce PSI reste sous le repère conventionnel de 0,10, mais dépasse la variabilité interne du jeu de référence : 200 découpages aléatoires de `reference_set` en deux moitiés donnent un PSI moyen de 0,0241 (IC 95 % : [0,0082 ; 0,0521]), et aucun de ces 200 PSI ne dépasse 0,0521. Le PSI de 0,0666 mesuré entre référence et production sort donc de cette plage de bruit d'échantillonnage : il s'agit d'un signal de dérive faible mais réel, à surveiller sans déclencher d'action immédiate.

Les 10 autres variables restent stables (PSI < 0,02 ou p-value > 0,19). En parallèle, la fiabilité des scores se dégrade progressivement : l'écart entre probabilité prédite et taux réel de défaut (ECE) passe de 0,2403 à 0,3152 (+31 %) entre le début et la fin de la fenêtre de 3 mois, alors que le taux réel de défaut reste stable (~20 %). Le modèle devient donc de plus en plus sur-confiant.

## Diagnostic
**Data drift avéré, concept drift non avéré.** La triangulation sur 4 axes converge :
1. **Features** : déplacement net de 3 variables (`int_rate`, `revol_util`, `grade`), avec un signal plus léger sur `annual_inc`, cohérent avec un changement de population de clients (profils plus risqués, crédits plus chers).
2. **AUC** (pouvoir discriminant) : stable, 0,7419 → 0,7459 (Δ = +0,004) entre semaines 1-4 et semaines 9-12. Le modèle continue de trier correctement les bons/mauvais dossiers.
3. **Calibration** : dégradation continue de l'ECE (+0,0749), signe que les probabilités prédites se décalent du taux réel — la conséquence typique d'un déplacement des features, pas d'une rupture de la relation entre variables et risque.
4. **Temporalité** : la dégradation de calibration suit la même trajectoire progressive que le déplacement des features, sans rupture brutale de l'AUC — ce qui exclut un artefact ponctuel.

Un concept drift aurait nécessité une chute de l'AUC et/ou un changement de la relation entre les variables et le risque réel ; ce signal est absent ici.

## Recommandation
1. **Confirmer côté métier** : vérifier auprès des équipes qu'il n'y a pas eu de changement des règles d'octroi, de la politique de risque, ou de la définition des variables (`int_rate`, `revol_util`) ou du défaut (`loan_status`) sur la période — condition nécessaire pour écarter tout à fait un concept drift.
2. **Contrôle qualité préalable** sur `revol_util` (taux de manquants) avant tout réentraînement, pour ne pas amplifier artificiellement le signal de dérive.
3. **Réentraîner le modèle** sur des données récentes afin de recalibrer les probabilités prédites au nouveau profil de clientèle. L'architecture et les features actuelles restent pertinentes (AUC stable) : il s'agit d'un recalage, pas d'une refonte.
4. **Évaluer le gain** du modèle réentraîné par rapport à l'actuel (AUC, ECE) avant bascule en production, pour s'assurer que le réentraînement apporte une amélioration réelle.

## Coût estimé
- Réentraînement : effort modéré (pipeline existant, pas de changement de features), estimé à 3-4 jours-hommes (1 jour extraction/contrôle qualité des données récentes, 1-2 jours ré-entraînement et validation AUC/ECE, 1 jour vérification métier et documentation).
- Risque prod : faible si le réentraînement est validé par comparaison AUC/ECE avant bascule (pas de refonte d'architecture).
- Fenêtre d'intervention : pas d'urgence à corriger dans l'instant (AUC intact), mais à traiter avant que l'ECE ne continue de se dégrader et n'impacte les décisions basées sur les seuils de score.

## Décision suggérée
> Le modèle reste fiable pour trier les dossiers (AUC stable), mais ses scores de probabilité sont de moins en moins fidèles au risque réel : nous recommandons un réentraînement sur données récentes (urgence moyenne), précédé d'une vérification métier et d'un contrôle qualité sur `revol_util`.
