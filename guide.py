"""
Contenu pédagogique de la page Guide débutant.

Tout le texte est ici, séparé de l'interface, pour être facile à corriger
sans toucher au code. Rédigé pour quelqu'un qui n'a jamais acheté et ne
connaît aucun sigle.
"""

INTRO = """
Tu veux acheter ta résidence principale et tu gagnes un salaire normal.
Bonne nouvelle : en France, il existe des dispositifs qui font baisser le
prix de 20 à 50 % et des prêts à 0 % ou 1 % qui remplacent une partie de
ton crédit bancaire. Mauvaise nouvelle : personne ne les explique
simplement, et la plupart des gens éligibles ne le savent même pas.

Cette page t'explique tout comme si tu partais de zéro : les dispositifs
qui baissent le prix, les prêts qui baissent la mensualité, lequel choisir
selon ta situation, le parcours étape par étape, et les pièges.
"""

IDEE_CLE = """
Il y a DEUX familles à ne pas confondre, et elles se cumulent :

1. Les dispositifs qui baissent LE PRIX du logement (BRS, PSLA, vente HLM,
   prix maîtrisé). Tu en choisis UN.
2. Les prêts aidés qui baissent LA MENSUALITÉ (PTZ, prêt Action Logement,
   PAS). Tu peux les empiler TOUS ensemble.

Exemple réel : un appartement de 60 m² à Caluire vendu 121 510 euros en
BRS alors que le marché local est à 190 000 euros, financé par un PTZ de
60 000 euros à 0 %, un prêt Action Logement de 30 000 euros à 1 % et un
petit prêt bancaire. Résultat : environ 360 euros par mois les dix
premières années. Moins qu'une chambre en foyer.
"""

DISPOSITIFS = [
    {
        "nom": "BRS - Bail réel solidaire",
        "resume": "Tu achètes les murs, pas le terrain. Le moins cher à l'entrée.",
        "prix": "20 à 40 % sous le marché",
        "comment": (
            "Un organisme (l'OFS) garde le terrain pour toujours et te le "
            "loue via une petite redevance mensuelle, environ 1,70 euro par "
            "m². Comme tu ne paies pas le terrain, le prix chute. Tu es "
            "propriétaire des murs, tu peux transmettre à tes enfants."
        ),
        "pour_qui": (
            "Ceux qui veulent la mensualité la plus basse possible, tout de "
            "suite, et qui comptent rester longtemps dans le logement."
        ),
        "le_hic": (
            "Le prix de REVENTE est plafonné à vie : tu ne toucheras jamais "
            "la plus-value si le quartier monte. La redevance se paie toute "
            "la vie, même crédit remboursé. Location interdite, toujours. "
            "Et il ne faut pas déjà posséder un logement qui pourrait te "
            "servir de résidence principale."
        ),
        "ou": "Programmes neufs des promoteurs, et de plus en plus de logements existants vendus par les bailleurs sociaux (les meilleures affaires).",
    },
    {
        "nom": "PSLA - Location-accession",
        "resume": "Tu loues d'abord LE logement que tu vas acheter, puis tu l'achètes. Le meilleur pour le patrimoine.",
        "prix": "TVA réduite à 5,5 % et prix bloqué dès le départ",
        "comment": (
            "Phase 1 : tu emménages comme locataire-accédant, et une partie "
            "de ton loyer est mise de côté pour devenir ton apport. Phase 2 : "
            "tu lèves l'option et tu achètes au prix fixé au départ, moins "
            "ce que tu as déjà accumulé. Un seul déménagement."
        ),
        "pour_qui": (
            "Ceux qui veulent construire un vrai patrimoine : à l'arrivée tu "
            "possèdes le logement ET le terrain, tu revends au prix du "
            "marché, et tu peux même le louer après 10 ans."
        ),
        "le_hic": (
            "C'est du neuf, donc 18 à 30 mois d'attente avant la livraison. "
            "Très peu de programmes, et quasiment invisibles sur internet : "
            "ça se trouve en appelant les opérateurs, pas en cherchant. "
            "Si tu pars avant 10 ans, tu rembourses une partie de la TVA "
            "économisée, dégressive de 10 % par an."
        ),
        "ou": "Coopératives HLM et bailleurs sociaux, en direct. Bonus énorme : exonération de taxe foncière pendant 15 ans.",
    },
    {
        "nom": "Vente HLM",
        "resume": "Un bailleur social vend un logement de son parc, en pleine propriété.",
        "prix": "20 à 30 % sous le marché, frais de notaire très réduits",
        "comment": (
            "Les bailleurs sociaux vendent chaque année une partie de leurs "
            "logements. Tu achètes en pleine propriété classique : pas de "
            "redevance, revente libre après quelques années, prix décoté."
        ),
        "pour_qui": "Ceux qui veulent de l'existant, disponible tout de suite, en pleine propriété.",
        "le_hic": (
            "Un ordre de priorité légal : les locataires du parc social "
            "passent AVANT toi. Si tu es locataire du privé, tu es servi en "
            "dernier. Le PTZ y est limité à 20 % du prix."
        ),
        "ou": "Sites des bailleurs (rubrique devenir propriétaire), bienveo.fr, et parfois Leboncoin via des agences mandatées.",
    },
    {
        "nom": "Accession à prix maîtrisé",
        "resume": "Du neuf vendu sous le marché grâce à un accord promoteur-commune.",
        "prix": "10 à 20 % sous le marché du neuf",
        "comment": (
            "La commune cède le terrain moins cher au promoteur, qui "
            "s'engage en échange sur un prix plafonné et des conditions "
            "d'éligibilité."
        ),
        "pour_qui": "Ceux qui veulent du neuf en pleine propriété sans passer par le BRS.",
        "le_hic": "Clause anti-spéculative de quelques années (interdiction de revendre ou obligation de reverser la décote), et offre dépendante de ta commune.",
        "ou": "Portail logement abordable de ta métropole, promoteurs.",
    },
]

PRETS = [
    {
        "nom": "PTZ - Prêt à taux zéro",
        "resume": "L'État te prête jusqu'à 50 % du prix, sans aucun intérêt.",
        "montant": "Jusqu'à 50 % du prix en appartement neuf, BRS ou PSLA. 20 % en vente HLM.",
        "conditions": (
            "Ne pas avoir été propriétaire de ta résidence principale depuis "
            "2 ans, et rester sous des plafonds de revenus (73 500 euros de "
            "revenu fiscal pour un couple en zone A : la plupart des salariés "
            "passent). Prolongé jusqu'à fin 2027."
        ),
        "le_plus": (
            "Le différé : pendant 2 à 10 ans selon tes revenus, tu ne "
            "rembourses RIEN sur ce prêt. Ta mensualité de départ est donc "
            "très basse. Attention, elle remonte après, et c'est CE montant "
            "que la banque vérifie."
        ),
    },
    {
        "nom": "Prêt Action Logement",
        "resume": "30 000 euros à 1 % si tu es salarié du privé.",
        "montant": "30 000 euros (40 000 en vente HLM), sur 25 ans max.",
        "conditions": (
            "Salarié d'une entreprise privée non agricole d'au moins 10 "
            "salariés, et pas propriétaire de ta résidence principale depuis "
            "10 ans. C'est un droit lié à ton contrat de travail : le "
            "demander ne coûte rien à ton employeur."
        ),
        "le_plus": (
            "30 000 euros pour environ 113 euros par mois. Le même montant "
            "emprunté à la banque coûterait environ 150 euros. Dépose la "
            "demande tôt : l'instruction prend 4 à 8 semaines."
        ),
    },
    {
        "nom": "PAS - Prêt d'accession sociale",
        "resume": "Le prêt bancaire principal, version encadrée par l'État.",
        "montant": "Le reste du financement.",
        "conditions": "Mêmes plafonds de revenus que le PTZ, banque conventionnée.",
        "le_plus": "Taux plafonné et frais de garantie réduits. Demande-le explicitement à ta banque ou ton courtier, on ne te le proposera pas spontanément.",
    },
]

CHOISIR = """
La question qui tranche entre BRS et PSLA n'est pas le prix, c'est :
comptes-tu vivre dans ce logement plus de 15 ans ?

- OUI, c'est pour la vie -> BRS. Le plafonnement de la revente ne te
  coûtera jamais rien puisque tu ne revends pas, et tu profites de la
  mensualité la plus basse du marché.
- NON, c'est une étape (enfant, mutation, plus grand un jour) -> PSLA.
  Tu paies un peu plus cher à l'entrée mais tu ressors avec un vrai bien
  revendable au prix du marché, voire louable après 10 ans.
- Tu veux de l'existant tout de suite -> vente HLM ou BRS sur parc
  existant, en acceptant l'ordre de priorité.
- Tes revenus dépassent les plafonds sociaux -> il te reste le PTZ sur du
  neuf libre (jusqu'à 73 500 euros de RFR pour un couple en zone A).
"""

PARCOURS = [
    ("1. Récupère ton avis d'imposition N-2",
     "Pour un achat en 2026, c'est l'avis 2025 sur les revenus 2024. La "
     "ligne qui compte : revenu fiscal de référence. Tout se calcule dessus."),
    ("2. Vérifie ta zone",
     "Tape ta commune dans le simulateur de zonage de service-public.fr. "
     "Lyon et sa métropole sont en zone A. La zone fixe tous tes plafonds."),
    ("3. Teste ton éligibilité dans l'onglet Tableau de bord",
     "Renseigne ton profil dans la barre de gauche : l'app te dit si tu "
     "passes les plafonds et dans quelle tranche PTZ tu tombes."),
    ("4. Inscris-toi partout, avant même d'avoir un bien",
     "Bailleurs sociaux de ta métropole (rubrique devenir propriétaire), "
     "BoRiS (boris.beta.gouv.fr) pour le BRS, coopératives HLM pour le "
     "PSLA, et l'ADIL de ton département pour un conseil gratuit et neutre. "
     "Les meilleures affaires partent par les listes de candidats, pas par "
     "les annonces."),
    ("5. Crée tes alertes",
     "Onglet Générateur de liens : il fabrique les recherches Leboncoin, "
     "SeLoger et Bienici avec les bons mots-clés (solidaire, brs, psla, "
     "accession). Enregistre chacune en alerte avec notification."),
    ("6. Un bien sort ? Évalue-le en 5 minutes",
     "Onglet Évaluateur d'adresse : décote réelle par rapport aux ventes du "
     "quartier, DPE, risques, écoles, vie de quartier. Puis onglet "
     "Simulateur de montage : ta mensualité exacte en deux phases, et le "
     "verdict finançable ou non."),
    ("7. Monte le dossier",
     "Simulation bancaire par un courtier (souvent exigée dans la "
     "candidature), dépôt Action Logement dès le compromis ou la "
     "réservation, et validation finale par l'ADIL. Compte 4 à 8 semaines "
     "pour Action Logement : ne le découvre pas au dernier moment."),
]

PIEGES = [
    ("La phase 2, le piège numéro un",
     "Grâce au différé du PTZ, ta mensualité de départ est très basse. Mais "
     "quand le différé se termine, elle saute. Les banques testent CE point "
     "haut, pas la mensualité de départ. Un projet qui passe en phase 1 "
     "mais pas en phase 2 sera refusé. L'app affiche toujours les deux."),
    ("Trop d'apport tue le PTZ",
     "Règle contre-intuitive : le PTZ ne peut pas dépasser le total de tes "
     "autres prêts (sauf à quotité 50 %, où il peut les dépasser de 25 %). "
     "Si tu mets un gros apport, tes autres prêts rétrécissent, et ton PTZ "
     "avec. Il existe un apport optimal : en général, juste de quoi couvrir "
     "les frais de notaire plus un matelas. L'app t'alerte si ton apport "
     "bride ton PTZ."),
    ("Un crédit en différé ne disparaît pas",
     "Prêt étudiant ou autre crédit en différé : tu paies peut-être 35 "
     "euros par mois aujourd'hui, mais la banque compte la mensualité "
     "FUTURE, celle d'après le différé. C'est elle qu'il faut saisir dans "
     "le profil, sinon tous les calculs mentent."),
    ("La redevance BRS est une charge, pas un détail",
     "70 à 120 euros par mois selon la surface, à vie, indexée chaque "
     "année, comptée par la banque dans ton taux d'endettement, et qui ne "
     "construit aucun capital."),
    ("En BRS, tu ne captes jamais la plus-value",
     "Prix de revente plafonné pour toujours. Si le quartier prend 40 %, "
     "c'est le prochain acheteur qui en profite, pas toi. C'est le prix de "
     "la décote à l'achat. Assume-le en connaissance de cause."),
    ("Résidence principale = 8 mois par an minimum",
     "Tous ces dispositifs exigent que tu habites le logement. Location "
     "interdite en BRS pour toujours, et en PSLA pendant 10 ans sous peine "
     "de reverser la TVA (sauf mutation à plus de 70 km, chômage d'un an, "
     "séparation)."),
    ("L'ordre de priorité des ventes de logements sociaux",
     "Sur la vente HLM et le BRS existant, les locataires du parc social "
     "passent devant tout le monde. Candidate quand même : les dossiers "
     "prioritaires incomplets sont fréquents, et ton dossier resservira."),
    ("Le prix affiché n'est pas toujours le bon",
     "En BRS, c'est l'organisme foncier qui fixe le prix maximum autorisé, "
     "pas l'agence. Et les frais de notaire affichés par les portails sont "
     "souvent calculés au taux de l'ancien (7 à 8 %) alors qu'en BRS, PSLA "
     "et neuf ils tombent à 2 ou 3 %. Fais-toi confirmer les deux par écrit."),
]

QUI_APPELER = """
- L'ADIL de ton département : conseil juridique et financier GRATUIT et
  neutre, par des juristes. C'est le premier appel à passer, avant le
  courtier et avant les vendeurs. Trouve la tienne sur anil.org.
- Les bailleurs sociaux de ta métropole : rubrique « devenir propriétaire »
  de leurs sites, et demande à être inscrit sur leur liste de candidats.
- BoRiS (boris.beta.gouv.fr) : la plateforme publique du BRS, test
  d'éligibilité et carte des logements.
- Un courtier : pour la simulation bancaire exigée dans les dossiers de
  candidature, et pour aller chercher la dérogation des 35 % réservée en
  priorité aux primo-accédants.
- Action Logement (actionlogement.fr) : dépôt en ligne dès que tu as une
  réservation ou un compromis.
"""
