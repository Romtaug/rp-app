"""
Couche présentation : styles, composants visuels et nettoyage des tableaux.

Direction graphique : papier de géomètre. Le sujet de l'application est le
foncier, et le bail réel solidaire sépare littéralement le sol du bâti :
d'où une palette de plan cadastral et un élément signature en strates.

  Papier    #EDF1F4   fond, bleu-gris de plan
  Encre     #16303F   texte et structure
  Trait     #C3D0D8   filets
  Bâti      #1F4E5F   ce que tu finances toi-même
  Or        #E8B33D   tout ce que l'État prête gratuitement ou à 1 %
  Favorable #2E7D5B   verdict positif
  Sanguine  #B3402E   verdict négatif

Tous les montants sont composés en IBM Plex Mono à chiffres tabulaires,
pour qu'ils s'alignent en colonne et se lisent comme un relevé.
"""

import pandas as pd
import streamlit as st

PAPIER = "#EDF1F4"
ENCRE = "#16303F"
TRAIT = "#C3D0D8"
BATI = "#1F4E5F"
OR = "#E8B33D"
FAVORABLE = "#2E7D5B"
SANGUINE = "#B3402E"
BRUME = "#6B8290"


def euros(x, decimales=0) -> str:
    """Montant en euros, espace insécable comme séparateur de milliers."""
    try:
        return f"{x:,.{decimales}f}".replace(",", "\u202f") + " €"
    except (TypeError, ValueError):
        return "n/d"


# ----------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------

def injecter_styles() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        .stApp {{ background: {PAPIER}; }}

        .block-container {{
            max-width: 1080px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }}

        .stApp, .stApp p, .stApp li, .stApp label, .stMarkdown {{
            font-family: 'IBM Plex Sans', system-ui, sans-serif;
            color: {ENCRE};
        }}

        h1, h2, h3 {{
            font-family: 'Bricolage Grotesque', system-ui, sans-serif;
            color: {ENCRE};
            letter-spacing: -0.015em;
        }}
        h1 {{ font-size: clamp(1.6rem, 4vw, 2.2rem); font-weight: 700; }}
        h2 {{
            font-size: clamp(1.15rem, 2.6vw, 1.4rem);
            font-weight: 600;
            margin-top: 2.2rem;
            padding-bottom: .35rem;
            border-bottom: 1px solid {TRAIT};
        }}
        h3 {{ font-size: 1.05rem; font-weight: 600; }}

        /* Barre latérale : le poste de réglage */
        section[data-testid="stSidebar"] {{
            background: #E3E9ED;
            border-right: 1px solid {TRAIT};
        }}
        section[data-testid="stSidebar"] * {{ color: {ENCRE}; }}

        /* Tous les chiffres en mono tabulaire */
        [data-testid="stMetricValue"], .chiffre, .mono {{
            font-family: 'IBM Plex Mono', ui-monospace, monospace;
            font-variant-numeric: tabular-nums;
            font-feature-settings: "tnum" 1;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.45rem; font-weight: 500; color: {ENCRE};
        }}
        [data-testid="stMetricLabel"] {{
            font-size: .78rem; text-transform: uppercase;
            letter-spacing: .06em; color: {BRUME};
        }}

        /* Surfaces plates, filets fins, angles discrets */
        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"] {{
            background: #FFFFFF;
            border: 1px solid {TRAIT};
            border-radius: 4px;
        }}
        div[data-testid="stMetric"] {{ padding: .85rem 1rem; }}

        /* Boutons : la couleur est posee sur le bouton ET sur tous ses
           enfants, car Streamlit enveloppe le libelle dans un <p> qui
           heriterait sinon de la couleur de texte globale. */
        .stButton > button, .stDownloadButton > button,
        .stFormSubmitButton > button {{
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
            border-radius: 4px;
            border: 1px solid {ENCRE};
            background: {ENCRE};
            transition: background .15s ease;
        }}
        .stButton > button, .stButton > button *,
        .stDownloadButton > button, .stDownloadButton > button *,
        .stFormSubmitButton > button, .stFormSubmitButton > button * {{
            color: {PAPIER} !important;
            fill: {PAPIER} !important;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background: {BATI}; border-color: {BATI};
        }}
        .stLinkButton > a {{
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
            border-radius: 4px;
            border: 1px solid {ENCRE};
            background: transparent;
        }}
        .stLinkButton > a, .stLinkButton > a * {{
            color: {ENCRE} !important;
        }}
        .stLinkButton > a:hover {{ background: #DDE5EA; }}

        .stTabs [data-baseweb="tab-list"] {{ gap: .2rem; border-bottom: 1px solid {TRAIT}; }}
        .stTabs [data-baseweb="tab"] {{
            font-family: 'IBM Plex Sans', sans-serif; font-weight: 500;
        }}

        /* --- Composants sur mesure --- */

        .verdict {{
            border-radius: 4px;
            padding: 1.1rem 1.3rem;
            margin: 0 0 1.6rem 0;
            animation: apparait .2s ease-out;
        }}
        @keyframes apparait {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
        @media (prefers-reduced-motion: reduce) {{
            .verdict {{ animation: none }}
        }}
        .verdict .eyebrow {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: .7rem; text-transform: uppercase;
            letter-spacing: .12em; opacity: .85;
        }}
        .verdict .titre {{
            font-family: 'Bricolage Grotesque', sans-serif;
            font-size: clamp(1.25rem, 3.4vw, 1.7rem);
            font-weight: 700; line-height: 1.15; margin: .2rem 0 .35rem;
        }}
        .verdict .detail {{ font-size: .92rem; opacity: .95; }}
        .verdict.oui {{ background: {FAVORABLE}; color: #F2F7F4; }}
        .verdict.non {{ background: {SANGUINE}; color: #FBF3F1; }}
        .verdict.neutre {{
            background: #FFFFFF; color: {ENCRE}; border: 1px solid {TRAIT};
        }}

        .strates {{ display: flex; height: 34px; border-radius: 3px;
                    overflow: hidden; border: 1px solid {ENCRE}; }}
        .strates > div {{ display: flex; align-items: center;
                          justify-content: center; }}
        .strates .part {{
            font-family: 'IBM Plex Mono', monospace; font-size: .72rem;
            font-weight: 600; white-space: nowrap;
        }}
        .legende {{ display: flex; flex-wrap: wrap; gap: 1.1rem;
                    margin-top: .7rem; }}
        .legende span.item {{ display: inline-flex; align-items: center;
                              gap: .45rem; font-size: .84rem; }}
        .legende i {{ width: 10px; height: 10px; border-radius: 2px;
                      display: inline-block; }}
        .legende b {{ font-family: 'IBM Plex Mono', monospace;
                      font-variant-numeric: tabular-nums; font-weight: 600; }}

        .dpe {{
            font-family: 'IBM Plex Mono', monospace; font-weight: 700;
            font-size: .8rem; padding: .18rem .5rem; border-radius: 3px;
            color: #10221B;
        }}

        .note {{
            font-size: .84rem; color: {BRUME};
            border-left: 2px solid {TRAIT}; padding-left: .7rem;
            margin: .5rem 0 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Composants
# ----------------------------------------------------------------------

def verdict(etat: str, titre: str, detail: str = "", eyebrow: str = "") -> None:
    """Bandeau de verdict. etat vaut oui, non ou neutre."""
    st.markdown(
        f'<div class="verdict {etat}">'
        f'{f"<div class=eyebrow>{eyebrow}</div>" if eyebrow else ""}'
        f'<div class="titre">{titre}</div>'
        f'{f"<div class=detail>{detail}</div>" if detail else ""}'
        f"</div>",
        unsafe_allow_html=True,
    )


def barre_strates(segments, total: float) -> None:
    """Élément signature : le plan de financement en strates.

    segments : liste de tuples (libellé, montant, couleur, texte_sombre).
    L'or signale tout ce qui est prêté gratuitement ou à 1 %.
    """
    segments = [s for s in segments if s[1] > 0]
    if not segments or total <= 0:
        return
    barres, legende = "", ""
    for libelle, montant, couleur, sombre in segments:
        part = montant / total * 100
        encre_txt = "#10221B" if sombre else "#F4F8FA"
        etiquette = (f'<span class="part" style="color:{encre_txt}">'
                     f"{part:.0f} %</span>" if part >= 9 else "")
        barres += (f'<div style="width:{part}%;background:{couleur}">'
                   f"{etiquette}</div>")
        legende += (f'<span class="item"><i style="background:{couleur}"></i>'
                    f"{libelle} <b>{euros(montant)}</b></span>")
    st.markdown(f'<div class="strates">{barres}</div>'
                f'<div class="legende">{legende}</div>',
                unsafe_allow_html=True)


def profil_mensualites(phase1: float, phase2: float, differe_ans: int,
                       capacite: float, duree_ans: int = 25) -> None:
    """Élément signature : le profil en marches sur 25 ans.

    Montre le saut de mensualité à la fin du différé du prêt à taux zéro,
    face à la capacité de la banque. C'est la phase 2 que la banque teste,
    et aucun simulateur ne la représente.
    """
    L, H = 640, 210
    gx, gy, gw, gh = 58, 18, L - 76, H - 62
    haut = max(phase1, phase2, capacite) * 1.18 or 1
    ech = lambda v: gy + gh - (v / haut) * gh
    xr = lambda a: gx + (a / duree_ans) * gw

    x_bascule = xr(max(min(differe_ans, duree_ans), 0))
    y1, y2, yc = ech(phase1), ech(phase2), ech(capacite)
    depasse = phase2 > capacite

    aires = (
        f'<path d="M{gx},{gy + gh} L{gx},{y1} L{x_bascule},{y1} '
        f'L{x_bascule},{y2} L{xr(duree_ans)},{y2} L{xr(duree_ans)},{gy + gh} Z" '
        f'fill="{BATI}" fill-opacity="0.14" stroke="none"/>'
        f'<path d="M{gx},{y1} L{x_bascule},{y1} L{x_bascule},{y2} '
        f'L{xr(duree_ans)},{y2}" fill="none" stroke="{BATI}" '
        f'stroke-width="2.5" stroke-linejoin="miter"/>'
    )
    seuil = (
        f'<line x1="{gx}" y1="{yc}" x2="{xr(duree_ans)}" y2="{yc}" '
        f'stroke="{SANGUINE if depasse else FAVORABLE}" stroke-width="1.5" '
        f'stroke-dasharray="5 4"/>'
        f'<text x="{xr(duree_ans)}" y="{yc - 7}" text-anchor="end" '
        f'font-family="IBM Plex Mono" font-size="11" '
        f'fill="{SANGUINE if depasse else FAVORABLE}">'
        f"capacité {euros(capacite)}</text>"
    )
    reperes = (
        f'<line x1="{gx}" y1="{gy + gh}" x2="{xr(duree_ans)}" y2="{gy + gh}" '
        f'stroke="{TRAIT}" stroke-width="1"/>'
        f'<line x1="{x_bascule}" y1="{gy}" x2="{x_bascule}" y2="{gy + gh}" '
        f'stroke="{TRAIT}" stroke-width="1" stroke-dasharray="3 3"/>'
    )
    etiquettes = (
        f'<text x="{gx + 6}" y="{y1 - 8}" font-family="IBM Plex Mono" '
        f'font-size="13" font-weight="600" fill="{ENCRE}">{euros(phase1)}</text>'
        f'<text x="{x_bascule + 6}" y="{y2 - 8}" font-family="IBM Plex Mono" '
        f'font-size="13" font-weight="600" fill="{ENCRE}">{euros(phase2)}</text>'
        f'<text x="{gx}" y="{H - 26}" font-family="IBM Plex Mono" '
        f'font-size="10.5" fill="{BRUME}">an 1</text>'
        f'<text x="{x_bascule}" y="{H - 26}" text-anchor="middle" '
        f'font-family="IBM Plex Mono" font-size="10.5" fill="{BRUME}">'
        f"fin du différé, an {differe_ans}</text>"
        f'<text x="{xr(duree_ans)}" y="{H - 26}" text-anchor="end" '
        f'font-family="IBM Plex Mono" font-size="10.5" fill="{BRUME}">'
        f"an {duree_ans}</text>"
        f'<text x="{gx}" y="{H - 8}" font-family="IBM Plex Sans" '
        f'font-size="11" fill="{BRUME}">'
        f"Mensualité tout compris, redevance incluse</text>"
    )
    st.markdown(
        f'<div style="background:#fff;border:1px solid {TRAIT};'
        f'border-radius:4px;padding:.6rem .4rem .2rem">'
        f'<svg viewBox="0 0 {L} {H}" width="100%" role="img" '
        f'aria-label="Profil de mensualité sur {duree_ans} ans avec le saut '
        f'à la fin du différé">{aires}{seuil}{reperes}{etiquettes}</svg></div>',
        unsafe_allow_html=True,
    )


_COULEURS_DPE = {"A": "#3E8F5A", "B": "#63A94C", "C": "#A8C24A",
                 "D": "#E8CE43", "E": "#E8A93D", "F": "#DE7C35",
                 "G": "#C4442F"}


def pastille_dpe(lettre) -> str:
    l = str(lettre).strip().upper()[:1]
    return (f'<span class="dpe" style="background:{_COULEURS_DPE.get(l, TRAIT)}">'
            f"{l or '?'}</span>") if l else "n/d"


def note(texte: str) -> None:
    st.markdown(f'<div class="note">{texte}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Nettoyage des tableaux bruts
# ----------------------------------------------------------------------

def _premiere_colonne(df: pd.DataFrame, candidats) -> str | None:
    for c in candidats:
        if c in df.columns:
            return c
    bas = {c.lower(): c for c in df.columns}
    for c in candidats:
        if c.lower() in bas:
            return bas[c.lower()]
    return None


def table_ventes(lignes) -> pd.DataFrame:
    """Ventes DVF : colonnes utiles, dates lisibles, prix au m² arrondi."""
    df = pd.DataFrame(lignes)
    if df.empty:
        return df
    df = df.rename(columns={"date": "Date", "type": "Type",
                            "prix": "Prix", "surface": "Surface m²",
                            "prix_m2": "Prix au m²"})
    for c in ("Prix", "Surface m²", "Prix au m²"):
        if c in df:
            df[c] = df[c].round(0).astype("Int64")
    garder = [c for c in ["Date", "Type", "Surface m²", "Prix", "Prix au m²"]
              if c in df]
    return df[garder].sort_values("Date", ascending=False)


def table_dpe(lignes) -> pd.DataFrame:
    """DPE ADEME : on ne garde que ce qui se lit, noms de colonnes français."""
    df = pd.DataFrame(lignes)
    if df.empty:
        return df
    mapping = {
        "Étiquette énergie": ["etiquette_dpe", "classe_consommation_energie",
                              "etiquette_energie"],
        "Étiquette GES": ["etiquette_ges", "classe_estimation_ges"],
        "Surface m²": ["surface_habitable_logement", "surface_habitable",
                       "surface_thermique_lot"],
        "Type": ["type_batiment", "tr002_type_batiment_description"],
        "Année": ["annee_construction", "periode_construction"],
        "Adresse": ["adresse_ban", "adresse_brute", "geo_adresse"],
        "Date": ["date_etablissement_dpe", "date_realisation_dpe"],
    }
    sortie = {}
    for libelle, candidats in mapping.items():
        col = _premiere_colonne(df, candidats)
        if col:
            sortie[libelle] = df[col]
    if not sortie:
        return df.head(30)
    propre = pd.DataFrame(sortie)
    if "Surface m²" in propre:
        propre["Surface m²"] = pd.to_numeric(
            propre["Surface m²"], errors="coerce").round(0).astype("Int64")
    return propre.head(40)


def repartition_dpe(lignes) -> dict:
    """Compte les logements par étiquette, pour la barre de synthèse."""
    df = pd.DataFrame(lignes)
    if df.empty:
        return {}
    col = _premiere_colonne(df, ["etiquette_dpe", "classe_consommation_energie",
                                 "etiquette_energie"])
    if not col:
        return {}
    serie = df[col].astype(str).str.strip().str.upper().str[:1]
    serie = serie[serie.isin(list("ABCDEFG"))]
    return {l: int(n) for l, n in serie.value_counts().items()}


def barre_dpe(repartition: dict) -> None:
    total = sum(repartition.values())
    if not total:
        return
    barres = ""
    for lettre in "ABCDEFG":
        n = repartition.get(lettre, 0)
        if not n:
            continue
        barres += (f'<div style="width:{n / total * 100}%;'
                   f'background:{_COULEURS_DPE[lettre]}">'
                   f'<span class="part" style="color:#10221B">{lettre}</span>'
                   f"</div>")
    st.markdown(f'<div class="strates">{barres}</div>'
                f'<div class="legende"><span class="item">'
                f"Répartition des <b>{total}</b> diagnostics de la commune"
                f"</span></div>", unsafe_allow_html=True)


def table_risques(lignes) -> pd.DataFrame:
    df = pd.DataFrame(lignes)
    if df.empty:
        return df
    if {"risque", "present"}.issubset(df.columns):
        df = df.copy()
        df["Concerné"] = df["present"].map({True: "oui", False: "non"})
        df = df.rename(columns={"risque": "Risque", "libelle": "Détail",
                                "categorie": "Catégorie"})
        df["Catégorie"] = df.get("Catégorie", "").replace(
            {"risquesNaturels": "Naturel",
             "risquesTechnologiques": "Technologique"})
        garder = [c for c in ["Catégorie", "Risque", "Concerné", "Détail"]
                  if c in df]
        vue = df[garder]
        if "Concerné" in vue:
            vue = pd.concat([vue[vue["Concerné"] == "oui"],
                             vue[vue["Concerné"] != "oui"]])
        return vue
    mapping = {"Risque": ["libelle_risque_long", "libelle_risque"],
               "Aléa": ["code_alea", "libelle_alea"],
               "Commune": ["libelle_commune"]}
    sortie = {}
    for libelle, candidats in mapping.items():
        col = _premiere_colonne(df, candidats)
        if col:
            sortie[libelle] = df[col]
    return pd.DataFrame(sortie) if sortie else df


def table_zonage(lignes) -> pd.DataFrame:
    df = pd.DataFrame(lignes)
    if df.empty:
        return df
    mapping = {"Zone": ["libelle", "libelong", "typezone"],
               "Type": ["typezone"],
               "Document": ["partition", "idurba"],
               "Destination": ["destdomi"]}
    sortie = {}
    for libelle, candidats in mapping.items():
        col = _premiere_colonne(df, candidats)
        if col and libelle not in sortie:
            sortie[libelle] = df[col]
    return pd.DataFrame(sortie) if sortie else df


def table_ecoles(lignes) -> pd.DataFrame:
    df = pd.DataFrame(lignes)
    if df.empty:
        return df
    df = df.rename(columns={"établissement": "Établissement", "type": "Type",
                            "statut": "Statut", "ips": "IPS"})
    if "IPS" in df:
        df["IPS"] = pd.to_numeric(df["IPS"], errors="coerce").round(0).astype("Int64")
        df = df.sort_values("IPS", ascending=False, na_position="last")
    return df


def table_equipements(lignes) -> pd.DataFrame:
    df = pd.DataFrame(lignes)
    if df.empty:
        return df
    return df.rename(columns={"categorie": "Catégorie", "nombre": "Nombre",
                              "plus_proche_m": "Plus proche (m)"})


# ----------------------------------------------------------------------
# Export
# ----------------------------------------------------------------------

def fiche_recap(adresse, commune, prix, surface, dispositif, m, cap,
                dec=None, extras=None) -> str:
    """Récapitulatif texte à emporter chez le courtier ou à joindre à une
    candidature. Tous les chiffres, aucune mise en forme exotique."""
    lignes = [
        "FICHE DE CHIFFRAGE - ACCESSION AIDÉE",
        "=" * 46, "",
        f"Bien        : {adresse or 'n/d'}",
        f"Commune     : {commune or 'n/d'}",
        f"Dispositif  : {dispositif}",
        f"Prix        : {euros(prix)}",
        f"Surface     : {surface} m²",
        f"Prix au m²  : {euros(prix / surface if surface else 0)}",
        "",
        "PLAN DE FINANCEMENT", "-" * 46,
        f"Prêt à taux zéro       : {euros(m['ptz'])}"
        f"   (quotité {m['quotite'] * 100:.0f} %, différé {m['differe_ans']} ans)",
        f"Prêt Action Logement   : {euros(m['action_logement'])}   (1 %)",
        f"Prêt principal         : {euros(m['principal'])}",
        f"Apport                 : {euros(m['apport'])}",
        f"Frais de notaire       : {euros(m['frais_notaire'])}",
        f"Coût total             : {euros(m['cout_total'])}",
        f"Part gratuite ou à 1 % : {m['part_gratuite'] * 100:.0f} %",
        "",
        "MENSUALITÉS", "-" * 46,
        f"Phase 1, années 1 à {m['differe_ans']} : {euros(m['phase1'])} par mois",
        f"Phase 2, après différé   : {euros(m['phase2'])} par mois",
        f"Redevance foncière       : {euros(m['redevance'])} par mois",
        "",
        "CAPACITÉ", "-" * 46,
        f"Revenus retenus     : {euros(cap['revenus_retenus'])} par mois",
        f"Plafond à {cap['taux_applique'] * 100:.0f} %       : {euros(cap['plafond_mensuel'])} par mois",
        f"Charges existantes  : {euros(cap['charges_existantes'])} par mois",
        f"Disponible          : {euros(cap['disponible'])} par mois",
        "",
        ("VERDICT : finançable, marge de "
         f"{euros(cap['disponible'] - m['phase2'])} par mois"
         if m["phase2"] <= cap["disponible"] else
         "VERDICT : dépassement de "
         f"{euros(m['phase2'] - cap['disponible'])} par mois en phase 2"),
    ]
    if dec and dec.get("ok"):
        lignes += ["", "MARCHÉ LOCAL", "-" * 46,
                   f"Médiane du secteur : {euros(dec['mediane_m2'])} par m²",
                   f"Décote du bien     : {dec['decote_pct']:.0f} %",
                   f"Base de calcul     : {dec['nb_ventes']} ventes réelles"]
    if extras:
        lignes += ["", "CONTEXTE", "-" * 46] + [f"{k} : {v}" for k, v in extras.items()]
    lignes += ["", "-" * 46,
               "Estimations produites par un outil personnel. Ne remplacent "
               "ni un courtier, ni un notaire, ni l'ADIL."]
    return "\n".join(lignes)
