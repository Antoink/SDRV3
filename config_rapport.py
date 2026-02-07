import pandas as pd
import re
import unicodedata

# =============================================================================
# 1. CONSTANTES & CONFIGURATIONS
# =============================================================================

SDR_RED = "#D71920"

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
    "Squat Keiser": "Keiser squat R=100", "Tirage Dos Keiser": "Tirage dos Keiser", "Développé couché (W)": "Developpé couché (W)",
    "Développé couché (W/kg)": "Developpé couché (W/kg)", "Landmine Throw": "Landmine throw",
    "VMA": "VMA", "Temps 10m (Terrain)": "Temps 10m", "5-0-5": "5 - 0 - 5",
    "Distance Totale": "Distance totale", "Distance HSR": "Distance HSR",
    "Nb Accélérations": "Nb Acc", "Nb Décélérations": "Nb Dec",
    "Vmax": "Vmax", "Amax": "Amax", "Dmax": "Dmax"
}

OFFICIAL_STRUCTURE = {
    "PROFILAGE MOTEUR": [
        "Somme ADD", "Ratio Squeeze", "Somme ABD", 
        "Knee To Wall (G)", "Knee To Wall (D)",
        "Nordic Ischio (G)", "Nordic Ischio (D)", 
        "Landing %", "Sit And Reach",
        "Q Conc 60° (G)", "Q Conc 60° (D)", "Q Conc 240° (G)", "Q Conc 240° (D)",
        "IJ Conc 60° (G)", "IJ Conc 60° (D)", "IJ Conc 240° (G)", "IJ Conc 240° (D)",
        "IJ Exc 30° (G)", "IJ Exc 30° (D)",
        "Score Sommeil", "Score Nutrition"
    ],
    "PROFILAGE ATHLÉTIQUE": [
        "CMJ (cm)", "Wattbike (6s)", "Squat Keiser", "Tirage Dos Keiser", 
         "Développé couché (W)", "Développé couché (W/kg)", "Landmine Throw"
    ],
    "PROFILAGE PHYSIOLOGIQUE": [
        "VMA", "Temps 10m (Terrain)", "5-0-5", "Distance Totale", "Distance HSR", 
        "Nb Accélérations", "Nb Décélérations", "Vmax", "Amax", "Dmax"
    ],
}

REPORT_NORMES = {
    "Knee To Wall (G)": [5, 9], "Knee To Wall (D)": [5, 9],        
    "Sit And Reach": [20, 24],                                      
    "Adducteurs (G)": [33, 39], "Adducteurs (D)": [33, 39],         
    "Abducteurs (G)": [33, 39], "Abducteurs (D)": [33, 39], 
    "Somme ADD": [34, 39], "Somme ABD": [34, 39], "Ratio Squeeze": [0.90, 1.10],
    "Landing %":[5,10], "Landing (G)": [20, 30], "Landing (D)": [20, 30],
    "Nordic Ischio (G)": [0.7, 0.8], "Nordic Ischio (D)": [0.7, 0.8], 
    "Q Conc 60° (G)": [2.8, 3.1], "Q Conc 60° (D)": [2.8, 3.1],     
    "Q Conc 240° (G)": [1.9, 2.2], "Q Conc 240° (D)": [1.9, 2.2],   
    "IJ Conc 60° (G)": [1.5, 1.8], "IJ Conc 60° (D)": [1.5, 1.8],   
    "IJ Conc 240° (G)": [1.2, 1.5], "IJ Conc 240° (D)": [1.2, 1.5], 
    "IJ Exc 30° (G)": [2.0, 2.4], "IJ Exc 30° (D)": [2.0, 2.4],     
    "Score Sommeil": [4, 8], "Score Nutrition": [4, 8],
    "Développé couché (W)": [400, 500], "Développé couché (W/kg)": [5, 7], 
    "Masse Grasse Plis (mm)": [40, 50],
    "CMJ (cm)": [35, 42], "Wattbike (6s)": [1100, 1300], 
    "Squat Keiser": [1500, 2000], "Tirage Dos Keiser": [800, 1200], 
    "Landmine Throw": [20, 30], 
    "VMA": [16, 22], "Distance HSR": [800, 1200], "Vmax": [31, 35],
    "Temps 10m (Terrain)": [1.76, 1.90], "5-0-5": [2.20, 2.40],
    "Distance Totale": [8000, 11000], "Nb Accélérations": [50, 150], 
    "Nb Décélérations": [50, 150], "Amax": [5, 7], "Dmax": [5, 7] 
}

# --- C'EST CETTE LISTE QUI MANQUAIT ---
RELATIVE_NORM_KEYS = [
    "Nordic Ischio (G)", "Nordic Ischio (D)",
    "Q Conc 60° (G)", "Q Conc 60° (D)",
    "Q Conc 240° (G)", "Q Conc 240° (D)",
    "IJ Conc 60° (G)", "IJ Conc 60° (D)",
    "IJ Conc 240° (G)", "IJ Conc 240° (D)",
    "IJ Exc 30° (G)", "IJ Exc 30° (D)"
]

UNITS = {
    "Knee To Wall": "cm", "Sit And Reach": "cm", "Landing": "N/kg", "Landing %": "%",
    "Adducteurs": "N", "Somme ADD": "N", "Abducteurs": "N", "Somme ABD": "N", "Nordic Ischio": "N",
    "Q Conc 60°": "Nm", "Q Conc 240°": "Nm", "IJ Conc 60°": "Nm", "IJ Conc 240°": "Nm", "IJ Exc 30°": "Nm",
    "CMJ (cm)": "cm", "Landmine Throw": "m",
    "Wattbike (6s)": "W", "Développé couché (W)": "W", "Développé couché (W/kg)": "W/kg",
    "Squat Keiser": "W", "Tirage Dos Keiser": "W",
    "VMA": "km/h", "Vmax": "km/h", "Temps 10m (Terrain)": "s", "5-0-5": "s",
    "Distance Totale": "m", "Distance HSR": "m", "Amax": "m/s²", "Dmax": "m/s²",
    "Score Sommeil": "pts", "Score Nutrition": "pts"
}

