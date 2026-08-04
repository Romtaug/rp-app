"""
Recherche de logement en accession aidée - application personnelle.

Lancement en local :   streamlit run app.py
Déploiement :          Streamlit Community Cloud, dépôt privé, accès
                       restreint à ta seule adresse mail.

Architecture : lib.py appelle les API et calcule, ui.py met en forme,
guide.py porte le contenu pédagogique, app.py orchestre. Les données
lourdes sont interrogées en direct, rien n'est stocké, donc l'application
couvre toute la France sans limite de volume.
"""

import pandas as pd
import streamlit as st

import guide
import lib
import rapport
import ui

st.set_page_config(page_title="Accession aidée", page_icon="🗝",
                   layout="wide", initial_sidebar_state="expanded")
ui.injecter_styles()

B = lib.charger_baremes()
euros = ui.euros

# Cache d'une heure sur les appels réseau : revenir sur une adresse déjà
# analysée est instantané, et les API publiques sont ménagées. La page
# Diagnostic n'utilise pas ces enveloppes, elle doit tester en direct.
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

ZONES = ["A", "Abis", "B1", "B2", "C"]
DISPOSITIFS = ["BRS", "PSLA", "Vente HLM", "Neuf QPV", "Neuf libre", "Ancien libre"]


# ----------------------------------------------------------------------
# Profil, saisi une fois dans la barre latérale
# ----------------------------------------------------------------------

def profil_sidebar():
    st.sidebar.markdown("### Ton profil")
    st.sidebar.caption("Saisi une fois, utilisé par toutes les pages.")

    p = st.session_state.setdefault("profil", {
        "rfr": 29000, "occupants": 2, "zone": "A", "salaire": 2570.0,
        "loyers": 0.0, "charges": 0.0, "epargne": 70000.0,
        "al_eligible": True, "derogation": False,
    })

    p["rfr"] = st.sidebar.number_input(
        "Revenu fiscal de référence (N-2)", 0, 300000, p["rfr"], step=500,
        help=lib.aide("rfr"))
    p["occupants"] = st.sidebar.number_input(
        "Personnes qui habiteront le logement", 1, 8, p["occupants"],
        help=lib.aide("occupants"))
    p["zone"] = st.sidebar.selectbox(
        "Zone", ZONES, index=ZONES.index(p["zone"]), help=lib.aide("zone"))

    st.sidebar.markdown("### Tes revenus")
    p["salaire"] = st.sidebar.number_input(
        "Salaire net mensuel", 0.0, 30000.0, p["salaire"], step=50.0,
        help="Ton net avant impôt, celui que la banque retient.")
    p["loyers"] = st.sidebar.number_input(
        "Loyers perçus par mois", 0.0, 20000.0, p["loyers"], step=10.0,
        help="La banque n'en retient que 70 %, pour couvrir la vacance "
             "locative et la taxe foncière.")
    p["charges"] = st.sidebar.number_input(
        "Mensualités de crédits en cours", 0.0, 10000.0, p["charges"], step=10.0,
        help="Pour un prêt en différé, indique la mensualité FUTURE "
             "d'amortissement, pas celle que tu paies aujourd'hui. C'est "
             "celle-là que la banque simule.")
    p["epargne"] = st.sidebar.number_input(
        "Épargne disponible", 0.0, 1000000.0, p["epargne"], step=1000.0)

    p["al_eligible"] = st.sidebar.checkbox(
        "Salarié du privé, 10 salariés et plus", p["al_eligible"],
        help=lib.aide("action_logement"))
    p["derogation"] = st.sidebar.checkbox(
        "Simuler la dérogation HCSF", p["derogation"], help=lib.aide("hcsf"))

    cap = lib.capacite_emprunt(p["salaire"], p["loyers"], p["charges"], B,
                               p["derogation"])
    st.sidebar.divider()
    st.sidebar.metric("Capacité mensuelle", euros(cap["disponible"]),
                      help=lib.aide("capacite"))
    return p, cap


# ----------------------------------------------------------------------
# Guide débutant
# ----------------------------------------------------------------------

def page_guide(p, cap):
    st.title("Acheter sa résidence principale avec les aides")
    ui.verdict("neutre",
               "Deux familles à ne pas confondre, et elles se cumulent",
               "Les dispositifs font baisser le PRIX du logement, et tu en "
               "choisis un seul. Les prêts aidés font baisser la MENSUALITÉ, "
               "et tu les empiles tous les trois.", eyebrow="Guide débutant")
    st.write(guide.INTRO)

    st.header("L'idée clé")
    st.write(guide.IDEE_CLE)

    st.header("Les dispositifs qui baissent le prix")
    st.caption("Tu en choisis un seul. Déplie chaque fiche.")
    for d in guide.DISPOSITIFS:
        with st.expander(f"{d['nom']} · {d['resume']}"):
            st.metric("Effet sur le prix", d["prix"])
            st.markdown(f"**Comment ça marche.** {d['comment']}")
            st.markdown(f"**Pour qui.** {d['pour_qui']}")
            ui.verdict("non", "Le hic", d["le_hic"])
            st.markdown(f"**Où le trouver.** {d['ou']}")

    st.header("Les prêts qui baissent la mensualité")
    st.caption("Ceux-là se cumulent tous les trois.")
    for pr in guide.PRETS:
        with st.expander(f"{pr['nom']} · {pr['resume']}"):
            st.markdown(f"**Montant.** {pr['montant']}")
            st.markdown(f"**Conditions.** {pr['conditions']}")
            ui.verdict("oui", "L'atout", pr["le_plus"])

    st.header("Lequel est fait pour toi")
    st.write(guide.CHOISIR)

    st.header("Le parcours")
    for titre, texte in guide.PARCOURS:
        st.markdown(f"**{titre}.** {texte}")

    st.header("Les huit pièges qui coûtent cher")
    for titre, texte in guide.PIEGES:
        with st.expander(titre):
            st.write(texte)

    st.header("La visite, ce qu'on regarde vraiment")
    ui.note("Les quatre premières lignes se préparent avant même de "
            "téléphoner. La dernière est la visite la plus rentable, et elle "
            "est gratuite.")
    for titre, texte in guide.VISITE:
        with st.expander(titre):
            st.write(texte)

    st.header("L'offre et le compromis")
    ui.verdict("non", "Une offre acceptée t'engage, pas le vendeur",
               "Toute condition non écrite est un risque que tu portes seul. "
               "Les cinq points ci-dessous sont ceux qui coûtent le plus cher "
               "quand on les découvre trop tard.")
    for titre, texte in guide.OFFRE:
        with st.expander(titre):
            st.write(texte)

    st.header("Le coût réel, au-delà du prix affiché")
    for poste, texte in guide.FRAIS_REELS:
        st.markdown(f"**{poste}.** {texte}")

    st.header("Négocier avec la banque")
    ui.verdict("oui", "Le taux n'est pas la seule ligne négociable",
               "L'assurance emprunteur pèse souvent plus de 10 000 € sur la "
               "durée totale, et c'est la ligne où tu as le plus de marge.")
    for titre, texte in guide.NEGOCIER_BANQUE:
        with st.expander(titre):
            st.write(texte)

    st.header("Qui appeler, dans l'ordre")
    st.write(guide.QUI_APPELER)

    st.header("Ta checklist, de la recherche aux clés")
    lignes_txt = ["CHECKLIST ACHAT DE RESIDENCE PRINCIPALE", "=" * 46, ""]
    for phase, elements in guide.CHECKLIST:
        st.markdown(f"**{phase}**")
        for e in elements:
            st.checkbox(e, key=f"chk_{phase}_{e}"[:120])
        lignes_txt.append(phase.upper())
        lignes_txt += [f"  [ ] {e}" for e in elements]
        lignes_txt.append("")
    st.download_button("Télécharger la checklist",
                       "\n".join(lignes_txt),
                       file_name="checklist-achat-rp.txt", mime="text/plain")

    ui.note("Ce guide vulgarise des règles vérifiées en juillet 2026 "
            "(décret n° 2025-299, arrêté du 24 février 2026). Il ne remplace "
            "ni l'ADIL, ni un courtier, ni un notaire.")


# ----------------------------------------------------------------------
# Tableau de bord
# ----------------------------------------------------------------------

def page_accueil(p, cap):
    st.title("Tableau de bord")

    res = lib.sous_plafond_ressources(p["rfr"], p["zone"], p["occupants"], B)
    tr = lib.tranche_ptz(p["rfr"], p["occupants"], p["zone"], 200000, B)

    if res["ok"] and tr["eligible"]:
        ui.verdict("oui", f"Tu es éligible, tranche PTZ {tr['tranche']}",
                   f"Quotité de {tr['quotite'] * 100:.0f} % du prix et différé "
                   f"de {tr['differe_ans']} ans. Ton revenu fiscal de "
                   f"{euros(res['rfr'])} reste sous le plafond de "
                   f"{euros(res['plafond'])} pour {p['occupants']} personne(s) "
                   f"en zone {p['zone']}.", eyebrow="Ta situation")
    elif tr["eligible"]:
        ui.verdict("non", "Au-dessus des plafonds sociaux",
                   f"{euros(res['rfr'])} contre un plafond de "
                   f"{euros(res['plafond'])}. Le BRS, le PSLA et la vente HLM "
                   f"te sont fermés, mais le PTZ reste ouvert sur du neuf "
                   f"libre, en tranche {tr['tranche']}.",
                   eyebrow="Ta situation")
    else:
        ui.verdict("non", "Au-dessus des plafonds, PTZ compris",
                   f"Revenu fiscal de {euros(res['rfr'])} pour un plafond "
                   f"d'éligibilité PTZ de "
                   f"{euros(tr.get('plafond_eligibilite', 0))}.",
                   eyebrow="Ta situation")

    c1, c2, c3 = st.columns(3)
    c1.metric("Revenus retenus", euros(cap["revenus_retenus"]),
              help="Salaire net plus 70 % des loyers perçus.")
    c2.metric(f"Plafond à {cap['taux_applique'] * 100:.0f} %",
              euros(cap["plafond_mensuel"]), help=lib.aide("hcsf"))
    c3.metric("Disponible", euros(cap["disponible"]),
              delta=(f"- {euros(cap['charges_existantes'])} de charges"
                     if cap["charges_existantes"] else None),
              delta_color="inverse", help=lib.aide("capacite"))

    st.header("Ce que ça veut dire, un terme par ligne")
    for cle in ["ptz", "differe", "phase2", "action_logement", "pas",
                "redevance", "regle_ptz_autres_prets"]:
        with st.expander(cle.replace("_", " ").upper()):
            st.write(lib.aide(cle))

    ui.note("Les barèmes de data/baremes.json ont été vérifiés en juillet 2026 "
            "et sont surveillés chaque lundi. Cette application ne remplace ni "
            "un courtier ni l'ADIL.")


# ----------------------------------------------------------------------
# Simulateur de montage
# ----------------------------------------------------------------------

def page_montage(p, cap):
    st.title("Simulateur de montage")

    c1, c2 = st.columns(2)
    prix = c1.number_input("Prix du bien", 20000, 800000, 121510, step=1000)
    surface = c2.number_input("Surface habitable en m²", 9, 300, 60)
    c1, c2 = st.columns(2)
    dispositif = c1.selectbox("Dispositif", DISPOSITIFS,
                              help="Il change les frais de notaire, l'accès "
                                   "aux prêts aidés et la présence d'une "
                                   "redevance.")
    apport = c2.number_input("Apport", 0, 500000, 8000, step=500,
                             help=lib.aide("regle_ptz_autres_prets"))

    red_m2, type_bien = None, "appartement"
    if dispositif == "BRS":
        red_m2 = st.slider("Redevance en euros par m² et par mois", 0.5, 3.0,
                           float(B["brs"]["redevance_eur_m2_mois_defaut"]),
                           0.05, help=lib.aide("redevance"))
    if dispositif == "Neuf libre":
        type_bien = st.radio("Type de bien", ["appartement", "maison"],
                             horizontal=True,
                             help="Quotité PTZ 50/40/40/20 % en appartement, "
                                  "30/20/20/10 % en maison individuelle. Le "
                                  "BRS et le PSLA gardent la grille "
                                  "appartement même en individuel.")

    m = lib.montage(prix, surface, p["rfr"], p["occupants"], p["zone"],
                    dispositif, apport, B, p["al_eligible"], red_m2, type_bien)
    dispo = cap["disponible"]
    marge = dispo - m["phase2"]

    st.divider()
    if marge >= 0:
        ui.verdict("oui",
                   f"Finançable · {euros(m['phase2'])} par mois au point le "
                   f"plus haut",
                   f"Il te reste {euros(marge)} de marge par mois quand le "
                   f"différé du prêt à taux zéro se termine, l'échéance que la "
                   f"banque teste. L'État finance "
                   f"{m['part_gratuite'] * 100:.0f} % de l'opération sans "
                   f"intérêts ou à 1 %.", eyebrow="Verdict")
    else:
        ui.verdict("non",
                   f"Dépassement de {euros(-marge)} par mois en phase 2",
                   "Trois leviers : rembourser un crédit en cours, faire "
                   "lisser le prêt par la banque, ou réduire le prêt à taux "
                   "zéro pour aplatir le profil.", eyebrow="Verdict")

    st.header("Le plan de financement")
    ui.barre_strates([
        ("Prêt à taux zéro", m["ptz"], ui.OR, True),
        ("Action Logement à 1 %", m["action_logement"], "#F0D48A", True),
        ("Prêt principal", m["principal"], ui.BATI, False),
        ("Apport", m["apport"], ui.BRUME, False),
    ], m["prix"])
    ui.note("En or, tout ce que l'État te prête gratuitement ou à 1 %. En "
            "pétrole, ce que tu finances au taux du marché.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Sans intérêts ou à 1 %", f"{m['part_gratuite'] * 100:.0f} %",
              help="Part du prix couverte par le PTZ et Action Logement.")
    c2.metric("Frais de notaire", euros(m["frais_notaire"]),
              help="Environ 3 % en BRS, PSLA et neuf, contre 7,5 % dans "
                   "l'ancien libre.")
    c3.metric("Coût total", euros(m["cout_total"]),
              help="Prix, frais de notaire et frais de garantie.")

    if m["ptz_bride"]:
        ui.verdict("non", "Ton apport bride ton prêt à taux zéro",
                   lib.aide("regle_ptz_autres_prets")
                   + " Réduis l'apport et le PTZ remonte.")

    st.header("Ton échéancier sur 25 ans")
    ui.profil_mensualites(m["phase1"], m["phase2"], m["differe_ans"], dispo)
    c1, c2 = st.columns(2)
    c1.metric(f"Phase 1, {m['differe_ans']} premières années",
              euros(m["phase1"]), help=lib.aide("differe"))
    c2.metric("Phase 2, après le différé", euros(m["phase2"]),
              help=lib.aide("phase2"))
    if m["redevance"] > 0:
        ui.note(f"Dont {euros(m['redevance'])} de redevance foncière par mois, "
                f"comptée comme une charge par la banque et qui ne construit "
                f"aucun capital.")

    if dispositif in ("BRS", "PSLA", "Vente HLM") and not m["aide_possible"]:
        ui.note("Tes ressources dépassent les plafonds PSLA et BRS : ce "
                "dispositif social ne t'est pas accessible.")
    if dispositif == "Ancien libre" and p["zone"] in ("A", "Abis", "B1"):
        ui.note("Ancien libre en zone tendue : ni PTZ ni Action Logement. Le "
                "PTZ dans l'ancien n'existe qu'en zones B2 et C avec au moins "
                "25 % de travaux.")

    st.divider()
    st.subheader("Emporter ce chiffrage")
    ui.note("Un classeur de sept onglets, avec graphiques et formules vivantes : "
            "change le prix dans l'onglet Financement et tout se recalcule. "
            "C'est le document à présenter au courtier.")
    st.download_button(
        "Télécharger le rapport Excel",
        rapport.construire(prix, surface, dispositif, m, cap, lib.GLOSSAIRE,
                           guide.CHECKLIST, B,
                           red_m2 or B["brs"]["redevance_eur_m2_mois_defaut"]),
        file_name=f"chiffrage-{dispositif.lower().replace(' ', '-')}-"
                  f"{int(prix)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument."
             "spreadsheetml.sheet")


# ----------------------------------------------------------------------
# Évaluateur d'adresse
# ----------------------------------------------------------------------

def page_evaluateur(p, cap):
    st.title("Évaluateur d'adresse")
    st.caption("Colle l'adresse d'une annonce. Tout est interrogé en direct.")

    adresse = st.text_input("Adresse",
                            "129 grande rue Saint-Clair, Caluire-et-Cuire")
    c1, c2 = st.columns(2)
    prix = c1.number_input("Prix demandé", 20000, 900000, 121510, step=1000)
    surface = c2.number_input("Surface m²", 9, 400, 60)
    c1, c2 = st.columns(2)
    dispositif = c1.selectbox("Dispositif", DISPOSITIFS)
    rayon = c2.slider("Rayon de comparaison en mètres", 100, 2000, 400, 50,
                      help=lib.aide("dvf"))

    if not st.button("Analyser cette adresse"):
        return

    g = geocoder_c(adresse)
    if not g["ok"]:
        ui.verdict("non", "Adresse introuvable",
                   f"{g.get('message')} Vérifie l'orthographe ou ajoute le "
                   f"code postal.")
        return
    d = g["donnees"]

    v = ventes_dvf_c(d["lat"], d["lon"], rayon, d["code_insee"])
    dec = lib.decote(prix / surface, v["donnees"]) if v["ok"] else None
    m = lib.montage(prix, surface, p["rfr"], p["occupants"], p["zone"],
                    dispositif, 8000, B, p["al_eligible"])
    marge = cap["disponible"] - m["phase2"]

    if dec and dec.get("ok"):
        signe = "sous" if dec["decote_pct"] > 0 else "au-dessus de"
        detail = (f"{abs(dec['decote_pct']):.0f} % {signe} la médiane du "
                  f"secteur, calculée sur {dec['nb_ventes']} ventes réelles "
                  f"dans un rayon de {rayon} mètres. Mensualité estimée en "
                  f"{dispositif} : {euros(m['phase2'])} au point le plus haut.")
    else:
        detail = (f"Pas assez de ventes comparables pour juger le prix. "
                  f"Mensualité estimée en {dispositif} : "
                  f"{euros(m['phase2'])} au point le plus haut.")
    ui.verdict("oui" if marge >= 0 else "non",
               f"{d['commune']} · {euros(prix / surface)} par m²",
               detail, eyebrow=d["label"])

    fc = commune_c(d["code_insee"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Prix au m²", euros(prix / surface))
    c2.metric("Médiane du secteur",
              euros(dec["mediane_m2"]) if dec and dec.get("ok") else "n/d",
              help=lib.aide("decote"))
    c3.metric("Population",
              f"{fc['donnees']['population']:,}".replace(",", "\u202f")
              if fc["ok"] and fc["donnees"].get("population") else "n/d")

    onglets = st.tabs(["Marché", "Énergie", "Risques", "Urbanisme",
                       "Vie de quartier"])

    with onglets[0]:
        if not v["ok"]:
            ui.verdict("non", "Ventes réelles indisponibles", v.get("message"))
        else:
            st.caption(f"Source : {v['source']}")
            st.dataframe(ui.table_ventes(v["donnees"]), width="stretch",
                         hide_index=True)

    with onglets[1]:
        dpe = dpe_c(d["code_insee"])
        if not dpe["ok"]:
            ui.verdict("non", "Diagnostics indisponibles", dpe.get("message"))
        else:
            rep = ui.repartition_dpe(dpe["donnees"])
            if rep:
                ui.barre_dpe(rep)
            ui.note(lib.aide("dpe"))
            st.dataframe(ui.table_dpe(dpe["donnees"]), width="stretch",
                         hide_index=True)

    with onglets[2]:
        a = argile_c(d["lat"], d["lon"])
        r2 = radon_c(d["code_insee"])
        c1, c2 = st.columns(2)
        c1.metric("Argile",
                  str(a["donnees"]["exposition"]).capitalize()
                  if a["ok"] else "n/d", help=lib.aide("argile"))
        c2.metric("Radon",
                  f"classe {r2['donnees']['classe']}"
                  if r2["ok"] and r2["donnees"]["classe"] else "n/d",
                  help=lib.aide("radon"))
        r = risques_c(d["code_insee"], d["lat"], d["lon"])
        if not r["ok"]:
            ui.verdict("non", "Risques indisponibles", r.get("message"))
        else:
            ui.note(lib.aide("georisques"))
            st.dataframe(ui.table_risques(r["donnees"]), width="stretch",
                         hide_index=True)

    with onglets[3]:
        pc = parcelle_c(d["lat"], d["lon"])
        if pc["ok"]:
            c1, c2 = st.columns(2)
            c1.metric("Parcelle",
                      f"{pc['donnees'].get('section') or '?'} "
                      f"{pc['donnees'].get('numero') or ''}".strip(),
                      help=lib.aide("parcelle"))
            cont = pc["donnees"].get("contenance_m2")
            c2.metric("Contenance du terrain",
                      f"{cont:,} m²".replace(",", "\u202f") if cont else "n/d")
        z = zonage_c(d["lat"], d["lon"])
        if not z["ok"]:
            ui.verdict("non", "Zonage indisponible", z.get("message"))
        else:
            ui.note(lib.aide("gpu"))
            st.dataframe(ui.table_zonage(z["donnees"]), width="stretch",
                         hide_index=True)

    with onglets[4]:
        o = osm_c(d["lat"], d["lon"], 600)
        if not o["ok"]:
            ui.verdict("non", "Équipements indisponibles", o.get("message"))
        else:
            st.caption(f"Dans un rayon de {o['rayon_m']} mètres · {o['source']}")
            st.dataframe(ui.table_equipements(o["donnees"]), width="stretch",
                         hide_index=True)
        e = ecoles_c(d["code_insee"])
        if not e["ok"]:
            ui.verdict("non", "Établissements indisponibles", e.get("message"))
        else:
            ui.note(lib.aide("ips"))
            st.dataframe(ui.table_ecoles(e["donnees"]), width="stretch",
                         hide_index=True)

    blocs = []
    infos_commune = []
    if fc["ok"]:
        for cle, lib_ in [("population", "Population"),
                          ("densite_hab_km2", "Densité (hab/km²)"),
                          ("surface_km2", "Superficie (km²)")]:
            if fc["donnees"].get(cle):
                infos_commune.append((lib_, fc["donnees"][cle]))
    if infos_commune:
        blocs.append(("La commune", infos_commune))
    risques_bloc = []
    if a["ok"]:
        risques_bloc.append(("Exposition au retrait-gonflement des argiles",
                             a["donnees"]["exposition"]))
    if r2["ok"] and r2["donnees"]["classe"]:
        risques_bloc.append(("Classe de potentiel radon",
                             r2["donnees"]["classe"]))
    if risques_bloc:
        blocs.append(("Les risques", risques_bloc))
    dpe_res = dpe_c(d["code_insee"])
    if dpe_res["ok"]:
        rep = ui.repartition_dpe(dpe_res["donnees"])
        if rep:
            blocs.append(("Étiquettes énergie de la commune",
                          [(f"Classe {l}", n) for l, n in sorted(rep.items())]))
    osm_res = osm_c(d["lat"], d["lon"], 600)
    if osm_res["ok"]:
        blocs.append(("Équipements à moins de 600 mètres",
                      [(x["categorie"],
                        f"{x['nombre']} dont le plus proche à "
                        f"{x['plus_proche_m']} m" if x["plus_proche_m"]
                        else "aucun") for x in osm_res["donnees"]]))
    ecoles_res = ecoles_c(d["code_insee"])
    if ecoles_res["ok"]:
        avec_ips = [x for x in ecoles_res["donnees"] if x.get("ips")]
        if avec_ips:
            blocs.append(("Établissements et indice de position sociale",
                          [(x["établissement"], x["ips"])
                           for x in avec_ips[:12]]))

    st.divider()
    st.subheader("Emporter la fiche de ce bien")
    ui.note("Sept onglets : synthèse avec le verdict, modèle de financement "
            "recalculable, échéancier graphique, les ventes réelles du "
            "quartier, le contexte de l'adresse, ta checklist et le lexique.")
    st.download_button(
        "Télécharger le rapport Excel",
        rapport.construire(prix, surface, dispositif, m, cap, lib.GLOSSAIRE,
                           guide.CHECKLIST, B,
                           B["brs"]["redevance_eur_m2_mois_defaut"],
                           d["label"], d["commune"], dec,
                           v["donnees"] if v["ok"] else None, blocs),
        file_name=f"fiche-{d['commune'].lower().replace(' ', '-')}-"
                  f"{int(prix)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument."
             "spreadsheetml.sheet")


# ----------------------------------------------------------------------
# Générateur de liens
# ----------------------------------------------------------------------

def page_liens(p, cap):
    st.title("Générateur de liens de recherche")
    ui.verdict("neutre", "Le PSLA et le BRS ancien ne sont indexés nulle part",
               "Cette page fabrique les URL à enregistrer en alertes sur "
               "chaque portail, puis liste les sites officiels qui diffusent "
               "des annonces BRS près de chez toi. Aucune donnée n'est "
               "collectée : tu ouvres les liens toi-même.")

    c1, c2 = st.columns(2)
    ville = c1.text_input("Ville", "Lyon")
    rayon = c2.slider("Rayon en km", 5, 60, 25)
    c1, c2 = st.columns(2)
    pmin = c1.number_input("Prix minimum", 0, 500000, 70000, step=5000)
    pmax = c2.number_input("Prix maximum", 10000, 900000, 230000, step=5000)

    if not st.button("Générer les liens"):
        return

    g = geocoder_c(ville)
    if not g["ok"]:
        ui.verdict("non", "Ville introuvable", "Vérifie l'orthographe.")
        return
    d = g["donnees"]

    st.header("Tes alertes à enregistrer")
    for l in lib.liens_recherche(d["commune"], d["lat"], d["lon"],
                                 d["code_insee"], rayon, pmin, pmax):
        with st.container(border=True):
            st.markdown(f"**{l['mot_cle']}** · {l['explication']}")
            c1, c2, c3 = st.columns(3)
            c1.link_button("Leboncoin", l["leboncoin"], width="stretch")
            c2.link_button("SeLoger", l["seloger"], width="stretch")
            c3.link_button("Bienici", l["bienici"], width="stretch")
    ui.note("Ouvre chaque lien et enregistre-le en alerte avec notification. "
            "Sur ce marché les biens partent en quelques jours : consulter à "
            "la main ne sert à rien.")

    st.header(f"Sites officiels qui diffusent du BRS près de {d['commune']}")
    sites = boris_sites_c(d["lat"], d["lon"], rayon)
    if not sites["ok"]:
        ui.verdict("non", "Annuaire BoRiS indisponible", sites.get("message"))
        return
    if not sites["donnees"]:
        ui.note("Aucun site recensé dans ce rayon. Élargis le rayon, ou "
                "consulte la carte nationale sur boris.beta.gouv.fr.")
        return

    # BoRiS renvoie une entrée par commune : le même opérateur apparaît donc
    # jusqu'à dix fois. On regroupe par opérateur et on liste ses communes,
    # ce qui est à la fois plus court et plus informatif.
    groupes = {}
    for s in sites["donnees"]:
        nom = (s.get("distributorName") or s.get("ofsName") or "Site").strip()
        url = (s.get("source") or "").strip()
        cle = (nom, url)
        g = groupes.setdefault(cle, {"nom": nom, "url": url,
                                     "ofs": set(), "communes": []})
        if s.get("ofsName"):
            g["ofs"].add(s["ofsName"].strip())
        ville_s = " ".join(x for x in [str(s.get("city") or "").strip(),
                                       str(s.get("zipcode") or "").strip()] if x)
        if ville_s and ville_s not in g["communes"]:
            g["communes"].append(ville_s)

    st.caption(f"Source : {sites['source']} · {len(groupes)} opérateurs "
               f"distincts sur {len(sites['donnees'])} entrées")
    for g in sorted(groupes.values(), key=lambda x: -len(x["communes"])):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{g['nom']}**")
            if g["ofs"]:
                c1.caption("Foncier porté par " + ", ".join(sorted(g["ofs"])))
            if g["communes"]:
                visibles = g["communes"][:6]
                suite = (f" et {len(g['communes']) - 6} autre(s)"
                         if len(g["communes"]) > 6 else "")
                c1.caption("Présent à " + ", ".join(visibles) + suite)
            if g["url"]:
                c2.link_button("Ouvrir", g["url"], width="stretch")
            else:
                c2.caption("Pas d'adresse web publiée")

    # La liste des organismes de foncier solidaire se déduit des entrées
    # ci-dessus, ce qui évite un appel supplémentaire et un tableau vide.
    tous_ofs = sorted({o for g in groupes.values() for o in g["ofs"]})
    if tous_ofs:
        st.header("Les organismes de foncier solidaire compétents")
        ui.note("C'est chez eux que tu t'inscris sur liste de candidats, et "
                "c'est le canal qui attrape les biens avant publication. "
                "Demande explicitement les logements déjà livrés et "
                "disponibles, pas seulement les prochains lancements.")
        for o in tous_ofs:
            st.markdown(f"- **{o}**")


# ----------------------------------------------------------------------
# Diagnostic des sources
# ----------------------------------------------------------------------

def page_diagnostic(p, cap):
    st.title("Diagnostic des sources")
    ui.note("Les chemins des API publiques changent régulièrement. Cette page "
            "teste chaque source en direct, sans cache, et nomme celle qui est "
            "cassée pour que tu saches quoi corriger dans lib.py.")

    if not st.button("Lancer les tests"):
        return

    tests = []
    with st.spinner("Interrogation des sources..."):
        g = lib.geocoder("1 place Bellecour Lyon")
        tests.append(("Géoplateforme, géocodage", g["ok"], g.get("message", "")))
        if g["ok"]:
            d = g["donnees"]
            for libelle, res in [
                ("DVF, ventes réelles",
                 lib.ventes_dvf(d["lat"], d["lon"], 300, d["code_insee"])),
                ("API Carto GPU, zonage",
                 lib.zonage_urbanisme(d["lat"], d["lon"])),
                ("Géorisques, rapport",
                 lib.risques(d["code_insee"], d["lat"], d["lon"])),
                ("Géorisques, argile", lib.argile_rga(d["lat"], d["lon"])),
                ("Géorisques, radon", lib.radon(d["code_insee"])),
                ("ADEME, DPE", lib.dpe_par_commune(d["code_insee"], 5)),
                ("geo.api.gouv.fr, commune",
                 lib.fiche_commune(d["code_insee"])),
                ("API Carto, cadastre",
                 lib.parcelle_cadastre(d["lat"], d["lon"])),
                ("OpenStreetMap Overpass",
                 lib.equipements_osm(d["lat"], d["lon"], 400)),
                ("Éducation nationale, IPS",
                 lib.ecoles_education(d["code_insee"], 5)),
                ("BoRiS, sites d'annonces",
                 lib.boris_sites_annonces(d["lat"], d["lon"], 30, 5)),
            ]:
                tests.append((libelle, res["ok"],
                              res.get("message", res.get("source", ""))))
        brs = lib.programmes_brs_grand_lyon(autoriser_repli=False)
        if not brs["ok"]:
            secours = lib.programmes_brs_grand_lyon(autoriser_repli=True)
            if secours["ok"]:
                brs = {"ok": True,
                       "message": ("API injoignable depuis Streamlit, mais le "
                                   "repli local fonctionne : "
                                   f"{len(secours['donnees'])} programmes lus "
                                   "dans l'instantané de la veille")}
        tests.append(("data.grandlyon, programmes BRS", brs["ok"],
                      brs.get("message", brs.get("source", ""))))

    ok = sum(1 for _, o, _ in tests if o)
    ui.verdict("oui" if ok == len(tests) else "non",
               f"{ok} sources sur {len(tests)} répondent",
               "Tout fonctionne." if ok == len(tests) else
               "Les échecs sont détaillés ci-dessous. Un timeout signifie que "
               "l'endpoint est bon mais le serveur lent : relance avant de "
               "modifier quoi que ce soit.", eyebrow="Diagnostic")

    for nom, o, msg in tests:
        (st.success if o else st.error)(
            f"{nom} : {msg or ('opérationnel' if o else 'échec')}")


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
choix = st.sidebar.radio("Navigation", list(PAGES.keys()),
                         label_visibility="collapsed")
PAGES[choix](profil, capacite)
