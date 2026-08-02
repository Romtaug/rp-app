"""
Recherche de logement en accession aidée - application personnelle.

Lancement en local :   streamlit run app.py
Déploiement :          Streamlit Community Cloud, dépôt privé, accès
                       restreint à ta seule adresse mail.

Toutes les données lourdes sont interrogées en direct par API, rien n'est
stocké : l'application couvre donc toute la France sans limite de volume.
"""

import pandas as pd
import streamlit as st

import guide
import lib

st.set_page_config(page_title="Accession aidée", page_icon="🏠", layout="wide")

B = lib.charger_baremes()

# Cache d'une heure sur les appels réseau : navigation instantanée quand on
# revient sur une adresse déjà analysée, et ménagement des API publiques.
# La page Diagnostic n'utilise PAS ces enveloppes : elle doit tester en direct.
geocoder_c = st.cache_data(ttl=3600, show_spinner=False)(lib.geocoder)
ventes_dvf_c = st.cache_data(ttl=3600, show_spinner=False)(lib.ventes_dvf)
dpe_c = st.cache_data(ttl=3600, show_spinner=False)(lib.dpe_par_commune)
risques_c = st.cache_data(ttl=3600, show_spinner=False)(lib.risques)
zonage_c = st.cache_data(ttl=3600, show_spinner=False)(lib.zonage_urbanisme)
commune_c = st.cache_data(ttl=3600, show_spinner=False)(lib.fiche_commune)
parcelle_c = st.cache_data(ttl=3600, show_spinner=False)(lib.parcelle_cadastre)
argile_c = st.cache_data(ttl=3600, show_spinner=False)(lib.argile_rga)
radon_c = st.cache_data(ttl=3600, show_spinner=False)(lib.radon)
osm_c = st.cache_data(ttl=3600, show_spinner=False)(lib.equipements_osm)
ecoles_c = st.cache_data(ttl=3600, show_spinner=False)(lib.ecoles_education)
boris_sites_c = st.cache_data(ttl=3600, show_spinner=False)(lib.boris_sites_annonces)
boris_ofs_c = st.cache_data(ttl=3600, show_spinner=False)(lib.boris_ofs_proche)

ZONES = ["A", "Abis", "B1", "B2", "C"]
DISPOSITIFS = ["BRS", "PSLA", "Vente HLM", "Neuf QPV", "Neuf libre", "Ancien libre"]


def euros(x: float) -> str:
    return f"{x:,.0f} €".replace(",", " ")


# ----------------------------------------------------------------------
# État partagé : le profil est saisi une fois et sert partout
# ----------------------------------------------------------------------

def profil_sidebar():
    st.sidebar.header("Ton profil")
    st.sidebar.caption("Saisi une seule fois, utilisé par toutes les pages.")

    p = st.session_state.setdefault("profil", {
        "rfr": 29000, "occupants": 2, "zone": "A",
        "salaire": 2570.0, "loyers": 0.0, "charges": 0.0,
        "epargne": 70000.0, "al_eligible": True, "derogation": False,
    })

    p["rfr"] = st.sidebar.number_input(
        "Revenu fiscal de référence (N-2)", 0, 300000, p["rfr"], step=500,
        help=lib.aide("rfr"))
    p["occupants"] = st.sidebar.number_input(
        "Personnes qui habiteront le logement", 1, 8, p["occupants"],
        help=lib.aide("occupants"))
    p["zone"] = st.sidebar.selectbox(
        "Zone", ZONES, index=ZONES.index(p["zone"]), help=lib.aide("zone"))
    p["salaire"] = st.sidebar.number_input(
        "Salaire net mensuel", 0.0, 30000.0, p["salaire"], step=50.0,
        help="Ton net avant impôt, celui que la banque retient.")
    p["loyers"] = st.sidebar.number_input(
        "Loyers perçus par mois", 0.0, 20000.0, p["loyers"], step=10.0,
        help="La banque n'en retient que 70 %, pour couvrir la vacance "
             "locative et la taxe foncière.")
    p["charges"] = st.sidebar.number_input(
        "Mensualités de crédits en cours", 0.0, 10000.0, p["charges"], step=10.0,
        help="Attention : pour un prêt en différé, indique la mensualité "
             "FUTURE d'amortissement, pas celle que tu paies aujourd'hui. "
             "C'est celle-là que la banque simule.")
    p["epargne"] = st.sidebar.number_input(
        "Épargne disponible", 0.0, 1000000.0, p["epargne"], step=1000.0)
    p["al_eligible"] = st.sidebar.checkbox(
        "Salarié du privé, entreprise de 10 salariés et plus",
        p["al_eligible"], help=lib.aide("action_logement"))
    p["derogation"] = st.sidebar.checkbox(
        "Simuler la dérogation HCSF", p["derogation"], help=lib.aide("hcsf"))

    cap = lib.capacite_emprunt(p["salaire"], p["loyers"], p["charges"], B,
                               p["derogation"])
    st.sidebar.divider()
    st.sidebar.metric("Capacité mensuelle disponible",
                      euros(cap["disponible"]), help=lib.aide("capacite"))
    return p, cap


# ----------------------------------------------------------------------
# Page 0 : guide débutant
# ----------------------------------------------------------------------

def page_guide(p, cap):
    st.title("Guide débutant : acheter sa résidence principale avec les aides")
    st.write(guide.INTRO)

    st.header("L'idée clé à comprendre d'abord")
    st.info(guide.IDEE_CLE)

    st.header("Famille 1 : les dispositifs qui baissent le prix")
    st.caption("Tu en choisis UN. Clique sur chaque fiche.")
    for d in guide.DISPOSITIFS:
        with st.expander(f"{d['nom']} - {d['resume']}"):
            c1, c2 = st.columns(2)
            c1.metric("Effet sur le prix", d["prix"])
            c2.markdown(f"**Où le trouver :** {d['ou']}")
            st.markdown(f"**Comment ça marche.** {d['comment']}")
            st.markdown(f"**Pour qui.** {d['pour_qui']}")
            st.warning(f"**Le hic.** {d['le_hic']}")

    st.header("Famille 2 : les prêts qui baissent la mensualité")
    st.caption("Ceux-là se CUMULENT tous.")
    for pr in guide.PRETS:
        with st.expander(f"{pr['nom']} - {pr['resume']}"):
            st.markdown(f"**Montant.** {pr['montant']}")
            st.markdown(f"**Conditions.** {pr['conditions']}")
            st.success(f"**Le plus.** {pr['le_plus']}")

    st.header("Lequel est fait pour toi")
    st.write(guide.CHOISIR)

    st.header("Le parcours, étape par étape")
    for titre, texte in guide.PARCOURS:
        st.markdown(f"**{titre}.** {texte}")

    st.header("Les 8 pièges qui coûtent cher")
    for titre, texte in guide.PIEGES:
        with st.expander(titre):
            st.write(texte)

    st.header("Qui appeler, dans l'ordre")
    st.write(guide.QUI_APPELER)

    st.divider()
    st.success(
        "Étape suivante : renseigne ton profil dans la barre de gauche, puis "
        "ouvre le Tableau de bord pour voir à quoi TU as droit, chiffres à "
        "l'appui."
    )
    st.caption(
        "Ce guide vulgarise des règles vérifiées en juillet 2026 (décret "
        "n° 2025-299, arrêté du 24 février 2026). Il ne remplace ni l'ADIL, "
        "ni un courtier, ni un notaire."
    )


# ----------------------------------------------------------------------
# Page 1 : tableau de bord
# ----------------------------------------------------------------------

def page_accueil(p, cap):
    st.title("Accession aidée, tableau de bord")
    st.write(
        "Cette application répond à trois questions : à quoi ai-je droit, "
        "ce bien est-il une bonne affaire, et où trouver les biens."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Revenus retenus", euros(cap["revenus_retenus"]))
    c2.metric("Plafond mensuel", euros(cap["plafond_mensuel"]))
    c3.metric("Disponible", euros(cap["disponible"]))

    res = lib.sous_plafond_ressources(p["rfr"], p["zone"], p["occupants"], B)
    if res["ok"]:
        st.success(
            f"Sous les plafonds de ressources : {euros(res['rfr'])} contre un "
            f"plafond de {euros(res['plafond'])} pour {p['occupants']} "
            f"personne(s) en zone {p['zone']}."
        )
    else:
        st.error(
            f"Au-dessus des plafonds : {euros(res['rfr'])} contre "
            f"{euros(res['plafond'])}."
        )

    tr = lib.tranche_ptz(p["rfr"], p["occupants"], p["zone"], 200000, B)
    if tr["eligible"]:
        st.info(
            f"Tranche PTZ {tr['tranche']} : quotité de "
            f"{tr['quotite']*100:.0f} % du prix, différé de "
            f"{tr['differe_ans']} ans. Revenu retenu après division par le "
            f"coefficient familial de {tr['coefficient']} : "
            f"{euros(tr['revenu_retenu'])}."
        )

    with st.expander("Comprendre les dispositifs en une minute"):
        for cle in ["brs", "psla", "ptz", "action_logement", "pas",
                    "differe", "redevance", "regle_ptz_autres_prets"]:
            st.markdown(f"**{cle.replace('_', ' ').upper()}** : {lib.aide(cle)}")

    st.warning(
        "Les barèmes du fichier data/baremes.json ont été vérifiés en juillet "
        "2026 et sont surveillés automatiquement. Cette application ne "
        "remplace ni un courtier ni l'ADIL."
    )


# ----------------------------------------------------------------------
# Page 2 : simulateur de montage
# ----------------------------------------------------------------------

def page_montage(p, cap):
    st.title("Simulateur de montage")
    st.caption("Combien l'État te prête, et est-ce que ça passe en banque.")

    c1, c2, c3, c4 = st.columns(4)
    prix = c1.number_input("Prix du bien", 20000, 800000, 121510, step=1000)
    surface = c2.number_input("Surface habitable en m²", 9, 300, 60)
    dispositif = c3.selectbox("Dispositif", DISPOSITIFS,
                              help="Le dispositif change les frais de "
                                   "notaire, l'accès aux prêts aidés et la "
                                   "présence d'une redevance.")
    apport = c4.number_input("Apport", 0, 500000, 8000, step=500,
                             help=lib.aide("regle_ptz_autres_prets"))

    red_m2 = None
    if dispositif == "BRS":
        red_m2 = st.slider("Redevance en euros par m² et par mois", 0.5, 3.0,
                           float(B["brs"]["redevance_eur_m2_mois_defaut"]), 0.05,
                           help=lib.aide("redevance"))

    type_bien = "appartement"
    if dispositif == "Neuf libre":
        type_bien = st.radio(
            "Type de bien", ["appartement", "maison"], horizontal=True,
            help="La quotité PTZ diffère : 50/40/40/20 % en appartement, "
                 "30/20/20/10 % en maison individuelle neuve. BRS et PSLA "
                 "gardent la grille appartement même en individuel.")

    m = lib.montage(prix, surface, p["rfr"], p["occupants"], p["zone"],
                    dispositif, apport, B, p["al_eligible"], red_m2,
                    type_bien)

    st.subheader("Plan de financement")
    lignes = [
        ("Prêt à taux zéro", m["ptz"]),
        ("Prêt Action Logement à 1 %", m["action_logement"]),
        ("Prêt principal", m["principal"]),
        ("Apport", m["apport"]),
    ]
    df = pd.DataFrame([{"Ligne": n, "Montant": round(v)} for n, v in lignes if v > 0])
    st.dataframe(df, width="stretch", hide_index=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Part financée sans intérêts ou à 1 %",
              f"{m['part_gratuite']*100:.0f} %")
    c2.metric("Frais de notaire estimés", euros(m["frais_notaire"]))
    c3.metric("Coût total de l'opération", euros(m["cout_total"]))

    if m["ptz_bride"]:
        st.warning(
            "Ton PTZ a été plafonné par le montant de tes autres prêts. "
            "Réduis ton apport pour récupérer du prêt à taux zéro. "
            + lib.aide("regle_ptz_autres_prets")
        )

    st.subheader("Mensualités")
    c1, c2 = st.columns(2)
    c1.metric(f"Phase 1, {m['differe_ans']} premières années",
              euros(m["phase1"]), help=lib.aide("differe"))
    c2.metric("Phase 2, après le différé",
              euros(m["phase2"]), help=lib.aide("phase2"))

    if m["redevance"] > 0:
        st.caption(f"Dont redevance foncière : {euros(m['redevance'])} par "
                   f"mois, comptée comme une charge par la banque et qui ne "
                   f"construit aucun capital.")

    dispo = cap["disponible"]
    if m["phase2"] <= dispo:
        st.success(f"Finançable. Marge de {euros(dispo - m['phase2'])} par "
                   f"mois au point le plus haut de l'échéancier.")
    else:
        st.error(
            f"Dépassement de {euros(m['phase2'] - dispo)} par mois en phase "
            f"2. Trois leviers : rembourser un crédit en cours, lisser le "
            f"prêt, ou réduire le PTZ pour aplatir le profil."
        )

    if dispositif in ("BRS", "PSLA", "Vente HLM") and not m["aide_possible"]:
        st.info("Tes ressources dépassent les plafonds PSLA/BRS : ce "
                "dispositif social n'est pas accessible. Le PTZ peut rester "
                "possible sur du neuf libre si tu restes sous ses propres "
                "plafonds.")
    if dispositif != "Ancien libre" and not m["ptz_possible"]:
        st.info("Pas de PTZ dans cette configuration : revenus au-dessus du "
                "plafond d'éligibilité, ou quotité nulle.")
    if dispositif == "Ancien libre" and p["zone"] in ("A", "Abis", "B1"):
        st.warning("Ancien libre en zone tendue : ni PTZ ni Action Logement. "
                   "Le PTZ dans l'ancien n'existe qu'en zones B2 et C avec au "
                   "moins 25 % de travaux.")


# ----------------------------------------------------------------------
# Page 3 : évaluateur d'adresse
# ----------------------------------------------------------------------

def page_evaluateur(p, cap):
    st.title("Évaluateur d'adresse")
    st.caption("Colle une adresse d'annonce. Tout est interrogé en direct.")

    c1, c2, c3 = st.columns([3, 1, 1])
    adresse = c1.text_input("Adresse", "129 grande rue Saint-Clair, Caluire-et-Cuire")
    prix = c2.number_input("Prix demandé", 20000, 900000, 121510, step=1000)
    surface = c3.number_input("Surface m²", 9, 400, 60)
    rayon = st.slider("Rayon de comparaison en mètres", 100, 2000, 400, 50,
                      help=lib.aide("dvf"))

    if not st.button("Analyser"):
        return

    g = geocoder_c(adresse)
    if not g["ok"]:
        st.error(f"Géocodage impossible : {g.get('message')}")
        return
    d = g["donnees"]

    fc = commune_c(d["code_insee"])
    entete = f"**{d['label']}** - {d['commune']} ({d['code_insee']})"
    if fc["ok"] and fc["donnees"].get("population"):
        f = fc["donnees"]
        entete += (f" - {f['population']:,} habitants".replace(",", " ")
                   + (f", {f['densite_hab_km2']:,} hab/km²".replace(",", " ")
                      if f.get("densite_hab_km2") else ""))
    st.write(entete)

    onglets = st.tabs(["Prix du marché", "Énergie", "Risques",
                       "Urbanisme", "Vie de quartier"])

    with onglets[0]:
        v = ventes_dvf_c(d["lat"], d["lon"], rayon)
        if not v["ok"]:
            st.warning(f"DVF indisponible : {v.get('message')}")
        else:
            ventes = v["donnees"]
            dec = lib.decote(prix / surface, ventes)
            if dec["ok"]:
                c1, c2, c3 = st.columns(3)
                c1.metric("Prix au m² du bien", euros(prix / surface))
                c2.metric("Médiane du secteur", euros(dec["mediane_m2"]))
                c3.metric("Décote", f"{dec['decote_pct']:.0f} %",
                          help=lib.aide("decote"))
                st.caption(f"Calcul sur {dec['nb_ventes']} ventes réelles "
                           f"dans un rayon de {rayon} mètres. "
                           f"Source : {v['source']}.")
                st.dataframe(pd.DataFrame(ventes).sort_values("date", ascending=False),
                             width="stretch", hide_index=True)
            else:
                st.info(dec.get("message"))

    with onglets[1]:
        dpe = dpe_c(d["code_insee"])
        if not dpe["ok"]:
            st.warning(dpe.get("message"))
        else:
            st.caption(f"Source : {dpe['source']}. "
                       f"{len(dpe['donnees'])} diagnostics sur la commune.")
            st.info(lib.aide("dpe"))
            st.dataframe(pd.DataFrame(dpe["donnees"]).head(50),
                         width="stretch", hide_index=True)

    with onglets[2]:
        c1, c2 = st.columns(2)
        a = argile_c(d["lat"], d["lon"])
        c1.metric("Argile (retrait-gonflement)",
                  a["donnees"]["exposition"].capitalize() if a["ok"] else "indisponible",
                  help=lib.aide("argile"))
        r2 = radon_c(d["code_insee"])
        c2.metric("Radon (classe 1 à 3)",
                  str(r2["donnees"]["classe"]) if r2["ok"] and r2["donnees"]["classe"]
                  else "indisponible",
                  help=lib.aide("radon"))
        r = risques_c(d["code_insee"], d["lat"], d["lon"])
        if not r["ok"]:
            st.warning(r.get("message"))
        else:
            st.info(lib.aide("georisques"))
            st.dataframe(pd.DataFrame(r["donnees"]),
                         width="stretch", hide_index=True)

    with onglets[3]:
        pc = parcelle_c(d["lat"], d["lon"])
        if pc["ok"]:
            c1, c2 = st.columns(2)
            c1.metric("Parcelle cadastrale",
                      f"{pc['donnees'].get('section') or '?'} "
                      f"{pc['donnees'].get('numero') or ''}",
                      help=lib.aide("parcelle"))
            cont = pc["donnees"].get("contenance_m2")
            c2.metric("Contenance du terrain",
                      f"{cont:,} m²".replace(",", " ") if cont else "?")
        z = zonage_c(d["lat"], d["lon"])
        if not z["ok"]:
            st.warning(z.get("message"))
        else:
            st.info(lib.aide("gpu"))
            st.dataframe(pd.DataFrame(z["donnees"]),
                         width="stretch", hide_index=True)

    with onglets[4]:
        o = osm_c(d["lat"], d["lon"], 600)
        if not o["ok"]:
            st.warning(f"OpenStreetMap indisponible : {o.get('message')}")
        else:
            st.caption(f"Équipements dans un rayon de {o['rayon_m']} mètres, "
                       f"source OpenStreetMap.")
            st.dataframe(pd.DataFrame(o["donnees"]),
                         width="stretch", hide_index=True)
        e = ecoles_c(d["code_insee"])
        if not e["ok"]:
            st.warning(f"Éducation nationale : {e.get('message')}")
        else:
            st.caption(
                f"Établissements scolaires de la commune, avec l'indice de "
                f"position sociale quand il est publié "
                f"({e.get('ips_disponibles', 0)} IPS trouvés).")
            st.info(lib.aide("ips"))
            st.dataframe(pd.DataFrame(e["donnees"]),
                         width="stretch", hide_index=True)


# ----------------------------------------------------------------------
# Page 4 : générateur de liens de recherche
# ----------------------------------------------------------------------

def page_liens(p, cap):
    st.title("Générateur de liens de recherche")
    st.write(
        "Le PSLA et le BRS ancien ne sont indexés nulle part correctement. "
        "Cette page fabrique les URL de recherche à enregistrer en alertes "
        "natives sur chaque portail. Aucune donnée n'est collectée : tu "
        "cliques les liens toi-même, ce qui est la seule méthode propre."
    )

    c1, c2, c3, c4 = st.columns(4)
    ville = c1.text_input("Ville", "Lyon")
    rayon = c2.slider("Rayon en km", 5, 60, 25)
    pmin = c3.number_input("Prix min", 0, 500000, 70000, step=5000)
    pmax = c4.number_input("Prix max", 10000, 900000, 230000, step=5000)

    if not st.button("Générer les liens"):
        return

    g = geocoder_c(ville)
    if not g["ok"]:
        st.error("Ville introuvable")
        return
    d = g["donnees"]

    liens = lib.liens_recherche(d["commune"], d["lat"], d["lon"],
                                d["code_insee"], rayon, pmin, pmax)
    for l in liens:
        with st.container(border=True):
            st.markdown(f"**{l['mot_cle']}** - {l['explication']}")
            c1, c2, c3 = st.columns(3)
            c1.link_button("Leboncoin", l["leboncoin"], width="stretch")
            c2.link_button("SeLoger", l["seloger"], width="stretch")
            c3.link_button("Bienici", l["bienici"], width="stretch")

    st.success(
        "Ouvre chaque lien et enregistre-le en alerte avec notification. "
        "Sur ce marché les biens partent en quelques jours, donc consulter "
        "manuellement ne sert à rien."
    )

    st.divider()
    st.subheader(f"L'annuaire officiel BoRiS autour de {d['commune']}")
    st.caption(
        "Les sites qui diffusent des annonces BRS près de chez toi, recensés "
        "par la plateforme publique BoRiS. C'est là que vivent les annonces "
        "BRS que ni Leboncoin ni personne n'agrège : ouvre-les et inscris-toi "
        "à leurs alertes."
    )
    sites = boris_sites_c(d["lat"], d["lon"], rayon)
    if not sites["ok"]:
        st.warning(f"BoRiS indisponible : {sites.get('message')}")
    elif not sites["donnees"]:
        st.info("Aucun site recensé dans ce rayon. Élargis le rayon ou "
                "consulte la carte nationale sur boris.beta.gouv.fr.")
    else:
        for s in sites["donnees"][:12]:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                nom = s.get("distributorName") or s.get("ofsName") or "Site"
                infos = " - ".join(x for x in [
                    f"{s.get('city') or ''} {s.get('zipcode') or ''}".strip(),
                    f"OFS : {s['ofsName']}" if s.get("ofsName") else ""] if x)
                c1.markdown(f"**{nom}**" + (f"  \n{infos}" if infos else ""))
                if s.get("source"):
                    c2.link_button("Ouvrir le site", s["source"], width="stretch")

    ofs = boris_ofs_c(ville, rayon)
    if ofs["ok"] and ofs["donnees"]:
        st.subheader("Les OFS compétents pour cette adresse")
        st.caption("C'est chez eux que tu t'inscris sur liste de candidats.")
        try:
            st.dataframe(pd.DataFrame(ofs["donnees"]),
                         width="stretch", hide_index=True)
        except Exception:
            st.json(ofs["donnees"])


# ----------------------------------------------------------------------
# Page 5 : diagnostic des sources
# ----------------------------------------------------------------------

def page_diagnostic(p, cap):
    st.title("Diagnostic des sources")
    st.write(
        "Les identifiants et chemins des API publiques changent "
        "régulièrement. Cette page teste chaque source EN DIRECT, sans "
        "cache, et te dit laquelle est cassée pour que tu saches quoi "
        "corriger dans lib.py."
    )

    if not st.button("Lancer les tests"):
        return

    tests = []
    g = lib.geocoder("1 place Bellecour Lyon")
    tests.append(("Géoplateforme, géocodage", g["ok"], g.get("message", "")))
    if g["ok"]:
        d = g["donnees"]
        v = lib.ventes_dvf(d["lat"], d["lon"], 300)
        tests.append(("DVF, ventes réelles", v["ok"],
                      v.get("message", f"{len(v.get('donnees') or [])} ventes")))
        z = lib.zonage_urbanisme(d["lat"], d["lon"])
        tests.append(("API Carto GPU, zonage", z["ok"], z.get("message", "")))
        r = lib.risques(d["code_insee"], d["lat"], d["lon"])
        tests.append(("Géorisques, rapport", r["ok"], r.get("message", "")))
        a = lib.argile_rga(d["lat"], d["lon"])
        tests.append(("Géorisques, argile RGA", a["ok"], a.get("message", "")))
        rd = lib.radon(d["code_insee"])
        tests.append(("Géorisques, radon", rd["ok"], rd.get("message", "")))
        dpe = lib.dpe_par_commune(d["code_insee"], 5)
        tests.append(("ADEME, DPE", dpe["ok"],
                      dpe.get("message", dpe.get("source", ""))))
        fc = lib.fiche_commune(d["code_insee"])
        tests.append(("geo.api.gouv.fr, commune", fc["ok"], fc.get("message", "")))
        pc = lib.parcelle_cadastre(d["lat"], d["lon"])
        tests.append(("API Carto, cadastre", pc["ok"], pc.get("message", "")))
        o = lib.equipements_osm(d["lat"], d["lon"], 400)
        tests.append(("OpenStreetMap Overpass", o["ok"], o.get("message", "")))
        e = lib.ecoles_education(d["code_insee"], 5)
        tests.append(("Éducation nationale, écoles et IPS", e["ok"],
                      e.get("message", "")))
        bo = lib.boris_sites_annonces(d["lat"], d["lon"], 30, 5)
        tests.append(("BoRiS, annuaire des sites d'annonces BRS", bo["ok"],
                      bo.get("message", "")))
    brs = lib.programmes_brs_grand_lyon()
    tests.append(("data.grandlyon, programmes BRS", brs["ok"],
                  brs.get("message", brs.get("source", ""))))

    for nom, ok, msg in tests:
        if ok:
            st.success(f"{nom} : fonctionne. {msg}")
        else:
            st.error(f"{nom} : échec. {msg}")


# ----------------------------------------------------------------------
# Navigation
# ----------------------------------------------------------------------

PAGES = {
    "Guide débutant": page_guide,
    "Tableau de bord": page_accueil,
    "Simulateur de montage": page_montage,
    "Évaluateur d'adresse": page_evaluateur,
    "Générateur de liens": page_liens,
    "Diagnostic des sources": page_diagnostic,
}

profil, capacite = profil_sidebar()
st.sidebar.divider()
choix = st.sidebar.radio("Navigation", list(PAGES.keys()))
PAGES[choix](profil, capacite)
