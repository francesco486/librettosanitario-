import streamlit as st
import datetime
import sqlite3
import json

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA & STILE PREMIUM AD ALTO CONTRASTO
# ---------------------------------------------------------
st.set_page_config(
    page_title="PetHealth - Libretto Digitale", 
    page_icon="🐾", 
    layout="centered"
)

# CSS Custom ad altissima leggibilità
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');

    /* Reset Globale e Tipografia */
    html, body, [class*="css"], div, p, span {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #1e293b;
    }

    /* Nascondi header Streamlit standard */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Background Principale */
    .stApp {
        background-color: #f8fafc !important;
    }

    /* Gestione Titoli */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* HERO BANNER (Intestazione Principale) */
    .hero-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        margin-bottom: 25px;
        border: 1px solid #334155;
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        margin: 0 0 8px 0 !important;
    }

    .hero-subtitle {
        color: #94a3b8 !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
    }

    /* CARD CLINICHE (Contenitori) */
    .custom-card {
        background-color: #ffffff !important;
        border-radius: 16px;
        padding: 22px;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 18px;
    }

    /* BANNER ANGELI */
    .angeli-text {
        font-size: 1.05rem;
        font-style: italic;
        color: #831843 !important;
        text-align: center;
        margin-bottom: 2rem;
        padding: 20px;
        background-color: #fce7f3 !important;
        border-radius: 16px;
        border-left: 6px solid #db2777;
        box-shadow: 0 4px 12px rgba(219, 39, 119, 0.08);
    }

    /* --- RISOLUZIONE PROBLEMA TESTO INVISIBILE NEI FORM/INPUT --- */
    /* Etichette dei Campi */
    label, div[data-testid="stWidgetLabel"] p {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }

    /* Input di Testo, TextArea, Selectbox, Number Input */
    input, textarea, select {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1px solid #94a3b8 !important;
        border-radius: 10px !important;
    }

    .stTextInput > div > div > input, 
    .stTextArea textarea, 
    .stSelectbox > div > div, 
    .stNumberInput > div > div > input,
    .stDateInput input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }

    .stTextInput > div > div > input:focus, 
    .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }

    /* Dropdown / Menu a Tendenza Opzioni */
    div[data-baseweb="popover"] *, div[data-baseweb="menu"] * {
        color: #0f172a !important;
        background-color: #ffffff !important;
    }

    /* EXPANDER (Accordion) */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 14px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }

    div[data-testid="stExpander"] summary p {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    /* PULSANTI GENERATION */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 0.6rem 1.2rem !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        border-color: #2563eb !important;
        color: #2563eb !important;
        background-color: #eff6ff !important;
    }

    /* Pulsante submit dei Form (Pulsante Primario Azione) */
    div[data-testid="stForm"] .stButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
    }

    div[data-testid="stForm"] .stButton > button:hover {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
    }

    /* BADGES & TAGS */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-green { background-color: #d1fae5; color: #065f46; }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }
    .badge-rose { background-color: #ffe4e6; color: #9f1239; }

    /* SIDEBAR LUXURY DARK */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b !important;
    }

    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        width: 100%;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-color: #2563eb !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. GESTIONE DATABASE SQLITE (MEMORIA PERMANENTE)
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

# --- Funzioni DB ---
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
# 3. SESSION STATE INITIALIZATION
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
# STEP 1: SCHERMATA LOGIN / REGISTRAZIONE
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <div style="display: inline-block; padding: 6px 16px; background-color: #dbeafe; border-radius: 50px; margin-bottom: 12px; border: 1px solid #bfdbfe;">
                <span style="color: #1e40af; font-weight: 800; font-size: 0.8rem; letter-spacing: 0.05em;">LIBRETTO VETERINARIO DIGITALE</span>
            </div>
            <h1 style="font-size: 2.6rem; font-weight: 800; color: #0f172a; margin-bottom: 6px;">PetHealth 🐾</h1>
            <p style="color: #475569; font-size: 1rem; max-width: 480px; margin: 0 auto; font-weight: 500;">
                Accedi al tuo profilo per gestire in modo semplice, sicuro ed elegante la salute dei tuoi animali.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
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
# MENU LATERALE (SIDEBAR DARK LUXURY)
# ---------------------------------------------------------
if st.session_state.logged_in and st.session_state.step_corrente != 'registrazione_animale':
    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 10px 0 15px 0;">
                <p style="font-size: 0.78rem; color: #94a3b8 !weight: 700; margin:0;">BENTORNATO/A</p>
                <h2 style="font-size: 1.3rem; color: #ffffff !important; margin:0;">{st.session_state.user_nome}</h2>
            </div>
        """, unsafe_allow_html=True)
        st.divider()
        
        if st.session_state.lista_animali_vivi:
            st.markdown("<p style='font-size: 0.8rem; font-weight: 800; color: #94a3b8 !important;'>LIBRETTO ATTIVO</p>", unsafe_allow_html=True)
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
            
            # --- MENU DI NAVIGAZIONE ---
            if st.session_state.step_corrente != 'angeli':
                st.divider()
                st.markdown("<p style='font-size: 0.8rem; font-weight: 800; color: #94a3b8 !important;'>SEZIONI DISPONIBILI</p>", unsafe_allow_html=True)
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
            <span class="badge badge-green">Nuovo Profilo</span>
            <h1 class="hero-title">Aggiungi un Animale 🐾</h1>
            <p class="hero-subtitle">Inserisci i dati principali per generare il libretto sanitario digitale</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("form_animale"):
        nome_pet = st.text_input("Nome dell'animale")
        specie = st.selectbox("Specie", ["Cane 🐶", "Gatto 🐱", "Coniglio 🐰", "Altro"])
        razza = st.text_input("Razza")
        microchip = st.text_input("Numero Microchip")
        submit_pet = st.form_submit_button("Crea Libretto Digitale ➔", use_container_width=True)
        
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
            <span class="badge badge-green">Profilo Sanitario Attivo</span>
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
            <div class="custom-card">
                <span class="badge badge-purple">Terapie Attive</span>
                <h3 style="margin-top: 5px; margin-bottom: 12px; font-size: 1.2rem;">💊 In Somministrazione</h3>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.terapie) == 0:
            st.markdown("<p style='color: #64748b;'>Nessuna terapia attiva al momento.</p>", unsafe_allow_html=True)
        else:
            for t in reversed(st.session_state.terapie[-3:]):
                st.markdown(f"<p style='margin-bottom:6px;'>🔹 <strong>{t.get('Farmaco', 'Farmaco')}</strong> <span style='color:#64748b;'>(dal {t.get('Data_Inizio', 'N/D')})</span></p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="custom-card">
                <span class="badge badge-blue">Storico Recente</span>
                <h3 style="margin-top: 5px; margin-bottom: 12px; font-size: 1.2rem;">📜 Ultime Visite</h3>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.prestazioni) == 0:
            st.markdown("<p style='color: #64748b;'>Nessuna visita recente registrata.</p>", unsafe_allow_html=True)
        else:
            for p in reversed(st.session_state.prestazioni[-3:]):
                st.markdown(f"<p style='margin-bottom:6px;'>🔸 <strong>{p.get('Data', 'N/D')}</strong> - {p.get('Prestazione', 'Visita')}</p>", unsafe_allow_html=True)
        
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
            <span class="badge badge-blue">Gestione Clinica</span>
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
                st.markdown(f"<h3 style='margin-bottom:6px;'>🩺 {item.get('Prestazione', 'Visita')} &bull; <span style='color: #2563eb;'>{item.get('Data', 'N/D')}</span></h3>", unsafe_allow_html=True)
                st.markdown(f"**🏥 Clinica / Medico:** <span style='color:#0f172a;'>{item.get('Veterinario', 'N/D')}</span>", unsafe_allow_html=True)
                if item.get('Dettagli'):
                    st.markdown(f"**📋 Dettagli Medici:** <span style='color:#334155;'>{item.get('Dettagli')}</span>", unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGINA: GESTIONE TERAPIE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'pagina_terapie':
    st.markdown(f"""
        <div class="hero-card">
            <span class="badge badge-purple">Farmacologia</span>
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
                st.markdown(f"<h3 style='margin-bottom:6px;'>💊 {t.get('Farmaco', 'Farmaco')}</h3>", unsafe_allow_html=True)
                st.markdown(f"**🗓️ Data Inizio Somministrazione:** <span style='color:#0f172a;'>{t.get('Data_Inizio', 'N/D')}</span>", unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGINA: GESTIONE FATTURE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'pagina_fatture':
    st.markdown(f"""
        <div class="hero-card">
            <span class="badge badge-rose">Contabilità & Documenti</span>
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
                st.markdown(f"<h3 style='margin-bottom:6px;'>🧾 Fattura N° {f['numero']} <span style='font-size: 0.95rem; color: #64748b;'>del {f['data']}</span></h3>", unsafe_allow_html=True)
                st.markdown(f"**🏥 Emittente:** <span style='color:#0f172a;'>{f['emittente']}</span>", unsafe_allow_html=True)
                st.markdown(f"**💶 Importo:** <span style='font-size: 1.15rem; font-weight: 800; color: #059669;'>{f['importo']:.2f} €</span>", unsafe_allow_html=True)
