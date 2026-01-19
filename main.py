import flet as ft
import sqlite3
import datetime
import csv
import io
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from engine import MoteurOrientation

# --- 1. LOGIQUE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("orientation_data.db", check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS resultats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, moy_sci REAL, moy_lit REAL, 
        revenu TEXT, interet TEXT, score_sci REAL, score_lit REAL, filiere TEXT, 
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS conseillers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    try:
        conn.execute("INSERT INTO conseillers (username, password) VALUES (?, ?)", ("admin", "1234"))
    except: pass
    conn.commit(); conn.close()

def verifier_acces(user, pwd):
    conn = sqlite3.connect("orientation_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conseillers WHERE username=? AND password=?", (user, pwd))
    res = cursor.fetchone(); conn.close()
    return res is not None

# --- 2. LOGIQUE D'EXPORTATION ---
def generer_pdf_complet():
    # Création d'un nom de fichier unique
    nom_f = f"Rapport_Orientation_{datetime.datetime.now().strftime('%M%S')}.pdf"
    chemin_assets = os.path.join("assets", nom_f)
    
    conn = sqlite3.connect("orientation_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nom, moy_sci, moy_lit, filiere, score_sci FROM resultats ORDER BY nom ASC")
    donnees = cursor.fetchall()
    conn.close()
    
    if not donnees: return "Base vide"
    
    pdf = FPDF(); pdf.add_page(); pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "RAPPORT D'ORIENTATION - IA SYSTEM", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(10)
    
    # En-tête du tableau
    pdf.set_font("helvetica", "B", 10); pdf.set_fill_color(200, 220, 255)
    pdf.cell(10, 8, "N°", border=1, fill=True); pdf.cell(50, 8, "Nom", border=1, fill=True); pdf.cell(15, 8, "Sci", border=1, fill=True); pdf.cell(15, 8, "Lit", border=1, fill=True); pdf.cell(60, 8, "IA Conseil", border=1, fill=True); pdf.cell(20, 8, "Conf.", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", "", 9)
    for i, r in enumerate(donnees, start=1):
        pdf.cell(10, 8, str(i), border=1); pdf.cell(50, 8, str(r[0]), border=1); pdf.cell(15, 8, str(r[1]), border=1); pdf.cell(15, 8, str(r[2]), border=1); pdf.cell(60, 8, str(r[3]), border=1); pdf.cell(20, 8, f"{round(r[4]*100, 1)}%", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Sauvegarde physique sur le serveur Render
    pdf.output(chemin_assets)
    return nom_f

# --- 3. INTERFACE UTILISATEUR (FLET) ---
async def main(page: ft.Page):
    # Création du dossier assets indispensable pour l'hébergement
    if not os.path.exists("assets"):
        os.makedirs("assets")

    init_db(); moteur = MoteurOrientation(); moteur.entrainer_automatique()
    page.title = "IA Orientation - Master 2026"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS 

    def notifier(m, c=ft.Colors.BLUE):
        page.overlay.append(ft.SnackBar(ft.Text(m, weight="bold"), bgcolor=c, open=True)); page.update()

    # --- ACTION D'EXPORTATION AVEC SÉCURITÉ ---
    async def exporter_pdf_action(e):
        nom_fichier = generer_pdf_complet()
        if nom_fichier != "Base vide":
            # 1. Fenêtre de secours pour clic manuel (très fiable)
            dialog = ft.AlertDialog(
                title=ft.Text("Rapport Généré !"),
                content=ft.Column([
                    ft.Text("Le navigateur peut bloquer le téléchargement automatique."),
                    ft.ElevatedButton(
                        "CLIQUEZ ICI POUR TÉLÉCHARGER", 
                        icon=ft.Icons.DOWNLOAD,
                        url=f"/{nom_fichier}", # Flet sert les assets à la racine
                        on_click=lambda _: setattr(dialog, "open", False)
                    )
                ], tight=True),
            )
            page.overlay.append(dialog)
            dialog.open = True
            
            # 2. Tentative de lancement automatique
            page.launch_url(f"/{nom_fichier}")
            page.update()
        else:
            notifier("❌ La base de données est vide", ft.Colors.RED)

    # --- COMPOSANTS UI DU DASHBOARD ---
    nom_in = ft.TextField(label="Nom de l'élève", width=450, border_radius=15)
    m_sci = ft.TextField(label="Moyenne Scientifique (0-20)", width=220, border_radius=15)
    m_lit = ft.TextField(label="Moyenne Littéraire (0-20)", width=220, border_radius=15)
    rev_in = ft.Dropdown(label="Revenu familial mensuel", width=450, border_radius=15, options=[
        ft.dropdown.Option(key="Tranche_A", text="Tranche A : [0 - 150 000 FCFA]"),
        ft.dropdown.Option(key="Tranche_B", text="Tranche B : [150 000 - 450 000 FCFA]"),
        ft.dropdown.Option(key="Tranche_C", text="Tranche C : [+ de 450 000 FCFA]")
    ])
    int_in = ft.Dropdown(label="Centre d'intérêt", width=450, border_radius=15, options=[
        ft.dropdown.Option(key="Sciences_Tech", text="Sciences & Technologie"),
        ft.dropdown.Option(key="Arts_Creativite", text="Arts & Créativité")
    ])

    res_final = ft.Text("Prêt", size=24, weight="bold", color=ft.Colors.LIGHT_GREEN_400)
    conf_txt = ft.Text("", italic=True, size=18, weight="bold")
    prog_conf = ft.ProgressBar(width=400, value=0, visible=False, color=ft.Colors.LIGHT_GREEN_400)
    xai_display = ft.Column(visible=False, horizontal_alignment="center", width=380, spacing=10)

    # --- LOGIQUE DE CALCUL ---
    async def calculer(e):
        try:
            sv = float(m_sci.value.strip().replace(",", ".")); lv = float(m_lit.value.strip().replace(",", "."))
            filiere, conf = moteur.predire_avec_probabilite(sv, lv, rev_in.value, int_in.value)
            res_final.value = f"CONSEIL IA : {filiere}"; conf_txt.value = f"Confiance IA : {round(conf*100, 2)}%"
            prog_conf.value = conf; prog_conf.visible = True
            
            # XAI Simulation (Interprétabilité)
            p_notes = (sv + lv) * 2; p_social = 35 if rev_in.value != "Tranche_A" else 15; p_perso = 25
            tot = p_notes + p_social + p_perso
            pn = [p_notes/tot, p_social/tot, p_perso/tot]
            
            xai_display.controls = [
                ft.Row([ft.Text("Scolaire", width=90), ft.ProgressBar(value=pn[0], color="blue", width=180), ft.Text(f"{round(pn[0]*100)}%")], alignment="center"),
                ft.Row([ft.Text("Social", width=90), ft.ProgressBar(value=pn[1], color="orange", width=180), ft.Text(f"{round(pn[1]*100)}%")], alignment="center"),
                ft.Row([ft.Text("Intérêt", width=90), ft.ProgressBar(value=pn[2], color="green", width=180), ft.Text(f"{round(pn[2]*100)}%")], alignment="center")
            ]
            xai_display.visible = True
            
            conn = sqlite3.connect("orientation_data.db"); conn.execute("INSERT INTO resultats (nom, moy_sci, moy_lit, revenu, interet, score_sci, score_lit, filiere) VALUES (?,?,?,?,?,?,?,?)", (nom_in.value.upper(), sv, lv, rev_in.value, int_in.value, conf, 0.0, filiere)); conn.commit(); conn.close()
            notifier("✅ Analyse enregistrée", ft.Colors.GREEN); page.update()
        except: notifier("❌ Erreur de saisie", ft.Colors.RED)

    # --- ASSEMBLAGE FINAL ---
    login_card = ft.Container(content=ft.Column([
        ft.Icon(ft.Icons.LOCK_PERSON, size=80, color=ft.Colors.LIGHT_GREEN_400),
        ft.Text("AUTHENTIFICATION CONSEILLER", size=20, weight="bold"),
        user_log := ft.TextField(label="Identifiant", width=320),
        pass_log := ft.TextField(label="Mot de passe", width=320, password=True),
        ft.ElevatedButton("ACCÉDER AU SYSTÈME", on_click=lambda _: tenter_connexion(), width=320, bgcolor=ft.Colors.INDIGO_600, color="white")
    ], horizontal_alignment="center"), expand=True, alignment=ft.Alignment(0,0))

    async def tenter_connexion():
        if verifier_acces(user_log.value, pass_log.value):
            page.clean()
            page.add(
                ft.AppBar(title=ft.Text("IA ORIENTATION - DASHBOARD MASTER"), bgcolor=ft.Colors.INDIGO_900),
                ft.Column([
                    ft.Container(height=20),
                    ft.Container(bgcolor=ft.Colors.BLUE_GREY_800, padding=30, border_radius=20, content=ft.Column([
                        nom_in, ft.Row([m_sci, m_lit], alignment="center"), rev_in, int_in,
                        ft.Row([
                            ft.ElevatedButton("ANALYSER", on_click=calculer, bgcolor=ft.Colors.GREEN_700, color="white"),
                            ft.ElevatedButton("EXPORTER PDF", on_click=exporter_pdf_action, bgcolor=ft.Colors.RED_700, color="white"),
                        ], alignment="center")
                    ], horizontal_alignment="center")),
                    ft.Container(height=20),
                    ft.Column([res_final, conf_txt, prog_conf], horizontal_alignment="center"),
                    ft.Container(padding=20, content=xai_display)
                ], scroll=ft.ScrollMode.ALWAYS)
            )
        else: notifier("🔒 Accès refusé", ft.Colors.RED)

    page.add(login_card)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    # CRUCIAL : assets_dir définit le dossier public pour les téléchargements
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="assets")