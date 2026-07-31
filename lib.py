"""
Bibliotheque unique de l'application. Version 2, corrigee apres verification
des sources le 31/07/2026.

Corrections majeures par rapport a la v1 :
  - Geocodage : api-adresse.data.gouv.fr est DECOMMISSIONNEE depuis fin
    janvier 2026. Bascule sur data.geopf.fr/geocodage (Geoplateforme IGN),
    iso-fonctionnelle, limite 50 req/s par IP.
  - DVF : ajout de l'API ouverte du Cerema (apidf, endpoints dvf_opendata)
    en source principale, l'API communautaire cquest devenant le repli.
  - Georisques : rapport de risques complet par coordonnees en premier,
    inventaire GASPAR par commune en repli. Les API v1 restent sans jeton.
  - PTZ : differes corriges (10/8/2/0 ans), durees totales 25/22/15/10,
    plafonds d'operation revalorises, quotite fixe 20% en vente HLM,
    grille individuelle 30/20/20/10, et exception a la regle de plafonnement
    quand la quotite atteint 50% (le PTZ peut alors depasser les autres
    prets de 25%).
  - PTZ : le pret est desormais correctement propose sur le neuf libre,
    independamment des plafonds PSLA qui ne gouvernent que BRS/PSLA/HLM.
"""

import json
import math
import os
from urllib.parse import quote_plus, urlencode

import requests

RACINE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 15
UA = {"User-Agent": "recherche-logement-perso/2.0"}


# ----------------------------------------------------------------------
# 1. GLOSSAIRE
# ----------------------------------------------------------------------

GLOSSAIRE = {
    "rfr": (
        "Revenu fiscal de reference. Ce n'est ni ton salaire brut ni ton net : "
        "c'est le montant calcule par le fisc, ecrit sur ton avis d'imposition, "
        "cadre 'Vos references'. Les dispositifs utilisent l'avis N-2 : pour un "
        "dossier en 2026, c'est l'avis 2025 sur les revenus 2024."
    ),
    "zone": (
        "Zonage ABC. La France est decoupee en 5 zones selon la tension du "
        "marche : A bis (Paris), A (Lyon, Nice, Geneve frontalier), B1 (grandes "
        "villes), B2, C. Tous tes plafonds en dependent. Lyon et sa metropole "
        "sont en zone A."
    ),
    "occupants": (
        "Nombre de personnes qui vont HABITER le logement, pas le nombre "
        "d'acheteurs. Tu peux acheter seul et declarer deux occupants. Plus il "
        "y a d'occupants, plus les plafonds montent et plus le PTZ est genereux, "
        "meme si la personne n'a aucun revenu."
    ),
    "ptz": (
        "Pret a taux zero. Un pret sans interets finance par l'Etat, reserve "
        "aux primo-accedants (pas proprietaires de leur residence principale "
        "depuis 2 ans). Prolonge jusqu'au 31 decembre 2027. Jusqu'a 50 % du "
        "prix en collectif neuf, BRS et PSLA."
    ),
    "quotite": (
        "Part du prix que le PTZ peut financer. Elle depend de ta tranche de "
        "revenus et du type de bien : 50/40/40/20 % en appartement neuf, BRS "
        "et PSLA ; 30/20/20/10 % en maison individuelle neuve ; 20 % fixe en "
        "vente HLM."
    ),
    "differe": (
        "Periode pendant laquelle tu ne rembourses RIEN sur le PTZ : 10 ans en "
        "tranche 1, 8 ans en tranche 2, 2 ans en tranche 3, aucun differe en "
        "tranche 4. Ta mensualite saute a la fin du differe, et c'est ce point "
        "haut que la banque teste."
    ),
    "tranche": (
        "Categorie de revenus qui fixe ta quotite et ton differe. Calcul : le "
        "plus eleve entre ton revenu fiscal N-2 et le prix de l'operation "
        "divise par 9, le tout divise par un coefficient familial (1 pour 1 "
        "personne, 1,4 pour 2, 1,7 pour 3, 2 pour 4). Tranche 1 = revenus les "
        "plus modestes = meilleures conditions."
    ),
    "action_logement": (
        "Pret complementaire a 1 % fixe, reserve aux salaries du prive dont "
        "l'entreprise compte au moins 10 salaries, primo-accedants ou non "
        "proprietaires depuis 10 ans. Jusqu'a 30 000 euros (40 000 en vente "
        "HLM), 25 ans maximum, plafonne a 40 % du cout de l'operation sauf en "
        "BRS et vente HLM. Environ 113 euros par mois pour 30 000 euros."
    ),
    "pas": (
        "Pret d'accession sociale. Un pret immobilier classique mais "
        "conventionne avec l'Etat : taux plafonne, frais de garantie reduits. "
        "Le socle qui complete le PTZ et Action Logement."
    ),
    "brs": (
        "Bail reel solidaire. Tu achetes le logement mais pas le terrain, qui "
        "reste a un organisme de foncier solidaire. Prix 20 a 40 % sous le "
        "marche, mais redevance mensuelle a vie et prix de revente plafonne "
        "pour toujours. Tu ne captes jamais la plus-value."
    ),
    "psla": (
        "Pret social location-accession. Tu emmenages d'abord comme locataire "
        "dans le logement que tu vas acheter, une partie du loyer devient ton "
        "apport, puis tu leves l'option. A l'arrivee tu possedes le logement "
        "ET le terrain, avec 15 ans d'exoneration de taxe fonciere."
    ),
    "redevance": (
        "Loyer du terrain verse a l'OFS en BRS. Elle s'ajoute a ta mensualite, "
        "compte comme une charge pour la banque, est indexee chaque annee et "
        "ne construit aucun capital. Plafonnee autour de 1,70 euro par m2 et "
        "par mois sur la Metropole de Lyon."
    ),
    "hcsf": (
        "Regle du Haut Conseil de stabilite financiere : mensualites assurance "
        "comprise sous 35 % des revenus, duree 25 ans maximum. Les banques "
        "peuvent deroger pour 20 % de leur production, en priorite pour les "
        "primo-accedants en residence principale, soit environ 38 a 40 %."
    ),
    "dvf": (
        "Demandes de valeurs foncieres : le fichier public de TOUTES les "
        "ventes reelles enregistrees par les notaires, prix, surface et "
        "adresse. La verite du marche, pas un prix d'annonce. Publie deux fois "
        "par an, absent en Alsace, Moselle et Mayotte."
    ),
    "dpe": (
        "Diagnostic de performance energetique, note de A a G. Les logements "
        "G sont interdits a la location depuis 2025, les F le seront en 2028. "
        "Une mauvaise note fait baisser le prix : opportunite si tu chiffres "
        "les travaux. La carte d'exposition aux argiles a ete durcie par "
        "l'arrete du 9 janvier 2026."
    ),
    "decote": (
        "Ecart entre le prix demande et le prix reel du marche local calcule "
        "sur les ventes DVF du quartier. Positif = moins cher que les voisins. "
        "Le seul indicateur objectif de bonne affaire."
    ),
    "georisques": (
        "Base publique des risques a l'adresse : inondation, argile qui "
        "fissure les murs, radon, pollution des sols, sismicite. A verifier "
        "avant toute offre, un risque connu se paie a la revente."
    ),
    "gpu": (
        "Geoportail de l'urbanisme : le zonage du plan local d'urbanisme d'une "
        "parcelle, servitudes et prescriptions. Utile pour savoir ce qui peut "
        "se construire a cote."
    ),
    "capacite": (
        "Mensualite maximum que la banque acceptera : 35 % de tes revenus "
        "retenus. Les revenus retenus = salaire net + 70 % des loyers percus."
    ),
    "phase2": (
        "Mensualite apres la fin du differe du PTZ, quand il commence a "
        "s'amortir. C'est le point le plus haut de ton echeancier et celui que "
        "la banque teste. Finanable en phase 1 mais pas en phase 2 = refuse."
    ),
    "regle_ptz_autres_prets": (
        "Le PTZ ne peut pas depasser le total de tes autres prets de plus de "
        "2 ans, sauf quand ta quotite atteint 50 % : il peut alors les "
        "depasser de 25 % au maximum. Consequence : trop d'apport reduit ton "
        "PTZ. Il existe un apport optimal, ni zero ni maximum."
    ),
}


def aide(cle: str) -> str:
    return GLOSSAIRE.get(cle, "")


# ----------------------------------------------------------------------
# 2. REFERENTIELS
# ----------------------------------------------------------------------

def charger_baremes() -> dict:
    with open(os.path.join(RACINE, "data", "baremes.json"), encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------
# 3. APIS
# ----------------------------------------------------------------------

def _get(url: str, params: dict | None = None) -> dict:
    try:
        r = requests.get(url, params=params, headers=UA, timeout=TIMEOUT)
        if r.status_code != 200:
            return {"ok": False, "donnees": None,
                    "message": f"HTTP {r.status_code}", "url": r.url}
        return {"ok": True, "donnees": r.json(), "message": "", "url": r.url}
    except Exception as e:
        return {"ok": False, "donnees": None, "message": str(e), "url": url}


def geocoder(adresse: str) -> dict:
    """
    Geocodage via la Geoplateforme IGN (data.geopf.fr).

    L'ancienne api-adresse.data.gouv.fr est decommissionnee depuis fin
    janvier 2026. Le nouveau service est iso-fonctionnel : memes parametres,
    meme format de reponse, limite de 50 requetes par seconde et par IP.
    """
    res = _get("https://data.geopf.fr/geocodage/search",
               {"q": adresse, "limit": 1, "index": "address"})
    if not res["ok"]:
        return {"ok": False, "message": res["message"], "source": "Geoplateforme"}
    feats = (res["donnees"] or {}).get("features") or []
    if not feats:
        return {"ok": False, "message": "Adresse introuvable", "source": "Geoplateforme"}
    p = feats[0]["properties"]
    lon, lat = feats[0]["geometry"]["coordinates"]
    return {
        "ok": True, "source": "Geoplateforme IGN",
        "donnees": {
            "label": p.get("label"), "lat": lat, "lon": lon,
            "code_insee": p.get("citycode"), "commune": p.get("city"),
            "code_postal": p.get("postcode"), "score": p.get("score"),
        },
    }


def _extraire(p: dict, candidats: tuple) -> float | None:
    for c in candidats:
        if p.get(c) not in (None, ""):
            try:
                return float(str(p[c]).replace(" ", "").replace(",", "."))
            except (TypeError, ValueError):
                continue
    return None


def ventes_dvf(lat: float, lon: float, rayon_m: int = 400) -> dict:
    """
    Ventes reelles autour d'un point.

    Source principale : l'API ouverte du Cerema (apidf), endpoints
    dvf_opendata, sans jeton pour la partie open data. On interroge les
    geomutations sur une emprise rectangulaire autour du point.
    Repli : l'API communautaire de Christian Quest, sans garantie de
    disponibilite.
    """
    dlat = rayon_m / 111320.0
    dlon = rayon_m / (111320.0 * max(math.cos(math.radians(lat)), 0.2))
    bbox = f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}"

    lignes = []
    res = _get("https://apidf-preprod.cerema.fr/dvf_opendata/geomutations/",
               {"in_bbox": bbox, "page_size": 500})
    if res["ok"]:
        feats = (res["donnees"] or {}).get("features") or []
        for f in feats:
            p = f.get("properties", {})
            val = _extraire(p, ("valeurfonc", "valeur_fonciere"))
            surf = _extraire(p, ("sbati", "surface_relle_bati", "surface_reelle_bati"))
            if not val or not surf or surf < 9 or val <= 0:
                continue
            lignes.append({
                "date": p.get("datemut") or p.get("date_mutation"),
                "type": p.get("libtypbien") or p.get("type_local"),
                "prix": val, "surface": surf, "prix_m2": val / surf,
            })
        if lignes:
            return {"ok": True, "source": "Cerema apidf (DVF+)", "donnees": lignes}

    res2 = _get("https://api.cquest.org/dvf",
                {"lat": lat, "lon": lon, "dist": rayon_m})
    if res2["ok"]:
        feats = (res2["donnees"] or {}).get("features") or []
        for f in feats:
            p = f.get("properties", {})
            val = _extraire(p, ("valeur_fonciere",))
            surf = _extraire(p, ("surface_relle_bati", "surface_reelle_bati"))
            if not val or not surf or surf < 9 or val <= 0:
                continue
            lignes.append({
                "date": p.get("date_mutation"),
                "type": p.get("type_local"),
                "prix": val, "surface": surf, "prix_m2": val / surf,
            })
        if lignes:
            return {"ok": True, "source": "api.cquest.org (repli)", "donnees": lignes}

    msg = res.get("message") or res2.get("message") or "Aucune vente trouvee"
    return {"ok": False, "source": "DVF", "message": msg}


def dpe_par_commune(code_insee: str, limite: int = 200) -> dict:
    """
    DPE de l'ADEME. L'identifiant du jeu change regulierement : on tente
    les identifiants connus, et deux syntaxes de filtre.
    """
    jeux = ["dpe03existant", "dpe-v2-logements-existants", "dpe-france"]
    filtres = [
        {"size": limite, "qs": f"code_insee_ban:{code_insee}"},
        {"size": limite, "q": code_insee},
    ]
    for jeu in jeux:
        url = f"https://data.ademe.fr/data-fair/api/v1/datasets/{jeu}/lines"
        for f in filtres:
            res = _get(url, f)
            if res["ok"] and isinstance(res["donnees"], dict):
                resultats = res["donnees"].get("results")
                if resultats:
                    return {"ok": True, "source": f"ADEME {jeu}", "donnees": resultats}
    return {"ok": False, "source": "ADEME",
            "message": "Aucun jeu ADEME n'a repondu avec des resultats. "
                       "Verifie l'identifiant du dataset sur data.ademe.fr."}


def risques(code_insee: str, lat: float | None = None,
            lon: float | None = None) -> dict:
    """
    Risques a l'adresse via Georisques (API v1, sans jeton).

    Source principale : le rapport de risques complet par coordonnees.
    Repli : l'inventaire GASPAR de la commune.
    """
    if lat is not None and lon is not None:
        res = _get("https://georisques.gouv.fr/api/v1/resultats_rapport_risque",
                   {"latlon": f"{lon},{lat}"})
        if res["ok"] and isinstance(res["donnees"], dict):
            d = res["donnees"]
            lignes = []
            for cat in ("risquesNaturels", "risquesTechnologiques"):
                for nom, det in (d.get(cat) or {}).items():
                    if isinstance(det, dict):
                        lignes.append({
                            "categorie": cat, "risque": nom,
                            "present": det.get("present"),
                            "libelle": det.get("libelle"),
                        })
            if lignes:
                return {"ok": True, "source": "Georisques rapport", "donnees": lignes}

    res2 = _get("https://georisques.gouv.fr/api/v1/gaspar/risques",
                {"code_insee": code_insee, "page_size": 50})
    if not res2["ok"]:
        return {"ok": False, "source": "Georisques", "message": res2["message"]}
    d = res2["donnees"] or {}
    items = d.get("data") or d.get("results") or []
    return {"ok": True, "source": "Georisques GASPAR", "donnees": items}


def zonage_urbanisme(lat: float, lon: float) -> dict:
    """Zonage PLU d'un point, API Carto de l'IGN, licence ouverte."""
    geom = json.dumps({"type": "Point", "coordinates": [lon, lat]})
    res = _get("https://apicarto.ign.fr/api/gpu/zone-urba", {"geom": geom})
    if not res["ok"]:
        return {"ok": False, "source": "API Carto GPU", "message": res["message"]}
    feats = (res["donnees"] or {}).get("features") or []
    return {"ok": True, "source": "API Carto GPU",
            "donnees": [f.get("properties", {}) for f in feats]}


def programmes_brs_grand_lyon() -> dict:
    """Programmes BRS publies par la Metropole de Lyon, API Features OGC."""
    base = "https://data.grandlyon.com/geoserver/ogc/features/v1/collections"
    res = _get(base, {"f": "json"})
    if not res["ok"]:
        return {"ok": False, "source": "data.grandlyon", "message": res["message"]}
    cols = (res["donnees"] or {}).get("collections") or []
    cible = None
    for c in cols:
        libelle = f"{c.get('id', '')} {c.get('title', '')}".lower()
        if "bail" in libelle or "brs" in libelle:
            cible = c.get("id")
            break
    if not cible:
        return {"ok": False, "source": "data.grandlyon",
                "message": "Collection BRS non trouvee dans la liste. Ouvre "
                           "l'onglet API du jeu de donnees et note son identifiant."}
    res2 = _get(f"{base}/{cible}/items", {"limit": 500, "f": "json"})
    if not res2["ok"]:
        return {"ok": False, "source": "data.grandlyon", "message": res2["message"]}
    feats = (res2["donnees"] or {}).get("features") or []
    return {"ok": True, "source": f"data.grandlyon / {cible}",
            "donnees": [f.get("properties", {}) for f in feats]}


# ----------------------------------------------------------------------
# 4. FINANCE
# ----------------------------------------------------------------------

def mensualite(capital: float, taux_annuel: float, duree_ans: float) -> float:
    if capital <= 0 or duree_ans <= 0:
        return 0.0
    n = duree_ans * 12
    if taux_annuel == 0:
        return capital / n
    i = taux_annuel / 12
    return capital * i / (1 - (1 + i) ** (-n))


def capacite_emprunt(salaire_net_mensuel: float, loyers_percus: float,
                     autres_charges: float, b: dict,
                     derogation: bool = False) -> dict:
    part = b["hcsf"]["part_loyers_retenue"]
    revenus = salaire_net_mensuel + loyers_percus * part
    taux = (b["hcsf"]["taux_effort_derogation"] if derogation
            else b["hcsf"]["taux_effort_max"])
    plafond = revenus * taux
    return {
        "revenus_retenus": revenus,
        "plafond_mensuel": plafond,
        "charges_existantes": autres_charges,
        "disponible": max(plafond - autres_charges, 0.0),
        "taux_applique": taux,
    }


def tranche_ptz(rfr: float, occupants: int, zone: str, cout_operation: float,
                b: dict) -> dict:
    """
    Tranche PTZ : revenu retenu = max(RFR, cout/9) divise par le coefficient
    familial. Eligibilite globale : RFR sous le plafond tranche 4 multiplie
    par le multiplicateur familial (1,5 pour 2 personnes, etc.).
    """
    n = str(min(occupants, 8))
    coef = b["coefficient_familial_tranche"].get(n, 1.0)
    mult = b["multiplicateur_plafond_ressources_ptz"].get(n, 1.0)
    grille = b["ptz_tranches"].get(zone, b["ptz_tranches"]["A"])
    plafond_absolu = grille[-1]["plafond_revenu_retenu"] * mult
    base = max(rfr, cout_operation / 9.0)
    revenu_retenu = base / coef

    if rfr > plafond_absolu:
        return {"eligible": False, "revenu_retenu": revenu_retenu,
                "coefficient": coef, "plafond_eligibilite": plafond_absolu,
                "tranche": None, "quotite": 0.0,
                "differe_ans": 0, "duree_totale_ans": 0}

    # Les tranches 1 a 3 sont bornees par part ; la tranche 4 couvre tout le
    # reste, l'eligibilite globale etant deja verifiee sur le RFR du foyer.
    for ligne in grille[:-1]:
        if revenu_retenu <= ligne["plafond_revenu_retenu"]:
            return {"eligible": True, "revenu_retenu": revenu_retenu,
                    "coefficient": coef, "plafond_eligibilite": plafond_absolu,
                    **ligne}
    return {"eligible": True, "revenu_retenu": revenu_retenu,
            "coefficient": coef, "plafond_eligibilite": plafond_absolu,
            **grille[-1]}


def plafond_operation(zone: str, occupants: int, b: dict) -> float:
    grille = b["ptz_plafond_operation"].get(zone, b["ptz_plafond_operation"]["A"])
    return float(grille.get(str(min(occupants, 5)), list(grille.values())[-1]))


def sous_plafond_ressources(rfr: float, zone: str, occupants: int, b: dict) -> dict:
    grille = b["plafond_ressources_psla_brs"].get(
        zone, b["plafond_ressources_psla_brs"]["A"])
    plafond = float(grille.get(str(min(occupants, 5)), list(grille.values())[-1]))
    return {"ok": rfr <= plafond, "plafond": plafond, "rfr": rfr}


DISPOSITIFS_PTZ = ("BRS", "PSLA", "Vente HLM", "Neuf QPV", "Neuf libre")
DISPOSITIFS_SOCIAUX = ("BRS", "PSLA", "Vente HLM", "Neuf QPV")


def montage(prix: float, surface: float, rfr: float, occupants: int, zone: str,
            dispositif: str, apport_souhaite: float, b: dict,
            action_logement_eligible: bool = True,
            redevance_m2: float | None = None,
            type_bien: str = "appartement") -> dict:
    """
    Plan de financement complet et mensualites en deux phases.

    Regles appliquees, verifiees sur le decret n. 2025-299 :
      - PTZ sur le neuf (libre inclus), le BRS, le PSLA et la vente HLM ;
        jamais sur l'ancien libre en zone A.
      - Quotite : grille collectif 50/40/40/20 pour appartement, BRS et
        PSLA ; grille individuelle 30/20/20/10 pour une maison neuve libre ;
        20 % fixe en vente HLM.
      - Les plafonds PSLA ne gouvernent que l'acces aux dispositifs sociaux,
        pas le PTZ lui-meme.
      - Le PTZ ne peut depasser la somme des autres prets de plus de 2 ans,
        sauf quotite a 50 % ou il peut les depasser de 25 % au plus.
    """
    frais_taux = (b["frais"]["notaire_ancien_libre"]
                  if dispositif == "Ancien libre"
                  else b["frais"]["notaire_neuf_ou_brs"])
    frais_notaire = prix * frais_taux
    frais_garantie = prix * b["frais"]["garantie_bancaire"]
    cout_total = prix + frais_notaire + frais_garantie

    ressources = sous_plafond_ressources(rfr, zone, occupants, b)
    social_ok = dispositif in DISPOSITIFS_SOCIAUX and ressources["ok"]

    tr = tranche_ptz(rfr, occupants, zone, prix, b)
    plaf_op = plafond_operation(zone, occupants, b)

    ptz_possible = dispositif in DISPOSITIFS_PTZ and tr["eligible"]
    if dispositif in DISPOSITIFS_SOCIAUX and not ressources["ok"]:
        ptz_possible = dispositif in ("Neuf QPV",) and tr["eligible"]
        social_ok = False

    quotite = tr.get("quotite", 0.0)
    if dispositif == "Vente HLM":
        quotite = b["ptz_quotite_vente_hlm"]
    elif dispositif == "Neuf libre" and type_bien == "maison":
        q_ind = b["ptz_quotite_individuel"]
        quotite = q_ind.get(str(tr.get("tranche")), 0.0) if tr["eligible"] else 0.0

    ptz = 0.0
    if ptz_possible and quotite > 0:
        assiette = min(prix, plaf_op)
        ptz = assiette * quotite

    al = 0.0
    if (action_logement_eligible and dispositif != "Ancien libre"
            and ressources["ok"]):
        al = float(b["action_logement"]["montant_vente_hlm"]
                   if dispositif == "Vente HLM"
                   else b["action_logement"]["montant_standard"])
        if dispositif not in b["action_logement"]["plafond_non_applicable"]:
            al = min(al, cout_total * b["action_logement"]["plafond_part_operation"])

    apport = max(0.0, min(apport_souhaite, cout_total))
    apport_net = max(0.0, apport - frais_notaire - frais_garantie)

    # Point fixe : PTZ <= facteur x (Action Logement + pret principal)
    facteur = 1.25 if quotite >= 0.5 else 1.0
    ptz_bride = False
    for _ in range(4):
        principal = max(0.0, prix - ptz - al - apport_net)
        limite = facteur * (al + principal)
        if ptz > limite + 1:
            ptz = limite
            ptz_bride = True
        else:
            break
    principal = max(0.0, prix - ptz - al - apport_net)

    duree = b["pret_principal"]["duree_max_ans"]
    taux_p = b["pret_principal"]["taux_pas_indicatif"]
    assurance = ((principal + al + ptz)
                 * b["pret_principal"]["taux_assurance_annuel_sur_capital"] / 12)

    m_al = mensualite(al, b["action_logement"]["taux"],
                      min(duree, b["action_logement"]["duree_max_ans"]))
    m_principal = mensualite(principal, taux_p, duree)

    red = 0.0
    if dispositif == "BRS":
        r = (redevance_m2 if redevance_m2 is not None
             else b["brs"]["redevance_eur_m2_mois_defaut"])
        red = surface * r

    differe = tr.get("differe_ans") or 0
    duree_ptz = tr.get("duree_totale_ans") or 0
    annees_amort_ptz = max(duree_ptz - differe, 1)
    m_ptz_apres = mensualite(ptz, 0.0, annees_amort_ptz)

    phase1 = m_al + m_principal + assurance + red
    phase2 = phase1 + m_ptz_apres

    return {
        "prix": prix, "frais_notaire": frais_notaire,
        "frais_garantie": frais_garantie, "cout_total": cout_total,
        "apport": apport, "ptz": ptz, "ptz_bride": ptz_bride,
        "quotite": quotite, "plafond_operation": plaf_op,
        "action_logement": al, "principal": principal,
        "tranche": tr, "ressources": ressources, "aide_possible": social_ok,
        "ptz_possible": ptz_possible and quotite > 0,
        "mensualite_al": m_al, "mensualite_principal": m_principal,
        "assurance": assurance, "redevance": red,
        "mensualite_ptz_apres_differe": m_ptz_apres,
        "phase1": phase1, "phase2": phase2,
        "differe_ans": differe, "duree_ptz_ans": duree_ptz,
        "part_gratuite": (ptz + al) / prix if prix else 0.0,
    }


def decote(prix_m2_bien: float, ventes: list) -> dict:
    valeurs = sorted(v["prix_m2"] for v in ventes if v.get("prix_m2"))
    if not valeurs:
        return {"ok": False, "message": "Pas assez de ventes comparables"}
    n = len(valeurs)
    mediane = (valeurs[n // 2] if n % 2
               else (valeurs[n // 2 - 1] + valeurs[n // 2]) / 2)
    return {
        "ok": True, "nb_ventes": n, "mediane_m2": mediane,
        "decote_pct": (1 - prix_m2_bien / mediane) * 100 if mediane else 0.0,
        "min_m2": valeurs[0], "max_m2": valeurs[-1],
    }


# ----------------------------------------------------------------------
# 5. LIENS DE RECHERCHE
# ----------------------------------------------------------------------

MOTS_CLES = {
    "solidaire": "attrape bail reel solidaire, foncier solidaire, OFS",
    "brs": "l'acronyme seul",
    "psla": "l'acronyme du pret social location-accession, rare mais gratuit",
    "accession": "accession sociale, maitrisee, a la propriete",
    "location-accession": "la formulation complete du PSLA",
    "prix maitrise": "les programmes a prix plafonne par les communes",
}


def _seloger_ci(code_insee: str) -> str:
    """
    SeLoger identifie les communes par un code 'ci' derive de l'INSEE :
    departement sur 2 caracteres, un zero, puis le code commune.
    Exemple : 69123 devient 690123. Meilleure approximation connue,
    a verifier au premier clic.
    """
    if len(code_insee) == 5:
        return code_insee[:2] + "0" + code_insee[2:]
    return code_insee


def liens_recherche(ville: str, lat: float, lon: float, code_insee: str,
                    rayon_km: int, prix_min: int, prix_max: int) -> list:
    """
    Genere les URL de recherche a enregistrer en alertes natives.
    Aucune collecte : tu ouvres les liens toi-meme.

    Le format de localisation Leboncoin reproduit celui observe sur de
    vraies URL : Ville__lat_lon_7308_rayonEnMetres.
    """
    sorties = []
    rayon_m = rayon_km * 1000
    ci = _seloger_ci(code_insee)
    for mot, explication in MOTS_CLES.items():
        lbc = ("https://www.leboncoin.fr/recherche?" + urlencode({
            "category": 9,
            "text": mot,
            "locations": f"{ville}__{lat}_{lon}_7308_{rayon_m}",
            "price": f"{prix_min}-{prix_max}",
        }))
        seloger = ("https://www.seloger.com/list.htm?" + urlencode({
            "projects": "2,5", "types": "1,2",
            "places": f"[{{ci:{ci}}}]",
            "price": f"{prix_min}/{prix_max}",
            "qsVersion": "1.0",
        }))
        bienici = ("https://www.bienici.com/recherche/achat/"
                   + quote_plus(ville.lower())
                   + f"?prix-max={prix_max}&q={quote_plus(mot)}")
        sorties.append({
            "mot_cle": mot, "explication": explication,
            "leboncoin": lbc, "seloger": seloger, "bienici": bienici,
        })
    return sorties
