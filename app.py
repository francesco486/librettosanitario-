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
    st.markdown("Parlaci un po' del tuo compagno di avventures.")
    
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
    st.title(f"Libretto Sanitario di {st.session_state.dati_animale['nome']} 🐾")
    
    # 1. Pulsante per aggiungere nuove prestazioni
    if st.button("➕ Aggiungi una Prestazione Veterinaria", use_container_width=True):
        st.session_state.step_corrente = 'aggiungi_prestazione'
        st.rerun()

    st.divider()
    
    # 2. Mostriamo la cronologia delle visite come schede dettagliate
    st.subheader("📜 Storico Visite & Cartella Clinica")
    
    if len(st.session_state.prestazioni) == 0:
        st.info("Nessuna prestazione registrata al momento. Clicca sul pulsante in alto per aggiungere la prima visita!")
    else:
        # Mostriamo le prestazioni partendo dalla più recente
        for item in reversed(st.session_state.prestazioni):
            # Titolo della scheda con stato di certificazione
            titolo_scheda = f"{item['Data']} - {item['Prestazione']} ({item['Stato'].split()[0]})"
            
            with st.expander(titolo_scheda):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**🏥 Clinica / Vet:** {item['Veterinario']}")
                    st.write(f"**🛡️ Stato:** {item['Stato']}")
                with col2:
                    st.write(f"**📅 Prossimo Richiamo:** {item['Scadenza/Richiamo']}")
                
                st.markdown("**📋 Dettagli Clinici & Note del Veterinario:**")
                st.info(item['Dettagli'])

# ---------------------------------------------------------
# STEP 4: AGGIUNTA PRESTAZIONE CON DETTAGLI CLINICI
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_prestazione':
    st.title("➕ Nuova Prestazione Sanitaria")
    st.markdown(f"Registra i dettagli della visita o del trattamento per **{st.session_state.dati_animale['nome']}**.")
    
    # Dati base della visita
    col_a, col_b = st.columns(2)
    with col_a:
        tipo_prestazione = st.selectbox("Tipo di Prestazione", ["Vaccino", "Antiparassitario", "Visita Generale", "Intervento Chirurgico", "Esami del Sangue / RX", "Altro"])
    with col_b:
        data_esecuzione = st.date_input("Data Esecuzione", datetime.date.today())
        
    nome_vet = st.text_input("Nome Clinica o Veterinario Curante", placeholder="Es. Clinica Veterinaria San Siro - Dr. Rossi")
    
    # CAMPO NUOVO: DETTAGLI E REFERTO VETERINARIO
    dettagli_prestazione = st.text_area(
        "📝 Dettagli della prestazione / Note Cliniche", 
        placeholder="Scrivi qui cosa è stato fatto durante la visita (es. Esito esami, peso dell'animale, posologia dei farmaci prescritto, raccomandazioni...)",
        height=130
    )
    
    st.divider()
    
    # Sistema per la scadenza/richiamo
    da_ripetere = st.checkbox("🔄 Questa prestazione richiede un richiamo o un controllo futuro?")
    data_scadenza = None
    if da_ripetere:
        data_scadenza = st.date_input("📅 Data del prossimo richiamo / controllo", datetime.date.today() + datetime.timedelta(days=365))
    
    st.divider()
    
    # Sistema di Certificazione Anti-Frode
    st.markdown("### 🔐 Certificazione Ufficiale")
    st.caption("Fai inserire il PIN alla clinica per autenticare ufficialmente questo referto.")
    certifica = st.checkbox("Certifica ora con PIN Veterinario")
    
    stato_certificazione = "🔴 Non Certificato (Dichiarato dal proprietario)"
    if certifica:
        pin_vet = st.text_input("PIN Veterinario (per test usa: 1234)", type="password")
        if pin_vet == "1234":
            st.success("✅ PIN Corretto. Referto certificato ufficialmente.")
            stato_certificazione = "🟢 Certificato Ufficialmente"
        elif pin_vet != "":
            st.error("❌ PIN Errato.")
    
    st.divider()
    
    # Pulsanti di azione
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
            else:
                # Salviamo tutti i dettagli, compreso il referto esteso
                nuova_prestazione = {
                    "Data": data_esecuzione.strftime("%d/%m/%Y"),
                    "Prestazione": tipo_prestazione,
                    "Veterinario": nome_vet,
                    "Dettagli": dettagli_prestazione if dettagli_prestazione else "Nessun dettaglio aggiuntivo inserito.",
                    "Scadenza/Richiamo": data_scadenza.strftime("%d/%m/%Y") if da_ripetere else "Non previsto",
                    "Stato": stato_certificazione
                }
                st.session_state.prestazioni.append(nuova_prestazione)
                
                # Torniamo alla dashboard
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
