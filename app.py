import streamlit as st
import datetime
import sqlite3
import json

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA & STILE PREMIUM "WOW"
# ---------------------------------------------------------
st.set_page_config(
    page_title="PetHealth - Libretto Digitale", 
    page_icon="🐾", 
    layout="centered"
)

# CSS Custom con Google Fonts, Gradients, Cards ed effetti Hover
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Reset e Tipografia Globale */
    html, body, [class*="css"], div, p, span, button, input, select, textarea {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* Nascondi Elementi di Default Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Background App */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }

    /* Hero Card Superiore */
    .hero-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 28px;
        border-radius: 24px;
        box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        margin-bottom: 6px !important;
        background: linear-gradient(90deg, #ffffff, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 500;
        margin: 0;
    }

    /* Card Personalizzate */
    .custom-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        margin-bottom: 16px;
    }

    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.08);
    }

    /* Banner Ricordo Angeli */
    .angeli-text {
        font-size: 1.05rem;
        font-style: italic;
        color: #831843;
        text-align: center;
        margin-bottom: 2rem;
        padding: 22px;
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
        border-radius: 20px;
        border-left: 6px solid #ec4899;
        box-shadow: 0 10px 15px -3px rgba(236, 72, 153, 0.1);
    }

    /* Pulsanti */
    .stButton > button {
        border-radius: 14px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.65rem 1.25rem !important;
        transition: all 0.25s ease !important;
        border: 1px solid #e2e8f0 !important;
        background: #ffffff !important;
        color: #1e293b !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }

    .stButton > button:hover {
        border-color: #2563eb !important;
        color: #2563eb !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.12) !important;
        transform: translateY(-1px) !important;
    }

    /* Pulsanti dentro i Form (Primary Call to Action) */
    div[data-testid="stForm"] .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    }

    div[data-testid="stForm"] .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
        transform: translateY(-1px) !important;
    }

    /* Sidebar Luxury */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b !important;
    }

    section[data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.18) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        color: #ffffff !important;
    }

    /* Styling Schede (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid #e2e8f0;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 10px 22px;
        font-weight: 600;
        color: #64748b;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #2563eb !important;
        border-bottom: 3px solid #2563eb !important;
    }

    /* Input & Form Styling */
    .stTextInput > div > div > input, .stSelectbox > div > div, .stTextArea textarea, .stNumberInput > div > div > input {
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        padding: 10px 14px !important;
        background-color: #ffffff !important;
    }

    .stTextInput > div > div > input:focus, .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }

    /* Badges Eleganti */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-emerald { background-color: #d1fae5; color: #065f46; }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }
    .badge-rose { background-color: #ffe4e6; color: #9f1239; }
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
        <div style="text-align: center; padding: 2.5rem 0 1.5rem 0;">
            <div style="display: inline-block; padding: 8px 18px; background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%); border-radius: 50px; margin-bottom: 12px; border: 1px solid #bfdbfe;">
                <span style="color: #1e40af; font-weight: 700; font-size: 0.82rem; letter-spacing: 0.05em;">PLATTAFORMA VETERINARIA DIGITALE</span>
            </div>
            <h1 style="font-size: 2.8rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">PetHealth 🐾</h1>
            <p style="color: #64748b; font-size: 1.05rem; max-width: 480px; margin: 0 auto;">
                Il libretto sanitario digitale progettato con eleganza e precisione per i tuoi compagni di vita.
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
            btn_reg = st.form_submit_button("Crea il tuo Account ➔", use_container_width=True)
            
            if btn_reg:
                if nome_reg and email_reg and pass_reg:
                    if registra_utente_db(nome_reg, email_reg, pass_reg):
                        st.success("✅ Account creato con successo! Ora puoi effettuare il Login.")
                    else:
                        st.error("⚠️ Questa e-mail risulta già registrata!")
                else:
                    st.warning("⚠️ Compila tutti i campi.")

# ---------------------------------------------------------
# MENU LATERALE (SIDEBAR LUXURY)
# ---------------------------------------------------------
if st.session_state.logged_in and st.session_state.step_corrente != 'registrazione_animale':
    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 10px 0 20px 0;">
                <span style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Bentornato</span>
                <h2 style="font-size: 1.4rem; color: #ffffff; margin: 0;">{st.session_state.user_nome}</h2>
            </div>
        """, unsafe_allow_html=True)
        st.divider()
        
        if st.session_state.lista_animali_vivi:
            st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #94a3b8;'>SELEZIONA ANIMALE</p>", unsafe_allow_html=True)
            pet_dict = {p['nome']: p for p in st.session_state.lista_animali_vivi}
            lista_nomi = list(pet_dict.keys())
            
            nome_attuale = st.session_state.dati_animale.get('nome', '') if not st.session_state.dati_animale.get('deceduto', 0) else ''
            idx_corrente = lista_nomi.index(nome_attuale) if nome_attuale in lista_nomi else 0
            
            animale_selezionato = st.selectbox("Libretto attivo:", lista_nomi, index=idx_corrente, label_visibility="collapsed")
            
            if st.session_state.step_corrente != 'angeli' and animale_selezionato != nome_attuale:
                nuovo_pet = pet_dict[animale_selezionato]
                st.session_state.dati_animale = nuovo_pet
                prest, ter = carica_dati_sanitari_pet_db(nuovo_pet['id'])
                st.session_state.prestazioni = prest
                st.session_state.terapie = ter
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
            
            # --- NAVIGAZIONE ---
            if st.session_state.step_corrente != 'angeli':
                st.divider()
                st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #94a3b8;'>SEZIONI LIBRETTO</p>", unsafe_allow_html=True)
                if st.button("🏠 Riepilogo Dashboard", use_container_width=True):
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
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ---------------------------------------------------------
# STEP: REGISTRAZIONE ANIMALE
# ---------------------------------------------------------
if st.session_state.step_corrente == 'registrazione_animale':
    if st.session_state.lista_animali_vivi or st.session_state.lista_animali_angeli:
        if st.button("⬅️ Annulla e torna indietro"):
            st.session_state.step_corrente = 'dashboard' if st.session_state.lista_animali_vivi else 'angeli'
            st.rerun()
            
    st.markdown("""
        <div class="hero-card">
            <span class="badge badge-emerald">Nuovo Profilo</span>
            <h1 class="hero-title">Aggiungi un Animale 🐾</h1>
            <p class="hero-subtitle">Crea un nuovo libretto sanitario digitale in pochi semplici passaggi</p>
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
            <div style="display: inline-block; padding: 6px 16px; background: #fce7f3; border-radius: 50px; margin-bottom: 10px;">
                <span style="color: #be185d; font-weight: 700; font-size: 0.82rem; letter-spacing: 0.05em;">IN MEMORIA PERMANENTE</span>
            </div>
            <h1 style="font-size: 2.5rem; font-weight: 800; color: #831843; margin-bottom: 8px;">I nostri angeli a 4 zampe 🕊️</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="angeli-text">Ricorda {st.session_state.user_nome}, per quanto doloroso, i nostri compagni di vita non ci abbandonano mai veramente. Il loro ricordo resta al sicuro qui con noi ❤️</div>', unsafe_allow_html=True)
    
    if not st.session_state.lista_animali_angeli:
        st.info("Non ci sono animali registrati in questa sezione.")
    else:
        for angelo in st.session_state.lista_animali_angeli:
            with st.expander(f"🕊️ {angelo['nome']} ({angelo['specie']} - {angelo['razza']})", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Data della scomparsa:** {angelo['data_decesso']}")
                with col2:
                    if angelo['certificato_morte'] and angelo['certificato_morte'] != "Nessun file":
                        st.write(f"**Certificato di Morte:** 📎 {angelo['certificato_morte']}")
                    else:
                        st.write("**Certificato di Morte:** Non allegato")
                
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
                with st.popover(f"🔄 Annulla registrazione decesso di {angelo['nome']}"):
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
            <span class="badge badge-emerald">Libretto Sanitario Attivo</span>
            <h1 class="hero-title">{st.session_state.dati_animale.get('nome', 'Animale')}</h1>
            <p class="hero-subtitle">
                {st.session_state.dati_animale.get('specie')} &bull; 
                Razza: <strong>{st.session_state.dati_animale.get('razza') or 'Non specificata'}</strong> &bull; 
                Microchip: <strong>{st.session_state.dati_animale.get('microchip') or 'Non inserito'}</strong>
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="custom-card">
                <span class="badge badge-purple">Farmaci e Terapie</span>
                <h3 style="margin-top: 5px; margin-bottom: 15px;">💊 In somministrazione</h3>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.terapie) == 0:
            st.write("Nessun farmaco attivo al momento.")
        else:
            for t in reversed(st.session_state.terapie[-3:]):
                st.markdown(f"🔹 **{t.get('Farmaco', 'Farmaco')}** *(dal {t.get('Data_Inizio', 'N/D')})*")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="custom-card">
                <span class="badge badge-blue">Storico Clinico</span>
                <h3 style="margin-top: 5px; margin-bottom: 15px;">📜 Ultime Visite</h3>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.prestazioni) == 0:
            st.write("Nessuna visita recente in archivio.")
        else:
            for p in reversed(st.session_state.prestazioni[-3:]):
                st.markdown(f"🔸 **{p.get('Data', 'N/D')}** - {p.get('Prestazione', 'Visita')}")
        
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
            <span class="badge badge-blue">Cartella Clinica</span>
            <h1 class="hero-title">Visite & Prestazioni</h1>
            <p class="hero-subtitle">Paziente: <strong>{st.session_state.dati_animale['nome']}</strong> &bull; Registra diagnosi, controlli e interventi</p>
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
                st.markdown(f"### 🩺 {item.get('Prestazione', 'Visita')} - <span style='color: #2563eb;'>{item.get('Data', 'N/D')}</span>", unsafe_allow_html=True)
                st.write(f"**🏥 Clinica / Medico:** {item.get('Veterinario', 'N/D')}")
                if item.get('Dettagli'):
                    st.write(f"**📋 Dettagli Medici:** {item.get('Dettagli')}")

# ---------------------------------------------------------
# PAGINA: GESTIONE TERAPIE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'pagina_terapie':
    st.markdown(f"""
        <div class="hero-card">
            <span class="badge badge-purple">Farmacologia & Cura</span>
            <h1 class="hero-title">Gestione Terapie</h1>
            <p class="hero-subtitle">Paziente: <strong>{st.session_state.dati_animale['nome']}</strong> &bull; Prescrizioni, dosaggi e piani terapeutici</p>
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
                st.markdown(f"### 💊 {t.get('Farmaco', 'Farmaco')}")
                st.write(f"**🗓️ Data Inizio Somministrazione:** {t.get('Data_Inizio', 'N/D')}")

# ---------------------------------------------------------
# PAGINA: GESTIONE FATTURE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'pagina_fatture':
    st.markdown(f"""
        <div class="hero-card">
            <span class="badge badge-rose">Contabilità & Documenti</span>
            <h1 class="hero-title">Fatture e Ricevute</h1>
            <p class="hero-subtitle">Paziente: <strong>{st.session_state.dati_animale['nome']}</strong> &bull; Archivio spese veterinarie e rendicontazione</p>
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
                st.markdown(f"### 🧾 Fattura N° {f['numero']} <span style='font-size: 1rem; color: #64748b;'>del {f['data']}</span>", unsafe_allow_html=True)
                st.write(f"**🏥 Emittente:** {f['emittente']}")
                st.markdown(f"**💶 Importo:** <span style='font-size: 1.2rem; font-weight: 700; color: #059669;'>{f['importo']:.2f} €</span>", unsafe_allow_html=True)
