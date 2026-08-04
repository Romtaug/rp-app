"""
Veille quotidienne des programmes en accession aidee.

Principe : on interroge les sources, on compare avec l'etat de la veille
stocke dans etat/etat.json, et on n'envoie un mail QUE s'il y a du nouveau.
Zero mail les jours sans nouveaute.

Variables d'environnement attendues (secrets GitHub) :
  BREVO_API_KEY     cle API Brevo
  MAIL_DEST         ton adresse de destination
  MAIL_EXP          adresse d'expedition validee chez Brevo
  COMMUNES          liste de communes separees par des virgules, filtre optionnel
"""

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

import lib

ETAT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "etat", "etat.json")
COMMUNES = [c.strip().lower() for c in os.environ.get("COMMUNES", "").split(",") if c.strip()]


def charger_etat() -> dict:
    if os.path.exists(ETAT):
        with open(ETAT, encoding="utf-8") as f:
            return json.load(f)
    return {"vus": [], "derniere_execution": None}


def sauver_etat(etat: dict) -> None:
    os.makedirs(os.path.dirname(ETAT), exist_ok=True)
    etat["derniere_execution"] = date.today().isoformat()
    with open(ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=2)


def cle_programme(p: dict) -> str:
    """Identifiant stable d'un programme, pour le diff."""
    for champ in ("id", "identifiant", "gid", "nom", "libelle", "adresse"):
        if p.get(champ):
            return f"{champ}:{p[champ]}"
    return json.dumps(p, sort_keys=True)[:200]


def enrichir(p: dict, b: dict) -> dict:
    """Ajoute le chiffrage au programme brut, pour que le mail soit decisionnel."""
    prix = None
    surface = None
    for k, v in p.items():
        kl = k.lower()
        if prix is None and "prix" in kl:
            try:
                prix = float(str(v).replace(" ", "").replace(",", "."))
            except (TypeError, ValueError):
                pass
        if surface is None and ("surf" in kl or "m2" in kl):
            try:
                surface = float(str(v).replace(" ", "").replace(",", "."))
            except (TypeError, ValueError):
                pass
    if not prix or not surface:
        return {"chiffrage": "donnees insuffisantes"}

    m = lib.montage(prix, surface, int(os.environ.get("RFR", 29000)),
                    int(os.environ.get("OCCUPANTS", 2)),
                    os.environ.get("ZONE", "A"), "BRS", 8000, b, True)
    cap = lib.capacite_emprunt(float(os.environ.get("SALAIRE", 2570)), 0.0, 0.0, b)
    return {
        "prix": round(prix),
        "prix_m2": round(prix / surface),
        "phase1": round(m["phase1"]),
        "phase2": round(m["phase2"]),
        "verdict": "finançable" if m["phase2"] <= cap["disponible"] else "hors capacite",
    }


def envoyer_mail(nouveautes: list) -> None:
    cle = os.environ.get("BREVO_API_KEY")
    dest = os.environ.get("MAIL_DEST")
    exp = os.environ.get("MAIL_EXP")
    if not (cle and dest and exp):
        print("Secrets Brevo absents, mail non envoye. Contenu :")
        print(json.dumps(nouveautes, ensure_ascii=False, indent=2))
        return

    lignes = "".join(
        f"<tr><td>{n.get('nom', '')}</td><td>{n.get('commune', '')}</td>"
        f"<td>{n['chiffrage'].get('prix_m2', '-')}</td>"
        f"<td>{n['chiffrage'].get('phase2', '-')}</td>"
        f"<td>{n['chiffrage'].get('verdict', '-')}</td></tr>"
        for n in nouveautes
    )
    html = (
        f"<p>{len(nouveautes)} nouveaute(s) en accession aidee.</p>"
        "<table border='1' cellpadding='6' style='border-collapse:collapse'>"
        "<tr><th>Programme</th><th>Commune</th><th>Prix m2</th>"
        "<th>Mensualite phase 2</th><th>Verdict</th></tr>"
        f"{lignes}</table>"
        "<p>Mensualite phase 2 = apres la fin du differe du PTZ, "
        "c'est le point le plus haut de l'echeancier.</p>"
    )
    r = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": cle, "content-type": "application/json"},
        json={
            "sender": {"email": exp, "name": "Veille accession"},
            "to": [{"email": dest}],
            "subject": f"{len(nouveautes)} nouveau(x) logement(s) en accession aidee",
            "htmlContent": html,
        },
        timeout=30,
    )
    print("Brevo:", r.status_code, r.text[:200])


def main() -> int:
    b = lib.charger_baremes()
    etat = charger_etat()
    vus = set(etat.get("vus", []))

    res = lib.programmes_brs_grand_lyon()
    if not res["ok"]:
        print("Source indisponible:", res.get("message"))
        return 0

    nouveautes = []
    for p in res["donnees"]:
        k = cle_programme(p)
        if k in vus:
            continue
        if COMMUNES:
            texte = json.dumps(p, ensure_ascii=False).lower()
            if not any(c in texte for c in COMMUNES):
                vus.add(k)
                continue
        p_enrichi = dict(p)
        p_enrichi["chiffrage"] = enrichir(p, b)
        nouveautes.append(p_enrichi)
        vus.add(k)

    # Instantané complet pour que l'application puisse lire les programmes
    # même quand data.grandlyon refuse la connexion depuis Streamlit Cloud.
    snap = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "programmes_brs.json")
    try:
        os.makedirs(os.path.dirname(snap), exist_ok=True)
        with open(snap, "w", encoding="utf-8") as f:
            json.dump({"date": date.today().isoformat(),
                       "source": res.get("source", ""),
                       "programmes": res["donnees"]},
                      f, ensure_ascii=False, indent=1)
        print(f"instantané écrit : {snap}")
    except Exception as e:
        print("instantané non écrit :", e)

    print(f"{len(res['donnees'])} programmes vus, {len(nouveautes)} nouveaux")
    if nouveautes:
        envoyer_mail(nouveautes)

    etat["vus"] = sorted(vus)
    sauver_etat(etat)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
