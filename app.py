import streamlit as st
import datetime

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA
# ---------------------------------------------------------
st.set_page_config(page_title="PetHealth - Registrazione", page_icon="🐾", layout="centered")

# Rimuove il menu di default di Streamlit per un look più pulito
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 20px; background-color: #ff4b4b; color: white;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. GESTIONE DEGLI STEP (STATO DELLA SESSIONE)
# ---------------------------------------------------------
# Definiamo a quale "pagina" si trova l'utente (1. utente, 2. animale, 3. dashboard)
if 'step_corrente' not in st.session_state:
    st.session_state.step_corrente = 'registrazione_utente'

if 'dati_utente' not in st.session_state:
    st.session_state.dati_utente = {}

if 'dati_animale' not in st.session_state:
    st.session_state.dati_animale = {}


# ---------------------------------------------------------
# STEP 1: REGISTRAZIONE PROPRIETARIO
# ---------------------------------------------------------
if st.session_state.step_corrente == 'registrazione_utente':
    st.title("Benvenuto su PetHealth 🐾")
    st.markdown("Crea il tuo account per tenere traccia della salute del tuo amico a quattro zampe.")
    
    with st.form("form_utente"):
        nome = st.text_input("Il tuo Nome e Cognome")
        email = st.text_input("La tua E-mail")
        password = st.text_input("Crea una Password", type="password")
        
        submit = st.form_submit_button("Continua ➔")
        
        if submit:
            if nome and email and password:
                # Salviamo i dati in memoria
                st.session_state.dati_utente = {"nome": nome, "email": email}
                # Passiamo allo step 2
                st.session_state.step_corrente = 'registrazione_animale'
                st.rerun() # Ricarica la pagina istantaneamente
            else:
                st.error("⚠️ Compila tutti i campi per proseguire.")


# ---------------------------------------------------------
# STEP 2: INSERIMENTO ANIMALE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'registrazione_animale':
    st.title(f"Ciao {st.session_state.dati_utente['nome']}! 👋")
    st.markdown("Ora parlaci un po' del tuo compagno di avventure.")
    
    with st.form("form_animale"):
        nome_pet = st.text_input("Nome dell'animale", placeholder="Es. Luna, Rocky...")
        
        col1, col2 = st.columns(2)
        with col1:
            specie = st.selectbox("Specie", ["Cane 🐶", "Gatto 🐱", "Coniglio 🐰", "Altro"])
        with col2:
            data_nascita = st.date_input("Data di nascita", datetime.date(2020, 1, 1))
            
        razza = st.text_input("Razza", placeholder="Es. Golden Retriever, Meticcio...")
        microchip = st.text_input("Numero Microchip (opzionale ma consigliato per i cani)")
        
        submit_pet = st.form_submit_button("Crea Libretto Sanitario ➔")
        
        if submit_pet:
            if nome_pet:
                st.session_state.dati_animale = {
                    "nome": nome_pet,
                    "specie": specie,
                    "razza": razza,
                    "microchip": microchip,
                    "data_nascita": data_nascita
                }
                st.session_state.step_corrente = 'dashboard'
                st.rerun()
            else:
                st.error("⚠️ Inserisci almeno il nome del tuo animale.")


# ---------------------------------------------------------
# STEP 3: DASHBOARD PRINCIPALE
# ---------------------------------------------------------
elif st.session_state.step_corrente == 'dashboard':
    st.success("🎉 Account e Libretto creati con successo!")
    
    st.title(f"Libretto di {st.session_state.dati_animale['nome']}")
    
    # Mostriamo una scheda riassuntiva
    st.markdown("### Dati Generali")
    st.info(f"""
    **Specie/Razza:** {st.session_state.dati_animale['specie']} - {st.session_state.dati_animale['razza']}  
    **Proprietario:** {st.session_state.dati_utente['nome']} ({st.session_state.dati_utente['email']})  
    **Microchip:** `{st.session_state.dati_animale['microchip'] if st.session_state.dati_animale['microchip'] else 'Non inserito'}`
    """)
    
    st.divider()
    
    st.subheader("Prossimi Passi")
    st.button("➕ Aggiungi una Prestazione Veterinaria")
    
    # Pulsante per resettare e riprovare il test
    st.divider()
    if st.button("Esci (Reset Test)"):
        st.session_state.step_corrente = 'registrazione_utente'
        st.session_state.dati_utente = {}
        st.session_state.dati_animale = {}
        st.rerun()
