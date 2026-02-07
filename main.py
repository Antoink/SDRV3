import streamlit as st
from utils import load_data, local_css, SDR_RED

# Imports des modules restants
import profiling
import cmj

# 1. CONFIGURATION PAGE
st.set_page_config(
    page_title="SDR Performance",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SÉCURITÉ : MOT DE PASSE (Optionnel, à garder si besoin) ---
def check_password():
    if 'password_correct' not in st.session_state:
        st.session_state['password_correct'] = False

    if st.session_state['password_correct']:
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            try:
                st.image("logo_sdr.png", width=150)
            except:
                st.title("SDR")
        
        st.markdown(f"<h3 style='text-align:center;'>ACCÈS RESTREINT</h3>", unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe", type="password", label_visibility="collapsed")
        
        if pwd:
            if pwd == "SDR": # Mot de passe simple
                st.session_state['password_correct'] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    return False

if not check_password():
    st.stop()

# ==============================================
# DÉBUT DE L'APPLICATION
# ==============================================

# 2. ACTIVATION DU DESIGN
local_css()

# 3. CHARGEMENT DES DONNÉES
# On charge une seule fois au début
full_data = load_data()

# 4. BARRE LATÉRALE (NAVIGATION SIMPLIFIÉE)
st.sidebar.markdown("## NAVIGATION")
page = st.sidebar.radio("Aller vers :", ["Profilage", "Recherche CMJ (Pro)"], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.info(f"Joueurs chargés : {len(full_data) if not full_data.empty else 0}")

if page == "Profilage":
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Options d'affichage**")
        
        # Initialisation de la variable si elle n'existe pas
        if "use_relative_mode" not in st.session_state:
            st.session_state.use_relative_mode = False
            
        # Le Toggle qui contrôle tout
        st.session_state.use_relative_mode = st.sidebar.toggle(
            "Données relatives (valeur/kg)", 
            value=st.session_state.use_relative_mode,
            help="Activez pour voir les performances pondérées par le poids de corps."
        )
# 5. AFFICHAGE DES PAGES
if page == "Profilage":
    # On passe full_data pour éviter de recharger dans profiling.py
    profiling.show_profiling_page(full_data)

elif page == "Recherche CMJ (Pro)":
    # On appelle la fonction principale de ton module cmj.py
    # Assure-toi que la fonction s'appelle bien show_cmj_page ou show_page dans cmj.py
    try:
        cmj.show_cmj_page(full_data)
    except AttributeError:
        # Fallback si le nom de la fonction est différent dans ton cmj.py actuel
        try:
            cmj.show_interface(full_data)
        except:
            st.error("Erreur : Impossible de trouver la fonction d'affichage dans cmj.py")


# streamlit run main.py
# ou 
# python -m streamlit run main.py
