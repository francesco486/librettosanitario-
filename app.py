import streamlit as st

# 1. Configurazione della pagina
st.set_page_config(
    page_title="PetHealth - Wellness & Care",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializzazione dello stato per la navigazione tra le sezioni
if "sezione_attiva" not in st.session_state:
    st.session_state.sezione_attiva = "dashboard"

# Inizializzazione della lista degli animali registrati
if "lista_animali" not in st.session_state:
    st.session_state.lista_animali = ["Orlando"]

# Inizializzazione dell'animale attivo selezionato
if "pet_selezionato" not in st.session_state:
    st.session_state.pet_selezionato = st.session_state.lista_animali[0]

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

# 3. BARRA LATERALE (SIDEBAR CON GESTIONE DEGLI EVENTI DI CLICK)
with st.sidebar:
    st.caption("BENTORNATO/A")
    st.markdown("### francesco Veraldi")
    st.write("")
    
    st.markdown("**LIBRETTO ATTIVO**")
    
    # Assicuriamoci che l'indice selezionato sia valido
    index_selezionato = 0
    if st.session_state.pet_selezionato in st.session_state.lista_animali:
        index_selezionato = st.session_state.lista_animali.index(st.session_state.pet_selezionato)
        
    pet_selected = st.selectbox(
        "", 
        st.session_state.lista_animali, 
        index=index_selezionato,
        key="pet_select"
    )
    # Aggiorniamo la selezione globale
    st.session_state.pet_selezionato = pet_selected
    
    st.write("")
    st.markdown("**SEZIONI**")
    
    if st.button("🏠 Riepilogo (Dashboard)"):
        st.session_state.sezione_attiva = "dashboard"
        st.rerun()
        
    if st.button("🏥 Visite e Clinica"):
        st.session_state.sezione_attiva = "visite"
        st.rerun()
        
    if st.button("💊 Terapie e Farmaci"):
        st.session_state.sezione_attiva = "terapie"
        st.rerun()
        
    if st.button("📄 Fatture e Spese"):
        st.session_state.sezione_attiva = "fatture"
        st.rerun()
    
    st.write("")
    if st.button("Registra Nuovo Animale"):
        st.session_state.sezione_attiva = "nuovo_animale"
        st.rerun()

# 4. CONTENUTO DINAMICO DELL'APPLICAZIONE IN BASE ALLA SELEZIONE

if st.session_state.sezione_attiva == "dashboard":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
            <div class="wellness-card">
                <span class="card-badge badge-purple">TERAPIE ATTIVE</span>
                <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">💊 In Somministrazione</h3>
                <p style="color: #64748b; font-size: 0.95rem;">Nessuna terapia attiva al momento per {pet_selected}.</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="wellness-card">
                <span class="card-badge badge-blue">STORICO RECENTE</span>
                <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">🪵 Ultime Visite</h3>
                <p style="color: #64748b; font-size: 0.95rem;">Nessuna visita recente registrata per {pet_selected}.</p>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # AREA RISERVATA VETERINARIO
    with st.expander(f"⚠️ Area Riservata Medico Veterinario (Registro Decesso - {pet_selected})"):
        st.warning(f"⚠️ Attenzione: questa procedura registrerà ufficialmente il decesso dell'animale {pet_selected}. L'azione è irreversibile e richiede la conferma con PIN Veterinario.")
        
        date_decesso = st.date_input("Data del decesso")
        certificato = st.file_uploader("Allega Certificato di Morte (PDF/Foto)", type=["pdf", "png", "jpg"])
        pin_vet = st.text_input("PIN Veterinario per confermare (es. 1234)", type="password")
        
        if st.button("Conferma e Archivia Registro"):
            if pin_vet:
                st.success("Operazione completata e registro archiviato con successo.")
            else:
                st.error("Inserire un PIN Veterinario valido per procedere.")

elif st.session_state.sezione_attiva == "visite":
    st.markdown(f"<h2 style='color: #1E3A2B;'>🏥 Visite e Clinica - {pet_selected}</h2>", unsafe_allow_html=True)
    
    with st.expander("➕ Aggiungi Nuova Visita Medica", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            data_visita = st.date_input("Data Visita")
            tipo_visita = st.selectbox("Tipo di Visita", ["Controllo Generale", "Vaccinazione", "Visita Specialistica", "Urgenza", "Controllo Post-Operatorio"])
            veterinario = st.text_input("Medico Veterinario / Clinica")
        with col2:
            diagnosi = st.text_area("Diagnosi / Note Cliniche", placeholder="Descrivi il motivo della visita e l'esito...")
            referto = st.file_uploader("Allega Referto o Esami (Opzionale)", type=["pdf", "png", "jpg"], key="visita_ref")
            fattura_visita = st.file_uploader("Allega Ricevuta / Fattura (Opzionale)", type=["pdf", "png", "jpg"], key="visita_fat")
        
        st.markdown("---")
        richiede_controllo = st.checkbox("🔄 Questa prestazione richiede un controllo successivo o va ripetuta?")
        
        if richiede_controllo:
            col_ctrl1, col_ctrl2 = st.columns(2)
            with col_ctrl1:
                data_prossimo_controllo = st.date_input("Data Prossimo Controllo / Ripetizione")
            with col_ctrl2:
                tipo_prestazione_ripetere = st.text_input("Tipo di Prestazione da Eseguire", placeholder="Es. Richiamo Vaccino, Controllo Ecografico, Esami del Sangue...")
        
        st.write("")
        if st.button("Salva Visita Medica"):
            st.success(f"Visita medica registrata con successo per {pet_selected}!")

elif st.session_state.sezione_attiva == "terapie":
    st.markdown(f"<h2 style='color: #1E3A2B;'>💊 Terapie e Farmaci - {pet_selected}</h2>", unsafe_allow_html=True)
    
    with st.expander("➕ Nuova Terapia o Prescrizione", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            nome_farmaco = st.text_input("Nome del Farmaco / Principio Attivo")
            dosaggio = st.text_input("Dosaggio (es. 1 compressa ogni 12 ore)")
            data_inizio = st.date_input("Data Inizio Terapia")
            data_fine = st.date_input("Data Fine Terapia (Presunta)")
        with col2:
            note_somministrazione = st.text_area("Istruzioni e Note", placeholder="Es. Somministrare a stomaco pieno...")
            ricetta = st.file_uploader("Allega Ricetta Medica / Prescrizione (Opzionale)", type=["pdf", "png", "jpg"], key="terapia_ric")
            fattura_farmaco = st.file_uploader("Allega Scontrino / Fattura Acquisto (Opzionale)", type=["pdf", "png", "jpg"], key="terapia_fat")
            
        st.markdown("---")
        richiede_controllo_terapia = st.checkbox("🔄 La terapia richiede una verifica intermedia o un richiamo?")
        
        if richiede_controllo_terapia:
            col_tctrl1, col_tctrl2 = st.columns(2)
            with col_tctrl1:
                data_prossimo_controllo_t = st.date_input("Data Controllo Terapia / Visita di Verifica")
            with col_tctrl2:
                tipo_prestazione_terapia = st.text_input("Tipo di Controllo Richiesto", placeholder="Es. Controllo valori ematici, Visita di controllo efficacia...")

        st.write("")
        if st.button("Salva Terapia"):
            st.success(f"Terapia registrata con successo per {pet_selected}!")

elif st.session_state.sezione_attiva == "fatture":
    st.markdown(f"<h2 style='color: #1E3A2B;'>📄 Fatture e Spese - {pet_selected}</h2>", unsafe_allow_html=True)
    
    with st.expander("➕ Carica Nuova Fattura o Ricevuta", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            data_spesa = st.date_input("Data Documento")
            categoria_spesa = st.selectbox("Categoria Spesa", ["Visita Veterinaria", "Farmaci", "Esami di Laboratorio", "Chirurgia", "Cibo / Integratori", "Altro"])
            importo = st.number_input("Importo (€)", min_value=0.0, step=0.5, format="%.2f")
        with col2:
            fornitore = st.text_input("Clinica / Farmacia / Fornitore")
            file_fattura = st.file_uploader("Allega Documento Fattura / Ricevuta", type=["pdf", "png", "jpg"], key="spesa_fat")
            note_spesa = st.text_input("Note Aggiuntive (Opzionale)")
            
        if st.button("Salva Fattura"):
            st.success("Fattura / Spesa registrata con successo!")

elif st.session_state.sezione_attiva == "nuovo_animale":
    st.markdown("<h2 style='color: #1E3A2B;'>🐾 Registra Nuovo Animale</h2>", unsafe_allow_html=True)
    
    with st.form("form_nuovo_animale"):
        col1, col2 = st.columns(2)
        with col1:
            nome_animale = st.text_input("Nome dell'animale*")
            specie = st.selectbox("Specie", ["Cane", "Gatto", "Coniglio", "Altro"])
            razza = st.text_input("Razza")
        with col2:
            data_nascita = st.date_input("Data di Nascita Presunta")
            microchip = st.text_input("Numero Microchip (Opzionale)")
            foto_profilo = st.file_uploader("Foto Profilo Animale (Opzionale)", type=["png", "jpg"])
            
        submit_animale = st.form_submit_button("Salva Scheda Animale")
        
        if submit_animale:
            if nome_animale.strip() != "":
                # Aggiungiamo l'animale alla lista se non è già presente
                if nome_animale not in st.session_state.lista_animali:
                    st.session_state.lista_animali.append(nome_animale)
                
                # Impostiamo il nuovo animale come quello attivo
                st.session_state.pet_selezionato = nome_animale
                # Riportiamo l'utente alla dashboard
                st.session_state.sezione_attiva = "dashboard"
                st.success(f"Scheda di {nome_animale} creata con successo!")
                st.rerun()
            else:
                st.error("Inserisci un nome valido per l'animale.")
