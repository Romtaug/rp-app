"""
Contenu pedagogique de la page Guide debutant.

Tout le texte est ici, separe de l'interface, pour etre facile a corriger
sans toucher au code. Redige pour quelqu'un qui n'a jamais achete et ne
connait aucun sigle.
"""

INTRO = """
Tu veux acheter ta residence principale et tu gagnes un salaire normal.
Bonne nouvelle : en France, il existe des dispositifs qui font baisser le
prix de 20 a 50 % et des prets a 0 % ou 1 % qui remplacent une partie de
ton credit bancaire. Mauvaise nouvelle : personne ne les explique
simplement, et la plupart des gens eligibles ne le savent meme pas.

Cette page t'explique tout comme si tu partais de zero : les dispositifs
qui baissent le prix, les prets qui baissent la mensualite, lequel choisir
selon ta situation, le parcours etape par etape, et les pieges.
"""

IDEE_CLE = """
Il y a DEUX familles a ne pas confondre, et elles se cumulent :

1. Les dispositifs qui baissent LE PRIX du logement (BRS, PSLA, vente HLM,
   prix maitrise). Tu en choisis UN.
2. Les prets aides qui baissent LA MENSUALITE (PTZ, pret Action Logement,
   PAS). Tu peux les empiler TOUS ensemble.

Exemple reel : un appartement de 60 m2 a Caluire vendu 121 510 euros en
BRS alors que le marche local est a 190 000 euros, finance par un PTZ de
60 000 euros a 0 %, un pret Action Logement de 30 000 euros a 1 % et un
petit pret bancaire. Resultat : environ 360 euros par mois les dix
premieres annees. Moins qu'une chambre en foyer.
"""

DISPOSITIFS = [
    {
        "nom": "BRS - Bail reel solidaire",
        "resume": "Tu achetes les murs, pas le terrain. Le moins cher a l'entree.",
        "prix": "20 a 40 % sous le marche",
        "comment": (
            "Un organisme (l'OFS) garde le terrain pour toujours et te le "
            "loue via une petite redevance mensuelle, environ 1,70 euro par "
            "m2. Comme tu ne paies pas le terrain, le prix chute. Tu es "
            "proprietaire des murs, tu peux transmettre a tes enfants."
        ),
        "pour_qui": (
            "Ceux qui veulent la mensualite la plus basse possible, tout de "
            "suite, et qui comptent rester longtemps dans le logement."
        ),
        "le_hic": (
            "Le prix de REVENTE est plafonne a vie : tu ne toucheras jamais "
            "la plus-value si le quartier monte. La redevance se paie toute "
            "la vie, meme credit rembourse. Location interdite, toujours. "
            "Et il ne faut pas deja posseder un logement qui pourrait te "
            "servir de residence principale."
        ),
        "ou": "Programmes neufs des promoteurs, et de plus en plus de logements existants vendus par les bailleurs sociaux (les meilleures affaires).",
    },
    {
        "nom": "PSLA - Location-accession",
        "resume": "Tu loues d'abord LE logement que tu vas acheter, puis tu l'achetes. Le meilleur pour le patrimoine.",
        "prix": "TVA reduite a 5,5 % et prix bloque des le depart",
        "comment": (
            "Phase 1 : tu emmenages comme locataire-accedant, et une partie "
            "de ton loyer est mise de cote pour devenir ton apport. Phase 2 : "
            "tu leves l'option et tu achetes au prix fixe au depart, moins "
            "ce que tu as deja accumule. Un seul demenagement."
        ),
        "pour_qui": (
            "Ceux qui veulent construire un vrai patrimoine : a l'arrivee tu "
            "possedes le logement ET le terrain, tu revends au prix du "
            "marche, et tu peux meme le louer apres 10 ans."
        ),
        "le_hic": (
            "C'est du neuf, donc 18 a 30 mois d'attente avant la livraison. "
            "Tres peu de programmes, et quasiment invisibles sur internet : "
            "ca se trouve en appelant les operateurs, pas en cherchant. "
            "Si tu pars avant 10 ans, tu rembourses une partie de la TVA "
            "economisee, degressive de 10 % par an."
        ),
        "ou": "Cooperatives HLM et bailleurs sociaux, en direct. Bonus enorme : exoneration de taxe fonciere pendant 15 ans.",
    },
    {
        "nom": "Vente HLM",
        "resume": "Un bailleur social vend un logement de son parc, en pleine propriete.",
        "prix": "20 a 30 % sous le marche, frais de notaire tres reduits",
        "comment": (
            "Les bailleurs sociaux vendent chaque annee une partie de leurs "
            "logements. Tu achetes en pleine propriete classique : pas de "
            "redevance, revente libre apres quelques annees, prix decote."
        ),
        "pour_qui": "Ceux qui veulent de l'existant, disponible tout de suite, en pleine propriete.",
        "le_hic": (
            "Un ordre de priorite legal : les locataires du parc social "
            "passent AVANT toi. Si tu es locataire du prive, tu es servi en "
            "dernier. Le PTZ y est limite a 20 % du prix."
        ),
        "ou": "Sites des bailleurs (rubrique devenir proprietaire), bienveo.fr, et parfois Leboncoin via des agences mandatees.",
    },
    {
        "nom": "Accession a prix maitrise",
        "resume": "Du neuf vendu sous le marche grace a un accord promoteur-commune.",
        "prix": "10 a 20 % sous le marche du neuf",
        "comment": (
            "La commune cede le terrain moins cher au promoteur, qui s'engage "
            "en echange sur un prix plafonne et des conditions d'eligibilite."
        ),
        "pour_qui": "Ceux qui veulent du neuf en pleine propriete sans passer par le BRS.",
        "le_hic": "Clause anti-speculative de quelques annees (interdiction de revendre ou obligation de reverser la decote), et offre dependante de ta commune.",
        "ou": "Portail logement abordable de ta metropole, promoteurs.",
    },
]

PRETS = [
    {
        "nom": "PTZ - Pret a taux zero",
        "resume": "L'Etat te prete jusqu'a 50 % du prix, sans aucun interet.",
        "montant": "Jusqu'a 50 % du prix en appartement neuf, BRS ou PSLA. 20 % en vente HLM.",
        "conditions": (
            "Ne pas avoir ete proprietaire de ta residence principale depuis "
            "2 ans, et rester sous des plafonds de revenus (73 500 euros de "
            "revenu fiscal pour un couple en zone A : la plupart des salaries "
            "passent). Prolonge jusqu'a fin 2027."
        ),
        "le_plus": (
            "Le differe : pendant 2 a 10 ans selon tes revenus, tu ne "
            "rembourses RIEN sur ce pret. Ta mensualite de depart est donc "
            "tres basse. Attention, elle remonte apres, et c'est CE montant "
            "que la banque verifie."
        ),
    },
    {
        "nom": "Pret Action Logement",
        "resume": "30 000 euros a 1 % si tu es salarie du prive.",
        "montant": "30 000 euros (40 000 en vente HLM), sur 25 ans max.",
        "conditions": (
            "Salarie d'une entreprise privee non agricole d'au moins 10 "
            "salaries, et pas proprietaire de ta residence principale depuis "
            "10 ans. C'est un droit lie a ton contrat de travail : le "
            "demander ne coute rien a ton employeur."
        ),
        "le_plus": (
            "30 000 euros pour environ 113 euros par mois. Le meme montant "
            "emprunte a la banque couterait environ 150 euros. Depose la "
            "demande tot : l'instruction prend 4 a 8 semaines."
        ),
    },
    {
        "nom": "PAS - Pret d'accession sociale",
        "resume": "Le pret bancaire principal, version encadree par l'Etat.",
        "montant": "Le reste du financement.",
        "conditions": "Memes plafonds de revenus que le PTZ, banque conventionnee.",
        "le_plus": "Taux plafonne et frais de garantie reduits. Demande-le explicitement a ta banque ou ton courtier, on ne te le proposera pas spontanement.",
    },
]

CHOISIR = """
La question qui tranche entre BRS et PSLA n'est pas le prix, c'est :
comptes-tu vivre dans ce logement plus de 15 ans ?

- OUI, c'est pour la vie -> BRS. Le plafonnement de la revente ne te
  coutera jamais rien puisque tu ne revends pas, et tu profites de la
  mensualite la plus basse du marche.
- NON, c'est une etape (enfant, mutation, plus grand un jour) -> PSLA.
  Tu paies un peu plus cher a l'entree mais tu ressors avec un vrai bien
  revendable au prix du marche, voire louable apres 10 ans.
- Tu veux de l'existant tout de suite -> vente HLM ou BRS sur parc
  existant, en acceptant l'ordre de priorite.
- Tes revenus depassent les plafonds sociaux -> il te reste le PTZ sur du
  neuf libre (jusqu'a 73 500 euros de RFR pour un couple en zone A).
"""

PARCOURS = [
    ("1. Recupere ton avis d'imposition N-2",
     "Pour un achat en 2026, c'est l'avis 2025 sur les revenus 2024. La "
     "ligne qui compte : revenu fiscal de reference. Tout se calcule dessus."),
    ("2. Verifie ta zone",
     "Tape ta commune dans le simulateur de zonage de service-public.fr. "
     "Lyon et sa metropole sont en zone A. La zone fixe tous tes plafonds."),
    ("3. Teste ton eligibilite dans l'onglet Tableau de bord",
     "Renseigne ton profil dans la barre de gauche : l'app te dit si tu "
     "passes les plafonds et dans quelle tranche PTZ tu tombes."),
    ("4. Inscris-toi partout, avant meme d'avoir un bien",
     "Bailleurs sociaux de ta metropole (rubrique devenir proprietaire), "
     "BoRiS (boris.beta.gouv.fr) pour le BRS, cooperatives HLM pour le "
     "PSLA, et l'ADIL de ton departement pour un conseil gratuit et neutre. "
     "Les meilleures affaires partent par les listes de candidats, pas par "
     "les annonces."),
    ("5. Cree tes alertes",
     "Onglet Generateur de liens : il fabrique les recherches Leboncoin, "
     "SeLoger et Bienici avec les bons mots-cles (solidaire, brs, psla, "
     "accession). Enregistre chacune en alerte avec notification."),
    ("6. Un bien sort ? Evalue-le en 5 minutes",
     "Onglet Evaluateur d'adresse : decote reelle par rapport aux ventes du "
     "quartier, DPE, risques. Puis onglet Simulateur de montage : ta "
     "mensualite exacte en deux phases, et le verdict finançable ou non."),
    ("7. Monte le dossier",
     "Simulation bancaire par un courtier (souvent exigee dans la "
     "candidature), depot Action Logement des le compromis ou la "
     "reservation, et validation finale par l'ADIL. Compte 4 a 8 semaines "
     "pour Action Logement : ne le decouvre pas au dernier moment."),
]

PIEGES = [
    ("La phase 2, le piege numero un",
     "Grace au differe du PTZ, ta mensualite de depart est tres basse. Mais "
     "quand le differe se termine, elle saute. Les banques testent CE point "
     "haut, pas la mensualite de depart. Un projet qui passe en phase 1 "
     "mais pas en phase 2 sera refuse. L'app affiche toujours les deux."),
    ("Trop d'apport tue le PTZ",
     "Regle contre-intuitive : le PTZ ne peut pas depasser le total de tes "
     "autres prets (sauf a quotite 50 %, ou il peut les depasser de 25 %). "
     "Si tu mets un gros apport, tes autres prets retrecissent, et ton PTZ "
     "avec. Il existe un apport optimal : en general, juste de quoi couvrir "
     "les frais de notaire plus un matelas. L'app t'alerte si ton apport "
     "bride ton PTZ."),
    ("Un credit en differe ne disparait pas",
     "Pret etudiant ou autre credit en differe : tu paies peut-etre 35 "
     "euros par mois aujourd'hui, mais la banque compte la mensualite "
     "FUTURE, celle d'apres le differe. C'est elle qu'il faut saisir dans "
     "le profil, sinon tous les calculs mentent."),
    ("La redevance BRS est une charge, pas un detail",
     "70 a 120 euros par mois selon la surface, a vie, indexee chaque "
     "annee, comptee par la banque dans ton taux d'endettement, et qui ne "
     "construit aucun capital."),
    ("En BRS, tu ne captes jamais la plus-value",
     "Prix de revente plafonne pour toujours. Si le quartier prend 40 %, "
     "c'est le prochain acheteur qui en profite, pas toi. C'est le prix de "
     "la decote a l'achat. Assume-le en connaissance de cause."),
    ("Residence principale = 8 mois par an minimum",
     "Tous ces dispositifs exigent que tu habites le logement. Location "
     "interdite en BRS pour toujours, et en PSLA pendant 10 ans sous peine "
     "de reverser la TVA (sauf mutation a plus de 70 km, chomage d'un an, "
     "separation)."),
    ("L'ordre de priorite des ventes de logements sociaux",
     "Sur la vente HLM et le BRS existant, les locataires du parc social "
     "passent devant tout le monde. Candidate quand meme : les dossiers "
     "prioritaires incomplets sont frequents, et ton dossier resservira."),
    ("Le prix affiche n'est pas toujours le bon",
     "En BRS, c'est l'organisme foncier qui fixe le prix maximum autorise, "
     "pas l'agence. Et les frais de notaire affiches par les portails sont "
     "souvent calcules au taux de l'ancien (7 a 8 %) alors qu'en BRS, PSLA "
     "et neuf ils tombent a 2 ou 3 %. Fais-toi confirmer les deux par ecrit."),
]

QUI_APPELER = """
- L'ADIL de ton departement : conseil juridique et financier GRATUIT et
  neutre, par des juristes. C'est le premier appel a passer, avant le
  courtier et avant les vendeurs. Trouve la tienne sur anil.org.
- Les bailleurs sociaux de ta metropole : rubrique "devenir proprietaire"
  de leurs sites, et demande a etre inscrit sur leur liste de candidats.
- BoRiS (boris.beta.gouv.fr) : la plateforme publique du BRS, test
  d'eligibilite et carte des logements.
- Un courtier : pour la simulation bancaire exigee dans les dossiers de
  candidature, et pour aller chercher la derogation des 35 % reservee en
  priorite aux primo-accedants.
- Action Logement (actionlogement.fr) : depot en ligne des que tu as une
  reservation ou un compromis.
"""
