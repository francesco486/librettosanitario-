import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, date

st.set_page_config(
    page_title="PetHealth - Wellness & Care",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "data_pethealth.json"

def genera_link_whatsapp(numero, animale, farmaco, dosaggio, orario, note=""):
    """Genera il link di invio immediato con messaggio pre-compilato per WhatsApp."""
    testo = f"🐾 *PetHealth - Promemoria Terapia*\n\n🐶 *Animale:* {animale}\n💊 *Farmaco:* {farmaco}\n🥄 *Dose / Quantità:* {dosaggio}\n⏰ *Orario Somministrazione:* {orario}\n"
    if note:
        testo += f"📝 *Istruzioni:* {note}\n"
    testo += "\n⚠️ *Ricordati di somministrare la terapia fino alla data di fine prevista!*"
    
    testo_encoded = urllib.parse.quote(testo)
    numero_pulito = "".join(filter(str.isdigit, str(numero)))
    if numero_pulito:
        return f"https://api.whatsapp.com/send?phone={numero_pulito}&text={testo_encoded}"
    return f"https://api.whatsapp.com/send?text={testo_encoded}"

def carica_dati():
    """Carica i dati salvati su file JSON se esiste."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def salva_dati():
    """Salva lo stato attuale su file JSON per mantenerlo persistente ad ogni reload."""
    dati = {
        "nome_utente": st.session_state.get("nome_utente", "Francesco"),
        "numero_whatsapp": st.session_state.get("numero_whatsapp", ""),
        "lista_animali": st.session_state.get("lista_animali", ["Orlando"]),
        "pet_selezionato": st.session_state.get("pet_selezionato", "Orlando"),
        "db_visite": st.session_state.get("db_visite", {"Orlando": []}),
        "db_terapie": st.session_state.get("db_terapie", {"Orlando": []}),
        "db_fatture": st.session_state.get("db_fatture", {"Orlando": []}),
        "angeli_archiviati": st.session_state.get("angeli_archiviati", {})
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Errore durante il salvataggio dei dati: {e}")

if "inizializzato" not in st.session_state:
    dati_salvati = carica_dati()
    if dati_salvati:
        st.session_state.nome_utente = dati_salvati.get("nome_utente", "Francesco")
        st.session_state.numero_whatsapp = dati_salvati.get("numero_whatsapp", "")
        st.session_state.lista_animali = dati_salvati.get("lista_animali", ["Orlando"])
        st.session_state.pet_selezionato = dati_salvati.get("pet_selezionato", "Orlando")
        st.session_state.db_visite = dati_salvati.get("db_visite", {"Orlando": []})
        st.session_state.db_terapie = dati_salvati.get("db_terapie", {"Orlando": []})
        st.session_state.db_fatture = dati_salvati.get("db_fatture", {"Orlando": []})
        st.session_state.angeli_archiviati = dati_salvati.get("angeli_archiviati", {})
    else:
        st.session_state.nome_utente = "Francesco"
        st.session_state.numero_whatsapp = ""
        st.session_state.lista_animali = ["Orlando"]
        st.session_state.pet_selezionato = "Orlando"
        st.session_state.db_visite = {"Orlando": []}
        st.session_state.db_terapie = {"Orlando": []}
        st.session_state.db_fatture = {"Orlando": []}
        st.session_state.angeli_archiviati = {}
        salva_dati()
    st.session_state.inizializzato = True

if "sezione_attiva" not in st.session_state:
    st.session_state.sezione_attiva = "dashboard"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    :root {
        color-scheme: light !important;
    }

    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F8F7F2 !important;
        color: #1e293b !important;
    }

    .stApp p:not([data-testid="stExpander"] *), 
    .stApp label {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        line-height: 1.45 !important;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #1E3A2B !important;
        border-right: 1px solid #2D4A3E !important;
    }

    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    @media (min-width: 768px) {
        [data-testid="stSidebarCollapseButton"], 
        [data-testid="stSidebarToggle"], 
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
        }

        section[data-testid="stSidebar"] {
            display: block !important;
            min-width: 21rem !important;
            max-width: 21rem !important;
        }
    }

    /* WELLNESS CARDS */
    .wellness-card {
        background-color: #FFFFFF !important;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #E2E8E4 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
        margin-bottom: 16px;
    }

    /* ANGELS CARD SPECIFICA */
    .angels-card {
        background-color: #FFFFFF !important;
        border-radius: 16px;
        padding: 24px;
        border: 1.5px solid #CBD5E1 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
    }

    /* BADGES */
    .card-badge {
        display: inline-block;
        padding: 4px 12px;
        background-color: #E8F0EC;
        color: #1E3A2B;
        font-weight: 700;
        font-size: 0.78rem;
        border-radius: 20px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-memorial { background-color: #F1F5F9; color: #475569; }

    /* INPUT E FORM GENERICS */
    label, div[data-testid="stWidgetLabel"] p {
        color: #1E3A2B !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        margin-bottom: 6px !important;
    }

    .stTextInput input, 
    .stTextArea textarea, 
    .stNumberInput input,
    .stDateInput input,
    div[data-baseweb="input"] {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
    }

    div[data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 1.5px dashed #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }

    div[data-testid="stFileUploader"] * {
        color: #1e293b !important;
    }

    div[data-testid="stFileUploader"] button {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
    }

    div[data-testid="stAlert"] {
        background-color: #fefce8 !important;
        border: 1px solid #fef08a !important;
        border-radius: 12px !important;
    }

    div[data-testid="stAlert"] * {
        color: #854d0e !important;
        font-weight: 600 !important;
    }

    /* PULSANTI */
    div[data-testid="stFormSubmitButton"] > button,
    .stButton > button {
        background-color: #1E3A2B !important;
        border: 1px solid #1E3A2B !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(30, 58, 43, 0.15) !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stFormSubmitButton"] > button p,
    div[data-testid="stFormSubmitButton"] > button span,
    div[data-testid="stFormSubmitButton"] > button div,
    .stButton > button p,
    .stButton > button span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    div[data-testid="stFormSubmitButton"] > button:hover,
    .stButton > button:hover {
        background-color: #2D4A3E !important;
        border-color: #2D4A3E !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: #2D4A3E !important;
        border: 1px solid #3E6352 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #3E6352 !important;
    }

    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 14px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
    }

    div[data-testid="stExpander"] summary {
        background-color: #ffffff !important;
        border-radius: 14px !important;
    }

    div[data-testid="stExpander"] details summary div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stExpander"] summary * {
        color: #1E3A2B !important;
        -webkit-text-fill-color: #1E3A2B !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label p {
        color: #D2E3D8 !important;
        -webkit-text-fill-color: #D2E3D8 !important;
    }

    /* STILI SCURI SEZIONE REGISTRA NUOVO ANIMALE */
    .form-nuovo-animale input {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    .form-nuovo-animale div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    .form-nuovo-animale div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .form-nuovo-animale div[data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        border: 1.5px dashed #334155 !important;
    }

    .form-nuovo-animale div[data-testid="stFileUploader"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .form-nuovo-animale div[data-testid="stFileUploader"] button {
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
        color: #FFFFFF !important;
    }
    
    /* STILE ROSSO PER I TAB 2 E 3 DELLA SEZIONE ANGELI */
    [data-testid="stTabs"] button[data-baseweb="tab"]:nth-of-type(2) *,
    [data-testid="stTabs"] button[data-baseweb="tab"]:nth-of-type(3) * {
        color: #DC2626 !important;
        -webkit-text-fill-color: #DC2626 !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.caption("BENTORNATO/A")
    st.markdown(f"### {st.session_state.nome_utente} Veraldi")
    
    with st.expander("⚙️ Impostazioni Notifiche WhatsApp", expanded=False):
        num_wa = st.text_input("Numero WhatsApp (con prefisso, es. +393331234567)", value=st.session_state.get("numero_whatsapp", ""))
        if st.button("Salva Numero WhatsApp"):
            st.session_state.numero_whatsapp = num_wa
            salva_dati()
            st.success("Numero WhatsApp salvato!")
            
    st.write("")
    
    st.markdown("**LIBRETTO ATTIVO**")
    
    if len(st.session_state.lista_animali) > 0:
        index_selezionato = 0
        if st.session_state.pet_selezionato in st.session_state.lista_animali:
            index_selezionato = st.session_state.lista_animali.index(st.session_state.pet_selezionato)
        
        pet_selected = st.selectbox(
            "", 
            st.session_state.lista_animali, 
            index=index_selezionato,
            key="pet_select"
        )
        if pet_selected != st.session_state.pet_selezionato:
            st.session_state.pet_selezionato = pet_selected
            salva_dati()
    else:
        st.info("Nessun animale attivo al momento.")
        pet_selected = None
    
    st.write("")
    st.markdown("**SEZIONI**")
    
    if st.button("🏠 Riepilogo (Dashboard)"):
        st.session_state.sezione_attiva = "dashboard"
        st.rerun()
        
    if st.button("🏥 Visite e Clinica"):
        st.session_state.sezione_attiva = "visite"
        st.rerun()
        
    if st.button("💊 Terapie e Farmaci"):
        st.session_state.sezione_attiva = "terapie"
        st.rerun()
        
    if st.button("📄 Fatture e Spese"):
        st.session_state.sezione_attiva = "fatture"
        st.rerun()
        
    if len(st.session_state.angeli_archiviati) > 0:
        st.write("")
        if st.button("🌈 I nostri angeli a 4 zampe"):
            st.session_state.sezione_attiva = "angeli"
            st.rerun()
    
    st.write("")
    if st.button("Registra Nuovo Animale"):
        st.session_state.sezione_attiva = "nuovo_animale"
        st.rerun()

if st.session_state.sezione_attiva == "dashboard":
    if pet_selected:
        col1, col2 = st.columns(2)

        terapie_pet = st.session_state.db_terapie.get(pet_selected, [])
        visite_pet = st.session_state.db_visite.get(pet_selected, [])

        with col1:
            st.markdown(f"""
                <div class="wellness-card">
                    <span class="card-badge badge-purple">TERAPIE ATTIVE & PROMEMORIA</span>
                    <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">💊 In Somministrazione</h3>
                </div>
            """, unsafe_allow_html=True)
            
            if terapie_pet:
                for idx, t in enumerate(terapie_pet):
                    orario_txt = t.get('orario', 'Non specificato')
                    with st.expander(f"💊 {t['farmaco']} ({t['periodo']}) - ⏰ {orario_txt}"):
                        st.write(f"**Dose / Quantità:** {t['dosaggio']}")
                        st.write(f"**Orario di Somministrazione:** {orario_txt}")
                        st.write(f"**Periodo:** {t['periodo']}")
                        if t.get('note'):
                            st.write(f"**Note / Istruzioni:** {t['note']}")
                        if t.get('ricetta'):
                            st.caption(f"📄 Ricetta: {t['ricetta']}")
                        
                        # Generazione link WhatsApp
                        link_wa = genera_link_whatsapp(
                            numero=st.session_state.get("numero_whatsapp", ""),
                            animale=pet_selected,
                            farmaco=t['farmaco'],
                            dosaggio=t['dosaggio'],
                            orario=orario_txt,
                            note=t.get('note', '')
                        )
                        st.link_button("📲 Invia Promemoria WhatsApp Ora", url=link_wa)
                        
                        st.write("")
                        if st.button("🗑️ Elimina Terapia", key=f"del_ter_dash_{idx}"):
                            st.session_state.db_terapie[pet_selected].pop(idx)
                            salva_dati()
                            st.success("Terapia eliminata con successo!")
                            st.rerun()
            else:
                st.info(f"Nessuna terapia attiva al momento per {pet_selected}.")

        with col2:
            st.markdown(f"""
                <div class="wellness-card">
                    <span class="card-badge badge-blue">STORICO RECENTE</span>
                    <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">🪵 Ultime Visite</h3>
                </div>
            """, unsafe_allow_html=True)
            
            if visite_pet:
                for idx, v in enumerate(reversed(visite_pet)):
                    real_idx = len(visite_pet) - 1 - idx
                    with st.expander(f"🏥 {v['tipo']} - {v['data']}"):
                        if v['veterinario']:
                            st.write(f"**Veterinario:** {v['veterinario']}")
                        if v['diagnosi']:
                            st.write(f"**Diagnosi:** {v['diagnosi']}")
                        if v.get('referto'):
                            st.caption(f"📄 Referto: {v['referto']}")
                            
                        if st.button("🗑️ Elimina Visita", key=f"del_vis_dash_{real_idx}"):
                            st.session_state.db_visite[pet_selected].pop(real_idx)
                            salva_dati()
                            st.success("Visita eliminata con successo!")
                            st.rerun()
            else:
                st.info(f"Nessuna visita recente registrata per {pet_selected}.")

        st.write("")

        with st.expander(f"⚠️ Area Riservata Medico Veterinario (Registro Decesso - {pet_selected})"):
            st.warning(f"⚠️ Attenzione: questa procedura registrerà ufficialmente il decesso dell'animale {pet_selected}. L'azione sposterà l'intera cartella clinica nella sezione 'I nostri angeli a 4 zampe'.")
            
            date_decesso = st.date_input("Data del decesso")
            certificato = st.file_uploader("Allega Certificato di Morte (PDF/Foto)", type=["pdf", "png", "jpg"], key="cert_morte")
            pin_vet = st.text_input("PIN Veterinario per confermare (es. 1234)", type="password", key="pin_morte")
            
            if st.button("Conferma e Archivia Registro"):
                if pin_vet == "1234":
                    animale_da_archiviare = pet_selected
                    
                    st.session_state.angeli_archiviati[animale_da_archiviare] = {
                        "data_decesso": str(date_decesso),
                        "certificato": certificato.name if certificato else "Non allegato",
                        "visite": st.session_state.db_visite.get(animale_da_archiviare, []),
                        "terapie": st.session_state.db_terapie.get(animale_da_archiviare, []),
                        "fatture": st.session_state.db_fatture.get(animale_da_archiviare, [])
                    }
                    
                    st.session_state.lista_animali.remove(animale_da_archiviare)
                    
                    if len(st.session_state.lista_animali) > 0:
                        st.session_state.pet_selezionato = st.session_state.lista_animali[0]
                    else:
                        st.session_state.pet_selezionato = None
                    
                    salva_dati()
                    st.success(f"Registro archiviato con successo. {animale_da_archiviare} è stato spostato con rispetto nella sezione 'I nostri angeli a 4 zampe'.")
                    st.session_state.sezione_attiva = "angeli"
                    st.rerun()
                else:
                    st.error("PIN Veterinario non valido. Inserire un PIN corretto per procedere.")
    else:
        st.info("Registra un nuovo animale o consulta la sezione 'I nostri angeli a 4 zampe'.")

elif st.session_state.sezione_attiva == "visite":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>🏥 Visite e Clinica - {pet_selected}</h2>", unsafe_allow_html=True)
        
        with st.expander("➕ Aggiungi Nuova Visita Medica", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                data_visita = st.date_input("Data Visita")
                tipo_visita = st.selectbox("Tipo di Visita", ["Controllo Generale", "Vaccinazione", "Visita Specialistica", "Urgenza", "Controllo Post-Operatorio"])
                veterinario = st.text_input("Medico Veterinario / Clinica")
            with col2:
                diagnosi = st.text_area("Diagnosi / Note Cliniche", placeholder="Descrivi il motivo della visita e l'esito...")
                referto = st.file_uploader("Allega Referto o Esami (Opzionale)", type=["pdf", "png", "jpg"], key="visita_ref")
                fattura_visita = st.file_uploader("Allega Ricevuta / Fattura (Opzionale)", type=["pdf", "png", "jpg"], key="visita_fat")
            
            st.markdown("---")
            richiede_controllo = st.checkbox("🔄 Questa prestazione richiede un controllo successivo o va ripetuta?")
            
            if richiede_controllo:
                col_ctrl1, col_ctrl2 = st.columns(2)
                with col_ctrl1:
                    data_prossimo_controllo = st.date_input("Data Prossimo Controllo / Ripetizione")
                with col_ctrl2:
                    tipo_prestazione_ripetere = st.text_input("Tipo di Prestazione da Eseguire", placeholder="Es. Richiamo Vaccino, Controllo Ecografico, Esami del Sangue...")
            
            st.write("")
            if st.button("Salva Visita Medica"):
                nuova_visita = {
                    "data": str(data_visita),
                    "tipo": tipo_visita,
                    "veterinario": veterinario,
                    "diagnosi": diagnosi,
                    "referto": referto.name if referto else None
                }
                
                if pet_selected not in st.session_state.db_visite:
                    st.session_state.db_visite[pet_selected] = []
                    
                st.session_state.db_visite[pet_selected].append(nuova_visita)
                salva_dati()
                st.success(f"Visita medica registrata con successo per {pet_selected}!")
                st.rerun()

        st.markdown("### 📋 Visite Registrate")
        visite_list = st.session_state.db_visite.get(pet_selected, [])
        if visite_list:
            for idx, v in enumerate(visite_list):
                with st.expander(f"🏥 {v['data']} - {v['tipo']} ({v['veterinario']})"):
                    st.write(f"**Diagnosi:** {v['diagnosi']}")
                    if v.get('referto'):
                        st.caption(f"📄 Referto: {v['referto']}")
                    if st.button("🗑️ Elimina Questa Visita", key=f"del_vis_page_{idx}"):
                        st.session_state.db_visite[pet_selected].pop(idx)
                        salva_dati()
                        st.success("Visita eliminata!")
                        st.rerun()
        else:
            st.info("Nessuna visita salvata al momento.")

    else:
        st.warning("Seleziona o registra un animale attivo per gestire le visite.")

elif st.session_state.sezione_attiva == "terapie":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>💊 Terapie e Farmaci - {pet_selected}</h2>", unsafe_allow_html=True)
        
        with st.expander("➕ Nuova Terapia o Prescrizione", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                nome_farmaco = st.text_input("Nome del Farmaco / Principio Attivo*")
                dosaggio = st.text_input("Dose / Quantità (es. 1/2 compressa, 5ml, 1 fiala)*")
                
                # Checkbox per somministrazione per più giorni
                is_multigiorno = st.checkbox("📅 La terapia va somministrata per più giorni?", value=False)
                
                data_inizio = st.date_input("Data Somministrazione / Inizio Terapia", value=date.today())
                
                if is_multigiorno:
                    data_fine = st.date_input("Data Fine Terapia (Presunta)")
                    st.markdown("---")
                    st.caption("🔔 **Configurazione Promemoria**")
                    attiva_promemoria = st.checkbox("📲 Attiva Promemoria Giornaliero WhatsApp", value=True)
                    if attiva_promemoria:
                        orario_somministrazione = st.time_input("Orario di Somministrazione Giornaliero", value=datetime.strptime("09:00", "%H:%M").time())
                    else:
                        orario_somministrazione = None
                else:
                    data_fine = data_inizio
                    attiva_promemoria = False
                    orario_somministrazione = None

            with col2:
                note_somministrazione = st.text_area("Istruzioni e Note", placeholder="Es. Somministrare a stomaco pieno, 1 ora prima dei pasti...")
                ricetta = st.file_uploader("Allega Ricetta Medica / Prescrizione (Opzionale)", type=["pdf", "png", "jpg"], key="terapia_ric")
                fattura_farmaco = st.file_uploader("Allega Scontrino / Fattura Acquisto (Opzionale)", type=["pdf", "png", "jpg"], key="terapia_fat")
                
            st.markdown("---")
            richiede_controllo_terapia = st.checkbox("🔄 La terapia richiede una verifica intermedia o un richiamo?")
            
            if richiede_controllo_terapia:
                col_tctrl1, col_tctrl2 = st.columns(2)
                with col_tctrl1:
                    data_prossimo_controllo_t = st.date_input("Data Controllo Terapia / Visita di Verifica")
                with col_tctrl2:
                    tipo_prestazione_terapia = st.text_input("Tipo di Controllo Richiesto", placeholder="Es. Controllo valori ematici, Visita di controllo efficacia...")

            st.write("")
            if st.button("Salva Terapia e Programma Promemoria"):
                if nome_farmaco.strip() and dosaggio.strip():
                    if is_multigiorno:
                        periodo_txt = f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}"
                        orario_str = orario_somministrazione.strftime("%H:%M") if (attiva_promemoria and orario_somministrazione) else "Non impostato"
                    else:
                        periodo_txt = f"Dose Unica ({data_inizio.strftime('%d/%m/%Y')})"
                        orario_str = "Dose singola"

                    nuova_terapia = {
                        "farmaco": nome_farmaco,
                        "dosaggio": dosaggio,
                        "orario": orario_str,
                        "periodo": periodo_txt,
                        "multigiorno": is_multigiorno,
                        "promemoria_attivo": attiva_promemoria if is_multigiorno else False,
                        "note": note_somministrazione,
                        "ricetta": ricetta.name if ricetta else None
                    }
                    
                    if pet_selected not in st.session_state.db_terapie:
                        st.session_state.db_terapie[pet_selected] = []
                        
                    st.session_state.db_terapie[pet_selected].append(nuova_terapia)
                    salva_dati()
                    st.success(f"Terapia per {nome_farmaco} registrata con successo!")
                    st.rerun()
                else:
                    st.error("Inserisci il nome del farmaco e la dose esatta.")

        st.markdown("### 📋 Terapie e Promemoria Programmati")
        terapie_list = st.session_state.db_terapie.get(pet_selected, [])
        if terapie_list:
            for idx, t in enumerate(terapie_list):
                orario_txt = t.get('orario', 'Non specificato')
                with st.expander(f"💊 {t['farmaco']} - Dose: {t['dosaggio']} ({t['periodo']})"):
                    st.write(f"**Dose / Quantità:** {t['dosaggio']}")
                    st.write(f"**Orario Somministrazione:** {orario_txt}")
                    st.write(f"**Periodo Terapia:** {t['periodo']}")
                    if t.get('note'):
                        st.write(f"**Istruzioni:** {t['note']}")
                    if t.get('ricetta'):
                        st.caption(f"📄 Ricetta allegata: {t['ricetta']}")
                    
                    # Mostra il pulsante promemoria solo se la terapia è per più giorni ed è attivata la notifica
                    if t.get('promemoria_attivo', False):
                        link_wa = genera_link_whatsapp(
                            numero=st.session_state.get("numero_whatsapp", ""),
                            animale=pet_selected,
                            farmaco=t['farmaco'],
                            dosaggio=t['dosaggio'],
                            orario=orario_txt,
                            note=t.get('note', '')
                        )
                        st.link_button("📲 Invia Promemoria WhatsApp", url=link_wa)
                    
                    st.write("")
                    if st.button("🗑️ Elimina Questa Terapia", key=f"del_ter_page_{idx}"):
                        st.session_state.db_terapie[pet_selected].pop(idx)
                        salva_dati()
                        st.success("Terapia eliminata!")
                        st.rerun()
        else:
            st.info("Nessuna terapia salvata al momento.")

    else:
        st.warning("Seleziona o registra un animale attivo per gestire le terapie.")

elif st.session_state.sezione_attiva == "fatture":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>📄 Fatture e Spese - {pet_selected}</h2>", unsafe_allow_html=True)
        
        with st.expander("➕ Carica Nuova Fattura o Ricevuta", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                data_spesa = st.date_input("Data Documento")
                categoria_spesa = st.selectbox("Categoria Spesa", ["Visita Veterinaria", "Farmaci", "Esami di Laboratorio", "Chirurgia", "Cibo / Integratori", "Altro"])
                importo = st.number_input("Importo (€)", min_value=0.0, step=0.5, format="%.2f")
            with col2:
                fornitore = st.text_input("Clinica / Farmacia / Fornitore")
                file_fattura = st.file_uploader("Allega Documento Fattura / Ricevuta", type=["pdf", "png", "jpg"], key="spesa_fat")
                note_spesa = st.text_input("Note Aggiuntive (Opzionale)")
                
            if st.button("Salva Fattura"):
                nuova_fattura = {
                    "data": str(data_spesa),
                    "categoria": categoria_spesa,
                    "importo": importo,
                    "fornitore": fornitore,
                    "documento": file_fattura.name if file_fattura else None
                }
                
                if pet_selected not in st.session_state.db_fatture:
                    st.session_state.db_fatture[pet_selected] = []
                    
                st.session_state.db_fatture[pet_selected].append(nuova_fattura)
                salva_dati()
                st.success("Fattura / Spesa registrata con successo!")
                st.rerun()

        st.markdown("### 📋 Fatture Registrate")
        fatture_list = st.session_state.db_fatture.get(pet_selected, [])
        if fatture_list:
            for idx, f in enumerate(fatture_list):
                with st.expander(f"📄 €{f['importo']:.2f} - {f['categoria']} ({f['data']})"):
                    st.write(f"**Fornitore:** {f['fornitore']}")
                    if f.get('documento'):
                        st.caption(f"📄 Documento: {f['documento']}")
                    if st.button("🗑️ Elimina Fattura", key=f"del_fat_page_{idx}"):
                        st.session_state.db_fatture[pet_selected].pop(idx)
                        salva_dati()
                        st.success("Fattura eliminata!")
                        st.rerun()
        else:
            st.info("Nessuna fattura salvata al momento.")

    else:
        st.warning("Seleziona o registra un animale attivo per gestire le fatture.")

elif st.session_state.sezione_attiva == "angeli":
    st.markdown("<h2 style='color: #1E3A2B;'>🌈 I Nostri Angeli a 4 Zampe</h2>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="angels-card">
            <span class="card-badge badge-memorial">MEMORIALE</span>
            <p style="font-size: 1.1rem; color: #334155; font-weight: 600; line-height: 1.6; margin-top: 10px; margin-bottom: 0;">
                Ricorda <strong>{st.session_state.nome_utente}</strong>, per quanto doloroso i nostri amici a 4 zampe non ci abbandonano mai veramente, ma ci proteggono da lassù 🐾
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    lista_angeli = list(st.session_state.angeli_archiviati.keys())
    
    if len(lista_angeli) > 0:
        col_select, col_restore = st.columns([2, 1])
        
        with col_select:
            angelo_selezionato = st.selectbox("Seleziona un angelo per consultare la sua cartella clinica archiviata:", lista_angeli)
            
        with col_restore:
            st.write("")
            st.write("")
            if st.button("🔄 Ripristina Animale Attivo"):
                if angelo_selezionato not in st.session_state.lista_animali:
                    st.session_state.lista_animali.append(angelo_selezionato)
                
                dati_ripristinati = st.session_state.angeli_archiviati.pop(angelo_selezionato)
                st.session_state.db_visite[angelo_selezionato] = dati_ripristinati.get("visite", [])
                st.session_state.db_terapie[angelo_selezionato] = dati_ripristinati.get("terapie", [])
                st.session_state.db_fatture[angelo_selezionato] = dati_ripristinati.get("fatture", [])
                
                st.session_state.pet_selezionato = angelo_selezionato
                
                if len(st.session_state.angeli_archiviati) == 0:
                    st.session_state.sezione_attiva = "dashboard"
                
                salva_dati()
                st.success(f"{angelo_selezionato} è stato ripristinato con successo tra gli animali attivi!")
                st.rerun()

        if angelo_selezionato in st.session_state.angeli_archiviati:
            dati_angelo = st.session_state.angeli_archiviati[angelo_selezionato]
            
            st.write("")
            st.markdown(f"### 📁 Cartella Clinica Archiviata: **{angelo_selezionato}**")
            st.caption(f"Data del decesso registrata: {dati_angelo['data_decesso']} | Certificato allegato: {dati_angelo['certificato']}")
            st.markdown("---")
            
            tab_visite, tab_terapie, tab_fatture = st.tabs([
                "🏥 Storico Visite", 
                "💊 Terapie Registrate", 
                "📄 Fatture e Documenti"
            ])
            
            with tab_visite:
                if dati_angelo.get("visite"):
                    for idx_v, v in enumerate(dati_angelo["visite"]):
                        with st.expander(f"🏥 {v['data']} - {v['tipo']} ({v['veterinario']})"):
                            st.write(f"**Diagnosi:** {v['diagnosi']}")
                            if v.get('referto'):
                                st.caption(f"📄 Referto: {v['referto']}")
                            if st.button("🗑️ Elimina Questa Visita", key=f"del_vis_ang_{idx_v}"):
                                dati_angelo["visite"].pop(idx_v)
                                salva_dati()
                                st.success("Visita eliminata dall'archivio!")
                                st.rerun()
                else:
                    st.info("Nessuna visita salvata nello storico al momento dell'archiviazione.")
                    
            with tab_terapie:
                if dati_angelo.get("terapie"):
                    for idx_t, t in enumerate(dati_angelo["terapie"]):
                        with st.expander(f"💊 {t['farmaco']} ({t['periodo']})"):
                            st.write(f"**Dosaggio:** {t['dosaggio']}")
                            st.write(f"**Note:** {t['note']}")
                            if t.get('ricetta'):
                                st.caption(f"📄 Ricetta: {t['ricetta']}")
                            if st.button("🗑️ Elimina Questa Terapia", key=f"del_ter_ang_{idx_t}"):
                                dati_angelo["terapie"].pop(idx_t)
                                salva_dati()
                                st.success("Terapia eliminata dall'archivio!")
                                st.rerun()
                else:
                    st.info("Nessuna terapia salvata nello storico al momento dell'archiviazione.")
                    
            with tab_fatture:
                if dati_angelo.get("fatture"):
                    for idx_f, f in enumerate(dati_angelo["fatture"]):
                        with st.expander(f"📄 €{f['importo']:.2f} - {f['categoria']} ({f['data']})"):
                            st.write(f"**Fornitore:** {f['fornitore']}")
                            if f.get('documento'):
                                st.caption(f"📄 Ricevuta/Fattura: {f['documento']}")
                            if st.button("🗑️ Elimina Questa Fattura", key=f"del_fat_ang_{idx_f}"):
                                dati_angelo["fatture"].pop(idx_f)
                                salva_dati()
                                st.success("Fattura eliminata dall'archivio!")
                                st.rerun()
                else:
                    st.info("Nessuna fattura salvata nello storico al momento dell'archiviazione.")

elif st.session_state.sezione_attiva == "nuovo_animale":
    st.markdown("<h2 style='color: #1E3A2B;'>🐾 Registra Nuovo Animale</h2>", unsafe_allow_html=True)
    
    st.markdown('<div class="form-nuovo-animale">', unsafe_allow_html=True)
    
    with st.form("form_nuovo_animale"):
        col1, col2 = st.columns(2)
        with col1:
            nome_animale = st.text_input("Nome dell'animale*")
            specie = st.selectbox("Specie", ["Cane", "Gatto", "Coniglio", "Altro"])
            razza = st.text_input("Razza")
        with col2:
            data_nascita = st.date_input("Data di Nascita Presunta")
            microchip = st.text_input("Numero Microchip (Opzionale)")
            foto_profilo = st.file_uploader("Foto Profilo Animale (Opzionale)", type=["png", "jpg"])
            
        submit_animale = st.form_submit_button("Salva Scheda Animale")
        
        if submit_animale:
            if nome_animale.strip() != "":
                if nome_animale not in st.session_state.lista_animali:
                    st.session_state.lista_animali.append(nome_animale)
                    st.session_state.db_visite[nome_animale] = []
                    st.session_state.db_terapie[nome_animale] = []
                    st.session_state.db_fatture[nome_animale] = []
                
                st.session_state.pet_selezionato = nome_animale
                st.session_state.sezione_attiva = "dashboard"
                salva_dati()
                st.success(f"Scheda di {nome_animale} creata con successo!")
                st.rerun()
            else:
                st.error("Inserisci un nome valido per l'animale.")
                
    st.markdown('</div>', unsafe_allow_html=True)
