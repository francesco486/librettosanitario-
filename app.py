import streamlit as st
import datetime
import pandas as pd

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA & STILE
# ---------------------------------------------------------
st.set_page_config(page_title="PetHealth - Libretto Digitale", page_icon="🐾", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .btn-salva>button {width: 100%; border-radius: 8px; background-color: #28a745; color: white; font-weight: bold;}
    .btn-indietro>button {width: 100%; border-radius: 8px; background-color: #6c757d; color: white; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MEMORIA E SESSION STATE
# ---------------------------------------------------------
if 'step_corrente' not in st.session_state:
    st.session_state.step_corrente = 'registrazione_utente'
if 'dati_utente' not in st.session_state:
    st.session_state.dati_utente = {}
if 'dati_animale' not in st.session_state:
    st.session_state.dati_animale = {}
if 'prestazioni' not in st.session_state:
    st.session_state.prestazioni = []
if 'terapie' not in st.session_state:
    st.session_state.terapie = []

# ---------------------------------------------------------
# STEP 1: REGISTRAZIONE PROPRIETARIO
# ---------------------------------------------------------
if st.session_state.step_corrente == 'registrazione_utente':
    st.title("Benvenuto su PetHealth 🐾")
    st.markdown("Crea il tuo account per tenere traccia della salute del tuo animale.")
    
    with st.form("form_utente"):
        nome = st.text_input("Il tuo Nome e Cognome")
        email = st.text_input("La tua E-mail")
        password = st.text_input("Crea una Password", type="password")
        submit = st.form_submit_button("Continua ➔")
        
        if submit and nome and email and password:
            st.session_state.dati_utente = {"nome": nome, "email": email}
            st.session_state.step_corrente = 'registrazione_animale'
            st.rerun()

# ---------------------------------------------------------
# STEP 2: INSERIMENTO ANIMALE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'registrazione_animale':
    st.title(f"Ciao {st.session_state.dati_utente.get('nome', '')}! 👋")
    st.markdown("Parlaci un po' del tuo compagno di avventure.")
    
    with st.form("form_animale"):
        nome_pet = st.text_input("Nome dell'animale")
        specie = st.selectbox("Specie", ["Cane 🐶", "Gatto 🐱", "Altro"])
        razza = st.text_input("Razza")
        microchip = st.text_input("Numero Microchip")
        submit_pet = st.form_submit_button("Crea Libretto ➔")
        
        if submit_pet and nome_pet:
            st.session_state.dati_animale = {"nome": nome_pet, "specie": specie, "razza": razza, "microchip": microchip}
            st.session_state.step_corrente = 'dashboard'
            st.rerun()

# ---------------------------------------------------------
# STEP 3: DASHBOARD PRINCIPALE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'dashboard':
    st.title(f"Libretto Sanitario di {st.session_state.dati_animale.get('nome', 'Animale')} 🐾")
    
    st.markdown("### ⚡ Azioni Rapide")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ Nuova Prestazione / Visita", use_container_width=True):
            st.session_state.step_corrente = 'aggiungi_prestazione'
            st.rerun()
    with col_btn2:
        if st.button("💊 Nuova Terapia / Farmaco", use_container_width=True):
            st.session_state.step_corrente = 'aggiungi_terapia'
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
        st.info("💡 Nessuna visita in archivio. Clicca su '➕ Nuova Prestazione / Visita' in alto per registrarne una!")
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
            
            with st.expander(titolo_scheda, expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**🏥 Clinica / Vet:** {vet}")
                    st.write(f"**🛡️ Stato:** {stato}")
                with col2:
                    st.write(f"**📅 Prossimo Richiamo:** {scadenza}")
                
                st.markdown("**📋 Note Cliniche:**")
                st.info(dettagli)
                
                st.markdown("---")
                st.markdown("### 📎 Referti ed Esami Allegati")
                if allegati:
                    for file_idx, doc in enumerate(allegati):
                        st.download_button(
                            label=f"📄 Scarica {doc['nome']}",
                            data=doc['bytes'],
                            file_name=doc['nome'],
                            mime=doc['tipo'],
                            key=f"dl_{original_idx}_{file_idx}"
                        )
                else:
                    st.caption("Nessun documento allegato a questa visita.")
                
                st.markdown("#### 📤 Carica un nuovo referto PDF/Foto per questa visita")
                nuovo_file = st.file_uploader(
                    "Seleziona un file dal PC o dallo smartphone (Ecografia, Esami, RX)", 
                    type=['pdf', 'png', 'jpg', 'jpeg'], 
                    key=f"upload_retroactive_{original_idx}"
                )
                
                if nuovo_file is not None:
                    if st.button("💾 Salva Referto in Questa Visita", key=f"btn_save_doc_{original_idx}"):
                        file_data = {
                            "nome": nuovo_file.name,
                            "bytes": nuovo_file.getvalue(),
                            "tipo": nuovo_file.type
                        }
                        if 'Allegati' not in st.session_state.prestazioni[original_idx]:
                            st.session_state.prestazioni[original_idx]['Allegati'] = []
                            
                        st.session_state.prestazioni[original_idx]['Allegati'].append(file_data)
                        st.success(f"✅ Referto '{nuovo_file.name}' salvato con successo!")
                        st.rerun()

# ---------------------------------------------------------
# STEP 4A: INSERIMENTO PRESTAZIONE VETERINARIA
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_prestazione':
    # Pulsante di ritorno rapido in alto
    if st.button("⬅️ Torna alla Dashboard (Annulla)", key="top_back_prestazione"):
        st.session_state.step_corrente = 'dashboard'
        st.rerun()
        
    st.title("🩺 Registra Prestazione Veterinaria")
    st.markdown(f"Aggiungi una visita, vaccino o controllo per **{st.session_state.dati_animale.get('nome', 'il tuo pet')}**.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        tipo_prestazione = st.selectbox("Tipo di Prestazione", ["Visita Generale", "Vaccino", "Antiparassitario", "Intervento Chirurgico", "Esami del Sangue / RX", "Ecografia", "Altro"])
    with col_b:
        data_esecuzione = st.date_input("Data Visita", datetime.date.today())
        
    nome_vet = st.text_input("Nome Clinica o Veterinario", placeholder="Es. Clinica Veterinaria San Siro - Dr. Rossi")
    
    dettagli_prestazione = st.text_area(
        "📝 Dettagli della visita / Esito clinico", 
        placeholder="Scrivi qui cosa è stato fatto durante la visita...",
        height=100
    )
    
    st.markdown("### 📎 Allegati Contestuali (Opzionale)")
    file_iniziale = st.file_uploader("Hai già il referto pronto? Caricalo ora (altrimenti potrai farlo in seguito)", type=['pdf', 'png', 'jpg', 'jpeg'], key="upload_iniziale")
    
    st.divider()
    
    da_ripetere = st.checkbox("🔄 Questa prestazione richiede un controllo futuro o un richiamo?")
    data_scadenza = None
    if da_ripetere:
        data_scadenza = st.date_input("📅 Data del prossimo controllo / richiamo", datetime.date.today() + datetime.timedelta(days=365))
    
    st.divider()
    
    st.markdown("### 🔐 Certificazione Ufficiale")
    certifica = st.checkbox("Certifica ora con PIN Veterinario")
    stato_certificazione = "🔴 Non Certificato (Dichiarato dal proprietario)"
    if certifica:
        pin_vet = st.text_input("PIN Veterinario (per test usa: 1234)", type="password")
        if pin_vet == "1234":
            st.success("✅ PIN Corretto. Prestazione certificata.")
            stato_certificazione = "🟢 Certificato Ufficialmente"
        elif pin_vet != "":
            st.error("❌ PIN Errato.")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="btn-indietro">', unsafe_allow_html=True)
        if st.button("⬅️ Annulla / Indietro", key="bottom_cancel_prestazione"):
            st.session_state.step_corrente = 'dashboard'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="btn-salva">', unsafe_allow_html=True)
        if st.button("Salva Prestazione"):
            if not nome_vet:
                st.error("⚠️ Inserisci il nome del veterinario o della clinica!")
            else:
                lista_allegati_iniziali = []
                if file_iniziale is not None:
                    lista_allegati_iniziali.append({
                        "nome": file_iniziale.name,
                        "bytes": file_iniziale.getvalue(),
                        "tipo": file_iniziale.type
                    })
                
                nuova_prestazione = {
                    "Data": data_esecuzione.strftime("%d/%m/%Y"),
                    "Prestazione": tipo_prestazione,
                    "Veterinario": nome_vet,
                    "Dettagli": dettagli_prestazione if dettagli_prestazione else "Nessuna nota aggiuntiva.",
                    "Scadenza/Richiamo": data_scadenza.strftime("%d/%m/%Y") if da_ripetere else "Non previsto",
                    "Stato": stato_certificazione,
                    "Allegati": lista_allegati_iniziali
                }
                st.session_state.prestazioni.append(nuova_prestazione)
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# STEP 4B: INSERIMENTO TERAPIA / FARMACO
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_terapia':
    # Pulsante di ritorno rapido in alto
    if st.button("⬅️ Torna alla Dashboard (Annulla)", key="top_back_terapia"):
        st.session_state.step_corrente = 'dashboard'
        st.rerun()
        
    st.title("💊 Prescrivi / Registra Terapia")
    st.markdown(f"Inserisci un farmaco o una cura da somministrare a **{st.session_state.dati_animale.get('nome', 'il tuo pet')}**.")
    
    nome_farmaco = st.text_input("Nome del Farmaco / Medicinale", placeholder="Es. Augmentin, Simparica...")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        data_inizio = st.date_input("Data Inizio Terapia", datetime.date.today())
    with col_t2:
        durata_terapia = st.text_input("Durata della Cura", placeholder="Es. 7 giorni, Continuativa...")
        
    nome_vet_prescrittore = st.text_input("Veterinario / Clinica Prescrittrice", placeholder="Es. Dr. Rossi")
    
    posologia = st.text_area("📋 Posologia & Istruzioni", placeholder="Es. 1 compressa ogni 12 ore...", height=100)
    
    st.divider()
    
    st.markdown("### 🔐 Certificazione Ufficiale Prescrizione")
    certifica_t = st.checkbox("Fai certificare la prescrizione con PIN Veterinario")
    stato_certificazione_t = "🔴 Non Certificato (Dichiarato dal proprietario)"
    if certifica_t:
        pin_vet_t = st.text_input("PIN Veterinario (per test usa: 1234)", type="password")
        if pin_vet_t == "1234":
            st.success("✅ PIN Corretto. Terapia certificata ufficialmente.")
            stato_certificazione_t = "🟢 Certificato Ufficialmente"
        elif pin_vet_t != "":
            st.error("❌ PIN Errato.")
            
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="btn-indietro">', unsafe_allow_html=True)
        if st.button("⬅️ Annulla / Indietro", key="bottom_cancel_terapia"):
            st.session_state.step_corrente = 'dashboard'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="btn-salva">', unsafe_allow_html=True)
        if st.button("Salva Terapia"):
            if not nome_farmaco or not nome_vet_prescrittore:
                st.error("⚠️ Compila i campi obbligatori!")
            else:
                nuova_terapia = {
                    "Farmaco": nome_farmaco,
                    "Data_Inizio": data_inizio.strftime("%d/%m/%Y"),
                    "Durata": durata_terapia if durata_terapia else "Non specificata",
                    "Veterinario": nome_vet_prescrittore,
                    "Posologia": posologia if posologia else "Seguire indicazioni del medico.",
                    "Stato": stato_certificazione_t
                }
                st.session_state.terapie.append(nuova_terapia)
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
