"""
Recherche de logement en accession aidee - application personnelle.

Lancement en local :   streamlit run app.py
Deploiement :          Streamlit Community Cloud, depot prive, acces restreint
                       a ta seule adresse mail.

Toutes les donnees lourdes sont interrogees en direct par API, rien n'est
stocke. L'application fonctionne donc sur toute la France sans limite de
volume.
"""

import pandas as pd
import streamlit as st

import guide
import lib

st.set_page_config(page_title="Accession aidee", page_icon="🏠", layout="wide")

B = lib.charger_baremes()

# Cache d'une heure sur les appels reseau : navigation instantanee quand on
# revient sur une adresse deja analysee, et menagement des API publiques.
# La page Diagnostic n'utilise PAS ces enveloppes : elle doit tester en direct.
geocoder_c = st.cache_data(ttl=3600, show_spinner=False)(lib.geocoder)
ventes_dvf_c = st.cache_data(ttl=3600, show_spinner=False)(lib.ventes_dvf)
dpe_c = st.cache_data(ttl=3600, show_spinner=False)(lib.dpe_par_commune)
risques_c = st.cache_data(ttl=3600, show_spinner=False)(lib.risques)
zonage_c = st.cache_data(ttl=3600, show_spinner=False)(lib.zonage_urbanisme)

ZONES = ["A", "Abis", "B1", "B2", "C"]
DISPOSITIFS = ["BRS", "PSLA", "Vente HLM", "Neuf QPV", "Neuf libre", "Ancien libre"]


# ----------------------------------------------------------------------
# Etat partage : le profil est saisi une fois et sert partout
# ----------------------------------------------------------------------

def profil_sidebar():
    st.sidebar.header("Ton profil")
    st.sidebar.caption("Saisi une seule fois, utilise par toutes les pages.")

    p = st.session_state.setdefault("profil", {
        "rfr": 29000, "occupants": 2, "zone": "A",
        "salaire": 2570.0, "loyers": 0.0, "charges": 0.0,
        "epargne": 70000.0, "al_eligible": True, "derogation": False,
    })

    p["rfr"] = st.sidebar.number_input(
        "Revenu fiscal de reference (N-2)", 0, 300000, p["rfr"], step=500,
        help=lib.aide("rfr"))
    p["occupants"] = st.sidebar.number_input(
        "Personnes qui habiteront le logement", 1, 8, p["occupants"],
        help=lib.aide("occupants"))
    p["zone"] = st.sidebar.selectbox(
        "Zone", ZONES, index=ZONES.index(p["zone"]), help=lib.aide("zone"))
    p["salaire"] = st.sidebar.number_input(
        "Salaire net mensuel", 0.0, 30000.0, p["salaire"], step=50.0,
        help="Ton net avant impot, celui que la banque retient.")
    p["loyers"] = st.sidebar.number_input(
        "Loyers percus par mois", 0.0, 20000.0, p["loyers"], step=10.0,
        help="La banque n'en retient que 70 %, pour couvrir la vacance "
             "locative et la taxe fonciere.")
    p["charges"] = st.sidebar.number_input(
        "Mensualites de credits en cours", 0.0, 10000.0, p["charges"], step=10.0,
        help="Attention : pour un pret en differe, indique la mensualite FUTURE "
             "d'amortissement, pas celle que tu paies aujourd'hui. C'est celle-la "
             "que la banque simule.")
    p["epargne"] = st.sidebar.number_input(
        "Epargne disponible", 0.0, 1000000.0, p["epargne"], step=1000.0)
    p["al_eligible"] = st.sidebar.checkbox(
        "Salarie du prive, entreprise de 10 salaries et plus",
        p["al_eligible"], help=lib.aide("action_logement"))
    p["derogation"] = st.sidebar.checkbox(
        "Simuler la derogation HCSF", p["derogation"], help=lib.aide("hcsf"))

    cap = lib.capacite_emprunt(p["salaire"], p["loyers"], p["charges"], B,
                               p["derogation"])
    st.sidebar.divider()
    st.sidebar.metric("Capacite mensuelle disponible",
                      f"{cap['disponible']:,.0f} EUR".replace(",", " "),
                      help=lib.aide("capacite"))
    return p, cap


# ----------------------------------------------------------------------
# Page 0 : guide debutant
# ----------------------------------------------------------------------

def page_guide(p, cap):
    st.title("Guide debutant : acheter sa residence principale avec les aides")
    st.write(guide.INTRO)

    st.header("L'idee cle a comprendre d'abord")
    st.info(guide.IDEE_CLE)

    st.header("Famille 1 : les dispositifs qui baissent le prix")
    st.caption("Tu en choisis UN. Clique sur chaque fiche.")
    for d in guide.DISPOSITIFS:
        with st.expander(f"{d['nom']} - {d['resume']}"):
            c1, c2 = st.columns(2)
            c1.metric("Effet sur le prix", d["prix"])
            c2.markdown(f"**Ou le trouver :** {d['ou']}")
            st.markdown(f"**Comment ca marche.** {d['comment']}")
            st.markdown(f"**Pour qui.** {d['pour_qui']}")
            st.warning(f"**Le hic.** {d['le_hic']}")

    st.header("Famille 2 : les prets qui baissent la mensualite")
    st.caption("Ceux-la se CUMULENT tous.")
    for pr in guide.PRETS:
        with st.expander(f"{pr['nom']} - {pr['resume']}"):
            st.markdown(f"**Montant.** {pr['montant']}")
            st.markdown(f"**Conditions.** {pr['conditions']}")
            st.success(f"**Le plus.** {pr['le_plus']}")

    st.header("Lequel est fait pour toi")
    st.write(guide.CHOISIR)

    st.header("Le parcours, etape par etape")
    for titre, texte in guide.PARCOURS:
        st.markdown(f"**{titre}.** {texte}")

    st.header("Les 8 pieges qui coutent cher")
    for titre, texte in guide.PIEGES:
        with st.expander(titre):
            st.write(texte)

    st.header("Qui appeler, dans l'ordre")
    st.write(guide.QUI_APPELER)

    st.divider()
    st.success(
        "Etape suivante : renseigne ton profil dans la barre de gauche, puis "
        "ouvre le Tableau de bord pour voir a quoi TU as droit, chiffres a "
        "l'appui."
    )
    st.caption(
        "Ce guide vulgarise des regles verifiees en juillet 2026 (decret "
        "n. 2025-299, arrete du 24 fevrier 2026). Il ne remplace ni l'ADIL, "
        "ni un courtier, ni un notaire."
    )


# ----------------------------------------------------------------------
# Page 1 : accueil
# ----------------------------------------------------------------------

def page_accueil(p, cap):
    st.title("Accession aidee, tableau de bord")
    st.write(
        "Cette application repond a trois questions : a quoi ai-je droit, "
        "ce bien est-il une bonne affaire, et ou trouver les biens."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Revenus retenus", f"{cap['revenus_retenus']:,.0f} EUR".replace(",", " "))
    c2.metric("Plafond mensuel", f"{cap['plafond_mensuel']:,.0f} EUR".replace(",", " "))
    c3.metric("Disponible", f"{cap['disponible']:,.0f} EUR".replace(",", " "))

    res = lib.sous_plafond_ressources(p["rfr"], p["zone"], p["occupants"], B)
    if res["ok"]:
        st.success(
            f"Sous les plafonds de ressources : {res['rfr']:,.0f} EUR contre un "
            f"plafond de {res['plafond']:,.0f} EUR pour {p['occupants']} "
            f"personne(s) en zone {p['zone']}.".replace(",", " ")
        )
    else:
        st.error(
            f"Au-dessus des plafonds : {res['rfr']:,.0f} EUR contre "
            f"{res['plafond']:,.0f} EUR.".replace(",", " ")
        )

    tr = lib.tranche_ptz(p["rfr"], p["occupants"], p["zone"], 200000, B)
    if tr["eligible"]:
        st.info(
            f"Tranche PTZ {tr['tranche']} : quotite de "
            f"{tr['quotite']*100:.0f} % du prix, differe de "
            f"{tr['differe_ans']} ans. Revenu retenu apres division par le "
            f"coefficient familial de {tr['coefficient']} : "
            f"{tr['revenu_retenu']:,.0f} EUR.".replace(",", " ")
        )

    with st.expander("Comprendre les dispositifs en une minute"):
        for cle in ["brs", "psla", "ptz", "action_logement", "pas",
                    "differe", "redevance", "regle_ptz_autres_prets"]:
            st.markdown(f"**{cle.replace('_', ' ').upper()}** : {lib.aide(cle)}")

    st.warning(
        "Les baremes du fichier data/baremes.json sont des valeurs de travail. "
        "Verifie-les sur service-public.fr et Legifrance avant toute decision. "
        "Cette application ne remplace ni un courtier ni l'ADIL."
    )


# ----------------------------------------------------------------------
# Page 2 : simulateur de montage
# ----------------------------------------------------------------------

def page_montage(p, cap):
    st.title("Simulateur de montage")
    st.caption("Combien l'Etat te prete, et est-ce que ca passe en banque.")

    c1, c2, c3, c4 = st.columns(4)
    prix = c1.number_input("Prix du bien", 20000, 800000, 121510, step=1000)
    surface = c2.number_input("Surface habitable en m2", 9, 300, 60)
    dispositif = c3.selectbox("Dispositif", DISPOSITIFS,
                              help="Le dispositif change les frais de notaire, "
                                   "l'acces aux prets aides et la presence "
                                   "d'une redevance.")
    apport = c4.number_input("Apport", 0, 500000, 8000, step=500,
                             help=lib.aide("regle_ptz_autres_prets"))

    red_m2 = None
    if dispositif == "BRS":
        red_m2 = st.slider("Redevance en euros par m2 et par mois", 0.5, 3.0,
                           float(B["brs"]["redevance_eur_m2_mois_defaut"]), 0.05,
                           help=lib.aide("redevance"))

    type_bien = "appartement"
    if dispositif == "Neuf libre":
        type_bien = st.radio(
            "Type de bien", ["appartement", "maison"], horizontal=True,
            help="La quotite PTZ differe : 50/40/40/20 % en appartement, "
                 "30/20/20/10 % en maison individuelle neuve. BRS et PSLA "
                 "gardent la grille appartement meme en individuel.")

    m = lib.montage(prix, surface, p["rfr"], p["occupants"], p["zone"],
                    dispositif, apport, B, p["al_eligible"], red_m2,
                    type_bien)

    st.subheader("Plan de financement")
    lignes = [
        ("Pret a taux zero", m["ptz"]),
        ("Pret Action Logement a 1 %", m["action_logement"]),
        ("Pret principal", m["principal"]),
        ("Apport", m["apport"]),
    ]
    df = pd.DataFrame([{"Ligne": n, "Montant": round(v)} for n, v in lignes if v > 0])
    st.dataframe(df, width="stretch", hide_index=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Part financee sans interets ou a 1 %",
              f"{m['part_gratuite']*100:.0f} %")
    c2.metric("Frais de notaire estimes", f"{m['frais_notaire']:,.0f} EUR".replace(",", " "))
    c3.metric("Cout total de l'operation", f"{m['cout_total']:,.0f} EUR".replace(",", " "))

    if m["ptz_bride"]:
        st.warning(
            "Ton PTZ a ete plafonne au montant de tes autres prets. "
            "Reduis ton apport pour recuperer du pret a taux zero. "
            + lib.aide("regle_ptz_autres_prets")
        )

    st.subheader("Mensualites")
    c1, c2 = st.columns(2)
    c1.metric(f"Phase 1, {m['differe_ans']} premieres annees",
              f"{m['phase1']:,.0f} EUR".replace(",", " "),
              help=lib.aide("differe"))
    c2.metric("Phase 2, apres le differe",
              f"{m['phase2']:,.0f} EUR".replace(",", " "),
              help=lib.aide("phase2"))

    if m["redevance"] > 0:
        st.caption(f"Dont redevance foncière : {m['redevance']:,.0f} EUR par mois, "
                   f"comptee comme une charge par la banque et qui ne construit "
                   f"aucun capital.".replace(",", " "))

    dispo = cap["disponible"]
    if m["phase2"] <= dispo:
        st.success(f"Finançable. Marge de {dispo - m['phase2']:,.0f} EUR par mois "
                   f"au point le plus haut de l'echeancier.".replace(",", " "))
    else:
        manque = m["phase2"] - dispo
        st.error(
            f"Depassement de {manque:,.0f} EUR par mois en phase 2. "
            f"Trois leviers : rembourser un credit en cours, lisser le pret, "
            f"ou reduire le PTZ pour aplatir le profil.".replace(",", " ")
        )

    if dispositif in ("BRS", "PSLA", "Vente HLM") and not m["aide_possible"]:
        st.info("Tes ressources depassent les plafonds PSLA/BRS : ce dispositif "
                "social n'est pas accessible. Le PTZ peut rester possible sur "
                "du neuf libre si tu restes sous ses propres plafonds.")
    if dispositif != "Ancien libre" and not m["ptz_possible"]:
        st.info("Pas de PTZ dans cette configuration : revenus au-dessus du "
                "plafond d'eligibilite, ou quotite nulle.")
    if dispositif == "Ancien libre" and p["zone"] in ("A", "Abis", "B1"):
        st.warning("Ancien libre en zone tendue : ni PTZ ni Action Logement. "
                   "Le PTZ dans l'ancien n'existe qu'en zones B2 et C avec au "
                   "moins 25 % de travaux.")


# ----------------------------------------------------------------------
# Page 3 : evaluateur d'adresse
# ----------------------------------------------------------------------

def page_evaluateur(p, cap):
    st.title("Evaluateur d'adresse")
    st.caption("Colle une adresse d'annonce. Tout est interroge en direct.")

    c1, c2, c3 = st.columns([3, 1, 1])
    adresse = c1.text_input("Adresse", "129 grande rue Saint-Clair, Caluire-et-Cuire")
    prix = c2.number_input("Prix demande", 20000, 900000, 121510, step=1000)
    surface = c3.number_input("Surface m2", 9, 400, 60)
    rayon = st.slider("Rayon de comparaison en metres", 100, 2000, 400, 50,
                      help=lib.aide("dvf"))

    if not st.button("Analyser"):
        return

    g = geocoder_c(adresse)
    if not g["ok"]:
        st.error(f"Geocodage impossible : {g.get('message')}")
        return
    d = g["donnees"]
    st.write(f"**{d['label']}** - commune {d['commune']} ({d['code_insee']})")

    onglets = st.tabs(["Prix du marche", "Energie", "Risques", "Urbanisme"])

    with onglets[0]:
        v = ventes_dvf_c(d["lat"], d["lon"], rayon)
        if not v["ok"]:
            st.warning(f"DVF indisponible : {v.get('message')}")
        else:
            ventes = v["donnees"]
            dec = lib.decote(prix / surface, ventes)
            if dec["ok"]:
                c1, c2, c3 = st.columns(3)
                c1.metric("Prix au m2 du bien", f"{prix/surface:,.0f} EUR".replace(",", " "))
                c2.metric("Mediane du secteur", f"{dec['mediane_m2']:,.0f} EUR".replace(",", " "))
                c3.metric("Decote", f"{dec['decote_pct']:.0f} %",
                          help=lib.aide("decote"))
                st.caption(f"Calcul sur {dec['nb_ventes']} ventes reelles dans "
                           f"un rayon de {rayon} metres.")
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
        r = risques_c(d["code_insee"], d["lat"], d["lon"])
        if not r["ok"]:
            st.warning(r.get("message"))
        else:
            st.info(lib.aide("georisques"))
            st.dataframe(pd.DataFrame(r["donnees"]),
                         width="stretch", hide_index=True)

    with onglets[3]:
        z = zonage_c(d["lat"], d["lon"])
        if not z["ok"]:
            st.warning(z.get("message"))
        else:
            st.info(lib.aide("gpu"))
            st.dataframe(pd.DataFrame(z["donnees"]),
                         width="stretch", hide_index=True)


# ----------------------------------------------------------------------
# Page 4 : generateur de liens de recherche
# ----------------------------------------------------------------------

def page_liens(p, cap):
    st.title("Generateur de liens de recherche")
    st.write(
        "Le PSLA et le BRS ancien ne sont indexes nulle part correctement. "
        "Cette page fabrique les URL de recherche a enregistrer en alertes "
        "natives sur chaque portail. Aucune donnee n'est collectee : tu cliques "
        "les liens toi-meme, ce qui est la seule methode propre."
    )

    c1, c2, c3, c4 = st.columns(4)
    ville = c1.text_input("Ville", "Lyon")
    rayon = c2.slider("Rayon en km", 5, 60, 25)
    pmin = c3.number_input("Prix min", 0, 500000, 70000, step=5000)
    pmax = c4.number_input("Prix max", 10000, 900000, 230000, step=5000)

    if not st.button("Generer les liens"):
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
        "Sur ce marche les biens partent en quelques jours, donc consulter "
        "manuellement ne sert a rien."
    )


# ----------------------------------------------------------------------
# Page 5 : diagnostic des API
# ----------------------------------------------------------------------

def page_diagnostic(p, cap):
    st.title("Diagnostic des sources")
    st.write(
        "Les identifiants et chemins des API publiques changent regulierement. "
        "Cette page teste chaque source et te dit laquelle est cassee, pour que "
        "tu saches quoi corriger dans lib.py."
    )

    if not st.button("Lancer les tests"):
        return

    tests = []
    g = lib.geocoder("1 place Bellecour Lyon")
    tests.append(("BAN, geocodage", g["ok"], g.get("message", "")))
    if g["ok"]:
        d = g["donnees"]
        v = lib.ventes_dvf(d["lat"], d["lon"], 300)
        tests.append(("DVF, ventes reelles", v["ok"],
                      v.get("message", f"{len(v.get('donnees') or [])} ventes")))
        z = lib.zonage_urbanisme(d["lat"], d["lon"])
        tests.append(("API Carto GPU, zonage", z["ok"], z.get("message", "")))
        r = lib.risques(d["code_insee"], d["lat"], d["lon"])
        tests.append(("Georisques", r["ok"], r.get("message", "")))
        dpe = lib.dpe_par_commune(d["code_insee"], 5)
        tests.append(("ADEME, DPE", dpe["ok"], dpe.get("message", dpe.get("source", ""))))
    brs = lib.programmes_brs_grand_lyon()
    tests.append(("data.grandlyon, programmes BRS", brs["ok"],
                  brs.get("message", brs.get("source", ""))))

    for nom, ok, msg in tests:
        if ok:
            st.success(f"{nom} : fonctionne. {msg}")
        else:
            st.error(f"{nom} : echec. {msg}")


# ----------------------------------------------------------------------
# Navigation
# ----------------------------------------------------------------------

PAGES = {
    "Guide debutant": page_guide,
    "Tableau de bord": page_accueil,
    "Simulateur de montage": page_montage,
    "Evaluateur d'adresse": page_evaluateur,
    "Generateur de liens": page_liens,
    "Diagnostic des sources": page_diagnostic,
}

profil, capacite = profil_sidebar()
st.sidebar.divider()
choix = st.sidebar.radio("Navigation", list(PAGES.keys()))
PAGES[choix](profil, capacite)
