import streamlit as st
import plotly.graph_objects as go

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="CapAvenir CMR - Analyse IA", layout="centered")

# --- STYLE CSS PERSONNALISÉ (Pour garder l'esthétique "Clean UI") ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stApp { font-family: 'Poppins', sans-serif; }
    .header-box {
        background-color: #0f172a;
        color: white;
        padding: 2rem;
        border-radius: 0 0 30px 30px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #f1f5f9;
        margin-bottom: 1rem;
    }
    .diagnostic-alert {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 1rem;
        border-radius: 10px;
        color: #92400e;
    }
    .diagnostic-success {
        background-color: #ecfdf5;
        border-left: 5px solid #10b981;
        padding: 1rem;
        border-radius: 10px;
        color: #065f46;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
    <div class="header-box">
        <h1 style='color: #10b981;'>CapAvenir CMR</h1>
        <p style='color: #94a3b8;'>Analyse de l'Orientation Intelligente</p>
    </div>
    """, unsafe_allow_html=True)

# --- SIMULATION DES DONNÉES (À remplacer par ta base de données Supabase plus tard) ---
labels = ['Logique (D48)', 'Maths (KRX)', 'Mécanique (MECA)', 'Littéraire (BV11)', 'Proverbes (PRC)']

# Notes des tests (Aptitudes)
aptitudes = [16, 17, 14, 12, 11] 
# Notes de classe (Trimestre 1)
notes_ecole = [12, 11, 10, 13, 14]

# --- CALCULS DES SCORES (Formules de ton mémoire) ---
# $SA = (KRX + D48) / 2$
# $LA = (BV11 + PRC) / 2$
sa = (aptitudes[1] + aptitudes[0]) / 2
la = (aptitudes[3] + aptitudes[4]) / 2

# --- GÉNÉRATION DU GRAPHIQUE RADAR AVEC PLOTLY ---
fig = go.Figure()

fig.add_trace(go.Scatterpolar(
    r=aptitudes,
    theta=labels,
    fill='toself',
    name='Aptitudes (Tests)',
    line_color='#10b981'
))

fig.add_trace(go.Scatterpolar(
    r=notes_ecole,
    theta=labels,
    fill='toself',
    name='Notes École',
    line_color='#3b82f6'
))

fig.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 20]),
        gridshape='polygon'
    ),
    showlegend=True,
    margin=dict(l=40, r=40, t=20, b=20),
    height=400
)

# Affichage du graphique dans une carte
st.markdown('<div class="card">', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- DIAGNOSTIC IA (LOGIQUE MÉTIER) ---
st.subheader("📝 Diagnostic de l'Assistant")

col1, col2 = st.columns(2)

with col1:
    st.metric("Aptitude Scientifique ($SA$)", f"{sa}/20")
with col2:
    st.metric("Aptitude Littéraire ($LA$)", f"{la}/20")

# Logique de détection des conflits
if sa > la:
    st.markdown(f"""
        <div class="diagnostic-success">
            <strong>Profil Scientifique Dominant :</strong><br>
            L'élève possède un fort potentiel logique et mathématique.
        </div>
    """, unsafe_allow_html=True)
    
    # Détection du décalage (Aptitude vs Note)
    if aptitudes[1] > notes_ecole[1] + 3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="diagnostic-alert">
                <strong>⚠️ Alerte Décalage :</strong><br>
                Le score KRX ({aptitudes[1]}) est bien supérieur à la note de classe ({notes_ecole[1]}). 
                L'élève est sous-performant par rapport à son potentiel.
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Lancer l'interpellation IA"):
            st.info("Simulation : L'IA ouvre une discussion pour comprendre le manque de motivation en Maths...")

# Pied de page
st.markdown("<br><hr><center><small>Mémoire ENS - Filière Informatique Niveau 5</small></center>", unsafe_allow_html=True)