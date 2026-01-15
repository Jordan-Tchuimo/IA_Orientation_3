import sqlite3

def init_db():
    """Crée la base de données et la table si elles n'existent pas."""
    conn = sqlite3.connect("orientation.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            moy_sci REAL,
            moy_lit REAL,
            revenu TEXT,
            interet TEXT,
            filiere TEXT,
            score REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def sauvegarder_eleve(nom, m_sci, m_lit, rev, int_eleve, filiere, score):
    """Enregistre un nouvel élève dans la base SQL."""
    conn = sqlite3.connect("orientation.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resultats (nom, moy_sci, moy_lit, revenu, interet, filiere, score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (nom, m_sci, m_lit, rev, int_eleve, filiere, score))
    conn.commit()
    conn.close()