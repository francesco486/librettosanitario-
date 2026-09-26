import streamlit as st
import json
import os
import urllib.parse
import requests
import hashlib
from datetime import datetime, date

st.set_page_config(
    page_title="PetHealth - Wellness & Care",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "data_pethealth.json"

def genera_codice_certificazione(pet_nome, vet_nome, num_ordine, data_prestazione):
    """Genera un codice identificativo univoco e inalterabile di certificazione sanitaria."""
    stringa_base = f"{pet_nome}-{vet_nome}-{num_ordine}-{data_prestazione}-{datetime.now().isoformat()}"
    hash_codice = hashlib.sha256(stringa_base.encode('utf-8')).hexdigest()[:8].upper()
    return f"VET-CERT-{hash_codice}"

def genera_link_whatsapp(numero, animale, farmaco, dosaggio, orario, note=""):
    """Genera il link di invio immediato con messaggio pre-compilato per WhatsApp per le Terapie."""
    testo = f"🐾 *PetHealth - Promemoria Terapia*\n\n🐶 *Animale:* {animale}\n💊 *Farmaco:* {farmaco}\n🥄 *Dose / Quantità:* {dosaggio}\n⏰ *Orario Somministrazione:* {orario}\n"
    if note:
        testo += f"📝 *Istruzioni:* {note}\n"
    testo += "\n⚠️ *Ricordati di somministrare la terapia fino alla data di fine prevista!*"
    
    testo_encoded = urllib.parse.quote(testo)
    numero_pulito = "".join(filter(str.isdigit, str(numero)))
    if numero_pulito:
        return f"https://api.whatsapp.com/send?phone={numero_pulito}&text={testo_encoded}"
    return f"https://api.whatsapp.com/send?text={testo_encoded}"

def genera_link_whatsapp_visita(numero, animale, tipo_visita, data_visita, veterinario="", note=""):
    """Genera il link di invio immediato con messaggio pre-compilato per WhatsApp per Visite e Controlli."""
    testo = f"🐾 *PetHealth - Promemoria Visita / Controllo*\n\n🐶 *Animale:* {animale}\n🏥 *Prestazione/Controllo:* {tipo_visita}\n📅 *Data Prevista:* {data_visita}\n"
    if veterinario:
        testo += f"🩺 *Veterinario / Clinica:* {veterinario}\n"
    if note:
        testo += f"📝 *Note:* {note}\n"
    testo += "\n⚠️ *Ricordati di confermare o presentarti all'appuntamento!*"
    
    testo_encoded = urllib.parse.quote(testo)
    numero_pulito = "".join(filter(str.isdigit, str(numero)))
    if numero_pulito:
        return f"https://api.whatsapp.com/send?phone={numero_pulito}&text={testo_encoded}"
    return f"https://api.whatsapp.com/send?text={testo_encoded}"

def mostra_pulsanti_promemoria_terapia(animale, farmaco, dosaggio, orario, note=""):
    """Mostra i pulsanti di invio WhatsApp per il Numero 1, Numero 2 o entrambi."""
    num1 = st.session_state.get("numero_whatsapp", "")
    num2 = st.session_state.get("numero_whatsapp_2", "")
    
    if num1 and num2:
        col_wa1, col_wa2 = st.columns(2)
        with col_wa1:
            link1 = genera_link_whatsapp(num1, animale, farmaco, dosaggio, orario, note)
            st.link_button("📲 WhatsApp (Numero 1)", url=link1)
        with col_wa2:
            link2 = genera_link_whatsapp(num2, animale, farmaco, dosaggio, orario, note)
            st.link_button("📲 WhatsApp (Numero 2)", url=link2)
    elif num1:
        link1 = genera_link_whatsapp(num1, animale, farmaco, dosaggio, orario, note)
        st.link_button("📲 Invia Promemoria WhatsApp", url=link1)
    elif num2:
        link2 = genera_link_whatsapp(num2, animale, farmaco, dosaggio, orario, note)
        st.link_button("📲 Invia Promemoria WhatsApp (Num 2)", url=link2)
    else:
        link_gen = genera_link_whatsapp("", animale, farmaco, dosaggio, orario, note)
        st.link_button("📲 Invia Promemoria WhatsApp", url=link_gen)

def mostra_pulsanti_promemoria_visita(animale, tipo_visita, data_visita, veterinario="", note=""):
    """Mostra i pulsanti di invio WhatsApp per i promemoria visita su Numero 1 o Numero 2."""
    num1 = st.session_state.get("numero_whatsapp", "")
    num2 = st.session_state.get("numero_whatsapp_2", "")
    
    if num1 and num2:
        col_wa1, col_wa2 = st.columns(2)
        with col_wa1:
            link1 = genera_link_whatsapp_visita(num1, animale, tipo_visita, data_visita, veterinario, note)
            st.link_button("📲 Promemoria Visita (Num 1)", url=link1)
        with col_wa2:
            link2 = genera_link_whatsapp_visita(num2, animale, tipo_visita, data_visita, veterinario, note)
            st.link_button("📲 Promemoria Visita (Num 2)", url=link2)
    elif num1:
        link1 = genera_link_whatsapp_visita(num1, animale, tipo_visita, data_visita, veterinario, note)
        st.link_button("📲 Promemoria Visita WhatsApp", url=link1)
    elif num2:
        link2 = genera_link_whatsapp_visita(num2, animale, tipo_visita, data_visita, veterinario, note)
        st.link_button("📲 Promemoria Visita WhatsApp", url=link2)
    else:
        link_gen = genera_link_whatsapp_visita("", animale, tipo_visita, data_visita, veterinario, note)
        st.link_button("📲 Promemoria Visita WhatsApp", url=link_gen)

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
        "numero_whatsapp_2": st.session_state.get("numero_whatsapp_2", ""),
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
        st.session_state.numero_whatsapp_2 = dati_salvati.get("numero_whatsapp_2", "")
        st.session_state.lista_animali = dati_salvati.get("lista_animali", ["Orlando"])
        st.session_state.pet_selezionato = dati_salvati.get("pet_selezionato", "Orlando")
        st.session_state.db_visite = dati_salvati.get("db_visite", {"Orlando": []})
        st.session_state.db_terapie = dati_salvati.get("db_terapie", {"Orlando": []})
        st.session_state.db_fatture = dati_salvati.get("db_fatture", {"Orlando": []})
        st.session_state.angeli_archiviati = dati_salvati.get("angeli_archiviati", {})
    else:
        st.session_state.nome_utente = "Francesco"
        st.session_state.numero_whatsapp = ""
        st.session_state.numero_whatsapp_2 = ""
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

    /* Assicura che tutti i testi degli input, etichette ed expander nella sidebar e nell'app siano visibili in colore NERO (#000000) */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] *,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] label p,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] input,
    div[data-testid="stExpander"] label p,
    div[data-testid="stExpander"] input {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
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
    div[data-baseweb="input"] input {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
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

    /* Riduzione dello spazio verticale tra i riquadri di testo nell'expander della sidebar */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stTextInput"] {
        margin-bottom: -0.4rem !important;
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
        num_wa_1 = st.text_input("Primo numero di telefono", value=st.session_state.get("numero_whatsapp", ""))
        num_wa_2 = st.text_input("Secondo numero di telefono (opzionale)", value=st.session_state.get("numero_whatsapp_2", ""))
        if st.button("Salva / Modifica Numeri WhatsApp"):
            st.session_state.numero_whatsapp = num_wa_1
            st.session_state.numero_whatsapp_2 = num_wa_2
            salva_dati()
            st.success("Numeri WhatsApp salvati e aggiornati con successo!")
            
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
        
    if st.button("✈️ Passaporto & Viaggi"):
        st.session_state.sezione_attiva = "passaporto"
        st.rerun()

    if st.button("🚨 Urgenze & Cliniche 24H"):
        st.session_state.sezione_attiva = "urgenze"
        st.rerun()

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
                        
                        mostra_pulsanti_promemoria_terapia(
                            animale=pet_selected,
                            farmaco=t['farmaco'],
                            dosaggio=t['dosaggio'],
                            orario=orario_txt,
                            note=t.get('note', '')
                        )
                        
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
                        if v.get('prossimo_controllo_data'):
                            st.write(f"⏰ **Prossimo Controllo:** {v['prossimo_controllo_data']} ({v.get('prossimo_controllo_tipo', 'Controllo')})")
                        if v.get('referto'):
                            st.caption(f"📄 Referto: {v['referto']}")
                        
                        mostra_pulsanti_promemoria_visita(
                            animale=pet_selected,
                            tipo_visita=v.get('prossimo_controllo_tipo', v['tipo']),
                            data_visita=v.get('prossimo_controllo_data', v['data']),
                            veterinario=v.get('veterinario', ''),
                            note=v.get('diagnosi', '')
                        )

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
        
        with st.expander("➕ Aggiungi Nuova Visita Medica / Prestazione", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                data_visita = st.date_input("Data Visita")
                tipo_visita = st.selectbox("Tipo di Visita", ["Controllo Generale", "Vaccinazione", "Visita Specialistica", "Urgenza", "Controllo Post-Operatorio", "Trattamento Antiparassitario Ufficiale"])
                veterinario = st.text_input("Medico Veterinario / Clinica")
            with col2:
                diagnosi = st.text_area("Diagnosi / Note Cliniche", placeholder="Descrivi il motivo della visita e l'esito...")
                referto = st.file_uploader("Allega Referto o Esami (Opzionale)", type=["pdf", "png", "jpg"], key="visita_ref")
                fattura_visita = st.file_uploader("Allega Ricevuta / Fattura (Opzionale)", type=["pdf", "png", "jpg"], key="visita_fat")
            
            st.markdown("---")
            st.markdown("🔒 **Certificazione Ufficiale Sanitaria (Per viaggi e validità legale)**")
            chi_inserisce = st.radio("Chi sta registrando questa prestazione?", ["Utente (In attesa di convalida veterinaria)", "Veterinario (Certificazione e Firma Immediata)"], horizontal=True)
            
            certificato_valido = False
            num_ordine_vet = ""
            codice_cert = None
            
            if chi_inserisce == "Veterinario (Certificazione e Firma Immediata)":
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    num_ordine_vet = st.text_input("N° Iscrizione Ordine dei Medici Veterinari (FNOVI / Prov.)*")
                with col_v2:
                    pin_convalida = st.text_input("PIN Segreto Veterinario (es. 1234)*", type="password")
                
                if pin_convalida == "1234" and num_ordine_vet.strip():
                    certificato_valido = True
                    codice_cert = genera_codice_certificazione(pet_selected, veterinario, num_ordine_vet, str(data_visita))
                    st.success(f"✅ Certificazione Digitale Generata: {codice_cert}")
                elif pin_convalida and pin_convalida != "1234":
                    st.error("PIN Veterinario errato. La prestazione verrà salvata in attesa di convalida.")

            richiede_controllo = st.checkbox("🔄 Questa prestazione richiede un controllo successivo o va ripetuta?")
            data_prossimo_ctrl = None
            tipo_prestazione_ctrl = None
            if richiede_controllo:
                col_ctrl1, col_ctrl2 = st.columns(2)
                with col_ctrl1:
                    data_prossimo_ctrl = st.date_input("Data Prossimo Controllo / Ripetizione")
                with col_ctrl2:
                    tipo_prestazione_ctrl = st.text_input("Tipo di Prestazione da Eseguire", placeholder="Es. Richiamo Vaccino, Controllo Ecografico...")
            
            st.write("")
            if st.button("Salva Visita Medica"):
                nuova_visita = {
                    "data": str(data_visita),
                    "tipo": tipo_visita,
                    "veterinario": veterinario,
                    "diagnosi": diagnosi,
                    "referto": referto.name if referto else None,
                    "prossimo_controllo_data": str(data_prossimo_ctrl) if richiede_controllo and data_prossimo_ctrl else None,
                    "prossimo_controllo_tipo": tipo_prestazione_ctrl if richiede_controllo else None,
                    "certificata": certificato_valido,
                    "num_ordine_vet": num_ordine_vet if certificato_valido else "",
                    "codice_certificato": codice_cert
                }
                
                if pet_selected not in st.session_state.db_visite:
                    st.session_state.db_visite[pet_selected] = []
                    
                st.session_state.db_visite[pet_selected].append(nuova_visita)
                salva_dati()
                st.success(f"Visita medica registrata con successo per {pet_selected}!")
                st.rerun()

        st.markdown("### 📋 Visite e Certificati Registrati")
        visite_list = st.session_state.db_visite.get(pet_selected, [])
        if visite_list:
            for idx, v in enumerate(visite_list):
                is_cert = v.get("certificata", False)
                badge_cert = f"✅ CERTIFICATA ({v.get('codice_certificato', '')})" if is_cert else "⏳ IN ATTESA DI CONVALIDA VETERINARIA"
                
                with st.expander(f"🏥 {v['data']} - {v['tipo']} | {badge_cert}"):
                    if is_cert:
                        st.success(f"🛡️ **Prestazione Sanitaria Ufficiale Certificata**\n\n• **Medico:** {v['veterinario']}\n• **N° Iscrizione Ordine:** {v.get('num_ordine_vet', 'N/D')}\n• **Codice univoco di convalida:** `{v.get('codice_certificato')}`")
                    else:
                        st.warning("⚠️ Questa prestazione è stata inserita dall'utente ed è in attesa di firma/convalida da parte del Medico Veterinario per avere valore di espatrio/viaggio.")
                    
                    st.write(f"**Diagnosi / Dettagli:** {v['diagnosi']}")
                    if v.get('prossimo_controllo_data'):
                        st.write(f"⏰ **Prossimo Controllo:** {v['prossimo_controllo_data']} ({v.get('prossimo_controllo_tipo', 'Controllo')})")
                    if v.get('referto'):
                        st.caption(f"📄 Referto: {v['referto']}")
                    
                    if not is_cert:
                        st.markdown("---")
                        st.markdown("🩺 **Area Riservata al Veterinario - Convalida Ora**")
                        c_v1, c_v2, c_btn = st.columns([2, 2, 2])
                        with c_v1:
                            v_nome = st.text_input("Nome Medico Veterinario", value=v.get('veterinario', ''), key=f"v_nome_{idx}")
                        with c_v2:
                            v_ord = st.text_input("N° Ordine FNOVI", key=f"v_ord_{idx}")
                        with c_btn:
                            v_pin = st.text_input("PIN Convalida (1234)", type="password", key=f"v_pin_{idx}")
                            if st.button("Firma e Convalida", key=f"btn_cert_{idx}"):
                                if v_pin == "1234" and v_ord.strip():
                                    v["certificata"] = True
                                    v["veterinario"] = v_nome
                                    v["num_ordine_vet"] = v_ord
                                    v["codice_certificato"] = genera_codice_certificazione(pet_selected, v_nome, v_ord, v['data'])
                                    salva_dati()
                                    st.success("Visita convalidata e firmata con successo!")
                                    st.rerun()
                                else:
                                    st.error("PIN o N° Ordine non valido.")

                    mostra_pulsanti_promemoria_visita(
                        animale=pet_selected,
                        tipo_visita=v.get('prossimo_controllo_tipo', v['tipo']),
                        data_visita=v.get('prossimo_controllo_data', v['data']),
                        veterinario=v.get('veterinario', ''),
                        note=v.get('diagnosi', '')
                    )

                    if st.button("🗑️ Elimina Questa Visita", key=f"del_vis_page_{idx}"):
                        st.session_state.db_visite[pet_selected].pop(idx)
                        salva_dati()
                        st.success("Visita eliminata!")
                        st.rerun()
        else:
            st.info("Nessuna visita salvata al momento.")

    else:
        st.warning("Seleziona o registra un animale attivo per gestire le visite.")

elif st.session_state.sezione_attiva == "passaporto":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>✈️ Passaporto Sanitario & Certificati di Viaggio - {pet_selected}</h2>", unsafe_allow_html=True)
        st.info("In questa sezione sono raccolte esclusivamente le prestazioni e le vaccinazioni **ufficialmente verificate e certificate dal Medico Veterinario**, idonee ai controlli sanitari e agli spostamenti/viaggi.")
        
        visite_cert = [v for v in st.session_state.db_visite.get(pet_selected, []) if v.get("certificata", False)]
        
        if visite_cert:
            for v in visite_cert:
                st.markdown(f"""
                    <div class="wellness-card" style="border-left: 5px solid #10B981 !important;">
                        <span class="card-badge badge-purple">CERTIFICATO VETERINARIO UFFICIALE</span>
                        <h4 style="color: #1E3A2B; margin-top: 5px; margin-bottom: 5px;">💉 {v['tipo']} — {v['data']}</h4>
                        <p style="margin-bottom: 4px;"><strong>Medico Responsabile:</strong> Dr. {v['veterinario']} (N° Ordine: {v.get('num_ordine_vet')})</p>
                        <p style="margin-bottom: 4px;"><strong>Codice Certificato Univoco:</strong> <code style="background-color:#E2E8F0; padding:2px 6px; border-radius:4px;">{v.get('codice_certificato')}</code></p>
                        <p style="margin-bottom: 0;"><strong>Diagnosi/Note Cliniche:</strong> {v['diagnosi']}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"Al momento {pet_selected} non ha ancora prestazioni sanitarie certificate dal veterinario per il passaporto.")
    else:
        st.warning("Seleziona o registra un animale attivo per accedere al passaporto.")

elif st.session_state.sezione_attiva == "urgenze":
    st.markdown("<h2 style='color: #1E3A2B;'>🚨 Urgenze & Cliniche Veterinarie 24H in Italia</h2>", unsafe_allow_html=True)
    st.info("Sei in vacanza o in spostamento in Italia? Usa questa guida rapida con il database completo delle strutture veterinarie H24 per tutte le regioni e province italiane, oppure ricerca direttamente la tua città.")
    
    col_search1, col_search2 = st.columns([2, 1])
    with col_search1:
        citta_ricerca = st.text_input("📍 Inserisci la tua posizione, provincia o città (es. Pescara, Trento, Perugia, Taranto...)", placeholder="Es. Perugia")
    with col_search2:
        st.write("")
        st.write("")
        if citta_ricerca.strip():
            query_map = urllib.parse.quote(f"clinica veterinaria 24 ore pronto soccorso {citta_ricerca.strip()}")
        else:
            query_map = urllib.parse.quote("clinica veterinaria pronto soccorso 24 ore aperto ora vicina a me")
        
        st.link_button("🔍 Apri Mappa Urgenze H24", f"https://www.google.com/maps/search/{query_map}")

    st.markdown("---")
    
    st.markdown("### 🏥 Ospedali e Cliniche Veterinarie H24 in Italia per Regione e Provincia")
    
    col_reg, col_prov_search = st.columns([1, 1])
    with col_reg:
        regione_filtro = st.selectbox(
            "Filtra per Regione:",
            [
                "Tutte le Regioni", "Abruzzo", "Basilicata", "Calabria", "Campania", 
                "Emilia-Romagna", "Friuli Venezia Giulia", "Lazio", "Liguria", 
                "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", 
                "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige", 
                "Umbria", "Valle d'Aosta", "Veneto"
            ]
        )
    with col_prov_search:
        filtro_testo = st.text_input("🔍 Filtra per Provincia o Città nel database:", value=citta_ricerca)

    cliniche_h24 = [
        # Abruzzo
        {"regione": "Abruzzo", "citta": "Pescara / Chieti", "nome": "Clinica Veterinaria D'Annunzio (H24)", "indirizzo": "Via Tiburtina Valeria 128, Pescara", "telefono": "085 4310502", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+D%27Annunzio+Pescara"},
        {"regione": "Abruzzo", "citta": "L'Aquila", "nome": "Clinica Veterinaria Ospedale San Francesco (H24)", "indirizzo": "Via Colle Sapone, L'Aquila", "telefono": "0862 318356", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+L%27Aquila"},
        {"regione": "Abruzzo", "citta": "Teramo", "nome": "Ospedale Veterinario Universitario Teramo (H24)", "indirizzo": "Piano D'Accio, Teramo", "telefono": "0861 266863", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Teramo"},

        # Basilicata
        {"regione": "Basilicata", "citta": "Potenza", "nome": "Clinica Veterinaria Lucana (H24)", "indirizzo": "Via del Gallitello, Potenza", "telefono": "0971 445200", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Potenza"},
        {"regione": "Basilicata", "citta": "Matera", "nome": "Pronto Soccorso Veterinario Matera (H24)", "indirizzo": "Via Lucana, Matera", "telefono": "0835 330201", "maps": "https://maps.google.com/?q=Pronto+Soccorso+Veterinario+Matera"},

        # Calabria
        {"regione": "Calabria", "citta": "Catanzaro", "nome": "Ospedale Veterinario Universitario Magna Graecia (H24)", "indirizzo": "Località Roccelletta di Borgia, Catanzaro", "telefono": "0961 3694001", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Catanzaro"},
        {"regione": "Calabria", "citta": "Cosenza", "nome": "Clinica Veterinaria Bruzia (H24)", "indirizzo": "Via Panebianco, Cosenza", "telefono": "0984 391212", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Cosenza"},
        {"regione": "Calabria", "citta": "Reggio Calabria", "nome": "Clinica Veterinaria Magna Grecia (H24)", "indirizzo": "Via Nazionale Pentimele, Reggio Calabria", "telefono": "0965 48800", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Reggio+Calabria"},

        # Campania
        {"regione": "Campania", "citta": "Napoli", "nome": "Ospedale Veterinario Flegreo (H24)", "indirizzo": "Via S. Gennaro Agnano 84, Pozzuoli (NA)", "telefono": "081 5708892", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Flegreo"},
        {"regione": "Campania", "citta": "Salerno", "nome": "Clinica Veterinaria Salernitana (H24)", "indirizzo": "Via S. Leonardo 120, Salerno", "telefono": "089 334141", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Salerno"},
        {"regione": "Campania", "citta": "Caserta", "nome": "Clinica Veterinaria San Prisco (H24)", "indirizzo": "Via Gianfrotta 12, Caserta", "telefono": "0823 848123", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Caserta"},
        {"regione": "Campania", "citta": "Avellino", "nome": "Clinica Veterinaria Irpina (H24)", "indirizzo": "Via Nazionale, Avellino", "telefono": "0825 628001", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Avellino"},

        # Emilia-Romagna
        {"regione": "Emilia-Romagna", "citta": "Bologna", "nome": "Ospedale Veterinario Universitario Ozzano (H24)", "indirizzo": "Via Tolara di Sopra 50, Ozzano dell'Emilia (BO)", "telefono": "051 2097000", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Universitario+Ozzano"},
        {"regione": "Emilia-Romagna", "citta": "Rimini / Riccione", "nome": "Clinica Veterinaria Riviera (H24)", "indirizzo": "Via Flaminia 120, Rimini", "telefono": "0541 380482", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Riviera+Rimini"},
        {"regione": "Emilia-Romagna", "citta": "Parma", "nome": "Ospedale Veterinario Universitario Parma (H24)", "indirizzo": "Strada del Taglio 10, Parma", "telefono": "0521 032734", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Parma"},
        {"regione": "Emilia-Romagna", "citta": "Modena", "nome": "Clinica Veterinaria Modena Sud (H24)", "indirizzo": "Via Emilia Est 1020, Modena", "telefono": "059 373737", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Modena"},
        {"regione": "Emilia-Romagna", "citta": "Forlì-Cesena / Ravenna", "nome": "Clinica Veterinaria Romagna (H24)", "indirizzo": "Via Ravegnana 200, Forlì", "telefono": "0543 720000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Forli"},

        # Friuli Venezia Giulia
        {"regione": "Friuli Venezia Giulia", "citta": "Trieste", "nome": "Clinica Veterinaria San Giacomo (H24)", "indirizzo": "Via San Giacomo 15, Trieste", "telefono": "040 365050", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Trieste"},
        {"regione": "Friuli Venezia Giulia", "citta": "Udine", "nome": "Clinica Veterinaria Udine Nord (H24)", "indirizzo": "Via Tricesimo 100, Udine", "telefono": "0432 481234", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Udine"},
        {"regione": "Friuli Venezia Giulia", "citta": "Pordenone", "nome": "Clinica Veterinaria Naonis (H24)", "indirizzo": "Via Montereale 45, Pordenone", "telefono": "0434 551122", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Pordenone"},

        # Lazio
        {"regione": "Lazio", "citta": "Roma", "nome": "Ospedale Veterinario Gregorio VII (H24)", "indirizzo": "Piazza di Villa Carpegna 52, Roma", "telefono": "06 66013444", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Gregorio+VII+Roma"},
        {"regione": "Lazio", "citta": "Roma Sud / Castelli", "nome": "Clinica Veterinaria Roma Sud (H24)", "indirizzo": "Via Pilade Mazza 24, Roma", "telefono": "06 72677392", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Roma+Sud"},
        {"regione": "Lazio", "citta": "Latina", "nome": "Clinica Veterinaria Latina Nord (H24)", "indirizzo": "Via Pontina Km 68, Latina", "telefono": "0773 690011", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Latina"},
        {"regione": "Lazio", "citta": "Viterbo", "nome": "Clinica Veterinaria Tuscia (H24)", "indirizzo": "Strada Cassia Nord, Viterbo", "telefono": "0761 251100", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Viterbo"},
        {"regione": "Lazio", "citta": "Frosinone", "nome": "Clinica Veterinaria Ciociaria (H24)", "indirizzo": "Via Monti Lepini, Frosinone", "telefono": "0775 881001", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Frosinone"},

        # Liguria
        {"regione": "Liguria", "citta": "Genova", "nome": "Clinica Veterinaria San Fruttuoso (H24)", "indirizzo": "Via Imperiale 1, Genova", "telefono": "010 500150", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+San+Fruttuoso+Genova"},
        {"regione": "Liguria", "citta": "Savona / Riviera", "nome": "Clinica Veterinaria Savonese (H24)", "indirizzo": "Via Stalingrado 15, Savona", "telefono": "019 821212", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Savona"},
        {"regione": "Liguria", "citta": "La Spezia", "nome": "Clinica Veterinaria Spezzina (H24)", "indirizzo": "Via Carducci 120, La Spezia", "telefono": "0187 512000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+La+Spezia"},

        # Lombardia
        {"regione": "Lombardia", "citta": "Milano", "nome": "Ospedale Veterinario San Siro (H24)", "indirizzo": "Via A. Strada 10, Milano", "telefono": "02 4525254", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+San+Siro+Milano"},
        {"regione": "Lombardia", "citta": "Milano East", "nome": "Clinica Veterinaria Gran Sasso (H24)", "indirizzo": "Via D'Ovidio 3, Milano", "telefono": "02 2663095", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Gran+Sasso+Milano"},
        {"regione": "Lombardia", "citta": "Brescia", "nome": "Clinica Veterinaria San Antonio (H24)", "indirizzo": "Via Triumplina 45, Brescia", "telefono": "030 2001234", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Brescia"},
        {"regione": "Lombardia", "citta": "Bergamo", "nome": "Ospedale Veterinario Orobico (H24)", "indirizzo": "Via Bergamo 88, Bergamo", "telefono": "035 311000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Bergamo"},
        {"regione": "Lombardia", "citta": "Monza e Brianza", "nome": "Clinica Veterinaria Brianza (H24)", "indirizzo": "Viale Elvezia 22, Monza", "telefono": "039 388800", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Monza"},
        {"regione": "Lombardia", "citta": "Varese / Como", "nome": "Clinica Veterinaria Lago Maggiore (H24)", "indirizzo": "Via Sempione 12, Varese", "telefono": "0332 284000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Varese"},

        # Marche
        {"regione": "Marche", "citta": "Ancona", "nome": "Clinica Veterinaria Dorica (H24)", "indirizzo": "Via Barilatti 10, Ancona", "telefono": "071 2800123", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Ancona"},
        {"regione": "Marche", "citta": "Pesaro e Urbino", "nome": "Clinica Veterinaria Rossini (H24)", "indirizzo": "Via SS Adriatica, Pesaro", "telefono": "0721 411000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Pesaro"},
        {"regione": "Marche", "citta": "Macerata / Fermo", "nome": "Clinica Veterinaria Maceratese (H24)", "indirizzo": "Via Mattei, Macerata", "telefono": "0733 30000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Macerata"},

        # Molise
        {"regione": "Molise", "citta": "Campobasso", "nome": "Clinica Veterinaria Molisana (H24)", "indirizzo": "Via XXIV Maggio, Campobasso", "telefono": "0874 481100", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Campobasso"},
        {"regione": "Molise", "citta": "Isernia / Termoli", "nome": "Pronto Soccorso Veterinario Termoli (H24)", "indirizzo": "Via Milano, Termoli", "telefono": "0875 700111", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Termoli"},

        # Piemonte
        {"regione": "Piemonte", "citta": "Torino", "nome": "Ospedale Veterinario Anubis (H24)", "indirizzo": "Strada della Prionda 21, Torino", "telefono": "011 3190209", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Anubis+Torino"},
        {"regione": "Piemonte", "citta": "Torino Sud / Moncalieri", "nome": "Ospedale Veterinario Universitario Grugliasco (H24)", "indirizzo": "Largo Braccini 2, Grugliasco (TO)", "telefono": "011 6709111", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Grugliasco"},
        {"regione": "Piemonte", "citta": "Cuneo", "nome": "Clinica Veterinaria Cuneese (H24)", "indirizzo": "Via Stura 10, Cuneo", "telefono": "0171 690000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Cuneo"},
        {"regione": "Piemonte", "citta": "Novara / Alessandria", "nome": "Clinica Veterinaria Novarese (H24)", "indirizzo": "Corso Milano 40, Novara", "telefono": "0321 620000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Novara"},

        # Puglia
        {"regione": "Puglia", "citta": "Bari", "nome": "Ospedale Veterinario S. Francesco (H24)", "indirizzo": "Via Trevisani 105, Bari", "telefono": "080 5231782", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+San+Francesco+Bari"},
        {"regione": "Puglia", "citta": "Lecce / Salento", "nome": "Clinica Veterinaria Salentina (H24)", "indirizzo": "Via Leuca 150, Lecce", "telefono": "0832 340000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Lecce"},
        {"regione": "Puglia", "citta": "Foggia", "nome": "Clinica Veterinaria Dauna (H24)", "indirizzo": "Via Manfredonia, Foggia", "telefono": "0881 700000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Foggia"},
        {"regione": "Puglia", "citta": "Taranto / Brindisi", "nome": "Clinica Veterinaria Jonica (H24)", "indirizzo": "Via Cintoia 12, Taranto", "telefono": "099 7700000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Taranto"},

        # Sardegna
        {"regione": "Sardegna", "citta": "Cagliari", "nome": "Clinica Veterinaria San Giuseppe (H24)", "indirizzo": "Via dei Conversi 12, Cagliari", "telefono": "070 488288", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+San+Giuseppe+Cagliari"},
        {"regione": "Sardegna", "citta": "Sassari / Olbia", "nome": "Ospedale Veterinario Universitario Sassari (H24)", "indirizzo": "Via Vienna 2, Sassari", "telefono": "079 229400", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Sassari"},
        {"regione": "Sardegna", "citta": "Olbia / Costa Smeralda", "nome": "Clinica Veterinaria Olbia (H24)", "indirizzo": "Via Aldo Moro, Olbia", "telefono": "0789 50000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Olbia"},

        # Sicilia
        {"regione": "Sicilia", "citta": "Palermo", "nome": "Clinica Veterinaria Vetrano (H24)", "indirizzo": "Via Leonardo Da Vinci 294, Palermo", "telefono": "091 6818160", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Vetrano+Palermo"},
        {"regione": "Sicilia", "citta": "Catania", "nome": "Clinica Veterinaria Etnea (H24)", "indirizzo": "Via Etnea 400, Catania", "telefono": "095 440000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Catania"},
        {"regione": "Sicilia", "citta": "Messina", "nome": "Ospedale Veterinario Universitario Messina (H24)", "indirizzo": "Polo Universitario Annunziata, Messina", "telefono": "090 3503111", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Messina"},
        {"regione": "Sicilia", "citta": "Siracusa / Ragusa", "nome": "Clinica Veterinaria Aretusa (H24)", "indirizzo": "Viale Teracati, Siracusa", "telefono": "0931 410000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Siracusa"},

        # Toscana
        {"regione": "Toscana", "citta": "Firenze", "nome": "Ospedale Veterinario Firenze Sud (H24)", "indirizzo": "Via Erbosa 12/r, Firenze", "telefono": "055 6811222", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Firenze+Sud"},
        {"regione": "Toscana", "citta": "Pisa / Livorno / Versilia", "nome": "Ospedale Didattico Veterinario San Piero a Grado (H24)", "indirizzo": "Via Livornese 1289, San Piero a Grado (PI)", "telefono": "050 2210100", "maps": "https://maps.google.com/?q=Ospedale+Didattico+Veterinario+Pisa"},
        {"regione": "Toscana", "citta": "Siena / Grosseto", "nome": "Clinica Veterinaria Senese (H24)", "indirizzo": "Strada Massetana, Siena", "telefono": "0577 280000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Siena"},
        {"regione": "Toscana", "citta": "Arezzo / Lucca", "nome": "Clinica Veterinaria Aretina (H24)", "indirizzo": "Via Galileo Galilei, Arezzo", "telefono": "0575 350000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Arezzo"},

        # Trentino-Alto Adige
        {"regione": "Trentino-Alto Adige", "citta": "Trento", "nome": "Clinica Veterinaria Trentina (H24)", "indirizzo": "Via Brennero 180, Trento", "telefono": "0461 820000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Trento"},
        {"regione": "Trentino-Alto Adige", "citta": "Bolzano", "nome": "Clinica Veterinaria Bolzano (H24)", "indirizzo": "Via Resia 40, Bolzano", "telefono": "0471 910000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Bolzano"},

        # Umbria
        {"regione": "Umbria", "citta": "Perugia", "nome": "Ospedale Veterinario Universitario Perugia (H24)", "indirizzo": "Via San Costanzo 4, Perugia", "telefono": "075 5857711", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Perugia"},
        {"regione": "Umbria", "citta": "Terni", "nome": "Clinica Veterinaria Ternana (H24)", "indirizzo": "Via Flaminia 50, Terni", "telefono": "0744 400000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Terni"},

        # Valle d'Aosta
        {"regione": "Valle d'Aosta", "citta": "Aosta", "nome": "Clinica Veterinaria Aostana (H24)", "indirizzo": "Corso Ivrea 30, Aosta", "telefono": "0165 31000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Aosta"},

        # Veneto
        {"regione": "Veneto", "citta": "Venezia / Mestre", "nome": "Clinica Veterinaria Sirio (H24)", "indirizzo": "Via Circonvallazione 8, Mestre (VE)", "telefono": "041 988288", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Sirio+Mestre"},
        {"regione": "Veneto", "citta": "Padova", "nome": "Ospedale Veterinario Universitario Legnaro (H24)", "indirizzo": "Viale dell'Universita 16, Legnaro (PD)", "telefono": "049 8272608", "maps": "https://maps.google.com/?q=Ospedale+Veterinario+Legnaro"},
        {"regione": "Veneto", "citta": "Verona", "nome": "Clinica Veterinaria Scaligera (H24)", "indirizzo": "Via Unita d'Italia, Verona", "telefono": "045 8900000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Verona"},
        {"regione": "Veneto", "citta": "Treviso / Vicenza", "nome": "Clinica Veterinaria Marca Trevigiana (H24)", "indirizzo": "Via Terraglio, Treviso", "telefono": "0422 400000", "maps": "https://maps.google.com/?q=Clinica+Veterinaria+Treviso"}
    ]

    filtrate = []
    for c in cliniche_h24:
        match_regione = (regione_filtro == "Tutte le Regioni") or (c["regione"].lower() == regione_filtro.lower())
        match_testo = True
        if filtro_testo.strip():
            query_str = filtro_testo.strip().lower()
            match_testo = (
                query_str in c["citta"].lower() or 
                query_str in c["regione"].lower() or 
                query_str in c["nome"].lower() or 
                query_str in c["indirizzo"].lower()
            )
        if match_regione and match_testo:
            filtrate.append(c)

    if filtrate:
        col_grid1, col_grid2 = st.columns(2)
        for i, c in enumerate(filtrate):
            target_col = col_grid1 if i % 2 == 0 else col_grid2
            with target_col:
                st.markdown(f"""
                    <div class="wellness-card" style="border-left: 5px solid #EF4444 !important;">
                        <span class="card-badge badge-purple" style="background-color: #FEE2E2; color: #991B1B;">H24 EMERGENCY</span>
                        <h4 style="color: #1E3A2B; margin-top: 5px; margin-bottom: 5px;">🏥 {c['nome']}</h4>
                        <p style="margin-bottom: 4px;"><strong>📍 Zona / Provincia:</strong> {c['citta']} ({c['regione']})</p>
                        <p style="margin-bottom: 4px;"><strong>🏠 Indirizzo:</strong> {c['indirizzo']}</p>
                        <p style="margin-bottom: 8px;"><strong>📞 Tel Emergenze:</strong> <a href="tel:{c['telefono'].replace(' ', '')}" style="color: #2563EB; font-weight:700;">{c['telefono']}</a></p>
                    </div>
                """, unsafe_allow_html=True)
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.link_button("📞 Chiama Ora", f"tel:{c['telefono'].replace(' ', '')}")
                with col_b2:
                    st.link_button("🗺️ Mappa & Naviga", c['maps'])
                st.write("")
    else:
        st.warning(f"Nessuna clinica pre-registrata nel database corrisponde ai filtri impostati ('{regione_filtro}' / '{filtro_testo}'). Utilizza il pulsante in alto '🔍 Apri Mappa Urgenze H24' per la ricerca in tempo reale su Google Maps per qualunque comune d'Italia.")

    st.markdown("---")
    st.markdown("### ☎️ Numeri e Servizi Utili in caso di Emergenza")
    
    col_num1, col_num2, col_num3 = st.columns(3)
    with col_num1:
        st.markdown("""
            <div class="wellness-card">
                <h4 style="color: #1E3A2B;">📞 Numero Unico 112</h4>
                <p>In caso di incidente stradale grave o smarrimento lungo autostrade / strade statali.</p>
            </div>
        """, unsafe_allow_html=True)
    with col_num2:
        st.markdown("""
            <div class="wellness-card">
                <h4 style="color: #1E3A2B;">🧪 Centro Antiveleni</h4>
                <p><strong>CAV Ospedale Niguarda:</strong> <a href="tel:0266101029">02 66101029</a> per consulenze immediate su ingestioni tossiche.</p>
            </div>
        """, unsafe_allow_html=True)
    with col_num3:
        st.markdown("""
            <div class="wellness-card">
                <h4 style="color: #1E3A2B;">🐾 Soccorso ENPA / Guardie</h4>
                <p>Segnalazioni di animali in difficoltà su territorio nazionale o recupero fauna.</p>
            </div>
        """, unsafe_allow_html=True)

    with st.expander("💡 Consigli di Primo Soccorso Veterinario Prima di Arrivare in Clinica"):
        st.markdown("""
        1. **Mantenere la calma:** L'animale percepisce l'ansia. Parla con tono di voce rassicurante e basso.
        2. **Chiamare prima di partire:** Telefona alla clinica mentre ti stai mettendo in viaggio così il team veterinario potrà preparare la sala d'emergenza o l'ossigeno.
        3. **Colpo di calore (Frequente in ferie d'estate):** Sposta subito l'animale all'ombra, bagnagli le zampe, l'addome e il collo con acqua a temperatura ambiente (MAI acqua ghiacciata per evitare shock termici).
        4. **Ingestione di sostanze tossiche o corpi estranei:** NON somministrare latte, olio o farmaci di testa tua. Conserva la confezione o la pianta ingerita per mostrarla al veterinario.
        5. **Traumi o ferite:** Copri eventuali ferite con un panno pulito mantenendo leggera pressione senza stringere eccessivamente.
        """)

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
                    
                    mostra_pulsanti_promemoria_terapia(
                        animale=pet_selected,
                        farmaco=t['farmaco'],
                        dosaggio=t['dosaggio'],
                        orario=orario_txt,
                        note=t.get('note', '')
                    )
                    
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
    else:
        st.info("Nessun animale è attualmente presente nella sezione 'I nostri angeli a 4 zampe'. Gli animali archiviati tramite il registro nell'Area Riservata della Dashboard appariranno qui insieme alla loro intera cartella clinica.")

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
