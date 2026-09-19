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
            FOREIGN KEY(user_email) REFERENCES utenti(email)
        )
    ''')
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

# --- Funzioni DB Utenti ---
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

# --- Funzioni DB Animali ---
def salva_animale_db(email, nome, specie, razza, microchip):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("INSERT INTO animali (user_email, nome, specie, razza, microchip) VALUES (?, ?, ?, ?, ?)",
              (email, nome, specie, razza, microchip))
    pet_id = c.lastrowid
    c.execute("INSERT INTO dati_sanitari VALUES (?, ?, ?)", (pet_id, json.dumps([]), json.dumps([])))
    conn.commit()
    conn.close()
    return pet_id

def carica_tutti_animali_db(email):
    """Carica la lista di tutti gli animali di un utente."""
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute("SELECT id, nome, specie, razza, microchip FROM animali WHERE user_email = ?", (email,))
    rows = c.fetchall()
    conn.close()
    pets = []
    for r in rows:
        pets.append({
            "id": r[0], "nome": r[1], "specie": r[2], "razza": r[3], "microchip": r[4]
        })
    return pets

def carica_dati_sanitari_pet_db(pet_id):
    """Carica le prestazioni e le terapie di uno specifico animale."""
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

# --- Funzioni DB Fatture ---
def salva_fattura_db(pet_id, num, data, emittente, desc, importo, file_name):
    conn = sqlite3.connect('pethealth.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO fatture (pet_id, numero_fattura, data_fattura, emittente, descrizione, importo, nome_file)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (pet_id, num, data, emittente, desc, importo, file_name))
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
    fatture_list = []
    for r in rows:
        fatture_list.append({
            "numero": r[0], "data": r[1], "emittente": r[2], 
            "descrizione": r[3], "importo": r[4], "file": r[5]
        })
    return fatture_list

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
if 'lista_animali' not in st.session_state:
    st.session_state.lista_animali = []
if 'dati_animale' not in st.session_state:
    st.session_state.dati_animale = {}
if 'prestazioni' not in st.session_state:
    st.session_state.prestazioni = []
if 'terapie' not in st.session_state:
    st.session_state.terapie = []

# ---------------------------------------------------------
# STEP 1: SCHERMATA LOGIN / REGISTRAZIONE UTENTE
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.title("Benvenuto su PetHealth 🐾")
    st.markdown("Accedi al tuo profilo o registrati per gestire il libretto dei tuoi animali.")
    
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
                    
                    # Carica TUTTI gli animali dell'utente
                    pets = carica_tutti_animali_db(email_log)
                    if pets:
                        st.session_state.lista_animali = pets
                        st.session_state.dati_animale = pets[0] # Imposta il primo come attivo di default
                        prest, ter = carica_dati_sanitari_pet_db(pets[0]['id'])
                        st.session_state.prestazioni = prest
                        st.session_state.terapie = ter
                        st.session_state.step_corrente = 'dashboard'
                    else:
                        st.session_state.lista_animali = []
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
# GESTIONE MENU LATERALE (SIDEBAR) - VISIBILE DOPO LOGIN
# ---------------------------------------------------------
if st.session_state.logged_in and st.session_state.lista_animali and st.session_state.step_corrente != 'registrazione_animale':
    with st.sidebar:
        st.header(f"👤 Ciao, {st.session_state.user_nome}")
        st.divider()
        st.subheader("I tuoi animali 🐾")
        
        # Dizionario per mappare i nomi agli oggetti pet interi
        pet_dict = {p['nome']: p for p in st.session_state.lista_animali}
        lista_nomi = list(pet_dict.keys())
        
        # Trova l'indice dell'animale attualmente attivo
        nome_attuale = st.session_state.dati_animale.get('nome', '')
        idx_corrente = lista_nomi.index(nome_attuale) if nome_attuale in lista_nomi else 0
        
        # Selectbox per cambiare animale
        animale_selezionato = st.selectbox("Seleziona il libretto attivo:", lista_nomi, index=idx_corrente)
        
        # Se l'utente ha cambiato animale nella selectbox, aggiorna i dati e ricarica
        if animale_selezionato != nome_attuale:
            nuovo_pet = pet_dict[animale_selezionato]
            st.session_state.dati_animale = nuovo_pet
            prest, ter = carica_dati_sanitari_pet_db(nuovo_pet['id'])
            st.session_state.prestazioni = prest
            st.session_state.terapie = ter
            # Se eravamo in una schermata di inserimento, torniamo in dashboard per sicurezza
            st.session_state.step_corrente = 'dashboard'
            st.rerun()
            
        st.write("")
        if st.button("➕ Aggiungi un altro animale", use_container_width=True):
            st.session_state.step_corrente = 'registrazione_animale'
            st.rerun()
            
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ---------------------------------------------------------
# STEP 2: REGISTRAZIONE ANIMALE (Primo o Successivi)
# ---------------------------------------------------------
if st.session_state.step_corrente == 'registrazione_animale':
    if len(st.session_state.lista_animali) > 0:
        if st.button("⬅️ Annulla e torna alla Dashboard"):
            st.session_state.step_corrente = 'dashboard'
            st.rerun()
            
    st.title("Aggiungi un Animale 🐾")
    st.markdown("Inserisci i dati del tuo compagno di avventure per creare il suo libretto digitale.")
    
    with st.form("form_animale"):
        nome_pet = st.text_input("Nome dell'animale")
        specie = st.selectbox("Specie", ["Cane 🐶", "Gatto 🐱", "Coniglio 🐰", "Altro"])
        razza = st.text_input("Razza")
        microchip = st.text_input("Numero Microchip")
        submit_pet = st.form_submit_button("Crea Libretto ➔")
        
        if submit_pet and nome_pet:
            # Salva sul DB
            pet_id = salva_animale_db(st.session_state.user_email, nome_pet, specie, razza, microchip)
            
            # Aggiorna la lista di tutti gli animali
            st.session_state.lista_animali = carica_tutti_animali_db(st.session_state.user_email)
            
            # Imposta il nuovo animale come quello attivo
            st.session_state.dati_animale = {
                "id": pet_id, "nome": nome_pet, "specie": specie, "razza": razza, "microchip": microchip
            }
            st.session_state.prestazioni = []
            st.session_state.terapie = []
            
            st.session_state.step_corrente = 'dashboard'
            st.rerun()

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

    # --- SEZIONE TERAPIE ---
    st.subheader("💊 Terapie & Farmaci in Corso")
    if len(st.session_state.terapie) == 0:
        st.info("Nessun farmaco o terapia attiva al momento.")
    else:
        for t in reversed(st.session_state.terapie):
            data_t = t.get('Data_Inizio', 'N/D')
            farmaco = t.get('Farmaco', 'Farmaco')
            stato_t = t.get('Stato', '🔴 Non certificato')
            icona_t = stato_t.split()[0] if stato_t else "🔴"
            
            with st.expander(f"💊 {farmaco} - Inizio: {data_t} ({icona_t})"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**🏥 Prescritto da:** {t.get('Veterinario', 'N/D')}")
                    st.write(f"**⏳ Durata Cura:** {t.get('Durata', 'N/D')}")
                with c2:
                    st.write(f"**🛡️ Certificazione:** {stato_t}")
                st.markdown("**📋 Posologia & Istruzioni:**")
                st.info(t.get('Posologia', 'Nessuna istruzione inserita.'))

    st.divider()

    # --- SEZIONE VISITE & REFERTI ALLEGATI ---
    st.subheader("📜 Cartella Clinica & Visite Veterinarie")
    if len(st.session_state.prestazioni) == 0:
        st.info("💡 Nessuna visita in archivio.")
    else:
        for real_idx, item in enumerate(reversed(st.session_state.prestazioni)):
            original_idx = len(st.session_state.prestazioni) - 1 - real_idx
            
            data = item.get('Data', 'N/D')
            prestazione = item.get('Prestazione', 'Visita')
            stato = item.get('Stato', '🔴 Non certificato')
            vet = item.get('Veterinario', 'N/D')
            scadenza = item.get('Scadenza/Richiamo', 'Non prevista')
            dettagli = item.get('Dettagli', 'Nessun dettaglio aggiuntivo.')
            allegati = item.get('Allegati', [])
            
            icona_stato = stato.split()[0] if stato else "🔴"
            titolo_scheda = f"🔍 {data} - {prestazione} ({icona_stato})"
            
            with st.expander(titolo_scheda):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**🏥 Clinica / Vet:** {vet}")
                    st.write(f"**🛡️ Stato:** {stato}")
                with col2:
                    st.write(f"**📅 Prossimo Richiamo:** {scadenza}")
                
                st.markdown("**📋 Note Cliniche:**")
                st.info(dettagli)
                
                if allegati:
                    st.markdown("**📎 Referti salvati:**")
                    for doc in allegati:
                        st.caption(f"📄 {doc.get('nome')}")

    st.divider()

    # --- SEZIONE FATTURE ---
    st.subheader("🧾 Fatture e Ricevute Sanitarie")
    lista_fatture = carica_fatture_db(st.session_state.dati_animale['id'])
    
    if not lista_fatture:
        st.info("Nessuna fattura registrata per questo animale.")
    else:
        totale_speso = sum(f['importo'] for f in lista_fatture)
        st.metric(label=f"💰 Totale Spese Sanitarie per {st.session_state.dati_animale['nome']}", value=f"{totale_speso:.2f} €")
        
        for f in lista_fatture:
            with st.expander(f"📄 Fattura N° {f['numero']} del {f['data']} - {f['importo']:.2f} €"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    st.write(f"**🏥 Emittente:** {f['emittente']}")
                    st.write(f"**📝 Descrizione:** {f['descrizione']}")
                with col_f2:
                    st.write(f"**💶 Importo Totale:** {f['importo']:.2f} €")
                    st.write(f"**📎 Allegato:** {f['file'] if f['file'] else 'Nessun file'}")

# ---------------------------------------------------------
# STEP 4A: INSERIMENTO PRESTAZIONE VETERINARIA
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_prestazione':
    if st.button("⬅️ Torna alla Dashboard"):
        st.session_state.step_corrente = 'dashboard'
        st.rerun()
        
    st.title(f"🩺 Registra Visita per {st.session_state.dati_animale['nome']}")
    
    col_a, col_b = st.columns(2)
    with col_a:
        tipo_prestazione = st.selectbox("Tipo di Prestazione", ["Visita Generale", "Vaccino", "Antiparassitario", "Intervento Chirurgico", "Esami del Sangue / RX", "Ecografia", "Altro"])
    with col_b:
        data_esecuzione = st.date_input("Data Visita", datetime.date.today())
        
    nome_vet = st.text_input("Nome Clinica o Veterinario")
    dettagli_prestazione = st.text_area("📝 Dettagli della visita / Esito clinico", height=100)
    
    file_iniziale = st.file_uploader("Allegato Referto (Opzionale)", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    da_ripetere = st.checkbox("🔄 Richiede un controllo futuro o richiamo?")
    data_scadenza = st.date_input("📅 Data richiamo", datetime.date.today() + datetime.timedelta(days=365)) if da_ripetere else None
    
    certifica = st.checkbox("Certifica ora con PIN Veterinario")
    stato_certificazione = "🔴 Non Certificato (Dichiarato dal proprietario)"
    if certifica:
        pin_vet = st.text_input("PIN Veterinario (test: 1234)", type="password")
        if pin_vet == "1234":
            st.success("✅ PIN Corretto.")
            stato_certificazione = "🟢 Certificato Ufficialmente"
        elif pin_vet != "":
            st.error("❌ PIN Errato.")
    
    st.divider()
    if st.button("Salva Prestazione"):
        if not nome_vet:
            st.error("⚠️ Inserisci il nome del veterinario!")
        else:
            lista_allegati_iniziali = [{"nome": file_iniziale.name}] if file_iniziale else []
            nuova_prestazione = {
                "Data": data_esecuzione.strftime("%d/%m/%Y"),
                "Prestazione": tipo_prestazione,
                "Veterinario": nome_vet,
                "Dettagli": dettagli_prestazione if dettagli_prestazione else "Nessuna nota.",
                "Scadenza/Richiamo": data_scadenza.strftime("%d/%m/%Y") if da_ripetere else "Non previsto",
                "Stato": stato_certificazione,
                "Allegati": lista_allegati_iniziali
            }
            st.session_state.prestazioni.append(nuova_prestazione)
            salva_sanitari_db(st.session_state.dati_animale['id'], st.session_state.prestazioni, st.session_state.terapie)
            st.session_state.step_corrente = 'dashboard'
            st.rerun()

# ---------------------------------------------------------
# STEP 4B: INSERIMENTO TERAPIA / FARMACO
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_terapia':
    if st.button("⬅️ Torna alla Dashboard"):
        st.session_state.step_corrente = 'dashboard'
        st.rerun()
        
    st.title(f"💊 Registra Terapia per {st.session_state.dati_animale['nome']}")
    nome_farmaco = st.text_input("Nome del Farmaco / Medicinale")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        data_inizio = st.date_input("Data Inizio Terapia", datetime.date.today())
    with col_t2:
        durata_terapia = st.text_input("Durata della Cura")
        
    nome_vet_prescrittore = st.text_input("Veterinario Prescrittore")
    posologia = st.text_area("📋 Posologia & Istruzioni", height=100)
    
    certifica_t = st.checkbox("Fai certificare con PIN Veterinario")
    stato_certificazione_t = "🔴 Non Certificato (Dichiarato dal proprietario)"
    if certifica_t:
        pin_vet_t = st.text_input("PIN Veterinario (test: 1234)", type="password")
        if pin_vet_t == "1234":
            st.success("✅ PIN Corretto.")
            stato_certificazione_t = "🟢 Certificato Ufficialmente"
        elif pin_vet_t != "":
            st.error("❌ PIN Errato.")
            
    st.divider()
    if st.button("Salva Terapia"):
        if not nome_farmaco or not nome_vet_prescrittore:
            st.error("⚠️ Compila tutti i campi obbligatori!")
        else:
            nuova_terapia = {
                "Farmaco": nome_farmaco,
                "Data_Inizio": data_inizio.strftime("%d/%m/%Y"),
                "Durata": durata_terapia if durata_terapia else "Non specificata",
                "Veterinario": nome_vet_prescrittore,
                "Posologia": posologia if posologia else "Seguire indicazioni.",
                "Stato": stato_certificazione_t
            }
            st.session_state.terapie.append(nuova_terapia)
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
        
    st.title(f"🧾 Registra Fattura per {st.session_state.dati_animale['nome']}")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        num_fattura = st.text_input("N° Fattura / Documento")
        emittente = st.text_input("Clinica / Veterinario Emittente")
    with col_f2:
        data_fattura = st.date_input("Data Emissione", datetime.date.today())
        importo = st.number_input("Importo Totale (€)", min_value=0.0, step=0.5, format="%.2f")
        
    descrizione_fattura = st.text_input("Descrizione / Servizi resi")
    file_fattura = st.file_uploader("Carica il file (PDF o Foto)", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    st.divider()
    if st.button("💾 Salva Fattura"):
        if not num_fattura or importo <= 0:
            st.error("⚠️ Inserisci almeno un numero di fattura e un importo valido!")
        else:
            nome_file_salvato = file_fattura.name if file_fattura else "Nessun file"
            salva_fattura_db(
                st.session_state.dati_animale['id'],
                num_fattura,
                data_fattura.strftime("%d/%m/%Y"),
                emittente if emittente else "Non specificato",
                descrizione_fattura if descrizione_fattura else "Prestazioni Sanitarie",
                importo,
                nome_file_salvato
            )
            st.success("✅ Fattura salvata correttamente!")
            st.session_state.step_corrente = 'dashboard'
            st.rerun()
