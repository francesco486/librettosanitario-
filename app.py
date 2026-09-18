import streamlit as st
import datetime
import pandas as pd

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA
# ---------------------------------------------------------
st.set_page_config(page_title="PetHealth - Registrazione", page_icon="🐾", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .btn-salva>button {width: 100%; border-radius: 8px; background-color: #28a745; color: white; font-weight: bold;}
    .btn-indietro>button {width: 100%; border-radius: 8px; background-color: #6c757d; color: white;}
    .certificato {color: #28a745; font-weight: bold;}
    .non-certificato {color: #dc3545; font-weight: bold;}
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
    st.session_state.prestazioni = [] # Lista vuota per salvare le prestazioni

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
    st.title(f"Libretto di {st.session_state.dati_animale['nome']} 🐾")
    
    # 1. Mostriamo lo storico delle prestazioni
    st.subheader("📜 Storico Prestazioni Sanitarie")
    if len(st.session_state.prestazioni) == 0:
        st.info("Nessuna prestazione registrata al momento.")
    else:
        # Trasformiamo la lista in una bella tabella
        df = pd.DataFrame(st.session_state.prestazioni)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # 2. Pulsante che ci porta alla schermata di aggiunta
    if st.button("➕ Aggiungi una Prestazione Veterinaria", use_container_width=True):
        st.session_state.step_corrente = 'aggiungi_prestazione'
        st.rerun()

# ---------------------------------------------------------
# STEP 4: AGGIUNTA PRESTAZIONE (NUOVA SEZIONE!)
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'aggiungi_prestazione':
    st.title("➕ Nuova Prestazione Sanitaria")
    st.markdown(f"Registra un vaccino, una visita o una terapia per **{st.session_state.dati_animale['nome']}**.")
    
    # Non usiamo st.form qui, così l'interfaccia può essere dinamica (apparire/scomparire elementi)
    tipo_prestazione = st.selectbox("Tipo di Prestazione", ["Vaccino", "Antiparassitario", "Visita di Controllo", "Esami del Sangue", "Altro"])
    nome_vet = st.text_input("Nome Clinica o Veterinario", placeholder="Es. Clinica San Siro")
    data_esecuzione = st.date_input("Data di esecuzione", datetime.date.today())
    
    st.divider()
    
    # Sistema dinamico per la scadenza
    da_ripetere = st.checkbox("🔄 Questa prestazione richiede un richiamo futuro?")
    data_scadenza = None
    if da_ripetere:
        data_scadenza = st.date_input("📅 Data in cui dovrà essere rifatta (Scadenza)", datetime.date.today() + datetime.timedelta(days=365))
    
    st.divider()
    
    # Sistema di Certificazione Anti-Frode
    st.markdown("### 🔐 Certificazione Ufficiale")
    st.info("Per rendere questa prestazione valida e certificata, chiedi al tuo veterinario di inserire il suo PIN autorizzato.")
    certifica = st.checkbox("Fai certificare ora dal Veterinario")
    
    stato_certificazione = "🔴 Non Certificato (Dichiarato dal proprietario)"
    if certifica:
        pin_vet = st.text_input("PIN del Veterinario (per test usa: 1234)", type="password")
        if pin_vet == "1234":
            st.success("✅ PIN Corretto. La prestazione sarà certificata.")
            stato_certificazione = "🟢 Certificato Ufficialmente"
        elif pin_vet != "":
            st.error("❌ PIN Errato.")
    
    st.divider()
    
    # Pulsanti di salvataggio e annullamento
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
                st.error("Inserisci il nome del veterinario!")
            else:
                # Salviamo i dati nella lista
                nuova_prestazione = {
                    "Data": data_esecuzione.strftime("%d/%m/%Y"),
                    "Prestazione": tipo_prestazione,
                    "Veterinario": nome_vet,
                    "Scadenza/Richiamo": data_scadenza.strftime("%d/%m/%Y") if da_ripetere else "Non previsto",
                    "Stato": stato_certificazione
                }
                st.session_state.prestazioni.append(nuova_prestazione)
                
                # Torniamo alla dashboard
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
