import streamlit as st
import pandas as pd
import datetime
import resend

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="PetHealth - Libretto Sanitario Digitale",
    page_icon="🐾",
    layout="wide"
)

# Style grafico leggero per rendere l'interfaccia accattivante
st.markdown("""
    <style>
    .stMetric { background-color: #f0f8ff; padding: 12px; border-radius: 8px; }
    .status-certified { color: #2e7d32; font-weight: bold; }
    .status-pending { color: #ed6c02; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 2. STATO IN MEMORIA (DATABASE PROVVISORIO)
# ---------------------------------------------------------
if "pet_info" not in st.session_state:
    st.session_state.pet_info = {
        "Nome": "Luna",
        "Specie": "Cane",
        "Razza": "Golden Retriever",
        "Microchip": "380260000123456",
        "Data Nascita": datetime.date(2022, 5, 12),
        "Veterinario": "Clinica Veterinaria San Siro"
    }

if "prestazioni" not in st.session_state:
    st.session_state.prestazioni = pd.DataFrame([
        {
            "ID": 1,
            "Tipo": "Vaccino Rabbia",
            "Data Esecuzione": datetime.date(2025, 10, 15),
            "Prossima Scadenza": datetime.date(2026, 10, 15),
            "Stato Certificazione": "🟢 Certificato (Clinica San Siro)",
            "Note/Terapia": "Richiamo annuale completato"
        },
        {
            "ID": 2,
            "Tipo": "Antiparassitario (Compressa)",
            "Data Esecuzione": datetime.date(2026, 9, 1),
            "Prossima Scadenza": datetime.date(2026, 10, 1),
            "Stato Certificazione": "🟡 Inserito da Proprietario",
            "Note/Terapia": "Somministrare a stomaco pieno"
        }
    ])


# ---------------------------------------------------------
# 3. FUNZIONE DI INVIO E-MAIL VIA RESEND API
# ---------------------------------------------------------
def invia_email_promemoria(api_key, email_destinatario, nome_pet, tipo_prestazione, data_scadenza):
    resend.api_key = api_key
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #2c3e50;">🐾 Promemoria Sanitario per {nome_pet}</h2>
        <p>Ciao! Ti ricordiamo che si sta avvicinando la scadenza per la seguente prestazione sanitaria:</p>
        <ul>
            <li><strong>Animale:</strong> {nome_pet}</li>
            <li><strong>Prestazione/Farmaco:</strong> {tipo_prestazione}</li>
            <li><strong>Data Scadenza:</strong> {data_scadenza.strftime('%d/%m/%Y')}</li>
        </ul>
        <p style="color: #7f8c8d; font-size: 12px;">Messaggio inviato automaticamente da PetHealth Digital Passport.</p>
    </div>
    """
    
    try:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",  # Indirizzo standard di test di Resend
            "to": email_destinatario,
            "subject": f"⏰ Promemoria Scadenza {tipo_prestazione} per {nome_pet}",
            "html": html_content
        })
        return True, r
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------
# 4. SIDEBAR E PROFILO ANIMALE
# ---------------------------------------------------------
st.sidebar.title("🐾 PetHealth Digital")
st.sidebar.caption("Libretto Sanitario & Certificazione")

st.sidebar.divider()
st.sidebar.subheader("📋 Scheda Animale")
st.sidebar.write(f"**Nome:** {st.session_state.pet_info['Nome']}")
st.sidebar.write(f"**Specie/Razza:** {st.session_state.pet_info['Specie']} - {st.session_state.pet_info['Razza']}")
st.sidebar.write(f"**Microchip:** `{st.session_state.pet_info['Microchip']}`")
st.sidebar.write(f"**Clinica:** {st.session_state.pet_info['Veterinario']}")

st.sidebar.divider()
st.sidebar.info("💡 **Sistema di Certificazione:** Le prestazioni contrassegnate in 🟢 sono convalidate direttamente dal PIN della clinica veterianaria.")


# ---------------------------------------------------------
# 5. CONTENUTO PRINCIPALE
# ---------------------------------------------------------
st.title("🐶 Libretto Sanitario & Promemoria Terapie")

# Tab per organizzare le funzionalità
tab1, tab2, tab3 = st.tabs(["📜 Storico & Scadenze", "➕ Aggiungi Prestazione", "📧 Test Invio E-mail Notification"])


# --- TAB 1: STORICO E TABELLA ---
with tab1:
    st.subheader("Cronologia Vaccini e Terapie")
    df = st.session_state.prestazioni
    
    if not df.empty:
        st.dataframe(
            df[["Tipo", "Data Esecuzione", "Prossima Scadenza", "Stato Certificazione", "Note/Terapia"]],
            use_container_width=True
        )
    else:
        st.info("Nessuna prestazione registrata.")


# --- TAB 2: AGGIUNTA NUOVA PRESTAZIONE ---
with tab2:
    st.subheader("Registra un nuovo Vaccino o Terapia")
    
    with st.form("form_prestazione", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo = st.text_input("Tipo di Prestazione / Farmaco", placeholder="Es. Vaccino Pentavalente, Antiparassitario...")
            data_es = st.date_input("Data Somministrazione / Visita", datetime.date.today())
            note = st.text_area("Note o Dosi Terapia", placeholder="Es. Somministrare mezza compressa al mattino")
            
        with col2:
            scadenza = st.date_input("Data Prossimo Richiamo / Scadenza", datetime.date.today() + datetime.timedelta(days=30))
            is_vet = st.checkbox("Certificato da Veterinario (Richiede PIN Clinica)")
            pin_vet = st.text_input("PIN Clinica Veterinaria (per Test usa: 1234)", type="password")
            
        submit = st.form_submit_button("💾 Salva nel Libretto")
        
        if submit:
            if not tipo:
                st.warning("⚠️ Inserisci il tipo di prestazione.")
            else:
                if is_vet and pin_vet == "1234":
                    stato = "🟢 Certificato (Clinica San Siro)"
                elif is_vet and pin_vet != "1234":
                    st.error("❌ PIN Veterinario errato. Salvato come non certificato.")
                    stato = "🟡 Inserito da Proprietario"
                else:
                    stato = "🟡 Inserito da Proprietario"
                    
                nuovo_id = len(st.session_state.prestazioni) + 1
                nuovo_rec = {
                    "ID": nuovo_id,
                    "Tipo": tipo,
                    "Data Esecuzione": data_es,
                    "Prossima Scadenza": scadenza,
                    "Stato Certificazione": stato,
                    "Note/Terapia": note
                }
                st.session_state.prestazioni = pd.concat([st.session_state.prestazioni, pd.DataFrame([nuovo_rec])], ignore_index=True)
                st.success(f"✅ Prestazione '{tipo}' aggiunta con successo!")


# --- TAB 3: TEST INVIO E-MAIL ---
with tab3:
    st.subheader("⚡ Test Notifica Automatica E-mail")
    st.markdown("Prova l'invio reale di un'email di avviso di scadenza sul tuo indirizzo di posta.")
    
    st.warning("📌 **Per testare l'invio gratuito:** Iscriviti su [resend.com](https://resend.com), genera una API Key gratuita e incollala qui sotto.")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        user_api_key = st.text_input("Incolla qui la tua Resend API Key", type="password", placeholder="re_123456789...")
        dest_email = st.text_input("La tua E-mail per ricevere il Test", placeholder="tuaemail@gmail.com")
        
    with col_e2:
        prestazione_sel = st.selectbox("Seleziona quale scadenza simulare:", st.session_state.prestazioni["Tipo"].tolist())
        
    if st.button("🚀 Invia E-mail di Test Adesso"):
        if not user_api_key or not dest_email:
            st.error("⚠️ Inserisci sia l'API Key di Resend che la tua e-mail di destinazione.")
        else:
            # Recupera i dati della prestazione selezionata
            row = st.session_state.prestazioni[st.session_state.prestazioni["Tipo"] == prestazione_sel].iloc[0]
            
            with st.spinner("Invio e-mail in corso..."):
                ok, res = invia_email_promemoria(
                    api_key=user_api_key,
                    email_destinatario=dest_email,
                    nome_pet=st.session_state.pet_info["Nome"],
                    tipo_prestazione=row["Tipo"],
                    data_scadenza=row["Prossima Scadenza"]
                )
                
            if ok:
                st.balloons()
                st.success(f"📩 E-mail inviata con successo a **{dest_email}**! Controlla la tua casella di posta (compresa la cartella Spam).")
            else:
                st.error(f"❌ Errore durante l'invio dell'e-mail: {res}")
