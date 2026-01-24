import flet as ft
import sqlite3
import datetime
import csv
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
    pdf.cell(0, 10, "RAPPORT D'ORIENTATION ALPHABETIQUE", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT); pdf.ln(10)
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
    page.title = "IA Orientation - Master 2026"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS 

    def notifier(m, c=ft.Colors.BLUE):
        page.overlay.append(ft.SnackBar(ft.Text(m, weight="bold"), bgcolor=c, open=True)); page.update()

    async def exporter_pdf_action(e):
        nom_fichier = generer_pdf_complet()
        if nom_fichier != "Base vide":
            # Correction de l'argument et du chemin
            page.launch_url(f"/{nom_fichier}", web_popup_window_name="_blank")
            notifier(f"📥 Export PDF : {nom_fichier}", ft.Colors.GREEN)
        else: notifier("❌ La base est vide", ft.Colors.RED)

    async def exporter_csv_action(e):
        nom_fichier = generer_csv_base()
        if nom_fichier != "Base vide":
            page.launch_url(f"/{nom_fichier}", web_popup_window_name="_blank")
            notifier(f"📥 Export CSV : {nom_fichier}", ft.Colors.GREEN)
        else: notifier("❌ La base est vide", ft.Colors.RED)

    # --- HISTORIQUE AVEC BOUTON SUPPRIMER ---
    async def voir_base(e):
        def actualiser():
            conn = sqlite3.connect("orientation_data.db")
            res = conn.execute("SELECT id, nom, filiere, score_sci FROM resultats ORDER BY nom ASC").fetchall()
            conn.close()
            tableau.rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(i))),
                    ft.DataCell(ft.Text(x[1])),
                    ft.DataCell(ft.Text(x[2], weight="bold")),
                    ft.DataCell(ft.Text(f"{round(x[3]*100, 1)}%")),
                    ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda _, r=x[0]: supprimer(r)))
                ]) for i, x in enumerate(res, start=1)
            ]
            page.update()

        def supprimer(id_r):
            conn = sqlite3.connect("orientation_data.db")
            conn.execute("DELETE FROM resultats WHERE id=?", (id_r,))
            conn.commit(); conn.close()
            actualiser()

        tableau = ft.DataTable(columns=[
            ft.DataColumn(ft.Text("N°")), ft.DataColumn(ft.Text("Nom")), 
            ft.DataColumn(ft.Text("Conseil")), ft.DataColumn(ft.Text("IA %")), 
            ft.DataColumn(ft.Text("Action"))
        ])
        actualiser()
        page.overlay.append(ft.AlertDialog(title=ft.Text("📜 Historique"), content=ft.Column([tableau], scroll="always"), open=True))
        page.update()

    async def calculer(e):
        try:
            v_sci = m_sci.value.strip().replace(",", "."); v_lit = m_lit.value.strip().replace(",", ".")
            sv, lv = float(v_sci), float(v_lit)
            if not (0 <= sv <= 20 and 0 <= lv <= 20):
                notifier("❌ Notes entre 0 et 20", ft.Colors.RED); return

            filiere, conf = moteur.predire_avec_probabilite(sv, lv, rev_in.value, int_in.value)
            res_final.value = f"CONSEIL IA : {filiere}"; conf_txt.value = f"IA Confiance : {round(conf*100, 2)}%"
            prog_conf.value = conf; prog_conf.visible = True
            
            p_notes = (sv + lv) * 2; p_social = 35 if rev_in.value != "Tranche_A" else 15; p_perso = 25
            tot = p_notes + p_social + p_perso; pn = [p_notes/tot, p_social/tot, p_perso/tot]
            
            xai_display.controls = [
                ft.Row([ft.Text("Scolaire", width=90), ft.ProgressBar(value=pn[0], color="blue", width=180), ft.Text(f"{round(pn[0]*100)}%")], alignment="center"),
                ft.Row([ft.Text("Social", width=90), ft.ProgressBar(value=pn[1], color="orange", width=180), ft.Text(f"{round(pn[1]*100)}%")], alignment="center"),
                ft.Row([ft.Text("Intérêt", width=90), ft.ProgressBar(value=pn[2], color="green", width=180), ft.Text(f"{round(pn[2]*100)}%")], alignment="center")
            ]
            xai_display.visible = True
            
            conn = sqlite3.connect("orientation_data.db")
            conn.execute("INSERT INTO resultats (nom, moy_sci, moy_lit, revenu, interet, score_sci, score_lit, filiere) VALUES (?,?,?,?,?,?,?,?)", (nom_in.value.upper(), sv, lv, rev_in.value, int_in.value, conf, 0.0, filiere))
            conn.commit(); conn.close(); notifier("✅ Analyse terminée", ft.Colors.GREEN); page.update()
        except: notifier("❌ Entrée invalide", ft.Colors.RED)

    # --- UI LAYOUT ---
    header_title = ft.Text("IA ORIENTATION SYSTEM", color=ft.Colors.LIGHT_GREEN_400, size=26, weight="bold")
    nom_in = ft.TextField(label="Nom de l'élève", width=450, border_radius=15)
    m_sci = ft.TextField(label="Moyenne Scientifique (0-20)", width=220, border_radius=15)
    m_lit = ft.TextField(label="Moyenne Littéraire (0-20)", width=220, border_radius=15)
    rev_in = ft.Dropdown(label="Revenu familial", width=450, border_radius=15, options=[ft.dropdown.Option(key="Tranche_A", text="0 - 150k"), ft.dropdown.Option(key="Tranche_B", text="150k - 450k"), ft.dropdown.Option(key="Tranche_C", text="+ 450k")])
    int_in = ft.Dropdown(label="Intérêt", width=450, border_radius=15, options=[ft.dropdown.Option(key="Sciences_Tech", text="Sciences"), ft.dropdown.Option(key="Arts_Creativite", text="Arts")])

    res_final = ft.Text("Prêt", size=24, weight="bold", color=ft.Colors.LIGHT_GREEN_400)
    conf_txt = ft.Text("", italic=True, size=18, weight="bold")
    prog_conf = ft.ProgressBar(width=400, value=0, visible=False, color=ft.Colors.LIGHT_GREEN_400)
    xai_display = ft.Column(visible=False, horizontal_alignment="center", width=380)

    main_card = ft.Container(bgcolor=ft.Colors.BLUE_GREY_800, padding=35, border_radius=25, content=ft.Column([
        nom_in, ft.Row([m_sci, m_lit], alignment="center"), rev_in, int_in, 
        ft.Row([ft.Button("ANALYSER", on_click=calculer), ft.Button("HISTO", on_click=voir_base)], alignment="center", spacing=10), 
        ft.Row([ft.TextButton("Exporter PDF", on_click=exporter_pdf_action), ft.TextButton("Exporter CSV", on_click=exporter_csv_action)], alignment="center")
    ], horizontal_alignment="center"))

    async def tenter_connexion(e):
        if verifier_acces(user_log.value, pass_log.value):
            page.clean()
            page.add(ft.Column([ft.Container(padding=25, content=header_title), main_card, ft.Column([res_final, conf_txt, prog_conf, xai_display], horizontal_alignment="center")], scroll=ft.ScrollMode.ALWAYS))
            page.update()
        else: notifier("🔒 Erreur Code", ft.Colors.RED)

    user_log = ft.TextField(label="Admin", width=320); pass_log = ft.TextField(label="Code", width=320, password=True, on_submit=tenter_connexion)
    page.add(ft.Container(content=ft.Column([ft.Icon(ft.Icons.LOCK, size=80), user_log, pass_log, ft.Button("OUVRIR", on_click=tenter_connexion, width=320)], horizontal_alignment="center"), alignment=ft.Alignment(0,0), expand=True))

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORT", 8550)), host="0.0.0.0", assets_dir="assets")