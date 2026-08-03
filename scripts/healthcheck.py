"""
Surveillance automatique des sources de l'application.

Lance chaque lundi matin par GitHub Actions, ce script appelle les six
API utilisees par l'app et verifie l'age des baremes. Deux canaux
d'alerte, dans l'ordre :

  1. Le code de sortie. En cas de panne, le script sort en erreur, le
     run GitHub Actions passe au rouge, et GitHub t'envoie NATIVEMENT un
     mail de workflow en echec. Aucune configuration necessaire : ca
     marche des le premier jour, meme sans Brevo.
  2. Si les secrets Brevo sont presents, un mail detaille est envoye en
     plus, avec le nom de la source tombee et le message d'erreur.

Silence total quand tout fonctionne : pas de mail, run vert.
"""

import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

import lib

SEUIL_AGE_BAREMES_JOURS = 330


def tester_sources() -> list:
    resultats = []
    g = lib.geocoder("1 place Bellecour Lyon")
    resultats.append(("Geoplateforme, geocodage", g["ok"], g.get("message", "")))
    if g["ok"]:
        d = g["donnees"]
        v = lib.ventes_dvf(d["lat"], d["lon"], 300)
        resultats.append(("DVF (Cerema puis cquest)", v["ok"],
                          v.get("message", f"{len(v.get('donnees') or [])} ventes")))
        z = lib.zonage_urbanisme(d["lat"], d["lon"])
        resultats.append(("API Carto GPU, zonage PLU", z["ok"], z.get("message", "")))
        r = lib.risques(d["code_insee"], d["lat"], d["lon"])
        resultats.append(("Georisques", r["ok"], r.get("message", "")))
        dpe = lib.dpe_par_commune(d["code_insee"], 5)
        resultats.append(("ADEME, DPE", dpe["ok"],
                          dpe.get("message", dpe.get("source", ""))))
        fc = lib.fiche_commune(d["code_insee"])
        resultats.append(("geo.api.gouv.fr, commune", fc["ok"], fc.get("message", "")))
        pc = lib.parcelle_cadastre(d["lat"], d["lon"])
        resultats.append(("API Carto, cadastre", pc["ok"], pc.get("message", "")))
        a = lib.argile_rga(d["lat"], d["lon"])
        resultats.append(("Georisques, argile RGA", a["ok"], a.get("message", "")))
        rd = lib.radon(d["code_insee"])
        resultats.append(("Georisques, radon", rd["ok"], rd.get("message", "")))
        o = lib.equipements_osm(d["lat"], d["lon"], 400)
        resultats.append(("OpenStreetMap Overpass", o["ok"], o.get("message", "")))
        e = lib.ecoles_education(d["code_insee"], 5)
        resultats.append(("Education nationale, ecoles et IPS", e["ok"], e.get("message", "")))
        bo = lib.boris_sites_annonces(d["lat"], d["lon"], 30, 5)
        resultats.append(("BoRiS, sites d'annonces BRS", bo["ok"], bo.get("message", "")))
    else:
        resultats.append(("Tests dependants du geocodage", False,
                          "non executes, geocodage en panne"))
    brs = lib.programmes_brs_grand_lyon()
    resultats.append(("data.grandlyon, programmes BRS", brs["ok"],
                      brs.get("message", brs.get("source", ""))))
    return resultats


def age_baremes_jours() -> int | None:
    b = lib.charger_baremes()
    d = b.get("_derniere_verification")
    if not d:
        return None
    try:
        return (date.today() - datetime.strptime(d, "%Y-%m-%d").date()).days
    except ValueError:
        return None


def envoyer_mail_brevo(sujet: str, html: str) -> None:
    cle = os.environ.get("BREVO_API_KEY")
    dest = os.environ.get("MAIL_DEST")
    exp = os.environ.get("MAIL_EXP")
    if not (cle and dest and exp):
        print("Secrets Brevo absents : le run rouge et le mail natif GitHub "
              "servent d'alerte.")
        return
    r = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": cle, "content-type": "application/json"},
        json={"sender": {"email": exp, "name": "Healthcheck immo-app"},
              "to": [{"email": dest}],
              "subject": sujet, "htmlContent": html},
        timeout=30,
    )
    print("Brevo:", r.status_code, r.text[:200])


def main() -> int:
    resultats = tester_sources()
    pannes = [(n, msg) for n, ok, msg in resultats if not ok]
    for n, ok, msg in resultats:
        print(f"{'OK ' if ok else 'KO '} {n} {('- ' + msg) if msg else ''}")

    alertes = list(pannes)
    age = age_baremes_jours()
    if age is not None and age > SEUIL_AGE_BAREMES_JOURS:
        alertes.append(("Baremes", f"non verifies depuis {age} jours : les "
                        "plafonds PTZ/PSLA ont probablement change, mets a "
                        "jour data/baremes.json"))
        print(f"KO  Baremes anciens ({age} jours)")
    elif age is not None:
        print(f"OK  Baremes verifies il y a {age} jours")

    if not alertes:
        print("Tout fonctionne.")
        return 0

    lignes = "".join(f"<tr><td>{n}</td><td>{m}</td></tr>" for n, m in alertes)
    envoyer_mail_brevo(
        f"immo-app : {len(alertes)} source(s) en panne",
        "<p>Le healthcheck hebdomadaire a detecte :</p>"
        "<table border='1' cellpadding='6' style='border-collapse:collapse'>"
        f"<tr><th>Source</th><th>Probleme</th></tr>{lignes}</table>"
        "<p>Ouvre la page Diagnostic des sources de l'app pour confirmer, "
        "puis corrige l'endpoint dans lib.py ou les valeurs dans "
        "data/baremes.json.</p>",
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
