import streamlit as st
import plotly.express as px
import pandas as pd
import utils

# --- 1. DÉFINITION DES INDICATEURS ---

KPI_GENERAL = {
    "Poids (kg)": "Poids_kg",
    "Hauteur Saut (Vit) (cm)": "Hauteur de saut (Vitesse) (cm)",
    "Puissance Max (W)": "Pic de Puissance Max (W)",
    "Force Max (N)": "Pic de Force Max (N)",
    "Vitesse Max (m/s)": "Pic de Vitesse Max (m/s)",
    "Impulsion Totale (N.s)": "Impulsion Totale (N•s)",
    "RFD Max (N/s)": "Pic de RFD Max (N/s)",
    "RSI": "RSI (TV/TC)"
}

KPI_DECHARGE = {
    "Profondeur (cm)": "Phase de Décharge - Déplacement Min (cm)",
    "Durée Décharge (ms)": "Phase de Décharge - Durée (ms)",
    "Force Min. (N)": "Phase de Décharge - Force Minimale(N)",
    "RFD Max Négative (N/s)": "Phase de Décharge - RFD Max Négative (N/s)",
    "Impulsion Décharge (N.s)": "Phase de Décharge - Impulsion Totale (N•s)"
}

KPI_EXCENTRIQUE = {
    "Durée Freinage (ms)": "Phase de Freinage - Durée (ms)",
    "Force Moy. Freinage (N)": "Phase de Freinage - Force de Freinage Moy (N)",
    "Force Max Freinage (N)": "Phase de Freinage - Force de Freinage Max (N)",
    "Puissance Max Freinage (W)": "Phase de Freinage - Puissance de Freinage Max (W)",
    "RFD Décélération (N/s)": "Phase de Freinage - RFD Décélération (N/s)",
    "RFD Excentrique (N/s)": "Phase de Freinage - RFD Excentrique (N/s)",
    "Impulsion Freinage (N.s)": "Phase de Freinage - Impulsion de freinage (N•s)"
}

KPI_CONCENTRIQUE = {
    "Hauteur de Saut (cm)": "Hauteur de Saut TV (cm)",
    "Puissance Max (W)": "Pic de Puissance Max (W)",
    "Force Propulsive Max (N)": "Force Propulsive Max (N)",
    "Puissance Propulsive Max (W)": "Puissance Propulsive Max (W)",
    "Impulsion Propulsive (N.s)": "Impulsion Propulsive (N•s)",
    "RFD Concentrique (N/s)": "Pic de RFD Max (N/s)"
}

KPI_ATTERRISSAGE = {
    "Force Max Atterr. (N)": "Force Max à l'Atterrissage (N)",
    "Force Moy. Atterr. (N)": "Force d'Atterrissage Moy (N)",
    "Ratio Force/Poids (N/kg)": "Ratio Pic de force d'atterrissage/poids du corps (N/kg)"
}

ALL_KPI = {**KPI_CONCENTRIQUE, **KPI_EXCENTRIQUE, **KPI_ATTERRISSAGE, **KPI_DECHARGE, **KPI_GENERAL}

# --- 2. DÉFINITION DES GLOSSAIRES PAR PHASE ---

GLOSSARY_DEFINITIONS = {
    "Général": {
        "Hauteur de saut (Vitesse)": "Résultat final de la performance, estimé via la vitesse d'envol.",
        "Puissance Max": "Explosivité réelle de l'athlète (Force x Vitesse).",
        "Force Max": "Force maximale appliquée au sol pour se propulser.",
        "Impulsion Totale": "Effort total produit (Force x Temps). 'Gold Standard' pour suivre l'effet de l'entraînement.",
        "RFD Max": "Vitesse de montée en force. Indicateur de l'explosivité nerveuse.",
        "RSI": "Indice de réactivité (Hauteur / Temps de contact). Efficacité du cycle étirement-détente."
    },
    "Phase Décharge": {
        "RFD Max Négative": "Vitesse de relâchement de la force pour initier la descente. Plus c'est bas (négatif), plus le démarrage est réactif.",
        "Impulsion Décharge": "Capacité à se relâcher efficacement avant le freinage. Conditionne la fluidité du saut.",
        "Force Min.": "Niveau de force le plus bas atteint lors du délestage (Unloading)."
    },
    "Phase Excentrique": {
        "Force Max Freinage": "Capacité maximale d'absorption de force. Lié à la performance de décélération sur terrain et prévention des blessures.",
        "RFD Décélération": "Vitesse d'application du freinage. Un taux élevé indique un freinage vif et 'sec' (vivacité).",
        "Impulsion Freinage": "Effort total pour stopper la descente. Indicateur de résilience musculaire face à la charge.",
        "RFD Excentrique": "Vitesse à laquelle la force de freinage est développée."
    },
    "Phase Concentrique": {
        "Force Propulsive Max": "Force maximale générée pour pousser le corps vers le haut (Triple extension).",
        "Puissance Propulsive Max": "Explosivité maximale développée lors de la montée.",
        "RFD Concentrique": "Vitesse de contraction musculaire lors de la poussée. Une montée raide = profil explosif.",
        "Impulsion Propulsive": "Quantité totale de mouvement générée pour le saut."
    },
    "Atterrissage": {
        "Force Max Atterr.": "Pic de force subi à l'impact. Renseigne sur le stress mécanique et le risque de blessure.",
        "Force Moy. Atterr.": "Force moyenne gérée durant la phase de stabilisation.",
        "Ratio Force/Poids": "Permet de relativiser l'impact subi par rapport au gabarit du joueur."
    }
}


# --- 3. FONCTIONS GRAPHIQUES ---

def chart_team_averages(df, selected_kpis_dict):
    if not selected_kpis_dict:
        return None

    cols = st.columns(len(selected_kpis_dict))
    
    for idx, (label, col) in enumerate(selected_kpis_dict.items()):
        if col in df.columns:
            raw_mean = df[col].mean()
            # Si donnée négative (ex: profondeur, RFD négatif), on affiche l'absolu pour la moyenne
            avg_val = abs(raw_mean)
            std_val = df[col].std()
            
            with cols[idx]:
                st.metric(
                    label=label,
                    value=f"{avg_val:.1f}",
                    delta=f"± {std_val:.1f} (SD)",
                    delta_color="off"
                )

def chart_player_profile_normalized(df, player_row, selected_kpis_dict):
    if not selected_kpis_dict:
        return None

    data = []
    for label, col in selected_kpis_dict.items():
        if col in df.columns:
            val_player = player_row[col]
            val_avg = df[col].mean()
            if val_avg == 0: continue

            # Absolu pour les négatifs (ex: profondeur)
            calc_player = abs(val_player)
            calc_avg = abs(val_avg)
            
            pct_diff = ((calc_player - calc_avg) / calc_avg) * 100
            
            data.append({
                "Indicateur": label, 
                "Différence %": pct_diff,
                "Valeur Brute": calc_player,
                "Moyenne Groupe": calc_avg
            })

    df_chart = pd.DataFrame(data)
    # Couleur : Noir si performance > moyenne, Rouge si < moyenne
    df_chart['Couleur'] = df_chart['Différence %'].apply(lambda x: '#000000' if x >= 0 else '#C0392B')

    fig = px.bar(
        df_chart,
        x="Indicateur",
        y="Différence %",
        color="Couleur",
        text_auto='.1f',
        title="Profil Joueur vs Moyenne Équipe (Écart en %)",
        color_discrete_map="identity"
    )
    
    fig.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.3)
    
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Ecart: %{y:.1f}%<br>Valeur Joueur: %{customdata[0]:.2f}<br>Moyenne Grp: %{customdata[1]:.2f}",
        customdata=df_chart[['Valeur Brute', 'Moyenne Groupe']]
    )
    
    fig.update_layout(showlegend=False, height=400, yaxis_title="Ecart à la moyenne (%)")
    return fig


def chart_phase_detail(df, player_row, col_name, label):
    if col_name not in df.columns:
        return None

    # 1. Analyse de la donnée
    avg_raw = df[col_name].mean()
    is_negative_data = avg_raw < 0
    
    # 2. Récupération du Record et du Nom
    try:
        if is_negative_data:
            idx_record = df[col_name].idxmin()
        else:
            idx_record = df[col_name].idxmax()
            
        record_val_raw = df.loc[idx_record, col_name]
        record_name = df.loc[idx_record, 'Joueur']
        
        if len(str(record_name)) > 15:
            record_name = str(record_name)[:12] + "..."
            
    except:
        record_val_raw = 0
        record_name = "?"

    # 3. Valeurs Absolues pour l'affichage graphique
    val_player_abs = abs(player_row[col_name])
    val_avg_abs = abs(avg_raw)
    val_record_abs = abs(record_val_raw)

    label_record_display = f"Record<br>({record_name})"

    df_chart = pd.DataFrame({
        "Comparaison": ["Joueur", "Moyenne", label_record_display],
        "Valeur": [val_player_abs, val_avg_abs, val_record_abs],
        "Couleur": ["#C0392B", "#95a5a6", "#000000"]
    })

    fig = px.bar(
        df_chart,
        x="Comparaison",
        y="Valeur",
        color="Couleur",
        title=label,
        text_auto='.1f',
        color_discrete_map="identity"
    )
    
    fig.update_layout(
        showlegend=False, 
        margin=dict(t=40, b=0, l=0, r=0), 
        height=250, 
        xaxis_title=None, 
        yaxis_title=None,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_yaxes(showgrid=True, gridcolor='lightgrey')
    return fig


# --- 4. PAGE PRINCIPALE ---

def show_page():
    st.title("Analyse CMJ : Profilage Physique")
    
    # --- UPLOAD ---
    st.markdown("### 📂 Chargement des Données")
    uploaded_file = st.file_uploader("Mettre à jour le fichier 'MASTER_CMJ_COMPLET.csv' ici (Prioritaire)", type=["csv"])
    
    df = pd.DataFrame()

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, sep=";")
        except Exception as e:
            st.error(f"Erreur lecture CSV : {e}")
    else:
        df = utils.load_cmj_data()
        if not df.empty:
            st.info("ℹ️ Utilisation du fichier local 'MASTER_CMJ_COMPLET.csv'.")
    
    if df.empty:
        st.warning("⚠️ Aucun fichier CMJ valide chargé. Veuillez uploader le CSV.")
        return

    df.columns = df.columns.str.strip()

    if 'Joueur' not in df.columns:
        st.error(f"La colonne 'Joueur' est introuvable. Colonnes dispos : {list(df.columns)}")
        return

    # -------------------------------------------------------------------------
    # PARTIE 1 : RÉFÉRENCES
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 1. Références Groupe & Configuration")
    
    default_selection = ["Hauteur de Saut (cm)", "Puissance Max (W)", "Durée Freinage (ms)"]
    valid_defaults = [k for k in default_selection if k in ALL_KPI]
    
    selected_labels = st.multiselect(
        "Indicateurs clés pour l'analyse :",
        options=list(ALL_KPI.keys()),
        default=valid_defaults,
        max_selections=5
    )
    selected_kpis = {k: ALL_KPI[k] for k in selected_labels}

    st.markdown("##### Moyennes du Groupe (Valeurs Absolues)")
    chart_team_averages(df, selected_kpis)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # PARTIE 2 : PROFIL JOUEUR
    # -------------------------------------------------------------------------
    st.markdown("### 2. Focus Joueur")
    
    joueurs_list = sorted(df['Joueur'].dropna().unique())
    selected_player = st.selectbox("Sélectionner un joueur :", options=joueurs_list)
    
    player_data = df[df['Joueur'] == selected_player].iloc[-1]

    if selected_kpis:
        st.caption("Barres Noires = Au-dessus de la moyenne (en valeur absolue).")
        st.plotly_chart(chart_player_profile_normalized(df, player_data, selected_kpis), use_container_width=True, key="profile_chart")
    else:
        st.warning("Veuillez sélectionner des indicateurs ci-dessus.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # PARTIE 3 : DÉTAILS PAR PHASE AVEC GLOSSAIRE INTÉGRÉ
    # -------------------------------------------------------------------------
    st.markdown("### 3. Analyse Détaillée par Phase")
    
    tab_names = ["Général", "Phase Décharge", "Phase Excentrique", "Phase Concentrique", "Atterrissage"]
    tabs = st.tabs(tab_names)

    phases_map = [
        (tabs[0], KPI_GENERAL, "Général"),
        (tabs[1], KPI_DECHARGE, "Phase Décharge"),
        (tabs[2], KPI_EXCENTRIQUE, "Phase Excentrique"),
        (tabs[3], KPI_CONCENTRIQUE, "Phase Concentrique"),
        (tabs[4], KPI_ATTERRISSAGE, "Atterrissage")
    ]

    for i, (tab, kpi_dict, phase_name) in enumerate(phases_map):
        with tab:
            # 1. Affichage des graphiques
            valid_kpis = {k: v for k, v in kpi_dict.items() if v in df.columns}
            
            if not valid_kpis:
                st.info("Pas de données disponibles pour cette phase.")
            else:
                cols = st.columns(2)
                for index, (label, col_name) in enumerate(valid_kpis.items()):
                    with cols[index % 2]:
                        fig = chart_phase_detail(df, player_data, col_name, label)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key=f"chart_{i}_{index}_{label}")

            # 2. Affichage du Glossaire Spécifique
            st.markdown("---")
            st.markdown(f"#### 📖 Glossaire : {phase_name}")
            
            if phase_name in GLOSSARY_DEFINITIONS:
                definitions = GLOSSARY_DEFINITIONS[phase_name]
                df_glossary = pd.DataFrame(list(definitions.items()), columns=["Indicateur", "Définition & Interprétation"])
                # Suppression de l'index numérique (0, 1, 2) en utilisant 'Indicateur' comme index
                st.table(df_glossary.set_index('Indicateur'))