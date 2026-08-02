"""
Bibliothèque unique de l'application. Version 3.

Nouveautés v3 :
  - Interface et glossaire entièrement accentués.
  - Six enrichissements gratuits et sans clé ajoutés : fiche commune
    (geo.api.gouv.fr), parcelle cadastrale (API Carto), exposition argile
    RGA et potentiel radon (Géorisques), équipements de quartier
    (OpenStreetMap Overpass), écoles et indice de position sociale
    (data.education.gouv.fr).
"""

import json
import math
import os
from urllib.parse import quote_plus, urlencode

import requests

RACINE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 15
UA = {"User-Agent": "recherche-logement-perso/3.0"}


# ----------------------------------------------------------------------
# 1. GLOSSAIRE
# ----------------------------------------------------------------------

GLOSSAIRE = {
    "rfr": (
        "Revenu fiscal de référence. Ce n'est ni ton salaire brut ni ton net : "
        "c'est le montant calculé par le fisc, écrit sur ton avis d'imposition, "
        "cadre « Vos références ». Les dispositifs utilisent l'avis N-2 : pour "
        "un dossier en 2026, c'est l'avis 2025 sur les revenus 2024."
    ),
    "zone": (
        "Zonage ABC. La France est découpée en 5 zones selon la tension du "
        "marché : A bis (Paris), A (Lyon, Nice, frontalier genevois), B1 "
        "(grandes villes), B2, C. Tous tes plafonds en dépendent. Lyon et sa "
        "métropole sont en zone A."
    ),
    "occupants": (
        "Nombre de personnes qui vont HABITER le logement, pas le nombre "
        "d'acheteurs. Tu peux acheter seul et déclarer deux occupants. Plus il "
        "y a d'occupants, plus les plafonds montent et plus le PTZ est "
        "généreux, même si la personne n'a aucun revenu."
    ),
    "ptz": (
        "Prêt à taux zéro. Un prêt sans intérêts financé par l'État, réservé "
        "aux primo-accédants (pas propriétaires de leur résidence principale "
        "depuis 2 ans). Prolongé jusqu'au 31 décembre 2027. Jusqu'à 50 % du "
        "prix en collectif neuf, BRS et PSLA."
    ),
    "quotite": (
        "Part du prix que le PTZ peut financer. Elle dépend de ta tranche de "
        "revenus et du type de bien : 50/40/40/20 % en appartement neuf, BRS "
        "et PSLA ; 30/20/20/10 % en maison individuelle neuve ; 20 % fixe en "
        "vente HLM."
    ),
    "differe": (
        "Période pendant laquelle tu ne rembourses RIEN sur le PTZ : 10 ans en "
        "tranche 1, 8 ans en tranche 2, 2 ans en tranche 3, aucun différé en "
        "tranche 4. Ta mensualité saute à la fin du différé, et c'est ce point "
        "haut que la banque teste."
    ),
    "tranche": (
        "Catégorie de revenus qui fixe ta quotité et ton différé. Calcul : le "
        "plus élevé entre ton revenu fiscal N-2 et le prix de l'opération "
        "divisé par 9, le tout divisé par un coefficient familial (1 pour 1 "
        "personne, 1,4 pour 2, 1,7 pour 3, 2 pour 4). Tranche 1 = revenus les "
        "plus modestes = meilleures conditions."
    ),
    "action_logement": (
        "Prêt complémentaire à 1 % fixe, réservé aux salariés du privé dont "
        "l'entreprise compte au moins 10 salariés, primo-accédants ou non "
        "propriétaires depuis 10 ans. Jusqu'à 30 000 euros (40 000 en vente "
        "HLM), 25 ans maximum, plafonné à 40 % du coût de l'opération sauf en "
        "BRS et vente HLM. Environ 113 euros par mois pour 30 000 euros."
    ),
    "pas": (
        "Prêt d'accession sociale. Un prêt immobilier classique mais "
        "conventionné avec l'État : taux plafonné, frais de garantie réduits. "
        "Le socle qui complète le PTZ et Action Logement."
    ),
    "brs": (
        "Bail réel solidaire. Tu achètes le logement mais pas le terrain, qui "
        "reste à un organisme de foncier solidaire. Prix 20 à 40 % sous le "
        "marché, mais redevance mensuelle à vie et prix de revente plafonné "
        "pour toujours. Tu ne captes jamais la plus-value."
    ),
    "psla": (
        "Prêt social location-accession. Tu emménages d'abord comme locataire "
        "dans le logement que tu vas acheter, une partie du loyer devient ton "
        "apport, puis tu lèves l'option. À l'arrivée tu possèdes le logement "
        "ET le terrain, avec 15 ans d'exonération de taxe foncière."
    ),
    "redevance": (
        "Loyer du terrain versé à l'OFS en BRS. Elle s'ajoute à ta mensualité, "
        "compte comme une charge pour la banque, est indexée chaque année et "
        "ne construit aucun capital. Plafonnée autour de 1,70 euro par m² et "
        "par mois sur la Métropole de Lyon."
    ),
    "hcsf": (
        "Règle du Haut Conseil de stabilité financière : mensualités assurance "
        "comprise sous 35 % des revenus, durée 25 ans maximum. Les banques "
        "peuvent déroger pour 20 % de leur production, en priorité pour les "
        "primo-accédants en résidence principale, soit environ 38 à 40 %."
    ),
    "dvf": (
        "Demandes de valeurs foncières : le fichier public de TOUTES les "
        "ventes réelles enregistrées par les notaires, prix, surface et "
        "adresse. La vérité du marché, pas un prix d'annonce. Publié deux fois "
        "par an, absent en Alsace, Moselle et Mayotte."
    ),
    "dpe": (
        "Diagnostic de performance énergétique, note de A à G. Les logements "
        "G sont interdits à la location depuis 2025, les F le seront en 2028. "
        "Une mauvaise note fait baisser le prix : opportunité si tu chiffres "
        "les travaux."
    ),
    "decote": (
        "Écart entre le prix demandé et le prix réel du marché local calculé "
        "sur les ventes DVF du quartier. Positif = moins cher que les voisins. "
        "Le seul indicateur objectif de bonne affaire."
    ),
    "georisques": (
        "Base publique des risques à l'adresse : inondation, argile qui "
        "fissure les murs, radon, pollution des sols, sismicité. À vérifier "
        "avant toute offre, un risque connu se paie à la revente."
    ),
    "argile": (
        "Retrait-gonflement des argiles : le sol gonfle quand il pleut, se "
        "rétracte à la sécheresse, et les murs fissurent. Première cause de "
        "sinistre habitation en France, carte durcie par l'arrêté du 9 "
        "janvier 2026. Exposition forte = surprime d'assurance et vigilance "
        "sur les fissures existantes."
    ),
    "radon": (
        "Gaz radioactif naturel qui remonte du sol, classé par commune de 1 "
        "(faible) à 3 (élevé). En classe 3, une mesure et parfois une "
        "ventilation renforcée sont recommandées, surtout en rez-de-chaussée."
    ),
    "ips": (
        "Indice de position sociale, publié par l'Éducation nationale pour "
        "chaque école et collège. Moyenne nationale autour de 100 : plus "
        "c'est haut, plus le profil social des élèves est favorisé. Un des "
        "meilleurs prédicteurs de la valeur d'un quartier à long terme."
    ),
    "parcelle": (
        "L'unité cadastrale du terrain : section, numéro et contenance en m². "
        "Utile pour vérifier ce que tu achètes exactement et interroger les "
        "règles d'urbanisme."
    ),
    "gpu": (
        "Géoportail de l'urbanisme : le zonage du plan local d'urbanisme d'une "
        "parcelle, servitudes et prescriptions. Utile pour savoir ce qui peut "
        "se construire à côté."
    ),
    "capacite": (
        "Mensualité maximum que la banque acceptera : 35 % de tes revenus "
        "retenus. Les revenus retenus = salaire net + 70 % des loyers perçus."
    ),
    "phase2": (
        "Mensualité après la fin du différé du PTZ, quand il commence à "
        "s'amortir. C'est le point le plus haut de ton échéancier et celui que "
        "la banque teste. Finançable en phase 1 mais pas en phase 2 = refusé."
    ),
    "regle_ptz_autres_prets": (
        "Le PTZ ne peut pas dépasser le total de tes autres prêts de plus de "
        "2 ans, sauf quand ta quotité atteint 50 % : il peut alors les "
        "dépasser de 25 % au maximum. Conséquence : trop d'apport réduit ton "
        "PTZ. Il existe un apport optimal, ni zéro ni maximum."
    ),
}


def aide(cle: str) -> str:
    return GLOSSAIRE.get(cle, "")


# ----------------------------------------------------------------------
# 2. RÉFÉRENTIELS
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


def _dist_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def geocoder(adresse: str) -> dict:
    """Géocodage via la Géoplateforme IGN, remplaçante officielle de
    l'ancienne api-adresse décommissionnée fin janvier 2026."""
    res = _get("https://data.geopf.fr/geocodage/search",
               {"q": adresse, "limit": 1, "index": "address"})
    if not res["ok"]:
        return {"ok": False, "message": res["message"], "source": "Géoplateforme"}
    feats = (res["donnees"] or {}).get("features") or []
    if not feats:
        return {"ok": False, "message": "Adresse introuvable", "source": "Géoplateforme"}
    p = feats[0]["properties"]
    lon, lat = feats[0]["geometry"]["coordinates"]
    return {
        "ok": True, "source": "Géoplateforme IGN",
        "donnees": {
            "label": p.get("label"), "lat": lat, "lon": lon,
            "code_insee": p.get("citycode"), "commune": p.get("city"),
            "code_postal": p.get("postcode"), "score": p.get("score"),
        },
    }


def fiche_commune(code_insee: str) -> dict:
    """Population, surface et densité de la commune, via geo.api.gouv.fr."""
    res = _get(f"https://geo.api.gouv.fr/communes/{code_insee}",
               {"fields": "nom,population,surface,codesPostaux"})
    if not res["ok"] or not isinstance(res["donnees"], dict):
        return {"ok": False, "source": "geo.api.gouv.fr",
                "message": res.get("message", "réponse vide")}
    d = res["donnees"]
    pop = d.get("population")
    surf_ha = d.get("surface")
    densite = round(pop / (surf_ha / 100)) if pop and surf_ha else None
    return {"ok": True, "source": "geo.api.gouv.fr",
            "donnees": {"nom": d.get("nom"), "population": pop,
                        "surface_km2": round(surf_ha / 100, 1) if surf_ha else None,
                        "densite_hab_km2": densite}}


def _extraire(p: dict, candidats: tuple) -> float | None:
    for c in candidats:
        if p.get(c) not in (None, ""):
            try:
                return float(str(p[c]).replace(" ", "").replace(",", "."))
            except (TypeError, ValueError):
                continue
    return None


def ventes_dvf(lat: float, lon: float, rayon_m: int = 400) -> dict:
    """Ventes réelles autour d'un point. Source principale : API ouverte du
    Cerema (apidf, DVF+). Repli : API communautaire cquest."""
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

    msg = res.get("message") or res2.get("message") or "Aucune vente trouvée"
    return {"ok": False, "source": "DVF", "message": msg}


def dpe_par_commune(code_insee: str, limite: int = 200) -> dict:
    """DPE de l'ADEME. Les identifiants de jeux changent : on tente les
    identifiants connus et deux syntaxes de filtre."""
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
            "message": "Aucun jeu ADEME n'a répondu avec des résultats. "
                       "Vérifie l'identifiant du dataset sur data.ademe.fr."}


def risques(code_insee: str, lat: float | None = None,
            lon: float | None = None) -> dict:
    """Risques à l'adresse via Géorisques v1, sans jeton. Rapport complet
    aux coordonnées en principal, inventaire GASPAR en repli."""
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
                return {"ok": True, "source": "Géorisques rapport", "donnees": lignes}

    res2 = _get("https://georisques.gouv.fr/api/v1/gaspar/risques",
                {"code_insee": code_insee, "page_size": 50})
    if not res2["ok"]:
        return {"ok": False, "source": "Géorisques", "message": res2["message"]}
    d = res2["donnees"] or {}
    items = d.get("data") or d.get("results") or []
    return {"ok": True, "source": "Géorisques GASPAR", "donnees": items}


def argile_rga(lat: float, lon: float) -> dict:
    """Exposition au retrait-gonflement des argiles, Géorisques v1."""
    res = _get("https://georisques.gouv.fr/api/v1/rga",
               {"latlon": f"{lon},{lat}"})
    if not res["ok"] or not isinstance(res["donnees"], dict):
        return {"ok": False, "source": "Géorisques RGA",
                "message": res.get("message", "réponse vide")}
    d = res["donnees"]
    expo = (d.get("exposition") or d.get("alea")
            or (d.get("data") or [{}])[0].get("exposition")
            if isinstance(d.get("data"), list) else d.get("exposition"))
    return {"ok": True, "source": "Géorisques RGA",
            "donnees": {"exposition": expo or "inconnue", "brut": d}}


def radon(code_insee: str) -> dict:
    """Potentiel radon de la commune (classe 1 à 3), Géorisques v1."""
    res = _get("https://georisques.gouv.fr/api/v1/radon",
               {"code_insee": code_insee, "page_size": 5})
    if not res["ok"] or not isinstance(res["donnees"], dict):
        return {"ok": False, "source": "Géorisques radon",
                "message": res.get("message", "réponse vide")}
    items = res["donnees"].get("data") or res["donnees"].get("results") or []
    classe = None
    if items:
        classe = (items[0].get("classe_potentiel") or items[0].get("classe")
                  or items[0].get("potentiel"))
    return {"ok": True, "source": "Géorisques radon",
            "donnees": {"classe": classe}}


def parcelle_cadastre(lat: float, lon: float) -> dict:
    """Parcelle cadastrale au point : section, numéro, contenance.
    API Carto de l'IGN, module cadastre, sans clé."""
    geom = json.dumps({"type": "Point", "coordinates": [lon, lat]})
    res = _get("https://apicarto.ign.fr/api/cadastre/parcelle", {"geom": geom})
    if not res["ok"]:
        return {"ok": False, "source": "API Carto cadastre", "message": res["message"]}
    feats = (res["donnees"] or {}).get("features") or []
    if not feats:
        return {"ok": False, "source": "API Carto cadastre",
                "message": "Aucune parcelle au point"}
    p = feats[0].get("properties", {})
    return {"ok": True, "source": "API Carto cadastre",
            "donnees": {"section": p.get("section"), "numero": p.get("numero"),
                        "contenance_m2": p.get("contenance"),
                        "commune": p.get("nom_com")}}


def zonage_urbanisme(lat: float, lon: float) -> dict:
    """Zonage PLU au point, API Carto de l'IGN, module GPU."""
    geom = json.dumps({"type": "Point", "coordinates": [lon, lat]})
    res = _get("https://apicarto.ign.fr/api/gpu/zone-urba", {"geom": geom})
    if not res["ok"]:
        return {"ok": False, "source": "API Carto GPU", "message": res["message"]}
    feats = (res["donnees"] or {}).get("features") or []
    return {"ok": True, "source": "API Carto GPU",
            "donnees": [f.get("properties", {}) for f in feats]}


_OVERPASS_URLS = ["https://overpass-api.de/api/interpreter",
                  "https://overpass.kumi.systems/api/interpreter"]

_CATEGORIES_OSM = {
    "Transports": lambda t: (t.get("highway") == "bus_stop"
                             or t.get("railway") in ("station", "tram_stop")),
    "Écoles": lambda t: t.get("amenity") == "school",
    "Commerces": lambda t: t.get("shop") in ("supermarket", "bakery", "convenience"),
    "Santé": lambda t: t.get("amenity") in ("pharmacy", "doctors"),
}


def equipements_osm(lat: float, lon: float, rayon_m: int = 600) -> dict:
    """Équipements du quartier via OpenStreetMap (Overpass, sans clé) :
    transports, écoles, commerces, santé, avec la distance du plus proche."""
    requete = f"""
    [out:json][timeout:20];
    (
      node(around:{rayon_m},{lat},{lon})[highway=bus_stop];
      node(around:{rayon_m},{lat},{lon})[railway~"^(station|tram_stop)$"];
      node(around:{rayon_m},{lat},{lon})[amenity~"^(school|pharmacy|doctors)$"];
      node(around:{rayon_m},{lat},{lon})[shop~"^(supermarket|bakery|convenience)$"];
    );
    out body;
    """
    derniere_erreur = ""
    for url in _OVERPASS_URLS:
        try:
            r = requests.post(url, data={"data": requete}, headers=UA, timeout=30)
            if r.status_code != 200:
                derniere_erreur = f"HTTP {r.status_code}"
                continue
            elements = (r.json() or {}).get("elements") or []
            lignes = []
            for nom_cat, test in _CATEGORIES_OSM.items():
                membres = [e for e in elements if test(e.get("tags", {}))]
                if not membres:
                    lignes.append({"categorie": nom_cat, "nombre": 0,
                                   "plus_proche_m": None})
                    continue
                dmin = min(_dist_m(lat, lon, e["lat"], e["lon"])
                           for e in membres if "lat" in e and "lon" in e)
                lignes.append({"categorie": nom_cat, "nombre": len(membres),
                               "plus_proche_m": round(dmin)})
            return {"ok": True, "source": "OpenStreetMap Overpass",
                    "donnees": lignes, "rayon_m": rayon_m}
        except Exception as e:
            derniere_erreur = str(e)
    return {"ok": False, "source": "OpenStreetMap Overpass",
            "message": derniere_erreur or "aucun miroir n'a répondu"}


def ecoles_education(code_insee: str, limite: int = 30) -> dict:
    """Écoles et collèges de la commune (annuaire de l'Éducation nationale),
    enrichis quand possible de l'indice de position sociale (IPS).
    API opendatasoft de data.education.gouv.fr, sans clé."""
    base = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets"
    res = _get(f"{base}/fr-en-annuaire-education/records",
               {"where": f'code_commune="{code_insee}"', "limit": limite,
                "select": "nom_etablissement,type_etablissement,"
                          "statut_public_prive,identifiant_de_l_etablissement"})
    if not res["ok"] or not isinstance(res["donnees"], dict):
        return {"ok": False, "source": "data.education.gouv.fr",
                "message": res.get("message", "réponse vide")}
    etabs = res["donnees"].get("results") or []
    if not etabs:
        return {"ok": False, "source": "data.education.gouv.fr",
                "message": "Aucun établissement trouvé pour cette commune"}

    ips_par_uai = {}
    for jeu in ("fr-en-ips-ecoles-ap2022", "fr-en-ips-colleges-ap2022",
                "fr-en-ips-ecoles", "fr-en-ips-colleges"):
        r2 = _get(f"{base}/{jeu}/records",
                  {"where": f'code_insee_de_la_commune="{code_insee}"',
                   "limit": 50, "order_by": "rentree_scolaire desc"})
        if r2["ok"] and isinstance(r2["donnees"], dict):
            for ligne in r2["donnees"].get("results") or []:
                uai = ligne.get("uai")
                valeur = ligne.get("ips")
                if uai and valeur and uai not in ips_par_uai:
                    ips_par_uai[uai] = valeur

    lignes = []
    for e in etabs:
        lignes.append({
            "établissement": e.get("nom_etablissement"),
            "type": e.get("type_etablissement"),
            "statut": e.get("statut_public_prive"),
            "ips": ips_par_uai.get(e.get("identifiant_de_l_etablissement")),
        })
    return {"ok": True, "source": "data.education.gouv.fr",
            "donnees": lignes, "ips_disponibles": len(ips_par_uai)}


def programmes_brs_grand_lyon() -> dict:
    """Programmes BRS publiés par la Métropole de Lyon, API Features OGC."""
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
                "message": "Collection BRS non trouvée dans la liste. Ouvre "
                           "l'onglet API du jeu de données et note son identifiant."}
    res2 = _get(f"{base}/{cible}/items", {"limit": 500, "f": "json"})
    if not res2["ok"]:
        return {"ok": False, "source": "data.grandlyon", "message": res2["message"]}
    feats = (res2["donnees"] or {}).get("features") or []
    return {"ok": True, "source": f"data.grandlyon / {cible}",
            "donnees": [f.get("properties", {}) for f in feats]}


_BORIS = "https://boris.beta.gouv.fr/api"


def _liste_defensive(d):
    """Les routes BoRiS renvoient une pagination dont la forme peut varier :
    on accepte une liste brute ou un dictionnaire l'enveloppant."""
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for cle in ("items", "data", "results", "brsDiffusionWebsites", "rows"):
            if isinstance(d.get(cle), list):
                return d[cle]
    return []


def boris_sites_annonces(lat: float, lon: float, rayon_km: int = 30,
                         limite: int = 50) -> dict:
    """Annuaire officiel BoRiS des sites qui diffusent des annonces BRS
    autour d'un point. Endpoints publics de la plateforme d'État, relevés
    dans son code source (MIT, github.com/MTES-MCT/boris). Champs :
    source (URL du site), distributorName, ofsName, city, zipcode."""
    res = _get(f"{_BORIS}/brs-diffusion-websites",
               {"latitude": lat, "longitude": lon, "radius": rayon_km,
                "page": 1, "pageSize": limite})
    if not res["ok"]:
        res2 = _get(f"{_BORIS}/brs-diffusion-websites/all")
        if not res2["ok"]:
            return {"ok": False, "source": "BoRiS",
                    "message": res.get("message") or res2.get("message")}
        tous = _liste_defensive(res2["donnees"])
        proches = [s for s in tous
                   if s.get("latitude") and s.get("longitude")
                   and _dist_m(lat, lon, s["latitude"], s["longitude"]) <= rayon_km * 1000]
        return {"ok": True, "source": "BoRiS (liste nationale filtrée)",
                "donnees": proches[:limite]}
    return {"ok": True, "source": "BoRiS",
            "donnees": _liste_defensive(res["donnees"])[:limite]}


def boris_ofs_proche(adresse: str, rayon_km: int = 20) -> dict:
    """Les organismes de foncier solidaire compétents autour d'une adresse,
    via la route publique find-my-ofs de BoRiS."""
    res = _get(f"{_BORIS}/find-my-ofs",
               {"address": adresse, "radius": rayon_km})
    if not res["ok"]:
        return {"ok": False, "source": "BoRiS find-my-ofs",
                "message": res["message"]}
    return {"ok": True, "source": "BoRiS find-my-ofs",
            "donnees": _liste_defensive(res["donnees"]) or res["donnees"]}


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
    "solidaire": "attrape bail réel solidaire, foncier solidaire, OFS",
    "brs": "l'acronyme seul",
    "psla": "l'acronyme du prêt social location-accession, rare mais gratuit",
    "accession": "accession sociale, maîtrisée, à la propriété",
    "location-accession": "la formulation complète du PSLA",
    "prix maitrise": "les programmes à prix plafonné par les communes",
}


def _seloger_ci(code_insee: str) -> str:
    if len(code_insee) == 5:
        return code_insee[:2] + "0" + code_insee[2:]
    return code_insee


def liens_recherche(ville: str, lat: float, lon: float, code_insee: str,
                    rayon_km: int, prix_min: int, prix_max: int) -> list:
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
