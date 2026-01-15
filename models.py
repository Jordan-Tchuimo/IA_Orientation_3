from dataclasses import dataclass

@dataclass
class Filiere:
    nom: str
    cout_annuel: int
    seuil_moyenne: float
    profil_riasec_ideal: str

@dataclass
class Eleve:
    moyenne: float
    score_riasec: str
    revenu_parental: int  # Assurez-vous que ce nom correspond à celui utilisé dans engine.py