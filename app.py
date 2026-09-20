import streamlit as st

# 1. Configurazione della pagina
st.set_page_config(
    page_title="PetHealth - Wellness & Care",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS Custom Completo con Fix Dark Mode e Stili Layout
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Forziamo il tema chiaro su tutto l'applicativo */
    :root {
        color-scheme: light !important;
    }

    /* Font Globale e Sfondo App */
    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F8F7F2 !important;
        color: #1e293b !important;
    }

    /* Reset generico per paragrafi e label */
    .stApp p:not([data-testid="stExpander"] *), 
    .stApp label {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        line-height: 1.45 !important;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #1E3A2B !important;
        border-right: 1px solid #2D4A3E !important;
    }

    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    @media (min-width: 768px) {
        [data-testid="stSidebarCollapseButton"], 
        [data-testid="stSidebarToggle"], 
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
        }

        section[data-testid="stSidebar"] {
            display: block !important;
            min-width: 21rem !important;
            max-width: 21rem !important;
        }
    }

    /* WELLNESS CARDS */
    .wellness-card {
        background-color: #FFFFFF !important;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #E2E8E4 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
        margin-bottom: 16px;
    }

    /* BADGES */
    .card-badge {
        display: inline-block;
        padding: 4px 12px;
        background-color: #E8F0EC;
        color: #1E3A2B;
        font-weight: 700;
        font-size: 0.78rem;
        border-radius: 20px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }

    /* INPUT E FORM - CORREZIONE COLORI E SFONDI */
    label, div[data-testid="stWidgetLabel"] p {
        color: #1E3A2B !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        margin-bottom: 6px !important;
    }

    /* Input generici, Date Input e File Uploader */
    .stTextInput input, 
    .stTextArea textarea, 
    .stSelectbox > div > div, 
    .stNumberInput input,
    .stDateInput input,
    div[data-baseweb="input"] {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }

    /* FIX FILE UPLOADER SCURO */
    div[data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 1.5px dashed #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }

    div[data-testid="stFileUploader"] * {
        color: #1e293b !important;
    }

    div[data-testid="stFileUploader"] button {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
    }

    /* FIX RIQUADRO GIALLO (st.warning / st.alert) */
    div[data-testid="stAlert"] {
        background-color: #fefce8 !important;
        border: 1px solid #fef08a !important;
        border-radius: 12px !important;
    }

    div[data-testid="stAlert"] * {
        color: #854d0e !important;
        font-weight: 600 !important;
    }

    /* PULSANTI FORM E SIDEBAR */
    div[data-testid="stFormSubmitButton"] > button,
    .stButton > button {
        background-color: #1E3A2B !important;
        border: 1px solid #1E3A2B !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(30, 58, 43, 0.15) !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stFormSubmitButton"] > button p,
    div[data-testid="stFormSubmitButton"] > button span,
    div[data-testid="stFormSubmitButton"] > button div,
    .stButton > button p,
    .stButton > button span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    div[data-testid="stFormSubmitButton"] > button:hover,
    .stButton > button:hover {
        background-color: #2D4A3E !important;
        border-color: #2D4A3E !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: #2D4A3E !important;
        border: 1px solid #3E6352 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #3E6352 !important;
    }

    /* FIX COMPLETO EXPANDER E HEADER SCURI */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 14px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
    }

    div[data-testid="stExpander"] summary {
        background-color: #ffffff !important;
        border-radius: 14px !important;
    }

    div[data-testid="stExpander"] details summary div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stExpander"] summary * {
        color: #1E3A2B !important;
        -webkit-text-fill-color: #1E3A2B !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    /* SELECTBOX SIDEBAR */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div,
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] * {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label p {
        color: #D2E3D8 !important;
        -webkit-text-fill-color: #D2E3D8 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. BARRA LATERALE (SIDEBAR)
with st.sidebar:
    st.caption("BENTORNATO/A")
    st.markdown("### francesco Veraldi")
    st.write("")
    
    st.markdown("**LIBRETTO ATTIVO**")
    pet_selected = st.selectbox("", ["Orlando"], key="pet_select")
    
    st.write("")
    st.markdown("**SEZIONI**")
    st.button("🏠 Riepilogo (Dashboard)")
    st.button("🏥 Visite e Clinica")
    st.button("💊 Terapie e Farmaci")
    st.button("📄 Fatture e Spese")
    
    st.write("")
    st.button("Registra Nuovo Animale")

# 4. CONTENUTO PRINCIPALE (DASHBOARD)
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="wellness-card">
            <span class="card-badge badge-purple">TERAPIE ATTIVE</span>
            <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">💊 In Somministrazione</h3>
            <p style="color: #64748b; font-size: 0.95rem;">Nessuna terapia attiva al momento.</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="wellness-card">
            <span class="card-badge badge-blue">STORICO RECENTE</span>
            <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">🪵 Ultime Visite</h3>
            <p style="color: #64748b; font-size: 0.95rem;">Nessuna visita recente registrata.</p>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# 5. AREA RISERVATA VETERINARIO (EXPANDER E FORM)
with st.expander("⚠️ Area Riservata Medico Veterinario (Registro Decesso)"):
    st.warning("⚠️ Attenzione: questa procedura registrerà ufficialmente il decesso dell'animale. L'azione è irreversibile e richiede la conferma con PIN Veterinario.")
    
    date_decesso = st.date_input("Data del decesso")
    certificato = st.file_uploader("Allega Certificato di Morte (PDF/Foto)", type=["pdf", "png", "jpg"])
    pin_vet = st.text_input("PIN Veterinario per confermare (es. 1234)", type="password")
    
    if st.button("Conferma e Archivia Registro"):
        if pin_vet:
            st.success("Operazione completata e registro archiviato con successo.")
        else:
            st.error("Inserire un PIN Veterinario valido per procedere.")
