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

# --- 2. EXPORTATIONS (TRI ALPHA & RÉ-INDEXATION) ---
def generer_csv_base():
    conn = sqlite3.connect("orientation_data.db"); cursor = conn.cursor()
    cursor.execute("SELECT nom, moy_sci, moy_lit, revenu, interet, score_sci, filiere, date FROM resultats ORDER BY nom ASC")
    donnees = cursor.fetchall(); conn.close()
    if not donnees: return "Base vide"
    export_final = []
    for index, r in enumerate(donnees, start=1):
        ligne = [index] + list(r)
        ligne[6] = f"{round(ligne[6] * 100, 1)}%" 
        export_final.append(ligne)
    nom_f = f"Export_Alpha_Master_{datetime.datetime.now().strftime('%M%S')}.csv"
    with open(nom_f, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["ID", "Nom", "Moy Sci", "Moy Lit", "Revenu", "Interêt", "IA Confiance", "Filière", "Date"])
        writer.writerows(export_final)
    return nom_f

def generer_pdf_complet():
    nom_f = f"Rapport_Alpha_{datetime.datetime.now().strftime('%M%S')}.pdf"
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
    pdf.output(nom_f); return nom_f

# --- 3. INTERFACE PRINCIPALE ---
async def main(page: ft.Page):
    init_db(); moteur = MoteurOrientation(); moteur.entrainer_automatique()
    page.title = "IA Orientation - Master 2026"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS 

    def notifier(m, c=ft.Colors.BLUE):
        page.overlay.append(ft.SnackBar(ft.Text(m, weight="bold"), bgcolor=c, open=True)); page.update()

    # --- COMPOSANTS UI DU DASHBOARD ---
    header_title = ft.Text("IA ORIENTATION SYSTEM", color=ft.Colors.LIGHT_GREEN_400, size=26, weight="bold")
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

    # --- LOGIQUE DU DASHBOARD ---
    async def changer_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        is_dark = page.theme_mode == ft.ThemeMode.DARK
        page.bgcolor = ft.Colors.BLUE_GREY_900 if is_dark else ft.Colors.BLUE_GREY_50
        main_card.bgcolor = ft.Colors.BLUE_GREY_800 if is_dark else ft.Colors.WHITE
        res_container.bgcolor = ft.Colors.BLUE_GREY_800 if is_dark else ft.Colors.WHITE
        t_col = ft.Colors.WHITE if is_dark else ft.Colors.BLACK
        nom_in.color = t_col; m_sci.color = t_col; m_lit.color = t_col
        header_container.gradient = ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=[ft.Colors.INDIGO_900, ft.Colors.GREEN_900] if is_dark else [ft.Colors.INDIGO_400, ft.Colors.GREEN_400])
        page.update()

    async def calculer(e):
        try:
            sv = float(m_sci.value.strip().replace(",", ".")); lv = float(m_lit.value.strip().replace(",", "."))
            filiere, conf = moteur.predire_avec_probabilite(sv, lv, rev_in.value, int_in.value)
            res_final.value = f"CONSEIL IA : {filiere}"; conf_txt.value = f"Confiance IA : {round(conf*100, 2)}%"
            prog_conf.value = conf; prog_conf.visible = True
            
            # CALCUL POIDS XAI (3 PARAMETRES)
            p_notes = (sv + lv) * 2
            p_social = 35 if rev_in.value != "Tranche_A" else 15
            p_perso = 25
            tot = p_notes + p_social + p_perso
            pn = [p_notes/tot, p_social/tot, p_perso/tot]
            
            xai_display.controls = [
                ft.Row([ft.Text("Scolaire", width=90), ft.ProgressBar(value=pn[0], color="blue", width=180), ft.Text(f"{round(pn[0]*100)}%")], alignment="center"),
                ft.Row([ft.Text("Social", width=90), ft.ProgressBar(value=pn[1], color="orange", width=180), ft.Text(f"{round(pn[1]*100)}%")], alignment="center"),
                ft.Row([ft.Text("Intérêt", width=90), ft.ProgressBar(value=pn[2], color="green", width=180), ft.Text(f"{round(pn[2]*100)}%")], alignment="center")
            ]
            xai_display.visible = True
            
            conn = sqlite3.connect("orientation_data.db"); conn.execute("INSERT INTO resultats (nom, moy_sci, moy_lit, revenu, interet, score_sci, score_lit, filiere) VALUES (?,?,?,?,?,?,?,?)", (nom_in.value.upper(), sv, lv, rev_in.value, int_in.value, conf, 0.0, filiere)); conn.commit(); conn.close()
            notifier("✅ Analyse terminée", "green"); page.update()
        except: notifier("❌ Entrez des nombres valides", "red")

    async def ouvrir_stats(e):
        conn = sqlite3.connect("orientation_data.db")
        stats = conn.execute("SELECT filiere, COUNT(*) FROM resultats GROUP BY filiere").fetchall(); conn.close()
        tab = ft.DataTable(columns=[ft.DataColumn(ft.Text("Filière")), ft.DataColumn(ft.Text("Total"))], rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(s[0])), ft.DataCell(ft.Text(str(s[1])))]) for s in stats])
        page.overlay.append(ft.AlertDialog(title=ft.Text("📊 Statistiques Générales"), content=tab, open=True)); page.update()

    async def voir_base(e):
        def actualiser():
            conn = sqlite3.connect("orientation_data.db"); res = conn.execute("SELECT id, nom, filiere, score_sci FROM resultats ORDER BY nom ASC").fetchall(); conn.close()
            tableau.rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(i))), ft.DataCell(ft.Text(x[1])), ft.DataCell(ft.Text(x[2], weight="bold")), ft.DataCell(ft.Text(f"{round(x[3]*100, 1)}%")), ft.DataCell(ft.Row([ft.IconButton(ft.Icons.EDIT, icon_color="blue", on_click=lambda _, r=x[0], n=x[1]: ouvrir_modif(r, n)), ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda _, r=x[0]: supprimer(r))]))]) for i, x in enumerate(res, start=1)]; page.update()
        def supprimer(id_r):
            conn = sqlite3.connect("orientation_data.db"); conn.execute("DELETE FROM resultats WHERE id=?", (id_r,)); conn.commit(); conn.close(); actualiser()
        def ouvrir_modif(id_r, n_anc):
            def sauver(e):
                conn = sqlite3.connect("orientation_data.db"); conn.execute("UPDATE resultats SET nom=? WHERE id=?", (ed_txt.value.upper(), id_r)); conn.commit(); conn.close(); d_edit.open = False; actualiser(); notifier("✅ Mis à jour")
            ed_txt = ft.TextField(label="Nouveau Nom", value=n_anc); d_edit = ft.AlertDialog(title=ft.Text("Modifier"), content=ed_txt, actions=[ft.TextButton("Sauver", on_click=sauver)])
            page.overlay.append(d_edit); d_edit.open = True; page.update()
        tableau = ft.DataTable(columns=[ft.DataColumn(ft.Text("N°")), ft.DataColumn(ft.Text("Nom")), ft.DataColumn(ft.Text("Conseil")), ft.DataColumn(ft.Text("IA %")), ft.DataColumn(ft.Text("Action"))])
        actualiser(); page.overlay.append(ft.AlertDialog(title=ft.Text("📜 Historique A-Z"), content=ft.Column([tableau], scroll="always"), open=True)); page.update()

    def importer_texte(e):
        def valider(e):
            try:
                f = io.StringIO(zone.value.strip()); lecteur = csv.reader(f, delimiter=';'); conn = sqlite3.connect("orientation_data.db")
                for r in lecteur:
                    if len(r) >= 9: conn.execute("INSERT INTO resultats (nom, moy_sci, moy_lit, revenu, interet, score_sci, score_lit, filiere) VALUES (?,?,?,?,?,?,?,?)", (r[1], float(r[2]), float(r[3]), r[4], r[5], float(r[6]), float(r[7]), r[8]))
                conn.commit(); conn.close(); d_imp.open = False; notifier("✅ Importation réussie"); page.update()
            except: notifier("❌ Erreur format", "red")
        zone = ft.TextField(label="Collez le texte CSV ici", multiline=True, min_lines=5); d_imp = ft.AlertDialog(title=ft.Text("Importer des données"), content=zone, actions=[ft.TextButton("Valider", on_click=valider)])
        page.overlay.append(d_imp); d_imp.open = True; page.update()

    # --- ASSEMBLAGE DES CARTES ---
    header_container = ft.Container(gradient=ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=[ft.Colors.INDIGO_900, ft.Colors.GREEN_900]), padding=25, border_radius=ft.BorderRadius.only(bottom_left=40, bottom_right=40), content=ft.Row([header_title, ft.IconButton(ft.Icons.LIGHT_MODE, on_click=changer_theme)], alignment="center"))
    
    main_card = ft.Container(bgcolor=ft.Colors.BLUE_GREY_800, padding=35, border_radius=25, content=ft.Column([
        nom_in, ft.Row([m_sci, m_lit], alignment="center"), rev_in, int_in, 
        ft.Row([
            ft.Button("ANALYSER", on_click=calculer, bgcolor=ft.Colors.INDIGO_500, color="white"), 
            ft.Button("STATS", on_click=ouvrir_stats, bgcolor=ft.Colors.AMBER_700, color="white"), 
            ft.Button("HISTO", on_click=voir_base, bgcolor=ft.Colors.BLUE_GREY_400, color="white"), 
            ft.Button("IMPORTER", on_click=importer_texte, bgcolor=ft.Colors.GREEN_600, color="white")
        ], alignment="center", spacing=10), 
        ft.Row([ft.TextButton("Exporter PDF", on_click=lambda _: notifier(f"Export : {generer_pdf_complet()}")), ft.TextButton("Exporter CSV", on_click=lambda _: notifier(f"Export : {generer_csv_base()}"))], alignment="center")
    ], horizontal_alignment="center"))
    
    res_container = ft.Container(bgcolor=ft.Colors.BLUE_GREY_800, padding=25, border_radius=25, content=ft.Column([ft.Text("📊 POIDS DÉCISIONNEL", weight="bold", size=14), xai_display], horizontal_alignment="center", spacing=15))

    # --- LOGIQUE DE CONNEXION ---
    async def tenter_connexion(e):
        if verifier_acces(user_log.value, pass_log.value):
            page.clean()
            page.add(ft.Column([header_container, ft.Container(height=20), main_card, ft.Container(height=20), ft.Row([ft.Column([res_final, conf_txt, prog_conf], horizontal_alignment="center", width=550, spacing=15), res_container], alignment="center", spacing=40)], scroll=ft.ScrollMode.ALWAYS, expand=True))
        else: notifier("🔒 Erreur d'accès", "red")
        page.update()

    user_log = ft.TextField(label="Admin", width=320, on_submit=lambda _: pass_log.focus())
    pass_log = ft.TextField(label="Code", width=320, password=True, on_submit=tenter_connexion)

    page.add(ft.Container(content=ft.Column([ft.Icon(ft.Icons.LOCK, size=80, color=ft.Colors.LIGHT_GREEN_400), ft.Text("CONNEXION", size=24, weight="bold"), user_log, pass_log, ft.Button("OUVRIR", on_click=tenter_connexion, width=320)], horizontal_alignment="center"), alignment=ft.Alignment(0,0), expand=True))

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)