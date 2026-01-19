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

# --- 2. EXPORTATIONS ---
def generer_csv_base():
    conn = sqlite3.connect("orientation_data.db"); cursor = conn.cursor()
    cursor.execute("SELECT nom, moy_sci, moy_lit, revenu, interet, score_sci, filiere, date FROM resultats ORDER BY nom ASC")
    donnees = cursor.fetchall(); conn.close()
    if not donnees: return "Base vide"
    
    nom_f = f"Export_{datetime.datetime.now().strftime('%M%S')}.csv"
    chemin = os.path.join("assets", nom_f)
    with open(chemin, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["ID", "Nom", "Moy Sci", "Moy Lit", "Revenu", "Interêt", "IA Confiance", "Filière", "Date"])
        for index, r in enumerate(donnees, start=1):
            ligne = [index] + list(r)
            ligne[6] = f"{round(ligne[6] * 100, 1)}%" 
            writer.writerow(ligne)
    return nom_f

def generer_pdf_complet():
    nom_f = f"Rapport_{datetime.datetime.now().strftime('%M%S')}.pdf"
    chemin = os.path.join("assets", nom_f)
    conn = sqlite3.connect("orientation_data.db"); cursor = conn.cursor()
    cursor.execute("SELECT nom, moy_sci, moy_lit, filiere, score_sci FROM resultats ORDER BY nom ASC")
    donnees = cursor.fetchall(); conn.close()
    if not donnees: return "Base vide"
    
    pdf = FPDF(); pdf.add_page(); pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "RAPPORT D'ORIENTATION", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(10)
    pdf.set_font("helvetica", "B", 10); pdf.set_fill_color(200, 220, 255)
    pdf.cell(10, 8, "N°", border=1, fill=True); pdf.cell(50, 8, "Nom", border=1, fill=True); pdf.cell(15, 8, "Sci", border=1, fill=True); pdf.cell(15, 8, "Lit", border=1, fill=True); pdf.cell(60, 8, "IA Conseil", border=1, fill=True); pdf.cell(20, 8, "Conf.", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", "", 9)
    for i, r in enumerate(donnees, start=1):
        pdf.cell(10, 8, str(i), border=1); pdf.cell(50, 8, str(r[0]), border=1); pdf.cell(15, 8, str(r[1]), border=1); pdf.cell(15, 8, str(r[2]), border=1); pdf.cell(60, 8, str(r[3]), border=1); pdf.cell(20, 8, f"{round(r[4]*100, 1)}%", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(chemin)
    return nom_f

# --- 3. INTERFACE PRINCIPALE ---
async def main(page: ft.Page):
    if not os.path.exists("assets"): os.makedirs("assets")
    init_db(); moteur = MoteurOrientation(); moteur.entrainer_automatique()
    page.title = "IA Orientation"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS 

    def notifier(m, c=ft.Colors.BLUE):
        page.overlay.append(ft.SnackBar(ft.Text(m, weight="bold"), bgcolor=c, open=True)); page.update()

    async def exporter_pdf_action(e):
        nom_fichier = generer_pdf_complet()
        if nom_fichier != "Base vide":
            # Correction : Ouvrir dans un nouvel onglet pour ne pas déconnecter
            page.launch_url(f"/{nom_fichier}", web_window_name="_blank")
            notifier("📥 PDF généré dans un nouvel onglet", ft.Colors.GREEN)
        else: notifier("❌ Base vide", ft.Colors.RED)

    async def exporter_csv_action(e):
        nom_fichier = generer_csv_base()
        if nom_fichier != "Base vide":
            page.launch_url(f"/{nom_fichier}", web_window_name="_blank")
            notifier("📥 CSV généré dans un nouvel onglet", ft.Colors.GREEN)
        else: notifier("❌ Base vide", ft.Colors.RED)

    # --- COMPOSANTS UI ---
    nom_in = ft.TextField(label="Nom de l'élève", width=450)
    # Correction : Accepte les chiffres, points et virgules
    m_sci = ft.TextField(label="Moyenne Scientifique (0-20)", width=220, hint_text="Ex: 15.5")
    m_lit = ft.TextField(label="Moyenne Littéraire (0-20)", width=220, hint_text="Ex: 12,0")
    
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
            # Correction : Conversion robuste pour décimaux et virgules
            sv = float(m_sci.value.strip().replace(",", "."))
            lv = float(m_lit.value.strip().replace(",", "."))
            
            # Correction : Validation 0-20
            if not (0 <= sv <= 20 and 0 <= lv <= 20):
                notifier("❌ Les notes doivent être entre 0 et 20", ft.Colors.ORANGE)
                return

            filiere, conf = moteur.predire_avec_probabilite(sv, lv, rev_in.value, int_in.value)
            res_final.value = f"CONSEIL IA : {filiere}"
            xai_display.visible = True
            
            conn = sqlite3.connect("orientation_data.db")
            conn.execute("INSERT INTO resultats (nom, moy_sci, moy_lit, revenu, interet, score_sci, score_lit, filiere) VALUES (?,?,?,?,?,?,?,?)", (nom_in.value.upper(), sv, lv, rev_in.value, int_in.value, conf, 0.0, filiere))
            conn.commit(); conn.close()
            notifier("✅ Analyse terminée", ft.Colors.GREEN); page.update()
        except ValueError:
            notifier("❌ Veuillez entrer des nombres valides (ex: 14.5)", ft.Colors.RED)

    async def tenter_connexion(e):
        if verifier_acces(user_log.value, pass_log.value):
            page.clean()
            page.add(
                ft.AppBar(title=ft.Text("DASHBOARD"), bgcolor=ft.Colors.INDIGO_900),
                ft.Column([
                    ft.Container(height=20),
                    ft.Container(bgcolor=ft.Colors.BLUE_GREY_800, padding=30, border_radius=20, content=ft.Column([
                        nom_in, ft.Row([m_sci, m_lit], alignment="center"), rev_in, int_in,
                        ft.Row([
                            ft.ElevatedButton("ANALYSER", on_click=calculer, bgcolor=ft.Colors.INDIGO_500, color="white"),
                            ft.ElevatedButton("PDF", on_click=exporter_pdf_action, bgcolor=ft.Colors.RED_700, color="white"),
                            ft.ElevatedButton("CSV", on_click=exporter_csv_action, bgcolor=ft.Colors.GREEN_700, color="white"),
                        ], alignment="center")
                    ], horizontal_alignment="center")),
                    ft.Container(height=20), res_final, xai_display
                ], scroll=ft.ScrollMode.ALWAYS)
            )
            page.update()
        else: notifier("🔒 Erreur", ft.Colors.RED)

    user_log = ft.TextField(label="Admin", width=320)
    pass_log = ft.TextField(label="Code", width=320, password=True, on_submit=tenter_connexion)
    page.add(ft.Container(content=ft.Column([ft.Icon(ft.Icons.LOCK, size=80), user_log, pass_log, ft.ElevatedButton("OUVRIR", on_click=tenter_connexion, width=320)], horizontal_alignment="center"), expand=True, alignment=ft.Alignment(0,0)))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="assets")