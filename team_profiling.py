import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
import unicodedata
import numpy as np

SDR_RED = "#D71920"

# --- Fonctions Utilitaires ---

def remove_accents(input_str):
    if not isinstance(input_str, str): return str(input_str)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def find_column_in_df(df, label):
    keywords = [remove_accents(label).lower()]
    df_cols_clean = [remove_accents(str(c)).lower().strip() for c in df.columns]
    
    for k in keywords:
        for idx, col_name in enumerate(df_cols_clean):
            if k in col_name: return df.columns[idx]
            
    parts = label.split(" ")
    if len(parts) > 1:
        main_key = parts[0].lower()
        for idx, col_name in enumerate(df_cols_clean):
            if main_key in col_name: return df.columns[idx]
    return None

def clean_numeric_series(series):
    return pd.to_numeric(series, errors='coerce')

def is_inverted_metric(label):
    keywords = ['temps', 'chrono', '10m', '505', 'agilité', 'masse grasse', 'landing']
    return any(x in str(label).lower() for x in keywords)

def get_unit(label):
    """
    Détermine l'unité en fonction du nom de la colonne (label).
    Ordre de priorité important pour éviter les conflits (ex: Landing % vs Landing N).
    """
    l = label.lower()
    
    # 0. Ratio et compteurs (Pas d'unité) - Priorité Max
    if "ratio" in l or "nb " in l: return ""

    # 1. Unités composées explicites
    if "n/kg" in l: return "N/kg"
    if "w/kg" in l: return "W/kg"
    if "m/s2" in l or "m/s²" in l: return "m/s²"
    
    # 2. Pourcentage (Doit passer AVANT les tests de force/landing)
    if "%" in l or "img" in l: return "%"

    # 3. Accélérations
    if "amax" in l or "dmax" in l: return "m/s²"
    
    # 4. Isocinétisme (Nm)
    if "conc" in l or "exc" in l or "nm" in l: return "Nm"

    # 5. Puissance (W) & Poids (kg)
    if "1rm" in l or "poids" in l: return "kg"
    if "watt" in l or "keiser" in l or "tirage" in l or "couché" in l: return "W"

    # 6. Force (N) - Landing simple tombe ici (si pas N/kg ni %)
    if "add" in l or "abd" in l or "nordic" in l or "force" in l or "landing" in l: return "N"
    
    # 7. Autres standards
    if "vma" in l or "vmax" in l or "vitesse" in l: return "km/h"
    if "cmj" in l or "saut" in l or "taille" in l or "reach" in l or "knee" in l: return "cm"
    if "temps" in l or "chrono" in l or "10m" in l or "505" in l: return "s"
    if "distance" in l or "landmine" in l: return "m"
    if "score" in l: return "pts"
    
    return ""

# --- Page Principale ---

def show_team_page(df, structure_dict):
    st.markdown(f"<h2 style='color:{SDR_RED}; border-bottom:1px solid {SDR_RED}; padding-bottom:5px;'>ANALYSE COLLECTIVE</h2>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("Aucune donnée disponible.")
        return

    # Gestion de l'état (Session State)
    if 'selected_player_profiling' not in st.session_state:
        st.session_state.selected_player_profiling = None

    st.markdown("   ")
  
    # --- Sélecteurs du haut ---
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        cat_sel = st.selectbox("Catégorie : ", list(structure_dict.keys()))
    with c2:
        metric_sel = st.selectbox("Indicateur : ", structure_dict[cat_sel])
    
    col_name = find_column_in_df(df, metric_sel)
    col_poste = find_column_in_df(df, "Poste")
    
    with c3:
        all_postes = sorted(df[col_poste].dropna().unique()) if col_poste else []
        sel_poste = st.multiselect("Filtrer par Poste", all_postes, default=all_postes)

    if not col_name:
        st.error("Données introuvables.")
        return

    # Préparation des données globales
    df_main = df.copy()
    if col_poste and sel_poste:
        df_main = df_main[df_main[col_poste].isin(sel_poste)]

    df_main['Valeur_Clean'] = clean_numeric_series(df_main[col_name])
    df_main = df_main.dropna(subset=['Valeur_Clean', 'Joueur'])
    
    inverted = is_inverted_metric(metric_sel)
    avg_val = df_main['Valeur_Clean'].mean()
    unit = get_unit(metric_sel)

    st.markdown("---")

    # --- Graphique 1 : Vue d'ensemble (Barres) ---
    st.subheader(f"Classement Équipe : {metric_sel}")

    if inverted:
        df_sorted = df_main.sort_values('Valeur_Clean', ascending=True)
    else:
        df_sorted = df_main.sort_values('Valeur_Clean', ascending=False)

    color_col = col_poste if col_poste else None
    
    fig_all = px.bar(
        df_sorted, 
        x='Joueur', 
        y='Valeur_Clean',
        color=color_col, 
        text='Valeur_Clean',
        color_discrete_sequence=[SDR_RED, 'black', '#555', '#888'] if color_col else [SDR_RED]
    )
    
    fig_all.add_hline(y=avg_val, line_dash="dash", line_color="#333", annotation_text=f"Moyenne : {avg_val:.2f}")
    fig_all.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_all.update_layout(
        xaxis_title="", 
        yaxis_title=f"{metric_sel} ({unit})",
        template="simple_white",
        height=450,
        margin=dict(b=50) 
    )
    
    st.plotly_chart(fig_all, use_container_width=True)

    # --- Graphique 2 : Analyse Croisée (4 Zones) ---
    st.markdown("---")
    st.markdown(f"<h4 style='color:{SDR_RED};'>Analyse croisée (Nuage de points)</h4>", unsafe_allow_html=True)
    
    all_kpis_flat = []
    for cat, vars_list in structure_dict.items():
        all_kpis_flat.extend(vars_list)
        
    c_sc1, c_sc2 = st.columns(2)
    with c_sc1:
        def_x = 0
        for i, k in enumerate(all_kpis_flat):
            if "vmax" in k.lower(): 
                def_x = i
                break
        scat_x = st.selectbox("Axe X (Horizontal)", all_kpis_flat, index=def_x, key="scat_x")
        
    with c_sc2:
        def_y = 1 if len(all_kpis_flat) > 1 else 0
        for i, k in enumerate(all_kpis_flat):
            if "cmj" in k.lower() or "saut" in k.lower(): 
                def_y = i
                break
        scat_y = st.selectbox("Axe Y (Vertical)", all_kpis_flat, index=def_y, key="scat_y")

    col_x_sc = find_column_in_df(df, scat_x)
    col_y_sc = find_column_in_df(df, scat_y)

    if col_x_sc and col_y_sc:
        df_scatter = df.copy()
        if col_poste and sel_poste:
            df_scatter = df_scatter[df_scatter[col_poste].isin(sel_poste)]
            
        df_scatter['Val_X'] = clean_numeric_series(df_scatter[col_x_sc])
        df_scatter['Val_Y'] = clean_numeric_series(df_scatter[col_y_sc])
        df_scatter = df_scatter.dropna(subset=['Val_X', 'Val_Y'])
        
        if not df_scatter.empty:
            mean_x = df_scatter['Val_X'].mean()
            mean_y = df_scatter['Val_Y'].mean()
            
            fig_scatter = px.scatter(
                df_scatter,
                x='Val_X', y='Val_Y',
                color=col_poste if col_poste else None,
                text='Joueur',
                hover_data=['Joueur'],
                color_discrete_sequence=[SDR_RED, 'black', '#555', '#888'] if col_poste else [SDR_RED]
            )
            fig_scatter.add_vline(x=mean_x, line_width=1, line_dash="dash", line_color=SDR_RED)
            fig_scatter.add_hline(y=mean_y, line_width=1, line_dash="dash", line_color=SDR_RED)
            fig_scatter.update_traces(textposition='top center', marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
            fig_scatter.update_layout(
                title=f"{scat_x} vs {scat_y}",
                xaxis_title=scat_x, yaxis_title=scat_y,
                template="simple_white", height=500
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    st.subheader("Distribution des joueurs (Boite à moustache)")
    
    # Sélecteur Indicateur
    dist_kpi = st.selectbox("Indicateur à analyser :", all_kpis_flat, index=0, key="dist_kpi_interactive")
    col_dist = find_column_in_df(df, dist_kpi)

    if col_dist:
        # Données
        df_viz = df.copy()
        if col_poste and sel_poste:
            df_viz = df_viz[df_viz[col_poste].isin(sel_poste)]
        
        df_viz['Valeur'] = clean_numeric_series(df_viz[col_dist])
        df_viz = df_viz.dropna(subset=['Valeur', 'Joueur'])

        if not df_viz.empty:
            unit_d = get_unit(dist_kpi)
            mean_val = df_viz['Valeur'].mean()
            
            # --- MENU SELECTION MANUEL (Backup & Synchro) ---
            all_p_list = sorted(df_viz['Joueur'].unique())
            
            col_sel_manual, _ = st.columns([1, 2])
            with col_sel_manual:
                curr_idx = 0
                if st.session_state.selected_player_profiling in all_p_list:
                    curr_idx = all_p_list.index(st.session_state.selected_player_profiling)
                
                def update_from_select():
                    st.session_state.selected_player_profiling = st.session_state.manual_player_picker
                
                manual_sel = st.selectbox(
                    "Sélectionner un joueur (ou cliquer sur le graphique) :", 
                    all_p_list, 
                    index=curr_idx,
                    key="manual_player_picker",
                    on_change=update_from_select
                )

            # --- JITTER & STYLE ---
            np.random.seed(42) 
            df_viz['Y_Jitter'] = np.random.uniform(-0.15, 0.15, size=len(df_viz))

            current_selection = st.session_state.selected_player_profiling
            # Si vide, on prend celui du menu
            if not current_selection:
                 current_selection = manual_sel
                 st.session_state.selected_player_profiling = manual_sel

            # Tri
            df_viz['SortOrder'] = df_viz['Joueur'].apply(lambda x: 1 if x == current_selection else 0)
            df_viz = df_viz.sort_values('SortOrder', ascending=True)

            # Couleurs
            colors = []
            sizes = []
            opacities = []
            lines_width = []
            lines_color = []

            for p in df_viz['Joueur']:
                if p == current_selection:
                    colors.append(SDR_RED)
                    sizes.append(25)
                    opacities.append(1.0)
                    lines_width.append(2)
                    lines_color.append('black')
                else:
                    colors.append("#888888")
                    sizes.append(12)
                    opacities.append(0.6)
                    lines_width.append(1)
                    lines_color.append('white')

            df_viz['Color'] = colors
            df_viz['Size'] = sizes
            df_viz['Opacity'] = opacities
            
            # --- FIGURE ---
            fig_interactive = go.Figure()

            fig_interactive.add_trace(go.Scatter(
                x=df_viz['Valeur'],
                y=df_viz['Y_Jitter'], 
                mode='markers',
                text=df_viz['Joueur'],
                customdata=df_viz['Joueur'].values,
                marker=dict(
                    color=colors,
                    size=sizes,
                    opacity=opacities,
                    line=dict(width=lines_width, color=lines_color),
                    symbol='circle'
                ),
                hovertemplate="<b>%{text}</b><br>Valeur: %{x:.2f}<extra></extra>",
                showlegend=False
            ))

            fig_interactive.add_vline(x=mean_val, line_width=2, line_dash="dash", line_color=SDR_RED, 
                                      annotation_text="Moy", annotation_position="top right")

            fig_interactive.update_layout(
                title=f"Distribution : {dist_kpi}",
                xaxis_title=f"Valeur ({unit_d})",
                yaxis=dict(showticklabels=False, range=[-0.5, 0.5], showgrid=False),
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
                template="simple_white",
                clickmode='event+select',
                dragmode='zoom'
            )

            # --- AFFICHAGE ---
            event = st.plotly_chart(
                fig_interactive, 
                on_select="rerun", 
                selection_mode="points", 
                use_container_width=True,
                key="dist_chart_interactive"
            )

            # Gestion Clic
            if event and event.get("selection") and event["selection"]["points"]:
                clicked_point = event["selection"]["points"][0]
                clicked_name = clicked_point.get("customdata")
                if clicked_name and clicked_name != st.session_state.selected_player_profiling:
                    st.session_state.selected_player_profiling = clicked_name
                    st.rerun()

            st.markdown("---")

            sel_p = st.session_state.selected_player_profiling
            if sel_p:
                player_row = df_viz[df_viz['Joueur'] == sel_p]
                if not player_row.empty:
                    val_p = player_row['Valeur'].iloc[0]
                    diff = val_p - mean_val
                    
                    st.markdown(f"<h3 style='text-align: center; color:{SDR_RED};'>{sel_p}</h3>", unsafe_allow_html=True)
                    
                    col_metrics = st.columns(3)
                    
                    col_metrics[0].metric("Valeur", f"{val_p:.2f} {unit_d}")
                    col_metrics[1].metric("Moyenne", f"{mean_val:.2f} {unit_d}")
                    
                    is_good = (diff < 0) if is_inverted_metric(dist_kpi) else (diff > 0)
                    col_metrics[2].metric("Écart", f"{diff:+.2f} {unit_d}", 
                                          delta_color="normal" if is_good else "inverse")
            else:
                st.info("Sélectionnez un joueur pour voir les détails.")