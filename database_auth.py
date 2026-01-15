import sqlite3

def setup_admin():
    conn = sqlite3.connect("orientation_data.db")
    # Création de la table des conseillers
    conn.execute('''CREATE TABLE IF NOT EXISTS conseillers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    
    # Ajout d'un compte par défaut (Identifiant: admin / MDP: 1234)
    try:
        conn.execute("INSERT INTO conseillers (username, password) VALUES (?, ?)", ("admin", "1234"))
        conn.commit()
        print("✅ Compte conseiller créé : admin / 1234")
    except:
        print("⚠️ Le compte admin existe déjà.")
    conn.close()

if __name__ == "__main__":
    setup_admin()