import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from fpdf import FPDF
from datetime import datetime, date

# --- CONFIGURATION ---
st.set_page_config(page_title="CapAvenir CMR - Version Finale Pro", layout="centered")

# --- FONCTION GÉNÉRATION PDF (VERSION COMPLÈTE) ---
def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête Institutionnel
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RAPPORT OFFICIEL D'ORIENTATION SCOLAIRE", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "CapAvenir CMR - Systeme Expert d'Aide a la Decision", ln=True, align="C")
    pdf.ln(10)

    # Section 1 : État Civil Complet
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 1. IDENTIFICATION DE L'ELEVE", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    info_fields = [
        ("Nom Complet", data['nom']),
        ("Date de Naissance", data['dob']),
        ("Sexe", data['genre']),
        ("Classe / Serie", f"{data['classe']} ({data['serie']})"),
        ("Etablissement", data['etablissement']),
        ("Revenu des Parents", data['revenu']),
        ("Projet Professionnel", data['projet'])
    ]
    for label, val in info_fields:
        pdf.cell(50, 8, f"{label} :", border=0)
        pdf.cell(0, 8, f"{val}", ln=True)
    
    pdf.ln(5)

    # Section 2 : Détails des Scores
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, " 2. DETAILS DES SCORES ET APTITUDES", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    
    # Tableau des rubriques
    pdf.cell(90, 8, f"Logique (D48) : {data['d48']}/20", border=1)
    pdf.cell(90, 8, f"Maths (KRX) : {data['krx']}/20", border=1, ln=True)
    pdf.cell(90, 8, f"Mecanique (MECA) : {data['meca']}/20", border=1)
    pdf.cell(90, 8, f"Litteraire (BV11) : {data['bv11']}/20", border=1, ln=True)
    pdf.cell(90, 8, f"Proverbes (PRC) : {data['prc']}/20", border=1, ln=True)
    
    pdf.set_font("Arial", "B", 11)
    pdf.ln(2)
    pdf.cell(90, 10, f"Moyenne Scientifique (SA) : {data['sa']}/20", border=0)
    pdf.cell(90, 10, f"Moyenne Litteraire (LA) : {data['la']}/20", border=0, ln=True)

    pdf.ln(5)

    # Section 3 : Verdict Final
    pdf.set_fill_color(16, 185, 129) if not data['conflit'] else pdf.set_fill_color(225, 29, 72)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 12, f" VERDICT : {data['verdict']}", ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.ln(2)
    clean_diag = data['diag'].replace('é', 'e').replace('è', 'e').replace('à', 'a').replace('’', "'")
    pdf.multi_cell(0, 8, f"Analyse de l'expert : {clean_diag}")

    return bytes(pdf.output())

# --- THEME & STYLE ---
st.sidebar.title("🎨 Personnalisation")
theme = st.sidebar.radio("Mode d'affichage :", ["Clair (Institutionnel)", "Sombre (Moderne)"])

if theme == "Clair (Institutionnel)":
    bg, card, txt, sub = "#e0f2fe", "#ffffff", "#0f172a", "#64748b"
    chart_txt = "#0f172a"
else:
    bg, card, txt, sub = "#0f172a", "#1e293b", "#f8fafc", "#94a3b8"
    chart_txt = "#f8fafc"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    [data-testid="stAppViewContainer"] {{ background-color: {bg}; }}
    .stApp {{ font-family: 'Poppins', sans-serif; color: {txt}; }}
    
    /* Correction visibilité textes/labels */
    label, .stMarkdown, p, h1, h2, h3, span {{ color: {txt} !important; }}
    .stTabs [data-baseweb="tab"] p {{ color: {txt} !important; }}

    .stCard {{ background: {card}; padding: 25px; border-radius: 25px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); margin-bottom: 20px; }}
    
    /* Embellissement des boutons d'exportation */
    .stDownloadButton button {{
        width: 100%;
        border-radius: 15px;
        height: 3.5rem;
        font-weight: 700;
        text-transform: uppercase;
        transition: all 0.3s ease;
        border: none;
    }}
    /* Bouton PDF (Emerald) */
    div.stDownloadButton:nth-child(1) button {{
        background-color: #10b981;
        color: white !important;
    }}
    /* Bouton CSV (Blue) */
    div.stDownloadButton:nth-child(2) button {{
        background-color: #3b82f6;
        color: white !important;
    }}
    .stDownloadButton button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        opacity: 0.9;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- APPLICATION ---
st.markdown(f'<div style="background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color:white; padding:2rem; border-radius:0 0 40px 40px; text-align:center; margin:-60px -20px 20px -20px;"><h1>CapAvenir CMR</h1><p>Intelligence Artificielle d\'Orientation Lycéenne</p></div>', unsafe_allow_html=True)

t_saisie, t_analyse = st.tabs(["📝 Dossier de l'élève", "📊 Analyse & Verdict"])

with t_saisie:
    st.markdown('<div class="stCard">### 👤 Identification de l\'élève', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    nom = c1.text_input("Nom(s) et Prénom(s)", "Wamba Jordan")
    dob = c2.date_input("Date de naissance", value=date(2010, 1, 1))
    genre = c1.selectbox("Sexe", ["Masculin", "Féminin"])
    etablissement = c2.text_input("Etablissement scolaire", "Lycée de Yaoundé")
    classe_opt = c1.selectbox("Classe", ["3ème", "Autres"])
    serie_opt = c2.selectbox("Option / Série", ["Allemand", "Espagnol", "Chinois", "Italien", "Bilingue"]) if classe_opt == "3ème" else c2.text_input("Précisez")
    revenu = c1.selectbox("Revenu des parents", ["Faible", "Moyen", "Élevé"])
    projet = c2.text_input("Métier envisagé", "Ingénieur logiciel")
    choix_perso = st.radio("Série souhaitée en Seconde :", ["Série C", "Série A"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="stCard">### 🏫 Performances & Tests Psychotechniques', unsafe_allow_html=True)
    n1, n2 = st.columns(2)
    m_sci, m_lit = n1.number_input("Moyenne Scientifique Classe", 0.0, 20.0, 11.5), n2.number_input("Moyenne Littéraire Classe", 0.0, 20.0, 13.0)
    st.divider()
    t1, t2, t3 = st.columns(3)
    d48, krx, meca = t1.number_input("Logique (D48)", 0, 20, 16), t2.number_input("Maths (KRX)", 0, 20, 17), t3.number_input("Méca (MECA)", 0, 20, 14)
    bv11, prc = st.columns(2)[0].number_input("Littéraire (BV11)", 0, 20, 12), st.columns(2)[1].number_input("Proverbes (PRC)", 0, 20, 11)
    st.markdown('</div>', unsafe_allow_html=True)

with t_analyse:
    sa, la = (krx + d48) / 2, (bv11 + prc) / 2
    verdict, is_conflit, diag_txt = "", False, ""

    if sa > la:
        if choix_perso == "Série C":
            verdict, diag_txt = "SÉRIE C (SCIENTIFIQUE)", "Parfaite adéquation entre les aptitudes et le projet."
        else:
            verdict, is_conflit = "SÉRIE C (DISCORDE)", True
            diag_txt = f"Alerte : Profil scientifique ({sa}/20) mais l'élève demande la Série A. Interpellation nécessaire."
    else:
        if choix_perso == "Série A":
            verdict, diag_txt = "SÉRIE A (LITTÉRAIRE)", "Le profil littéraire est confirmé par les tests et le choix de l'élève."
        else:
            verdict, is_conflit = "SÉRIE A (DISCORDE)", True
            diag_txt = f"Alerte : Potentiel littéraire ({la}/20) mais l'élève force la Série C. Risque d'échec élevé."

    # Affichage Verdict
    v_color = "#10b981" if not is_conflit else "#e11d48"
    st.markdown(f"""
        <div style="background:{v_color}; color:white; padding:20px; border-radius:20px; text-align:center;">
            <small>DECISION DU SYSTEME EXPERT</small>
            <h1 style="color:white !important; margin:0;">{verdict}</h1>
            <p style="color:white !important; font-weight:600;">{"⚠️ ACTION CONSEILLER REQUISE" if is_conflit else "✅ DOSSIER COHÉRENT"}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="stCard">### Analyse détaillée<br>{diag_txt}</div>', unsafe_allow_html=True)

    # Radar Chart
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[d48, krx, meca, bv11, prc], theta=['D48','KRX','MECA','BV11','PRC'], fill='toself', name='Aptitudes', line_color='#10b981'))
    fig.add_trace(go.Scatterpolar(r=[m_sci, m_sci, 10, m_lit, m_lit], theta=['D48','KRX','MECA','BV11','PRC'], fill='toself', name='École', line_color='#3b82f6'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 20]), gridshape='linear'), paper_bgcolor='rgba(0,0,0,0)', font_color=chart_txt, height=350)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Exports Embellis
    st.markdown("### 📥 Finalisation du dossier")
    c_exp1, c_exp2 = st.columns(2)
    
    # PDF
    pdf_b = generate_pdf({'nom':nom, 'dob':dob.strftime('%d/%m/%Y'), 'genre':genre, 'classe':classe_opt, 'serie':serie_opt, 'etablissement':etablissement, 'revenu':revenu, 'projet':projet, 'd48':d48, 'krx':krx, 'meca':meca, 'bv11':bv11, 'prc':prc, 'sa':sa, 'la':la, 'verdict':verdict, 'diag':diag_txt, 'conflit':is_conflit})
    c_exp1.download_button("📄 Exporter en PDF", pdf_b, f"Rapport_{nom}.pdf", "application/pdf")
    
    # CSV
    df = pd.DataFrame([{'Nom':nom, 'Verdict':verdict, 'SA':sa, 'LA':la, 'Discorde':is_conflit}])
    c_exp2.download_button("📊 Exporter en Excel (CSV)", df.to_csv(index=False).encode('utf-8-sig'), f"Data_{nom}.csv", "text/csv")

st.markdown(f'<p style="text-align:center; color:{sub}; font-size:0.7rem; margin-top:50px;">CapAvenir CMR | ENS 2026 | Application Intelligente d\'Orientation</p>', unsafe_allow_html=True)