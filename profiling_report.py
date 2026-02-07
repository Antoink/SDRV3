import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
import os
import re
import unicodedata
from io import BytesIO
from math import pi
from scipy import stats

# --- IMPORT DES CONFIGURATIONS EXISTANTES ---
from config_rapport import (
    OFFICIAL_STRUCTURE, 
    REPORT_NORMES, 
    UNITS, 
    COL_MAPPING, 
    SDR_RED, 
    RELATIVE_NORM_KEYS
)

# =============================================================================
# 1. FONCTIONS UTILITAIRES (INTERNES AU RAPPORT)
# =============================================================================

def clean_numeric_value(val):
    if pd.isna(val) or val == "" or val == "-": return None
    try:
        if isinstance(val, (int, float)): return float(val)
        val_str = str(val).replace(',', '.')
        match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
        if match: return float(match.group())
        return None
    except: return None

def remove_accents(input_str):
    if not isinstance(input_str, str): return str(input_str)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def find_column_in_df(df, label):
    # Mapping inversé simplifié pour la recherche
    col_map_lower = {k.lower(): v for k, v in COL_MAPPING.items()}
    label_lower = label.lower()
    
    # 1. Essai direct via mapping
    if label_lower in col_map_lower:
        mapped = col_map_lower[label_lower]
        if mapped in df.columns: return mapped
        
    # 2. Recherche par mot clé approximatif
    df_cols_clean = [remove_accents(str(c)).lower().strip() for c in df.columns]
    label_clean = remove_accents(label).lower().strip().replace("(g)", "").replace("(d)", "")
    
    for idx, col in enumerate(df_cols_clean):
        if label_clean in col:
            return df.columns[idx]
    return None

def is_inverted(label):
    keywords = ['temps', 'chrono', '10m', '505', 'agilité', 'masse grasse', 'landing %']
    return any(x in str(label).lower() for x in keywords)

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

def get_report_color(label, val):
    if val is None: return "#888"
    col_clean = str(label).replace("(G)", "").replace("(D)", "").strip()
    
    # Recherche de la norme
    found_key = next((k for k in REPORT_NORMES.keys() if k in col_clean), None)
    if not found_key: return "#666"
    
    low, high = REPORT_NORMES[found_key]
    c_bad, c_avg, c_good = "#D71920", "#F39C12", "#27AE60"
    
    if is_inverted(label):
        return c_good if val < low else (c_avg if val <= high else c_bad)
    else:
        return c_bad if val < low else (c_avg if val < high else c_good)

# =============================================================================
# 2. GESTION DES IMAGES & GRAPHIQUES
# =============================================================================

def img_to_b64(img_path):
    try:
        with open(img_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

def get_best_photo_path(player_name):
    folder = "Photos"
    if not os.path.exists(folder): return None
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    clean_p = remove_accents(player_name).lower().strip()
    
    for f in files:
        if clean_p in remove_accents(f).lower():
            return os.path.join(folder, f)
    return None

def create_radar_chart(categories, values, text_color="black"):
    if not categories: return ""
    N = len(categories)
    values_closed = values + values[:1]
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    # Fond
    ax.fill_between(angles, 0, 33, color='#D71920', alpha=0.15)
    ax.fill_between(angles, 66, 100, color='#27AE60', alpha=0.15)
    
    # Axes
    plt.xticks(angles[:-1], categories, color=text_color, size=9, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([33, 66, 100], ["33", "66", ""], color="#888", size=8)
    plt.ylim(0, 100)
    
    # Tracé
    ax.plot(angles, values_closed, linewidth=2, linestyle='solid', color=SDR_RED, marker='o', markersize=5)
    ax.fill(angles, values_closed, color=SDR_RED, alpha=0.4)
    
    # Nettoyage
    ax.spines['polar'].set_color('#ccc')
    ax.yaxis.grid(True, color='#ccc', linestyle='dashed')
    ax.xaxis.grid(True, color='#ccc')
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_b64

# =============================================================================
# 3. FONCTION PRINCIPALE : GENERATE REPORT
# =============================================================================

def generate_report(player_name, df_row, df, poste, laterality, number, dominant_point, weak_point, strat_point, anthro_data):
    
    # --- A. PRÉPARATION DES DONNÉES ---
    
    # 1. Calcul du Top/Flop 3
    all_scores = []
    for cat, vars in OFFICIAL_STRUCTURE.items():
        for label in vars:
            col_name = COL_MAPPING.get(label, label)
            if col_name not in df.columns: col_name = find_column_in_df(df, label)
            
            val = clean_numeric_value(df_row.get(col_name))
            if col_name and val is not None:
                mean_val, p = calculate_percentile(df, col_name, val)
                all_scores.append({"label": label, "percentile": p, "val": val, "mean": mean_val})
    
    all_scores.sort(key=lambda x: x["percentile"], reverse=True)
    top_3, flop_3 = all_scores[:3], all_scores[-3:]

    # 2. Génération Radar Athlétique
    radar_config = [
        {"label": "Vitesse", "cols": ["Vmax"], "unit": ["km/h"]},
        {"label": "Endurance", "cols": ["VMA"], "unit": ["km/h"]},
        {"label": "Puissance", "cols": ["Wattbike 6s (W)", "Développé couché (W/kg)"], "unit": ["W","W/kg"]},
        {"label": "Force", "cols": ["Nordic Mean", "Adducteurs Mean"], "unit": ["N", "N"]},
        {"label": "Mobilité", "cols": ["Sit And Reach", "Calculated_KTW_Mean"], "unit": ["cm", "cm"]},
        {"label": "Perf. Terrain", "cols": ["Amax", "Dmax"], "unit": ["m/s²", "m/s²"]},
        {"label": "Explosivité", "cols": ["CMJ (cm)"], "unit": ["cm"]}
    ]
    
    # Pré-calcul des moyennes (G+D) pour le radar
    ng, nd = COL_MAPPING.get("Nordic Ischio (G)"), COL_MAPPING.get("Nordic Ischio (D)")
    if ng in df.columns and nd in df.columns: df['Nordic Mean'] = df[[ng, nd]].mean(axis=1)
    
    ag, ad = COL_MAPPING.get("Adducteurs (G)"), COL_MAPPING.get("Adducteurs (D)")
    if ag in df.columns and ad in df.columns: df['Adducteurs Mean'] = df[[ag, ad]].mean(axis=1)
    
    kg, kd = COL_MAPPING.get("Knee To Wall (G)"), COL_MAPPING.get("Knee To Wall (D)")
    if kg in df.columns and kd in df.columns: df['Calculated_KTW_Mean'] = df[[kg, kd]].mean(axis=1)

    radar_labels, radar_values, details_html = [], [], ""
    
    for item in radar_config:
        radar_labels.append(item['label'])
        sum_p, count, sub_details = 0, 0, []
        
        for idx, col_key in enumerate(item['cols']):
            # Gestion des moyennes calculées
            if "Mean" in col_key:
                if col_key == "Nordic Mean": 
                    val = (clean_numeric_value(df_row.get(ng)) + clean_numeric_value(df_row.get(nd))) / 2
                elif col_key == "Adducteurs Mean": 
                    val = (clean_numeric_value(df_row.get(ag)) + clean_numeric_value(df_row.get(ad))) / 2
                elif col_key == "Calculated_KTW_Mean": 
                    val = (clean_numeric_value(df_row.get(kg)) + clean_numeric_value(df_row.get(kd))) / 2
                col_name = col_key
            else:
                col_name = COL_MAPPING.get(col_key, find_column_in_df(df, col_key))
                val = clean_numeric_value(df_row.get(col_name))
            
            if val is not None:
                try:
                    _, p = calculate_percentile(df, col_name, val)
                    sum_p += p
                    count += 1
                except: pass
                
                u = item['unit'][idx] if len(item['unit']) > idx else ""
                disp_val = f"{val:.2f}{u}" if val <= 100 else f"{int(val)}{u}"
                
                # Nettoyage nom pour affichage
                clean_name = col_key.replace("Calculated_", "").replace("_Mean", "").replace(" Mean", "")
                if clean_name == "Nordic": clean_name = "F. Post."
                if clean_name == "Adducteurs": clean_name = "F. Add."
                if clean_name == "KTW": clean_name = "Mob. Cheville"
                
                sub_details.append(f"{clean_name}: <b>{disp_val}</b>")

        final_score = sum_p / count if count > 0 else 0
        radar_values.append(final_score)
        
        c_style = "color:#27ae60" if final_score > 66 else ("color:#F39C12" if final_score > 33 else "color:#D71920")
        details_html += f"""<div style="border-bottom:1px solid #eee; padding:3px 0;"><div style="display:flex; justify-content:space-between;"><span style="font-weight:bold; font-size:9pt; color:#333;">{item['label']}</span><span style="{c_style}; font-weight:bold; font-size:8pt;">P{int(final_score)}</span></div><div style="font-size:7pt; color:#888;">{" • ".join(sub_details)}</div></div>"""

    radar_b64 = create_radar_chart(radar_labels, radar_values, text_color="black")

    # 3. Calcul Asymétries (Force / Mobilité)
    def calc_asym_avg(pairs):
        t, c = 0, 0
        for g, d in pairs:
            cg, cd = COL_MAPPING.get(g, g), COL_MAPPING.get(d, d)
            if cg not in df.columns: cg = find_column_in_df(df, g)
            if cd not in df.columns: cd = find_column_in_df(df, d)
            
            vg = clean_numeric_value(df_row.get(cg))
            vd = clean_numeric_value(df_row.get(cd))
            
            if vg is not None and vd is not None:
                # KTW: % par rapport au max équipe (pour éviter les écarts énormes sur petites valeurs)
                if "Knee" in g or "KTW" in g:
                    max_l = pd.to_numeric(df[cg], errors='coerce').max()
                    max_r = pd.to_numeric(df[cd], errors='coerce').max()
                    ref = max(max_l, max_r) if (pd.notna(max_l) and pd.notna(max_r)) else 15
                    if ref > 0:
                        t += (vd - vg) / ref * 100
                        c += 1
                else:
                    ref = max(vg, vd)
                    if ref > 0:
                        t += (vd - vg) / ref * 100
                        c += 1
        return t / c if c > 0 else 0

    force_pairs = [("Adducteurs (G)", "Adducteurs (D)"), ("Abducteurs (G)", "Abducteurs (D)"), ("Nordic Ischio (G)", "Nordic Ischio (D)"), ("Landing (G)", "Landing (D)")]
    mob_pairs = [("Knee To Wall (G)", "Knee To Wall (D)")]
    
    avg_force = calc_asym_avg(force_pairs)
    avg_mob = calc_asym_avg(mob_pairs)

    def get_bar_html(val, title):
        marker = 50 + max(min((val / 20) * 50, 50), -50) # Borne à +/- 20% d'asymétrie pour l'affichage
        return f"""
        <div style="margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; font-size:7pt; margin-bottom:2px; font-weight:bold; color:#555;">
                <span>G</span> <span style="color:#333;">{title}: {val:+.1f}%</span> <span>D</span>
            </div>
            <div style="position:relative; width:100%; height:6px; background:linear-gradient(90deg, #3498db 0%, #bdc3c7 45%, #bdc3c7 55%, #3498db 100%); border-radius:3px;">
                <div style="position:absolute; left:{marker}%; top:-1px; width:2px; height:8px; background:#333; border:1px solid white;"></div>
            </div>
        </div>
        """

    # --- B. CONSTRUCTION DU HTML ---
    
    # Images
    photo_b64 = img_to_b64(get_best_photo_path(player_name))
    photo_html = f'<img src="data:image/png;base64,{photo_b64}" style="width:200px; height:200px; object-fit:contain; border-radius:8px;">' if photo_b64 else ""
    
    # Logo (Assure-toi que logo_sdr.png est dans le dossier ou change le nom ici)
    logo_b64 = img_to_b64("logo_sdr.png")
    if not logo_b64: logo_b64 = img_to_b64("logo.png") # Fallback
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="100">'

    # CSS Global
    css = f"""
    <style>
        @page {{ size: A4; margin: 10mm; }}
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; margin: 0; padding: 0; background-color: #eee; font-size: 9pt; }}
        .page {{ 
            background: white; width: 210mm; height: 297mm; margin: 10px auto; 
            padding: 10mm 15mm; box-shadow: 0 0 10px rgba(0,0,0,0.1); box-sizing: border-box;
            position: relative; page-break-after: always;
        }}
        .page:last-child {{ page-break-after: avoid; }}
        
        .header-container {{ display: flex; padding: 5px 0; margin-bottom: 15px; align-items:center; }}
        .section-title {{ font-size: 10pt; font-weight: 900; color: white; background-color: {SDR_RED}; padding: 4px 12px; margin-top: 10px; margin-bottom: 5px; border-radius: 4px; display: block; text-align: center; }}
        
        table.summary-table {{ width: 100%; border-collapse: collapse; font-size: 8pt; margin-bottom: 15px; }}
        table.summary-table th {{ background-color: #f2f2f2; text-align: left; padding: 6px; }}
        table.summary-table td {{ padding: 6px; border-bottom: 1px solid #eee; }}
        
        table.kpi-table {{ width: 100%; border-collapse: collapse; font-size: 8pt; margin-bottom: 5px; }}
        table.kpi-table th {{ text-align: left; color: #999; font-size: 7pt; text-transform: uppercase; border-bottom: 1px solid #ddd; }}
        table.kpi-table td {{ padding: 3px; border-bottom: 1px solid #f9f9f9; vertical-align: middle; }}
        
        .val-cell {{ font-weight: 800; font-size: 8pt; color: #333; }}
        .bar-container {{ width: 100%; height: 6px; background-color: #eee; border-radius: 3px; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 3px; }}
        
        .comment-block {{ margin-bottom: 15px; padding: 12px; border-radius: 8px; border-left: 6px solid #ccc; background: #f9f9f9; }}
        .comment-block h3 {{ margin: 0 0 6px 0; font-size: 10pt; }}
        .dom {{ border-color: #27ae60; background: #f0fbf4; }} .dom h3 {{ color: #27ae60; }}
        .weak {{ border-color: {SDR_RED}; background: #fff0f0; }} .weak h3 {{ color: {SDR_RED}; }}
        .strat {{ border-color: #f39c12; background: #fefcf5; }} .strat h3 {{ color: #f39c12; }}
    </style>
    """

    # --- HTML PAGE 1 ---
    
    summary_rows = ""
    for x in top_3:
        summary_rows += f"""<tr style="color:#27ae60; font-weight:bold;"><td>{x['label']}</td><td>{x['val']:.2f}</td><td>{x['mean']:.2f}</td><td>Mieux que {int(x['percentile'])}%</td></tr>"""
    summary_rows += f"""<tr><td colspan="4" style="border-bottom:1px solid #ddd; height:2px;"></td></tr>"""
    for x in flop_3:
        summary_rows += f"""<tr style="color:{SDR_RED}; font-weight:bold;"><td>{x['label']}</td><td>{x['val']:.2f}</td><td>{x['mean']:.2f}</td><td>Mieux que {int(x['percentile'])}%</td></tr>"""

    page_1 = f"""
    <div class="page">
        <div class="header-container">
            <div style="width: 200px; margin-right: 25px;">{photo_html}</div>
            <div style="flex-grow: 1; display:flex; flex-direction:column; justify-content:center;">
                <h1 style="margin:0; color:{SDR_RED}; font-size:28pt; text-transform:uppercase;">{player_name}</h1>
                <div style="font-size:25pt; font-weight:bold; color:{SDR_RED}; margin:5px 0;">#{number}</div>
                <div style="font-size:17pt; font-weight:bold; text-transform:uppercase; color:#333;">{poste} | {laterality}</div>
                <div style="font-size:15pt; color:#666; margin-top:5px;">{int(df_row.get('Age', 0))} ans | {anthro_data.get('Taille','-')} | {anthro_data.get('Poids','-')}</div>
            </div>
            <div style="text-align:right;">
                {logo_html}
                <div style="font-weight:bold; color:#333; font-size:9pt; margin-top:8px; text-transform:uppercase;">
                    Département<br><span style="color:{SDR_RED}">Performance</span>
                </div>
            </div>
        </div>

        <div style="margin-bottom:15px;">
            <div class="section-title">PROFIL ATHLÉTIQUE</div>
            <div style="display:flex; align-items:center; gap:20px;">
                <div style="width:55%;"><img src="data:image/png;base64,{radar_b64}" style="width:100%;"></div>
                <div style="width:45%; background:#fff; padding:8px; border-radius:8px; border:1px solid #eee;">
                   {details_html}
                </div>
            </div>
        </div>

        <div style="margin-bottom:20px;">
            <div class="section-title">PERFORMANCES CLÉS</div>
            <table class="summary-table">
                <thead><tr><th>Indicateur</th><th>Valeur</th><th>Moyenne</th><th>Positionnement</th></tr></thead>
                <tbody>{summary_rows}</tbody>
            </table>
        </div>

        <div style="margin-top:auto;">
            <div class="section-title">SYMÉTRIE GLOBALE</div>
            <div style="background:#fff; padding:10px; border-radius:5px; border:1px solid #ddd;">
                {get_bar_html(avg_force, "FORCE")}
                {get_bar_html(avg_mob, "MOBILITÉ")}
            </div>
        </div>
        <div style="position:absolute; bottom:10mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">PAGE 1/3</div>
    </div>
    """

    # --- HTML PAGE 2 (DETAILS) ---
    
    details_content = ""
    for cat_name, variables in OFFICIAL_STRUCTURE.items():
        # Vérif si données dispos
        if not any((COL_MAPPING.get(v, v) in df.columns) or (find_column_in_df(df, v)) for v in variables):
            continue

        rows = ""
        for label in variables:
            col_name = COL_MAPPING.get(label, label)
            if col_name not in df.columns: col_name = find_column_in_df(df, label)
            
            val = clean_numeric_value(df_row.get(col_name))
            if pd.isna(val) or val is None: continue
            
            _, percentile = calculate_percentile(df, col_name, val)
            text_color = get_report_color(label, val)
            bar_color = "#D71920" if percentile < 33 else "#F39C12" if percentile < 66 else "#27AE60"
            unit = UNITS.get(label.replace("(G)", "").replace("(D)", "").strip(), "")
            
            rows += f"""
                <tr>
                    <td>{label}</td>
                    <td class="val-cell" style="color:{text_color}">{val}<span style="font-size:7pt;color:#999;">{unit}</span></td>
                    <td>
                        <div style="display:flex; align-items:center; gap:5px;">
                            <div class="bar-container" style="flex-grow:1;"><div class="bar-fill" style="width: {int(percentile)}%; background-color: {bar_color};"></div></div>
                            <div style="font-size:7pt; color:#666; font-weight:bold;">P{int(percentile)}</div>
                        </div>
                    </td>
                </tr>
            """
        
        if rows:
            details_content += f"""
            <div style="break-inside: avoid; margin-bottom:12px;">
                <div style="font-weight:bold; color:{SDR_RED}; border-bottom:1px solid #ddd; margin-bottom:4px; font-size:9pt;">{cat_name}</div>
                <table class="kpi-table">
                    <thead><tr><th width="40%">Test</th><th width="20%">Val.</th><th width="40%">Pos.</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
            """

    # Asymétries détaillées
    asym_html = ""
    detail_pairs = [
        ("Knee To Wall (G)", "Knee To Wall (D)", "Mobilité Cheville"),
        ("Adducteurs (G)", "Adducteurs (D)", "Force Adducteurs"),
        ("Abducteurs (G)", "Abducteurs (D)", "Force Abducteurs"),
        ("Nordic Ischio (G)", "Nordic Ischio (D)", "Force Exc. Ischios"),
        ("Landing (G)", "Landing (D)", "Réception Saut")
    ]
    
    for l_g, l_d, name in detail_pairs:
        c_g = COL_MAPPING.get(l_g, l_g)
        if c_g not in df.columns: c_g = find_column_in_df(df, l_g)
        c_d = COL_MAPPING.get(l_d, l_d)
        if c_d not in df.columns: c_d = find_column_in_df(df, l_d)
        
        v_g = clean_numeric_value(df_row.get(c_g))
        v_d = clean_numeric_value(df_row.get(c_d))
        
        if v_g is not None and v_d is not None:
            # Calcul différence relative au max
            ref = max(v_g, v_d)
            if "Knee" in name: # Ref équipe pour KTW
                max_l = pd.to_numeric(df[c_g], errors='coerce').max()
                max_r = pd.to_numeric(df[c_d], errors='coerce').max()
                ref = max(max_l, max_r) if pd.notna(max_l) else 15

            pct = abs(v_g - v_d) / ref * 100 if ref > 0 else 0
            color = "#27ae60" if pct < 10 else ("#f39c12" if pct < 15 else "#D71920")
            weak = "D" if v_g > v_d else "G"
            
            asym_html += f"""
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:8pt; border-bottom:1px solid #eee; padding:3px 0;">
                <span style="color:#333;">{name}</span>
                <div style="text-align:right;">
                    <span style="font-size:7pt; color:#666; margin-right:4px;">Faiblesse {weak}</span>
                    <span style="font-weight:bold; color:{color};">{pct:.1f}%</span>
                </div>
            </div>
            """

    page_2 = f"""
    <div class="page">
        <div style="border-bottom:2px solid {SDR_RED}; margin-bottom:15px; padding-bottom:5px;">
            <span style="font-weight:900; font-size:14pt; color:{SDR_RED};">{player_name}</span>
            <span style="font-size:9pt; color:#666; margin-left:10px;">DÉTAIL DES TESTS</span>
        </div>
        <div style="column-count: 2; column-gap: 20px;">
            {details_content}
        </div>
        
        <div style="break-inside: avoid; margin-top:20px;">
            <div style="font-weight:bold; color:{SDR_RED}; border-bottom:1px solid #ddd; margin-bottom:10px; font-size:10pt;">DÉTAIL ASYMÉTRIES</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; background:#f9f9f9; padding:10px; border-radius:5px;">
                {asym_html}
            </div>
        </div>
        <div style="position:absolute; bottom:10mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">PAGE 2/3</div>
    </div>
    """

    # --- HTML PAGE 3 (CONCLUSION) ---
    
    page_3 = f"""
    <div class="page">
        <div style="border-bottom:2px solid {SDR_RED}; margin-bottom:30px; padding-bottom:5px;">
            <span style="font-weight:900; font-size:14pt; color:{SDR_RED};">{player_name}</span>
            <span style="font-size:9pt; color:#666; margin-left:10px;">OBSERVATIONS</span>
        </div>

        <div style="margin-top:20px;">
            <div class="comment-block dom"><h3>POINT(S) FORT(S)</h3><p>{dominant_point if dominant_point else " "}</p></div>
            <div class="comment-block weak"><h3>AXE(S) D'AMELIORATION</h3><p>{weak_point if weak_point else " "}</p></div>
            <div class="comment-block strat"><h3>STRATÉGIE D'INTERVENTION</h3><p>{strat_point if strat_point else " "}</p></div>
        </div>

        <div style="margin-top: 400px; display: flex; justify-content: space-between; align-items: flex-end;">
            <div style="text-align:left;">
                {logo_html}
                <div style="font-weight:bold; color:#333; font-size:9pt; margin-top:8px; text-transform:uppercase;">
                    Département<br><span style="color:{SDR_RED}">Performance</span>
                </div>
            </div>
            <div style="text-align: right; margin-right: 10px;">
                <div style="font-weight:bold; font-size:9pt; color:#333; margin-bottom:130px;">Signature</div>
            </div>
        </div>
        <div style="position:absolute; bottom:10mm; width:100%; text-align:center; font-size:8pt; color:#ccc;">PAGE 3/3</div>
    </div>
    """

    full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css}</head><body>{page_1}{page_2}{page_3}</body></html>"
    return full_html