# diagnostic_engine.py
from disease_data import DISEASE_DB

class DiagnosticEngine:
    def __init__(self):
        self.selected_crop = None
        self.selected_symptoms = []
        self.all_symptoms = set()
        self.build_symptom_map()
    
    def build_symptom_map(self):
        self.symptom_map = {}
        for crop, diseases in DISEASE_DB.items():
            for disease, info in diseases.items():
                for symptom in info["symptoms"]:
                    if symptom not in self.symptom_map:
                        self.symptom_map[symptom] = []
                    self.symptom_map[symptom].append((crop, disease))
                    self.all_symptoms.add(symptom)
    
    def set_crop(self, crop):
        self.selected_crop = crop
        self.crop_symptoms = set()
        if crop in DISEASE_DB:
            for disease, info in DISEASE_DB[crop].items():
                for symptom in info["symptoms"]:
                    self.crop_symptoms.add(symptom)
        return list(self.crop_symptoms)
    
    def add_symptom(self, symptom):
        if symptom not in self.selected_symptoms:
            self.selected_symptoms.append(symptom)
    
    def remove_symptom(self, symptom):
        if symptom in self.selected_symptoms:
            self.selected_symptoms.remove(symptom)
    
    def diagnose(self):
        if not self.selected_crop or not self.selected_symptoms:
            return None
        
        results = []
        for disease, info in DISEASE_DB[self.selected_crop].items():
            symptom_match = 0
            disease_symptoms = set(info["symptoms"])
            
            for symptom in self.selected_symptoms:
                if symptom in disease_symptoms:
                    symptom_match += 1
            
            if symptom_match > 0:
                match_percentage = (symptom_match / len(disease_symptoms)) * 100
                results.append({
                    "disease": disease.replace("_", " ").title(),
                    "match": round(match_percentage, 1),
                    "info": info,
                    "symptoms_matched": symptom_match,
                    "total_symptoms": len(disease_symptoms)
                })
        
        results.sort(key=lambda x: x["match"], reverse=True)
        return results
    
    def get_all_symptoms(self):
        return list(self.crop_symptoms)
    
    def reset(self):
        self.selected_crop = None
        self.selected_symptoms = []