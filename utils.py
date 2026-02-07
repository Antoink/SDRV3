import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
import os
from io import BytesIO
from math import pi

# =============================================================================
# 1. CONSTANTES & CONFIGURATION
# =============================================================================

SDR_RED = "#D71920"
BLACK = "#000000"
WHITE = "#FFFFFF"
SDR_GREY = "#F0F2F6"

def local_css():
    """Injecte le CSS global pour la sidebar et les titres."""
    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {SDR_RED}; }}
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1 {{ color: white !important; }}
    h1, h2, h3 {{ color: {SDR_RED} !important; }}
    /* Ajustement mobile */
    @media (max-width: 768px) {{
        .hero-container {{ flex-direction: column; text-align: center; }}
        .hero-right {{ justify-content: center; margin-top: 10px; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. GESTION DES IMAGES
# =============================================================================

def img_to_b64(image_path):
    """Convertit une image locale en chaîne base64 pour l'intégrer au HTML."""
    if not image_path or not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        return ""

def get_best_photo_path(player_name):
    """Cherche la photo du joueur dans le dossier Photos."""
    folder = "Photos"
    if not os.path.exists(folder): return None
    
    # Création d'un map {nom_fichier_lower: nom_fichier_reel}
    files_map = {f.lower(): f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))}
    
    clean_name = player_name.strip()
    parts = clean_name.split()
    
    # Stratégies de recherche (Nom complet, Nom Prénom, Prénom Nom)
    candidates = [clean_name]
    if len(parts) > 1:
        candidates.append(f"{parts[-1]} {' '.join(parts[:-1])}") # NOM Prénom
        candidates.append(f"{' '.join(parts[1:])} {parts[0]}")   # Prénom NOM
    
    extensions = [".jpg", ".png", ".jpeg"]
    
    for cand in candidates:
        for ext in extensions:
            target_key = f"{cand}{ext}".lower()
            if target_key in files_map:
                return os.path.join(folder, files_map[target_key])
    return None

# =============================================================================
# 3. LOGIQUE MÉTIER & CALCULS
# =============================================================================

def is_inverted(label):
    """Définit si une métrique est inversée (plus petit = mieux)."""
    keywords = ['temps', 'chrono', '10m', '505', 'agilité', 'masse grasse', 'landing', "Landing %"]
    return any(x in str(label).lower() for x in keywords)

@st.cache_data
def load_data():
    """Charge les données principales (utilisé par main.py)."""
    # Liste des fichiers potentiels par ordre de priorité
    files = ["Profilage pratiquexlsx.xlsx", "Profilage.xlsx"]
    
    for f in files:
        if os.path.exists(f):
            try:
                df = pd.read_excel(f, header=0)
                # Nettoyage des colonnes (supprime les espaces avant/après)
                df.columns = [str(c).strip() for c in df.columns]
                
                # Identification de la colonne Joueur
                cols_lower = {str(c).lower().strip(): c for c in df.columns}
                target = next((cols_lower[k] for k in ['joueur', 'nom', 'name'] if k in cols_lower), None)
                
                if target:
                    df = df.dropna(subset=[target]).rename(columns={target: 'Joueur'})
                    df['Joueur'] = df['Joueur'].astype(str).str.title().str.strip()
                    return df
            except Exception:
                continue
                
    return pd.DataFrame()

# =============================================================================
# 4. GÉNÉRATION DE GRAPHIQUES (RADAR)
# =============================================================================

def create_radar_chart(categories, values, text_color="black"):
    """
    Génère un Radar Chart et retourne l'image en Base64.
    text_color: 'white' pour l'app Streamlit (fond sombre), 'black' pour le PDF (fond blanc).
    """
    if not categories or not values:
        return ""

    N = len(categories)
    
    # Calcul des angles
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # Fermer la boucle
    
    # Fermer la boucle des valeurs
    values_closed = values + values[:1]
    
    # Création de la figure
    # Facecolor transparent pour s'adapter au fond
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    fig.patch.set_alpha(0)
    ax.set_facecolor((0,0,0,0)) # Fond du plot transparent
    
    # Axe Y (0 à 100)
    ax.set_ylim(0, 100)
    ax.set_yticks([33, 66, 100])
    ax.set_yticklabels([]) # Pas de labels numériques sur les cercles
    
    # Couleurs des cercles de grille
    ax.yaxis.grid(True, color=text_color, linestyle='--', alpha=0.3)
    ax.xaxis.grid(True, color=text_color, linestyle='-', alpha=0.3)
    
    # Tracer la ligne de données
    line_color = SDR_RED
    ax.plot(angles, values_closed, color=line_color, linewidth=2, linestyle='solid')
    ax.fill(angles, values_closed, color=line_color, alpha=0.25)
    
    # Labels des catégories (X axis)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=9, color=text_color, weight='bold')
    
    # Ajustement position labels pour éviter chevauchement
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        if angle in (0, pi):
            label.set_horizontalalignment('center')
        elif 0 < angle < pi:
            label.set_horizontalalignment('left')
        else:
            label.set_horizontalalignment('right')

    # Suppression du cadre extérieur (spine)
    ax.spines['polar'].set_visible(False)

    # Sauvegarde en mémoire
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    plt.close(fig)
    
    return base64.b64encode(buf.getvalue()).decode()