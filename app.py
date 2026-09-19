import streamlit as st
import datetime
import sqlite3
import json

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA & STILE
# ---------------------------------------------------------
st.set_page_config(page_title="PetHealth - Libretto Digitale", page_icon="🐾", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stMetric {background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #e9ecef;}
    .angeli-text {font-size: 1.15rem; font-style: italic; color: #555; text-align: center; margin-bottom: 2rem; padding: 15px; background-color: #fdf2f8; border-radius: 10px; border-left: 5px solid #f472b6;}
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
    
    # Aggiornamento automatico per database esistenti
    try:
        c.execute("ALTER TABLE animali ADD COLUMN deceduto INTEGER DEFAULT 0")
        c.execute("ALTER TABLE animali ADD COLUMN data_decesso TEXT")
        c.execute("ALTER TABLE animali ADD COLUMN certificato_morte TEXT")
    except sqlite3.OperationalError:
        pass # Le colonne esistono già
        
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
        SELECT numero_fattura, data_fattura, emittente, descrizione, importo, nome_file 
        FROM fatture WHERE pet_id = ? ORDER BY id DESC
    ''', (pet_id,))
    rows = c.fetchall()
    conn.close()
    return [{"numero": r[0], "data": r[1], "emittente": r[2], "descrizione": r[3], "importo": r[4], "file": r[5]} for r in rows]

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

# Aggiornamento Liste (Helper)
def aggiorna_sessione_animali(email):
    vivi, angeli = carica_tutti_animali_db(email)
    st.session_state.lista_animali_vivi = vivi
    st.session_state.lista_animali_angeli = angeli

# ---------------------------------------------------------
# STEP 1: SCHERMATA LOGIN / REGISTRAZIONE
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.title("Benvenuto su PetHealth 🐾")
    st.markdown("Accedi al tuo profilo o registrati per gestire i libretti dei tuoi animali.")
    
    tab_login, tab_reg = st.tabs(["🔑 Accedi", "📝 Registrati"])
    
    with tab_login:
        with st.form("form_login"):
            email_log = st.text_input("E-mail")
            pass_log = st.text_input("Password", type="password")
            btn_log = st.form_submit_button("Accedi ➔")
            
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
            btn_reg = st.form_submit_button("Crea Account ➔")
            
            if btn_reg:
                if nome_reg and email_reg and pass_reg:
                    if registra_utente_db(nome_reg, email_reg, pass_reg):
                        st.success("✅ Account creato con successo! Ora puoi effettuare il Login.")
                    else:
                        st.error("⚠️ Questa e-mail risulta già registrata!")
                else:
                    st.warning("⚠️ Compila tutti i campi.")

# ---------------------------------------------------------
# MENU LATERALE (SIDEBAR)
# ---------------------------------------------------------
if st.session_state.logged_in and st.session_state.step_corrente != 'registrazione_animale':
    with st.sidebar:
        st.header(f"👤 Ciao, {st.session_state.user_nome}")
        st.divider()
        
        # Sezione Animali Attivi
        if st.session_state.lista_animali_vivi:
            st.subheader("I tuoi animali 🐾")
            pet_dict = {p['nome']: p for p in st.session_state.lista_animali_vivi}
            lista_nomi = list(pet_dict.keys())
            
            nome_attuale = st.session_state.dati_animale.get('nome', '') if not st.session_state.dati_animale.get('deceduto', 0) else ''
            idx_corrente = lista_nomi.index(nome_attuale) if nome_attuale in lista_nomi else 0
            
            animale_selezionato = st.selectbox("Libretto attivo:", lista_nomi, index=idx_corrente)
            
            if st.session_state.step_corrente != 'angeli' and animale_selezionato != nome_attuale:
                nuovo_pet = pet_dict[animale_selezionato]
                st.session_state.dati_animale = nuovo_pet
                prest, ter = carica_dati_sanitari_pet_db(nuovo_pet['id'])
                st.session_state.prestazioni = prest
                st.session_state.terapie = ter
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
                
            if st.session_state.step_corrente == 'angeli':
                if st.button("🔙 Torna alla Dashboard (Animali attivi)", use_container_width=True):
                    st.session_state.step_corrente = 'dashboard'
                    if st.session_state.lista_animali_vivi:
                        st.session_state.dati_animale = st.session_state.lista_animali_vivi[0]
                        prest, ter = carica_dati_sanitari_pet_db(st.session_state.dati_animale['id'])
                        st.session_state.prestazioni = prest
                        st.session_state.terapie = ter
                    st.rerun()

        st.write("")
        if st.button("➕ Aggiungi animale", use_container_width=True):
            st.session_state.step_corrente = 'registrazione_animale'
            st.rerun()
            
        st.divider()
        
        # Pulsante Sezione Angeli
        if st.session_state.lista_animali_angeli:
            if st.button("🕊️ I nostri angeli a 4 zampe", use_container_width=True):
                st.session_state.step_corrente = 'angeli'
                st.rerun()
                
        st.write("")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ---------------------------------------------------------
# STEP 2: REGISTRAZIONE ANIMALE
# ---------------------------------------------------------
if st.session_state.step_corrente == 'registrazione_animale':
    if st.session_state.lista_animali_vivi or st.session_state.lista_animali_angeli:
        if st.button("⬅️ Annulla e torna indietro"):
            st.session_state.step_corrente = 'dashboard' if st.session_state.lista_animali_vivi else 'angeli'
            st.rerun()
            
    st.title("Aggiungi un Animale 🐾")
    
    with st.form("form_animale"):
        nome_pet = st.text_input("Nome dell'animale")
        specie = st.selectbox("Specie", ["Cane 🐶", "Gatto 🐱", "Coniglio 🐰", "Altro"])
        razza = st.text_input("Razza")
        microchip = st.text_input("Numero Microchip")
        submit_pet = st.form_submit_button("Crea Libretto ➔")
        
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
# NUOVA SEZIONE: I NOSTRI ANGELI A 4 ZAMPE 🕊️
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'angeli':
    st.title("I nostri angeli a 4 zampe 🕊️")
    st.markdown(f'<div class="angeli-text">Ricorda {st.session_state.user_nome}, per quanto doloroso, i nostri amici non ci abbandonano mai veramente ma ci proteggono da lassù ❤️</div>', unsafe_allow_html=True)
    
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
                st.markdown(f"### Archivio Clinico di {angelo['nome']}")
                
                # Carica dati in sola lettura
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

# ---------------------------------------------------------
# STEP 3: DASHBOARD PRINCIPALE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'dashboard':
    st.title(f"Libretto di {st.session_state.dati_animale.get('nome', 'Animale')} 🐾")
    st.caption(f"Specie: {st.session_state.dati_animale.get('specie')} | Razza: {st.session_state.dati_animale.get('razza')} | Microchip: {st.session_state.dati_animale.get('microchip')}")
    
    st.markdown("### ⚡ Azioni Rapide")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("➕ Nuova Visita", use_container_width=True):
            st.session_state.step_corrente = 'aggiungi_prestazione'
            st.rerun()
    with col_btn2:
        if st.button("💊 Nuova Terapia", use_container_width=True):
            st.session_state.step_corrente = 'aggiungi_terapia'
            st.rerun()
    with col_btn3:
        if st.button("🧾 Carica Fattura", use_container_width=True):
            st.session_state.step_corrente = 'aggiungi_fattura'
            st.rerun()

    st.divider()

    # --- SEZIONE TERAPIE E VISITE ---
    st.subheader("💊 Terapie & Farmaci in Corso")
    if len(st.session_state.terapie) == 0:
        st.info("Nessun farmaco o terapia attiva al momento.")
    else:
        for t in reversed(st.session_state.terapie):
            st.markdown(f"**{t.get('Farmaco', 'Farmaco')}** - Inizio: {t.get('Data_Inizio', 'N/D')}")
            st.caption(f"Prescritto da: {t.get('Veterinario', 'N/D')} | Stato: {t.get('Stato', '')}")

    st.divider()

    st.subheader("📜 Cartella Clinica & Visite Veterinarie")
    if len(st.session_state.prestazioni) == 0:
        st.info("💡 Nessuna visita in archivio.")
    else:
        for item in reversed(st.session_state.prestazioni):
            with st.expander(f"🔍 {item.get('Data', 'N/D')} - {item.get('Prestazione', 'Visita')}"):
                st.write(f"**🏥 Clinica / Vet:** {item.get('Veterinario', 'N/D')}")
                st.write(f"**📋 Note Cliniche:** {item.get('Dettagli', '')}")

    st.divider()

    # --- ZONA VETERINARIO: REGISTRA DECESSO ---
    with st.expander("⚠️ Area Riservata Medico Veterinario (Registra Decesso)"):
        st.warning("L'azione sottostante sposterà permanentemente la cartella clinica di questo animale nella sezione 'I nostri angeli a 4 zampe'.")
        with st.form("form_decesso"):
            data_dec = st.date_input("Data del decesso", datetime.date.today())
            cert_morte = st.file_uploader("Allega Certificato di Morte (PDF/Foto)", type=['pdf', 'png', 'jpg'])
            pin_vet_dec = st.text_input("PIN Veterinario per confermare (es. 1234)", type="password")
            submit_dec = st.form_submit_button("Conferma Decesso")
            
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
# STEP 4A: INSERIMENTO PRESTAZIONE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_prestazione':
    if st.button("⬅️ Torna alla Dashboard"):
        st.session_state.step_corrente = 'dashboard'
        st.rerun()
    st.title(f"🩺 Registra Visita per {st.session_state.dati_animale['nome']}")
    tipo_prestazione = st.selectbox("Tipo di Prestazione", ["Visita Generale", "Vaccino", "Altro"])
    data_esecuzione = st.date_input("Data Visita")
    nome_vet = st.text_input("Nome Clinica o Veterinario")
    dettagli = st.text_area("📝 Dettagli")
    if st.button("Salva Prestazione"):
        nuova_prestazione = {"Data": data_esecuzione.strftime("%d/%m/%Y"), "Prestazione": tipo_prestazione, "Veterinario": nome_vet, "Dettagli": dettagli}
        st.session_state.prestazioni.append(nuova_prestazione)
        salva_sanitari_db(st.session_state.dati_animale['id'], st.session_state.prestazioni, st.session_state.terapie)
        st.session_state.step_corrente = 'dashboard'
        st.rerun()

# ---------------------------------------------------------
# STEP 4B: INSERIMENTO TERAPIA
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_terapia':
    if st.button("⬅️ Torna alla Dashboard"):
        st.session_state.step_corrente = 'dashboard'
        st.rerun()
    st.title("💊 Registra Terapia")
    farmaco = st.text_input("Farmaco")
    data_in = st.date_input("Data Inizio")
    if st.button("Salva Terapia"):
        st.session_state.terapie.append({"Farmaco": farmaco, "Data_Inizio": data_in.strftime("%d/%m/%Y")})
        salva_sanitari_db(st.session_state.dati_animale['id'], st.session_state.prestazioni, st.session_state.terapie)
        st.session_state.step_corrente = 'dashboard'
        st.rerun()

# ---------------------------------------------------------
# STEP 4C: INSERIMENTO FATTURA
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_fattura':
    if st.button("⬅️ Torna alla Dashboard"):
        st.session_state.step_corrente = 'dashboard'
        st.rerun()
    st.title("🧾 Registra Fattura")
    num_fattura = st.text_input("N° Fattura")
    importo = st.number_input("Importo (€)", min_value=0.0)
    if st.button("Salva Fattura") and num_fattura:
        salva_fattura_db(st.session_state.dati_animale['id'], num_fattura, "Oggi", "Vet", "Desc", importo, "")
        st.session_state.step_corrente = 'dashboard'
        st.rerun()
