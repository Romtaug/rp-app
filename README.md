# Recherche de logement en accession aidée

Application Streamlit personnelle. Elle répond à trois questions : à quoi ai-je droit, ce bien est-il une bonne affaire, et où trouver les biens.

Couverture : France entière. Aucune donnée lourde n'est stockée, tout est interrogé en direct par API, donc il n'y a pas de limite de volume ni de périmètre.

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déploiement privé sur Streamlit Community Cloud

1. Pousse le dépôt en **privé** sur GitHub
2. Sur share.streamlit.io, déploie depuis ce dépôt privé
3. Dans les réglages de l'app, section Sharing, passe l'app en privé et n'invite que ton adresse mail
4. Rien d'autre à configurer : aucune des API utilisées ne demande de clé

## Les cinq pages

| Page | Ce qu'elle fait |
|---|---|
| Guide débutant | Les dispositifs expliqués de zéro : fiches BRS/PSLA/vente HLM/prix maîtrisé, les 3 prêts, lequel choisir, le parcours en 7 étapes, les 8 pièges, qui appeler |
| Tableau de bord | Ta capacité d'emprunt, tes plafonds, ta tranche PTZ, et un glossaire complet |
| Simulateur de montage | Le plan de financement empilé et les deux phases de mensualité, avec verdict |
| Évaluateur d'adresse | Décote contre les ventes réelles, DPE, risques, zonage, pour une adresse donnée |
| Générateur de liens | Les URL de recherche à enregistrer en alertes sur les portails |
| Diagnostic des sources | Teste chaque API et te dit laquelle est cassée |

## Les sources utilisées

| Source | Ce qu'elle apporte | Clé requise |
|---|---|---|
| Base Adresse Nationale | Géocodage, code INSEE. Pivot de toutes les jointures | Non |
| DVF via api.cquest.org | Ventes réelles autour d'un point, pour calculer la décote | Non |
| DPE ADEME | Classe énergie et consommation à l'adresse | Non |
| Géorisques | Inondation, argile, radon, pollution des sols | Non |
| API Carto GPU (IGN) | Zonage du plan local d'urbanisme, servitudes | Non |
| data.grandlyon | Programmes en bail réel solidaire de la Métropole | Non |

## Deux choses que tu dois savoir

**État de la vérification (31/07/2026).** Les barèmes de `data/baremes.json` ont été confrontés aux sources publiques : différés PTZ 10/8/2/0 ans et durées 25/22/15/10 (décret n° 2025-299), quotités 50/40/40/20 en collectif et 30/20/20/10 en individuel, 20 % fixe en vente HLM, plafonds d'opération revalorisés (zone A, 2 personnes : 225 000 €), plafonds PSLA/BRS de l'arrêté du 24 février 2026 (zones A bis/A/B1 : 38 844 € pour 1 personne, 58 057 € pour 2), Action Logement 30 000 € à 1 % sur 25 ans (40 000 € en vente HLM). Restent des estimations signalées dans le JSON : les plafonds PSLA pour 3 et 5 personnes, et le coefficient familial au-delà de 4 occupants.

**Le géocodage utilise la Géoplateforme IGN** (`data.geopf.fr/geocodage`) : l'ancienne api-adresse.data.gouv.fr a été décommissionnée fin janvier 2026. **Le DVF interroge d'abord l'API ouverte du Cerema** (apidf, endpoints dvf_opendata) puis l'API communautaire cquest en repli. **Géorisques** passe par le rapport de risques complet aux coordonnées, avec l'inventaire GASPAR en repli, le tout en v1 sans jeton. Les endpoints n'ont pas pu être appelés depuis mon environnement de construction : la page Diagnostic des sources reste ton premier réflexe au premier lancement.

## Les deux automatisations

**La veille** (`.github/workflows/veille.yml`) tourne chaque matin à 6h, compare les programmes disponibles avec l'état de la veille stocké dans `etat/etat.json`, et n'envoie un mail que s'il y a du nouveau, avec un tableau déjà chiffré : prix au m², mensualité en phase 2, verdict finançable ou non.

**Le healthcheck** (`.github/workflows/healthcheck.yml`) tourne chaque lundi à 7h. Il appelle les six API de l'app et vérifie l'âge des barèmes (alerte au-delà de 330 jours). En cas de panne, le run passe au rouge et **GitHub t'envoie nativement un mail d'échec, sans aucune configuration**. Si les secrets Brevo sont présents, un mail détaillé nommant la source tombée est envoyé en plus. Silence total quand tout va bien.

Secrets GitHub optionnels pour les mails Brevo : `BREVO_API_KEY`, `MAIL_DEST`, `MAIL_EXP`. Pour la veille, active aussi Settings > Actions > General > Workflow permissions > Read and write.

## Vérification finale (31/07/2026)

L'application a été exécutée réellement page par page via le framework de test officiel de Streamlit : les 6 pages se rendent sans exception, le simulateur est stable sur les 6 dispositifs, et un profil extrême (8 occupants, zone C, 120 000 € de RFR) ne provoque aucune erreur. Le healthcheck et la veille ont été testés de bout en bout sur des réponses simulées : détection de panne, codes de sortie, diff des programmes, contenu des mails, alerte barèmes périmés. La logique financière passe 9 tests contre le barème réglementaire. L'API dépréciée `use_container_width` a été migrée. Ce qui reste non testable hors ligne : les appels réels aux 6 API publiques, couverts dès le premier lundi par le healthcheck, et immédiatement par la page Diagnostic des sources.

## L'ancienne section veille

<!-- 

Le workflow `.github/workflows/veille.yml` tourne chaque matin à 6h, compare les programmes disponibles avec l'état de la veille stocké dans `etat/etat.json`, et n'envoie un mail que s'il y a du nouveau. Le mail contient un tableau déjà chiffré : prix au m², mensualité en phase 2, verdict finançable ou non.

Secrets GitHub à créer : `BREVO_API_KEY`, `MAIL_DEST`, `MAIL_EXP`.

Pour désactiver, supprime le bloc `schedule` du workflow. -->

## Ce que le code fait de non évident

**La règle du PTZ plafonné.** Le montant du prêt à taux zéro ne peut pas dépasser le total des autres prêts de plus de deux ans. Conséquence contre-intuitive : mettre trop d'apport réduit ton PTZ. L'application le détecte et t'avertit. Il existe donc un apport optimal, ni zéro ni maximum.

**Les deux phases de mensualité.** Tous les simulateurs affichent une mensualité moyenne. Celle qui compte est la phase 2, après la fin du différé du PTZ, parce que c'est le point le plus haut de l'échéancier et c'est celui que la banque teste. Un projet finançable en phase 1 mais pas en phase 2 sera refusé.

**Les crédits en différé.** Dans le champ des mensualités en cours, il faut saisir la charge future d'amortissement, pas celle payée aujourd'hui. Un prêt étudiant en différé à 35 euros par mois qui passera à 700 euros doit être saisi à 700.

## Limites assumées

Trois bases décisives sont réservées aux collectivités et à leurs prestataires, et resteront inaccessibles : les fichiers fonciers MAJIC qui contiennent l'identité des propriétaires, LOVAC détaillé qui liste les logements vacants depuis plus de deux ans, et DV3F qui type les mutations. C'est ce que les outils professionnels du foncier facturent.

Le PSLA n'est référencé dans aucun jeu de données ouvert. Il se trouve en demandant aux opérateurs, pas en cherchant.

## Avertissement

Cet outil produit des estimations. Il ne remplace ni un courtier, ni un notaire, ni l'ADIL, qui eux engagent leur responsabilité.
