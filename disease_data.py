# disease_data.py
DISEASE_DB = {
    "maize": {
        "northern_leaf_blight": {
            "symptoms": ["long cigar-shaped lesions", "gray-green or tan spots", "lesions parallel to leaf veins"],
            "treatment": "Apply fungicides like mancozeb. Use resistant varieties.",
            "cause": "Fungus Exserohilum turcicum",
            "severity": "High"
        },
        "gray_leaf_spot": {
            "symptoms": ["small rectangular lesions", "grayish-brown spots", "lesions between veins"],
            "treatment": "Fungicide application (chlorothalonil). Crop rotation.",
            "cause": "Fungus Cercospora zeae-maydis",
            "severity": "Medium"
        },
        "maize_streak_virus": {
            "symptoms": ["yellow streaks on leaves", "stunted growth", "pale spots"],
            "treatment": "No cure. Control leafhopper vectors. Plant resistant varieties.",
            "cause": "Maize streak virus (MSV)",
            "severity": "High"
        },
        "rust": {
            "symptoms": ["pustules on leaves", "orange/brown powdery spots", "leaf tearing"],
            "treatment": "Fungicides (propiconazole). Resistant hybrids.",
            "cause": "Fungus Puccinia sorghi",
            "severity": "Medium"
        },
        "stalk_rot": {
            "symptoms": ["soft stalk", "lodging", "discolored pith"],
            "treatment": "Improve drainage. Use resistant hybrids. Crop rotation.",
            "cause": "Various fungi (Fusarium, Macrophomina)",
            "severity": "High"
        }
    },
    "tomato": {
        "early_blight": {
            "symptoms": ["dark concentric rings on leaves", "yellowing", "leaf drop"],
            "treatment": "Remove infected leaves. Copper-based fungicides.",
            "cause": "Fungus Alternaria solani",
            "severity": "Medium"
        },
        "late_blight": {
            "symptoms": ["water-soaked lesions", "white fuzzy growth under leaves", "fruit rot"],
            "treatment": "Fungicides (chlorothalonil, mancozeb). Destroy infected plants.",
            "cause": "Fungus Phytophthora infestans",
            "severity": "Very High"
        },
        "tomato_leaf_curl": {
            "symptoms": ["curled leaves", "yellow edges", "stunted growth"],
            "treatment": "Control whiteflies. Remove affected plants.",
            "cause": "Tomato leaf curl virus (TLCV)",
            "severity": "High"
        },
        "bacterial_wilt": {
            "symptoms": ["sudden wilting", "brown vascular tissue", "oozing when cut"],
            "treatment": "No cure. Remove infected plants. Solarize soil.",
            "cause": "Bacterium Ralstonia solanacearum",
            "severity": "Very High"
        },
        "blossom_end_rot": {
            "symptoms": ["dark sunken spots at blossom end of fruit", "leathery texture"],
            "treatment": "Maintain consistent watering. Apply calcium spray.",
            "cause": "Calcium deficiency (environmental)",
            "severity": "Medium"
        }
    }
}

def get_crops():
    return list(DISEASE_DB.keys())

def get_diseases(crop):
    return list(DISEASE_DB.get(crop, {}).keys())

def get_disease_info(crop, disease):
    return DISEASE_DB.get(crop, {}).get(disease, {})