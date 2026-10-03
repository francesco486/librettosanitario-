import streamlit as st
import json
import os
import urllib.parse
import hashlib
import uuid
from datetime import datetime, date
import streamlit.components.v1 as components

if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

st.set_page_config(
    page_title="PetHealth - Wellness & Care",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

DATA_FILE = "data_pethealth.json"

def hash_password(password):
    """Calcola l'hash SHA-256 della password per una conservazione sicura nel database."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def genera_id_veterinario_permanente(num_ordine, provincia=""):
    """Genera un ID univoco, deterministico e PERMANENTE per il Veterinario basato su FNOVI e Provincia."""
    pulito = f"{str(num_ordine).strip().upper()}-{str(provincia).strip().upper()}"
    hash_vet = hashlib.sha256(pulito.encode('utf-8')).hexdigest()[:6].upper()
    return f"VET-ID-{hash_vet}"

def genera_codice_certificazione(pet_name, vet_id, date_str, prestazione):
    """Genera un codice univoco di certificazione sanitaria valida."""
    raw = f"{pet_name}-{vet_id}-{date_str}-{prestazione}"
    return f"CERT-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:8].upper()}"

def carica_dati():
    """Carica i dati del database da file JSON locale se esistente."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def salva_dati():
    """Salva lo stato globale e degli utenti registrati nel file JSON."""
    dati = {
        "users": st.session_state.get("db_users", {}),
        "db_veterinari": st.session_state.get("db_veterinari", {})
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Errore durante il salvataggio dei dati: {e}")

if "db_users" not in st.session_state or "db_veterinari" not in st.session_state:
    dati_salvati = carica_dati()
    if dati_salvati and "users" in dati_salvati:
        st.session_state.db_users = dati_salvati.get("users", {})
        st.session_state.db_veterinari = dati_salvati.get("db_veterinari", {})
    else:
        st.session_state.db_users = {}
        st.session_state.db_veterinari = {}
        salva_dati()

if "logged_user_email" not in st.session_state:
    st.session_state.logged_user_email = None

if "sezione_attiva" not in st.session_state:
    st.session_state.sezione_attiva = "dashboard"

if "verification_pending_email" not in st.session_state:
    st.session_state.verification_pending_email = None

def cambia_sezione(nuova_sezione):
    """Imposta la sezione attiva e richiede la chiusura automatica della sidebar."""
    st.session_state.sezione_attiva = nuova_sezione
    st.session_state.trigger_close_sidebar = True
    st.rerun()

def mostra_scansionatore_barre(titolo="📷 Scansiona Etichetta Vaccino o Microchip"):
    """Mostra un lettore avanzato di etichette e microchip con rimozione automatica dello sfondo ed esaltazione testo."""
    st.markdown(f"##### {titolo}")
    st.caption("Inquadra l'etichetta del vaccino o del microchip nel riquadro verde. Clicca su 'Scatta ed Isola Etichetta' per rimuovere lo sfondo e pulire la scansione.")
    
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
        <style>
            body { font-family: -apple-system, sans-serif; margin: 0; padding: 2px; background-color: #f8f7f2; text-align: center; }
            .main-wrapper { max-width: 480px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; }
            .controls-panel { width: 100%; display: flex; gap: 8px; justify-content: center; margin-bottom: 10px; flex-wrap: wrap; }
            .btn-action { background-color: #16a34a; color: #ffffff !important; border: none; padding: 12px 18px; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 0.95rem; flex: 1; min-width: 160px; box-shadow: 0 4px 6px rgba(0,0,0,0.15); transition: background-color 0.2s; }
            .btn-action:hover { opacity: 0.9; }
            .btn-action:active { transform: scale(0.98); }
            .btn-sec { background-color: #475569 !important; }
            .scanner-container { position: relative; width: 100%; max-height: 280px; border-radius: 16px; overflow: hidden; border: 2.5px solid #1E3A2B; background: #000; display: flex; justify-content: center; align-items: center; }
            #video-feed { width: 100%; max-height: 280px; object-fit: cover; display: block; }
            .scan-mask {
                position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                pointer-events: none; display: flex; align-items: center; justify-content: center;
                box-shadow: inset 0 0 0 2000px rgba(15, 23, 42, 0.65);
            }
            .target-box {
                width: 240px; height: 120px; border: 3px solid #22c55e; border-radius: 12px;
                box-shadow: 0 0 20px rgba(34, 197, 94, 0.8); position: relative; animation: pulseGlow 2s infinite;
            }
            @keyframes pulseGlow {
                0% { border-color: #22c55e; box-shadow: 0 0 10px rgba(34, 197, 94, 0.6); }
                50% { border-color: #86efac; box-shadow: 0 0 25px rgba(134, 239, 172, 1); }
                100% { border-color: #22c55e; box-shadow: 0 0 10px rgba(34, 197, 94, 0.6); }
            }
            #result-box { width: 100%; margin-top: 10px; padding: 12px; background: #FFFFFF; border-radius: 12px; border: 1.5px solid #22c55e; display: none; box-sizing: border-box; }
            .code-text { font-family: monospace; font-size: 1.05rem; font-weight: bold; color: #1E3A2B; background: #F1F5F9; padding: 6px 10px; border-radius: 6px; word-break: break-all; margin-top: 6px; }
            #cropped-preview { max-width: 100%; height: auto; max-height: 160px; border-radius: 8px; border: 1px solid #CBD5E1; margin-top: 8px; object-fit: contain; background-color: #ffffff; }
        </style>
    </head>
    <body>
        <div class="main-wrapper">
            <div class="controls-panel">
                <button class="btn-action" onclick="scattaRitaglio()">📸 Scatta ed Isola Etichetta</button>
                <button class="btn-action btn-sec" onclick="riavviaCamera()">🔄 Riavvia Camera</button>
            </div>

            <div class="scanner-container">
                <video id="video-feed" autoplay playsinline muted></video>
                <div class="scan-mask"><div class="target-box" id="target-box"></div></div>
            </div>

            <div id="result-box">
                <div style="color:#15803d; font-weight:bold; margin-bottom:4px;">✅ Etichetta Acquisita & Sfondo Eliminato</div>
                <img id="cropped-preview" alt="Etichetta Pulita e Isolata">
                <div id="code-output" class="code-text">Etichetta/Fustella Acquisita</div>
                <button class="btn-action" style="margin-top:8px; width: 100%;" onclick="copiaEIncolla()">📋 Copia Testo Rilevato</button>
            </div>
        </div>

        <canvas id="crop-canvas" style="display:none;"></canvas>

        <script>
            let currentStream = null;
            const video = document.getElementById('video-feed');

            async function avviaFotocamera() {
                try {
                    if (currentStream) {
                        currentStream.getTracks().forEach(track => track.stop());
                    }
                    const constraints = {
                        video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }
                    };
                    currentStream = await navigator.mediaDevices.getUserMedia(constraints);
                    video.srcObject = currentStream;
                } catch (err) {
                    console.error("Errore accesso fotocamera:", err);
                }
            }

            // ALGORITMO DI RIMOZIONE DELLO SFONDO E PULIZIA CARTA
            function rimuoviSfondoEPulisci(ctx, width, height) {
                const imgData = ctx.getImageData(0, 0, width, height);
                const d = imgData.data;

                // Calcolo luminosità media per adattamento dinamico
                let sumLum = 0;
                for (let i = 0; i < d.length; i += 4) {
                    sumLum += (0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2]);
                }
                const avgLum = sumLum / (width * height);
                const threshold = Math.min(Math.max(avgLum * 1.02, 115), 185);

                for (let i = 0; i < d.length; i += 4) {
                    let r = d[i], g = d[i+1], b = d[i+2];
                    let lum = 0.299 * r + 0.587 * g + 0.114 * b;

                    // Se il pixel appartiene allo sfondo / tavolo / carta chiara, rendilo BIANCO PURO (#FFFFFF)
                    if (lum > threshold) {
                        d[i] = 255;
                        d[i+1] = 255;
                        d[i+2] = 255;
                    } else {
                        // Esalta il contrasto del testo e delle righe dei codici a barre
                        let factor = 1.35;
                        d[i] = Math.max(0, Math.min(255, (r - 128) * factor + 128 - 25));
                        d[i+1] = Math.max(0, Math.min(255, (g - 128) * factor + 128 - 25));
                        d[i+2] = Math.max(0, Math.min(255, (b - 128) * factor + 128 - 25));
                    }
                }
                ctx.putImageData(imgData, 0, 0);
            }

            function scattaRitaglio() {
                if (!video.videoWidth) return;
                const canvas = document.getElementById('crop-canvas');
                const ctx = canvas.getContext('2d');

                const videoWidth = video.videoWidth;
                const videoHeight = video.videoHeight;
                
                const cropW = Math.floor(videoWidth * 0.65);
                const cropH = Math.floor(videoHeight * 0.35);
                const cropX = Math.floor((videoWidth - cropW) / 2);
                const cropY = Math.floor((videoHeight - cropH) / 2);

                canvas.width = cropW;
                canvas.height = cropH;

                ctx.drawImage(video, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH);

                // Applicazione dell'algoritmo di pulizia e isolamento dello sfondo
                rimuoviSfondoEPulisci(ctx, cropW, cropH);

                const dataUrl = canvas.toDataURL('image/png');
                document.getElementById('cropped-preview').src = dataUrl;
                document.getElementById('result-box').style.display = 'block';

                if (window.Html5Qrcode) {
                    const html5QrCode = new Html5Qrcode("crop-canvas");
                    html5QrCode.scanFileV2(dataURLtoFile(dataUrl, "label.png"), false)
                        .then(decodedResult => {
                            document.getElementById('code-output').innerText = decodedResult.decodedText;
                        })
                        .catch(() => {
                            document.getElementById('code-output').innerText = "Etichetta/Fustella Acquisita";
                        });
                }
            }

            function dataURLtoFile(dataurl, filename) {
                let arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
                    bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
                while(n--){ u8arr[n] = bstr.charCodeAt(n); }
                return new File([u8arr], filename, {type:mime});
            }

            function copiaEIncolla() {
                const text = document.getElementById('code-output').innerText;
                const dummy = document.createElement("textarea");
                document.body.appendChild(dummy);
                dummy.value = text;
                dummy.select();
                document.execCommand("copy");
                document.body.removeChild(dummy);
            }

            function riavviaCamera() {
                document.getElementById('result-box').style.display = 'none';
                avviaFotocamera();
            }

            window.onload = avviaFotocamera;
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=560)

def mostra_avviso_nessun_animale():
    """Mostra un avviso amichevole quando l'utente non ha ancora registrato animali."""
    st.markdown("""
        <div class="wellness-card" style="text-align: center; padding: 35px; border-left: 6px solid #1E3A2B !important;">
            <h2 style="color: #1E3A2B; margin-bottom: 10px;">🐾 Nessun Animale Registrato</h2>
            <p style="color: #475569; font-size: 1.05rem;">
                Non hai ancora inserito un animale domestico nel tuo account.<br>
                Registra ora il tuo primo pet per accedere a tutte le funzionalità del libretto sanitario digitale!
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("➕ Registra Subito il Tuo Primo Animale", type="primary"):
        cambia_sezione("nuovo_animale")

def genera_link_whatsapp(numero, animale, farmaco, dosaggio, orario, note=""):
    testo = f"🐾 *PetHealth - Promemoria Terapia*\n\n🐶 *Animale:* {animale}\n💊 *Farmaco:* {farmaco}\n🥄 *Dose:* {dosaggio}\n⏰ *Orario:* {orario}\n"
    if note: testo += f"📝 *Istruzioni:* {note}\n"
    testo += "\n⚠️ *Ricordati di somministrare la terapia fino alla fine prevista!*"
    numero_pulito = "".join(filter(str.isdigit, str(numero)))
    return f"https://api.whatsapp.com/send?phone={numero_pulito}&text={urllib.parse.quote(testo)}" if numero_pulito else f"https://api.whatsapp.com/send?text={urllib.parse.quote(testo)}"

def genera_link_whatsapp_visita(numero, animale, tipo_visita, data_visita, veterinario="", note=""):
    testo = f"🐾 *PetHealth - Promemoria Visita*\n\n🐶 *Animale:* {animale}\n🏥 *Prestazione:* {tipo_visita}\n📅 *Data:* {data_visita}\n"
    if veterinario: testo += f"🩺 *Veterinario:* {veterinario}\n"
    if note: testo += f"📝 *Note:* {note}\n"
    testo += "\n⚠️ *Ricordati di confermare o presentarti all'appuntamento!*"
    numero_pulito = "".join(filter(str.isdigit, str(numero)))
    return f"https://api.whatsapp.com/send?phone={numero_pulito}&text={urllib.parse.quote(testo)}" if numero_pulito else f"https://api.whatsapp.com/send?text={urllib.parse.quote(testo)}"

def mostra_pulsanti_promemoria_terapia(animale, farmaco, dosaggio, orario, note=""):
    user_data = st.session_state.db_users.get(st.session_state.logged_user_email, {})
    num1 = user_data.get("numero_whatsapp", "")
    num2 = user_data.get("numero_whatsapp_2", "")
    if num1 and num2:
        c1, c2 = st.columns(2)
        with c1: st.link_button("📲 WhatsApp (Num 1)", url=genera_link_whatsapp(num1, animale, farmaco, dosaggio, orario, note))
        with c2: st.link_button("📲 WhatsApp (Num 2)", url=genera_link_whatsapp(num2, animale, farmaco, dosaggio, orario, note))
    else:
        st.link_button("📲 Invia Promemoria WhatsApp", url=genera_link_whatsapp(num1 or num2, animale, farmaco, dosaggio, orario, note))

def mostra_pulsanti_promemoria_visita(animale, tipo_visita, data_visita, veterinario="", note=""):
    user_data = st.session_state.db_users.get(st.session_state.logged_user_email, {})
    num1 = user_data.get("numero_whatsapp", "")
    num2 = user_data.get("numero_whatsapp_2", "")
    if num1 and num2:
        c1, c2 = st.columns(2)
        with c1: st.link_button("📲 Promemoria Visita (Num 1)", url=genera_link_whatsapp_visita(num1, animale, tipo_visita, data_visita, veterinario, note))
        with c2: st.link_button("📲 Promemoria Visita (Num 2)", url=genera_link_whatsapp_visita(num2, animale, tipo_visita, data_visita, veterinario, note))
    else:
        st.link_button("📲 Promemoria Visita WhatsApp", url=genera_link_whatsapp_visita(num1 or num2, animale, tipo_visita, data_visita, veterinario, note))

def verifica_o_registra_pin_vet(num_ordine, provincia, nome_vet, pin_inserito, email="", telefono="", struttura="", indirizzo=""):
    db_vet = st.session_state.get("db_veterinari", {})
    chiave_vet = f"{str(num_ordine).strip().upper()}-{str(provincia).strip().upper()}"
    vet_id = genera_id_veterinario_permanente(num_ordine, provincia)
    
    if chiave_vet in db_vet:
        if str(pin_inserito).strip() == str(db_vet[chiave_vet].get("pin")).strip():
            return True, "Autenticazione riuscita", vet_id
        else:
            return False, f"PIN errato per l'iscrizione FNOVI N° {num_ordine} ({provincia.upper()}).", None
    else:
        if len(str(pin_inserito).strip()) < 4:
            return False, "Il PIN segreto deve contenere almeno 4 cifre o caratteri.", None
        db_vet[chiave_vet] = {
            "nome": nome_vet.strip(), "num_ordine": str(num_ordine).strip(), "provincia": str(provincia).strip().upper(),
            "struttura": struttura.strip(), "email": email.strip(), "telefono": telefono.strip(),
            "indirizzo": indirizzo.strip(), "vet_id": vet_id, "pin": str(pin_inserito).strip(), "data_registrazione": str(date.today())
        }
        st.session_state.db_veterinari = db_vet
        salva_dati()
        return True, f"Profilo Medico registrato con ID: {vet_id}", vet_id

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    :root { color-scheme: light !important; }
    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F8F7F2 !important; color: #1e293b !important;
    }
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background-color: transparent !important; }
    section[data-testid="stSidebar"] {
        background-color: #1E3A2B !important; border-right: 1px solid #2D4A3E !important;
    }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    .wellness-card {
        background-color: #FFFFFF !important; border-radius: 16px; padding: 20px;
        border: 1px solid #E2E8E4 !important; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02); margin-bottom: 16px;
    }
    .auth-container {
        max-width: 540px; margin: 30px auto; background-color: #FFFFFF; padding: 32px;
        border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    }
    .card-badge {
        display: inline-block; padding: 4px 12px; background-color: #E8F0EC; color: #1E3A2B;
        font-weight: 700; font-size: 0.78rem; border-radius: 20px; margin-bottom: 10px;
        text-transform: uppercase; letter-spacing: 0.04em;
    }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-green { background-color: #dcfce7; color: #15803d; }
    
    div[data-testid="stFormSubmitButton"] > button, .stButton > button {
        background-color: #1E3A2B !important; border: 1px solid #1E3A2B !important;
        border-radius: 12px !important; padding: 0.75rem 1.5rem !important; width: 100% !important;
        box-shadow: 0 4px 12px rgba(30, 58, 43, 0.15) !important; transition: all 0.2s ease !important;
    }
    div[data-testid="stFormSubmitButton"] > button p, div[data-testid="stFormSubmitButton"] > button span,
    .stButton > button p, .stButton > button span {
        color: #FFFFFF !important; font-weight: 700 !important; font-size: 1rem !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #2D4A3E !important; border: 1px solid #3E6352 !important;
    }
    </style>
""", unsafe_allow_html=True)

if st.session_state.get("trigger_close_sidebar", False):
    st.session_state.trigger_close_sidebar = False
    components.html("""
        <script>
            setTimeout(function() {
                var sidebar = window.parent.document.querySelector('section[data-testid="stSidebar"]');
                if (sidebar && sidebar.getAttribute('aria-expanded') === 'true') {
                    var collapseBtn = window.parent.document.querySelector('button[data-testid="stSidebarCollapseButton"]') || 
                                      window.parent.document.querySelector('button[aria-label="Close sidebar"]') ||
                                      window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');
                    if (collapseBtn) {
                        collapseBtn.click();
                    }
                }
            }, 120);
        </script>
    """, height=0, width=0)

if st.session_state.logged_user_email is None:
    st.markdown("<h1 style='text-align: center; color: #1E3A2B; margin-top: 15px;'>🐾 PetHealth Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #475569; font-size:1.1rem; margin-bottom: 25px;'>La piattaforma digitale per la gestione della salute, libretto sanitario ed anagrafica dei tuoi animali domestici.</p>", unsafe_allow_html=True)

    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Accedi", "📝 Registrati", "📧 Attivazione Account"])

    # SCHEDA ACCESSO
    with auth_tab1:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #1E3A2B; text-align: center; margin-bottom: 10px;'>Accedi al tuo Account</h3>", unsafe_allow_html=True)
        st.caption("Inserisci le tue credenziali di accesso per entrare nell'applicazione.")
        st.write("")
        
        with st.form("form_login"):
            login_email = st.text_input("Indirizzo Email*", placeholder="es. mario.rossi@email.it")
            login_pass = st.text_input("Password*", type="password", placeholder="••••••••")
            btn_login = st.form_submit_button("🔑 Accedi alla Web App")
            
            if btn_login:
                email_clean = login_email.strip().lower()
                users_db = st.session_state.db_users
                
                if email_clean in users_db:
                    user_info = users_db[email_clean]
                    if user_info.get("stato") == "in_attesa":
                        st.warning("⚠️ Il tuo profilo richiede prima l'attivazione. Utilizza la scheda 'Attivazione Account' per accedere.")
                        st.session_state.verification_pending_email = email_clean
                    elif user_info.get("password") == hash_password(login_pass):
                        st.session_state.logged_user_email = email_clean
                        st.success(f"Benvenuto/a {user_info.get('nome')}!")
                        st.rerun()
                    else:
                        st.error("❌ Password non corretta. Riprova.")
                else:
                    st.error("❌ Nessun profilo registrato con questa email. Effettua prima la registrazione nel tab 'Registrati'.")
        st.markdown("</div>", unsafe_allow_html=True)

    # SCHEDA REGISTRAZIONE
    with auth_tab2:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #1E3A2B; text-align: center; margin-bottom: 10px;'>Modulo di Registrazione Utente</h3>", unsafe_allow_html=True)
        st.caption("Compila tutti i campi richiesti per creare il tuo profilo di gestione animali.")
        st.write("")
        
        with st.form("form_registrazione"):
            reg_nome = st.text_input("Nome e Cognome Proprietario*", placeholder="es. Mario Rossi")
            reg_email = st.text_input("Indirizzo Email*", placeholder="es. mario.rossi@email.it")
            reg_telefono = st.text_input("Numero di Cellulare / WhatsApp*", placeholder="es. +39 333 1234567")
            
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                reg_pass = st.text_input("Crea Password*", type="password", placeholder="••••••••")
            with col_p2:
                reg_pass_conf = st.text_input("Conferma Password*", type="password", placeholder="••••••••")
            
            st.write("")
            btn_register = st.form_submit_button("📝 Registra il tuo Account")
            
            if btn_register:
                email_c = reg_email.strip().lower()
                if not reg_nome.strip() or not email_c or not reg_pass or not reg_telefono.strip():
                    st.error("⚠ Compila tutti i campi obbligatori marcati con (*).")
                elif reg_pass != reg_pass_conf:
                    st.error("❌ Le password inserite non corrispondono.")
                elif len(reg_pass) < 6:
                    st.error("⚠️️ La password deve essere di almeno 6 caratteri.")
                elif email_c in st.session_state.db_users:
                    st.error("❌ Risulta già presente un profilo con questa email.")
                else:
                    code_token = str(uuid.uuid4())[:8].upper()
                    st.session_state.db_users[email_c] = {
                        "nome": reg_nome.strip(),
                        "email": email_c,
                        "password": hash_password(reg_pass),
                        "numero_whatsapp": reg_telefono.strip(),
                        "numero_whatsapp_2": "",
                        "stato": "in_attesa",
                        "codice_conferma": code_token,
                        "data_registrazione": str(date.today()),
                        "lista_animali": [],
                        "pet_selezionato": None,
                        "db_visite": {},
                        "db_terapie": {},
                        "db_fatture": {},
                        "db_anagrafica": {},
                        "angeli_archiviati": {}
                    }
                    salva_dati()
                    st.session_state.verification_pending_email = email_c
                    st.success("✅ Registrazione effettuata con successo! È stato generato il tuo codice di attivazione.")
                    st.info("👉 Passa alla scheda 'Attivazione Account' per attivare ed effettuare il tuo primo accesso.")
        st.markdown("</div>", unsafe_allow_html=True)

    with auth_tab3:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #1E3A2B; text-align: center; margin-bottom: 10px;'>Attivazione & Conferma Registrazione</h3>", unsafe_allow_html=True)
        
        target_email = st.session_state.verification_pending_email or ""
        email_to_verify = st.text_input("Inserisci l'email con cui ti sei registrato:", value=target_email)
        
        if email_to_verify.strip().lower() in st.session_state.db_users:
            u_data = st.session_state.db_users[email_to_verify.strip().lower()]
            if u_data.get("stato") == "attivo":
                st.success("🎉 Questo account risulta già attivo! Puoi accedere subito nella scheda 'Accedi'.")
            else:
                st.markdown(f"""
                    <div style="background:#F0FDF4; border:1.5px dashed #16A34A; padding:20px; border-radius:12px; margin-top:15px; margin-bottom:15px;">
                        <h4 style="margin:0 0 10px 0; color:#15803D;">✉ Messaggio di Benvenuto PetHealth</h4>
                        <p style="margin:0 0 8px 0; color:#1E293B;"><strong>Utente:</strong> {u_data['nome']}</p>
                        <p style="margin:0 0 8px 0; color:#1E293B;"><strong>Email:</strong> {u_data['email']}</p>
                        <p style="margin:0 0 12px 0; color:#1E293B;"><strong>Codice di Attivazione:</strong> <code>{u_data.get('codice_conferma')}</code></p>
                        <hr style="border:0; border-top:1px solid #CBD5E1; margin:10px 0;">
                        <p style="color:#334155; font-size:0.92rem;">Clicca sul pulsante sottostante per confermare e accedere direttamente alla Web App.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔗 CONFERMA ATTIVAZIONE ED ENTRA SUBITO"):
                    u_data["stato"] = "attivo"
                    st.session_state.db_users[email_to_verify.strip().lower()] = u_data
                    salva_dati()
                    st.session_state.logged_user_email = email_to_verify.strip().lower()
                    st.success("🎉 Registrazione attivata con successo!")
                    st.rerun()
        else:
            if email_to_verify:
                st.error("Nessun account in attesa di attivazione trovato per questa email.")
            else:
                st.info("Registrati nella scheda 'Registrati' prima di procedere all'attivazione.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

user_email = st.session_state.logged_user_email
user_db = st.session_state.db_users[user_email]

if "lista_animali" not in user_db: user_db["lista_animali"] = []
if "db_visite" not in user_db: user_db["db_visite"] = {}
if "db_terapie" not in user_db: user_db["db_terapie"] = {}
if "db_fatture" not in user_db: user_db["db_fatture"] = {}
if "db_anagrafica" not in user_db: user_db["db_anagrafica"] = {}
if "angeli_archiviati" not in user_db: user_db["angeli_archiviati"] = {}

lista_animali = user_db["lista_animali"]
pet_selezionato = user_db.get("pet_selezionato")

with st.sidebar:
    st.caption("UTENTE REGISTRATO")
    st.markdown(f"### 👤 {user_db.get('nome', 'Utente')}")
    st.caption(f"📧 {user_email}")
    
    if st.button("🚪 Logout / Esci"):
        st.session_state.logged_user_email = None
        st.rerun()
        
    st.markdown("---")
    
    with st.expander("⚙️ Impostazioni Notifiche WhatsApp", expanded=False):
        num_wa_1 = st.text_input("Primo numero di telefono", value=user_db.get("numero_whatsapp", ""))
        num_wa_2 = st.text_input("Secondo numero di telefono (opzionale)", value=user_db.get("numero_whatsapp_2", ""))
        if st.button("Salva Numeri WhatsApp"):
            user_db["numero_whatsapp"] = num_wa_1
            user_db["numero_whatsapp_2"] = num_wa_2
            salva_dati()
            st.success("Numeri WhatsApp aggiornati!")
            
    st.write("")
    st.markdown("**LIBRETTO ATTIVO**")
    
    if len(lista_animali) > 0:
        index_selezionato = 0
        if pet_selezionato in lista_animali:
            index_selezionato = lista_animali.index(pet_selezionato)
        
        pet_selected = st.selectbox("", lista_animali, index=index_selezionato, key="pet_select")
        if pet_selected != pet_selezionato:
            user_db["pet_selezionato"] = pet_selected
            salva_dati()
    else:
        st.info("Nessun animale registrato nel tuo account.")
        pet_selected = None
    
    st.write("")
    st.markdown("**SEZIONI**")
    
    if st.button("🏠 Riepilogo (Dashboard)"): cambia_sezione("dashboard")
    if st.button("📋 Anagrafica Pet & Proprietario"): cambia_sezione("anagrafica")
    if st.button("🏥 Visite e Clinica"): cambia_sezione("visite")
    if st.button("💊 Terapie e Farmaci"): cambia_sezione("terapie")
    if st.button("📄 Fatture e Spese"): cambia_sezione("fatture")
    if st.button("✈️ Passaporto & Viaggi"): cambia_sezione("passaporto")
    if st.button("🚨 Urgenze & Cliniche 24H"): cambia_sezione("urgenze")
    if st.button("🌈 I nostri angeli a 4 zampe"): cambia_sezione("angeli")
    
    st.write("")
    if st.button("➕ Registra Nuovo Animale"): cambia_sezione("nuovo_animale")

if st.session_state.sezione_attiva == "dashboard":
    if pet_selected:
        col1, col2 = st.columns(2)
        terapie_pet = user_db["db_terapie"].get(pet_selected, [])
        visite_pet = user_db["db_visite"].get(pet_selected, [])

        with col1:
            st.markdown(f"""
                <div class="wellness-card">
                    <span class="card-badge badge-purple">TERAPIE ATTIVE & PROMEMORIA</span>
                    <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">💊 In Somministrazione</h3>
                </div>
            """, unsafe_allow_html=True)
            
            if terapie_pet:
                terapie_ordinate = sorted(enumerate(terapie_pet), key=lambda x: x[1].get('data_inizio', ''), reverse=True)
                for idx, t in terapie_ordinate:
                    orario_txt = t.get('orario', 'Non specificato')
                    with st.expander(f"💊 {t['farmaco']} ({t['periodo']}) - ⏰ {orario_txt}"):
                        st.write(f"**Dose / Quantità:** {t['dosaggio']}")
                        st.write(f"**Orario di Somministrazione:** {orario_txt}")
                        st.write(f"**Periodo:** {t['periodo']}")
                        if t.get('note'): st.write(f"**Note:** {t['note']}")
                        mostra_pulsanti_promemoria_terapia(pet_selected, t['farmaco'], t['dosaggio'], orario_txt, t.get('note', ''))
                        if st.button("🗑️ Elimina Terapia", key=f"del_ter_dash_{idx}"):
                            user_db["db_terapie"][pet_selected].pop(idx)
                            salva_dati(); st.rerun()
            else:
                st.info(f"Nessuna terapia attiva registrata per {pet_selected}.")

        with col2:
            st.markdown(f"""
                <div class="wellness-card">
                    <span class="card-badge badge-blue">STORICO RECENTE</span>
                    <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">🪵 Ultime Visite</h3>
                </div>
            """, unsafe_allow_html=True)
            
            if visite_pet:
                visite_ordinate = sorted(enumerate(visite_pet), key=lambda x: x[1].get('data', ''), reverse=True)
                for idx, v in visite_ordinate:
                    with st.expander(f"🏥 {v['tipo']} - {v['data']}"):
                        if v.get('veterinario'): st.write(f"**Veterinario:** {v['veterinario']}")
                        if v.get('vet_id_permanente'): st.caption(f"🆔 ID Medico Permanente: `{v['vet_id_permanente']}`")
                        if v.get('nome_vaccino'): st.write(f"💉 **Vaccino:** {v.get('nome_vaccino')} | **Lotto:** {v.get('lotto_vaccino', 'N/D')}")
                        if v.get('diagnosi'): st.write(f"**Diagnosi:** {v['diagnosi']}")
                        mostra_pulsanti_promemoria_visita(pet_selected, v.get('prossimo_controllo_tipo', v['tipo']), v.get('prossimo_controllo_data', v['data']), v.get('veterinario', ''), v.get('diagnosi', ''))
                        if st.button("🗑️ Elimina Visita", key=f"del_vis_dash_{idx}"):
                            user_db["db_visite"][pet_selected].pop(idx)
                            salva_dati(); st.rerun()
            else:
                st.info(f"Nessuna visita medica registrata per {pet_selected}.")

        st.write("")
        with st.expander("🩺 Registrazione & Impostazione PIN Medico Veterinario", expanded=False):
            st.markdown("#### ➕ Registrazione Scheda Medico Veterinario")
            with st.form("form_reg_vet_dash"):
                c_rv1, c_rv2 = st.columns(2)
                with c_rv1:
                    r_nome_vet = st.text_input("Nome e Cognome Medico / Titolare*")
                    r_struttura = st.text_input("Nome Clinica / Studio")
                    r_num_ord = st.text_input("N° Iscrizione Ordine FNOVI*")
                    r_prov_ord = st.text_input("Provincia Ordine*")
                with c_rv2:
                    r_email = st.text_input("Email / PEC")
                    r_telefono = st.text_input("Telefono Studio")
                    r_indirizzo = st.text_input("Indirizzo Clinica")
                    r_pin_vet = st.text_input("Imposta PIN Segreto Medico*", type="password")
                
                sub_vet = st.form_submit_button("💾 Registra Veterinario")
                if sub_vet:
                    if r_nome_vet.strip() and r_num_ord.strip() and r_prov_ord.strip() and r_pin_vet.strip():
                        esito, msg, v_id = verifica_o_registra_pin_vet(r_num_ord, r_prov_ord, r_nome_vet, r_pin_vet, r_email, r_telefono, r_struttura, r_indirizzo)
                        if esito: st.success(f"✅ {msg}")
                        else: st.error(f"❌ {msg}")
                    else: st.error("Compila tutti i campi obbligatori (*).")

        with st.expander(f"⚠ Area Riservata Medico Veterinario (Registro Decesso - {pet_selected})"):
            date_decesso = st.date_input("Data del decesso")
            certificato = st.file_uploader("Allega Certificato di Morte", type=["pdf", "png", "jpg"], key="cert_morte")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1: v_num_ord_d = st.text_input("N° Ordine FNOVI*", key="v_num_ord_d")
            with col_d2: v_prov_d = st.text_input("Provincia Ordine*", key="v_prov_d")
            with col_d3: pin_vet_d = st.text_input("PIN Segreto Veterinario*", type="password", key="pin_morte")
            
            if st.button("Conferma e Archivia Registro Decesso"):
                if v_num_ord_d.strip() and v_prov_d.strip() and pin_vet_d:
                    esito, msg, vet_id = verifica_o_registra_pin_vet(v_num_ord_d, v_prov_d, "Veterinario Responsabile", pin_vet_d)
                    if esito:
                        user_db["angeli_archiviati"][pet_selected] = {
                            "data_decesso": str(date_decesso),
                            "certificato": certificato.name if certificato else "Non allegato",
                            "veterinario_id": vet_id,
                            "visite": user_db["db_visite"].pop(pet_selected, []),
                            "terapie": user_db["db_terapie"].pop(pet_selected, []),
                            "fatture": user_db["db_fatture"].pop(pet_selected, []),
                            "anagrafica": user_db["db_anagrafica"].pop(pet_selected, {})
                        }
                        user_db["lista_animali"].remove(pet_selected)
                        user_db["pet_selezionato"] = user_db["lista_animali"][0] if user_db["lista_animali"] else None
                        salva_dati(); st.success(f"{pet_selected} è stato spostato nel Registro degli Angeli."); st.rerun()
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "anagrafica":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>📋 Scheda Anagrafica - {pet_selected}</h2>", unsafe_allow_html=True)
        anagrafica_corrente = user_db["db_anagrafica"].get(pet_selected, {
            "tipo_animale": "Cane", "nome": pet_selected, "razza": "", "data_nascita": str(date.today()),
            "microchip": "", "microchip_foto": "", "segni_particolari": "", "proprietario_nome": user_db.get("nome", ""),
            "proprietario_indirizzo": "", "proprietario_telefono": user_db.get("numero_whatsapp", ""), "proprietario_citta": ""
        })

        col_view1, col_view2 = st.columns(2)
        with col_view1:
            st.markdown(f"""
                <div class="wellness-card" style="border-left: 5px solid #1E3A2B !important;">
                    <span class="card-badge badge-purple">🐾 DATI ANAGRAFICI PET</span>
                    <h3 style="color: #1E3A2B; margin-top: 5px; margin-bottom: 12px;">{anagrafica_corrente.get('nome', pet_selected)}</h3>
                    <p>• <strong>Specie:</strong> {anagrafica_corrente.get('tipo_animale', 'N/D')}</p>
                    <p>• <strong>Razza:</strong> {anagrafica_corrente.get('razza') or 'Non specificata'}</p>
                    <p>• <strong>Data Nascita:</strong> {anagrafica_corrente.get('data_nascita', 'N/D')}</p>
                    <p>• <strong>Microchip:</strong> <code>{anagrafica_corrente.get('microchip') or 'Non inserito'}</code></p>
                    <p>• <strong>Segni Particolari:</strong> {anagrafica_corrente.get('segni_particolari') or 'Nessuno'}</p>
                </div>
            """, unsafe_allow_html=True)
            if anagrafica_corrente.get('microchip_foto'):
                st.caption("📷 Etichetta Microchip Scansionata:")
                st.image(anagrafica_corrente.get('microchip_foto'), use_container_width=True)

        with col_view2:
            st.markdown(f"""
                <div class="wellness-card" style="border-left: 5px solid #3B82F6 !important;">
                    <span class="card-badge badge-blue">👤 PROPRIETARIO</span>
                    <h3 style="color: #1E3A2B; margin-top: 5px; margin-bottom: 12px;">{anagrafica_corrente.get('proprietario_nome') or user_db.get('nome')}</h3>
                    <p>• <strong>Indirizzo:</strong> {anagrafica_corrente.get('proprietario_indirizzo') or 'Non specificato'}</p>
                    <p>• <strong>Telefono:</strong> {anagrafica_corrente.get('proprietario_telefono') or 'Non specificato'}</p>
                    <p>• <strong>Città:</strong> {anagrafica_corrente.get('proprietario_citta') or 'Non specificata'}</p>
                </div>
            """, unsafe_allow_html=True)

        with st.expander("✏ Modifica Anagrafica Pet e Proprietario", expanded=True):
            with st.form("form_edit_anagrafica"):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    e_tipo = st.selectbox("Tipo / Specie Animale*", ["Cane", "Gatto", "Coniglio", "Uccello", "Rettile", "Altro"])
                    e_nome = st.text_input("Nome Animale*", value=anagrafica_corrente.get('nome', pet_selected))
                    e_razza = st.text_input("Razza", value=anagrafica_corrente.get('razza', ''))
                with col_a2:
                    e_data_nascita = st.date_input("Data di Nascita")
                    e_microchip = st.text_input("Numero Microchip", value=anagrafica_corrente.get('microchip', ''))
                    e_segni = st.text_area("Segni Particolari", value=anagrafica_corrente.get('segni_particolari', ''))

                st.markdown("---")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    e_prop_nome = st.text_input("Nome e Cognome Proprietario*", value=anagrafica_corrente.get('proprietario_nome', user_db.get('nome', '')))
                    e_prop_indirizzo = st.text_input("Indirizzo", value=anagrafica_corrente.get('proprietario_indirizzo', ''))
                with col_p2:
                    e_prop_telefono = st.text_input("Telefono", value=anagrafica_corrente.get('proprietario_telefono', user_db.get('numero_whatsapp', '')))
                    e_prop_citta = st.text_input("Città", value=anagrafica_corrente.get('proprietario_citta', ''))

                if st.form_submit_button("💾 Salva Modifiche Anagrafica"):
                    if e_nome.strip():
                        old_n = pet_selected; new_n = e_nome.strip()
                        nuovi_dati = {
                            "tipo_animale": e_tipo, "nome": new_n, "razza": e_razza, "data_nascita": str(e_data_nascita),
                            "microchip": e_microchip, "microchip_foto": anagrafica_corrente.get('microchip_foto', ''),
                            "segni_particolari": e_segni, "proprietario_nome": e_prop_nome,
                            "proprietario_indirizzo": e_prop_indirizzo, "proprietario_telefono": e_prop_telefono, "proprietario_citta": e_prop_citta
                        }
                        if old_n != new_n:
                            user_db["lista_animali"] = [new_n if p == old_n else p for p in user_db["lista_animali"]]
                            user_db["db_visite"][new_n] = user_db["db_visite"].pop(old_n, [])
                            user_db["db_terapie"][new_n] = user_db["db_terapie"].pop(old_n, [])
                            user_db["db_fatture"][new_n] = user_db["db_fatture"].pop(old_n, [])
                            user_db["db_anagrafica"].pop(old_n, None)
                            user_db["pet_selezionato"] = new_n
                        user_db["db_anagrafica"][new_n] = nuovi_dati
                        salva_dati(); st.success(f"Anagrafica di {new_n} aggiornata!"); st.rerun()

elif st.session_state.sezione_attiva == "visite":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>🏥 Visite e Clinica - {pet_selected}</h2>", unsafe_allow_html=True)
        with st.expander("🔍 Scansiona ed Isola Etichetta Vaccino / Microchip"):
            mostra_scansionatore_barre("📷 Fotocamera & Isolamento Etichetta Vaccino")

        with st.expander("➕ Aggiungi Nuova Visita Medica", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                data_visita = st.date_input("Data Visita")
                tipo_visita = st.selectbox("Tipo Visita", ["Controllo Generale", "Vaccinazione", "Visita Specialistica", "Urgenza", "Controllo Post-Operatorio"])
                veterinario = st.text_input("Medico Veterinario / Clinica")
            with col2:
                diagnosi = st.text_area("Diagnosi / Note Cliniche")
                referto = st.file_uploader("Allega Referto o Scansione Etichetta (Opzionale)", type=["pdf", "png", "jpg"], key="v_ref")

            nome_vaccino, lotto_vaccino, scadenza_vaccino = "", "", None
            if tipo_visita == "Vaccinazione":
                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1: nome_vaccino = st.text_input("Nome Vaccino*")
                with col_v2: lotto_vaccino = st.text_input("N° Lotto Vaccino*")
                with col_v3: scadenza_vaccino = st.date_input("Scadenza Vaccino")

            chi_inserisce = st.radio("Chi inserisce la prestazione?", ["Utente (In attesa di firma)", "Veterinario (Certificazione Ufficiale Immediata)"], horizontal=True)
            certificato_valido, vet_id_perm, codice_cert, num_ordine_vet, provincia_vet = False, None, None, "", ""

            if "Veterinario" in chi_inserisce:
                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1: num_ordine_vet = st.text_input("N° Ordine FNOVI*")
                with col_v2: provincia_vet = st.text_input("Provincia Ordine*")
                with col_v3: pin_convalida = st.text_input("PIN Segreto Medico*", type="password")
                if num_ordine_vet and provincia_vet and pin_convalida:
                    esito, msg, vet_id_perm = verifica_o_registra_pin_vet(num_ordine_vet, provincia_vet, veterinario, pin_convalida)
                    if esito:
                        certificato_valido = True
                        codice_cert = genera_codice_certificazione(pet_selected, vet_id_perm, str(data_visita), tipo_visita)
                        st.success(f"✅ Medico Verificato! Codice Certificato: `{codice_cert}`")

            if st.button("Salva Visita Medica"):
                nuova_visita = {
                    "data": str(data_visita), "tipo": tipo_visita, "veterinario": veterinario, "diagnosi": diagnosi,
                    "referto": referto.name if referto else None, "certificata": certificato_valido,
                    "num_ordine_vet": num_ordine_vet, "provincia_vet": provincia_vet, "vet_id_permanente": vet_id_perm,
                    "codice_certificato": codice_cert, "nome_vaccino": nome_vaccino, "lotto_vaccino": lotto_vaccino,
                    "scadenza_vaccino": str(scadenza_vaccino) if scadenza_vaccino else ""
                }
                if pet_selected not in user_db["db_visite"]: user_db["db_visite"][pet_selected] = []
                user_db["db_visite"][pet_selected].append(nuova_visita)
                salva_dati(); st.success("Visita registrata con successo!"); st.rerun()

        st.markdown("### 📋 Visite e Certificati Registrati")
        visite_list = user_db["db_visite"].get(pet_selected, [])
        visite_ordinate = sorted(enumerate(visite_list), key=lambda x: x[1].get('data', ''), reverse=True)
        for idx, v in visite_ordinate:
            is_cert = v.get("certificata", False)
            with st.expander(f"🏥 {v['data']} - {v['tipo']} | {'✅ CERTIFICATA' if is_cert else '⏳ IN ATTESA DI FIRMA'}"):
                st.write(f"**Veterinario:** Dr. {v.get('veterinario', 'N/D')}")
                if is_cert: st.success(f"🛡️ **Codice Certificato:** `{v.get('codice_certificato')}` | ID Medico: `{v.get('vet_id_permanente')}`")
                if v.get('nome_vaccino'):
                    st.write(f"💉 **Vaccino:** {v.get('nome_vaccino')} | **Lotto:** {v.get('lotto_vaccino', 'N/D')}")
                if v.get('diagnosi'): st.write(f"**Diagnosi:** {v['diagnosi']}")
                if v.get('referto'):
                    st.caption(f"📄 Allegato/Etichetta: {v['referto']}")
                mostra_pulsanti_promemoria_visita(pet_selected, v['tipo'], v['data'], v.get('veterinario', ''), v.get('diagnosi', ''))
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "terapie":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>💊 Terapie e Farmaci - {pet_selected}</h2>", unsafe_allow_html=True)
        with st.expander("🔍 Scansiona Barcode Farmaco"):
            mostra_scansionatore_barre("📷 Lettore Codici Farmaci")

        with st.expander("➕ Nuova Terapia o Prescrizione", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                nome_farmaco = st.text_input("Nome del Farmaco*")
                dosaggio = st.text_input("Dose / Quantità*")
                is_multigiorno = st.checkbox("📅 Terapia somministrata per più giorni?")
                data_inizio = st.date_input("Data Inizio Terapia", value=date.today())
                data_fine = st.date_input("Data Fine Terapia") if is_multigiorno else data_inizio
                orario_somm = st.time_input("Orario Somministrazione", value=datetime.strptime("09:00", "%H:%M").time())
            with col2:
                note_somm = st.text_area("Istruzioni e Note")
                ricetta = st.file_uploader("Allega Ricetta Medica", type=["pdf", "png", "jpg"], key="t_ric")

            if st.button("Salva Terapia"):
                if nome_farmaco.strip() and dosaggio.strip():
                    periodo_txt = f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}" if is_multigiorno else f"Dose Unica ({data_inizio.strftime('%d/%m/%Y')})"
                    nuova_terapia = {
                        "farmaco": nome_farmaco, "dosaggio": dosaggio, "orario": orario_somm.strftime("%H:%M"),
                        "periodo": periodo_txt, "data_inizio": str(data_inizio), "note": note_somm, "ricetta": ricetta.name if ricetta else None
                    }
                    if pet_selected not in user_db["db_terapie"]: user_db["db_terapie"][pet_selected] = []
                    user_db["db_terapie"][pet_selected].append(nuova_terapia)
                    salva_dati(); st.success("Terapia salvata con successo!"); st.rerun()

        st.markdown("### 📋 Terapie Programmate")
        terapie_list = user_db["db_terapie"].get(pet_selected, [])
        terapie_ordinate = sorted(enumerate(terapie_list), key=lambda x: x[1].get('data_inizio', ''), reverse=True)
        for idx, t in terapie_ordinate:
            with st.expander(f"💊 {t['farmaco']} - Dose: {t['dosaggio']} ({t['periodo']})"):
                st.write(f"**Orario:** {t.get('orario')}")
                if t.get('note'): st.write(f"**Istruzioni:** {t['note']}")
                mostra_pulsanti_promemoria_terapia(pet_selected, t['farmaco'], t['dosaggio'], t.get('orario', ''), t.get('note', ''))
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "fatture":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>📄 Fatture e Spese - {pet_selected}</h2>", unsafe_allow_html=True)
        with st.expander("➕ Carica Nuova Fattura", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                data_spesa = st.date_input("Data Documento")
                categoria_spesa = st.selectbox("Categoria", ["Visita Veterinaria", "Farmaci", "Esami", "Chirurgia", "Cibo / Integratori"])
                importo = st.number_input("Importo (€)", min_value=0.0, step=0.5, format="%.2f")
            with col2:
                fornitore = st.text_input("Clinica / Farmacia")
                file_fattura = st.file_uploader("Allega Ricevuta/Fattura", type=["pdf", "png", "jpg"], key="f_upl")

            if st.button("Salva Fattura"):
                nuova_fattura = {"data": str(data_spesa), "categoria": categoria_spesa, "importo": importo, "fornitore": fornitore, "documento": file_fattura.name if file_fattura else None}
                if pet_selected not in user_db["db_fatture"]: user_db["db_fatture"][pet_selected] = []
                user_db["db_fatture"][pet_selected].append(nuova_fattura)
                salva_dati(); st.success("Fattura salvata!"); st.rerun()

        st.markdown("### 📋 Fatture Registrate")
        for idx, f in enumerate(user_db["db_fatture"].get(pet_selected, [])):
            with st.expander(f"📄 €{f['importo']:.2f} - {f['categoria']} ({f['data']})"):
                st.write(f"**Fornitore:** {f['fornitore']}")
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "passaporto":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>✈️ Passaporto & Viaggi - {pet_selected}</h2>", unsafe_allow_html=True)
        visite_cert = [v for v in user_db["db_visite"].get(pet_selected, []) if v.get("certificata", False)]
        if visite_cert:
            for v in visite_cert:
                st.markdown(f"""
                    <div class="wellness-card" style="border-left: 5px solid #10B981 !important;">
                        <span class="card-badge badge-purple">CERTIFICATO UFFICIALE</span>
                        <h4>💉 {v['tipo']} — {v['data']}</h4>
                        <p><strong>Medico:</strong> Dr. {v['veterinario']}</p>
                        <p><strong>Codice Certificato:</strong> <code>{v.get('codice_certificato')}</code></p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Nessuna prestazione ufficialmente certificata dal veterinario per il passaporto.")
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "urgenze":
    st.markdown("<h2 style='color: #1E3A2B;'>🚨 Urgenze & Cliniche Veterinarie 24H</h2>", unsafe_allow_html=True)
    citta_ricerca = st.text_input("📍 Inserisci la Città o Località di Vacanza:", placeholder="es. Rimini, Olbia, Roma...")
    q = urllib.parse.quote_plus(f"pronto soccorso veterinario 24 ore a {citta_ricerca.strip()}" if citta_ricerca else "pronto soccorso veterinario 24 ore vicino a me")
    st.link_button(f"🗺️ Apri Mappa Cliniche 24H per '{citta_ricerca or 'posizione attuale'}' su Google Maps", f"https://www.google.com/maps/search/?api=1&query={q}")

elif st.session_state.sezione_attiva == "angeli":
    st.markdown("<h2 style='color: #1E3A2B;'>🌈 I Nostri Angeli a 4 Zampe</h2>", unsafe_allow_html=True)
    angeli_list = list(user_db["angeli_archiviati"].keys())
    if angeli_list:
        sel_ang = st.selectbox("Seleziona un angelo per consultare la cartella clinica:", angeli_list)
        if st.button("🔄 Ripristina Animale tra gli Attivi"):
            user_db["lista_animali"].append(sel_ang)
            dati_ang = user_db["angeli_archiviati"].pop(sel_ang)
            user_db["db_visite"][sel_ang] = dati_ang.get("visite", [])
            user_db["db_terapie"][sel_ang] = dati_ang.get("terapie", [])
            user_db["db_fatture"][sel_ang] = dati_ang.get("fatture", [])
            user_db["pet_selezionato"] = sel_ang
            salva_dati(); st.success(f"{sel_ang} è stato ripristinato!"); st.rerun()
    else:
        st.info("Nessun animale registrato nella sezione Angeli.")

elif st.session_state.sezione_attiva == "nuovo_animale":
    st.markdown("<h2 style='color: #1E3A2B;'>🐾 Registra Nuovo Animale</h2>", unsafe_allow_html=True)
    st.caption("Compila la scheda anagrafica sottostante per creare il nuovo libretto sanitario digitale.")
    
    with st.expander("📷 Scansiona Codice Microchip da Libretto Cartaceo", expanded=False):
        mostra_scansionatore_barre("📷 Scansiona Adesivo Microchip dell'Animale")

    with st.form("form_nuovo_animale"):
        st.markdown("### 🐾 1. Dati Anagrafici dell'Animale")
        c1, c2 = st.columns(2)
        with c1:
            n_nome = st.text_input("Nome dell'Animale*", placeholder="es. Luna, Max, Baffo...")
            n_specie = st.selectbox("Specie / Tipo Animale*", ["Cane", "Gatto", "Coniglio", "Uccello", "Rettile", "Altro"])
            n_razza = st.text_input("Razza dell'Animale", placeholder="es. Meticcio, Labradoodle, Europeo...")
        with c2:
            n_data = st.date_input("Data di Nascita Presunta / Effettiva")
            n_microchip = st.text_input("Numero Microchip (15 Cifre)", placeholder="es. 380260000000000")
            n_segni = st.text_input("Segni Particolari o Note", placeholder="es. Macchia sul petto, macchia nera zampa destra...")
        
        st.markdown("---")
        st.markdown("### 👤 2. Dati Anagrafici del Proprietario")
        cp1, cp2 = st.columns(2)
        with cp1:
            n_prop_nome = st.text_input("Nome e Cognome Proprietario*", value=user_db.get("nome", ""))
            n_prop_tel = st.text_input("Telefono / WhatsApp Proprietario*", value=user_db.get("numero_whatsapp", ""))
        with cp2:
            n_prop_indirizzo = st.text_input("Indirizzo di Residenza", placeholder="es. Via Roma 12")
            n_prop_citta = st.text_input("Città", placeholder="es. Milano, Roma...")

        st.write("")
        if st.form_submit_button("💾 Salva e Crea Libretto Sanitario"):
            if n_nome.strip():
                pet_name = n_nome.strip()
                if pet_name not in user_db["lista_animali"]:
                    user_db["lista_animali"].append(pet_name)
                    user_db["db_visite"][pet_name] = []
                    user_db["db_terapie"][pet_name] = []
                    user_db["db_fatture"][pet_name] = []
                user_db["db_anagrafica"][pet_name] = {
                    "tipo_animale": n_specie,
                    "nome": pet_name,
                    "razza": n_razza,
                    "data_nascita": str(n_data),
                    "microchip": n_microchip.strip(),
                    "segni_particolari": n_segni,
                    "proprietario_nome": n_prop_nome.strip(),
                    "proprietario_telefono": n_prop_tel.strip(),
                    "proprietario_indirizzo": n_prop_indirizzo.strip(),
                    "proprietario_citta": n_prop_citta.strip()
                }
                user_db["pet_selezionato"] = pet_name
                st.session_state.sezione_attiva = "anagrafica"
                salva_dati()
                st.success(f"🎉 Scheda e libretto sanitario di {pet_name} creati con successo!")
                st.rerun()
            else:
                st.error("⚠️️ Inserisci almeno il Nome dell'Animale.")

else:
    st.session_state.sezione_attiva = "dashboard"
    st.rerun()
