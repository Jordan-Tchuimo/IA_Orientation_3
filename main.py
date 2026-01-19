import flet as ft
import sqlite3
import datetime
import csv
import io
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from engine import MoteurOrientation

# --- 1. INITIALISATION PHYSIQUE (Avant l'app) ---
# Indispensable pour que Render ne plante pas au démarrage
if not os.path.exists("assets"):
    os.makedirs("assets")

# --- 2. LOGIQUE DE DONNÉES ---
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
    try:
        conn = sqlite3.connect("orientation_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conseillers WHERE username=? AND password=?", (user, pwd))
        res = cursor.fetchone(); conn.close()
        return res is not None
    except: return False

# --- 3. LOGIQUE D'EXPORTATION ---
def generer_pdf_complet():
    nom_f = f"Rapport_{datetime.datetime.now().strftime('%M%S')}.pdf"
    chemin_assets = os.path.join("assets", nom_f)
    
    conn = sqlite3.connect("orientation_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nom, moy_sci, moy_lit, filiere, score_sci FROM resultats ORDER BY nom ASC")
    donnees = cursor.fetchall(); conn.close()
    
    if not donnees: return "Base vide"
    
    pdf = FPDF(); pdf.add_page(); pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "RAPPORT D'ORIENTATION - IA SYSTEM", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 10); pdf.set_fill_color(200, 220, 255)
    pdf.cell(10, 8, "N°", border=1, fill=True); pdf.cell(50, 8, "Nom", border=1, fill=True); pdf.cell(15, 8, "Sci", border=1, fill=True); pdf.cell(15, 8, "Lit", border=1, fill=True); pdf.cell(60, 8, "IA Conseil", border=1, fill=True); pdf.cell(20, 8, "Conf.", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", "", 9)
    for i, r in enumerate(donnees, start=1):
        pdf.cell(10, 8, str(i), border=1); pdf.cell(50, 8, str(r[0]), border=1); pdf.cell(15, 8, str(r[1]), border=1); pdf.cell(15, 8, str(r[2]), border=1); pdf.cell(60, 8, str(r[3]), border=1); pdf.cell(20, 8, f"{round(r[4]*100, 1)}%", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.output(chemin_assets)
    return nom_f

# --- 4. INTERFACE PRINCIPALE ---
async def main(page: ft.Page):
    init_db()
    moteur = MoteurOrientation()
    try:
        moteur.entrainer_automatique()
    except:
        print("Note: Entraînement ignoré (données absentes)")

    page.title = "IA Orientation - Master 2026"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS 

    def notifier(m, c=ft.Colors.BLUE):
        page.overlay.append(ft.SnackBar(ft.Text(m, weight="bold"), bgcolor=c, open=True)); page.update()

    # Action Exportation
    async def exporter_pdf_action(e):
        nom_fichier = generer_pdf_complet()
        if nom_fichier != "Base vide":
            dialog = ft.AlertDialog(
                title=ft.Text("Rapport Prêt"),
                content=ft.ElevatedButton("TÉLÉCHARGER LE PDF", icon=ft.Icons.DOWNLOAD, url=f"/{nom_fichier}"),
            )
            page.overlay.append(dialog); dialog.open = True
            page.launch_url(f"/{nom_fichier}"); page.update()
        else:
            notifier("❌ Base vide", ft.Colors.RED)

    # UI Components
    nom_in = ft.TextField(label="Nom de l'élève", width=450)
    m_sci = ft.TextField(label="Moyenne Scientifique", width=220)
    m_lit = ft.TextField(label="Moyenne Littéraire", width=220)
    rev_in = ft.Dropdown(label="Revenu familial", width=450, options=[
        ft.dropdown.Option("Tranche_A", "Tranche A"), ft.dropdown.Option("Tranche_B", "Tranche B"), ft.dropdown.Option("Tranche_C", "Tranche C")
    ])
    int_in = ft.Dropdown(label="Intérêt", width=450, options=[
        ft.dropdown.Option("Sciences_Tech", "Sciences"), ft.dropdown.Option("Arts_Creativite", "Arts")
    ])

    res_final = ft.Text("Prêt", size=24, color=ft.Colors.LIGHT_GREEN_400)
    xai_display = ft.Column(visible=False, horizontal_alignment="center", width=380)

    async def calculer(e):
        try:
            sv = float(m_sci.value.replace(",", ".")); lv = float(m_lit.value.replace(",", "."))
            filiere, conf = moteur.predire_avec_probabilite(sv, lv, rev_in.value, int_in.value)
            res_final.value = f"CONSEIL IA : {filiere}"
            xai_display.visible = True
            
            conn = sqlite3.connect("orientation_data.db")
            conn.execute("INSERT INTO resultats (nom, moy_sci, moy_lit, revenu, interet, score_sci, score_lit, filiere) VALUES (?,?,?,?,?,?,?,?)", (nom_in.value.upper(), sv, lv, rev_in.value, int_in.value, conf, 0.0, filiere))
            conn.commit(); conn.close()
            notifier("✅ Analyse réussie", ft.Colors.GREEN); page.update()
        except Exception as ex: 
            notifier(f"❌ Erreur : {str(ex)}", ft.Colors.RED)

    async def tenter_connexion(e):
        if verifier_acces(user_log.value, pass_log.value):
            page.clean()
            page.add(
                ft.AppBar(title=ft.Text("IA ORIENTATION - DASHBOARD"), bgcolor=ft.Colors.INDIGO_900),
                ft.Column([
                    ft.Container(height=20),
                    ft.Container(bgcolor=ft.Colors.BLUE_GREY_800, padding=30, border_radius=20, content=ft.Column([
                        nom_in, ft.Row([m_sci, m_lit], alignment="center"), rev_in, int_in,
                        ft.Row([
                            ft.ElevatedButton("ANALYSER", on_click=calculer, bgcolor=ft.Colors.GREEN_700, color="white"),
                            ft.ElevatedButton("EXPORTER PDF", on_click=exporter_pdf_action, bgcolor=ft.Colors.RED_700, color="white"),
                        ], alignment="center")
                    ], horizontal_alignment="center")),
                    ft.Container(height=20), res_final, xai_display
                ], scroll=ft.ScrollMode.ALWAYS)
            )
        else: notifier("🔒 Accès refusé", ft.Colors.RED)

    user_log = ft.TextField(label="Identifiant", width=320)
    pass_log = ft.TextField(label="Mot de passe", width=320, password=True)
    page.add(ft.Container(content=ft.Column([ft.Icon(ft.Icons.LOCK, size=80), user_log, pass_log, ft.ElevatedButton("OUVRIR", on_click=tenter_connexion, width=320)], horizontal_alignment="center"), expand=True, alignment=ft.Alignment(0,0)))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="assets")