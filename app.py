import streamlit as st
import datetime
import pandas as pd

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA
# ---------------------------------------------------------
st.set_page_config(page_title="PetHealth - Libretto Digitale", page_icon="🐾", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .btn-salva>button {width: 100%; border-radius: 8px; background-color: #28a745; color: white; font-weight: bold;}
    .btn-indietro>button {width: 100%; border-radius: 8px; background-color: #6c757d; color: white;}
    .terapia-box {background-color: #e8f4f8; border-left: 5px solid #2980b9; padding: 10px; border-radius: 5px; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. GESTIONE DEGLI STEP (STATO DELLA SESSIONE)
# ---------------------------------------------------------
if 'step_corrente' not in st.session_state:
    st.session_state.step_corrente = 'registrazione_utente'
if 'dati_utente' not in st.session_state:
    st.session_state.dati_utente = {}
if 'dati_animale' not in st.session_state:
    st.session_state.dati_animale = {}
if 'prestazioni' not in st.session_state:
    st.session_state.prestazioni = []

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
    st.title(f"Ciao {st.session_state.dati_utente['nome']}! 👋")
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
    
    # Pulsante per aggiungere nuove visite o cure
    if st.button("➕ Aggiungi una Prestazione o Terapia Veterinaria", use_container_width=True):
        st.session_state.step_corrente = 'aggiungi_prestazione'
        st.rerun()

    st.divider()
    
    # 1. SEZIONE TERAPIE IN CORSO (Mostra subito i farmaci da somministrare)
    terapie_attive = [p for p in st.session_state.prestazioni if p.get('Ha_Terapia', False)]
    
    if terapie_attive:
        st.subheader("💊 Terapie & Farmaci da Somministrare")
        for t in terapie_attive:
            with st.container():
                st.markdown(f"""
                <div class="terapia-box">
                    <h4>💊 {t.get('Nome_Farmaco', 'Farmaco')}</h4>
                    <p><b>Posologia/Istruzioni:</b> {t.get('Posologia', 'N/D')}</p>
                    <p><b>Durata:</b> {t.get('Durata_Terapia', 'N/D')} | <b>Prescritto il:</b> {t.get('Data', 'N/D')} da {t.get('Veterinario', 'N/D')}</p>
                </div>
                """, unsafe_allow_html=True)
        st.divider()

    # 2. STORICO COMPLETO VISITE
    st.subheader("📜 Cartella Clinica & Storico Visite")
    
    if len(st.session_state.prestazioni) == 0:
        st.info("Nessuna prestazione o cura registrata al momento. Clicca sul pulsante in alto per iniziare!")
    else:
        for item in reversed(st.session_state.prestazioni):
            data = item.get('Data', 'N/D')
            prestazione = item.get('Prestazione', 'Visita')
            stato = item.get('Stato', 'Non certificato')
            vet = item.get('Veterinario', 'N/D')
            scadenza = item.get('Scadenza/Richiamo', 'Non prevista')
            dettagli = item.get('Dettagli', 'Nessun dettaglio aggiuntivo.')
            ha_terapia = item.get('Ha_Terapia', False)
            
            icona_stato = stato.split()[0] if stato else "🔴"
            titolo_scheda = f"{data} - {prestazione} ({icona_stato})"
            
            with st.expander(titolo_scheda):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**🏥 Clinica / Vet:** {vet}")
                    st.write(f"**🛡️ Stato:** {stato}")
                with col2:
                    st.write(f"**📅 Prossimo Richiamo:** {scadenza}")
                
                st.markdown("**📋 Note della Visita:**")
                st.info(dettagli)
                
                if ha_terapia:
                    st.markdown("**💊 Terapia Prescritta:**")
                    st.warning(f"**Farmaco:** {item.get('Nome_Farmaco')}\n\n**Istruzioni:** {item.get('Posologia')}\n\n**Durata:** {item.get('Durata_Terapia')}")

# ---------------------------------------------------------
# STEP 4: AGGIUNTA PRESTAZIONE E TERAPIA
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_prestazione':
    st.title("➕ Nuova Prestazione / Terapia")
    st.markdown(f"Registra la visita e le eventuali prescrizioni per **{st.session_state.dati_animale.get('nome', 'il tuo pet')}**.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        tipo_prestazione = st.selectbox("Tipo di Prestazione", ["Visita Generale", "Vaccino", "Antiparassitario", "Prescrizione Terapia/Farmaco", "Intervento Chirurgico", "Esami del Sangue / RX", "Altro"])
    with col_b:
        data_esecuzione = st.date_input("Data Visita/Prescrizione", datetime.date.today())
        
    nome_vet = st.text_input("Nome Clinica o Veterinario Curante", placeholder="Es. Clinica Veterinaria San Siro - Dr. Rossi")
    
    dettagli_prestazione = st.text_area(
        "📝 Dettagli della visita / Diagnosi", 
        placeholder="Scrivi qui l'esito della visita o le osservazioni del veterinario...",
        height=100
    )
    
    st.divider()
    
    # --- NUOVA SEZIONE: PRESCRIZIONE FARMACI ---
    st.markdown("### 💊 Prescrizione Cura / Farmaci per Casa")
    prescrive_terapia = st.checkbox("Il veterinario ha prescritto farmaci o una terapia da fare a casa?")
    
    nome_farmaco = ""
    posologia = ""
    durata_terapia = ""
    
    if prescrive_terapia:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nome_farmaco = st.text_input("Nome del Farmaco / Medicinale", placeholder="Es. Augmentin, Simparica, Ribes Pet...")
            durata_terapia = st.text_input("Durata della cura", placeholder="Es. 7 giorni, 2 settimane, Continuativa...")
        with col_f2:
            posologia = st.text_area("Posologia & Dosaggio", placeholder="Es. 1 compressa ogni 12 ore a stomaco pieno", height=93)
            
    st.divider()
    
    # Sistema per il richiamo/visita di controllo
    da_ripetere = st.checkbox("🔄 Richiede un controllo futuro o un richiamo vaccinale?")
    data_scadenza = None
    if da_ripetere:
        data_scadenza = st.date_input("📅 Data del prossimo controllo / richiamo", datetime.date.today() + datetime.timedelta(days=365))
    
    st.divider()
    
    # Sistema di Certificazione Anti-Frode
    st.markdown("### 🔐 Certificazione Ufficiale")
    st.caption("Fai inserire il PIN alla clinica per autenticare questa scheda e la relativa ricetta/prescrizione.")
    certifica = st.checkbox("Certifica ora con PIN Veterinario")
    
    stato_certificazione = "🔴 Non Certificato (Dichiarato dal proprietario)"
    if certifica:
        pin_vet = st.text_input("PIN Veterinario (per test usa: 1234)", type="password")
        if pin_vet == "1234":
            st.success("✅ PIN Corretto. Scheda e terapia certificate ufficialmente.")
            stato_certificazione = "🟢 Certificato Ufficialmente"
        elif pin_vet != "":
            st.error("❌ PIN Errato.")
    
    st.divider()
    
    # Pulsanti
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="btn-indietro">', unsafe_allow_html=True)
        if st.button("Annulla"):
            st.session_state.step_corrente = 'dashboard'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="btn-salva">', unsafe_allow_html=True)
        if st.button("Salva nel Libretto"):
            if not nome_vet:
                st.error("⚠️ Inserisci il nome del veterinario o della clinica!")
            elif prescrive_terapia and not nome_farmaco:
                st.error("⚠️ Hai spuntato la prescrizione di una terapia: inserisci il nome del farmaco!")
            else:
                nuova_prestazione = {
                    "Data": data_esecuzione.strftime("%d/%m/%Y"),
                    "Prestazione": tipo_prestazione,
                    "Veterinario": nome_vet,
                    "Dettagli": dettagli_prestazione if dettagli_prestazione else "Nessuna nota aggiuntiva.",
                    "Ha_Terapia": prescrive_terapia,
                    "Nome_Farmaco": nome_farmaco,
                    "Posologia": posologia if posologia else "Seguire indicazioni del veterinario.",
                    "Durata_Terapia": durata_terapia if durata_terapia else "Da concordare",
                    "Scadenza/Richiamo": data_scadenza.strftime("%d/%m/%Y") if da_ripetere else "Non previsto",
                    "Stato": stato_certificazione
                }
                st.session_state.prestazioni.append(nuova_prestazione)
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
