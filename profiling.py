import streamlit as st
import pandas as pd
import base64
import os
import re
import unicodedata
import matplotlib.pyplot as plt
import numpy as np
from math import pi
from io import BytesIO
from scipy import stats

# Imports existants
from utils import SDR_RED
from team_profiling import show_team_page
from profiling_report import generate_report

# On garde les configs si besoin
from config_rapport import OFFICIAL_STRUCTURE, REPORT_NORMES, UNITS

# =============================================================================
# CONFIGURATION LOCALE & MAPPINGS
# =============================================================================

# Mapping pour faire correspondre les Libellés UI -> Colonnes Excel
COL_MAPPING = {
    "Knee To Wall (G)": "Knee To Wall - Gauche", "Knee To Wall (D)": "Knee To Wall - Droite",
    "Sit And Reach": "Sit And Reach",
    "Somme ADD": "Somme ADD", "Adducteurs (G)": "Adducteurs - Gauche", "Adducteurs (D)": "Adducteurs - Droite",
    "Ratio Squeeze": "Ratio Squeeze (ADD/ABD)",
    "Somme ABD": "Somme ABD", "Abducteurs (G)": "Abducteurs - Gauche ", 
    "Abducteurs (D)": "Abducteurs - Droite (N/kg)", 
    "Nordic Ischio (G)": "Nordic Ischio - Gauche", "Nordic Ischio (D)": "Nordic Ischio - Droite",
    "Landing (G)": "Landing G (N/kg)", "Landing (D)": "Landing Dt (N/kg)", "Landing %": "Landing %",
    "Q Conc 60° (G)": "Q G conc 60°/s", "Q Conc 60° (D)": "Q Dt conc 60°/s",
    "Q Conc 240° (G)": "Q G conc 240°/s", "Q Conc 240° (D)": "Q Dt conc 240°/s",
    "IJ Conc 60° (G)": "IJ G conc 60°/s", "IJ Conc 60° (D)": "IJ Dt conc 60°/s",
    "IJ Conc 240° (G)": "IJ G conc 240°/s", "IJ Conc 240° (D)": "IJ Dt conc 240°/s",
    "IJ Exc 30° (G)": "IJ G Exc 30°/s", "IJ Exc 30° (D)": "IJ Dt exc 30°/s",
    "Score Sommeil": "Score Sommeil", "Score Nutrition": "Score Nutrition",
    "CMJ (cm)": "CMJ (cm)", "Wattbike (6s)": "Wattbike 6s (W)",
    "Squat Keiser": "Keiser squat R=100", "Tirage Dos Keiser": "Tirage dos Keiser",
    "Développé couché (W)": "Developpé couché (W)",
    "Développé couché (W/kg)": "Developpé couché (W/kg)", "Landmine Throw": "Landmine throw",
    "VMA": "VMA", "Temps 10m (Terrain)": "Temps 10m", "5-0-5": "5 - 0 - 5",
    "Distance Totale": "Distance totale", "Distance HSR": "Distance HSR", "Distance Sprint (92% Vmax)": "Distance Sprint (92% Vmax)",
    "Nb Accélérations": "Nb Acc", "Nb Décélérations": "Nb Dec",
    "Vmax": "Vmax", "Amax": "Amax", "Dmax": "Dmax"
}

# Mapping pour les valeurs relatives (tooltips)
REL_COL_MAPPING = {
    "Somme ADD": "Somme ADD (N/kg)", "Somme ABD": "Somme ABD (N/kg)",
    "Adducteurs (G)": "Adducteurs - Gauche (N/kg)", "Adducteurs (D)": "Adducteurs - Droite (N/kg)",
    "Abducteurs (G)": "Abducteurs - Gauche (N/kg)", "Abducteurs (D)": "Abducteurs - Droite", 
    "Nordic Ischio (G)": "Nordic Ischio - Gauche (N/kg)", "Nordic Ischio (D)": "Nordic Ischio - Droite (N/kg)",
    "Q Conc 60° (G)": "Q G conc 60°/s (N/kg)", "Q Conc 60° (D)": "Q Dt conc 60°/s (N/kg)",
    "Q Conc 240° (G)": "Q G conc 240°/s (N/kg)", "Q Conc 240° (D)": "Q Dt conc 240°/s (N/kg)",
    "IJ Conc 60° (G)": "IJ G conc 60°/s (N/kg)", "IJ Conc 60° (D)": "IJ Dt conc 60°/s (N/kg)",
    "IJ Conc 240° (G)": "IJ G conc 240°/s (N/kg)", "IJ Conc 240° (D)": "IJ Dt conc 240°/s (N/kg)",
    "IJ Exc 30° (G)": "IJ G Exc 30°/s (N/kg)", "IJ Exc 30° (D)": "IJ Dt exc 30°/s (N/kg)",
    "Q Exc 30° (G)": "Q G exc 30°/s (N/kg)", "Q Exc 30° (D)": "Q Dt exc 30°/s (N/kg)",
    "Développé couché (W)": "Developpé couché (W/kg)","Q Exc 30° (G)": "Q G exc 30°/s (N/kg)", "Q Exc 30° (D)": "Q Dt exc 30°/s (N/kg)"
}

# Sources (si non importées depuis configrapport)
SOURCES_CONFIG = {
    "Q Conc 60°": "Scientifique", "Q Conc 240°": "Scientifique", 
    "IJ Conc 60°": "Scientifique", "IJ Conc 240°": "Scientifique", "IJ Exc 30°": "Scientifique"
}

KEYWORD_MAPPING = {
    "Taille": ["taille", "height"], "Poids": ["poids", "weight"],
    "Masse Grasse Plis (mm)": ["masse grasse", "fat", "img"],
    "Numéro": ["numero", "numéro", "number", "maillot"],
    "Poste": ["poste", "position"], "Latéralité": ["latéralité", "laterality", "pied"],
    "Knee To Wall (G)": ["knee to wall - gauche", "ktw g"], "Knee To Wall (D)": ["knee to wall - droite", "ktw d"],
    "Sit And Reach": ["sit and reach", "souplesse"],
    "Adducteurs (G)": ["adducteurs - gauche", "add g"], "Adducteurs (D)": ["adducteurs - droite", "add d"],
    "Abducteurs (G)": ["abducteurs - gauche", "abd g"], "Abducteurs (D)": ["abducteurs - droite", "abd d"],
    "Nordic Ischio (G)": ["nordic ischio - gauche", "nordic g"], "Nordic Ischio (D)": ["nordic ischio - droite", "nordic d"],
    "Landing (G)": ["landing g"], "Landing (D)": ["landing dt", "landing d"],
    "Landing %": ["landing %", "landing", "asymétrie landing"],
    "Q Conc 60° (G)": ["q g conc 60"], "Q Conc 60° (D)": ["q dt conc 60"],
    "Q Conc 240° (G)": ["q g conc 240"], "Q Conc 240° (D)": ["q dt conc 240"],
    "IJ Conc 60° (G)": ["ij g conc 60"], "IJ Conc 60° (D)": ["ij dt conc 60"],
    "IJ Conc 240° (G)": ["ij g conc 240"], "IJ Conc 240° (D)": ["ij dt conc 240"],
    "IJ Exc 30° (G)": ["ij g exc 30"], "IJ Exc 30° (D)": ["ij dt exc 30"],
    "Q Exc 30° (G)": ["q g exc 30", "quad g exc 30"], 
    "Q Exc 30° (D)": ["q dt exc 30", "quad dt exc 30"],
    "Ratio Mixte (G)": ["ratio mixte g", "mixte g"], 
    "Ratio Mixte (D)": ["ratio mixte dt", "mixte d", "mixte dt", "ratio mixte d"],
    "Score Sommeil": ["score sommeil", "sommeil"], "Score Nutrition": ["score nutrition", "nutrition"],
    "CMJ (cm)": ["cmj", "saut"], "Wattbike 6s (W)": ["wattbike"],
    "Squat Keiser": ["keiser squat", "squat r=100"], "Tirage Dos Keiser": ["tirage dos"],
    
    
    "Développé couché (W)" : ["developpé couché (W)", "couché (W)"], 
    "Développé couché (W/kg)" : ["developpé couché (W/kg)", "couché (W/kg)"],
    
    "Landmine Throw": ["landmine"],
    "10m 1080 (s)": ["10m 1080", "1080"],
    "VMA": ["vma"], "SV1": ["sv1"], "SV2": ["sv2"],
    "Temps 10m (Terrain)": ["temps 10m", "chrono 10m"], "5-0-5": ["5 - 0 - 5", "505"],
    "Distance Totale": ["distance totale", "total dist"], "Distance HSR": ["distance hsr", "hsr"],
    "Distance Sprint (92% Vmax)" : ["distance sprint", "sprint"],
    "Nb Accélérations": ["nb acc"], "Nb Décélérations": ["nb dec"],
    "Vmax": ["vmax"], "Amax": ["amax"], "Dmax": ["dmax"],
    "Score Sommeil": ["score sommeil", "sommeil"], "Score Nutrition": ["score nutrition", "nutrition"],
}




def remove_accents(input_str):
    if not isinstance(input_str, str): return str(input_str)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

# plus c'est bas, mieux c'est (copié du doc RPE)
def is_inverted(label):
    keywords = ['temps', 'chrono', '10m', '505', 'agilité', 'masse grasse', 'landing', "Landing %"]
    return any(x in str(label).lower() for x in keywords)

def clean_numeric_value(val):
    if pd.isna(val) or val == "" or val == "-": return None
    try:
        if isinstance(val, (int, float)): return float(val)
        val_str = str(val).replace(',', '.')
        match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
        if match: return float(match.group())
        return None
    except: return None


# calcul des percentiles (avec sécurité rajouté )
def calculate_percentile(df, col_name, value):
    if col_name not in df.columns or pd.isna(value): return 0, 0
    valid_values = pd.to_numeric(df[col_name], errors='coerce').dropna()
    if valid_values.empty: return 0, 0
    mean_val = valid_values.mean()
    inverted = is_inverted(col_name)
    
    if inverted:
        percentile = (valid_values >= value).mean() * 100
    else:
        percentile = (valid_values <= value).mean() * 100
    return mean_val, percentile

def calculate_rank_info(df, col_name, value):
    if col_name not in df.columns or pd.isna(value): return "-", "-"
    valid_data = pd.to_numeric(df[col_name], errors='coerce').dropna()
    if valid_data.empty: return "-", "-"
    inverted = is_inverted(col_name)
    ranked = valid_data.rank(method='min', ascending=inverted)
    try:
        matches = ranked[valid_data == float(value)]
        if not matches.empty:
            player_rank = int(matches.iloc[0])
            total = len(valid_data)
            return player_rank, total
        return "-", "-"
    except: return "-", "-"

# calcul des asymétries
def get_asymmetry(df_row, metric_label, df):
    if "(G)" not in metric_label: return None
    metric_label_d = metric_label.replace("(G)", "(D)")
    col_g = find_column_in_df(df, metric_label)
    col_d = find_column_in_df(df, metric_label_d)
    if not col_g or not col_d: return None
    val_g = clean_numeric_value(df_row.get(col_g))
    val_d = clean_numeric_value(df_row.get(col_d))
    if val_g is None or val_d is None: return None
    try:
        max_val = max(val_g, val_d)
        if max_val == 0: return 0
        diff = (abs(val_g - val_d) / max_val) * 100
        return diff
    except: return None

def find_column_in_df(df, label):
    keywords = KEYWORD_MAPPING.get(label, [])
    keywords_clean = [remove_accents(k).lower().strip() for k in keywords]
    df_cols_clean = [remove_accents(str(c)).lower().strip() for c in df.columns]
    for k in keywords_clean:
        for idx, col_name in enumerate(df_cols_clean):
            if k in col_name: return df.columns[idx]
    return None

# trouver le numéro (au cas ou ça change)
def find_number_column(df):
    cols_map = {remove_accents(str(c)).lower().strip(): c for c in df.columns}
    targets = ['numero', 'numéro', 'number', 'maillot', 'shirt', 'n°']
    for t in targets:
        if t in cols_map: return cols_map[t]
    for c_clean, c_original in cols_map.items():
        if c_clean.startswith("num") or c_clean == "n°": return c_original
    return None

def img_to_b64(img_path):
    try:
        with open(img_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

# ajout des photos des joueurs
def get_best_photo_path(player_name):
    folder = "Photos"
    if not os.path.exists(folder): return None
    
    files_map = {f.lower(): f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))}
    
    clean_name = player_name.strip()
    parts = clean_name.split()
    
    candidates = []
    candidates.append(clean_name)
    
    if len(parts) > 1:
        inverted = f"{parts[-1]} {' '.join(parts[:-1])}"
        candidates.append(inverted)
        
        candidates.append(f"{' '.join(parts[1:])} {parts[0]}")

    extensions = [".jpg", ".png", ".jpeg"]
    
    for cand in candidates:
        for ext in extensions:
            target_key = f"{cand}{ext}".lower()
            if target_key in files_map:
                return os.path.join(folder, files_map[target_key])
            
    return None

def create_radar_chart(categories, values, text_color="white"):
    """
    Génère un graphique radar avec des zones de performance (0-33% rouge, 66-100% vert).
    Retourne l'image encodée en base64.
    """
    if not categories: return ""
    
    # Nombre de variables
    N = len(categories)
    
    # Fermeture du polygone (répéter la première valeur à la fin)
    values_closed = values + values[:1]
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    # Création de la figure
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # --- Zones de fond (Contextualisation) ---
    # Zone Rouge (Faible : 0-33)
    ax.fill_between(angles, 0, 33, color='#D71920', alpha=0.15)
    # Zone Verte (Fort : 66-100)
    ax.fill_between(angles, 66, 100, color='#27AE60', alpha=0.15)
    
    # --- Axes et Labels ---
    # Ajustement de la couleur du texte selon le fond (Streamlit=White, PDF=Black)
    plt.xticks(angles[:-1], categories, color=text_color, size=9, weight='bold')
    
    # Position des labels radiaux (0, 33, 66, 100)
    ax.set_rlabel_position(0)
    
    # Couleur de la grille : plus claire si texte noir (PDF), plus foncée si texte blanc (Streamlit Dark)
    grid_color = "#ccc" if text_color == "black" else "#555" 
    
    plt.yticks([33, 66, 100], ["33", "66", ""], color="#888", size=8)
    plt.ylim(0, 100)
    
    # --- Styles de grille ---
    ax.yaxis.grid(True, color=grid_color, linestyle='dashed')
    ax.xaxis.grid(True, color=grid_color)
    ax.spines['polar'].set_color(grid_color)
    
    # --- Tracé des données ---
    # Ligne et points
    ax.plot(angles, values_closed, linewidth=2, linestyle='solid', color=SDR_RED, marker='o', markersize=5)
    # Remplissage de la forme du joueur
    ax.fill(angles, values_closed, color=SDR_RED, alpha=0.4)
    
    # Transparence globale du fond de l'image
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    # --- Sauvegarde ---
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return img_b64

def create_multi_radar_chart(categories, values_l, values_r, values_norm, max_val=5.0):
    if not categories: return ""
    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    # Fermeture des boucles
    v_l = values_l + values_l[:1]
    v_r = values_r + values_r[:1]
    v_n = values_norm + values_norm[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # Axes et Grille
    plt.xticks(angles[:-1], categories, color='white', size=8, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4], ["1", "2", "3", "4"], color="#888", size=7)
    plt.ylim(0, max_val)
    
    ax.yaxis.grid(True, color="#444", linestyle='dashed')
    ax.xaxis.grid(True, color="#444")
    ax.spines['polar'].set_color('#444')
    ax.set_facecolor("none")
    fig.patch.set_alpha(0.0)
    
    # Courbe GAUCHE (Bleu/Cyan)
    ax.plot(angles, v_l, linewidth=2, linestyle='solid', color='#3498DB', label='Gauche')
    ax.fill(angles, v_l, color='#3498DB', alpha=0.1)
    
    # Courbe DROITE (Rouge/Orange)
    ax.plot(angles, v_r, linewidth=2, linestyle='solid', color='#E74C3C', label='Droite')
    ax.fill(angles, v_r, color='#E74C3C', alpha=0.1)
    
    # Courbe NORME (Vert pointillé)
    ax.plot(angles, v_n, linewidth=2, linestyle='--', color='#2ECC71', label='Obj.')
    
    # Légende
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1), fontsize=8, frameon=False, labelcolor='white')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_b64

# --- HELPERS UI / LOGIQUE METIER (GLOBAL) ---

def smart_format(val):
    if pd.isna(val) or val is None or val == "": return "-"
    try:
        val_float = float(val)
        if val_float == 0: return "0"
        if val_float % 1 == 0: return f"{int(val_float)}"
        return f"{val_float:.2f}"
    except: return "-"

def get_clean_label(label):
    return label.replace("(G)", "").replace("(D)", "").strip()

def get_unit(label):
    return UNITS.get(get_clean_label(label), "")

def get_col_name(label):
    return COL_MAPPING.get(label, label)

def get_rel_col_name(label):
    return REL_COL_MAPPING.get(label, None)

def get_source(label):
    return SOURCES_CONFIG.get(get_clean_label(label), "Club")

def get_norm_text(label):
    col_clean = str(label).replace("(G)", "").replace("(D)", "").strip()
    # Recherche dans REPORT_NORMES importé
    found_key = next((k for k in REPORT_NORMES.keys() if k in col_clean), None)
    if not found_key: return "-"
    
    low, high = REPORT_NORMES[found_key]
    suffix = f" {get_unit(label)}"
    
    if is_inverted(label):
        return f"Obj: < {smart_format(low)}{suffix}"
    else:
        return f"Obj: {smart_format(low)} - {smart_format(high)}{suffix}"

def get_bar_color(pct):
    if pct < 33: return "#D71920"
    if pct < 66: return "#F39C12"
    return "#27AE60"

def get_status_data_local(label, value):
    val = clean_numeric_value(value)
    if val is None: return "#888", "-", "#888" 
    
    col_clean = str(label).replace("(G)", "").replace("(D)", "").strip()
    found_key = next((k for k in REPORT_NORMES.keys() if k in col_clean), None)
    
    if not found_key: return "#444444", "-", "#FFFFFF"
    
    low, high = REPORT_NORMES[found_key]
    
    # Logique couleur UI
    c_bad, c_avg, c_good = "#D71920", "#F39C12", "#27AE60"
    
    if is_inverted(label):
        if val < low: return c_good, "Bon", c_good
        elif val <= high: return c_avg, "Moyen", c_avg
        else: return c_bad, "Mauvais", c_bad
    else:
        if val < low: return c_bad, "Mauvais", c_bad
        elif val < high: return c_avg, "Moyen", c_avg
        else: return c_good, "Bon", c_good

def get_rel_display_smart(row_data, label_name, abs_val, p_poids):
    rel_col = get_rel_col_name(label_name)
    
    # 1. Chercher colonne explicite
    if rel_col and rel_col in row_data:
        val = clean_numeric_value(row_data[rel_col])
        if val: 
             u = "W/kg" if ("W/kg" in rel_col or "Watt" in label_name or "couché (W)" in label_name) else "N/kg"
             return f"{val:.2f} {u}"
    
    # 2. Calcul dynamique si poids dispo
    if p_poids and p_poids > 0 and abs_val is not None:
        unit_abs = get_unit(label_name)
        if unit_abs == "N": return f"{(abs_val/p_poids):.2f} N/kg"
        elif unit_abs == "W" or "Watt" in label_name: return f"{(abs_val/p_poids):.2f} W/kg"
        
    return None

def get_tooltip_html(row, label):
    rel_col = get_rel_col_name(label)
    if rel_col and rel_col in row:
        val_rel = clean_numeric_value(row[rel_col])
        if val_rel is not None:
            unit_rel = "N/kg" if ("N/kg" in rel_col or "Abducteurs - Droite" == rel_col) else "W/kg" if "W/kg" in rel_col else ""
            return f"title='Relatif: {val_rel:.2f} {unit_rel}'"
    return ""

def get_asym_badge_info(val_l, val_r, df_data, col_l, col_r):
    if val_l is None or val_r is None: return None, None
    
    if "Knee" in col_l or "KTW" in col_l:
         max_l = pd.to_numeric(df_data[col_l], errors='coerce').max()
         max_r = pd.to_numeric(df_data[col_r], errors='coerce').max()
         ref = max(max_l, max_r) if (pd.notna(max_l) and pd.notna(max_r)) else 0
         if ref == 0: return 0, ""
         pct = (abs(val_l - val_r) / ref) * 100
    else:
         if max(val_l, val_r) == 0: return 0, ""
         pct = (abs(val_l - val_r) / max(val_l, val_r)) * 100
         
    side = "G" if val_l < val_r else "D"
    return pct, side


def inject_custom_css():
    st.markdown(f"""
    <style>
        .section-header {{ font-size: 18px; font-weight: 800; color: #FFF; margin-top: 25px; margin-bottom: 10px; padding-left: 10px; border-left: 5px solid {SDR_RED}; text-transform: uppercase; }}
        .kpi-card {{ background-color: #2b2d3e; border-radius: 8px; padding: 12px; margin-bottom: 8px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 1px solid #3f4254; transition: transform 0.2s; }}
        .kpi-card:hover {{ transform: translateY(-2px); border-color: {SDR_RED}; }}
        .kpi-top {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px; }}
        .kpi-lbl {{ font-size: 11px; color: #a1a5b7; font-weight: 600; text-transform: uppercase; }}
        .kpi-val {{ font-size: 22px; font-weight: 800; color: white; margin: 5px 0; }}
        .progress-bg {{ background-color: #1e1e2d; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 8px; }}
        .progress-fill {{ height: 100%; border-radius: 3px; }}
        .kpi-footer {{ display: flex; justify-content: space-between; font-size: 10px; color: #7e8299; margin-top: 4px; }}
        .alert-badge {{ color: #ff5252; font-weight: bold; font-size: 10px; }}
        textarea {{ background-color: #1e1e2d !important; color: white !important; border: 1px solid #444; }}
        .hero-container {{ background: linear-gradient(135deg, #1e1e2d 0%, #141414 100%); border-left: 6px solid {SDR_RED}; padding: 25px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 25px; }}
        .hero-left {{ display: flex; align-items: center; gap: 25px; }}
        .hero-photo {{ width: 110px; height: 110px; border-radius: 12px; border: 3px solid {SDR_RED}; object-fit: cover; box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
        .hero-details {{ display: flex; flex-direction: column; }}
        .hero-name {{ font-size: 40px; font-weight: 900; color: #FFFFFF; text-transform: uppercase; line-height: 1; margin-bottom: 0px; }}
        .hero-number {{ font-size: 26px; font-weight: 800; color: {SDR_RED}; margin-bottom: 5px; letter-spacing: 1px; }}
        .hero-meta {{ font-size: 16px; font-weight: 600; color: #bdc3c7; text-transform: uppercase; letter-spacing: 1px; }}
        .hero-right {{ display: flex; gap: 40px; padding-right: 20px; }}
        .stat-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; }}
        .stat-label {{ font-size: 11px; font-weight: 700; color: {SDR_RED}; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
        .stat-value {{ font-size: 28px; font-weight: 800; color: #FFFFFF; }}
    </style>""", unsafe_allow_html=True)

def load_data_from_source(source):
    """Charge les données depuis un fichier (str path) ou un objet file uploadé."""
    try:
        df = pd.read_excel(source, header=0)
        cols_lower = {str(c).lower().strip(): c for c in df.columns}
        target = next((cols_lower[k] for k in ['joueur', 'nom', 'name'] if k in cols_lower), None)
        if not target: return pd.DataFrame(), "Colonne 'Joueur' introuvable dans le fichier."
        df = df.dropna(subset=[target]).rename(columns={target: 'Joueur'})
        df['Joueur'] = df['Joueur'].astype(str).str.title().str.strip()
        return df, None
    except Exception as e: return pd.DataFrame(), str(e)

def load_all_data():
    """Charge le fichier par défaut si aucun upload n'est fait."""
    possible_files = ["Profilage pratiquexlsx.xlsx", "Profilage.xlsx"]
    found_file = None
    for f in possible_files:
        if os.path.exists(f):
            found_file = f
            break
    if not found_file: return pd.DataFrame(), "Fichier introuvable"
    return load_data_from_source(found_file)



# =============================================================================
# MAIN PAGE FUNCTION
# =============================================================================

def show_profiling_page(df_main=None):
    inject_custom_css()
    
    st.title("PROFILAGE")

    # --- 3. CHARGEMENT ---
    with st.expander("Aide chargement des données (Autre équipe) ", expanded=True):
        st.markdown("### PROTOCOLE DE MISE À JOUR")
        c1, c2 = st.columns(2)
        template_path = "Document Profilage Reims.xlsx" 
        with c1:
            if os.path.exists(template_path):
                with open(template_path, "rb") as f:
                    st.download_button("Télécharger le modèle vide", f, "Document_Profilage_Reims_Vide.xlsx", 
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else:
                st.info("Fichier modèle non détecté.")

        df = pd.DataFrame() 
        with c2:
            uploaded_file = st.file_uploader("⬆️ DÉPOSER LE FICHIER REMPLI", type=["xlsx"], label_visibility="collapsed")
            if uploaded_file:
                df, err = load_data_from_source(uploaded_file)
                if not df.empty:
                    st.success("✅ Fichier chargé !")
                    try:
                        with open("Profilage pratiquexlsx.xlsx", "wb") as f: f.write(uploaded_file.getbuffer())
                    except: st.warning("Visualisation active.")

    st.markdown("---")
    if df.empty: df, err = load_all_data()
    if df.empty:
        st.info("Aucune donnée chargée.")
        return

    # --- 4. AFFICHAGE PRINCIPAL ---
    tab_indiv, tab_team = st.tabs(["PROFIL INDIVIDUEL", "ANALYSE COLLECTIVE"])

    with tab_indiv:
        all_players = sorted(df['Joueur'].unique())
        col_sel, _ = st.columns([1, 2])
        with col_sel: p_sel = st.selectbox("Rechercher un joueur :", all_players)
        
        row = df[df['Joueur'] == p_sel].iloc[0]
        
        poids_col_name = find_column_in_df(df, "Poids")
        poids_joueur = clean_numeric_value(row.get(poids_col_name))
        
        col_poste = find_column_in_df(df, "Poste")
        col_lat = find_column_in_df(df, "Latéralité")
        col_num = find_number_column(df)
        val_num = f"#{int(float(row[col_num]))}" if (col_num and col_num in row and pd.notna(row[col_num])) else ""
        val_poste = row[col_poste] if col_poste else "-"
        val_lat = row[col_lat] if col_lat else "-"

        anthro_vals = {}
        for label in ["Taille", "Poids", "Masse Grasse Plis (mm)"]:
            col_name = find_column_in_df(df, label)
            val = clean_numeric_value(row.get(col_name))
            unit = " cm" if label == "Taille" else " kg" if label == "Poids" else " mm"
            anthro_vals[label] = f"{smart_format(val)}{unit}" if val else "-"

        photo_path = get_best_photo_path(p_sel) 
        img_src = f"data:image/png;base64,{img_to_b64(photo_path)}" if photo_path else ""
        img_html = f'<img src="{img_src}" class="hero-photo">' if img_src else '<div class="hero-photo" style="display:flex;align-items:center;justify-content:center;background:#222;color:#555;font-size:10px;">PHOTO</div>'
        
        st.markdown(f"""
<div class="hero-container">
<div class="hero-left">{img_html}<div class="hero-details"><div class="hero-name">{p_sel}</div><div class="hero-number">{val_num}</div><div class="hero-meta">{val_poste} | {val_lat}</div></div></div>
<div class="hero-right">
<div class="stat-box"><div class="stat-label">TAILLE</div><div class="stat-value">{anthro_vals['Taille']}</div></div>
<div class="stat-box"><div class="stat-label">POIDS</div><div class="stat-value">{anthro_vals['Poids']}</div></div>
<div class="stat-box"><div class="stat-label">Masse Grasse</div><div class="stat-value">{anthro_vals['Masse Grasse Plis (mm)']}</div></div>
</div>
</div>
""", unsafe_allow_html=True)
        
   # ---------------------------------------------------------------------
        # DÉBUT DU BLOC : RADAR GPS & TABLEAU (DESIGN PREMIUM + LÉGENDE)
        # ---------------------------------------------------------------------

        # 1. Configuration
        radar_config = [
            {"label": "Vmax", "cols": ["Vmax"]},
            {"label": "Amax", "cols": ["Amax"]},
            {"label": "Dmax", "cols": ["Dmax"]},
            {"label": "Dist. Totale", "cols": ["Distance Totale"]},
            {"label": "Dist. HSR", "cols": ["Distance HSR"]},
            {"label": "Sprint (>92%)", "cols": ["Distance Sprint (92% Vmax)"]}
        ]
        
        # 2. Préparation des données
        row_updated = df[df['Joueur'] == p_sel].iloc[0]
        radar_labels = []
        radar_values = []
        table_rows_data = []

        for item in radar_config:
            radar_labels.append(item['label'])
            sum_p = 0
            count = 0
            
            # Variables d'affichage par défaut
            val_str = "-"
            norm_str = ""
            
            for col_key in item['cols']:
                col_name = COL_MAPPING.get(col_key, col_key)
                val = clean_numeric_value(row_updated.get(col_name))
                
                if col_name and val is not None:
                    try:
                        # Calcul Score
                        _, p = calculate_percentile(df, col_name, val)
                        sum_p += p
                        count += 1
                        
                        # Formatage Valeur + Unité
                        unit = UNITS.get(col_key, "")
                        if val > 100: 
                            val_str = f"{int(val)} {unit}"
                        else: 
                            val_str = f"{val:.2f} {unit}"
                        
                        # Récupération de la Norme (Objectif)
                        norm_key = next((k for k in REPORT_NORMES.keys() if k == col_key), None)
                        if not norm_key:
                            norm_key = next((k for k in REPORT_NORMES.keys() if k in col_key), None)
                            
                        if norm_key:
                            low, high = REPORT_NORMES[norm_key]
                            norm_str = f"Obj: {low}-{high}"
                            
                    except: pass
            
            final_score = sum_p / count if count > 0 else 0
            radar_values.append(final_score)
            
            table_rows_data.append({
                "label": item['label'], 
                "value_display": val_str,
                "norm_display": norm_str,
                "score": int(final_score)
            })

        # 3. Affichage
        c_radar, c_table = st.columns([3, 2])
        
        with c_radar:
            radar_b64 = create_radar_chart(radar_labels, radar_values, text_color="white")
            st.image(f"data:image/png;base64,{radar_b64}", use_container_width=True)

        with c_table:
            # --- AJOUT DU HEADER EXPLICATIF ---
            # C'est ici qu'on explique ce qu'est le score
            st.markdown("""
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding:0 5px; border-bottom:1px solid #444; padding-bottom:5px;'>
                <span style='color:#AAA; font-size:11px; font-weight:bold; letter-spacing:1px;'>INDICATEURS CLÉS</span>
                <span style='color:#AAA; font-size:10px; display:flex; align-items:center;'>
                    SCORE (PERCENTILE) &nbsp;
                    <span title="Le score sur 100 représente le classement du joueur par rapport au reste du groupe (Percentile)." style="cursor:help; font-size:14px;">ℹ️</span>
                </span>
            </div>
            """, unsafe_allow_html=True)

            # --- LISTE DES CARTES ---
            html_content = "<div style='display:flex; flex-direction:column; gap:8px;'>"
            
            for row_data in table_rows_data:
                score = row_data['score']
                color = "#27ae60" if score > 66 else "#F39C12" if score > 33 else "#D71920"
                
                # J'ajoute un 'title' au badge pour expliquer au survol
                card_html = f"<div style='background-color:#2b2d3e; border-radius:6px; padding:8px 12px; border-left:4px solid {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>" \
                            f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;'>" \
                            f"<span style='color:#FFF; font-weight:bold; font-size:14px;'>{row_data['label']}</span>" \
                            f"<span title='Percentile : Mieux que {score}% des joueurs' style='cursor:help; background-color:{color}; color:white; padding:1px 6px; border-radius:4px; font-size:11px; font-weight:bold;'>{score}/100</span>" \
                            f"</div>" \
                            f"<div style='display:flex; justify-content:space-between; align-items:center; font-size:12px;'>" \
                            f"<span style='color:#EEE;'>{row_data['value_display']}</span>" \
                            f"<span style='color:#888; font-style:italic;'>{row_data['norm_display']}</span>" \
                            f"</div>" \
                            f"</div>"
                
                html_content += card_html
            
            html_content += "</div>"
            st.markdown(html_content, unsafe_allow_html=True)


        

        # --- LEGENDE ---
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
<div style="background-color: #1E1E2D; padding: 15px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #3F4254; font-size: 14px;">
<div style="font-weight:bold; margin-bottom:15px; color:#FFF; text-transform:uppercase; border-bottom:1px solid #444; padding-bottom:5px;">Lecture des Indicateurs</div>
<div style="display:flex; flex-wrap:wrap; gap: 40px;">
<div style="flex:1; min-width:250px;">
<div style="font-weight:bold; color:#A1A5B7; font-size:13px; margin-bottom:8px;"> 1. Barre de couleurs (Percentile) = GROUPE</div>
<div style="font-size:12px; color:#CCC; margin-bottom:5px;">Indique le classement du joueur par rapport à <b>l'effectif</b>.</div>
<div style="display:flex; align-items:center; gap:5px; font-size:11px; color:#888;">
<div style="width:30px; height:6px; background:#D71920; border-radius:3px;"></div> &lt; 33%
<div style="width:30px; height:6px; background:#F39C12; border-radius:3px;"></div> 33-66%
<div style="width:30px; height:6px; background:#27AE60; border-radius:3px;"></div> &gt; 66%
</div>
</div>
<div style="flex:1; min-width:250px;">
<div style="font-weight:bold; color:#A1A5B7; font-size:13px; margin-bottom:8px;"> 2. Couleur du nombre = NORME</div>
<div style="font-size:12px; color:#CCC; margin-bottom:5px;">Indique si la performance respecte la <b>norme fixée</b>.</div>
<div style="display:flex; gap:15px; font-size:12px; font-weight:bold;">
<span style="color:white;">Exemple : </span>
<span style="color:#D71920;">15.0 (Hors Obj.)</span>
<span style="color:#F39C12;">18.0 (Limite)</span>
<span style="color:#27AE60;">22.0 (Au-dessus)</span>
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='text-align:center; font-size:11px; color:#aaa; font-style:italic; margin-top:-15px; margin-bottom:15px;'>* Pour les tests bilatéraux (G/D), le percentile affiché est la moyenne des deux côtés.</div>", unsafe_allow_html=True)

        use_relative = st.session_state.get("use_relative_mode", False)

        # =============================================================================
        # 1. DÉFINITION DES FONCTIONS D'AFFICHAGE (ROBUSTES ET DYNAMIQUES)
        # =============================================================================
        
        def get_data_smart(label, use_rel_mode):
            """
            Récupère intelligemment les données (Absolues ou Relatives) pour un indicateur.
            Retourne : (Valeur, Colonne_utilisée_pour_percentile, Unité, Label_Secondaire)
            """
            col_abs = get_col_name(label)
            val_abs = clean_numeric_value(row.get(col_abs))
            
            # Unités de base
            unit_abs = get_unit(label) 
            is_force_or_power = any(u in unit_abs for u in ["N", "W", "kg"]) and "cm" not in unit_abs and "s" not in unit_abs
            
            # Si on n'est pas en mode relatif ou si l'unité ne s'y prête pas (cm, s, deg...), on renvoie l'absolu
            if not use_rel_mode or not is_force_or_power or val_abs is None:
                _, pct = calculate_percentile(df, col_abs, val_abs)
                rel_txt = get_rel_display_smart(row, label, val_abs, poids_joueur)
                return val_abs, pct, unit_abs, rel_txt, "abs"

            # --- MODE RELATIF ACTIVÉ ---
            
            # 1. Chercher si une colonne relative existe déjà dans l'Excel
            potential_suffixes = [" (N/kg)", " (W/kg)", " N/kg", " W/kg", " (Relatif)", " Relatif"]
            col_rel = None
            for suff in potential_suffixes:
                candidate = col_abs + suff
                if candidate in df.columns:
                    col_rel = candidate
                    break
            
            # Cas spécial : parfois le nom absolu a des parenthèses ex: "Wattbike (6s)" -> "Wattbike (W/kg)"
            if not col_rel and "(" in col_abs:
                base = col_abs.split("(")[0].strip()
                for suff in potential_suffixes:
                    candidate = base + suff
                    if candidate in df.columns:
                        col_rel = candidate
                        break

            # 2. Si colonne trouvée -> On l'utilise
            if col_rel:
                val_rel = clean_numeric_value(row.get(col_rel))
                _, pct_rel = calculate_percentile(df, col_rel, val_rel)
                unit_rel = "N/kg" if "N" in unit_abs else "W/kg" if "W" in unit_abs else "ratio"
                sub_txt = f"{smart_format(val_abs)} {unit_abs}" # L'absolu devient le secondaire
                return val_rel, pct_rel, unit_rel, sub_txt, "rel"
            
            # 3. Si colonne NON trouvée -> On CALCULE (Fallback mathématique)
            elif poids_joueur and poids_joueur > 0:
                val_rel = val_abs / poids_joueur
                unit_rel = "N/kg" if "N" in unit_abs else "W/kg" if "W" in unit_abs else "ratio"
                
                # Pour le percentile, on doit créer une série temporaire : Col_Absolue / Col_Poids
                # On suppose que la colonne poids s'appelle "Poids (Kg)" ou "Poids"
                col_poids_name = None
                for c in df.columns:
                    if "poids" in c.lower() and ("kg" in c.lower() or c.lower() == "poids"):
                        col_poids_name = c
                        break
                
                if col_poids_name:
                    # Calcul vectoriel pour le classement
                    try:
                        # On évite la division par zéro
                        serie_rel = df[col_abs] / df[col_poids_name].replace(0, np.nan)
                        # Calcul du percentile sur cette série calculée
                        if pd.isna(val_rel): pct_rel = 0
                        else:
                            import scipy.stats as stats
                            clean_series = serie_rel.dropna()
                            pct_rel = stats.percentileofscore(clean_series, val_rel, kind='weak')
                        
                        sub_txt = f"{smart_format(val_abs)} {unit_abs}"
                        return val_rel, pct_rel, unit_rel, sub_txt, "rel"
                    except:
                        pass # Echec calcul vectoriel

            # Si tout échoue, retour à l'absolu
            _, pct = calculate_percentile(df, col_abs, val_abs)
            return val_abs, pct, unit_abs, None, "abs"


        def render_single_kpi(label, subtitle=None):
            # Récupération dynamique
            val, pct, unit, sub_text, mode = get_data_smart(label, use_relative)
            
            # Couleurs (basées sur la valeur affichée ou l'absolue pour la norme texte ?)
            # Pour la norme texte (Objective), on garde souvent l'absolu car les objectifs relatifs sont rares.
            # MAIS pour la barre de couleur, on utilise le percentile calculé (donc relatif si mode relatif)
            
            bar_w = max(5, int(pct)) if val is not None else 0
            bar_col = get_bar_color(pct)
            
            # Couleur du texte : On garde la logique "Norme Absolue" pour savoir si c'est vert/rouge
            # car c'est souvent là que sont définis les seuils.
            col_abs_name = get_col_name(label)
            val_abs_ref = clean_numeric_value(row.get(col_abs_name))
            status_res = get_status_data_local(label, val_abs_ref)
            if len(status_res) == 3: color, _, txt_col = status_res
            else: color, txt_col = status_res[0], "#FFF"

            val_display = f"{smart_format(val)} <span style='font-size:14px; color:#aaa; font-weight:normal;'>{unit}</span>"
            
            # Le badge secondaire
            if mode == "rel":
                # En mode relatif, le secondaire est l'absolu (déjà formaté dans sub_text)
                sub_html = f"<div style='background:#3b3e54; color:#fff; padding:4px 8px; border-radius:6px; font-size:12px; font-weight:bold;'>{sub_text}</div>"
            else:
                # En mode absolu, le secondaire est le relatif (si dispo)
                sub_html = f"<div style='background:#3b3e54; color:#fff; padding:4px 8px; border-radius:6px; font-size:12px; font-weight:bold;'>{sub_text}</div>" if sub_text else ""

            sub_title_html = f"<div style='font-size:12px; color:#888; margin-top:-2px; margin-bottom:8px; font-style:italic;'>{subtitle}</div>" if subtitle else ""
            norm_txt = get_norm_text(label).replace('Obj: ', '')
            tip = get_tooltip_html(row, label)

            st.markdown(f"""
<div class="kpi-card" {tip} style="padding:15px; border:1px solid #3b3e54; background:#1e1e2d; border-radius:10px; margin-bottom:15px;">
<div class="kpi-top" style="margin-bottom:5px;">
<div class="kpi-lbl" style="font-size:16px; font-weight:bold; color:#FFF; text-transform:uppercase; letter-spacing:1px;">{label}</div>
</div>
{sub_title_html}
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; background:#2b2d3e; padding:10px; border-radius:8px;">
<div style="font-size:28px; font-weight:900; color:{txt_col}; line-height:1;">{val_display}</div>
{sub_html}
</div>
<div style="margin-bottom:12px;">
<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
<span style="font-size:11px; color:#888;">Niveau ({'Poids de corps' if mode=='rel' else 'Groupe'})</span>
<span style="font-size:11px; font-weight:bold; color:{bar_col};">Top {int(pct)}%</span>
</div>
<div class="progress-bg" style="height:10px; background:#151520; border-radius:5px;">
<div class="progress-fill" style="width: {bar_w}%; background-color: {bar_col}; height:100%; border-radius:5px;"></div>
</div>
</div>
<div class="kpi-footer" style="background:#2b2d3e; padding:8px 12px; border-radius:6px; border-left:4px solid #7f8c8d;">
<div style="display:flex; flex-direction:column;">
<span style="color:#888; font-size:10px; font-weight:bold; text-transform:uppercase;">Objectif / Norme</span>
<span style="color:#FFF; font-size:13px; font-weight:bold;">{norm_txt}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

        def render_pair_kpi(l_label, r_label):
            # Récupération Gauche
            val_l, pct_l, unit_l, sub_l, mode_l = get_data_smart(l_label, use_relative)
            # Récupération Droite
            val_r, pct_r, unit_r, sub_r, mode_r = get_data_smart(r_label, use_relative)
            
            # Couleurs texte
            st_l = get_status_data_local(l_label, clean_numeric_value(row.get(get_col_name(l_label))))
            txt_l = st_l[2] if len(st_l) == 3 else "#FFF"
            st_r = get_status_data_local(r_label, clean_numeric_value(row.get(get_col_name(r_label))))
            txt_r = st_r[2] if len(st_r) == 3 else "#FFF"
            
            # Calcul Asymétrie (Toujours sur l'absolu)
            col_l_abs, col_r_abs = get_col_name(l_label), get_col_name(r_label)
            val_l_abs, val_r_abs = clean_numeric_value(row.get(col_l_abs)), clean_numeric_value(row.get(col_r_abs))
            asym_pct, weak_side = get_asym_badge_info(val_l_abs, val_r_abs, df, col_l_abs, col_r_abs)
            
            # --- LOGIQUE 3 COULEURS ---
            asym_html = ""
            if asym_pct is not None:
                if asym_pct < 10:
                    # VERT : Équilibré
                    asym_html = f"""
<div style='background:rgba(39, 174, 96, 0.15); border:1px solid #27AE60; color:#a2f0c3; padding:6px 10px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>
Équilibré ({asym_pct:.0f}%)
</div>"""
                elif 10 <= asym_pct < 15:
                    # ORANGE : Attention
                    asym_html = f"""
<div style='background:rgba(243, 156, 18, 0.15); border:1px solid #F39C12; color:#fce5cd; padding:6px 10px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>
⚠ Attention {weak_side} ({asym_pct:.0f}%)
</div>"""
                else:
                    # ROUGE : Déséquilibre
                    asym_html = f"""
<div style='background:rgba(215, 25, 32, 0.15); border:1px solid #D71920; color:#ffcccc; padding:6px 10px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>
Déficit {weak_side} ({asym_pct:.0f}%)
</div>"""
            
            clean_title = get_clean_label(l_label)

            # NOTE IMPORTANTE : LE HTML CI-DESSOUS EST COLLÉ A GAUCHE POUR EVITER LE BUG
            st.markdown(f"""
<div class="kpi-card" style="padding:15px; border:1px solid #3b3e54; background:#1e1e2d; border-radius:10px; margin-bottom:15px;">
<div class="kpi-lbl" style="font-size:16px; font-weight:bold; color:#FFF; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; border-bottom:1px solid #3b3e54; padding-bottom:5px;">{clean_title}</div>
{asym_html}
<div style="margin-bottom:15px;">
<div style="display:flex; align-items:center; margin-bottom:5px;">
<div style="background:#3498db; color:white; font-weight:bold; padding:2px 8px; border-radius:4px; font-size:12px; margin-right:8px;">G</div>
<div style="font-size:20px; font-weight:bold; color:{txt_l};">{smart_format(val_l)} <span style="font-size:12px; color:#888;">{unit_l}</span></div>
<div style="margin-left:auto; background:#2b2d3e; color:#ccc; padding:2px 6px; border-radius:4px; font-size:11px;">{sub_l if sub_l else '-'}</div>
</div>
<div style="background:#151520; height:8px; border-radius:4px; width:100%;">
<div style="width:{max(5, int(pct_l))}%; height:100%; background:{get_bar_color(pct_l)}; border-radius:4px;"></div>
</div>
</div>
<div style="margin-bottom:5px;">
<div style="display:flex; align-items:center; margin-bottom:5px;">
<div style="background:#e74c3c; color:white; font-weight:bold; padding:2px 8px; border-radius:4px; font-size:12px; margin-right:8px;">D</div>
<div style="font-size:20px; font-weight:bold; color:{txt_r};">{smart_format(val_r)} <span style="font-size:12px; color:#888;">{unit_r}</span></div>
<div style="margin-left:auto; background:#2b2d3e; color:#ccc; padding:2px 6px; border-radius:4px; font-size:11px;">{sub_r if sub_r else '-'}</div>
</div>
<div style="background:#151520; height:8px; border-radius:4px; width:100%;">
<div style="width:{max(5, int(pct_r))}%; height:100%; background:{get_bar_color(pct_r)}; border-radius:4px;"></div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        def render_muscle_group_card(title_main, l_label, r_label, sum_label):
            # Récupération intelligente
            val_l, pct_l, unit_l, sub_l, _ = get_data_smart(l_label, use_relative)
            val_r, pct_r, unit_r, sub_r, _ = get_data_smart(r_label, use_relative)
            val_s, pct_s, unit_s, sub_s, _ = get_data_smart(sum_label, use_relative)

            # Couleurs (Absolu)
            txt_l = get_status_data_local(l_label, clean_numeric_value(row.get(get_col_name(l_label))))[2] if len(get_status_data_local(l_label, 0))==3 else "#FFF"
            txt_r = get_status_data_local(r_label, clean_numeric_value(row.get(get_col_name(r_label))))[2] if len(get_status_data_local(r_label, 0))==3 else "#FFF"
            txt_s = get_status_data_local(sum_label, clean_numeric_value(row.get(get_col_name(sum_label))))[2] if len(get_status_data_local(sum_label, 0))==3 else "#FFF"
            
            norm_s = get_norm_text(sum_label).replace('Obj: ', '')
            
            # Asymétrie (Absolu)
            asym_pct, weak_side = get_asym_badge_info(clean_numeric_value(row.get(get_col_name(l_label))), clean_numeric_value(row.get(get_col_name(r_label))), df, get_col_name(l_label), get_col_name(r_label))
            
            # --- LOGIQUE 3 COULEURS ---
            asym_html = ""
            if asym_pct is not None:
                if asym_pct < 10:
                    # VERT
                    asym_html = f"""
<div style='background:rgba(39, 174, 96, 0.15); border:1px solid #27AE60; color:#a2f0c3; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>
Équilibré ({asym_pct:.0f}%)
</div>"""
                elif 10 <= asym_pct < 15:
                    # ORANGE
                    asym_html = f"""
<div style='background:rgba(243, 156, 18, 0.15); border:1px solid #F39C12; color:#fce5cd; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>
⚠ Attention {weak_side} ({asym_pct:.0f}%)
</div>"""
                else:
                    # ROUGE
                    asym_html = f"""
<div style='background:rgba(215, 25, 32, 0.15); border:1px solid #D71920; color:#ffcccc; padding:6px; border-radius:6px; font-size:12px; font-weight:bold; text-align:center; margin-bottom:12px;'>
Déficit {weak_side} ({asym_pct:.0f}%)
</div>"""

            st.markdown(f"""
<div class="kpi-card" style="padding:15px; border:1px solid #3b3e54; background:#1e1e2d; border-radius:10px; margin-bottom:15px;">
<div class="kpi-lbl" style="font-size:16px; font-weight:bold; color:#FFF; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px; border-bottom:1px solid #3b3e54; padding-bottom:5px;">{title_main}</div>
{asym_html}
<div style="background:#2b2d3e; padding:10px; border-radius:8px; margin-bottom:12px;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
<span style="color:#3498db; font-weight:900;">G</span>
<span style="font-size:16px; font-weight:bold; color:{txt_l}">{smart_format(val_l)} <span style="font-size:10px; color:#888;">{unit_l}</span></span>
<span style="font-size:10px; background:#3b3e54; padding:2px 4px; border-radius:3px;">{sub_l if sub_l else '-'}</span>
</div>
<div style="background:#151520; height:6px; border-radius:3px; margin-bottom:8px;">
<div style="width:{max(5, int(pct_l))}%; height:100%; background:{get_bar_color(pct_l)}; border-radius:3px;"></div>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
<span style="color:#e74c3c; font-weight:900;">D</span>
<span style="font-size:16px; font-weight:bold; color:{txt_r}">{smart_format(val_r)} <span style="font-size:10px; color:#888;">{unit_r}</span></span>
<span style="font-size:10px; background:#3b3e54; padding:2px 4px; border-radius:3px;">{sub_r if sub_r else '-'}</span>
</div>
<div style="background:#151520; height:6px; border-radius:3px;">
<div style="width:{max(5, int(pct_r))}%; height:100%; background:{get_bar_color(pct_r)}; border-radius:3px;"></div>
</div>
</div>
<div style="margin-top:5px; border-top:1px dashed #444; padding-top:10px;">
<div style="display:flex; justify-content:space-between; align-items:end; margin-bottom:5px;">
<span style="font-size:12px; font-weight:bold; color:#CCC;">FORCE TOTALE</span>
<div style="text-align:right; line-height:1.2;">
<div style="font-size:20px; font-weight:bold; color:{txt_s};">{smart_format(val_s)} <span style="font-size:12px; color:#888;">{unit_s}</span></div>
<div style="font-size:11px; color:#aaa;">{sub_s if sub_s else '-'}</div>
</div>
</div>
<div style="display:flex; justify-content:space-between; margin-bottom:2px;">
<span style="font-size:11px; color:#666; font-weight:bold;">NORME: {norm_s}</span>
<span style="font-size:11px; color:{get_bar_color(pct_s)}; font-weight:bold;">Top {int(pct_s)}%</span>
</div>
<div style="background:#151520; height:8px; border-radius:4px;">
<div style="width:{max(5, int(pct_s))}%; height:100%; background:{get_bar_color(pct_s)}; border-radius:4px;"></div>
</div>
</div>
</div>""", unsafe_allow_html=True)
        def render_wellness_combined():
            # Pas de relatif pour le wellness
            val_s = clean_numeric_value(row.get("Score Sommeil"))
            _, pct_s = calculate_percentile(df, "Score Sommeil", val_s)
            col_s = get_bar_color(pct_s)
            
            val_n = clean_numeric_value(row.get("Score Nutrition"))
            _, pct_n = calculate_percentile(df, "Score Nutrition", val_n)
            col_n = get_bar_color(pct_n)

            st.markdown(f"""
<div class="kpi-card" style="padding:20px; background:#1e1e2d; border-radius:10px; border:1px solid #3b3e54; margin-bottom:20px;">
<div class="kpi-lbl" style="font-size:18px; font-weight:bold; color:#FFF; text-transform:uppercase; margin-bottom:15px; border-bottom:1px solid #444; padding-bottom:10px;">BIEN-ÊTRE & RÉCUPÉRATION</div>
<div style="display:flex; gap:30px;">
<div style="flex:1;">
<div style="display:flex; align-items:center; margin-bottom:10px;">
<span style="font-size:24px; margin-right:10px;">💤</span>
<div>
<div style="font-size:14px; color:#aaa; font-weight:bold;">SOMMEIL</div>
<div style="font-size:32px; font-weight:bold; color:#FFF; line-height:1;">{smart_format(val_s)}<span style="font-size:16px; color:#666;">/10</span></div>
</div>
</div>
<div style="background:#151520; height:12px; border-radius:6px; margin-bottom:5px;">
<div style="width:{max(5, int(pct_s))}%; height:100%; background:{col_s}; border-radius:6px;"></div>
</div>
<div style="text-align:right; font-size:12px; font-weight:bold; color:{col_s};">Meilleur que {int(pct_s)}% de l'équipe</div>
</div>
<div style="width:1px; background:#3b3e54;"></div>
<div style="flex:1;">
<div style="display:flex; align-items:center; margin-bottom:10px;">
<span style="font-size:24px; margin-right:10px;">🥦</span>
<div>
<div style="font-size:14px; color:#aaa; font-weight:bold;">NUTRITION</div>
<div style="font-size:32px; font-weight:bold; color:#FFF; line-height:1;">{smart_format(val_n)}<span style="font-size:16px; color:#666;">/10</span></div>
</div>
</div>
<div style="background:#151520; height:12px; border-radius:6px; margin-bottom:5px;">
<div style="width:{max(5, int(pct_n))}%; height:100%; background:{col_n}; border-radius:6px;"></div>
</div>
<div style="text-align:right; font-size:12px; font-weight:bold; color:{col_n};">Meilleur que {int(pct_n)}% de l'équipe</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        def render_subheader(title):
            st.markdown(f"<div style='color:#7f8c8d; font-size:14px; font-weight:bold; margin-top:20px; margin-bottom:10px; border-left:3px solid #E74C3C; padding-left:10px;'>{title}</div>", unsafe_allow_html=True)

        # =============================================================================
        # 2. AFFICHAGE MANUEL STRUCTURÉ (CORRIGÉ : PLEINE LARGEUR POUR SOLOS)
        # =============================================================================
        
        # --- PROFILAGE MOTEUR ---
        st.markdown(f"<div class='section-header' style='font-size:22px; margin-top:30px; margin-bottom:10px; border-bottom:2px solid #555; padding-bottom:5px;'>PROFILAGE MOTEUR</div>", unsafe_allow_html=True)

        render_subheader("FORCE")
        # Ici on garde les colonnes car ils sont 3
        c_add, c_sq, c_abd = st.columns([1.3, 0.7, 1.3])
        with c_add: render_muscle_group_card("ADDUCTEURS", "Adducteurs (G)", "Adducteurs (D)", "Somme ADD")
        with c_sq: 
            st.markdown("<br><br>", unsafe_allow_html=True)
            render_single_kpi("Ratio Squeeze")
        with c_abd: render_muscle_group_card("ABDUCTEURS", "Abducteurs (G)", "Abducteurs (D)", "Somme ABD")
        render_pair_kpi("Nordic Ischio (G)", "Nordic Ischio (D)")

              # ---------------------------------------------------------------------
        # AJOUT : RADAR BIODEX (RELATIF - G/D/NORME)
        # ---------------------------------------------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:15px; font-size:16px; font-weight:bold; color:#FFF; border-bottom:2px solid #D71920; padding-bottom:5px;'>RADAR BIODEX (VALEURS RELATIVES)</div>", unsafe_allow_html=True)

        # 1. CONFIGURATION DES OBJECTIFS (NORMES N/KG)
        targets = {
            "Q 60°": 3.0,
            "Q 240°": 1.8,
            "IJ 60°": 1.8,
            "IJ 240°": 1.4,
            "IJ Exc 30°": 2.5
            # "Q Exc 30°": 3.5  <-- Désactivé car absent du fichier CSV
        }

        # 2. MAPPING EXACT DES COLONNES (Basé sur votre fichier)
        # Structure : Label -> { Relatif G/D (pour radar), Brut G/D (pour tableau) }
        biodex_full_config = [
            {
                "label": "Q 60°",
                "g_rel": "Q G conc 60°/s (N/kg)", "d_rel": "Q Dt conc 60°/s (N/kg)",
                "g_raw": "Q G conc 60°/s",        "d_raw": "Q Dt conc 60°/s"
            },
            {
                "label": "Q 240°",
                "g_rel": "Q G conc 240°/s (N/kg)", "d_rel": "Q Dt conc 240°/s (N/kg)",
                "g_raw": "Q G conc 240°/s",        "d_raw": "Q Dt conc 240°/s"
            },
            {
                "label": "IJ 60°",
                "g_rel": "IJ G conc 60°/s (N/kg)", "d_rel": "IJ Dt conc 60°/s (N/kg)",
                "g_raw": "IJ G conc 60°/s",        "d_raw": "IJ Dt conc 60°/s"
            },
            {
                "label": "IJ 240°",
                "g_rel": "IJ G conc 240°/s (N/kg)", "d_rel": "IJ Dt conc 240°/s (N/kg)",
                "g_raw": "IJ G conc 240°/s",        "d_raw": "IJ Dt conc 240°/s"
            },
            {
                "label": "IJ Exc 30°",
                # Attention : "Exc" (G) vs "exc" (Dt) dans vos en-têtes
                "g_rel": "IJ G Exc 30°/s (N/kg)", "d_rel": "IJ Dt exc 30°/s (N/kg)",
                "g_raw": "IJ G Exc 30°/s",        "d_raw": "IJ Dt exc 30°/s"
            }
        ]

        radar_cats = []
        vals_l_rel = []
        vals_r_rel = []
        vals_norm = []
        
        table_data = [] 

        # 3. BOUCLE DE RÉCUPÉRATION
        for item in biodex_full_config:
            lbl = item["label"]
            radar_cats.append(lbl)
            vals_norm.append(targets.get(lbl, 0))
            
            # -- Radar : Valeurs RELATIVES (N/kg) --
            # On utilise .get() direct sur la ligne (row) avec le nom exact
            # Si vous utilisez une fonction find_column, assurez-vous qu'elle trouve le nom exact
            col_g_rel = item["g_rel"]
            col_d_rel = item["d_rel"]
            
            # Utilisation de find_column_in_df si nécessaire, sinon accès direct si les colonnes sont standardisées
            # Ici, je force la recherche pour être sûr
            real_col_g_rel = find_column_in_df(df, col_g_rel) or col_g_rel
            real_col_d_rel = find_column_in_df(df, col_d_rel) or col_d_rel

            v_g_rel = clean_numeric_value(row.get(real_col_g_rel))
            v_d_rel = clean_numeric_value(row.get(real_col_d_rel))
            
            vals_l_rel.append(v_g_rel if v_g_rel is not None else 0)
            vals_r_rel.append(v_d_rel if v_d_rel is not None else 0)
            
            # -- Tableau : Valeurs BRUTES (Nm) --
            col_g_raw = item["g_raw"]
            col_d_raw = item["d_raw"]
            
            real_col_g_raw = find_column_in_df(df, col_g_raw) or col_g_raw
            real_col_d_raw = find_column_in_df(df, col_d_raw) or col_d_raw
            
            v_g_raw = clean_numeric_value(row.get(real_col_g_raw))
            v_d_raw = clean_numeric_value(row.get(real_col_d_raw))

            # Calcul LSI sur le brut
            s_lsi = "-"
            c_lsi = "#888"
            if v_g_raw is not None and v_d_raw is not None:
                mx = max(v_g_raw, v_d_raw)
                if mx > 0:
                    lsi = ((v_d_raw - v_g_raw) / mx) * 100
                    s_lsi = f"{lsi:.0f}%"
                    if abs(lsi) > 10: c_lsi = "#D71920"
                    elif abs(lsi) > 5: c_lsi = "#F39C12"
                    else: c_lsi = "#27AE60"
            
            table_data.append({
                "label": lbl,
                "v_g": f"{v_g_raw:.0f}" if v_g_raw is not None else "-",
                "v_d": f"{v_d_raw:.0f}" if v_d_raw is not None else "-",
                "lsi": s_lsi,
                "c_lsi": c_lsi
            })

        # 4. AFFICHAGE RADAR (RELATIF) - VERSION OPTIMISÉE ERGONOMIE
        c_left, c_center, c_right = st.columns([0.2, 3, 0.2]) 
        with c_center:
            if not radar_cats:
                st.warning("Aucune donnée Biodex configurée trouvée.")
            else:
                import plotly.graph_objects as go
                
                # Calcul de l'échelle max
                max_data = max(max(vals_l_rel), max(vals_r_rel), max(vals_norm))
                limit_scale = max(4.0, max_data * 1.1)
                
                # Bouclage des données
                cats_closed = radar_cats + [radar_cats[0]]
                l_closed = vals_l_rel + [vals_l_rel[0]]
                r_closed = vals_r_rel + [vals_r_rel[0]]
                n_closed = vals_norm + [vals_norm[0]]

                fig = go.Figure()

                # --- TRACE OBJECTIF (Fond de référence) ---
                fig.add_trace(go.Scatterpolar(
                    r=n_closed,
                    theta=cats_closed,
                    fill='toself', # Remplissage léger pour visualiser l'aire cible
                    name='Objectif',
                    mode='lines', # Pas de points pour l'objectif, juste la ligne
                    line=dict(color='#2ECC71', dash='dash', width=2),
                    fillcolor='rgba(46, 204, 113, 0.1)', # Très transparent
                    hoverinfo='skip' # On ne peut pas cliquer dessus (ne gêne pas la navigation)
                ))

                # --- TRACE GAUCHE (Interactive) ---
                fig.add_trace(go.Scatterpolar(
                    r=l_closed,
                    theta=cats_closed,
                    name='Gauche',
                    mode='lines+markers', # Ligne + Points (pour faciliter la visée)
                    fill='toself',
                    line=dict(color='#3498DB', width=3),
                    marker=dict(size=8, color='#3498DB', symbol='circle'), # Gros points faciles à viser
                    fillcolor='rgba(52, 152, 219, 0.15)',
                    hoveron='points', # L'info-bulle ne s'affiche QUE sur les points (plus précis)
                    hovertemplate='<b>Gauche</b><br>%{theta}: <b>%{r:.2f}</b> N/kg<extra></extra>'
                ))

                # --- TRACE DROITE (Interactive) ---
                fig.add_trace(go.Scatterpolar(
                    r=r_closed,
                    theta=cats_closed,
                    name='Droite',
                    mode='lines+markers',
                    fill='toself',
                    line=dict(color='#E74C3C', width=3),
                    marker=dict(size=8, color='#E74C3C', symbol='circle'), # Gros points
                    fillcolor='rgba(231, 76, 60, 0.15)',
                    hoveron='points', # Évite les conflits de superposition
                    hovertemplate='<b>Droite</b><br>%{theta}: <b>%{r:.2f}</b> N/kg<extra></extra>'
                ))

                # --- MISE EN PAGE ---
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, limit_scale],
                            showticklabels=True,
                            tickfont=dict(color="gray", size=9),
                            gridcolor="#444",
                            linecolor="#444",
                            layer="below traces" # La grille reste derrière
                        ),
                        angularaxis=dict(
                            tickfont=dict(color="white", size=12, weight="bold"),
                            gridcolor="#555",
                            linecolor="white",
                            layer="below traces"
                        ),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=40, r=40, t=20, b=20),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.1,
                        xanchor="center",
                        x=0.5,
                        font=dict(color="white", size=12)
                    ),
                    height=450,
                    hovermode="closest" # Important pour sélectionner le point le plus proche
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

       # 5. TABLEAU (BRUT)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("###### Résultats Détaillés (Nm)")
        
        html_rows = ""
        for item in biodex_full_config:
            lbl = item["label"]
            # Recup valeurs (identique à avant)
            col_g_raw, col_d_raw = item["g_raw"], item["d_raw"]
            real_col_g_raw = find_column_in_df(df, col_g_raw) or col_g_raw
            real_col_d_raw = find_column_in_df(df, col_d_raw) or col_d_raw
            v_g_raw = clean_numeric_value(row.get(real_col_g_raw))
            v_d_raw = clean_numeric_value(row.get(real_col_d_raw))

            # Calcul LSI et COULEURS
            s_lsi = "-"
            c_lsi = "#888"
            if v_g_raw is not None and v_d_raw is not None:
                mx = max(v_g_raw, v_d_raw)
                if mx > 0:
                    lsi = ((v_d_raw - v_g_raw) / mx) * 100
                    s_lsi = f"{lsi:.0f}%"
                    
                    # --- COULEURS LSI ---
                    abs_lsi = abs(lsi)
                    if abs_lsi >= 15: 
                        c_lsi = "#D71920" # Rouge
                    elif abs_lsi >= 10: 
                        c_lsi = "#F39C12" # Orange
                    else: 
                        c_lsi = "#27AE60" # Vert
            
            html_rows += f"<tr style='border-bottom:1px solid #444;'><td style='padding:6px; color:#ddd;'>{lbl}</td><td style='text-align:center; color:white;'>{f'{v_g_raw:.0f}' if v_g_raw else '-'}</td><td style='text-align:center; color:white;'>{f'{v_d_raw:.0f}' if v_d_raw else '-'}</td><td style='text-align:center; color:{c_lsi}; font-weight:bold;'>{s_lsi}</td></tr>"

        # Ratio Mixte (Colonnes existantes)
        col_rm_g = find_column_in_df(df, "Ratio Mixte G") or "Ratio Mixte G"
        col_rm_d = find_column_in_df(df, "Ratio Mixte D") or "Ratio Mixte D"
        
        val_rm_g = clean_numeric_value(row.get(col_rm_g))
        val_rm_d = clean_numeric_value(row.get(col_rm_d))

        def get_ratio_color(val):
            if val is None: return "#888"
            if val < 0.8: return "#D71920"
            elif val <= 1.0: return "#F39C12"
            else: return "#27AE60"

        s_rm_g = f"{val_rm_g:.2f}" if val_rm_g is not None else "-"
        s_rm_d = f"{val_rm_d:.2f}" if val_rm_d is not None else "-"
        
        html_rows += f"<tr style='border-top:2px solid #666; background-color:rgba(255,255,255,0.05);'><td style='padding:6px; font-weight:bold; color:white;'>Ratio Mixte</td><td style='text-align:center; font-weight:bold; color:{get_ratio_color(val_rm_g)};'>{s_rm_g}</td><td style='text-align:center; font-weight:bold; color:{get_ratio_color(val_rm_d)};'>{s_rm_d}</td><td style='text-align:center;'>-</td></tr>"

        final_table = f"""
        <table style='width:100%; border-collapse:collapse; font-size:12px; font-family:sans-serif;'>
            <tr style='background-color:#222; color:#AAA; text-transform:uppercase; font-size:10px;'>
                <th style='padding:8px; text-align:left;'>Test</th>
                <th style='padding:8px; text-align:center;'>G (Nm)</th>
                <th style='padding:8px; text-align:center;'>D (Nm)</th>
                <th style='padding:8px; text-align:center;'>LSI</th>
            </tr>
            {html_rows}
        </table>
        """
        st.markdown(final_table, unsafe_allow_html=True)

        render_subheader("MOBILITÉ")
        
        c_mob2, c_mob3 = st.columns(2)
        with c_mob2: render_single_kpi("Sit And Reach")
        with c_mob3: render_pair_kpi("Knee To Wall (G)", "Knee To Wall (D)")
        
        render_subheader("MONITORING")
        # Wellness prend déjà toute la largeur par définition dans sa fonction
        render_wellness_combined()

        # --- PROFILAGE ATHLÉTIQUE ---
        st.markdown(f"<div class='section-header' style='font-size:22px; margin-top:40px; margin-bottom:10px; border-bottom:2px solid #555; padding-bottom:5px;'>PROFILAGE ATHLÉTIQUE</div>", unsafe_allow_html=True)

        render_subheader("EXPLOSIVITÉ")
        # CORRECTION : CMJ est seul -> Pas de colonnes, affichage direct
        render_single_kpi("CMJ (cm)")

        render_subheader("PUISSANCE")
        c_pwr2, c_pwr3 = st.columns(2)
        with c_pwr2: render_single_kpi("Squat Keiser")
        with c_pwr3: render_single_kpi("Tirage Dos Keiser")

        c_pwr1, c_pwr4 = st.columns(2)
        with c_pwr1: render_single_kpi("Wattbike (6s)")
        with c_pwr4: render_single_kpi("Landmine Throw")
        
        c_pwr5, c_pwr6 = st.columns(2)
        with c_pwr5: render_single_kpi("Développé couché (W)")
        with c_pwr6: render_single_kpi("Développé couché (W/kg)")


        # --- PROFILAGE PHYSIOLOGIQUE ---
        st.markdown(f"<div class='section-header' style='font-size:22px; margin-top:40px; margin-bottom:10px; border-bottom:2px solid #555; padding-bottom:5px;'>PROFILAGE PHYSIOLOGIQUE</div>", unsafe_allow_html=True)

        render_subheader("GPS")
        c_gps1, c_gps2, c_gps3 = st.columns(3)
        with c_gps1: render_single_kpi("Amax")
        with c_gps2: render_single_kpi("Dmax")
        with c_gps3: render_single_kpi("Vmax")
        
        c_gps4, c_gps5 = st.columns(2)
        with c_gps4: render_single_kpi("Nb Accélérations")
        with c_gps5: render_single_kpi("Nb Décélérations")

        c_gps6, c_gps7, c_gps8 = st.columns(3)
        with c_gps6: render_single_kpi("Distance HSR")
        with c_gps7: render_single_kpi("Distance Totale")
        with c_gps8 : render_single_kpi("Distance Sprint (92% Vmax)")

        render_subheader("TESTS TERRAIN")
        c_field1, c_field2, c_field3 = st.columns(3)
        with c_field1: render_single_kpi("VMA")
        with c_field2: render_single_kpi("Temps 10m (Terrain)")
        with c_field3: render_single_kpi("5-0-5")
        
        st.markdown("<br>", unsafe_allow_html=True) 
       
        # =============================================================================
        # 3. BOUCLE DE SÉCURITÉ (POUR AFFICHER CE QUI RESTE - LAYOUT INTELLIGENT)
        # =============================================================================
        
        ALREADY_HANDLED = [
            "Adducteurs (G)", "Adducteurs (D)", "Somme ADD", "Ratio Squeeze",
            "Abducteurs (G)", "Abducteurs (D)", "Somme ABD",
            "Nordic Ischio (G)", "Nordic Ischio (D)", "Sit And Reach",
            "Knee To Wall (G)", "Knee To Wall (D)",
            "Score Sommeil", "Score Nutrition",
            "CMJ (cm)", "Wattbike (6s)", "Squat Keiser", "Tirage Dos Keiser",
            "Landmine Throw", "Développé couché (W)", "Développé couché (W/kg)",
            "Amax", "Dmax", "Vmax", "Nb Accélérations", "Nb Décélérations", "Distance HSR",
            "VMA", "Temps 10m (Terrain)", "5-0-5", "Distance Totale", "Distance Sprint (92% Vmax)",
            "Landing %",
            "Q Conc 60° (G)", "Q Conc 60° (D)", "Q Conc 240° (G)", "Q Conc 240° (D)",
            "IJ Conc 60° (G)", "IJ Conc 60° (D)", "IJ Conc 240° (G)", "IJ Conc 240° (D)",
            "IJ Exc 30° (G)", "IJ Exc 30° (D)", "Q Exc 30° (G)", "Q Exc 30° (D)"
        ]

        for cat, variables in OFFICIAL_STRUCTURE.items():
            if "BIODEX" in cat.upper() or "ISO" in cat.upper(): continue
            
            vars_to_show = [v for v in variables if v not in ALREADY_HANDLED]
            if not vars_to_show: continue 
            
            items_to_render = []
            i = 0
            while i < len(vars_to_show):
                label = vars_to_show[i]
                if "(G)" in label and i + 1 < len(vars_to_show):
                    next_label = vars_to_show[i+1]
                    if next_label == label.replace("(G)", "(D)"):
                        items_to_render.append({"type": "pair", "labels": (label, next_label)})
                        i += 2
                        continue
                items_to_render.append({"type": "single", "label": label})
                i += 1
            
            if not items_to_render: continue

            st.markdown(f"<div class='section-header' style='font-size:18px; margin-top:30px;'>AUTRES INDICATEURS ({cat})</div>", unsafe_allow_html=True)
            
            # --- LOGIQUE INTELLIGENTE 1, 2 OU 3 COLONNES ---
            nb_items = len(items_to_render)
            
            if nb_items == 1:
                cols = st.columns(1) # Pleine largeur
            elif nb_items == 2:
                cols = st.columns(2) # 50/50
            else:
                cols = st.columns(3) # Tiers

            for idx, item in enumerate(items_to_render):
                with cols[idx % len(cols)]:
                    if item["type"] == "pair":
                        render_pair_kpi(item["labels"][0], item["labels"][1])
                    else:
                        render_single_kpi(item["label"])

        st.markdown("---")
        
        key_dom, key_weak, key_strat, key_ante = f"str_dom_{p_sel}", f"str_weak_{p_sel}", f"str_strat_{p_sel}", f"str_ante_{p_sel}"

        if key_dom not in st.session_state: st.session_state[key_dom] = ""
        if key_weak not in st.session_state: st.session_state[key_weak] = ""
        if key_strat not in st.session_state: st.session_state[key_strat] = ""
        if key_ante not in st.session_state: st.session_state[key_ante] = ""

        c_txt1, c_txt2 = st.columns(2)
        with c_txt1:
            st.markdown(f"<div style='color:{SDR_RED}; font-weight:bold; margin-bottom:5px;'>POINT(S) FORT(S)</div>", unsafe_allow_html=True)
            st.session_state[key_dom] = st.text_area("Fort", st.session_state[key_dom], height=150, label_visibility="collapsed", key=f"ad_{p_sel}")
        with c_txt2:
            st.markdown(f"<div style='color:#888; font-weight:bold; margin-bottom:5px;'>AXES D'AMÉLIORATION</div>", unsafe_allow_html=True)
            st.session_state[key_weak] = st.text_area("Faible", st.session_state[key_weak], height=150, label_visibility="collapsed", key=f"aw_{p_sel}")
        
        c_txt3, c_txt4 = st.columns(2)
        with c_txt3:
            st.markdown(f"<div style='color:#27AE60; font-weight:bold; margin-bottom:5px;'>STRATÉGIE</div>", unsafe_allow_html=True)
            st.session_state[key_strat] = st.text_area("Strat", st.session_state[key_strat], height=150, label_visibility="collapsed", key=f"as_{p_sel}")
        with c_txt4:
            st.markdown(f"<div style='color:#F39C12; font-weight:bold; margin-bottom:5px;'>ANTÉCÉDENTS BLESSURE</div>", unsafe_allow_html=True)
            st.session_state[key_ante] = st.text_area("Antéced", st.session_state[key_ante], height=150, label_visibility="collapsed", key=f"aa_{p_sel}")


        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("ℹ️ Détail des Normes & Sources", expanded=False):
            data_norms = []
            seen_metrics = set()
            for cat, variables in OFFICIAL_STRUCTURE.items():
                for var in variables:
                    clean_name = get_clean_label(var)
                    if clean_name in seen_metrics: continue
                    seen_metrics.add(clean_name)
                    norm_val = get_norm_text(var).replace("Obj: ", "")
                    source = get_source(var)
                    data_norms.append({"Catégorie": cat, "Indicateur": clean_name, "Norme": norm_val, "Source": source})
            st.dataframe(pd.DataFrame(data_norms), use_container_width=True, hide_index=True)

        with tab_team:
            show_team_page(df, OFFICIAL_STRUCTURE)

        
        # Données anthropométriques pour l'en-tête
        anthro_vals = {
            "Taille": row.get('Taille (cm)', '-'),
            "Poids": row.get('Poids (Kg)', '-'),
            "Masse Grasse": row.get('Masse grasse Plis (mm)', '-')
        }
        
        # Données anthropométriques
        anthro_vals = {
            "Taille": row.get('Taille (cm)', '-'),
            "Poids": row.get('Poids (Kg)', '-'),
            "Masse Grasse": row.get('Masse grasse Plis (mm)', '-')
        }

        
        # 1. Récupération sécurisée des notes
        safe_dom = st.session_state.get(key_dom, "")
        safe_weak = st.session_state.get(key_weak, "")
        safe_strat = st.session_state.get(key_strat, "")

        # 2. Génération immédiate du rapport (sans condition if st.button)
        html_rep = generate_report(
            p_sel, row, df, 
            val_poste, val_lat, val_num, 
            safe_dom, safe_weak, safe_strat, 
            anthro_vals
        )
        
        # 3. Encodage en Base64
        b64 = base64.b64encode(html_rep.encode()).decode()
        
        # 4. Affichage du bouton HTML personnalisé (Votre style)
        download_btn = f'''
        <a href="data:text/html;base64,{b64}" download="Profilage_{p_sel}.html" style="text-decoration:none;">
            <button style="background-color:{SDR_RED}; color:white; padding:12px 20px; border:none; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">
                TÉLÉCHARGER LE RAPPORT PDF
            </button>
        </a>
        '''
        
        st.markdown(download_btn, unsafe_allow_html=True)
