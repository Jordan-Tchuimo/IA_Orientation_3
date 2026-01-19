import pandas as pd
import random

def generer():
    data = []
    # Textes simplifiés pour éviter les erreurs d'encodage
    revenus = ["Tranche_A", "Tranche_B", "Tranche_C"]
    interets = ["Sciences_Tech", "Arts_Creativite"]
    filieres = ["SCIENCES", "ARTS"]
    
    for _ in range(600):
        m_sci = round(random.uniform(6, 18), 2)
        m_lit = round(random.uniform(6, 18), 2)
        rev = random.choice(revenus)
        int_ = random.choice(interets)
        
        # Logique de base + 15% de bruit pour le réalisme
        filiere = filieres[0] if (m_sci + (2 if int_ == interets[0] else 0)) > (m_lit + (2 if int_ == interets[1] else 0)) else filieres[1]
        if random.random() < 0.15: filiere = random.choice(filieres)
            
        data.append([m_sci, m_lit, rev, int_, filiere])
    
    pd.DataFrame(data, columns=["moy_sci", "moy_lit", "revenu", "interet", "filiere"]).to_csv("donnees_apprentissage.csv", index=False)
    print("✅ Fichier donnees_apprentissage.csv créé avec succès.")

if __name__ == "__main__":
    generer()