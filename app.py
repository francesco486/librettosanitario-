import streamlit as st
import datetime
import sqlite3
import json

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA & STILE NICEPAGE WELLNESS & CARE
# ---------------------------------------------------------
st.set_page_config(
    page_title="PetHealth - Wellness & Care", 
    page_icon="🐾", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Custom mirato per risolvere bug di Tab e Form Submit Button
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Font Globale e Sfondo Pagina */
    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F8F7F2 !important;
        color: #1e293b !important;
    }

    /* Reset altezze linea per evitare sovrapposizioni */
    p, span, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        line-height: 1.45 !important;
    }

    /* Nascondi Elementi Standard Streamlit */
    #MainMenu, footer, header {
        visibility: hidden;
    }

    /* Sidebar Scuro Verde Foresta */
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

    /* HERO BANNER */
    .hero-card {
        background: linear-gradient(135deg, #1E3A2B 0%, #2D4A3E 100%);
        padding: 26px 24px;
        border-radius: 18px;
        color: #FFFFFF !important;
        box-shadow: 0 8px 20px rgba(30, 58, 43, 0.12);
        margin-bottom: 22px;
        border: 1px solid #2D4A3E;
    }

    .hero-title {
        color: #FFFFFF !important;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        margin: 0 0 8px 0 !important;
    }

    .hero-subtitle {
        color: #D2E3D8 !important;
        font-size: 0.98rem !important;
        margin: 0 !important;
        font-weight: 400 !important;
    }

    /* WELLNESS CARD */
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
    .badge-rose { background-color: #fce7f3; color: #9d174d; }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }

    /* BANNER SPAZIO ANGELI */
    .angeli-text {
        font-size: 1.05rem;
        font-style: italic;
        color: #831843 !important;
        text-align: center;
        margin-bottom: 1.8rem;
        padding: 18px;
        background-color: #fce7f3 !important;
        border-radius: 16px;
        border-left: 6px solid #db2777;
    }

    /* INPUT E FORM */
    label, div[data-testid="stWidgetLabel"] p {
        color: #1E3A2B !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        margin-bottom: 6px !important;
    }

    .stTextInput input, 
    .stTextArea textarea, 
    .stSelectbox > div > div, 
    .stNumberInput input,
    .stDateInput input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        padding: 10px 14px !important;
    }

    /* CORREZIONE PER I TAB (ACCEDI / REGISTRATI) */
    div[data-testid="stTabs"] {
        background-color: transparent !important;
    }

    div[data-baseweb="tab-list"] {
        gap: 10px !important;
        background-color: transparent !important;
        border-bottom: none !important;
    }

    div[data-baseweb="tab"] {
        background-color: #E2E8E4 !important;
        border-radius: 20px !important;
        padding: 8px 22px !important;
        border: none !important;
        height: auto !important;
    }

    div[data-baseweb="tab"] p, 
    div[data-baseweb="tab"] span {
        color: #1E3A2B !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #1E3A2B !important;
    }

    div[data-baseweb="tab"][aria-selected="true"] p, 
    div[data-baseweb="tab"][aria-selected="true"] span {
        color: #FFFFFF !important;
    }

    /* CORREZIONE PER I PULSANTI DEI FORM (ACCEDI AL PROFILO / REGISTRATI) */
    div[data-testid="stFormSubmitButton"] > button,
    .stButton > button {
        background-color: #1E3A2B !important;
        border: 1px solid #1E3A2B !important;
        border-radius: 25px !important;
        padding: 0.6rem 1.5rem !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(30, 58, 43, 0.15) !important;
        transition: background-color 0.2s ease !important;
    }

    div[data-testid="stFormSubmitButton"] > button p,
    div[data-testid="stFormSubmitButton"] > button span,
    .stButton > button p,
    .stButton > button span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    div[data-testid="stFormSubmitButton"] > button:hover,
    .stButton > button:hover {
        background-color: #2D4A3E !important;
        border-color: #2D4A3E !important;
    }

    /* Pulsanti Sidebar */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #2D4A3E !important;
        border: 1px solid #3E6352 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #3E6352 !important;
    }

    /* EXPANDER (Accordion) */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 14px !important;
        margin-bottom: 12px !important;
    }

    div[data-testid="stExpander"] summary p {
        color: #1E3A2B !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. GESTIONE DATABASE SQLITE
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS utenti (
            email TEXT PRIMARY KEY,
            nome TEXT,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS animali (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            nome TEXT,
            specie TEXT,
            razza TEXT,
            microchip TEXT,
            deceduto INTEGER DEFAULT 0,
            data_decesso TEXT,
            certificato_morte TEXT,
            FOREIGN KEY(user_email) REFERENCES utenti(email)
        )
    ''')
    
    try:
        c.execute("ALTER TABLE animali ADD COLUMN deceduto INTEGER DEFAULT 0")
        c.execute("ALTER TABLE animali ADD COLUMN data_decesso TEXT")
        c.execute("ALTER TABLE animali ADD COLUMN certificato_morte TEXT")
    except sqlite3.OperationalError:
        pass
        
    c.execute('''
        CREATE TABLE IF NOT EXISTS dati_sanitari (
            pet_id INTEGER PRIMARY KEY,
            prestazioni TEXT,
            terapie TEXT,
            FOREIGN KEY(pet_id) REFERENCES animali(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS fatture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            numero_fattura TEXT,
            data_fattura TEXT,
            emittente TEXT,
            descrizione TEXT,
            importo REAL,
            nome_file TEXT,
            FOREIGN KEY(pet_id) REFERENCES animali(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- FUNZIONI DATABASE ---
def registra_utente_db(nome, email, password):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO utenti VALUES (?, ?, ?)", (email, nome, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verifica_login_db(email, password):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("SELECT nome FROM utenti WHERE email = ? AND password = ?", (email, password))
    user = c.fetchone()
    conn.close()
    return user

def salva_animale_db(email, nome, specie, razza, microchip):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("INSERT INTO animali (user_email, nome, specie, razza, microchip, deceduto) VALUES (?, ?, ?, ?, ?, 0)",
              (email, nome, specie, razza, microchip))
    pet_id = c.lastrowid
    c.execute("INSERT INTO dati_sanitari VALUES (?, ?, ?)", (pet_id, json.dumps([]), json.dumps([])))
    conn.commit()
    conn.close()
    return pet_id

def registra_decesso_db(pet_id, data_decesso, certificato):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("UPDATE animali SET deceduto = 1, data_decesso = ?, certificato_morte = ? WHERE id = ?",
              (data_decesso, certificato, pet_id))
    conn.commit()
    conn.close()

def annulla_decesso_db(pet_id):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("UPDATE animali SET deceduto = 0, data_decesso = NULL, certificato_morte = NULL WHERE id = ?", (pet_id,))
    conn.commit()
    conn.close()

def carica_tutti_animali_db(email):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("SELECT id, nome, specie, razza, microchip, deceduto, data_decesso, certificato_morte FROM animali WHERE user_email = ?", (email,))
    rows = c.fetchall()
    conn.close()
    pets_vivi = []
    pets_angeli = []
    for r in rows:
        animale = {
            "id": r[0], "nome": r[1], "specie": r[2], "razza": r[3], "microchip": r[4], 
            "deceduto": r[5], "data_decesso": r[6], "certificato_morte": r[7]
        }
        if r[5] == 1:
            pets_angeli.append(animale)
        else:
            pets_vivi.append(animale)
    return pets_vivi, pets_angeli

def carica_dati_sanitari_pet_db(pet_id):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("SELECT prestazioni, terapie FROM dati_sanitari WHERE pet_id = ?", (pet_id,))
    sanitari = c.fetchone()
    conn.close()
    prestazioni = json.loads(sanitari[0]) if sanitari else []
    terapie = json.loads(sanitari[1]) if sanitari else []
    return prestazioni, terapie

def salva_sanitari_db(pet_id, prestazioni, terapie):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("UPDATE dati_sanitari SET prestazioni = ?, terapie = ? WHERE pet_id = ?",
              (json.dumps(prestazioni), json.dumps(terapie), pet_id))
    conn.commit()
    conn.close()

def carica_fatture_db(pet_id):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, numero_fattura, data_fattura, emittente, descrizione, importo, nome_file 
        FROM fatture WHERE pet_id = ? ORDER BY id DESC
    ''', (pet_id,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "numero": r[1], "data": r[2], "emittente": r[3], "descrizione": r[4], "importo": r[5], "file": r[6]} for r in rows]

def salva_fattura_db(pet_id, num, data, emittente, desc, importo, file_name):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO fatture (pet_id, numero_fattura, data_fattura, emittente, descrizione, importo, nome_file)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (pet_id, num, data, emittente, desc, importo, file_name))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# 3. GESTIONE STATO DELLA SESSIONE (SESSION STATE)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'user_nome' not in st.session_state:
    st.session_state.user_nome = ""
if 'step_corrente' not in st.session_state:
    st.session_state.step_corrente = 'auth'
if 'lista_animali_vivi' not in st.session_state:
    st.session_state.lista_animali_vivi = []
if 'lista_animali_angeli' not in st.session_state:
    st.session_state.lista_animali_angeli = []
if 'dati_animale' not in st.session_state:
    st.session_state.dati_animale = {}
if 'prestazioni' not in st.session_state:
    st.session_state.prestazioni = []
if 'terapie' not in st.session_state:
    st.session_state.terapie = []

def aggiorna_sessione_animali(email):
    vivi, angeli = carica_tutti_animali_db(email)
    st.session_state.lista_animali_vivi = vivi
    st.session_state.lista_animali_angeli = angeli

# ---------------------------------------------------------
# STEP 1: LOGIN E REGISTRAZIONE UTENTE
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <div style="display: inline-block; padding: 6px 16px; background-color: #E8F0EC; border-radius: 50px; margin-bottom: 12px; border: 1px solid #d1e2d8;">
                <span style="color: #1E3A2B; font-weight: 800; font-size: 0.8rem; letter-spacing: 0.05em;">WELLNESS & CARE VETERINARIO</span>
            </div>
            <h1 style="font-size: 2.5rem; font-weight: 800; color: #1E3A2B; margin-bottom: 8px;">PetHealth 🐾</h1>
            <p style="color: #475569; font-size: 1rem; max-width: 480px; margin: 0 auto; font-weight: 500;">
                Accedi al tuo centro salute digitale per gestire in modo semplice, curato ed elegante la vita dei tuoi animali.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col_centered = st.columns([1, 2, 1])[1]
    with col_centered:
        tab_login, tab_reg = st.tabs(["🔑 Accedi", "📝 Registrati"])
        
        with tab_login:
            with st.form("form_login"):
                email_log = st.text_input("E-mail")
                pass_log = st.text_input("Password", type="password")
                btn_log = st.form_submit_button("Accedi al Profilo ➔", use_container_width=True)
                
                if btn_log:
                    user = verifica_login_db(email_log, pass_log)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email_log
                        st.session_state.user_nome = user[0]
                        
                        aggiorna_sessione_animali(email_log)
                        
                        if st.session_state.lista_animali_vivi:
                            st.session_state.dati_animale = st.session_state.lista_animali_vivi[0]
                            prest, ter = carica_dati_sanitari_pet_db(st.session_state.dati_animale['id'])
                            st.session_state.prestazioni = prest
                            st.session_state.terapie = ter
                            st.session_state.step_corrente = 'dashboard'
                        elif st.session_state.lista_animali_angeli:
                            st.session_state.step_corrente = 'angeli'
                        else:
                            st.session_state.step_corrente = 'registrazione_animale'
                        st.rerun()
                    else:
                        st.error("❌ E-mail o Password errate.")
                        
        with tab_reg:
            with st.form("form_registrazione"):
                nome_reg = st.text_input("Nome e Cognome")
                email_reg = st.text_input("E-mail")
                pass_reg = st.text_input("Password", type="password")
                btn_reg = st.form_submit_button("Crea Account ➔", use_container_width=True)
                
                if btn_reg:
                    if nome_reg and email_reg and pass_reg:
                        if registra_utente_db(nome_reg, email_reg, pass_reg):
                            st.success("✅ Account creato con successo! Ora puoi effettuare il Login.")
                        else:
                            st.error("⚠️ Questa e-mail risulta già registrata!")
                    else:
                        st.warning("⚠️ Compila tutti i campi.")

# ---------------------------------------------------------
# MENU LATERALE (SIDEBAR DARK VERDE FOREST)
# ---------------------------------------------------------
if st.session_state.logged_in and st.session_state.step_corrente != 'registrazione_animale':
    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 10px 0 15px 0;">
                <p style="font-size: 0.78rem; color: #D2E3D8 !important; font-weight: 700; margin:0;">BENTORNATO/A</p>
                <h2 style="font-size: 1.3rem; color: #ffffff !important; margin:0;">{st.session_state.user_nome}</h2>
            </div>
        """, unsafe_allow_html=True)
        st.divider()
        
        if st.session_state.lista_animali_vivi:
            st.markdown("<p style='font-size: 0.8rem; font-weight: 800; color: #D2E3D8 !important;'>LIBRETTO ATTIVO</p>", unsafe_allow_html=True)
            pet_dict = {p['nome']: p for p in st.session_state.lista_animali_vivi}
            lista_nomi = list(pet_dict.keys())
            
            nome_attuale = st.session_state.dati_animale.get('nome', '') if not st.session_state.dati_animale.get('deceduto', 0) else ''
            idx_corrente = lista_nomi.index(nome_attuale) if nome_attuale in lista_nomi else 0
            
            animale_selezionato = st.selectbox("Seleziona animale:", lista_nomi, index=idx_corrente, label_visibility="collapsed")
            
            if st.session_state.step_corrente != 'angeli' and animale_selezionato != nome_attuale:
                nuovo_pet = pet_dict[animale_selezionato]
                st.session_state.dati_animale = nuovo_pet
                prest, ter = carica_dati_sanitari_pet_db(nuovo_pet['id'])
                st.session_state.prestazioni = prest
                st.session_state.terapie = ter
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
            
            if st.session_state.step_corrente != 'angeli':
                st.divider()
                st.markdown("<p style='font-size: 0.8rem; font-weight: 800; color: #D2E3D8 !important;'>SEZIONI</p>", unsafe_allow_html=True)
                if st.button("🏠 Riepilogo (Dashboard)", use_container_width=True):
                    st.session_state.step_corrente = 'dashboard'
                    st.rerun()
                if st.button("🩺 Visite e Clinica", use_container_width=True):
                    st.session_state.step_corrente = 'pagina_visite'
                    st.rerun()
                if st.button("💊 Terapie e Farmaci", use_container_width=True):
                    st.session_state.step_corrente = 'pagina_terapie'
                    st.rerun()
                if st.button("🧾 Fatture e Spese", use_container_width=True):
                    st.session_state.step_corrente = 'pagina_fatture'
                    st.rerun()
                
            if st.session_state.step_corrente == 'angeli':
                st.divider()
                if st.button("🔙 Torna alla Dashboard", use_container_width=True):
                    st.session_state.step_corrente = 'dashboard'
                    if st.session_state.lista_animali_vivi:
                        st.session_state.dati_animale = st.session_state.lista_animali_vivi[0]
                        prest, ter = carica_dati_sanitari_pet_db(st.session_state.dati_animale['id'])
                        st.session_state.prestazioni = prest
                        st.session_state.terapie = ter
                    st.rerun()

        st.divider()
        if st.button("➕ Registra Nuovo Animale", use_container_width=True):
            st.session_state.step_corrente = 'registrazione_animale'
            st.rerun()
            
        if st.session_state.lista_animali_angeli:
            if st.button("🕊️ Angeli a 4 Zampe", use_container_width=True):
                st.session_state.step_corrente = 'angeli'
                st.rerun()
                
        st.write("")
        if st.button("🚪 Esci (Logout)", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ---------------------------------------------------------
# STEP: REGISTRAZIONE NUOVO ANIMALE
# ---------------------------------------------------------
if st.session_state.step_corrente == 'registrazione_animale':
    if st.session_state.lista_animali_vivi or st.session_state.lista_animali_angeli:
        if st.button("⬅️ Annulla e torna indietro"):
            st.session_state.step_corrente = 'dashboard' if st.session_state.lista_animali_vivi else 'angeli'
            st.rerun()
            
    st.markdown("""
        <div class="hero-card">
            <span class="card-badge">Nuovo Profilo</span>
            <h1 class="hero-title">Aggiungi un Animale 🐾</h1>
            <p class="hero-subtitle">Inserisci i dati per attivare la nuova cartella clinica</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("form_animale"):
        nome_pet = st.text_input("Nome dell'animale")
        specie = st.selectbox("Specie", ["Cane 🐶", "Gatto 🐱", "Coniglio 🐰", "Altro"])
        razza = st.text_input("Razza")
        microchip = st.text_input("Numero Microchip")
        submit_pet = st.form_submit_button("Crea Cartella Clinica ➔", use_container_width=True)
        
        if submit_pet and nome_pet:
            pet_id = salva_animale_db(st.session_state.user_email, nome_pet, specie, razza, microchip)
            aggiorna_sessione_animali(st.session_state.user_email)
            nuovo_pet = [p for p in st.session_state.lista_animali_vivi if p['id'] == pet_id][0]
            st.session_state.dati_animale = nuovo_pet
            st.session_state.prestazioni = []
            st.session_state.terapie = []
            st.session_state.step_corrente = 'dashboard'
            st.rerun()

# ---------------------------------------------------------
# STEP: MEMORIAL ANGELI
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'angeli':
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0 1rem 0;">
            <div style="display: inline-block; padding: 6px 16px; background-color: #fce7f3; border-radius: 50px; margin-bottom: 10px; border: 1px solid #fbcfe8;">
                <span style="color: #9d174d; font-weight: 800; font-size: 0.8rem; letter-spacing: 0.05em;">SPAZIO MEMORIA PERMANENTE</span>
            </div>
            <h1 style="font-size: 2.4rem; font-weight: 800; color: #831843 !important; margin-bottom: 8px;">I nostri angeli a 4 zampe 🕊️</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="angeli-text">Ricorda {st.session_state.user_nome}, per quanto doloroso, i nostri compagni di vita non ci abbandonano mai veramente. Il loro ricordo e il loro storico restano al sicuro qui con noi ❤️</div>', unsafe_allow_html=True)
    
    if not st.session_state.lista_animali_angeli:
        st.info("Non ci sono animali registrati in questa sezione.")
    else:
        for angelo in st.session_state.lista_animali_angeli:
            with st.expander(f"🕊️ {angelo['nome']} ({angelo['specie']} - {angelo['razza']})", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Data della scomparsa:** <span style='color:#0f172a;'>{angelo['data_decesso']}</span>", unsafe_allow_html=True)
                with col2:
                    if angelo['certificato_morte'] and angelo['certificato_morte'] != "Nessun file":
                        st.markdown(f"**Certificato di Morte:** 📎 {angelo['certificato_morte']}")
                    else:
                        st.markdown("**Certificato di Morte:** Non allegato")
                
                st.divider()
                st.markdown(f"### Storico Clinico Archiviato di {angelo['nome']}")
                
                prestazioni_angelo, terapie_angelo = carica_dati_sanitari_pet_db(angelo['id'])
                fatture_angelo = carica_fatture_db(angelo['id'])
                
                tab_visite, tab_terapie, tab_fatture = st.tabs(["📜 Visite", "💊 Terapie", "🧾 Fatture"])
                
                with tab_visite:
                    if not prestazioni_angelo:
                        st.write("Nessuna visita registrata.")
                    for item in reversed(prestazioni_angelo):
                        st.markdown(f"**{item.get('Data', '')} - {item.get('Prestazione', '')}**")
                        st.caption(f"Vet: {item.get('Veterinario', '')} | {item.get('Dettagli', '')}")
                        st.markdown("---")
                with tab_terapie:
                    if not terapie_angelo:
                        st.write("Nessuna terapia registrata.")
                    for t in reversed(terapie_angelo):
                        st.markdown(f"**{t.get('Farmaco', '')}** (Inizio: {t.get('Data_Inizio', '')})")
                        st.caption(f"Durata: {t.get('Durata', '')} | Posologia: {t.get('Posologia', '')}")
                        st.markdown("---")
                with tab_fatture:
                    if not fatture_angelo:
                        st.write("Nessuna fattura registrata.")
                    for f in fatture_angelo:
                        st.markdown(f"**Fattura N° {f['numero']} del {f['data']} - {f['importo']:.2f} €**")
                        st.caption(f"Emittente: {f['emittente']} | Allegato: {f['file']}")
                        st.markdown("---")
                
                st.divider()
                with st.popover(f"🔄 Annulla segnalazione decesso di {angelo['nome']}"):
                    st.warning("Usa questa funzione solo se la segnalazione di decesso è stata effettuata per errore.")
                    with st.form(f"form_annulla_{angelo['id']}"):
                        pin_undo = st.text_input("Inserisci PIN Veterinario (es. 1234)", type="password")
                        btn_undo = st.form_submit_button("Annulla Decesso e Ripristina Profilo")
                        
                        if btn_undo:
                            if pin_undo == "1234":
                                annulla_decesso_db(angelo['id'])
                                st.success(f"Profilo di {angelo['nome']} ripristinato con successo!")
                                aggiorna_sessione_animali(st.session_state.user_email)
                                st.session_state.dati_animale = angelo
                                st.session_state.dati_animale['deceduto'] = 0
                                st.session_state.prestazioni, st.session_state.terapie = carica_dati_sanitari_pet_db(angelo['id'])
                                st.session_state.step_corrente = 'dashboard'
                                st.rerun()
                            else:
                                st.error("❌ PIN Veterinario errato.")

# ---------------------------------------------------------
# PAGINA: DASHBOARD (RIEPILOGO)
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'dashboard':
    st.markdown(f"""
        <div class="hero-card">
            <span class="card-badge">Profilo Sanitario Attivo</span>
            <h1 class="hero-title">{st.session_state.dati_animale.get('nome', 'Animale')}</h1>
            <p class="hero-subtitle">
                Specie: <strong style="color:#ffffff;">{st.session_state.dati_animale.get('specie')}</strong> &bull; 
                Razza: <strong style="color:#ffffff;">{st.session_state.dati_animale.get('razza') or 'Non specificata'}</strong> &bull; 
                Microchip: <strong style="color:#ffffff;">{st.session_state.dati_animale.get('microchip') or 'Non inserito'}</strong>
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="wellness-card">
                <span class="card-badge badge-purple">Terapie Attive</span>
                <h3 style="margin-top: 6px; margin-bottom: 12px; font-size: 1.2rem; color:#1E3A2B;">💊 In Somministrazione</h3>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.terapie) == 0:
            st.markdown("<p style='color: #64748b; margin:0;'>Nessuna terapia attiva al momento.</p>", unsafe_allow_html=True)
        else:
            for t in reversed(st.session_state.terapie[-3:]):
                st.markdown(f"<p style='margin-bottom:8px; line-height: 1.4;'>🔹 <strong>{t.get('Farmaco', 'Farmaco')}</strong> <span style='color:#64748b;'>(dal {t.get('Data_Inizio', 'N/D')})</span></p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="wellness-card">
                <span class="card-badge badge-blue">Storico Recente</span>
                <h3 style="margin-top: 6px; margin-bottom: 12px; font-size: 1.2rem; color:#1E3A2B;">📜 Ultime Visite</h3>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.prestazioni) == 0:
            st.markdown("<p style='color: #64748b; margin:0;'>Nessuna visita recente registrata.</p>", unsafe_allow_html=True)
        else:
            for p in reversed(st.session_state.prestazioni[-3:]):
                st.markdown(f"<p style='margin-bottom:8px; line-height: 1.4;'>🔸 <strong>{p.get('Data', 'N/D')}</strong> - {p.get('Prestazione', 'Visita')}</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    with st.expander("⚠️ Area Riservata Medico Veterinario (Registra Decesso)"):
        st.warning("L'azione sottostante sposterà la cartella clinica di questo animale nella sezione 'I nostri angeli a 4 zampe'.")
        with st.form("form_decesso"):
            data_dec = st.date_input("Data del decesso", datetime.date.today())
            cert_morte = st.file_uploader("Allega Certificato di Morte (PDF/Foto)", type=['pdf', 'png', 'jpg'])
            pin_vet_dec = st.text_input("PIN Veterinario per confermare (es. 1234)", type="password")
            submit_dec = st.form_submit_button("Conferma e Archivia Registro")
            
            if submit_dec:
                if pin_vet_dec == "1234":
                    nome_file_cert = cert_morte.name if cert_morte else "Nessun file"
                    registra_decesso_db(st.session_state.dati_animale['id'], data_dec.strftime("%d/%m/%Y"), nome_file_cert)
                    st.success("Operazione confermata. Cartella archiviata.")
                    aggiorna_sessione_animali(st.session_state.user_email)
                    st.session_state.step_corrente = 'angeli'
                    st.rerun()
                else:
                    st.error("❌ PIN Veterinario errato.")

# ---------------------------------------------------------
# PAGINA: GESTIONE VISITE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'pagina_visite':
    st.markdown(f"""
        <div class="hero-card">
            <span class="card-badge badge-blue">Gestione Clinica</span>
            <h1 class="hero-title">Visite & Prestazioni</h1>
            <p class="hero-subtitle">Paziente: <strong style="color:#ffffff;">{st.session_state.dati_animale['nome']}</strong> &bull; Registra referti, diagnosi e controlli</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("➕ Registra Nuova Visita Medica", expanded=False):
        with st.form("form_visita"):
            tipo_prestazione = st.selectbox("Tipo di Prestazione", ["Visita Generale", "Vaccino", "Intervento Chirurgico", "Controllo Periodico", "Esami del Sangue", "Altro"])
            data_esecuzione = st.date_input("Data Visita", datetime.date.today())
            nome_vet = st.text_input("Nome Clinica o Medico Veterinario")
            dettagli = st.text_area("📝 Note Cliniche, Diagnosi o Referti")
            
            if st.form_submit_button("Salva Prestazione Clinica ➔", use_container_width=True):
                nuova_prestazione = {"Data": data_esecuzione.strftime("%d/%m/%Y"), "Prestazione": tipo_prestazione, "Veterinario": nome_vet, "Dettagli": dettagli}
                st.session_state.prestazioni.append(nuova_prestazione)
                salva_sanitari_db(st.session_state.dati_animale['id'], st.session_state.prestazioni, st.session_state.terapie)
                st.success("Visita salvata correttamente!")
                st.rerun()

    st.divider()
    st.subheader("Archivio Storico Visite")
    if len(st.session_state.prestazioni) == 0:
        st.info("💡 Nessuna visita medica registrata finora.")
    else:
        for item in reversed(st.session_state.prestazioni):
            with st.container(border=True):
                st.markdown(f"<h3 style='margin-bottom:8px; color:#1E3A2B;'>🩺 {item.get('Prestazione', 'Visita')} &bull; <span style='color: #2563eb;'>{item.get('Data', 'N/D')}</span></h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin-bottom:4px;'><strong>🏥 Clinica / Medico:</strong> {item.get('Veterinario', 'N/D')}</p>", unsafe_allow_html=True)
                if item.get('Dettagli'):
                    st.markdown(f"<p style='margin-bottom:0px;'><strong>📋 Dettagli Medici:</strong> {item.get('Dettagli')}</p>", unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGINA: GESTIONE TERAPIE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'pagina_terapie':
    st.markdown(f"""
        <div class="hero-card">
            <span class="card-badge badge-purple">Farmacologia</span>
            <h1 class="hero-title">Gestione Terapie</h1>
            <p class="hero-subtitle">Paziente: <strong style="color:#ffffff;">{st.session_state.dati_animale['nome']}</strong> &bull; Registra farmaci, dosaggi e trattamenti</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("➕ Aggiungi Nuova Terapia Farmacologica", expanded=False):
        with st.form("form_terapia"):
            farmaco = st.text_input("Nome del Farmaco / Principi Attivi")
            data_in = st.date_input("Data Inizio Terapia", datetime.date.today())
            
            if st.form_submit_button("Salva Terapia Farmacologica ➔", use_container_width=True):
                st.session_state.terapie.append({"Farmaco": farmaco, "Data_Inizio": data_in.strftime("%d/%m/%Y")})
                salva_sanitari_db(st.session_state.dati_animale['id'], st.session_state.prestazioni, st.session_state.terapie)
                st.success("Terapia aggiunta al registro!")
                st.rerun()

    st.divider()
    st.subheader("Terapie Registrate")
    if len(st.session_state.terapie) == 0:
        st.info("💡 Nessun farmaco o terapia inserita.")
    else:
        for t in reversed(st.session_state.terapie):
            with st.container(border=True):
                st.markdown(f"<h3 style='margin-bottom:8px; color:#1E3A2B;'>💊 {t.get('Farmaco', 'Farmaco')}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin-bottom:0px;'><strong>🗓️ Data Inizio Somministrazione:</strong> {t.get('Data_Inizio', 'N/D')}</p>", unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGINA: GESTIONE FATTURE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'pagina_fatture':
    st.markdown(f"""
        <div class="hero-card">
            <span class="card-badge badge-rose">Contabilità & Documenti</span>
            <h1 class="hero-title">Fatture e Ricevute</h1>
            <p class="hero-subtitle">Paziente: <strong style="color:#ffffff;">{st.session_state.dati_animale['nome']}</strong> &bull; Archivio spese veterinarie</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("➕ Inserisci Nuova Fattura Spesa", expanded=False):
        with st.form("form_fattura"):
            num_fattura = st.text_input("N° Documento / Fattura")
            data_fattura = st.date_input("Data Documento", datetime.date.today())
            emittente = st.text_input("Emittente (es. Clinica Veterinaria San Francesco)")
            importo = st.number_input("Importo Complessivo (€)", min_value=0.0, step=10.0)
            
            if st.form_submit_button("Salva Fattura in Archivio ➔", use_container_width=True) and num_fattura:
                salva_fattura_db(st.session_state.dati_animale['id'], num_fattura, data_fattura.strftime("%d/%m/%Y"), emittente, "", importo, "")
                st.success("Fattura archiviata con successo!")
                st.rerun()

    st.divider()
    st.subheader("Registro Documenti Fiscali")
    fatture = carica_fatture_db(st.session_state.dati_animale['id'])
    if not fatture:
        st.info("💡 Nessun documento contabile presente.")
    else:
        for f in fatture:
            with st.container(border=True):
                st.markdown(f"<h3 style='margin-bottom:8px; color:#1E3A2B;'>🧾 Fattura N° {f['numero']} <span style='font-size: 0.95rem; color: #64748b;'>del {f['data']}</span></h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin-bottom:4px;'><strong>🏥 Emittente:</strong> {f['emittente']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin-bottom:0px;'><strong>💶 Importo:</strong> <span style='font-size: 1.1rem; font-weight: 800; color: #059669;'>{f['importo']:.2f} €</span></p>", unsafe_allow_html=True)
