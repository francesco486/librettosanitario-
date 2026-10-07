import streamlit as st
import json
import os
import io
import base64
import urllib.parse
import hashlib
import uuid
import re
import math
import calendar
from datetime import datetime, date, timedelta
from html import escape as html_escape
import streamlit.components.v1 as components

import numpy as np
from PIL import Image, ImageFilter, ImageOps

# Lettura automatica dei codici a barre (OPZIONALE).
# Se la libreria "pyzbar" non è installata l'app funziona lo stesso:
# l'immagine viene salvata e il numero si scrive a mano.
try:
    from pyzbar.pyzbar import decode as _zbar_decode
except Exception:
    _zbar_decode = None

# Creazione del PDF del libretto (OPZIONALE: serve la libreria "reportlab" nel file requirements.txt).
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm, mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                    KeepTogether, Flowable, CondPageBreak)
    from reportlab.platypus import Image as RLImage
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# Tema chiaro per tutti i dispositivi: sui telefoni con modo scuro Streamlit passa al tema scuro
# (testi chiari) e alcuni elementi diventano illeggibili sulla grafica chiara dell'app.
try:
    for _chiave_tema, _valore_tema in {
        "theme.base": "light", "theme.primaryColor": "#0284C7", "theme.backgroundColor": "#F8F6F0",
        "theme.secondaryBackgroundColor": "#FFFFFF", "theme.textColor": "#1E293B",
    }.items():
        st._config.set_option(_chiave_tema, _valore_tema)
except Exception:
    pass

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

# ---------------------------------------------------------------------------
# SCANSIONE ETICHETTE (microchip e vaccini) CON RIMOZIONE AUTOMATICA DELLO SFONDO
# ---------------------------------------------------------------------------

def _soglia_otsu(a):
    """Trova automaticamente la soglia che separa 'carta chiara' da 'sfondo scuro'."""
    hist = np.bincount(a.ravel(), minlength=256).astype(np.float64)
    totale = a.size
    somma_tot = float(np.dot(np.arange(256), hist))
    peso_b, somma_b, migliore, soglia = 0.0, 0.0, 0.0, 127
    for t in range(256):
        peso_b += hist[t]
        if peso_b == 0:
            continue
        peso_f = totale - peso_b
        if peso_f == 0:
            break
        somma_b += t * hist[t]
        media_b = somma_b / peso_b
        media_f = (somma_tot - somma_b) / peso_f
        varianza = peso_b * peso_f * (media_b - media_f) ** 2
        if varianza > migliore:
            migliore, soglia = varianza, t
    return soglia

def _riquadro_etichetta(img):
    """Individua la zona chiara (l'etichetta). Restituisce (x0, y0, x1, y1) in pixel, oppure None."""
    grigio = ImageOps.grayscale(img)
    w, h = grigio.size
    piccola = grigio.resize((max(1, w // 4), max(1, h // 4))).filter(ImageFilter.GaussianBlur(2))
    a = np.asarray(piccola)
    ph, pw = a.shape
    chiaro = a > _soglia_otsu(a)

    righe = np.where(chiaro.mean(axis=1) > 0.30)[0]
    colonne = np.where(chiaro.mean(axis=0) > 0.30)[0]
    if len(righe) == 0 or len(colonne) == 0:
        return None

    y0, y1 = righe[0], righe[-1] + 1
    x0, x1 = colonne[0], colonne[-1] + 1
    # Se la zona trovata è troppo piccola non ci fidiamo
    if (y1 - y0) * (x1 - x0) < 0.15 * ph * pw:
        return None

    margine_y, margine_x = int(0.02 * ph), int(0.02 * pw)
    y0, y1 = max(0, y0 - margine_y), min(ph, y1 + margine_y)
    x0, x1 = max(0, x0 - margine_x), min(pw, x1 + margine_x)

    sx, sy = w / pw, h / ph
    return (int(x0 * sx), int(y0 * sy), min(w, int(x1 * sx)), min(h, int(y1 * sy)))

def _ritaglia_etichetta(img):
    """Ritaglio automatico sulla zona chiara trovata (se non la trova lascia l'immagine intera)."""
    box = _riquadro_etichetta(img)
    return img.crop(box) if box else img

def _appiattisci_sfondo(grigio):
    """Elimina ombre e sfondo: la carta diventa bianco puro, inchiostro e barre restano nitidi."""
    w, h = grigio.size
    f = 8
    piccola = grigio.resize((max(1, w // f), max(1, h // f)))
    k = int(max(3, min(15, min(piccola.size) // 2)))
    if k % 2 == 0:
        k += 1
    sfondo = piccola.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.GaussianBlur(6))
    sfondo = sfondo.resize((w, h), Image.BILINEAR)

    g = np.asarray(grigio, dtype=np.float32)
    s = np.maximum(np.asarray(sfondo, dtype=np.float32), 1.0)
    norm = np.clip(g / s, 0, 1)

    bianco = 0.90
    nero = min(float(np.percentile(norm, 1)), bianco - 0.15)
    x = np.clip((norm - nero) / (bianco - nero), 0, 1)
    x = x ** 1.4
    return Image.fromarray((x * 255).astype(np.uint8), "L")

def _leggi_codici(immagine):
    """Prova a leggere i codici a barre presenti nell'immagine (solo se pyzbar è disponibile)."""
    if _zbar_decode is None:
        return []
    try:
        trovati = _zbar_decode(immagine)
        return [t.data.decode("utf-8", "ignore") for t in trovati if t.data]
    except Exception:
        return []

@st.cache_data(show_spinner=False, max_entries=20)
def elabora_etichetta(raw_bytes, rimuovi_sfondo=True, ritaglio_auto=True):
    """Riceve la foto, rimuove lo sfondo e restituisce (immagine in base64, codici letti)."""
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1600, 1600))

    if rimuovi_sfondo:
        ritagliata = _ritaglia_etichetta(img) if ritaglio_auto else img
        risultato = _appiattisci_sfondo(ImageOps.grayscale(ritagliata))
        codici = _leggi_codici(risultato) or _leggi_codici(ritagliata)
    else:
        risultato = img
        codici = _leggi_codici(img)

    risultato.thumbnail((1000, 1000))
    buf = io.BytesIO()
    if rimuovi_sfondo:
        risultato.save(buf, format="PNG", optimize=True)
    else:
        risultato.save(buf, format="JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode("ascii"), codici

@st.cache_data(show_spinner=False, max_entries=10)
def prepara_anteprima_ritaglio(raw_bytes):
    """Crea l'anteprima leggera per lo strumento di ritaglio e il riquadro iniziale suggerito."""
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    box = _riquadro_etichetta(img)
    if box:
        iniziale = [box[0] / w, box[1] / h, box[2] / w, box[3] / h]
    else:
        iniziale = [0.04, 0.04, 0.96, 0.96]
    anteprima = img.copy()
    anteprima.thumbnail((900, 900))
    buf = io.BytesIO()
    anteprima.save(buf, format="JPEG", quality=80)
    data_url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    return data_url, iniziale

def ritaglia_bytes(raw_bytes, box):
    """Ritaglia la foto originale (alta qualità) secondo il riquadro scelto [x0, y0, x1, y1] in frazioni 0-1."""
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    x0 = int(max(0.0, min(1.0, float(box[0]))) * w)
    y0 = int(max(0.0, min(1.0, float(box[1]))) * h)
    x1 = int(max(0.0, min(1.0, float(box[2]))) * w)
    y1 = int(max(0.0, min(1.0, float(box[3]))) * h)
    if x1 - x0 < 10 or y1 - y0 < 10:
        return raw_bytes
    buf = io.BytesIO()
    img.crop((x0, y0, x1, y1)).save(buf, format="JPEG", quality=92)
    return buf.getvalue()

# ---------------------------------------------------------------------------
# FOTOCAMERA GUIDATA: riquadro verde + ritaglio automatico.
# Viene salvato SOLO ciò che sta dentro il riquadro (o, se il telefono lo supporta,
# il solo codice a barre rilevato in automatico e riquadrato in giallo).
# Il componente viene creato da solo in una cartella "componente_scanner".
# ---------------------------------------------------------------------------
SCANNER_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html, body { margin: 0; padding: 0; background: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  #wrap { width: 100%; max-width: 640px; margin: 0 auto; padding: 2px; box-sizing: border-box; }
  #stage { position: relative; width: 100%; aspect-ratio: 4 / 3; background: #000; border-radius: 14px; overflow: hidden; border: 2.5px solid #1E3A2B; box-sizing: border-box; }
  #video { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
  #frame { position: absolute; border: 3px solid #22c55e; border-radius: 10px; box-shadow: 0 0 0 2000px rgba(15,23,42,0.62); pointer-events: none; }
  #detect { position: absolute; border: 3px solid #facc15; border-radius: 6px; display: none; pointer-events: none; }
  #hint { position: absolute; left: 0; right: 0; bottom: 6px; text-align: center; color: #fff; font-size: 13px; font-weight: 600; text-shadow: 0 1px 3px rgba(0,0,0,0.9); pointer-events: none; padding: 0 8px; }
  .row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  button { flex: 1; min-width: 110px; border: none; border-radius: 10px; padding: 12px 14px; font-size: 15px; font-weight: 700; cursor: pointer; color: #fff; background: #16a34a; }
  button.sec { background: #475569; }
  button:active { transform: scale(0.98); }
  #status { margin-top: 8px; font-size: 14px; color: #1E3A2B; text-align: center; min-height: 20px; }
  #status.err { color: #b91c1c; }
</style>
</head>
<body>
<div id="wrap">
  <div id="stage">
    <video id="video" autoplay playsinline muted></video>
    <div id="frame"></div>
    <div id="detect"></div>
    <div id="hint"></div>
  </div>
  <div class="row">
    <button id="btnScatta">📸 Scatta</button>
    <button id="btnTorcia" class="sec" style="display:none">🔦 Torcia</button>
    <button id="btnRiavvia" class="sec">🔄 Riavvia</button>
  </div>
  <div id="status"></div>
</div>
<script>
(function () {
  var wrap = document.getElementById("wrap");
  var video = document.getElementById("video");
  var stage = document.getElementById("stage");
  var frame = document.getElementById("frame");
  var detectBox = document.getElementById("detect");
  var hint = document.getElementById("hint");
  var statusEl = document.getElementById("status");
  var btnScatta = document.getElementById("btnScatta");
  var btnTorcia = document.getElementById("btnTorcia");
  var btnRiavvia = document.getElementById("btnRiavvia");

  var args = { modo: "etichetta", frame_w: 0.85, frame_h: 0.6 };
  var stream = null, track = null, torchOn = false, avviando = false;
  var detector = null, ultimo = null;

  try { if ("BarcodeDetector" in window) { detector = new BarcodeDetector(); } } catch (e) { detector = null; }

  function send(type, data) {
    var m = { isStreamlitMessage: true, type: type };
    for (var k in data) { m[k] = data[k]; }
    window.parent.postMessage(m, "*");
  }
  var ultimaAltezza = 0;
  function setHeight() {
    var h = Math.ceil(wrap.getBoundingClientRect().height) + 6;
    if (Math.abs(h - ultimaAltezza) < 2) { return; }
    ultimaAltezza = h;
    send("streamlit:setFrameHeight", { height: h });
  }
  function setStatus(t, err) { statusEl.textContent = t || ""; statusEl.className = err ? "err" : ""; }

  function applicaFrame() {
    var fw = args.frame_w, fh = args.frame_h;
    frame.style.width = (fw * 100) + "%";
    frame.style.height = (fh * 100) + "%";
    frame.style.left = ((1 - fw) / 2 * 100) + "%";
    frame.style.top = ((1 - fh) / 2 * 100) + "%";
    hint.textContent = (args.modo === "barcode")
      ? "Inquadra il codice a barre dentro il riquadro verde"
      : "Inquadra l'etichetta dentro il riquadro verde";
  }

  function geom() {
    var vw = video.videoWidth, vh = video.videoHeight;
    var cw = stage.clientWidth, ch = stage.clientHeight;
    if (!vw || !vh || !cw || !ch) { return null; }
    var s = Math.max(cw / vw, ch / vh);
    return { vw: vw, vh: vh, cw: cw, ch: ch, s: s, ox: (vw * s - cw) / 2, oy: (vh * s - ch) / 2 };
  }

  async function avvia() {
    if (stream || avviando) { return; }
    avviando = true;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false
      });
      video.srcObject = stream;
      track = stream.getVideoTracks()[0];
      var caps = (track && track.getCapabilities) ? (track.getCapabilities() || {}) : {};
      if (caps.focusMode && caps.focusMode.indexOf("continuous") >= 0) {
        try { await track.applyConstraints({ advanced: [{ focusMode: "continuous" }] }); } catch (e) {}
      }
      btnTorcia.style.display = caps.torch ? "block" : "none";
      setStatus("");
    } catch (err) {
      stream = null; track = null;
      setStatus("Fotocamera non disponibile: consenti l'accesso oppure usa «Carica una foto».", true);
    }
    avviando = false;
    setHeight();
  }

  function ferma() {
    if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); }
    stream = null; track = null; torchOn = false;
    video.srcObject = null;
  }

  function mostraBox() {
    var g = geom();
    if (!g || !ultimo || (Date.now() - ultimo.t) > 900) { detectBox.style.display = "none"; return; }
    var b = ultimo.box;
    detectBox.style.left = (b.x * g.s - g.ox) + "px";
    detectBox.style.top = (b.y * g.s - g.oy) + "px";
    detectBox.style.width = (b.width * g.s) + "px";
    detectBox.style.height = (b.height * g.s) + "px";
    detectBox.style.display = "block";
  }

  async function ciclo() {
    if (detector && stream && video.videoWidth) {
      try {
        var res = await detector.detect(video);
        if (res && res.length) {
          var scelto = res[0];
          for (var i = 0; i < res.length; i++) {
            if (/^\d{15}$/.test(res[i].rawValue || "")) { scelto = res[i]; break; }
          }
          ultimo = { box: scelto.boundingBox, value: scelto.rawValue || "", t: Date.now() };
        }
      } catch (e) {}
      mostraBox();
    }
    setTimeout(ciclo, 300);
  }

  function scatta() {
    var g = geom();
    if (!g || !stream) { setStatus("La fotocamera non è ancora pronta.", true); return; }
    var fw = args.frame_w, fh = args.frame_h;
    var sx = (g.cw * (1 - fw) / 2 + g.ox) / g.s;
    var sy = (g.ch * (1 - fh) / 2 + g.oy) / g.s;
    var sw = (g.cw * fw) / g.s;
    var sh = (g.ch * fh) / g.s;

    var recente = ultimo && ((Date.now() - ultimo.t) < 1500);
    if (args.modo === "barcode" && recente) {
      var b = ultimo.box;
      sx = b.x - b.width * 0.15;
      sy = b.y - b.height * 0.35;
      sw = b.width * 1.30;
      sh = b.height * 1.85;
    }
    sx = Math.max(0, sx); sy = Math.max(0, sy);
    sw = Math.min(g.vw - sx, sw); sh = Math.min(g.vh - sy, sh);
    if (sw < 10 || sh < 10) { setStatus("Inquadratura non valida, riprova.", true); return; }

    var k = Math.min(1, 1600 / Math.max(sw, sh));
    var canvas = document.createElement("canvas");
    canvas.width = Math.round(sw * k);
    canvas.height = Math.round(sh * k);
    canvas.getContext("2d").drawImage(video, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    var dataUrl = canvas.toDataURL("image/jpeg", 0.92);

    send("streamlit:setComponentValue", {
      value: { img: dataUrl, codice: recente ? ultimo.value : "", n: Date.now() },
      dataType: "json"
    });
    setStatus("✅ Foto acquisita: controlla il risultato qui sotto. Puoi scattare di nuovo se non va bene.");
  }

  btnScatta.addEventListener("click", scatta);
  btnRiavvia.addEventListener("click", function () { ferma(); avvia(); });
  btnTorcia.addEventListener("click", async function () {
    if (!track) { return; }
    try {
      torchOn = !torchOn;
      await track.applyConstraints({ advanced: [{ torch: torchOn }] });
    } catch (e) { torchOn = false; }
  });

  // La fotocamera si accende solo quando il riquadro è visibile (e si spegne quando non lo è)
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { avvia(); } else { ferma(); } });
    }, { threshold: 0.05 }).observe(stage);
  } else {
    avvia();
  }

  window.addEventListener("message", function (ev) {
    if (ev.data && ev.data.type === "streamlit:render") {
      var a = ev.data.args || {};
      if (a.modo) { args.modo = a.modo; }
      if (a.frame_w) { args.frame_w = a.frame_w; }
      if (a.frame_h) { args.frame_h = a.frame_h; }
      applicaFrame();
      setHeight();
    }
  });
  window.addEventListener("resize", setHeight);
  if ("ResizeObserver" in window) { new ResizeObserver(setHeight).observe(wrap); }
  window.addEventListener("pagehide", ferma);

  send("streamlit:componentReady", { apiVersion: 1 });
  applicaFrame();
  setHeight();
  ciclo();
})();
</script>
</body>
</html>
"""

CROP_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html, body { margin: 0; padding: 0; background: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  #wrap { width: 100%; max-width: 640px; margin: 0 auto; padding: 2px; box-sizing: border-box; }
  #area { padding: 16px; background: #111; border-radius: 14px; border: 2.5px solid #1E3A2B; box-sizing: border-box; overflow: hidden; }
  #inner { position: relative; line-height: 0; user-select: none; -webkit-user-select: none; }
  #img { width: 100%; height: auto; display: block; pointer-events: none; -webkit-user-drag: none; }
  #box { position: absolute; border: 2px solid #22c55e; box-shadow: 0 0 0 4000px rgba(15,23,42,0.62); touch-action: none; cursor: move; box-sizing: border-box; }
  .h { position: absolute; width: 30px; height: 30px; margin: -15px 0 0 -15px; touch-action: none; }
  .h::after { content: ""; position: absolute; left: 7px; top: 7px; width: 16px; height: 16px; background: #22c55e; border: 2px solid #fff; border-radius: 50%; box-sizing: border-box; }
  .h[data-h="nw"] { left: 0; top: 0; cursor: nwse-resize; }
  .h[data-h="n"]  { left: 50%; top: 0; cursor: ns-resize; }
  .h[data-h="ne"] { left: 100%; top: 0; cursor: nesw-resize; }
  .h[data-h="e"]  { left: 100%; top: 50%; cursor: ew-resize; }
  .h[data-h="se"] { left: 100%; top: 100%; cursor: nwse-resize; }
  .h[data-h="s"]  { left: 50%; top: 100%; cursor: ns-resize; }
  .h[data-h="sw"] { left: 0; top: 100%; cursor: nesw-resize; }
  .h[data-h="w"]  { left: 0; top: 50%; cursor: ew-resize; }
  .row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  button { flex: 1; min-width: 130px; border: none; border-radius: 10px; padding: 11px 12px; font-size: 14px; font-weight: 700; cursor: pointer; color: #fff; background: #475569; }
  button:active { transform: scale(0.98); }
  #info { margin-top: 8px; font-size: 13px; color: #1E3A2B; text-align: center; }
</style>
</head>
<body>
<div id="wrap">
  <div id="area">
    <div id="inner">
      <img id="img" alt="Foto da ritagliare">
      <div id="box">
        <div class="h" data-h="nw"></div><div class="h" data-h="n"></div><div class="h" data-h="ne"></div>
        <div class="h" data-h="e"></div><div class="h" data-h="se"></div><div class="h" data-h="s"></div>
        <div class="h" data-h="sw"></div><div class="h" data-h="w"></div>
      </div>
    </div>
  </div>
  <div class="row">
    <button id="btnIniziale">🎯 Riquadro suggerito</button>
    <button id="btnTutta">⬜ Tutta l'immagine</button>
  </div>
  <div id="info">Trascina gli angoli e i bordi per ritagliare. Sposta il riquadro trascinandolo al centro.</div>
</div>
<script>
(function () {
  var wrap = document.getElementById("wrap");
  var inner = document.getElementById("inner");
  var img = document.getElementById("img");
  var boxEl = document.getElementById("box");
  var btnIniziale = document.getElementById("btnIniziale");
  var btnTutta = document.getElementById("btnTutta");

  var box = { x0: 0.04, y0: 0.04, x1: 0.96, y1: 0.96 };
  var iniziale = [0.04, 0.04, 0.96, 0.96];
  var srcAttuale = null;
  var drag = null;
  var ultimaAltezza = 0;
  var MIN = 0.06;

  function send(type, data) {
    var m = { isStreamlitMessage: true, type: type };
    for (var k in data) { m[k] = data[k]; }
    window.parent.postMessage(m, "*");
  }
  function setHeight() {
    var h = Math.ceil(wrap.getBoundingClientRect().height) + 6;
    if (Math.abs(h - ultimaAltezza) < 2) { return; }
    ultimaAltezza = h;
    send("streamlit:setFrameHeight", { height: h });
  }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

  function aplica() {
    boxEl.style.left = (box.x0 * 100) + "%";
    boxEl.style.top = (box.y0 * 100) + "%";
    boxEl.style.width = ((box.x1 - box.x0) * 100) + "%";
    boxEl.style.height = ((box.y1 - box.y0) * 100) + "%";
  }
  function invia() {
    send("streamlit:setComponentValue", {
      value: { box: [box.x0, box.y0, box.x1, box.y1], n: Date.now() },
      dataType: "json"
    });
  }

  function onDown(e) {
    var t = e.target;
    var h = t.getAttribute ? t.getAttribute("data-h") : null;
    var mode = h || (t === boxEl ? "move" : null);
    if (!mode) { return; }
    e.preventDefault();
    try { t.setPointerCapture(e.pointerId); } catch (err) {}
    var r = inner.getBoundingClientRect();
    drag = { mode: mode, sx: e.clientX, sy: e.clientY, w: r.width || 1, h: r.height || 1,
             b: { x0: box.x0, y0: box.y0, x1: box.x1, y1: box.y1 } };
  }
  function onMove(e) {
    if (!drag) { return; }
    e.preventDefault();
    var dx = (e.clientX - drag.sx) / drag.w;
    var dy = (e.clientY - drag.sy) / drag.h;
    var b = drag.b, m = drag.mode;
    var x0 = b.x0, y0 = b.y0, x1 = b.x1, y1 = b.y1;
    if (m === "move") {
      var w = b.x1 - b.x0, h = b.y1 - b.y0;
      x0 = clamp(b.x0 + dx, 0, 1 - w); y0 = clamp(b.y0 + dy, 0, 1 - h);
      x1 = x0 + w; y1 = y0 + h;
    } else {
      if (m.indexOf("w") >= 0) { x0 = clamp(b.x0 + dx, 0, b.x1 - MIN); }
      if (m.indexOf("e") >= 0) { x1 = clamp(b.x1 + dx, b.x0 + MIN, 1); }
      if (m.indexOf("n") >= 0) { y0 = clamp(b.y0 + dy, 0, b.y1 - MIN); }
      if (m.indexOf("s") >= 0) { y1 = clamp(b.y1 + dy, b.y0 + MIN, 1); }
    }
    box = { x0: x0, y0: y0, x1: x1, y1: y1 };
    aplica();
  }
  function onUp() {
    if (!drag) { return; }
    drag = null;
    invia();
  }

  boxEl.addEventListener("pointerdown", onDown);
  boxEl.addEventListener("pointermove", onMove);
  boxEl.addEventListener("pointerup", onUp);
  boxEl.addEventListener("pointercancel", onUp);

  btnIniziale.addEventListener("click", function () {
    box = { x0: iniziale[0], y0: iniziale[1], x1: iniziale[2], y1: iniziale[3] };
    aplica(); invia();
  });
  btnTutta.addEventListener("click", function () {
    box = { x0: 0, y0: 0, x1: 1, y1: 1 };
    aplica(); invia();
  });

  img.addEventListener("load", function () { aplica(); setHeight(); });

  window.addEventListener("message", function (ev) {
    if (ev.data && ev.data.type === "streamlit:render") {
      var a = ev.data.args || {};
      // Il riquadro viene reimpostato SOLO quando arriva una nuova foto
      if (a.src && a.src !== srcAttuale) {
        srcAttuale = a.src;
        img.src = a.src;
        if (a.box && a.box.length === 4) {
          iniziale = a.box;
          box = { x0: a.box[0], y0: a.box[1], x1: a.box[2], y1: a.box[3] };
        }
        aplica();
      }
      setHeight();
    }
  });
  window.addEventListener("resize", setHeight);
  if ("ResizeObserver" in window) { new ResizeObserver(setHeight).observe(wrap); }

  send("streamlit:componentReady", { apiVersion: 1 });
  aplica();
  setHeight();
})();
</script>
</body>
</html>
"""

def _registra_componente(nome, sottocartella, html):
    """Crea (se serve) la cartella del componente e lo registra in Streamlit."""
    cartella = os.path.join(os.path.dirname(os.path.abspath(__file__)), sottocartella)
    os.makedirs(cartella, exist_ok=True)
    percorso = os.path.join(cartella, "index.html")
    aggiorna = True
    if os.path.exists(percorso):
        with open(percorso, "r", encoding="utf-8") as f:
            aggiorna = (f.read() != html)
    if aggiorna:
        with open(percorso, "w", encoding="utf-8") as f:
            f.write(html)
    return components.declare_component(nome, path=cartella)

try:
    _scanner_cam = _registra_componente("pethealth_scanner", "componente_scanner", SCANNER_HTML)
except Exception:
    _scanner_cam = None  # in questo caso si usa la fotocamera standard di Streamlit

try:
    _cropper = _registra_componente("pethealth_cropper", "componente_ritaglio", CROP_HTML)
except Exception:
    _cropper = None  # in questo caso il ritaglio si fa con i cursori

# ---------------------------------------------------------------------------
# I TUOI ANIMALI: cerchietti con le foto, cliccabili per cambiare il libretto attivo
# ---------------------------------------------------------------------------
AVATAR_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
  html, body { margin: 0; padding: 0; background: transparent; font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  #wrap { padding: 4px 4px 10px 4px; box-sizing: border-box; }
  #card { background: #FFFFFF; border: 1px solid #ECE6D6; border-radius: 20px; padding: 14px 18px 12px 18px; box-sizing: border-box;
          box-shadow: 0 1px 2px rgba(30,58,43,0.04), 0 14px 30px -22px rgba(30,58,43,0.25); }
  .pill { display: inline-block; background: #F4EEDD; color: #7A5F2A; border: 1px solid #E6DAB9; border-radius: 999px;
          font-size: 11px; font-weight: 700; letter-spacing: 0.12em; padding: 4px 13px; text-transform: uppercase; }
  #lista { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 14px 0 6px 0; }
  .av { background: none; border: none; padding: 4px; margin: 0; width: 76px; display: flex; flex-direction: column; align-items: center;
        cursor: pointer; font-family: inherit; border-radius: 14px; transition: transform 0.18s ease; }
  .av:hover { transform: translateY(-2px); }
  .av:focus-visible { outline: 2px solid #B8975A; outline-offset: 2px; }
  .cerchio { width: 56px; height: 56px; min-width: 56px; border-radius: 50%; overflow: hidden; display: flex; align-items: center; justify-content: center;
             box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 3.5px #E3D9BE; opacity: 0.88; transition: box-shadow 0.18s ease, opacity 0.18s ease; }
  .cerchio img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .cerchio.vuoto { background: linear-gradient(135deg, #F4EEDD, #E8F0EA); font-size: 28px; }
  .av:hover .cerchio { opacity: 1; }
  .av.attivo .cerchio { opacity: 1; box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 4.5px #B8975A, 0 8px 16px -8px rgba(30,58,43,0.55); }
  .nome { margin-top: 8px; max-width: 72px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; color: #5A6B62; font-weight: 600; }
  .av.attivo .nome { color: #1E3A2B; font-weight: 700; }
  #nota { font-size: 12px; color: #5B6A62; margin-top: 2px; }
</style>
</head>
<body>
<div id="wrap"><div id="card">
  <span class="pill">🐾 I tuoi animali</span>
  <div id="lista"></div>
  <div id="nota">Tocca una foto per aprire il libretto di quell'animale.</div>
</div></div>
<script>
(function () {
  var wrap = document.getElementById("wrap");
  var lista = document.getElementById("lista");
  var dati = { animali: [], attivo: "" };
  var ultimaAltezza = 0;

  function send(type, data) {
    var m = { isStreamlitMessage: true, type: type };
    for (var k in data) { m[k] = data[k]; }
    window.parent.postMessage(m, "*");
  }
  function setHeight() {
    var h = Math.ceil(wrap.getBoundingClientRect().height) + 4;
    if (Math.abs(h - ultimaAltezza) < 2) { return; }
    ultimaAltezza = h;
    send("streamlit:setFrameHeight", { height: h });
  }

  function disegna() {
    lista.innerHTML = "";
    dati.animali.forEach(function (a) {
      var attivo = (a.nome === dati.attivo);
      var b = document.createElement("button");
      b.type = "button";
      b.className = "av" + (attivo ? " attivo" : "");
      b.title = a.nome;
      b.setAttribute("aria-label", "Apri il libretto di " + a.nome);
      b.setAttribute("aria-pressed", attivo ? "true" : "false");
      var c = document.createElement("span");
      c.className = "cerchio";
      if (a.foto) {
        var im = document.createElement("img");
        im.src = a.foto; im.alt = "";
        c.appendChild(im);
      } else {
        c.className += " vuoto";
        c.textContent = a.emoji || "🐾";
      }
      var n = document.createElement("span");
      n.className = "nome";
      n.textContent = a.nome;
      b.appendChild(c); b.appendChild(n);
      b.addEventListener("click", function () {
        if (a.nome === dati.attivo) { return; }
        dati.attivo = a.nome;
        disegna();
        send("streamlit:setComponentValue", { value: { pet: a.nome, n: Date.now() }, dataType: "json" });
      });
      lista.appendChild(b);
    });
    setHeight();
  }

  window.addEventListener("message", function (ev) {
    if (ev.data && ev.data.type === "streamlit:render") {
      var a = ev.data.args || {};
      dati.animali = a.animali || [];
      dati.attivo = a.attivo || "";
      disegna();
    }
  });
  window.addEventListener("resize", setHeight);
  if ("ResizeObserver" in window) { new ResizeObserver(setHeight).observe(wrap); }
  send("streamlit:componentReady", { apiVersion: 1 });
  setHeight();
})();
</script>
</body>
</html>
"""

try:
    _avatar = _registra_componente("pethealth_avatar", "componente_avatar", AVATAR_HTML)
except Exception:
    _avatar = None  # in questo caso si usano i pulsanti con il nome dell'animale

@st.cache_data(show_spinner=False, max_entries=50)
def miniatura_foto_animale(b64_img):
    """Miniatura quadrata leggera (120 px) della foto, per i cerchietti. Restituisce '' se la foto non è leggibile."""
    try:
        img = Image.open(io.BytesIO(base64.b64decode(b64_img))).convert("RGB")
        w, h = img.size
        lato = min(w, h)
        sx, sy = (w - lato) // 2, (h - lato) // 2
        img = img.crop((sx, sy, sx + lato, sy + lato)).resize((120, 120), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""

def seleziona_animale(nome):
    """Cambia il libretto attivo, come se l'utente lo avesse scelto dalla barra laterale."""
    utente_corrente = st.session_state.db_users[st.session_state.logged_user_email]
    utente_corrente["pet_selezionato"] = nome
    st.session_state["pet_select_forza"] = nome      # la barra laterale lo applica al prossimo ciclo
    salva_dati()
    st.rerun()


def azzera_scansione(chiave):
    """Svuota il riquadro di scansione (da chiamare dopo il salvataggio)."""
    k = f"scan_cnt_{chiave}"
    st.session_state[k] = st.session_state.get(k, 0) + 1

def scansiona_etichetta(chiave, titolo, descrizione, modo_guida="etichetta"):
    """Fotocamera guidata (o caricamento foto), rimozione sfondo. Restituisce (immagine_base64, codice_letto).
    modo_guida: "barcode" (microchip) oppure "etichetta" (vaccino)."""
    cnt_key = f"scan_cnt_{chiave}"
    if cnt_key not in st.session_state:
        st.session_state[cnt_key] = 0
    n = st.session_state[cnt_key]

    if modo_guida == "barcode":
        frame_w, frame_h = 0.88, 0.36
    else:
        frame_w, frame_h = 0.84, 0.66

    st.markdown(f"##### {titolo}")
    st.caption(descrizione)

    modo = st.radio(
        "Come vuoi acquisire l'immagine?",
        ["📷 Fotocamera guidata", "🖼️ Carica una foto"],
        horizontal=True, key=f"scan_modo_{chiave}_{n}"
    )

    foto_bytes = None
    codice_js = ""

    if modo.startswith("📷"):
        if _scanner_cam is not None:
            st.caption("🎯 Posiziona il codice/etichetta dentro il **riquadro verde** e premi «Scatta»: verrà salvato solo ciò che è dentro il riquadro. "
                       "Se il tuo telefono lo supporta, il codice a barre viene riconosciuto da solo e segnato in giallo.")
            risultato_cam = _scanner_cam(
                key=f"scan_cam_{chiave}_{n}", modo=modo_guida,
                frame_w=frame_w, frame_h=frame_h, default=None
            )
            if risultato_cam and risultato_cam.get("img"):
                try:
                    foto_bytes = base64.b64decode(risultato_cam["img"].split(",", 1)[1])
                    codice_js = (risultato_cam.get("codice") or "").strip()
                except Exception:
                    foto_bytes = None
        else:
            st.caption("💡 Inquadra bene l'etichetta, occupando gran parte della foto.")
            foto = st.camera_input("Inquadra l'etichetta e scatta", key=f"scan_cam_{chiave}_{n}")
            if foto is not None:
                foto_bytes = foto.getvalue()
    else:
        st.caption("💡 Su smartphone scegli «Scatta foto» per usare la fotocamera posteriore. Avvicinati: l'etichetta deve riempire la foto.")
        foto = st.file_uploader("Scegli la foto dell'etichetta", type=["png", "jpg", "jpeg"], key=f"scan_up_{chiave}_{n}")
        if foto is not None:
            foto_bytes = foto.getvalue()

    if foto_bytes is None:
        return None, ""

    # --- Ritaglio manuale (facoltativo) ---
    foto_lavoro = foto_bytes
    ritaglio_auto = True
    if st.checkbox("✂️ Ritaglia l'immagine acquisita", key=f"scan_crop_on_{chiave}_{n}",
                   help="Trascina il riquadro verde per tenere solo l'etichetta."):
        try:
            anteprima, box_iniziale = prepara_anteprima_ritaglio(foto_bytes)
            box_scelto = box_iniziale
            if _cropper is not None:
                st.caption("Trascina gli angoli e i bordi del riquadro verde per tenere solo l'etichetta. "
                           "Il riquadro parte già posizionato sull'etichetta riconosciuta.")
                chiave_foto = hashlib.md5(foto_bytes).hexdigest()[:10]
                sel = _cropper(key=f"scan_crop_{chiave}_{n}_{chiave_foto}", src=anteprima, box=box_iniziale, default=None)
                if sel and sel.get("box") and len(sel["box"]) == 4:
                    box_scelto = sel["box"]
            else:
                st.caption("Usa i cursori per scegliere la parte da tenere.")
                sx = st.slider("Ritaglio orizzontale (%)", 0, 100, (int(box_iniziale[0] * 100), int(box_iniziale[2] * 100)), key=f"scan_sx_{chiave}_{n}")
                sy = st.slider("Ritaglio verticale (%)", 0, 100, (int(box_iniziale[1] * 100), int(box_iniziale[3] * 100)), key=f"scan_sy_{chiave}_{n}")
                if sx[1] - sx[0] >= 3 and sy[1] - sy[0] >= 3:
                    box_scelto = [sx[0] / 100, sy[0] / 100, sx[1] / 100, sy[1] / 100]
            foto_lavoro = ritaglia_bytes(foto_bytes, box_scelto)
            ritaglio_auto = False  # il ritaglio lo ha deciso l'utente
        except Exception as e:
            st.warning(f"Ritaglio non disponibile per questa foto: {e}")
            foto_lavoro = foto_bytes
            ritaglio_auto = True

    scelta = st.radio(
        "Versione da salvare",
        ["✨ Etichetta pulita (sfondo rimosso)", "📄 Foto originale"],
        horizontal=True, key=f"scan_ver_{chiave}_{n}"
    )
    rimuovi = scelta.startswith("✨")

    try:
        b64, codici = elabora_etichetta(foto_lavoro, rimuovi, ritaglio_auto)
    except Exception as e:
        st.error(f"Non è stato possibile elaborare l'immagine: {e}")
        return None, ""

    c1, c2 = st.columns(2)
    with c1:
        st.caption("Foto acquisita" if foto_lavoro is foto_bytes else "Foto ritagliata")
        st.image(foto_lavoro)
    with c2:
        st.caption("Risultato che verrà salvato")
        st.image(base64.b64decode(b64))

    codice = codice_js or (codici[0] if codici else "")
    if codice:
        st.success(f"🔎 Codice a barre letto: `{codice}`")
    if modo_guida == "barcode":
        if codice_microchip_valido(codice):
            svg_prev = genera_barcode_svg(codice)
            if svg_prev:
                st.caption("🖨️ Versione digitale (vettoriale) del codice a barre, che verrà mostrata nell'anagrafica:")
                st.markdown(svg_in_html(svg_prev), unsafe_allow_html=True)
        elif codice:
            st.warning("Il codice letto non sembra un numero di microchip (15 cifre): controllalo e scrivilo a mano nel campo «Numero Microchip».")
        else:
            st.caption("ℹ️ Il numero non è stato letto dalla foto: scrivilo nel campo «Numero Microchip» e l'app creerà il codice a barre digitale.")
    st.info("✅ Immagine pronta: verrà salvata quando confermi con il pulsante di salvataggio.")
    return b64, codice

def mostra_immagine_salvata(b64_img, didascalia="", larghezza=None):
    """Mostra un'immagine salvata (base64) nelle schede."""
    if not b64_img:
        return
    try:
        dati = base64.b64decode(b64_img)
        if didascalia:
            st.caption(didascalia)
        if larghezza:
            st.image(dati, width=larghezza)
        else:
            st.image(dati)
    except Exception:
        st.warning("Immagine salvata non leggibile.")

# ---------------------------------------------------------------------------
# CODICE A BARRE DIGITALE (vettoriale, SVG) - standard Code 128
# Parte dal numero del microchip e disegna un codice nitido, senza sfondo né ombre.
# ---------------------------------------------------------------------------
_CODE128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312", "132212", "221213",
    "221312", "231212", "112232", "122132", "122231", "113222", "123122", "123221", "223211", "221132",
    "221231", "213212", "223112", "312131", "311222", "321122", "321221", "312212", "322112", "322211",
    "212123", "212321", "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121", "313121", "211331",
    "231131", "213113", "213311", "213131", "311123", "311321", "331121", "312113", "312311", "332111",
    "314111", "221411", "431111", "111224", "111422", "121124", "121421", "141122", "141221", "112214",
    "112412", "122114", "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112", "421211", "212141",
    "214121", "412121", "111143", "111341", "131141", "114113", "114311", "411113", "411311", "113141",
    "114131", "311141", "411131", "211412", "211214", "211232", "2331112",
]

def _code128_valori(testo):
    """Converte il testo nella sequenza di simboli Code 128 (con cifre in Set C quando possibile)."""
    if testo.isdigit() and len(testo) >= 2:
        valori = [105]                                  # Start C
        pari = len(testo) - (len(testo) % 2)
        for i in range(0, pari, 2):
            valori.append(int(testo[i:i + 2]))
        if len(testo) % 2:
            valori.append(100)                          # passa al Set B per l'ultima cifra
            valori.append(ord(testo[-1]) - 32)
    else:
        valori = [104] + [ord(c) - 32 for c in testo]   # Start B
    controllo = valori[0] + sum(i * v for i, v in enumerate(valori[1:], 1))
    valori.append(controllo % 103)
    valori.append(106)                                  # Stop
    return valori

def genera_barcode_svg(testo, altezza=80, modulo=2, quiet=10):
    """Restituisce il codice a barre Code 128 come immagine SVG (testo), oppure None se non è possibile."""
    testo = "".join(str(testo or "").split())
    if not testo or any(ord(c) < 32 or ord(c) > 126 for c in testo):
        return None
    elementi = "".join(_CODE128_PATTERNS[v] for v in _code128_valori(testo))
    moduli_totali = sum(int(c) for c in elementi)
    larghezza = (moduli_totali + 2 * quiet) * modulo
    totale_h = altezza + 30
    barre, x, e_barra = [], quiet * modulo, True
    for c in elementi:
        w = int(c) * modulo
        if e_barra:
            barre.append(f'<rect x="{x}" y="4" width="{w}" height="{altezza}"/>')
        x += w
        e_barra = not e_barra
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {larghezza} {totale_h}" width="{larghezza}" height="{totale_h}">'
        f'<rect width="100%" height="100%" fill="#ffffff"/>'
        f'<g fill="#000000" shape-rendering="crispEdges">{"".join(barre)}</g>'
        f'<text x="{larghezza / 2}" y="{altezza + 24}" text-anchor="middle" font-family="monospace" '
        f'font-size="18" letter-spacing="2" fill="#000000">{html_escape(testo)}</text>'
        f'</svg>'
    )

def svg_in_html(svg, larghezza_max=360):
    """Prepara l'SVG per essere mostrato dentro una scheda HTML."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (f'<div style="text-align:center;margin:6px 0 10px 0;">'
            f'<img alt="Codice a barre del microchip" src="data:image/svg+xml;base64,{b64}" '
            f'style="width:100%;max-width:{larghezza_max}px;border:1px solid #E2E8F0;border-radius:8px;"></div>')


# ---------------------------------------------------------------------------
# PESO: formattazione, dati del grafico e grafico dell'andamento (immagine SVG nitida)
# ---------------------------------------------------------------------------
def _num_it(valore, decimali):
    """12.4 -> '12,4' (virgola decimale all'italiana)."""
    return f"{valore:.{decimali}f}".replace(".", ",")

def fmt_peso(kg):
    """0.35 -> '350 g'  |  12.4 -> '12,4 kg'"""
    try:
        kg = float(kg)
    except Exception:
        return "—"
    if kg < 1:
        return f"{round(kg * 1000)} g"
    return f"{kg:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " kg"

def fmt_variazione(delta_kg):
    """+0,8 kg  /  -120 g"""
    segno = "+" if delta_kg > 0 else ("-" if delta_kg < 0 else "")
    return segno + fmt_peso(abs(delta_kg))

def _tick_gradevoli(lo, hi, n=5):
    """Scala 'a numeri tondi' per l'asse verticale. Restituisce (valori, passo)."""
    if hi <= lo:
        hi = lo + 1.0
    grezzo = (hi - lo) / max(1, n - 1)
    mag = 10 ** math.floor(math.log10(grezzo))
    passo = mag * 10
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= grezzo:
            passo = m * mag
            break
    primo = math.ceil(lo / passo - 1e-9) * passo
    valori, k = [], 0
    while k <= 12:
        t = round(primo + k * passo, 6)
        if t > hi + 1e-9:
            break
        valori.append(t)
        k += 1
    if len(valori) < 2:
        valori = [round(lo, 6), round(hi, 6)]
    return valori, passo

def _prepara_grafico_peso(voci, max_tick_x=5):
    """Trasforma l'elenco delle pesate nei dati pronti per disegnare il grafico (usato da app e PDF)."""
    punti = []
    for v in voci or []:
        try:
            d = date.fromisoformat(str(v.get("data"))[:10])
            kg = float(v.get("peso_kg"))
        except Exception:
            continue
        if kg > 0:
            punti.append((d, kg))
    if not punti:
        return None
    punti.sort(key=lambda p: p[0])

    in_grammi = max(p[1] for p in punti) < 1.0          # animali molto piccoli: si mostrano i grammi
    f = 1000.0 if in_grammi else 1.0
    valori = [p[1] * f for p in punti]
    vmin, vmax = min(valori), max(valori)
    margine = (vmax - vmin) * 0.25 if vmax > vmin else max(vmax * 0.1, 1.0)
    lo, hi = max(0.0, vmin - margine), vmax + margine
    ticks, passo = _tick_gradevoli(lo, hi, 5)
    if abs(passo - round(passo)) < 1e-9:
        dec = 0
    elif abs(passo * 10 - round(passo * 10)) < 1e-9:
        dec = 1
    else:
        dec = 2

    d0, d1 = punti[0][0], punti[-1][0]
    span = (d1 - d0).days
    def frazione(d):
        return 0.5 if span == 0 else (d - d0).days / span

    tutti_interi = all(abs(v - round(v)) < 0.05 for v in valori)
    def etichetta(v):
        if in_grammi:
            return str(round(v)) if tutti_interi else _num_it(v, 1)
        return _num_it(v, 2).rstrip("0").rstrip(",")

    # date da scrivere sotto l'asse (senza sovrapposizioni)
    if len(punti) <= max_tick_x or span == 0:
        candidate = sorted({p[0] for p in punti})
    else:
        candidate = [d0 + timedelta(days=round(span * i / (max_tick_x - 1))) for i in range(max_tick_x)]
    xticks, ultimo_fx = [], -1.0
    for d in candidate:
        fx = frazione(d)
        if ultimo_fx < 0 or fx - ultimo_fx >= 0.16:
            xticks.append((fx, d.strftime("%d/%m/%y")))
            ultimo_fx = fx

    return {
        "unita": "g" if in_grammi else "kg",
        "punti": [{"fx": frazione(d), "v": v, "txt": etichetta(v), "data": d} for (d, _), v in zip(punti, valori)],
        "ticks": [(t, _num_it(t, dec)) for t in ticks],
        "ylo": lo, "yhi": hi,
        "xticks": xticks,
    }

def _indici_con_etichetta(g):
    """Quali punti portano il valore scritto: se sono tanti solo primo/ultimo/minimo/massimo, e mai due etichette sovrapposte."""
    n = len(g["punti"])
    if n <= 10:
        candidati = list(range(n))
    else:
        valori = [p["v"] for p in g["punti"]]
        candidati = sorted({0, n - 1, valori.index(min(valori)), valori.index(max(valori))})
    intervallo = (g["yhi"] - g["ylo"]) or 1.0
    scelti = []
    for i in candidati:
        p = g["punti"][i]
        if scelti:
            q = g["punti"][scelti[-1]]
            vicino = abs(p["fx"] - q["fx"]) < 0.075 and abs(p["v"] - q["v"]) / intervallo < 0.14
            if vicino:
                if i == n - 1:          # l'ultima pesata ha la precedenza
                    scelti.pop()
                else:
                    continue
        scelti.append(i)
    return set(scelti)

def genera_grafico_peso_svg(voci):
    """Grafico dell'andamento del peso come immagine SVG (testo), oppure None se non ci sono pesate valide."""
    g = _prepara_grafico_peso(voci)
    if not g:
        return None
    W, H = 560, 330
    sx, dx, top, bas = 70, 22, 48, 60
    area_w, area_h = W - sx - dx, H - top - bas
    pad = 20
    base_y = top + area_h

    def X(fx):
        return sx + pad + fx * (area_w - 2 * pad)

    def Y(v):
        return top + (1 - (v - g["ylo"]) / (g["yhi"] - g["ylo"])) * area_h

    s = [f'<rect width="{W}" height="{H}" rx="14" fill="#ffffff"/>',
         f'<text x="{sx}" y="28" font-size="18" font-weight="700" fill="#1E3A2B">Andamento del peso ({g["unita"]})</text>']
    for val, txt in g["ticks"]:
        y = Y(val)
        s.append(f'<line x1="{sx}" y1="{y:.1f}" x2="{W - dx}" y2="{y:.1f}" stroke="#E2E8F0" stroke-width="1"/>')
        s.append(f'<text x="{sx - 8}" y="{y + 5:.1f}" text-anchor="end" font-size="16" fill="#475569">{txt}</text>')
    s.append(f'<line x1="{sx}" y1="{base_y}" x2="{W - dx}" y2="{base_y}" stroke="#94A3B8" stroke-width="1.5"/>')
    for fx, txt in g["xticks"]:
        x = X(fx)
        s.append(f'<line x1="{x:.1f}" y1="{base_y}" x2="{x:.1f}" y2="{base_y + 6}" stroke="#94A3B8" stroke-width="1.5"/>')
        s.append(f'<text x="{x:.1f}" y="{base_y + 26}" text-anchor="middle" font-size="15" fill="#475569">{txt}</text>')

    xy = [(X(p["fx"]), Y(p["v"])) for p in g["punti"]]
    if len(xy) > 1:
        area = f"{xy[0][0]:.1f},{base_y} " + " ".join(f"{x:.1f},{y:.1f}" for x, y in xy) + f" {xy[-1][0]:.1f},{base_y}"
        s.append(f'<polygon points="{area}" fill="#0284C7" fill-opacity="0.12"/>')
        linea = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
        s.append(f'<polyline points="{linea}" fill="none" stroke="#0284C7" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
    for x, y in xy:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="#ffffff" stroke="#0284C7" stroke-width="3"/>')
    for i in sorted(_indici_con_etichetta(g)):          # le etichette sopra tutti i punti
        x, y = xy[i]
        ty = y - 13 if y - 13 > top - 4 else y + 25
        ancora = "start" if x < sx + 24 else ("end" if x > W - dx - 24 else "middle")
        s.append(f'<text x="{x:.1f}" y="{ty:.1f}" text-anchor="{ancora}" font-size="16" font-weight="700" fill="#0F172A" '
                 f'stroke="#ffffff" stroke-width="4" paint-order="stroke">{g["punti"][i]["txt"]}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'font-family="Arial, Helvetica, sans-serif">{"".join(s)}</svg>')

def grafico_in_html(svg, larghezza_max=720):
    """Prepara il grafico SVG per essere mostrato nella pagina."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (f'<div style="margin:6px 0 14px 0;"><img alt="Grafico dell\'andamento del peso" src="data:image/svg+xml;base64,{b64}" '
            f'style="width:100%;max-width:{larghezza_max}px;border:1px solid #E2E8F0;border-radius:14px;"></div>')


# ---------------------------------------------------------------------------
# CALORE: registrazione dei periodi, statistiche e calendario annuale (solo per le femmine)
# ---------------------------------------------------------------------------
SESSI = ["Non specificato", "Maschio", "Femmina"]
MESI_IT = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
           "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
GIORNI_IT = ["L", "M", "M", "G", "V", "S", "D"]

def _data_o_none(valore):
    try:
        return date.fromisoformat(str(valore)[:10])
    except Exception:
        return None

def periodi_calore(voci, oggi=None):
    """Elenco ordinato dei calori registrati, con data di fine effettiva (se è ancora in corso vale 'oggi')."""
    oggi = oggi or date.today()
    elenco = []
    for idx, c in enumerate(voci or []):
        ini = _data_o_none(c.get("inizio"))
        if not ini:
            continue
        fin = _data_o_none(c.get("fine")) if c.get("fine") else None
        fin_eff = fin if fin else max(ini, oggi)
        if fin_eff < ini:
            fin_eff = ini
        elenco.append({"inizio": ini, "fine": fin, "fine_eff": fin_eff, "in_corso": fin is None,
                       "note": c.get("note", ""), "idx": idx})
    elenco.sort(key=lambda p: p["inizio"])
    return elenco

def durata_giorni(p):
    return (p["fine_eff"] - p["inizio"]).days + 1

def statistiche_calori(voci, oggi=None):
    """Numero di calori, durata e intervallo medi, stima (indicativa) del prossimo calore."""
    oggi = oggi or date.today()
    per = periodi_calore(voci, oggi)
    if not per:
        return None
    durate = [durata_giorni(p) for p in per if not p["in_corso"]]
    intervalli = [(per[i]["inizio"] - per[i - 1]["inizio"]).days for i in range(1, len(per))]
    media_int = round(sum(intervalli) / len(intervalli)) if intervalli else None
    media_dur = round(sum(durate) / len(durate)) if durate else None
    prossimo = per[-1]["inizio"] + timedelta(days=media_int) if media_int else None
    in_corso = next((p for p in reversed(per) if p["in_corso"] and p["inizio"] <= oggi), None)
    return {"n": len(per), "periodi": per, "durata_media": media_dur, "intervallo_medio": media_int,
            "prossimo": prossimo, "in_corso": in_corso}

def giorni_di_calore(periodi, limite=120):
    giorni = set()
    for p in periodi:
        d = p["inizio"]
        while d <= p["fine_eff"] and (d - p["inizio"]).days <= limite:
            giorni.add(d)
            d += timedelta(days=1)
    return giorni

def genera_calendario_calori_html(anno, stat, oggi=None):
    """Calendario dei 12 mesi dell'anno con i giorni di calore evidenziati (HTML senza righe vuote)."""
    oggi = oggi or date.today()
    periodi = stat["periodi"] if stat else []
    giorni = giorni_di_calore(periodi)
    stima = set()
    if stat and stat.get("prossimo"):
        for k in range(stat["durata_media"] or 1):
            stima.add(stat["prossimo"] + timedelta(days=k))
    cal = calendar.Calendar(firstweekday=0)
    mesi = []
    for mese in range(1, 13):
        righe = ["<tr>" + "".join(f"<th>{g}</th>" for g in GIORNI_IT) + "</tr>"]
        for settimana in cal.monthdayscalendar(anno, mese):
            celle = []
            for giorno in settimana:
                if giorno == 0:
                    celle.append("<td></td>")
                    continue
                d = date(anno, mese, giorno)
                classi = []
                if d in giorni:
                    classi.append("cal-calore")
                elif d in stima:
                    classi.append("cal-stima")
                if d == oggi:
                    classi.append("cal-oggi")
                celle.append(f'<td class="{" ".join(classi)}">{giorno}</td>')
            righe.append("<tr>" + "".join(celle) + "</tr>")
        mesi.append(f'<div class="cal-mese"><div class="cal-titolo">{MESI_IT[mese - 1]} {anno}</div>'
                    f'<table class="cal-tab">{"".join(righe)}</table></div>')
    legenda = ('<div class="cal-legenda"><span><i class="cal-box cal-box-calore"></i> Giorni di calore</span>'
               + ('<span><i class="cal-box cal-box-stima"></i> Stima indicativa del prossimo calore</span>' if stima else "")
               + '<span><i class="cal-box cal-box-oggi"></i> Oggi</span></div>')
    return f'<div class="cal-griglia">{"".join(mesi)}</div>{legenda}'


# ---------------------------------------------------------------------------
# LIBRETTO SANITARIO IN PDF (anagrafica + microchip vettoriale, visite con etichette, terapie, fatture)
# ---------------------------------------------------------------------------
PDF_VERDE = "#1E3A2B"
PDF_AZZURRO = "#0284C7"
PDF_GRIGIO_CHIARO = "#F1F5F9"
PDF_BORDO = "#CBD5E1"

def _pdf_txt(valore, vuoto="—"):
    """Prepara un testo per il PDF: toglie le emoji (i font del PDF non le hanno) e protegge i simboli speciali."""
    s = "" if valore is None else str(valore)
    s = s.encode("cp1252", "ignore").decode("cp1252").strip()
    if not s:
        return vuoto
    return html_escape(s, quote=False).replace("\n", "<br/>")

def _data_it(valore):
    """2024-03-05 -> 05/03/2024"""
    try:
        return date.fromisoformat(str(valore)[:10]).strftime("%d/%m/%Y")
    except Exception:
        return _pdf_txt(valore)

def _importo_it(valore):
    """1234.5 -> 1.234,50"""
    try:
        return f"{float(valore):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"

def _pdf_immagine(b64_img, larghezza_max, altezza_max):
    """Crea l'immagine per il PDF mantenendo le proporzioni. Restituisce None se non valida."""
    if not b64_img:
        return None
    try:
        dati = base64.b64decode(b64_img)
        with Image.open(io.BytesIO(dati)) as im:
            w, h = im.size
        if w < 1 or h < 1:
            return None
        fattore = min(larghezza_max / w, altezza_max / h)
        return RLImage(io.BytesIO(dati), width=w * fattore, height=h * fattore)
    except Exception:
        return None

if REPORTLAB_OK:
    class CodiceBarreCode128(Flowable):
        """Codice a barre Code 128 disegnato come vero VETTORIALE dentro il PDF."""
        def __init__(self, testo, altezza=1.7 * cm, modulo=0.45 * mm):
            Flowable.__init__(self)
            self.testo = "".join(str(testo).split())
            self.elementi = "".join(_CODE128_PATTERNS[v] for v in _code128_valori(self.testo))
            self.modulo = modulo
            self.altezza = altezza
            self.quiet = 10 * modulo
            self.larghezza = sum(int(c) for c in self.elementi) * modulo + 2 * self.quiet
            self.hAlign = "LEFT"

        def wrap(self, larghezza_disp, altezza_disp):
            return self.larghezza, self.altezza + 0.6 * cm

        def draw(self):
            c = self.canv
            c.setFillColor(colors.white)
            c.rect(0, 0, self.larghezza, self.altezza + 0.6 * cm, stroke=0, fill=1)
            c.setFillColor(colors.black)
            x, e_barra = self.quiet, True
            for ch in self.elementi:
                w = int(ch) * self.modulo
                if e_barra:
                    c.rect(x, 0.5 * cm, w, self.altezza, stroke=0, fill=1)
                x += w
                e_barra = not e_barra
            c.setFont("Helvetica", 9)
            c.drawCentredString(self.larghezza / 2, 0.12 * cm, self.testo)

    class GraficoPesoPDF(Flowable):
        """Grafico dell'andamento del peso, disegnato in vettoriale dentro il PDF."""
        def __init__(self, g, larghezza, altezza=7.2 * cm):
            Flowable.__init__(self)
            self.g = g
            self.larghezza = larghezza
            self.altezza = altezza
            self.hAlign = "LEFT"

        def wrap(self, larghezza_disp, altezza_disp):
            return self.larghezza, self.altezza

        def draw(self):
            c, g = self.canv, self.g
            azzurro = colors.HexColor("#0284C7")
            grigio = colors.HexColor("#475569")
            sx, dx, top, bas = 1.7 * cm, 0.7 * cm, 1.3 * cm, 1.2 * cm
            area_w = self.larghezza - sx - dx
            area_h = self.altezza - top - bas
            pad = 0.5 * cm

            def X(fx):
                return sx + pad + fx * (area_w - 2 * pad)

            def Y(v):
                return bas + (v - g["ylo"]) / (g["yhi"] - g["ylo"]) * area_h

            c.setStrokeColor(colors.HexColor("#CBD5E1"))
            c.setFillColor(colors.white)
            c.setLineWidth(0.6)
            c.roundRect(0, 0, self.larghezza, self.altezza, 6, stroke=1, fill=1)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.HexColor("#1E3A2B"))
            c.drawString(sx, self.altezza - 0.75 * cm, f"Andamento del peso ({g['unita']})")

            c.setFont("Helvetica", 8)
            for val, txt in g["ticks"]:
                y = Y(val)
                c.setStrokeColor(colors.HexColor("#E2E8F0"))
                c.setLineWidth(0.5)
                c.line(sx, y, self.larghezza - dx, y)
                c.setFillColor(grigio)
                c.drawRightString(sx - 0.2 * cm, y - 2.5, txt)

            c.setStrokeColor(colors.HexColor("#94A3B8"))
            c.setLineWidth(0.8)
            c.line(sx, bas, self.larghezza - dx, bas)
            for fx, txt in g["xticks"]:
                x = X(fx)
                c.line(x, bas, x, bas - 3)
                c.setFillColor(grigio)
                c.drawCentredString(x, bas - 0.5 * cm, txt)

            xy = [(X(p["fx"]), Y(p["v"])) for p in g["punti"]]
            if len(xy) > 1:
                tracciato = c.beginPath()
                tracciato.moveTo(xy[0][0], bas)
                for x, y in xy:
                    tracciato.lineTo(x, y)
                tracciato.lineTo(xy[-1][0], bas)
                tracciato.close()
                c.setFillColor(colors.HexColor("#E0F2FE"))
                c.drawPath(tracciato, stroke=0, fill=1)
                c.setStrokeColor(azzurro)
                c.setLineWidth(1.8)
                for (x1, y1), (x2, y2) in zip(xy, xy[1:]):
                    c.line(x1, y1, x2, y2)
            c.setLineWidth(1.6)
            c.setStrokeColor(azzurro)
            c.setFillColor(colors.white)
            for x, y in xy:
                c.circle(x, y, 2.6, stroke=1, fill=1)
            c.setFont("Helvetica-Bold", 8.5)
            c.setFillColor(colors.HexColor("#0F172A"))
            for i in sorted(_indici_con_etichetta(g)):
                x, y = xy[i]
                c.drawCentredString(x, y + 5, g["punti"][i]["txt"])

def genera_pdf_libretto(pet, user_db, includi_fatture=True):
    """Crea il PDF del libretto sanitario dell'animale e restituisce i byte del file."""
    if not REPORTLAB_OK:
        raise RuntimeError("Libreria reportlab non installata")

    verde = colors.HexColor(PDF_VERDE)
    azzurro = colors.HexColor(PDF_AZZURRO)
    grigio_chiaro = colors.HexColor(PDF_GRIGIO_CHIARO)
    bordo = colors.HexColor(PDF_BORDO)
    testo_grigio = colors.HexColor("#475569")

    oggi_txt = date.today().strftime("%d/%m/%Y")
    pet_pulito = pet.encode("cp1252", "ignore").decode("cp1252") or "animale"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=2.3 * cm, bottomMargin=1.8 * cm,
        title=f"Libretto sanitario - {pet_pulito}", author="PetHealth"
    )
    W = doc.width - 12  # il riquadro di pagina ha 6 pt di margine interno per lato

    stile = {
        "titolo": ParagraphStyle("titolo", fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=verde),
        "nome": ParagraphStyle("nome", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=azzurro),
        "sotto": ParagraphStyle("sotto", fontName="Helvetica", fontSize=10, leading=14, textColor=testo_grigio),
        "banda": ParagraphStyle("banda", fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=colors.white),
        "sezione2": ParagraphStyle("sezione2", fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=verde, spaceBefore=6, spaceAfter=3),
        "cella": ParagraphStyle("cella", fontName="Helvetica", fontSize=9.5, leading=12.5, textColor=colors.HexColor("#1E293B")),
        "etichetta": ParagraphStyle("etichetta", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=testo_grigio),
        "testata": ParagraphStyle("testata", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=verde),
        "testata_dx": ParagraphStyle("testata_dx", fontName="Helvetica-Bold", fontSize=9, leading=13, alignment=2),
        "th": ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.white),
        "vuoto": ParagraphStyle("vuoto", fontName="Helvetica-Oblique", fontSize=9.5, leading=13, textColor=testo_grigio),
        "piccolo": ParagraphStyle("piccolo", fontName="Helvetica", fontSize=8, leading=11, textColor=testo_grigio),
    }

    def P(testo, nome="cella"):
        return Paragraph(testo, stile[nome])

    def banda(titolo):
        t = Table([[P(_pdf_txt(titolo), "banda")]], colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), azzurro),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    def tabella_chiave_valore(righe, larghezza_chiave=4.2 * cm):
        dati = [[P(_pdf_txt(k), "etichetta"), v if not isinstance(v, str) else P(v)] for k, v in righe]
        t = Table(dati, colWidths=[larghezza_chiave, W - larghezza_chiave])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), grigio_chiaro),
            ("BOX", (0, 0), (-1, -1), 0.6, bordo), ("INNERGRID", (0, 0), (-1, -1), 0.3, bordo),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    def tabella_elenco(intestazioni, righe, larghezze, allinea_dx=()):
        dati = [[P(_pdf_txt(h), "th") for h in intestazioni]] + righe
        t = Table(dati, colWidths=larghezze, repeatRows=1)
        stile_t = [
            ("BACKGROUND", (0, 0), (-1, 0), verde),
            ("BOX", (0, 0), (-1, -1), 0.6, bordo), ("INNERGRID", (0, 0), (-1, -1), 0.3, bordo),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, grigio_chiaro]),
        ]
        for col in allinea_dx:
            stile_t.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
        t.setStyle(TableStyle(stile_t))
        return t

    # --------------------------------------------------------------- dati
    ana = user_db.get("db_anagrafica", {}).get(pet, {}) or {}
    visite = sorted(user_db.get("db_visite", {}).get(pet, []), key=lambda v: str(v.get("data", "")))
    terapie = sorted(user_db.get("db_terapie", {}).get(pet, []), key=lambda t: str(t.get("data_inizio", "")))
    pesi = sorted(user_db.get("db_peso", {}).get(pet, []), key=lambda p: str(p.get("data", "")))
    fatture = sorted(user_db.get("db_fatture", {}).get(pet, []), key=lambda f: str(f.get("data", "")))

    storia = []

    numero_sezione = [0]

    def apri_sezione(titolo, spazio=5 * cm):
        numero_sezione[0] += 1
        storia.append(CondPageBreak(spazio))   # se resta poco spazio, passa alla pagina successiva
        storia.append(banda(f"{numero_sezione[0]}. {titolo}"))

    def sottotitolo(titolo):
        storia.append(CondPageBreak(3.5 * cm))
        storia.append(P(titolo, "sezione2"))

    # --------------------------------------------------------------- intestazione
    blocco_titolo = [P("Libretto Sanitario Digitale", "titolo"), Spacer(1, 4), P(_pdf_txt(ana.get("nome") or pet), "nome")]
    sotto = " · ".join([x for x in [ana.get("tipo_animale"), ana.get("razza")] if x])
    if sotto:
        blocco_titolo.append(P(_pdf_txt(sotto), "sotto"))
    blocco_titolo.append(P(f"Documento generato il {oggi_txt}", "sotto"))
    img_pet = _pdf_immagine(ana.get("foto_animale"), 3.6 * cm, 4.2 * cm)
    if img_pet:
        img_pet.hAlign = "CENTER"
        intestazione = Table([[blocco_titolo, img_pet]], colWidths=[W - 4.4 * cm, 4.4 * cm])
        intestazione.setStyle(TableStyle([
            ("VALIGN", (0, 0), (0, 0), "TOP"), ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 0),
            ("TOPPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
            ("BOX", (1, 0), (1, 0), 1.2, colors.HexColor("#B8975A")),
            ("LEFTPADDING", (1, 0), (1, 0), 5), ("RIGHTPADDING", (1, 0), (1, 0), 5),
            ("TOPPADDING", (1, 0), (1, 0), 5), ("BOTTOMPADDING", (1, 0), (1, 0), 5),
        ]))
        storia.append(intestazione)
    else:
        storia.extend(blocco_titolo)
    storia.append(Spacer(1, 12))

    # --------------------------------------------------------------- anagrafica
    apri_sezione("Anagrafica dell'animale")
    storia.append(Spacer(1, 6))
    codice_mc = (ana.get("microchip") or "").strip()
    righe_ana = [
        ("Nome", _pdf_txt(ana.get("nome") or pet)),
        ("Specie", _pdf_txt(ana.get("tipo_animale"))),
        ("Sesso", _pdf_txt(ana.get("sesso"), "Non specificato")),
        ("Razza", _pdf_txt(ana.get("razza"))),
        ("Data di nascita", _data_it(ana.get("data_nascita")) if ana.get("data_nascita") else "—"),
        ("Numero microchip", _pdf_txt(codice_mc, "Non inserito")),
        ("Segni particolari", _pdf_txt(ana.get("segni_particolari"), "Nessuno")),
    ]
    storia.append(tabella_chiave_valore(righe_ana))

    if codice_mc and genera_barcode_svg(codice_mc):
        storia.append(Spacer(1, 8))
        storia.append(KeepTogether([
            P("Codice a barre del microchip (versione digitale vettoriale)", "sezione2"),
            CodiceBarreCode128(codice_mc),
        ]))
    img_mc = _pdf_immagine(ana.get("microchip_foto"), 8 * cm, 4 * cm)
    if img_mc:
        img_mc.hAlign = "LEFT"
        storia.append(Spacer(1, 6))
        storia.append(KeepTogether([P("Scansione originale dell'etichetta del microchip", "sezione2"), img_mc]))

    storia.append(Spacer(1, 10))
    sottotitolo("Proprietario")
    storia.append(tabella_chiave_valore([
        ("Nome e cognome", _pdf_txt(ana.get("proprietario_nome") or user_db.get("nome"))),
        ("Indirizzo", _pdf_txt(ana.get("proprietario_indirizzo"))),
        ("Città", _pdf_txt(ana.get("proprietario_citta"))),
        ("Telefono", _pdf_txt(ana.get("proprietario_telefono") or user_db.get("numero_whatsapp"))),
    ]))
    storia.append(Spacer(1, 14))

    # --------------------------------------------------------------- visite
    apri_sezione("Visite mediche e vaccinazioni")
    storia.append(Spacer(1, 6))

    vaccini = [v for v in visite if v.get("nome_vaccino") or v.get("tipo") == "Vaccinazione"]
    if vaccini:
        sottotitolo("Riepilogo vaccinazioni")
        righe_vac = []
        for v in vaccini:
            righe_vac.append([
                P(_data_it(v.get("data"))), P(_pdf_txt(v.get("nome_vaccino"))), P(_pdf_txt(v.get("lotto_vaccino"))),
                P(_data_it(v.get("scadenza_vaccino")) if v.get("scadenza_vaccino") else "—"),
                P("Certificata" if v.get("certificata") else "In attesa di firma"),
            ])
        storia.append(tabella_elenco(["Data", "Vaccino", "Lotto", "Scadenza", "Stato"], righe_vac,
                                     [2.6 * cm, W - 2.6 * cm - 3.2 * cm - 2.6 * cm - 3.4 * cm, 3.2 * cm, 2.6 * cm, 3.4 * cm]))
        storia.append(Spacer(1, 10))

    if visite:
        sottotitolo("Dettaglio delle visite")
        for v in visite:
            cert = bool(v.get("certificata"))
            stato = '<font color="#15803D"><b>CERTIFICATA</b></font>' if cert else '<font color="#B45309"><b>In attesa di firma</b></font>'
            testata = Table([[P(f"{_data_it(v.get('data'))} &nbsp;-&nbsp; {_pdf_txt(v.get('tipo'))}", "testata"), P(stato, "testata_dx")]],
                            colWidths=[W * 0.62, W * 0.38])
            testata.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E0F2FE")),
                ("BOX", (0, 0), (-1, -1), 0.6, bordo), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            righe_v = [("Veterinario / clinica", _pdf_txt(v.get("veterinario")))]
            if cert:
                righe_v.append(("Codice certificato", _pdf_txt(v.get("codice_certificato"))))
                righe_v.append(("ID medico permanente", _pdf_txt(v.get("vet_id_permanente"))))
                if v.get("num_ordine_vet"):
                    righe_v.append(("Iscrizione ordine (FNOVI)", _pdf_txt(f"N. {v.get('num_ordine_vet')} - {str(v.get('provincia_vet', '')).upper()}")))
            if v.get("nome_vaccino") or v.get("tipo") == "Vaccinazione":
                righe_v.append(("Vaccino", _pdf_txt(v.get("nome_vaccino"))))
                righe_v.append(("Lotto", _pdf_txt(v.get("lotto_vaccino"))))
                if v.get("scadenza_vaccino"):
                    righe_v.append(("Scadenza vaccino", _data_it(v.get("scadenza_vaccino"))))
            righe_v.append(("Diagnosi / note cliniche", _pdf_txt(v.get("diagnosi"))))
            if v.get("referto"):
                righe_v.append(("Referto allegato", _pdf_txt(v.get("referto"))))
            img_et = _pdf_immagine(v.get("etichetta_vaccino"), 8 * cm, 5.5 * cm)
            if img_et:
                img_et.hAlign = "LEFT"
                righe_v.append(("Etichetta del vaccino", img_et))
            storia.append(KeepTogether([testata, tabella_chiave_valore(righe_v), Spacer(1, 9)]))
    else:
        storia.append(P("Nessuna visita medica registrata.", "vuoto"))
    storia.append(Spacer(1, 10))

    # --------------------------------------------------------------- terapie
    apri_sezione("Terapie e farmaci")
    storia.append(Spacer(1, 6))
    if terapie:
        righe_t = []
        for t in terapie:
            note = _pdf_txt(t.get("note"), "")
            if t.get("ricetta"):
                note = (note + "<br/>" if note else "") + f"Ricetta: {_pdf_txt(t.get('ricetta'))}"
            righe_t.append([P(_pdf_txt(t.get("farmaco"))), P(_pdf_txt(t.get("dosaggio"))), P(_pdf_txt(t.get("orario"))),
                            P(_pdf_txt(t.get("periodo"))), P(note or "—")])
        storia.append(tabella_elenco(["Farmaco", "Dose", "Orario", "Periodo", "Istruzioni / note"], righe_t,
                                     [3.6 * cm, 2.8 * cm, 1.8 * cm, 4.2 * cm, W - 3.6 * cm - 2.8 * cm - 1.8 * cm - 4.2 * cm]))
    else:
        storia.append(P("Nessuna terapia registrata.", "vuoto"))
    storia.append(Spacer(1, 14))

    # --------------------------------------------------------------- peso
    apri_sezione("Peso e andamento", spazio=9.5 * cm)
    storia.append(Spacer(1, 6))
    grafico = _prepara_grafico_peso(pesi)
    if grafico:
        storia.append(GraficoPesoPDF(grafico, W))
        storia.append(Spacer(1, 8))
        validi = []
        for pz in pesi:
            try:
                validi.append((pz, float(pz.get("peso_kg"))))
            except Exception:
                continue
        righe_p = [[P(_data_it(pz.get("data"))), P(_pdf_txt(fmt_peso(kg))), P(_pdf_txt(pz.get("note"), "—"))] for pz, kg in validi]
        storia.append(tabella_elenco(["Data", "Peso", "Note"], righe_p, [3 * cm, 3.4 * cm, W - 6.4 * cm]))
        if len(validi) >= 2:
            (p0, k0), (p1, k1) = validi[0], validi[-1]
            storia.append(Spacer(1, 4))
            storia.append(P(f"Prima pesata: {_data_it(p0.get('data'))} ({_pdf_txt(fmt_peso(k0))}) &nbsp;|&nbsp; "
                            f"Ultima pesata: {_data_it(p1.get('data'))} ({_pdf_txt(fmt_peso(k1))}) &nbsp;|&nbsp; "
                            f"Variazione: {_pdf_txt(fmt_variazione(k1 - k0))}", "sotto"))
    else:
        storia.append(P("Nessuna pesata registrata.", "vuoto"))
    storia.append(Spacer(1, 14))

    # --------------------------------------------------------------- calore (solo femmine o se ci sono dati)
    calori_pdf = periodi_calore(user_db.get("db_calori", {}).get(pet, []))
    if ana.get("sesso") == "Femmina" or calori_pdf:
        apri_sezione("Calore (calendario dei calori)")
        storia.append(Spacer(1, 6))
        if calori_pdf:
            righe_c = []
            for pc in calori_pdf:
                righe_c.append([P(_data_it(str(pc["inizio"]))),
                                P(_data_it(str(pc["fine"])) if pc["fine"] else "In corso"),
                                P(f"{durata_giorni(pc)} giorni" + (" (finora)" if pc["in_corso"] else "")),
                                P(_pdf_txt(pc["note"], "—"))])
            storia.append(tabella_elenco(["Inizio", "Fine", "Durata", "Note"], righe_c,
                                         [3 * cm, 3 * cm, 3.4 * cm, W - 9.4 * cm]))
            stat_c = statistiche_calori(user_db.get("db_calori", {}).get(pet, []))
            parti = [f"Calori registrati: {stat_c['n']}"]
            if stat_c["durata_media"]:
                parti.append(f"durata media: {stat_c['durata_media']} giorni")
            if stat_c["intervallo_medio"]:
                parti.append(f"intervallo medio tra un calore e l'altro: {stat_c['intervallo_medio']} giorni")
            storia.append(Spacer(1, 4))
            storia.append(P(" &nbsp;|&nbsp; ".join(parti), "sotto"))
        else:
            storia.append(P("Nessun calore registrato.", "vuoto"))
        storia.append(Spacer(1, 14))

    # --------------------------------------------------------------- fatture
    if includi_fatture:
        apri_sezione("Fatture e spese")
        storia.append(Spacer(1, 6))
        if fatture:
            righe_f, totale = [], 0.0
            for f in fatture:
                try:
                    totale += float(f.get("importo", 0) or 0)
                except Exception:
                    pass
                righe_f.append([P(_data_it(f.get("data"))), P(_pdf_txt(f.get("categoria"))), P(_pdf_txt(f.get("fornitore"))),
                                P(f"€ {_importo_it(f.get('importo'))}")])
            righe_f.append([P(""), P(""), P("<b>Totale</b>"), P(f"<b>€ {_importo_it(totale)}</b>")])
            tab_f = tabella_elenco(["Data", "Categoria", "Clinica / farmacia", "Importo"], righe_f,
                                   [2.6 * cm, 4.6 * cm, W - 2.6 * cm - 4.6 * cm - 3.2 * cm, 3.2 * cm], allinea_dx=(3,))
            storia.append(tab_f)
        else:
            storia.append(P("Nessuna fattura registrata.", "vuoto"))
        storia.append(Spacer(1, 14))

    storia.append(P("Le prestazioni indicate come «Certificata» sono state convalidate dal medico veterinario tramite PIN nell'app PetHealth. "
                    "Documento generato automaticamente da PetHealth.", "piccolo"))

    def decora_pagina(canvas, documento):
        canvas.saveState()
        larghezza_pagina, altezza_pagina = A4
        canvas.setStrokeColor(azzurro)
        canvas.setLineWidth(1.8)
        canvas.line(documento.leftMargin, altezza_pagina - 1.55 * cm, larghezza_pagina - documento.rightMargin, altezza_pagina - 1.55 * cm)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(verde)
        canvas.drawString(documento.leftMargin, altezza_pagina - 1.3 * cm, "PetHealth")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(testo_grigio)
        canvas.drawRightString(larghezza_pagina - documento.rightMargin, altezza_pagina - 1.3 * cm, f"Libretto sanitario di {pet_pulito}")
        canvas.drawCentredString(larghezza_pagina / 2, 1.0 * cm, f"Pagina {documento.page}")
        canvas.restoreState()

    doc.build(storia, onFirstPage=decora_pagina, onLaterPages=decora_pagina)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# FOTO DELL'ANIMALE: scelta (galleria o scatto), ritaglio facoltativo, ridimensionamento e visualizzazione
# ---------------------------------------------------------------------------
EMOJI_SPECIE = {"Cane": "🐶", "Gatto": "🐱", "Coniglio": "🐰", "Uccello": "🐦", "Rettile": "🦎"}

def elabora_foto_animale(raw_bytes):
    """Prepara la foto per essere salvata: orientamento corretto, sfondo bianco se trasparente, max 900 px, JPEG leggero."""
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        sfondo = Image.new("RGB", img.size, (255, 255, 255))
        sfondo.paste(img, mask=img.split()[-1])
        img = sfondo
    else:
        img = img.convert("RGB")
    img.thumbnail((900, 900))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")

@st.cache_data(show_spinner=False, max_entries=10)
def anteprima_foto_ritaglio(raw_bytes):
    """Anteprima leggera della foto per lo strumento di ritaglio."""
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((900, 900))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

def html_foto_animale(b64_img, specie, nome, dimensione=116):
    """Foto tonda con cornice dorata; se manca la foto mostra un segnaposto con l'emoji della specie."""
    stile = (f"width:{dimensione}px;height:{dimensione}px;min-width:{dimensione}px;max-width:{dimensione}px;"
             "aspect-ratio:1/1;border-radius:50%;flex:none;display:block;overflow:hidden;")
    stile += ("box-shadow:0 0 0 3px #FFFFFF, 0 0 0 5px #B8975A, 0 14px 26px -12px rgba(30,58,43,0.5);")
    if b64_img:
        return (f'<img alt="Foto di {html_escape(str(nome), quote=True)}" '
                f'src="data:image/jpeg;base64,{b64_img}" style="{stile}object-fit:cover;">')
    emoji = EMOJI_SPECIE.get(specie, "🐾")
    return (f'<div style="{stile}display:flex;align-items:center;justify-content:center;font-size:{int(dimensione * 0.5)}px;'
            f'background:linear-gradient(135deg,#F4EEDD,#E8F0EA);">{emoji}</div>')

def scegli_foto_animale(chiave):
    """Interfaccia per scegliere la foto dell'animale. Restituisce la foto pronta (base64) oppure None."""
    n = st.session_state.get(f"scan_cnt_{chiave}", 0)
    modo = st.radio("Come vuoi inserire la foto?", ["🖼️ Carica una foto", "📷 Scatta ora"],
                    horizontal=True, key=f"fa_modo_{chiave}_{n}")
    if modo.startswith("📷"):
        file_foto = st.camera_input("Scatta una foto al tuo animale", key=f"fa_cam_{chiave}_{n}")
    else:
        st.caption("💡 Su smartphone puoi scegliere una foto dalla galleria oppure scattarla al momento.")
        file_foto = st.file_uploader("Scegli la foto (JPG, PNG o WEBP)", type=["jpg", "jpeg", "png", "webp"],
                                     key=f"fa_up_{chiave}_{n}")
    if file_foto is None:
        return None

    grezza = file_foto.getvalue()
    foto_lavoro = grezza
    if st.checkbox("✂️ Ritaglia la foto", key=f"fa_crop_{chiave}_{n}"):
        try:
            box_iniziale = [0.04, 0.04, 0.96, 0.96]
            box_scelto = box_iniziale
            if _cropper is not None:
                st.caption("Trascina gli angoli e i bordi del riquadro verde per scegliere la parte da tenere.")
                chiave_foto = hashlib.md5(grezza).hexdigest()[:10]
                sel = _cropper(key=f"fa_cropper_{chiave}_{n}_{chiave_foto}", src=anteprima_foto_ritaglio(grezza),
                               box=box_iniziale, default=None)
                if sel and sel.get("box") and len(sel["box"]) == 4:
                    box_scelto = sel["box"]
            else:
                sx = st.slider("Ritaglio orizzontale (%)", 0, 100, (4, 96), key=f"fa_sx_{chiave}_{n}")
                sy = st.slider("Ritaglio verticale (%)", 0, 100, (4, 96), key=f"fa_sy_{chiave}_{n}")
                if sx[1] - sx[0] >= 3 and sy[1] - sy[0] >= 3:
                    box_scelto = [sx[0] / 100, sy[0] / 100, sx[1] / 100, sy[1] / 100]
            foto_lavoro = ritaglia_bytes(grezza, box_scelto)
        except Exception as e:
            st.warning(f"Ritaglio non disponibile per questa foto: {e}")
            foto_lavoro = grezza

    try:
        pronta = elabora_foto_animale(foto_lavoro)
    except Exception:
        st.error("Non riesco a leggere questa immagine. Prova con una foto in formato JPG o PNG.")
        return None
    st.caption("Anteprima della foto che verrà salvata:")
    st.image(base64.b64decode(pronta), width=240)
    return pronta


def codice_microchip_valido(codice):
    """Un microchip ISO valido ha 15 cifre."""
    return bool(codice) and codice.isdigit() and len(codice) == 15

def mostra_scansionatore_barre(titolo="📷 Scansiona Etichetta Vaccino o Microchip"):
    """Lettore live di barcode (usato per i farmaci nella sezione Terapie)."""
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
    div[data-testid="stDownloadButton"] > button {
        background-color: #1E3A2B !important; border: 1px solid #1E3A2B !important;
        border-radius: 12px !important; padding: 0.75rem 1.5rem !important; width: 100% !important;
        box-shadow: 0 4px 12px rgba(30, 58, 43, 0.15) !important;
    }
    div[data-testid="stDownloadButton"] > button p, div[data-testid="stDownloadButton"] > button span {
        color: #FFFFFF !important; font-weight: 700 !important; font-size: 1rem !important;
    }

    /* ===== CALENDARIO DEL CALORE ===== */

.cal-griglia { display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: 12px; margin: 8px 0 12px 0; }
.cal-mese { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 10px 10px 8px 10px; }
.cal-titolo { font-weight: 700; color: #1E3A2B; margin-bottom: 6px; font-size: 0.95rem; }
.cal-tab { width: 100%; border-collapse: separate !important; border-spacing: 2px !important; table-layout: fixed; margin: 0 !important; }
.cal-tab tr { background: transparent !important; }
.cal-tab th { border: none !important; background: transparent !important; font-size: 0.68rem; color: #64748B; font-weight: 600; text-align: center; padding: 2px 0 !important; }
.cal-tab td { border: none !important; background: transparent; height: 26px; text-align: center; font-size: 0.78rem; color: #1E293B; border-radius: 7px; padding: 0 !important; }
.cal-tab td.cal-calore { background: #F43F5E !important; color: #FFFFFF !important; font-weight: 700; }
.cal-tab td.cal-stima { box-shadow: inset 0 0 0 1.5px #F43F5E; color: #BE123C; }
.cal-tab td.cal-oggi { outline: 2px solid #0284C7; outline-offset: -1px; font-weight: 700; }
.cal-legenda { display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.82rem; color: #475569; margin-bottom: 10px; }
.cal-box { display: inline-block; width: 14px; height: 14px; border-radius: 4px; vertical-align: -2px; margin-right: 4px; }
.cal-box-calore { background: #F43F5E; } .cal-box-stima { box-shadow: inset 0 0 0 1.5px #F43F5E; } .cal-box-oggi { outline: 2px solid #0284C7; outline-offset: -1px; }

    /* ===== MENU LATERALE AZZURRO CON SCRITTE BIANCHE (uguale su tutti i dispositivi) ===== */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarUserContent"] {
        background-color: #0284C7 !important;
        background-image: none !important;
    }
    [data-testid="stSidebar"] { border-right: 1px solid #0369A1 !important; }

    /* Tutte le scritte del menù in bianco */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] li, [data-testid="stSidebar"] small, [data-testid="stSidebar"] summary,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { opacity: 1 !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, 0.45) !important; }

    /* Campi di testo e menù a tendina: sfondo bianco e testo scuro, per restare leggibili */
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {
        color: #0F172A !important; -webkit-text-fill-color: #0F172A !important; background-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] input::placeholder, [data-testid="stSidebar"] textarea::placeholder {
        color: #64748B !important; -webkit-text-fill-color: #64748B !important;
    }
    [data-testid="stSidebar"] [data-baseweb="input"], [data-testid="stSidebar"] [data-baseweb="base-input"],
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #0F172A !important; -webkit-text-fill-color: #0F172A !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] svg { fill: #0F172A !important; }

    /* Pulsanti del menù */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        background-color: #0369A1 !important; border: 1px solid rgba(255, 255, 255, 0.55) !important; box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
        background-color: #075985 !important;
    }

    /* Riquadri a scomparsa e messaggi dentro il menù */
    [data-testid="stSidebar"] [data-testid="stExpander"] details {
        background-color: rgba(255, 255, 255, 0.14) !important;
        border: 1px solid rgba(255, 255, 255, 0.45) !important; border-radius: 12px !important;
    }
    [data-testid="stSidebar"] summary svg { fill: #FFFFFF !important; color: #FFFFFF !important; }
    [data-testid="stSidebar"] [data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.18) !important; border: 1px solid rgba(255, 255, 255, 0.45) !important;
    }

    /* Freccia per chiudere il menù (dentro il menù) e per riaprirlo (sempre visibile, azzurra) */
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button:hover {
        background-color: transparent !important; border: none !important; box-shadow: none !important;
    }
    [data-testid="stSidebarCollapseButton"] svg, [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarHeader"] svg {
        color: #FFFFFF !important; fill: #FFFFFF !important;
    }
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button {
        background-color: #0284C7 !important; border-radius: 10px !important;
    }
    [data-testid="stExpandSidebarButton"] svg, [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {
        color: #FFFFFF !important; fill: #FFFFFF !important;
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
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# GRAFICA RAFFINATA
# Tutti questi stili valgono SOLO per l'area principale: il menù laterale azzurro resta identico.
# Palette: verde profondo (#1E3A2B), avorio (#F8F6F0), oro champagne (#B8975A), azzurro del menù (#0284C7).
# ---------------------------------------------------------------------------
_PREFISSI_AREA_PRINCIPALE = [
    'section.main',
    '[data-testid="stMain"]',
    '[data-testid="stAppViewContainer"] > section:not([data-testid="stSidebar"])',
]

def _css_area_principale(regole):
    """Applica ogni regola solo all'area principale della pagina (mai al menù laterale)."""
    blocchi = []
    for selettori, dichiarazioni in regole:
        elenco = []
        for s in selettori.split("|"):
            s = s.strip()
            for pref in _PREFISSI_AREA_PRINCIPALE:
                elenco.append(f"{pref} {s}")
        blocchi.append(",\n".join(elenco) + " {" + dichiarazioni + "}")
    return "\n".join(blocchi)

_FONT_TITOLI = "'Playfair Display', Georgia, 'Times New Roman', serif"

_REGOLE_GRAFICA = [
    # --- impaginazione ---
    ('[data-testid="stMainBlockContainer"] | .block-container',
     'padding-top: 2.4rem !important; max-width: 1240px !important; margin-left: auto !important; margin-right: auto !important;'),

    # --- titoli ---
    ('h1 | h2 | h3',
     "font-family: " + _FONT_TITOLI + " !important; font-weight: 600 !important; letter-spacing: -0.01em !important;"),
    ('h1', 'font-size: 2.3rem !important; line-height: 1.15 !important;'),
    ('h2', 'font-size: 1.7rem !important; line-height: 1.25 !important;'),
    ('h3', 'font-size: 1.28rem !important; line-height: 1.3 !important;'),
    ('h2::after',
     'content: ""; display: block; width: 58px; height: 2px; margin-top: 10px; '
     'background: linear-gradient(90deg, #B8975A, rgba(184, 151, 90, 0));'),
    ('.wellness-card h2::after', 'display: none;'),
    ('p | li', 'line-height: 1.6;'),
    ('code',
     'background: #F3EFE3 !important; color: #5E4B1F !important; border-radius: 6px !important; '
     'padding: 0.12rem 0.45rem !important; font-size: 0.88em !important;'),
    ('hr',
     'border: none !important; height: 1px !important; margin: 1.6rem 0 !important; '
     'background: linear-gradient(90deg, rgba(184,151,90,0), #CDB98A, rgba(184,151,90,0)) !important;'),
    ('[data-testid="stCaptionContainer"]', 'color: #5B6A62 !important;'),

    # --- schede ---
    ('.wellness-card',
     'background: #FFFFFF !important; border: 1px solid #ECE6D6 !important; border-radius: 20px !important; '
     'padding: 22px 26px !important; margin-bottom: 18px !important; '
     'box-shadow: 0 1px 2px rgba(30, 58, 43, 0.04), 0 18px 40px -24px rgba(30, 58, 43, 0.24) !important; '
     'transition: box-shadow 0.25s ease, transform 0.25s ease;'),
    ('.wellness-card:hover',
     'box-shadow: 0 1px 2px rgba(30, 58, 43, 0.05), 0 24px 46px -24px rgba(30, 58, 43, 0.32) !important; transform: translateY(-1px);'),
    ('.wellness-card p', 'margin: 0.3rem 0 !important; color: #2B3A33;'),
    ('.auth-container',
     'border: 1px solid #ECE6D6 !important; border-top: 3px solid #B8975A !important; border-radius: 24px !important; '
     'box-shadow: 0 1px 2px rgba(30, 58, 43, 0.04), 0 28px 60px -30px rgba(30, 58, 43, 0.30) !important;'),

    # --- etichette (badge) ---
    ('.card-badge',
     'background: #F4EEDD !important; color: #7A5F2A !important; border: 1px solid #E6DAB9; '
     'font-size: 0.68rem !important; font-weight: 700 !important; letter-spacing: 0.12em !important; padding: 4px 13px !important;'),
    ('.badge-purple', 'background: #E8F0EA !important; color: #1E3A2B !important; border-color: #CFE0D4 !important;'),
    ('.badge-blue', 'background: #E3F1F9 !important; color: #0B5F8A !important; border-color: #C5E1F1 !important;'),
    ('.badge-green', 'background: #E4F2E7 !important; color: #1E6B3A !important; border-color: #C6E3CC !important;'),

    # --- pulsanti ---
    ('.stButton > button | [data-testid="stBaseButton-secondary"] | [data-testid="stBaseButton-primary"] | '
     '[data-testid="stFormSubmitButton"] > button | [data-testid="stDownloadButton"] > button',
     'background: linear-gradient(135deg, #2A5240 0%, #1E3A2B 100%) !important; border: 1px solid #1E3A2B !important; '
     'border-radius: 14px !important; padding: 0.7rem 1.4rem !important; '
     'box-shadow: 0 8px 18px -8px rgba(30, 58, 43, 0.5) !important; '
     'transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease !important;'),
    ('.stButton > button:hover | [data-testid="stBaseButton-secondary"]:hover | [data-testid="stBaseButton-primary"]:hover | '
     '[data-testid="stFormSubmitButton"] > button:hover | [data-testid="stDownloadButton"] > button:hover',
     'transform: translateY(-1px); filter: brightness(1.08); box-shadow: 0 14px 24px -10px rgba(30, 58, 43, 0.55) !important;'),
    ('.stButton > button:active | [data-testid="stFormSubmitButton"] > button:active | [data-testid="stDownloadButton"] > button:active',
     'transform: translateY(0); filter: brightness(0.98);'),
    ('.stButton > button:focus-visible | [data-testid="stFormSubmitButton"] > button:focus-visible | [data-testid="stDownloadButton"] > button:focus-visible',
     'outline: 2px solid #B8975A !important; outline-offset: 2px !important;'),
    ('.stButton > button p | .stButton > button span | [data-testid="stFormSubmitButton"] > button p | '
     '[data-testid="stDownloadButton"] > button p',
     'font-size: 0.95rem !important; font-weight: 600 !important; letter-spacing: 0.012em !important;'),
    ('[data-testid^="stBaseLinkButton"]',
     'border: 1.5px solid #1E3A2B !important; border-radius: 14px !important; background: #FFFFFF !important; '
     'box-shadow: 0 6px 14px -8px rgba(30, 58, 43, 0.35) !important; transition: transform 0.18s ease, background 0.18s ease !important;'),
    ('[data-testid^="stBaseLinkButton"]:hover', 'background: #F4EEDD !important; transform: translateY(-1px);'),
    ('[data-testid^="stBaseLinkButton"] p', 'color: #1E3A2B !important; font-weight: 600 !important;'),

    # --- campi di inserimento ---
    ('[data-baseweb="input"] | [data-baseweb="textarea"] | [data-baseweb="select"] > div',
     'background-color: #FFFFFF !important; border: 1px solid #DCD5C2 !important; border-radius: 12px !important; '
     'box-shadow: none !important; transition: border-color 0.18s ease, box-shadow 0.18s ease;'),
    ('[data-baseweb="input"]:focus-within | [data-baseweb="textarea"]:focus-within | [data-baseweb="select"] > div:focus-within',
     'border-color: #0284C7 !important; box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.14) !important;'),
    ('[data-baseweb="base-input"]', 'background-color: transparent !important; border-radius: 12px !important;'),
    ('[data-testid="stWidgetLabel"] p | [data-testid="stWidgetLabel"] label',
     'font-size: 0.84rem !important; font-weight: 600 !important; color: #3C4B43 !important; letter-spacing: 0.01em;'),
    ('[data-testid="stFileUploaderDropzone"]',
     'border: 1.5px dashed #CDB98A !important; background: #FBF9F3 !important; border-radius: 16px !important;'),
    ('[data-testid="stForm"]',
     'border: 1px solid #ECE6D6 !important; border-radius: 20px !important; background: #FFFFFF; padding: 1.3rem 1.5rem !important; '
     'box-shadow: 0 18px 40px -28px rgba(30, 58, 43, 0.22);'),

    # --- tendine ---
    ('[data-testid="stExpander"] details',
     'background: #FFFFFF !important; border: 1px solid #E9E3D3 !important; border-radius: 16px !important; '
     'box-shadow: 0 1px 2px rgba(30, 58, 43, 0.04); transition: box-shadow 0.22s ease, border-color 0.22s ease;'),
    ('[data-testid="stExpander"] details:hover',
     'border-color: #D6CAA8 !important; box-shadow: 0 14px 28px -20px rgba(30, 58, 43, 0.30);'),
    ('[data-testid="stExpander"] summary', 'padding: 0.8rem 1.1rem !important; border-radius: 16px;'),
    ('[data-testid="stExpander"] summary p', 'font-weight: 600 !important; color: #1E3A2B !important;'),

    # --- schede di accesso (tab) ---
    ('button[data-baseweb="tab"]', 'font-weight: 600 !important; color: #5A6B62;'),
    ('button[data-baseweb="tab"][aria-selected="true"]', 'color: #1E3A2B !important;'),
    ('[data-baseweb="tab-highlight"]', 'background-color: #B8975A !important; height: 3px !important; border-radius: 3px;'),
    ('[data-baseweb="tab-border"]', 'background-color: #E9E3D3 !important;'),

    # --- numeri (metriche) e messaggi ---
    ('[data-testid="stMetric"]',
     'background: #FFFFFF; border: 1px solid #ECE6D6; border-radius: 18px; padding: 14px 18px; '
     'box-shadow: 0 1px 2px rgba(30, 58, 43, 0.04), 0 14px 30px -22px rgba(30, 58, 43, 0.25);'),
    ('[data-testid="stMetricLabel"] p',
     'font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.09em !important; font-weight: 700 !important; color: #5B6A62 !important;'),
    ('[data-testid="stMetricValue"]', "font-family: " + _FONT_TITOLI + " !important; color: #1E3A2B !important; font-weight: 600 !important;"),
    ('[data-testid="stAlert"]', 'border-radius: 14px !important; border: 1px solid rgba(30, 58, 43, 0.12) !important;'),

    # --- immagini e fotocamera ---
    ('[data-testid="stImage"] img', 'border-radius: 12px; border: 1px solid #ECE6D6;'),
    ('[data-testid="stCameraInput"] > div', 'border-radius: 16px;'),

    # --- calendario del calore ---
    ('.cal-mese',
     'border: 1px solid #ECE6D6 !important; border-radius: 18px !important; padding: 12px 12px 10px 12px !important; '
     'box-shadow: 0 1px 2px rgba(30, 58, 43, 0.04), 0 14px 30px -22px rgba(30, 58, 43, 0.26);'),
    ('.cal-titolo',
     "font-family: " + _FONT_TITOLI + "; font-size: 1.02rem !important; letter-spacing: 0.01em; "
     "border-bottom: 1px solid #F0EADB; padding-bottom: 6px; margin-bottom: 8px !important;"),
    ('.cal-tab th', 'color: #9A8A62 !important; letter-spacing: 0.06em;'),
    ('.cal-tab td.cal-calore',
     'background: linear-gradient(135deg, #E8667F, #D6455F) !important; box-shadow: 0 3px 8px -3px rgba(214, 69, 95, 0.65);'),
    ('.cal-tab td.cal-stima', 'box-shadow: inset 0 0 0 1.5px #D6455F;'),
]

# Regole di sicurezza: anche con il tema scuro del telefono, testi e campi restano chiari e leggibili.
_CAMPI_TESTO = 'input:not([type="checkbox"]):not([type="radio"]):not([type="range"]) | textarea'
_REGOLE_TEMA_CHIARO = [
    ('[data-testid="stMarkdownContainer"] p | [data-testid="stMarkdownContainer"] li', 'color: #1E293B;'),
    ('[data-testid="stCaptionContainer"] p | [data-testid="stCaptionContainer"] span', 'color: #5B6A62 !important;'),
    (_CAMPI_TESTO,
     'color: #0F172A !important; -webkit-text-fill-color: #0F172A !important; background-color: #FFFFFF !important; caret-color: #0284C7;'),
    ('input::placeholder | textarea::placeholder',
     'color: #94A3B8 !important; -webkit-text-fill-color: #94A3B8 !important; opacity: 1 !important;'),
    ('[data-baseweb="input"] | [data-baseweb="base-input"] | [data-baseweb="textarea"] | [data-baseweb="select"] > div',
     'background-color: #FFFFFF !important;'),
    ('[data-baseweb="input"] svg | [data-baseweb="select"] svg | [data-testid="stNumberInput"] button',
     'color: #64748B !important; fill: #64748B !important;'),
    ('[data-baseweb="select"] *', 'color: #0F172A !important; -webkit-text-fill-color: #0F172A !important;'),
    ('[data-testid="stAlert"] p | [data-testid="stAlert"] span | [data-testid="stAlert"] li | [data-testid="stAlert"] strong | '
     '[data-testid="stAlert"] em | [data-testid="stAlert"] code | [data-testid="stAlert"] a',
     'color: #1E293B !important; -webkit-text-fill-color: #1E293B !important;'),
    ('[data-testid="stRadio"] label p | [data-testid="stCheckbox"] label p | [data-baseweb="radio"] p | [data-baseweb="checkbox"] p',
     'color: #1E293B !important;'),
    ('button[data-baseweb="tab"]', 'color: #5A6B62 !important;'),
    ('button[data-baseweb="tab"][aria-selected="true"]', 'color: #1E3A2B !important;'),
    ('[data-testid="stFileUploaderDropzone"] span | [data-testid="stFileUploaderDropzone"] small | '
     '[data-testid="stFileUploaderDropzone"] p | [data-testid="stFileUploaderDropzone"] div', 'color: #475569 !important;'),
    ('[data-testid="stFileUploaderDropzone"] button',
     'background: #FFFFFF !important; color: #1E3A2B !important; border: 1px solid #DCD5C2 !important;'),
]

st.markdown(
    "<style>\n"
    "@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&display=swap');\n"
    ".stApp { background-image: radial-gradient(1100px 520px at 88% -8%, rgba(184, 151, 90, 0.11), rgba(184, 151, 90, 0) 62%); }\n"
    + _css_area_principale([('::selection', 'background: rgba(184, 151, 90, 0.35);')])
    + "\n" + _css_area_principale(_REGOLE_GRAFICA + _REGOLE_TEMA_CHIARO) +
    "\n</style>",
    unsafe_allow_html=True
)


# ---------------------------------------------------------------------------
# CHIUSURA AUTOMATICA DELLA SIDEBAR (dopo la scelta di una sezione)
# Lo script riprova più volte e prova più selettori, così funziona anche se
# Streamlit disegna il pulsante con un po' di ritardo.
# L'utente può sempre riaprire il menù con la freccia in alto a sinistra.
# ---------------------------------------------------------------------------
# Script che chiude il menù. Contiene un codice casuale (__NONCE__) che cambia a ogni clic:
# così Streamlit lo ricarica sempre e il menù si chiude ogni volta, non solo la prima.
SCRIPT_CHIUDI_SIDEBAR = """
<script>
/* __NONCE__ */
(function () {
    var doc = window.parent.document;
    var tentativi = 0, clicks = 0, ultimoClick = 0;

    function sidebarAperta(sb) {
        var aria = sb.getAttribute('aria-expanded');
        if (aria !== null) { return aria === 'true'; }
        return sb.getBoundingClientRect().width > 60;
    }
    function trovaPulsante() {
        return doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
               doc.querySelector('button[data-testid="stSidebarCollapseButton"]') ||
               doc.querySelector('[data-testid="stSidebarHeader"] button') ||
               doc.querySelector('button[aria-label="Close sidebar"]') ||
               doc.querySelector('button[aria-label="Collapse sidebar"]');
    }
    // Restituisce true quando il menù risulta chiuso
    function passo() {
        var sb = doc.querySelector('[data-testid="stSidebar"]');
        if (!sb) { return false; }
        if (!sidebarAperta(sb)) { return true; }
        if (Date.now() - ultimoClick < 700) { return false; }   // aspetto che finisca l'animazione
        var btn = trovaPulsante();
        if (btn && clicks < 4) { btn.click(); clicks++; ultimoClick = Date.now(); }
        return false;
    }
    var timer = setInterval(function () {
        tentativi++;
        if (passo() || tentativi > 60) { clearInterval(timer); }
    }, 100);
})();
</script>
"""

if st.session_state.get("trigger_close_sidebar", False):
    st.session_state.trigger_close_sidebar = False
    components.html(SCRIPT_CHIUDI_SIDEBAR.replace("__NONCE__", uuid.uuid4().hex), height=0, width=0)

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
                        "db_peso": {},
                        "db_calori": {},
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
if "db_peso" not in user_db: user_db["db_peso"] = {}
if "db_calori" not in user_db: user_db["db_calori"] = {}
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
        
        scelta_forzata = st.session_state.pop("pet_select_forza", None)
        if scelta_forzata in lista_animali:
            st.session_state["pet_select"] = scelta_forzata
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
    if st.button("⚖️ Peso e Andamento"): cambia_sezione("peso")
    sesso_selezionato = (user_db["db_anagrafica"].get(pet_selected, {}) or {}).get("sesso") if pet_selected else None
    if sesso_selezionato == "Femmina":
        if st.button("🌸 Calore e Calendario"): cambia_sezione("calore")
    if st.button("📄 Fatture e Spese"): cambia_sezione("fatture")
    if st.button("✈️ Passaporto & Viaggi"): cambia_sezione("passaporto")
    if st.button("📘 Libretto PDF (scarica)"): cambia_sezione("pdf_libretto")
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
                    with st.expander(f"💊 {t['farmaco']} ({t['periodo']}) - ⏰ {orario_txt}", expanded=False):
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
                    with st.expander(f"🏥 {v['tipo']} - {v['data']}", expanded=False):
                        if v.get('veterinario'): st.write(f"**Veterinario:** {v['veterinario']}")
                        if v.get('vet_id_permanente'): st.caption(f"🆔 ID Medico Permanente: `{v['vet_id_permanente']}`")
                        if v.get('nome_vaccino'): st.write(f"💉 **Vaccino:** {v.get('nome_vaccino')} | **Lotto:** {v.get('lotto_vaccino', 'N/D')}")
                        mostra_immagine_salvata(v.get('etichetta_vaccino'), "🏷️ Etichetta del vaccino")
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

        with st.expander(f"⚠ Area Riservata Medico Veterinario (Registro Decesso - {pet_selected})", expanded=False):
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
                            "peso": user_db["db_peso"].pop(pet_selected, []),
                            "calori": user_db["db_calori"].pop(pet_selected, []),
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
        if st.session_state.get("foto_flash"):
            st.success(st.session_state.pop("foto_flash"))
        anagrafica_corrente = user_db["db_anagrafica"].get(pet_selected, {
            "tipo_animale": "Cane", "nome": pet_selected, "razza": "", "data_nascita": str(date.today()),
            "microchip": "", "microchip_foto": "", "segni_particolari": "", "proprietario_nome": user_db.get("nome", ""),
            "proprietario_indirizzo": "", "proprietario_telefono": user_db.get("numero_whatsapp", ""), "proprietario_citta": ""
        })

        foto_attuale = anagrafica_corrente.get("foto_animale") or ""
        blocco_foto = html_foto_animale(foto_attuale, anagrafica_corrente.get("tipo_animale"),
                                        anagrafica_corrente.get("nome") or pet_selected)
        codice_mc = (anagrafica_corrente.get('microchip') or '').strip()
        svg_mc = genera_barcode_svg(codice_mc) if codice_mc else None
        blocco_barcode = svg_in_html(svg_mc) if svg_mc else ""

        col_view1, col_view2 = st.columns(2)
        with col_view1:
            st.markdown(f"""
                <div class="wellness-card" style="border-left: 5px solid #1E3A2B !important;">
                    <div style="text-align:center;margin-bottom:12px;"><div style="display:flex;justify-content:center;margin:2px 0 16px 0;">{blocco_foto}</div><span class="card-badge badge-purple">🐾 DATI ANAGRAFICI PET</span><h3 style="color: #1E3A2B; margin-top: 5px; margin-bottom: 4px;">{anagrafica_corrente.get('nome', pet_selected)}</h3></div>
                    <p>• <strong>Specie:</strong> {anagrafica_corrente.get('tipo_animale', 'N/D')}</p>
                    <p>• <strong>Sesso:</strong> {anagrafica_corrente.get('sesso') or 'Non specificato'}</p>
                    <p>• <strong>Razza:</strong> {anagrafica_corrente.get('razza') or 'Non specificata'}</p>
                    <p>• <strong>Data Nascita:</strong> {anagrafica_corrente.get('data_nascita', 'N/D')}</p>
                    <p>• <strong>Microchip:</strong> <code>{anagrafica_corrente.get('microchip') or 'Non inserito'}</code></p>{blocco_barcode}
                    <p>• <strong>Segni Particolari:</strong> {anagrafica_corrente.get('segni_particolari') or 'Nessuno'}</p>
                </div>
            """, unsafe_allow_html=True)
            if svg_mc:
                st.download_button(
                    "⬇️ Scarica il codice a barre (immagine vettoriale SVG)",
                    data=svg_mc, file_name=f"microchip_{codice_mc}.svg", mime="image/svg+xml",
                    key=f"dl_mc_{pet_selected}"
                )
            if anagrafica_corrente.get('microchip_foto'):
                with st.expander("📷 Mostra la scansione originale dell'etichetta", expanded=False):
                    mostra_immagine_salvata(anagrafica_corrente.get('microchip_foto'))
                if not svg_mc:
                    st.info("Inserisci il numero del microchip nella modifica anagrafica per creare il codice a barre digitale.")

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

            animali_av = []
            for nome_av in lista_animali:
                ana_av = user_db["db_anagrafica"].get(nome_av, {}) or {}
                animali_av.append({
                    "nome": nome_av,
                    "foto": miniatura_foto_animale(ana_av["foto_animale"]) if ana_av.get("foto_animale") else "",
                    "emoji": EMOJI_SPECIE.get(ana_av.get("tipo_animale"), "🐾"),
                })
            if _avatar is not None:
                scelta_av = _avatar(key="avatar_animali", animali=animali_av, attivo=pet_selected, default=None)
                if scelta_av and scelta_av.get("n") != st.session_state.get("avatar_ultimo_click"):
                    st.session_state["avatar_ultimo_click"] = scelta_av.get("n")
                    if scelta_av.get("pet") in lista_animali and scelta_av.get("pet") != pet_selected:
                        seleziona_animale(scelta_av["pet"])
            else:
                st.caption("🐾 I tuoi animali: tocca il nome per aprire il suo libretto.")
                colonne_av = st.columns(max(1, min(len(lista_animali), 3)))
                for i_av, nome_av in enumerate(lista_animali):
                    if colonne_av[i_av % len(colonne_av)].button(("✅ " if nome_av == pet_selected else "") + nome_av,
                                                                 key=f"scegli_animale_{nome_av}"):
                        seleziona_animale(nome_av)

        etichetta_foto = ("🔄 Cambia" if foto_attuale else "📸 Aggiungi") + f" la foto di {pet_selected}"
        with st.expander(etichetta_foto, expanded=False):
            st.caption("La foto resterà sempre visibile nella scheda anagrafica di questo animale.")
            chiave_foto_pet = f"foto_{pet_selected}"
            nuova_foto = scegli_foto_animale(chiave_foto_pet)
            if nuova_foto:
                if st.button(f"💾 Salva la foto di {pet_selected}", key=f"salva_foto_{pet_selected}"):
                    record_foto = user_db["db_anagrafica"].setdefault(pet_selected, dict(anagrafica_corrente))
                    record_foto["foto_animale"] = nuova_foto
                    azzera_scansione(chiave_foto_pet)
                    st.session_state["foto_flash"] = f"Foto di {pet_selected} salvata."
                    salva_dati()
                    st.rerun()
            if foto_attuale:
                if st.button("🗑️ Rimuovi la foto attuale", key=f"rimuovi_foto_{pet_selected}"):
                    record_foto = user_db["db_anagrafica"].setdefault(pet_selected, dict(anagrafica_corrente))
                    record_foto["foto_animale"] = ""
                    st.session_state["foto_flash"] = f"Foto di {pet_selected} rimossa."
                    salva_dati()
                    st.rerun()

        with st.expander("✏ Modifica Anagrafica Pet e Proprietario", expanded=False):
            # --- Scansione del codice a barre del microchip (fuori dal modulo di salvataggio) ---
            chiave_mc = f"e_microchip_{pet_selected}"
            chiave_scan_mc = f"chip_edit_{pet_selected}"
            if chiave_mc not in st.session_state:
                st.session_state[chiave_mc] = anagrafica_corrente.get('microchip', '')

            foto_chip, codice_chip = scansiona_etichetta(
                chiave_scan_mc,
                "📷 Scansiona il codice a barre del microchip",
                "Fotografa l'adesivo del microchip: lo sfondo viene rimosso e l'immagine verrà mostrata nella scheda anagrafica.",
                modo_guida="barcode"
            )
            chiave_ultimo = f"ultimo_codice_{chiave_mc}"
            if codice_microchip_valido(codice_chip) and st.session_state.get(chiave_ultimo) != codice_chip:
                st.session_state[chiave_mc] = codice_chip
                st.session_state[chiave_ultimo] = codice_chip

            if anagrafica_corrente.get('microchip_foto'):
                if st.button("🗑️ Rimuovi l'immagine del microchip salvata", key=f"rm_chip_img_{pet_selected}"):
                    record = user_db["db_anagrafica"].setdefault(pet_selected, dict(anagrafica_corrente))
                    record["microchip_foto"] = ""
                    salva_dati(); st.rerun()

            st.markdown("---")

            specie_opzioni = ["Cane", "Gatto", "Coniglio", "Uccello", "Rettile", "Altro"]
            tipo_attuale = anagrafica_corrente.get('tipo_animale', 'Cane')
            idx_tipo = specie_opzioni.index(tipo_attuale) if tipo_attuale in specie_opzioni else 0
            sesso_attuale = anagrafica_corrente.get('sesso', 'Non specificato')
            idx_sesso = SESSI.index(sesso_attuale) if sesso_attuale in SESSI else 0
            try:
                data_nascita_attuale = date.fromisoformat(str(anagrafica_corrente.get('data_nascita')))
            except Exception:
                data_nascita_attuale = date.today()

            with st.form("form_edit_anagrafica"):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    e_tipo = st.selectbox("Tipo / Specie Animale*", specie_opzioni, index=idx_tipo)
                    e_sesso = st.selectbox("Sesso", SESSI, index=idx_sesso)
                    e_nome = st.text_input("Nome Animale*", value=anagrafica_corrente.get('nome', pet_selected))
                    e_razza = st.text_input("Razza", value=anagrafica_corrente.get('razza', ''))
                with col_a2:
                    e_data_nascita = st.date_input("Data di Nascita", value=data_nascita_attuale, min_value=date(2000, 1, 1), max_value=date.today())
                    e_microchip = st.text_input("Numero Microchip", key=chiave_mc, help="Con questo numero l'app crea il codice a barre digitale nella scheda anagrafica.")
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
                        microchip_foto_finale = foto_chip if foto_chip else anagrafica_corrente.get('microchip_foto', '')
                        nuovi_dati = {
                            "tipo_animale": e_tipo, "sesso": e_sesso, "nome": new_n, "razza": e_razza, "data_nascita": str(e_data_nascita),
                            "microchip": e_microchip.strip(), "microchip_foto": microchip_foto_finale,
                            "foto_animale": anagrafica_corrente.get("foto_animale", ""),
                            "segni_particolari": e_segni, "proprietario_nome": e_prop_nome,
                            "proprietario_indirizzo": e_prop_indirizzo, "proprietario_telefono": e_prop_telefono, "proprietario_citta": e_prop_citta
                        }
                        if old_n != new_n:
                            user_db["lista_animali"] = [new_n if p == old_n else p for p in user_db["lista_animali"]]
                            user_db["db_visite"][new_n] = user_db["db_visite"].pop(old_n, [])
                            user_db["db_terapie"][new_n] = user_db["db_terapie"].pop(old_n, [])
                            user_db["db_fatture"][new_n] = user_db["db_fatture"].pop(old_n, [])
                            user_db["db_peso"][new_n] = user_db["db_peso"].pop(old_n, [])
                            user_db["db_calori"][new_n] = user_db["db_calori"].pop(old_n, [])
                            user_db["db_anagrafica"].pop(old_n, None)
                            user_db["pet_selezionato"] = new_n
                        user_db["db_anagrafica"][new_n] = nuovi_dati
                        if foto_chip:
                            azzera_scansione(chiave_scan_mc)
                        salva_dati(); st.success(f"Anagrafica di {new_n} aggiornata!"); st.rerun()
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "visite":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>🏥 Visite e Clinica - {pet_selected}</h2>", unsafe_allow_html=True)

        with st.expander("➕ Aggiungi Nuova Visita Medica", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                data_visita = st.date_input("Data Visita")
                tipo_visita = st.selectbox("Tipo Visita", ["Controllo Generale", "Vaccinazione", "Visita Specialistica", "Urgenza", "Controllo Post-Operatorio"])
                veterinario = st.text_input("Medico Veterinario / Clinica")
            with col2:
                diagnosi = st.text_area("Diagnosi / Note Cliniche")
                referto = st.file_uploader("Allega Referto (Opzionale)", type=["pdf", "png", "jpg"], key="v_ref")

            nome_vaccino, lotto_vaccino, scadenza_vaccino = "", "", None
            etichetta_vaccino_b64 = ""
            if tipo_visita == "Vaccinazione":
                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1: nome_vaccino = st.text_input("Nome Vaccino*")
                with col_v2: lotto_vaccino = st.text_input("N° Lotto Vaccino*")
                with col_v3: scadenza_vaccino = st.date_input("Scadenza Vaccino")

                st.markdown("---")
                foto_vaccino, _codice_vaccino = scansiona_etichetta(
                    "vaccino",
                    "🏷️ Scansiona l'etichetta del vaccino",
                    "Fotografa l'adesivo del vaccino: lo sfondo viene rimosso e l'etichetta verrà salvata nella scheda di questa vaccinazione.",
                    modo_guida="etichetta"
                )
                etichetta_vaccino_b64 = foto_vaccino or ""
                st.markdown("---")

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
                    "scadenza_vaccino": str(scadenza_vaccino) if scadenza_vaccino else "",
                    "etichetta_vaccino": etichetta_vaccino_b64
                }
                if pet_selected not in user_db["db_visite"]: user_db["db_visite"][pet_selected] = []
                user_db["db_visite"][pet_selected].append(nuova_visita)
                azzera_scansione("vaccino")
                salva_dati(); st.success("Visita registrata con successo!"); st.rerun()

        st.markdown("### 📋 Visite e Certificati Registrati")
        visite_list = user_db["db_visite"].get(pet_selected, [])
        visite_ordinate = sorted(enumerate(visite_list), key=lambda x: x[1].get('data', ''), reverse=True)
        for idx, v in visite_ordinate:
            is_cert = v.get("certificata", False)
            with st.expander(f"🏥 {v['data']} - {v['tipo']} | {'✅ CERTIFICATA' if is_cert else '⏳ IN ATTESA DI FIRMA'}", expanded=False):
                st.write(f"**Veterinario:** Dr. {v.get('veterinario', 'N/D')}")
                if is_cert: st.success(f"🛡️ **Codice Certificato:** `{v.get('codice_certificato')}` | ID Medico: `{v.get('vet_id_permanente')}`")
                if v.get('nome_vaccino'):
                    st.write(f"💉 **Vaccino:** {v.get('nome_vaccino')} | **Lotto:** {v.get('lotto_vaccino', 'N/D')}")
                mostra_immagine_salvata(v.get('etichetta_vaccino'), "🏷️ Etichetta del vaccino")
                if v.get('diagnosi'): st.write(f"**Diagnosi:** {v['diagnosi']}")
                if v.get('referto'):
                    st.caption(f"📄 Allegato: {v['referto']}")
                mostra_pulsanti_promemoria_visita(pet_selected, v['tipo'], v['data'], v.get('veterinario', ''), v.get('diagnosi', ''))
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "terapie":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>💊 Terapie e Farmaci - {pet_selected}</h2>", unsafe_allow_html=True)
        with st.expander("🔍 Scansiona Barcode Farmaco", expanded=False):
            mostra_scansionatore_barre("📷 Lettore Codici Farmaci")

        with st.expander("➕ Nuova Terapia o Prescrizione", expanded=False):
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
            with st.expander(f"💊 {t['farmaco']} - Dose: {t['dosaggio']} ({t['periodo']})", expanded=False):
                st.write(f"**Orario:** {t.get('orario')}")
                if t.get('note'): st.write(f"**Istruzioni:** {t['note']}")
                mostra_pulsanti_promemoria_terapia(pet_selected, t['farmaco'], t['dosaggio'], t.get('orario', ''), t.get('note', ''))
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "peso":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>⚖️ Peso e Andamento - {html_escape(pet_selected)}</h2>", unsafe_allow_html=True)
        voci = user_db["db_peso"].setdefault(pet_selected, [])
        n_p = st.session_state.get("peso_cnt", 0)

        if st.session_state.get("peso_flash"):
            st.success(st.session_state.pop("peso_flash"))

        with st.expander("➕ Registra una nuova pesata", expanded=False):
            st.caption("Facoltativo: registra il peso quando vuoi, ad esempio dopo una visita. Dalla prima pesata comparirà il grafico dell'andamento.")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                data_peso = st.date_input("Data della pesata", value=date.today(), min_value=date(2000, 1, 1),
                                          max_value=date.today(), key=f"peso_data_{n_p}")
                unita_peso = st.radio("Unità di misura", ["kg", "g"], horizontal=True, key=f"peso_unita_{n_p}")
            with col_p2:
                if unita_peso == "kg":
                    valore_peso = st.number_input("Peso (kg)", min_value=0.0, max_value=250.0, value=0.0, step=0.1,
                                                  format="%.2f", key=f"peso_kg_{n_p}")
                else:
                    valore_peso = st.number_input("Peso (g)", min_value=0.0, max_value=250000.0, value=0.0, step=5.0,
                                                  format="%.0f", key=f"peso_g_{n_p}")
                nota_peso = st.text_input("Note (facoltative)", placeholder="es. dopo la visita, a digiuno...", key=f"peso_nota_{n_p}")

            if st.button("💾 Salva pesata"):
                if valore_peso <= 0:
                    st.error("Inserisci un peso maggiore di zero.")
                else:
                    peso_kg = round(valore_peso / 1000.0, 4) if unita_peso == "g" else round(valore_peso, 3)
                    esistente = next((p for p in voci if p.get("data") == str(data_peso)), None)
                    if esistente:
                        esistente["peso_kg"] = peso_kg
                        esistente["note"] = nota_peso.strip()
                        messaggio = f"Pesata del {data_peso.strftime('%d/%m/%Y')} aggiornata: {fmt_peso(peso_kg)}."
                    else:
                        voci.append({"data": str(data_peso), "peso_kg": peso_kg, "note": nota_peso.strip()})
                        messaggio = f"Pesata salvata: {fmt_peso(peso_kg)} il {data_peso.strftime('%d/%m/%Y')}."
                    st.session_state["peso_cnt"] = n_p + 1
                    st.session_state["peso_flash"] = messaggio
                    salva_dati()
                    st.rerun()

        validi = [p for p in sorted(voci, key=lambda p: str(p.get("data", "")))
                  if isinstance(p.get("peso_kg"), (int, float)) and p["peso_kg"] > 0]
        if validi:
            ultimo, primo = validi[-1], validi[0]
            precedente = validi[-2] if len(validi) >= 2 else None
            m1, m2, m3 = st.columns(3)
            m1.metric(f"Ultimo peso ({_data_it(ultimo.get('data'))})", fmt_peso(ultimo["peso_kg"]),
                      delta=fmt_variazione(ultimo["peso_kg"] - precedente["peso_kg"]) if precedente else None, delta_color="off")
            if precedente:
                m2.metric(f"Variazione dal {_data_it(primo.get('data'))}", fmt_variazione(ultimo["peso_kg"] - primo["peso_kg"]))
            m3.metric("Pesate registrate", len(validi))

            st.markdown(grafico_in_html(genera_grafico_peso_svg(validi)), unsafe_allow_html=True)
            if not precedente:
                st.caption("Registra almeno un'altra pesata per vedere l'andamento nel tempo.")
        else:
            st.info(f"Nessuna pesata registrata per {pet_selected}: inserisci il primo peso qui sopra e comparirà il grafico dell'andamento.")

        if voci:
            st.markdown("### 📋 Storico pesate")
            for idx, p in sorted(enumerate(voci), key=lambda x: str(x[1].get("data", "")), reverse=True):
                with st.expander(f"⚖️ {_data_it(p.get('data'))} - {fmt_peso(p.get('peso_kg'))}", expanded=False):
                    st.write(f"**Peso:** {fmt_peso(p.get('peso_kg'))}")
                    if p.get("note"):
                        st.write(f"**Note:** {p['note']}")
                    if st.button("🗑️ Elimina pesata", key=f"del_peso_{idx}"):
                        voci.pop(idx)
                        salva_dati()
                        st.rerun()
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "calore":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>🌸 Calore e Calendario - {html_escape(pet_selected)}</h2>", unsafe_allow_html=True)
        sesso_pet = (user_db["db_anagrafica"].get(pet_selected, {}) or {}).get("sesso")
        if sesso_pet != "Femmina":
            st.info("Questa sezione è dedicata alle femmine. Se è un errore, imposta il sesso dell'animale nella scheda Anagrafica.")
            if st.button("📋 Vai all'Anagrafica"):
                cambia_sezione("anagrafica")
        else:
            voci_c = user_db["db_calori"].setdefault(pet_selected, [])
            oggi_c = date.today()
            n_c = st.session_state.get("calore_cnt", 0)

            if st.session_state.get("calore_flash"):
                st.success(st.session_state.pop("calore_flash"))

            stat_c = statistiche_calori(voci_c, oggi_c)
            if stat_c and stat_c["in_corso"]:
                inizio_c = stat_c["in_corso"]["inizio"]
                st.info(f"🌸 Calore in corso dal {inizio_c.strftime('%d/%m/%Y')} (giorno {durata_giorni(stat_c['in_corso'])}). "
                        "Quando finisce, segnalalo qui sotto nello storico dei calori.")

            with st.expander("➕ Registra un calore", expanded=False):
                st.caption("Segna sul calendario il periodo di calore. Se è appena iniziato lascia attiva la casella «ancora in corso» e chiudilo più avanti.")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    inizio_nuovo = st.date_input("Data di inizio", value=oggi_c, min_value=date(2000, 1, 1),
                                                 max_value=oggi_c, key=f"cal_ini_{n_c}")
                    in_corso_nuovo = st.checkbox("Il calore è ancora in corso", value=True, key=f"cal_corso_{n_c}")
                with col_c2:
                    if in_corso_nuovo:
                        fine_nuovo = None
                    else:
                        fine_nuovo = st.date_input("Data di fine", value=inizio_nuovo, min_value=inizio_nuovo,
                                                   max_value=oggi_c, key=f"cal_fine_{n_c}_{inizio_nuovo.isoformat()}")
                    note_nuove = st.text_area("Note (facoltative)", placeholder="es. perdite, comportamento, accoppiamento evitato...",
                                              key=f"cal_note_{n_c}")

                if st.button("💾 Salva calore"):
                    fine_eff_nuova = fine_nuovo if fine_nuovo else max(inizio_nuovo, oggi_c)
                    sovrapposto = any(not (fine_eff_nuova < pc["inizio"] or inizio_nuovo > pc["fine_eff"])
                                      for pc in periodi_calore(voci_c, oggi_c))
                    if sovrapposto:
                        st.error("Queste date si sovrappongono a un calore già registrato. Controlla lo storico qui sotto.")
                    else:
                        voci_c.append({"inizio": str(inizio_nuovo), "fine": str(fine_nuovo) if fine_nuovo else "",
                                       "note": note_nuove.strip()})
                        st.session_state["calore_cnt"] = n_c + 1
                        st.session_state["calore_flash"] = f"Calore registrato dal {inizio_nuovo.strftime('%d/%m/%Y')}."
                        salva_dati()
                        st.rerun()

            if stat_c:
                k1, k2, k3 = st.columns(3)
                k1.metric("Calori registrati", stat_c["n"])
                k2.metric("Intervallo medio", f"{stat_c['intervallo_medio']} giorni" if stat_c["intervallo_medio"] else "—")
                k3.metric("Durata media", f"{stat_c['durata_media']} giorni" if stat_c["durata_media"] else "—")
                if stat_c["prossimo"]:
                    st.info(f"🗓️ Prossimo calore stimato intorno al {stat_c['prossimo'].strftime('%d/%m/%Y')}. "
                            "È solo una stima basata sui dati inseriti: ogni animale è diverso, confrontati con il veterinario.")
                else:
                    st.caption("Con almeno due calori registrati comparirà l'intervallo medio e una stima indicativa del prossimo.")
            else:
                st.info(f"Nessun calore registrato per {pet_selected}: usa il riquadro qui sopra per segnare il primo.")

            anni_c = {oggi_c.year}
            if stat_c:
                anni_c |= {pc["inizio"].year for pc in stat_c["periodi"]} | {pc["fine_eff"].year for pc in stat_c["periodi"]}
                if stat_c["prossimo"]:
                    anni_c.add(stat_c["prossimo"].year)
            anni_opz = sorted(anni_c)
            st.markdown("### 📅 Calendario")
            anno_sel = st.selectbox("Anno da visualizzare", anni_opz, index=anni_opz.index(oggi_c.year), key="cal_anno")
            st.markdown(genera_calendario_calori_html(anno_sel, stat_c, oggi_c), unsafe_allow_html=True)

            if stat_c:
                st.markdown("### 📋 Storico dei calori")
                for pc in sorted(stat_c["periodi"], key=lambda x: x["inizio"], reverse=True):
                    fine_txt = pc["fine"].strftime("%d/%m/%Y") if pc["fine"] else "in corso"
                    with st.expander(f"🌸 {pc['inizio'].strftime('%d/%m/%Y')} → {fine_txt} ({durata_giorni(pc)} giorni)", expanded=False):
                        st.write(f"**Durata:** {durata_giorni(pc)} giorni" + (" (finora)" if pc["in_corso"] else ""))
                        if pc["note"]:
                            st.write(f"**Note:** {pc['note']}")
                        if pc["in_corso"] and pc["inizio"] <= oggi_c:
                            if st.button("✅ Segna come terminato oggi", key=f"cal_fine_btn_{pc['idx']}"):
                                voci_c[pc["idx"]]["fine"] = str(oggi_c)
                                st.session_state["calore_flash"] = "Calore segnato come terminato oggi."
                                salva_dati()
                                st.rerun()
                        if st.button("🗑️ Elimina questo calore", key=f"cal_del_{pc['idx']}"):
                            voci_c.pop(pc["idx"])
                            salva_dati()
                            st.rerun()
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "fatture":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>📄 Fatture e Spese - {pet_selected}</h2>", unsafe_allow_html=True)
        with st.expander("➕ Carica Nuova Fattura", expanded=False):
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
            with st.expander(f"📄 €{f['importo']:.2f} - {f['categoria']} ({f['data']})", expanded=False):
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
                mostra_immagine_salvata(v.get('etichetta_vaccino'), "🏷️ Etichetta del vaccino", larghezza=320)
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
            user_db["db_peso"][sel_ang] = dati_ang.get("peso", [])
            user_db["db_calori"][sel_ang] = dati_ang.get("calori", [])
            if dati_ang.get("anagrafica"):
                user_db["db_anagrafica"][sel_ang] = dati_ang["anagrafica"]
            user_db["pet_selezionato"] = sel_ang
            salva_dati(); st.success(f"{sel_ang} è stato ripristinato!"); st.rerun()
    else:
        st.info("Nessun animale registrato nella sezione Angeli.")

elif st.session_state.sezione_attiva == "pdf_libretto":
    st.markdown("<h2 style='color: #1E3A2B;'>📘 Libretto Sanitario in PDF</h2>", unsafe_allow_html=True)
    if pet_selected:
        visite_pdf = user_db["db_visite"].get(pet_selected, [])
        n_visite = len(visite_pdf)
        n_vaccini = sum(1 for v in visite_pdf if v.get("nome_vaccino") or v.get("tipo") == "Vaccinazione")
        n_etichette = sum(1 for v in visite_pdf if v.get("etichetta_vaccino"))
        n_terapie = len(user_db["db_terapie"].get(pet_selected, []))
        n_pesate = len(user_db["db_peso"].get(pet_selected, []))
        n_fatture = len(user_db["db_fatture"].get(pet_selected, []))
        ana_pdf = user_db["db_anagrafica"].get(pet_selected, {})
        ha_microchip = bool((ana_pdf.get("microchip") or "").strip())
        n_calori = len(user_db["db_calori"].get(pet_selected, []))
        riga_calori = (f"<p>• <strong>{n_calori}</strong> calori registrati nel calendario</p>" if ana_pdf.get("sesso") == "Femmina" else "")

        st.markdown(f"""
            <div class="wellness-card" style="border-left: 5px solid #1E3A2B !important;">
                <span class="card-badge badge-green">LIBRETTO DI {html_escape(pet_selected)}</span>
                <h3 style="color: #1E3A2B; margin-top: 5px; margin-bottom: 10px;">Cosa conterrà il PDF</h3>
                <p>• <strong>Anagrafica</strong> dell'animale e del proprietario, con la <strong>foto</strong> e il <strong>codice a barre digitale del microchip</strong></p>
                <p>• <strong>{n_visite}</strong> visite mediche (di cui <strong>{n_vaccini}</strong> vaccinazioni, con <strong>{n_etichette}</strong> etichette dei vaccini)</p>
                <p>• <strong>{n_terapie}</strong> terapie e farmaci</p>
                <p>• <strong>{n_pesate}</strong> pesate, con il <strong>grafico dell'andamento del peso</strong></p>{riga_calori}
                <p>• <strong>{n_fatture}</strong> fatture e spese (facoltative)</p>
            </div>
        """, unsafe_allow_html=True)

        if not ha_microchip:
            st.info("Non hai ancora inserito il numero del microchip: nel PDF non comparirà il codice a barre. Puoi aggiungerlo dalla sezione Anagrafica.")

        includi_fatture = st.checkbox("Includi anche fatture e spese", value=True, key="pdf_includi_fatture")

        if not REPORTLAB_OK:
            st.error("Per creare il PDF serve la libreria «reportlab». Su GitHub apri il file requirements.txt, aggiungi una riga con scritto "
                     "reportlab, salva con «Commit changes» e attendi che l'app si riavvii.")
        else:
            if st.button("📄 Genera il PDF del libretto"):
                try:
                    with st.spinner("Sto creando il PDF..."):
                        dati_pdf = genera_pdf_libretto(pet_selected, user_db, includi_fatture)
                    st.session_state["pdf_libretto"] = {
                        "pet": pet_selected, "utente": user_email, "bytes": dati_pdf,
                        "ora": datetime.now().strftime("%H:%M")
                    }
                except Exception as e:
                    st.session_state.pop("pdf_libretto", None)
                    st.error(f"Non è stato possibile creare il PDF: {e}")

            pdf_pronto = st.session_state.get("pdf_libretto")
            if pdf_pronto and pdf_pronto.get("pet") == pet_selected and pdf_pronto.get("utente") == user_email:
                nome_pulito = re.sub(r"[^A-Za-z0-9_-]+", "_", pet_selected).strip("_") or "animale"
                st.success(f"✅ PDF pronto (creato alle {pdf_pronto['ora']}, {len(pdf_pronto['bytes']) // 1024} KB). Se modifichi dei dati, genera di nuovo il PDF.")
                st.download_button(
                    "⬇️ Scarica il PDF del libretto",
                    data=pdf_pronto["bytes"],
                    file_name=f"Libretto_{nome_pulito}_{date.today().isoformat()}.pdf",
                    mime="application/pdf",
                    key="dl_pdf_libretto"
                )
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "nuovo_animale":
    st.markdown("<h2 style='color: #1E3A2B;'>🐾 Registra Nuovo Animale</h2>", unsafe_allow_html=True)
    st.caption("Compila la scheda anagrafica sottostante per creare il nuovo libretto sanitario digitale.")
    
    with st.expander("📷 Scansiona il Codice a Barre del Microchip", expanded=False):
        foto_chip_n, codice_chip_n = scansiona_etichetta(
            "chip_nuovo",
            "📷 Scansiona l'adesivo del microchip",
            "Fotografa l'adesivo del libretto cartaceo: lo sfondo viene rimosso e l'immagine verrà salvata nella scheda anagrafica.",
            modo_guida="barcode"
        )
    if codice_microchip_valido(codice_chip_n) and st.session_state.get("ultimo_codice_chip_nuovo") != codice_chip_n:
        st.session_state["n_microchip"] = codice_chip_n
        st.session_state["ultimo_codice_chip_nuovo"] = codice_chip_n

    foto_nuova_b64 = None
    with st.expander("📸 Foto dell'animale (facoltativa)", expanded=False):
        foto_nuova_b64 = scegli_foto_animale("foto_nuovo")

    with st.form("form_nuovo_animale"):
        st.markdown("### 🐾 1. Dati Anagrafici dell'Animale")
        c1, c2 = st.columns(2)
        with c1:
            n_nome = st.text_input("Nome dell'Animale*", placeholder="es. Luna, Max, Baffo...")
            n_specie = st.selectbox("Specie / Tipo Animale*", ["Cane", "Gatto", "Coniglio", "Uccello", "Rettile", "Altro"])
            n_sesso = st.selectbox("Sesso*", SESSI)
            n_razza = st.text_input("Razza dell'Animale", placeholder="es. Meticcio, Labradoodle, Europeo...")
        with c2:
            n_data = st.date_input("Data di Nascita Presunta / Effettiva", value=date.today(), min_value=date(2000, 1, 1), max_value=date.today())
            n_microchip = st.text_input("Numero Microchip (15 Cifre)", key="n_microchip", placeholder="es. 380260000000000", help="Con questo numero l'app crea il codice a barre digitale nella scheda anagrafica.")
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
                    user_db["db_peso"][pet_name] = []
                    user_db["db_calori"][pet_name] = []
                user_db["db_anagrafica"][pet_name] = {
                    "tipo_animale": n_specie,
                    "sesso": n_sesso,
                    "nome": pet_name,
                    "razza": n_razza,
                    "data_nascita": str(n_data),
                    "microchip": n_microchip.strip(),
                    "microchip_foto": foto_chip_n or "",
                    "foto_animale": foto_nuova_b64 or user_db["db_anagrafica"].get(pet_name, {}).get("foto_animale", ""),
                    "segni_particolari": n_segni,
                    "proprietario_nome": n_prop_nome.strip(),
                    "proprietario_telefono": n_prop_tel.strip(),
                    "proprietario_indirizzo": n_prop_indirizzo.strip(),
                    "proprietario_citta": n_prop_citta.strip()
                }
                user_db["pet_selezionato"] = pet_name
                st.session_state.sezione_attiva = "anagrafica"
                azzera_scansione("chip_nuovo")
                azzera_scansione("foto_nuovo")
                st.session_state.pop("ultimo_codice_chip_nuovo", None)
                salva_dati()
                st.success(f"🎉 Scheda e libretto sanitario di {pet_name} creati con successo!")
                st.rerun()
            else:
                st.error("⚠️️ Inserisci almeno il Nome dell'Animale.")

else:
    st.session_state.sezione_attiva = "dashboard"
    st.rerun()
