import streamlit as st
import plotly.graph_objects as go
import json
import os
import requests
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="CapAvenir CMR - Orientation Scolaire IA",
    page_icon="🎓",
    layout="wide"
)

# --- STYLE CSS GLOBAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    .main { background-color: #f8fafc; }
    .stApp { font-family: 'Poppins', sans-serif; }

    .header-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        color: white;
        padding: 2rem 3rem;
        border-radius: 0 0 30px 30px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.2rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #0f172a;
        border-left: 4px solid #10b981;
        padding-left: 0.7rem;
        margin-bottom: 1rem;
    }
    .alert-warning {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        color: #92400e;
        margin: 0.5rem 0;
    }
    .alert-success {
        background-color: #ecfdf5;
        border-left: 5px solid #10b981;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        color: #065f46;
        margin: 0.5rem 0;
    }
    .alert-danger {
        background-color: #fef2f2;
        border-left: 5px solid #ef4444;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        color: #991b1b;
        margin: 0.5rem 0;
    }
    .alert-info {
        background-color: #eff6ff;
        border-left: 5px solid #3b82f6;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        color: #1e40af;
        margin: 0.5rem 0;
    }
    .badge-c {
        background: #10b981; color: white;
        padding: 0.3rem 1rem; border-radius: 20px;
        font-weight: 700; font-size: 1.1rem;
    }
    .badge-a {
        background: #3b82f6; color: white;
        padding: 0.3rem 1rem; border-radius: 20px;
        font-weight: 700; font-size: 1.1rem;
    }
    .badge-probe {
        background: #f59e0b; color: white;
        padding: 0.3rem 1rem; border-radius: 20px;
        font-weight: 700; font-size: 1.1rem;
    }
    .step-nav {
        display: flex; justify-content: center; gap: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .chat-bubble-ia {
        background: #e0f2fe;
        border-radius: 0 14px 14px 14px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        color: #0c4a6e;
        max-width: 85%;
    }
    .chat-bubble-user {
        background: #dcfce7;
        border-radius: 14px 0 14px 14px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0 0.5rem auto;
        color: #14532d;
        max-width: 85%;
        text-align: right;
    }
    .stat-box {
        text-align: center;
        padding: 1rem;
        background: #f8fafc;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    .stat-box .val {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stat-box .lbl {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
    <div class="header-box">
        <h1 style='color:#10b981; margin:0; font-size:2rem;'>🎓 CapAvenir CMR</h1>
        <p style='color:#94a3b8; margin:0.3rem 0 0;'>Système Intelligent d'Orientation Scolaire Automatisée</p>
        <small style='color:#64748b;'>ENS Filière Informatique – Niveau 5</small>
    </div>
""", unsafe_allow_html=True)

# =====================================================================
# SESSION STATE — Initialisation de toutes les variables
# =====================================================================
defaults = {
    "step": 0,
    "nom": "", "prenom": "", "age": 15, "sexe": "Masculin",
    "lycee": "", "classe": "3ème",
    "choix_personnel": "C (Scientifique)",
    "projet_professionnel": "",
    "revenu_parents": "Moyen (50 000 – 150 000 FCFA/mois)",
    "notes_sci": {"Maths": 10.0, "Sciences Physiques": 10.0, "SVT": 10.0},
    "notes_lit": {"Français": 10.0, "Histoire-Géo": 10.0, "Anglais": 10.0},
    "scores_bruts": {"D48": 10.0, "KRX": 10.0, "MECA": 10.0, "BV11": 10.0, "PRC": 10.0},
    "chat_history": [],
    "orientation_finale": None,
    "probation": False,
    "diagnostic_done": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================================
# FONCTION DE SIMULATION IA (si pas de clé API)
# =====================================================================
def _simulate_ia_response(user_input: str, conflit_type: str, prenom: str, SA: float, moy_sci: float, choix: str) -> str:
    user_lower = user_input.lower()
    if conflit_type == "decale":
        if any(w in user_lower for w in ["avocat", "droit", "journaliste", "politique", "littérature"]):
            return f"Je comprends ton ambition, {prenom} ! C'est un beau projet. Sache tout de même que tes aptitudes logiques (D48 élevé) t'ouvrent aussi des portes en droit ou en économie après un bac C. Réfléchis bien avant de te fermer des opportunités."
        elif any(w in user_lower for w in ["médecin", "ingénieur", "informatique", "science", "maths"]):
            return f"Excellente cohérence, {prenom} ! Ton projet professionnel est parfaitement aligné avec tes aptitudes scientifiques. La série C est clairement la voie la plus directe pour y arriver."
        else:
            return f"Merci pour ta réponse, {prenom}. Tes résultats montrent un réel potentiel scientifique (SA = {SA:.1f}/20). Parles-en aussi avec tes parents et un conseiller humain avant de décider définitivement."
    elif conflit_type == "reveur":
        if any(w in user_lower for w in ["oui", "vais", "améliorer", "travailler", "effort"]):
            return f"Voilà la bonne attitude, {prenom} ! 💪 Tu as les capacités (SA = {SA:.1f}/20), il te faut maintenant les résultats. Fixons comme objectif d'atteindre au moins 12/20 en maths au 2ème trimestre."
        elif any(w in user_lower for w in ["non", "difficile", "pas", "incapable"]):
            return f"Ne te décourage pas, {prenom}. Tes aptitudes prouvent que tu en es capable intellectuellement. La difficulté est souvent une question de méthode. As-tu accès à des cours de soutien ?"
        else:
            return f"Le potentiel est là (SA = {SA:.1f}/20), mais les notes ne suivent pas encore. Qu'est-ce qui te pose le plus de difficultés en classe, {prenom} ?"
    return f"Merci pour cette information, {prenom}. Y a-t-il autre chose que tu voudrais me dire sur ton projet d'orientation ?"

# =====================================================================
# NAVIGATION PAR ÉTAPES
# =====================================================================
STEPS = [
    "📋 Profil Élève",
    "📚 Notes Scolaires",
    "🧪 Tests Psychotechniques",
    "🤖 Diagnostic IA",
    "📄 Fiche d'Orientation",
]

# Barre de progression
step = st.session_state.step
cols_nav = st.columns(len(STEPS))
for i, (col, label) in enumerate(zip(cols_nav, STEPS)):
    with col:
        if i == step:
            st.markdown(f"<div style='text-align:center; background:#10b981; color:white; border-radius:8px; padding:0.4rem 0.2rem; font-size:0.8rem; font-weight:600;'>{label}</div>", unsafe_allow_html=True)
        elif i < step:
            st.markdown(f"<div style='text-align:center; background:#d1fae5; color:#065f46; border-radius:8px; padding:0.4rem 0.2rem; font-size:0.8rem;'>✓ {label}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:center; background:#f1f5f9; color:#94a3b8; border-radius:8px; padding:0.4rem 0.2rem; font-size:0.8rem;'>{label}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# ÉTAPE 0 — PROFIL ÉLÈVE
# =====================================================================
if step == 0:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Informations Personnelles de l\'Élève</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.nom = st.text_input("Nom", value=st.session_state.nom)
        st.session_state.age = st.number_input("Âge", min_value=12, max_value=20, value=st.session_state.age)
    with col2:
        st.session_state.prenom = st.text_input("Prénom", value=st.session_state.prenom)
        st.session_state.sexe = st.selectbox("Sexe", ["Masculin", "Féminin"], index=0 if st.session_state.sexe == "Masculin" else 1)
    with col3:
        st.session_state.lycee = st.text_input("Lycée / Établissement", value=st.session_state.lycee)
        st.session_state.classe = st.selectbox("Classe actuelle", ["3ème", "3ème Avancée"])

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Projet Personnel & Contexte Familial</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.choix_personnel = st.selectbox(
            "Choix de série souhaité par l'élève",
            ["C (Scientifique)", "A (Littéraire)", "Indécis(e)"],
        )
        st.session_state.projet_professionnel = st.text_area(
            "Projet professionnel (ce que l'élève veut faire plus tard)",
            value=st.session_state.projet_professionnel,
            placeholder="Ex: Devenir médecin, ingénieur, avocat...",
            height=100,
        )
    with col2:
        st.session_state.revenu_parents = st.selectbox(
            "Revenu mensuel estimé des parents",
            [
                "Faible (< 50 000 FCFA/mois)",
                "Moyen (50 000 – 150 000 FCFA/mois)",
                "Élevé (> 150 000 FCFA/mois)",
            ],
        )
        st.markdown("""
            <div class="alert-info">
                💡 Le revenu des parents est utilisé pour évaluer l'accès aux cours de répétition
                et la faisabilité d'études longues.
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("➡️ Étape suivante : Notes Scolaires", use_container_width=True):
        if st.session_state.nom and st.session_state.prenom:
            st.session_state.step = 1
            st.rerun()
        else:
            st.error("Veuillez renseigner au minimum le nom et le prénom de l'élève.")

# =====================================================================
# ÉTAPE 1 — NOTES SCOLAIRES (Trimestre 1)
# =====================================================================
elif step == 1:
    st.markdown(f'<div class="card"><div class="section-title">Notes du 1er Trimestre — {st.session_state.prenom} {st.session_state.nom}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📐 Matières Scientifiques**")
        for matiere in st.session_state.notes_sci:
            st.session_state.notes_sci[matiere] = st.number_input(
                matiere, min_value=0.0, max_value=20.0, step=0.5,
                value=st.session_state.notes_sci[matiere], key=f"sci_{matiere}"
            )
        moy_sci = sum(st.session_state.notes_sci.values()) / len(st.session_state.notes_sci)
        st.metric("📊 Moyenne Scientifique (T1)", f"{moy_sci:.2f}/20")

    with col2:
        st.markdown("**📖 Matières Littéraires**")
        for matiere in st.session_state.notes_lit:
            st.session_state.notes_lit[matiere] = st.number_input(
                matiere, min_value=0.0, max_value=20.0, step=0.5,
                value=st.session_state.notes_lit[matiere], key=f"lit_{matiere}"
            )
        moy_lit = sum(st.session_state.notes_lit.values()) / len(st.session_state.notes_lit)
        st.metric("📊 Moyenne Littéraire (T1)", f"{moy_lit:.2f}/20")

    st.markdown('</div>', unsafe_allow_html=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.step = 0
            st.rerun()
    with col_next:
        if st.button("➡️ Étape suivante : Tests Psychotechniques", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# =====================================================================
# ÉTAPE 2 — TESTS PSYCHOTECHNIQUES
# =====================================================================
elif step == 2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Scores des Tests Psychotechniques (Notes Brutes /20)</div>', unsafe_allow_html=True)

    test_info = {
        "D48":  ("🔷 D48 — Test de Raisonnement Logique",  "Mesure la capacité à identifier des règles et progressions logiques."),
        "KRX":  ("📐 KRX — Test d'Aptitude Mathématique", "Évalue la pensée numérique, les suites et le calcul."),
        "MECA": ("⚙️ MECA — Test de Compréhension Mécanique", "Appréhension des mécanismes physiques et techniques."),
        "BV11": ("📖 BV11 — Test de Vocabulaire Littéraire", "Richesse du vocabulaire, synonymes et compréhension de texte."),
        "PRC":  ("💬 PRC — Test de Proverbes", "Compréhension du langage figuré et du raisonnement linguistique."),
    }

    col1, col2 = st.columns(2)
    tests_list = list(test_info.items())
    for i, (code, (titre, desc)) in enumerate(tests_list):
        col = col1 if i % 2 == 0 else col2
        with col:
            st.markdown(f"**{titre}**")
            st.caption(desc)
            st.session_state.scores_bruts[code] = st.slider(
                f"Score {code}", min_value=0.0, max_value=20.0, step=0.5,
                value=st.session_state.scores_bruts[code], key=f"test_{code}"
            )

    # Aperçu temps réel des aptitudes
    sb = st.session_state.scores_bruts
    sa_preview = (sb["KRX"] + sb["D48"]) / 2
    la_preview = (sb["BV11"] + sb["PRC"]) / 2
    meca_note = sb["MECA"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Aperçu temps réel :**")
    c1, c2, c3 = st.columns(3)
    c1.metric("SA (Aptitude Scientifique)", f"{sa_preview:.1f}/20", help="= (KRX + D48) / 2")
    c2.metric("LA (Aptitude Littéraire)", f"{la_preview:.1f}/20", help="= (BV11 + PRC) / 2")
    c3.metric("MECA (Complémentaire)", f"{meca_note:.1f}/20")

    st.markdown('</div>', unsafe_allow_html=True)

    # Note sur l'étalonnage
    st.markdown("""
        <div class="alert-info">
            ℹ️ <strong>Note sur l'étalonnage :</strong> Les notes brutes seront converties en notes étalonnées
            lors du diagnostic, selon les tables de conversion standard. Dans cette version, un facteur
            d'étalonnage simplifié est appliqué (×1.0 car les scores sont déjà sur /20).
        </div>
    """, unsafe_allow_html=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("➡️ Lancer le Diagnostic IA 🤖", use_container_width=True, type="primary"):
            st.session_state.step = 3
            st.session_state.chat_history = []
            st.session_state.diagnostic_done = False
            st.rerun()

# =====================================================================
# ÉTAPE 3 — DIAGNOSTIC IA
# =====================================================================
elif step == 3:
    # ----------- Calculs centraux -----------
    sb = st.session_state.scores_bruts
    SA = (sb["KRX"] + sb["D48"]) / 2
    LA = (sb["BV11"] + sb["PRC"]) / 2
    MECA = sb["MECA"]

    moy_sci = sum(st.session_state.notes_sci.values()) / len(st.session_state.notes_sci)
    moy_lit = sum(st.session_state.notes_lit.values()) / len(st.session_state.notes_lit)

    choix = st.session_state.choix_personnel
    revenu = st.session_state.revenu_parents

    # Détermination du conflit
    conflit_type = None
    if SA > LA:
        if moy_sci < 10 and "C" in choix:
            conflit_type = "reveur"       # Cas A : bonnes aptitudes, mauvaises notes, veut C
        elif "A" in choix:
            conflit_type = "decale"       # Cas B : profil sci, choisit A
    elif LA > SA:
        if moy_lit < 10 and "A" in choix:
            conflit_type = "reveur_lit"   # Cas littéraire identique

    # Recommandation initiale du moteur de règles
    def get_recommandation():
        if SA > LA and moy_sci >= 10:
            return "C", "Profil Scientifique Confirmé", "success"
        elif LA > SA and moy_lit >= 10:
            return "A", "Profil Littéraire Confirmé", "success"
        elif SA > LA and moy_sci >= 10 and "A" in choix:
            return "C", "Profil Scientifique malgré choix A", "warning"
        elif SA > LA and moy_sci < 10:
            return "C_probe", "Série C sous réserve d'amélioration", "warning"
        elif LA > SA and moy_lit < 10:
            return "A_probe", "Série A sous réserve d'amélioration", "warning"
        elif SA == LA:
            return "?", "Profil indéterminé – entretien approfondi requis", "warning"
        else:
            return "A", "Orientation par défaut", "info"

    serie, message_diag, diag_type = get_recommandation()
    st.session_state.orientation_finale = serie
    st.session_state.probation = "probe" in serie

    # ----------- AFFICHAGE -----------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Analyse du Profil</div>', unsafe_allow_html=True)

    # Métriques principales
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="stat-box"><div class="val">{SA:.1f}</div><div class="lbl">SA – Aptitude Sci.</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="stat-box"><div class="val">{LA:.1f}</div><div class="lbl">LA – Aptitude Lit.</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="stat-box"><div class="val">{moy_sci:.1f}</div><div class="lbl">Moy. Sci. Scolaire</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="stat-box"><div class="val">{moy_lit:.1f}</div><div class="lbl">Moy. Lit. Scolaire</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Graphique radar
    labels = ['Logique (D48)', 'Maths (KRX)', 'Mécanique (MECA)', 'Littéraire (BV11)', 'Proverbes (PRC)']
    aptitudes = [sb["D48"], sb["KRX"], sb["MECA"], sb["BV11"], sb["PRC"]]
    notes_ecole = [
        st.session_state.notes_sci.get("Maths", 10),
        st.session_state.notes_sci.get("Sciences Physiques", 10),
        st.session_state.notes_sci.get("SVT", 10),
        st.session_state.notes_lit.get("Français", 10),
        st.session_state.notes_lit.get("Histoire-Géo", 10),
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=aptitudes, theta=labels, fill='toself',
        name='Aptitudes (Tests Psychotechniques)', line_color='#10b981',
        fillcolor='rgba(16, 185, 129, 0.15)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=notes_ecole, theta=labels, fill='toself',
        name='Notes Scolaires (T1)', line_color='#3b82f6',
        fillcolor='rgba(59, 130, 246, 0.15)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 20]), gridshape='polygon'),
        showlegend=True, margin=dict(l=40, r=40, t=20, b=20), height=380,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------- DIAGNOSTIC PRINCIPAL -----------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🤖 Verdict du Moteur d\'Inférence</div>', unsafe_allow_html=True)

    alert_class = {"success": "alert-success", "warning": "alert-warning", "danger": "alert-danger", "info": "alert-info"}.get(diag_type, "alert-info")

    serie_display = serie.replace("_probe", "").replace("_", "")
    badge_class = "badge-c" if "C" in serie_display else ("badge-a" if "A" in serie_display else "badge-probe")

    st.markdown(f"""
        <div class="{alert_class}">
            <strong>Recommandation :</strong>
            <span class="{badge_class}" style="margin-left:0.8rem;">Série {serie_display}</span><br><br>
            {message_diag}
        </div>
    """, unsafe_allow_html=True)

    # Probation
    if st.session_state.probation:
        st.markdown("""
            <div class="alert-warning" style="margin-top:0.8rem;">
                ⚠️ <strong>Mode Probation activé :</strong> L'élève est orienté(e) sous condition
                d'améliorer ses résultats scolaires au 2ème et 3ème trimestre. Un suivi sera
                mis en place. Si aucune amélioration n'est constatée en fin d'année,
                l'orientation sera révisée.
            </div>
        """, unsafe_allow_html=True)

    # Prise en compte du revenu
    if "Faible" in revenu and "C" in serie:
        st.markdown("""
            <div class="alert-info" style="margin-top:0.8rem;">
                💰 <strong>Note sur le contexte familial :</strong> Le revenu familial étant modeste,
                il est recommandé de vérifier l'accès aux structures de soutien scolaire
                (cours de répétition, bourses) avant de confirmer l'orientation en série C.
            </div>
        """, unsafe_allow_html=True)

    # Décalage aptitudes vs notes
    if abs(SA - moy_sci) > 3:
        sens = "supérieure" if SA > moy_sci else "inférieure"
        st.markdown(f"""
            <div class="alert-warning" style="margin-top:0.8rem;">
                📉 <strong>Décalage détecté :</strong> L'aptitude scientifique ({SA:.1f}/20)
                est {sens} de {abs(SA-moy_sci):.1f} points à la moyenne scolaire ({moy_sci:.1f}/20).
                {'L\'élève est sous-performant(e) par rapport à son potentiel.' if SA > moy_sci else 'L\'élève compense par le travail un potentiel plus modeste.'}
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ----------- AGENT CONVERSATIONNEL IA -----------
    if conflit_type:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💬 Agent IA d\'Interpellation</div>', unsafe_allow_html=True)

        if conflit_type == "reveur":
            context_msg = f"Bonjour {st.session_state.prenom} ! J'ai analysé ton dossier. Tu as d'excellentes aptitudes scientifiques (SA = {SA:.1f}/20), ce qui est très encourageant ! Cependant, tes notes scolaires en matières scientifiques ({moy_sci:.1f}/20) sont en dessous de 10. Pour réussir en série C, tu devras vraiment améliorer tes résultats en classe. Qu'est-ce qui te passionne dans la science ?"
        elif conflit_type == "decale":
            context_msg = f"Bonjour {st.session_state.prenom} ! Tes tests révèlent un fort potentiel scientifique (SA = {SA:.1f}/20 vs LA = {LA:.1f}/20). Or tu as choisi la série A. Peux-tu m'expliquer pourquoi tu préfères la filière littéraire ?"
        else:
            context_msg = f"Bonjour {st.session_state.prenom} ! Parlons de ton orientation ensemble."

        # Afficher l'historique
        if not st.session_state.chat_history:
            st.session_state.chat_history.append({"role": "ia", "content": context_msg})

        for msg in st.session_state.chat_history:
            if msg["role"] == "ia":
                st.markdown(f'<div class="chat-bubble-ia">🤖 <strong>Agent CapAvenir :</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble-user">{msg["content"]} <strong>: {st.session_state.prenom}</strong></div>', unsafe_allow_html=True)

        # Champ de réponse
        user_input = st.text_input(
            "Votre réponse (ou celle de l'élève) :",
            key="chat_input",
            placeholder="Écrivez ici..."
        )

        if st.button("📨 Envoyer", use_container_width=True):
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input})

                # Appel API Anthropic (Claude) avec fallback simulation
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")

                # Construction du prompt système
                system_prompt = f"""Tu es un conseiller d'orientation scolaire IA bienveillant et expert
pour le système éducatif camerounais. Tu aides un(e) élève nommé(e) {st.session_state.prenom} {st.session_state.nom}
qui est en {st.session_state.classe} au lycée {st.session_state.lycee or 'non précisé'}.

Données de l'élève :
- Aptitude Scientifique (SA) : {SA:.1f}/20
- Aptitude Littéraire (LA) : {LA:.1f}/20
- Moyenne scolaire scientifique : {moy_sci:.1f}/20
- Moyenne scolaire littéraire : {moy_lit:.1f}/20
- Choix personnel : {choix}
- Projet professionnel : {st.session_state.projet_professionnel or 'Non précisé'}
- Type de conflit : {conflit_type}

Ton rôle : Engager une conversation naturelle et empathique pour explorer les motivations
de l'élève. Tu dois orienter vers la meilleure décision pour son avenir, en tenant compte
de son profil réel. Sois concis (2-3 phrases max). Pas de listes. Parle directement à l'élève."""

                # Historique pour l'API
                messages_api = []
                for m in st.session_state.chat_history:
                    role = "assistant" if m["role"] == "ia" else "user"
                    messages_api.append({"role": role, "content": m["content"]})

                if api_key and len(api_key) > 20:
                    try:
                        response = requests.post(
                            "https://api.anthropic.com/v1/messages",
                            headers={
                                "Content-Type": "application/json",
                                "x-api-key": api_key,
                                "anthropic-version": "2023-06-01",
                            },
                            json={
                                "model": "claude-sonnet-4-20250514",
                                "max_tokens": 300,
                                "system": system_prompt,
                                "messages": messages_api,
                            },
                            timeout=15,
                        )
                        data = response.json()
                        ia_reply = data["content"][0]["text"]
                    except Exception as e:
                        ia_reply = _simulate_ia_response(user_input, conflit_type, st.session_state.prenom, SA, moy_sci, choix)
                else:
                    ia_reply = _simulate_ia_response(user_input, conflit_type, st.session_state.prenom, SA, moy_sci, choix)

                st.session_state.chat_history.append({"role": "ia", "content": ia_reply})
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("➡️ Générer la Fiche d'Orientation 📄", use_container_width=True, type="primary"):
            st.session_state.step = 4
            st.rerun()

# =====================================================================
# ÉTAPE 4 — FICHE D'ORIENTATION
# =====================================================================
elif step == 4:
    serie = st.session_state.orientation_finale or "?"
    serie_clean = serie.replace("_probe", "").replace("_", "")
    prenom = st.session_state.prenom
    nom = st.session_state.nom
    sb = st.session_state.scores_bruts
    SA = (sb["KRX"] + sb["D48"]) / 2
    LA = (sb["BV11"] + sb["PRC"]) / 2
    moy_sci = sum(st.session_state.notes_sci.values()) / len(st.session_state.notes_sci)
    moy_lit = sum(st.session_state.notes_lit.values()) / len(st.session_state.notes_lit)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"""
        <div style="text-align:center; padding:1rem 0;">
            <div style="font-size:0.85rem; color:#64748b; text-transform:uppercase; letter-spacing:0.1em;">République du Cameroun</div>
            <div style="font-size:0.8rem; color:#64748b;">Ministère de l'Éducation de Base</div>
            <hr style="margin:0.8rem 0;">
            <div style="font-size:1.5rem; font-weight:700; color:#0f172a;">FICHE D'ORIENTATION SCOLAIRE</div>
            <div style="font-size:0.9rem; color:#64748b;">Générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <b>Nom & Prénom :</b> {nom} {prenom}<br>
            <b>Âge :</b> {st.session_state.age} ans &nbsp;|&nbsp; <b>Sexe :</b> {st.session_state.sexe}<br>
            <b>Classe :</b> {st.session_state.classe}<br>
            <b>Lycée :</b> {st.session_state.lycee or '—'}
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <b>Choix personnel :</b> {st.session_state.choix_personnel}<br>
            <b>Projet professionnel :</b> {st.session_state.projet_professionnel or '—'}<br>
            <b>Revenu familial :</b> {st.session_state.revenu_parents}
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tableau des scores
    st.markdown("**📊 Résultats des Tests Psychotechniques**")
    t_col = st.columns(5)
    for i, (code, nom_test) in enumerate([("D48","Logique"), ("KRX","Maths"), ("MECA","Mécanique"), ("BV11","Littéraire"), ("PRC","Proverbes")]):
        with t_col[i]:
            st.markdown(f'<div class="stat-box"><div class="val" style="font-size:1.4rem;">{sb[code]:.1f}</div><div class="lbl">{code}<br>{nom_test}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("SA", f"{SA:.1f}/20")
    a2.metric("LA", f"{LA:.1f}/20")
    a3.metric("Moy. Sci.", f"{moy_sci:.1f}/20")
    a4.metric("Moy. Lit.", f"{moy_lit:.1f}/20")

    st.markdown("<br>", unsafe_allow_html=True)
    badge_class = "badge-c" if "C" in serie_clean else ("badge-a" if "A" in serie_clean else "badge-probe")
    color = "#10b981" if "C" in serie_clean else "#3b82f6"

    st.markdown(f"""
        <div style="text-align:center; padding:1.5rem; background:{'#ecfdf5' if 'C' in serie_clean else '#eff6ff'};
             border-radius:12px; border: 2px solid {color};">
            <div style="font-size:0.9rem; color:#64748b; margin-bottom:0.5rem;">ORIENTATION RECOMMANDÉE</div>
            <span class="{badge_class}" style="font-size:1.5rem; padding:0.5rem 2rem;">SÉRIE {serie_clean}</span>
            {'<div style="margin-top:0.8rem; color:#92400e; font-size:0.85rem;"><strong>⚠️ Sous réserve</strong> — Amélioration des résultats requise d\'ici fin d\'année.</div>' if st.session_state.probation else ''}
        </div>
    """, unsafe_allow_html=True)

    # Entretien IA résumé
    if st.session_state.chat_history:
        st.markdown("<br><b>💬 Synthèse de l'entretien IA :</b>", unsafe_allow_html=True)
        last_ia = [m["content"] for m in st.session_state.chat_history if m["role"] == "ia"]
        if last_ia:
            st.info(f"Dernier message de l'agent : {last_ia[-1]}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Boutons d'action
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Retour au Diagnostic", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with col2:
        # Génération du contenu texte de la fiche
        fiche_txt = f"""FICHE D'ORIENTATION SCOLAIRE — CapAvenir CMR
Générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}

ÉLÈVE : {nom} {prenom} | Âge : {st.session_state.age} ans | {st.session_state.sexe}
Lycée : {st.session_state.lycee or '—'} | Classe : {st.session_state.classe}
Choix personnel : {st.session_state.choix_personnel}
Projet professionnel : {st.session_state.projet_professionnel or '—'}

RÉSULTATS DES TESTS :
D48={sb['D48']:.1f} | KRX={sb['KRX']:.1f} | MECA={sb['MECA']:.1f} | BV11={sb['BV11']:.1f} | PRC={sb['PRC']:.1f}

SA (Aptitude Scientifique) = {SA:.2f}/20
LA (Aptitude Littéraire)   = {LA:.2f}/20
Moyenne Scientifique (T1)  = {moy_sci:.2f}/20
Moyenne Littéraire (T1)    = {moy_lit:.2f}/20

ORIENTATION : SÉRIE {serie_clean}
{'STATUT : PROBATION – Amélioration requise' if st.session_state.probation else 'STATUT : CONFIRMÉ'}
"""
        st.download_button(
            "📥 Télécharger la Fiche (.txt)",
            fiche_txt,
            file_name=f"orientation_{nom}_{prenom}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col3:
        if st.button("🔄 Nouveau Dossier", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("<br><hr><center><small>CapAvenir CMR © 2025 — Mémoire ENS Filière Informatique Niveau 5</small></center>", unsafe_allow_html=True)