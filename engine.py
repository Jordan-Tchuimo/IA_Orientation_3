import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

class MoteurOrientation:
    def __init__(self):
        # On garde max_depth=4 pour que l'indice de confiance soit réaliste
        self.model = DecisionTreeClassifier(max_depth=4, min_samples_leaf=10, random_state=42)
        self.le_rev = LabelEncoder()
        self.le_int = LabelEncoder()
        self.le_filiere = LabelEncoder()
        self.colonnes = ['moy_sci', 'moy_lit', 'revenu_n', 'interet_n']

    def entrainer_automatique(self):
        try:
            df = pd.read_csv("donnees_apprentissage.csv")
            df['revenu_n'] = self.le_rev.fit_transform(df['revenu'])
            df['interet_n'] = self.le_int.fit_transform(df['interet'])
            y = self.le_filiere.fit_transform(df['filiere'])
            X = df[self.colonnes]
            self.model.fit(X, y)
            print("✅ IA Entraînée avec succès.")
        except Exception as e:
            print(f"❌ Erreur entraînement : {e}")

    def predire_avec_probabilite(self, ms, ml, rev, inte):
        rev_n = self.le_rev.transform([rev])[0]
        int_n = self.le_int.transform([inte])[0]
        
        # On crée un DataFrame avec les noms de colonnes pour éviter l'avertissement jaune
        X = pd.DataFrame([[ms, ml, rev_n, int_n]], columns=self.colonnes)
        
        probabilites = self.model.predict_proba(X)[0]
        confiance = max(probabilites)
        prediction = self.model.predict(X)[0]
        
        return self.le_filiere.inverse_transform([prediction])[0], confiance