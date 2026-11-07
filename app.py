import streamlit as st
import copy
import json
import os
import io
import base64
import urllib.parse
import hashlib
import hmac
import secrets
import smtplib
import sys
from email.message import EmailMessage
import uuid
import threading
import contextlib
import re
import math
import struct
import calendar
from datetime import datetime, date, timedelta, timezone
from html import escape as html_escape
import streamlit.components.v1 as components

import numpy as np
from PIL import Image, ImageFilter, ImageOps
import warnings as _warnings
Image.MAX_IMAGE_PIXELS = 30_000_000                       # oltre questa grandezza un'immagine è rifiutata (protegge la memoria del server)
_warnings.simplefilter("error", Image.DecompressionBombWarning)

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

# ---------------------------------------------------------------------------
# APP INSTALLABILE (PWA): pagina italiana non traducibile, icona, manifest, service worker, banner «Installa».
# I file (manifest, icone, service worker) li scrive l'app stessa in una cartella che il server pubblica:
# aggiornando app.py si aggiorna anche l'app installata sul telefono.
# ---------------------------------------------------------------------------
_JS_PWA = r"""<script>
(function () {
  var P, D;
  try { P = window.parent; D = P.document; } catch (e) { return; }
  try {
    D.documentElement.setAttribute("lang", "it");
    D.documentElement.setAttribute("translate", "no");
    D.documentElement.classList.add("notranslate");
    if (D.body) { D.body.setAttribute("translate", "no"); D.body.classList.add("notranslate"); }
    if (!D.querySelector('meta[name="google"][content="notranslate"]')) {
      var m = D.createElement("meta"); m.name = "google"; m.content = "notranslate"; D.head.appendChild(m);
    }
    var l = D.querySelector('meta[http-equiv="content-language"]');
    if (!l) { l = D.createElement("meta"); l.setAttribute("http-equiv", "content-language"); D.head.appendChild(l); }
    l.setAttribute("content", "it");
  } catch (e) {}

  if (P.__phPwa) { return; }
  P.__phPwa = true;

  try {
    var metaNamed = function (n, c) {
      var m = D.querySelector('meta[name="' + n + '"]');
      if (!m) { m = D.createElement("meta"); m.setAttribute("name", n); D.head.appendChild(m); }
      m.setAttribute("content", c);
    };
    var addLink = function (rel, href, sizes) {
      var sel = 'link[rel="' + rel + '"]' + (sizes ? '[sizes="' + sizes + '"]' : "");
      var k = D.querySelector(sel);
      if (!k) { k = D.createElement("link"); k.setAttribute("rel", rel); if (sizes) { k.setAttribute("sizes", sizes); } D.head.appendChild(k); }
      k.setAttribute("href", href);
    };
    metaNamed("theme-color", "#CFE9F8");
    metaNamed("mobile-web-app-capable", "yes");
    metaNamed("apple-mobile-web-app-capable", "yes");
    metaNamed("apple-mobile-web-app-title", "PetHealth");
    metaNamed("apple-mobile-web-app-status-bar-style", "default");
    addLink("manifest", "/manifest.webmanifest");
    addLink("apple-touch-icon", "/pwa-icons/apple-touch-icon.png", "180x180");
  } catch (e) {}

  try {
    if ("serviceWorker" in P.navigator && P.isSecureContext) {
      P.navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {});
    }
  } catch (e) {}

  /* ---- banner «Installa l'app» (solo telefoni e tablet, solo se non è già installata) ---- */
  var standalone = false, coarse = false;
  try { standalone = P.matchMedia("(display-mode: standalone)").matches || P.navigator.standalone === true; } catch (e) {}
  try { coarse = P.matchMedia("(pointer: coarse)").matches; } catch (e) {}
  if (standalone || !coarse) { return; }
  var ua = P.navigator.userAgent || "";
  var isIOS = /iPad|iPhone|iPod/.test(ua) || (P.navigator.platform === "MacIntel" && P.navigator.maxTouchPoints > 1);

  var dismissed = function () {
    try { var t = parseInt(P.localStorage.getItem("ph_install_x") || "0", 10); return t && (Date.now() - t) < 14 * 86400000; } catch (e) { return false; }
  };
  var dismiss = function () { try { P.localStorage.setItem("ph_install_x", String(Date.now())); } catch (e) {} };

  try {
    var stl = D.createElement("style");
    stl.textContent =
      "#ph-install{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));max-width:520px;margin:0 auto;" +
      "z-index:1000002;display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:18px;background:#1E3A2B;color:#fff;" +
      "border:1px solid #D9BF86;box-shadow:0 18px 44px -14px rgba(0,0,0,.55);font-family:'Plus Jakarta Sans',-apple-system,sans-serif}" +
      "#ph-install .t{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px;font-size:13px;line-height:1.35;color:#E6E3D8}" +
      "#ph-install .t b:first-child{font-size:15px;color:#fff}" +
      "#ph-install button{font:700 14px 'Plus Jakarta Sans',sans-serif;border:0;border-radius:99px;cursor:pointer}" +
      "#ph-inst-go{background:#1FA0E3;color:#fff;padding:10px 16px;min-height:40px}" +
      "#ph-inst-x{background:transparent;color:#E6E3D8;font-size:24px!important;line-height:1;padding:4px 8px}";
    D.head.appendChild(stl);
  } catch (e) {}

  var deferred = null;
  var mostra = function (modo) {
    if (dismissed() || D.getElementById("ph-install") || !D.body) { return; }
    var b = D.createElement("div");
    b.id = "ph-install"; b.setAttribute("role", "dialog"); b.setAttribute("aria-label", "Installa l'app");
    b.innerHTML = '<img src="/pwa-icons/icon-192.png" alt="" width="44" height="44" style="border-radius:11px;flex:none">' +
      '<div class="t"><b>Installa PetHealth</b><span>' +
      (modo === "ios" ? "Tocca <b>Condividi</b> (il quadrato con la freccia) e poi «<b>Aggiungi alla schermata Home</b>»."
                      : "Aprila come un'app, a schermo intero e sempre aggiornata.") +
      '</span></div>' + (modo === "ios" ? "" : '<button id="ph-inst-go" type="button">Installa</button>') +
      '<button id="ph-inst-x" type="button" aria-label="Chiudi">&times;</button>';
    D.body.appendChild(b);
    var x = D.getElementById("ph-inst-x");
    if (x) { x.addEventListener("click", function () { dismiss(); b.remove(); }); }
    var go = D.getElementById("ph-inst-go");
    if (go) {
      go.addEventListener("click", function () {
        if (!deferred) { return; }
        deferred.prompt();
        deferred.userChoice.then(function () { deferred = null; b.remove(); }).catch(function () {});
      });
    }
  };

  P.addEventListener("beforeinstallprompt", function (e) { e.preventDefault(); deferred = e; mostra("android"); });
  P.addEventListener("appinstalled", function () { var b = D.getElementById("ph-install"); if (b) { b.remove(); } });
  if (isIOS) { setTimeout(function () { mostra("ios"); }, 3000); }
})();
</script>"""
components.html(_JS_PWA, height=0, width=0)

PWA_VERSIONE = "6"
_PWA_ICONA_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAMAAADDpiTIAAABIFBMVEX9/vzz+/zj+P3g9Pvi8fjd8Pfb7/fY8fjY7/fX7vfY7PnW"
    "7PrY7PPT7/jS7vzT7vXS7fzT7fbT7PzR7P3T7PfT7PPU6/rR6/vT6/fT6/PQ7fvQ7PnQ6/zQ6/fQ6/bN7vrP7fjN7fjP7PvO7PfO"
    "7PXM7PfO6/vP6/nP6/fO6/bP6/XN6/XO6/PL6/jZ6fXV6ffU6vjT6vrT6fXS6fjS6PXS6fPQ6vrQ6vfQ6fnO6vjN6vnQ6fTO6vTT"
    "5fPM4/G8zuSQob1ba44yQmsaKlgOHVgGHGEDGmkGGl8GGGcDGGcCGWkCGWcCGWUCF2cBGGcIGGAFGGEIGFQDGGQBGGQDGF0HFWIF"
    "FWMEFWICFWIHFVsHFU8DFVYEEl8EEk8CD1ABC0iHRtM4AADohElEQVR42uydCUMay9KGIyMMwyLBAEKIZF80XkAUMUHQRBBMNCyy"
    "OoD//1989Vb1DIsbLjkn935pz8ku4tTT1VXVtTxZ/bv+X68nfx/BXwD+rr8A/F1/Afi7/gLwd/0F4O/6C8Df9ReAv+svAH/XXwD+"
    "rr8A/F1/Afi7/gLwd/0F4O/6C8Df9ReAv+svAH/XXwD+rr8A/F1/Afi7/gLwd/0F4O/6C8Df9ReAv+svAH/XXwD+rr8A/F1/Afi7"
    "/gLwd/0F4O/6C8Df9ReAv+svAH/XXwD+rr8A/F1/Afi7/gLwd/0F4F9fiauX/Xd/AfhfXLnEtWvV/kgkQvaf5nL/X1D43wYgB0Em"
    "5McoJBwNBQ3D7dYvLbdBy60boTEY+DxefwH479T0/OPqaoikTmJ3u92G26nrTm1R0xwO7Zo1RsIf+qsB/pvVPX4ZCvpFmEq6Lk+q"
    "UCzuX7mK1trd3d3yepwWC15vKDRhPfwF4L/DwqN9b4jgSei0lNgPsL7dsA7UEiS2I16vxwsIgEH0f9JOfPK/Jnva9Qaf8Z50KgO5"
    "H4yl/h3rcGKV1Br/yXdZFgwMQiGV9Hhc9JIunTCYdBv+AvBnCT8YNETd657tomx4EbsI9/y6NaQ1/SeMxPdDJkGBUEx5oFB0IxiM"
    "RtlITPwF4M8RfoxlT9LXDRG92vAidlu+jfNGg//H6jf6ssyJ1Wq1+g1rQTcohaAo2MKX0JxGKPY/ogn+uwFgLy0RhY1PgvGkiuNd"
    "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"
)
_PWA_ICONA_MASK_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAMAAADDpiTIAAABIFBMVEX9/vzz/Pzj+P3g9Pvi8fjd7/fc8fjb7fbY8fjY7/fX7vfY"
    "7PnW7PrY7PPT7/jS7vzU7vXS7fzT7fbT7PzR7P3T7PfT7PPU6/rR6/vT6/fT6/PQ7fvQ7PnQ6/zQ6/fQ6/bO7vrP7fjN7fjP7PvO"
    "7PfO7PXM7PfP6/rP6/fO6/bP6/XN6/XO6/PL6/jY6fXV6vjU6vjT6vrT6fXS6fjS6PXS6fPQ6vrQ6vfQ6fnO6vjN6vnQ6fTO6vXU"
    "5fPM4/C7zOKPoL1bbI80RG0eLVsPH1YGHGADGmkGGl8GGGcDGGcCGWkCGWcCGGkCGWUIGGEFGGEIGFUDGGQDGFwBGGYAGGEHFWIF"
    "FWMEFWICFWIHFVsDFVsFFVAEEl4EEk4DD04BC0dCUGD/AACgfklEQVR42u2dCUPa2hLHrwRCCIsUGxCkoK3WpT5QFLFFcEPBVsOi"
    "LCGA3/9bvPnPSQC31t737K29mdtrW2utMr/MdubM/JVy5F8tfzkvgQOAIw4AjjgAOOIA4IgDgCMOAI44ADjiAOCIA4AjDgCOOAA4"
    "4gDgiAOAIw4AjjgAOOIA4IgDgCMOAI44ADjiAOCIA4AjDgCOOAA44gDgiAOAIw4AjjgAOOIA4IgDgCMOAI44ADjiAOCIA4AjDgCO"
    "OAA44gDgiAOAIw4AjjgAOOIA4IgDgCMOAI44ADjiAOCIA4AjDgCOOAA44gDgiAOAIw4AjjgAOOIA4IgDgCMOAI44ADjiAOCIA4Aj"
    "DgCOOAA44gDgiAOAIw4AjjgAOOIA4IgDgCMOAI44ADjiAOCIA4AjDgCOOAA44gDgiAOAIw4AjjgAOOIA4IgDgCMOAI44ADjiAOCI"
    "A4AjDgCOOAA44gDgiAOAA4DzEjgAOOIA4IgDgCMOAI44APyLJE0/hOCX/L8DwB8tBaHuQrpYLIpf0i8KBevd9AcF8cdpB4A/T/ek"
    "3EKhmE6kixEtEvb5ZFlW7ohPUSKapsXT8RR9JMQB4A955tfxZGtaSFMVWYLIHm/G6/VncqXdLIvf78efMAj4OaRpkTigKazBSzgA"
    "vFIfT+Yctl4LhUitMmnZXyqXDw+PbDkey/hdR4eHh+XybsAvkYEIBAIaHMP6n8zAX3+q8gsbxbSmKLIsKYEtS+3Q9cnJqZAKpNFo"
    "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"
)

_PWA_SW = """// Service worker PetHealth: nessuna cache dei contenuti dell'app (si vede sempre l'ultima versione).
// Unica eccezione: la copia di sola lettura del libretto, salvata dall'app solo se l'utente la attiva, che si mostra senza internet.
const VERSIONE = "pethealth-__V__";
const CACHE_LIBRETTO = "ph-libretto";
async function paginaOffline(url) {
  try {
    if (!/[?&](libretto|animale)=/.test(url)) {
      const c = await caches.open(CACHE_LIBRETTO);
      const r = await c.match("/offline-libretto");
      if (r) { return r; }
    }
  } catch (_) {}
  return caches.match("/offline.html");
}
self.addEventListener("install", (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(VERSIONE).then((c) => c.addAll(["/offline.html", "/pwa-icons/icon-192.png"])));
});
self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) { if (k !== VERSIONE && k !== CACHE_LIBRETTO) { await caches.delete(k); } }
    await self.clients.claim();
  })());
});
self.addEventListener("push", (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { title: "PetHealth", body: e.data ? e.data.text() : "" }; }
  e.waitUntil(self.registration.showNotification(d.title || "PetHealth", {
    body: d.body || "", icon: "/pwa-icons/icon-192.png", badge: "/pwa-icons/favicon-32.png",
    tag: d.tag || "pethealth", lang: "it", data: { url: d.url || "/" },
    vibrate: [250, 120, 250], renotify: true, silent: false, timestamp: Date.now(),
  }));
});
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "/";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((lista) => {
    for (const c of lista) { if ("focus" in c) { return c.focus(); } }
    return self.clients.openWindow(url);
  }));
});
self.addEventListener("fetch", (e) => {
  if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request).then((r) => (r.status >= 500 ? paginaOffline(e.request.url).then((o) => o || r) : r))
      .catch(() => paginaOffline(e.request.url)));
  }
});
"""

_PWA_OFFLINE = """<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PetHealth · Sei offline</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#CFE9F8;color:#14291E;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;text-align:center;padding:24px;box-sizing:border-box}
.c{max-width:360px}img{width:84px;height:84px;border-radius:20px}
h1{font-family:Georgia,serif;font-weight:600;font-size:1.8rem;margin:18px 0 8px}
p{color:#2B4538;line-height:1.5;margin:0 0 22px}
button{background:#1FA0E3;color:#fff;border:0;border-radius:99px;font:700 16px sans-serif;padding:14px 26px;min-height:48px}
</style></head><body><div class="c"><img src="/pwa-icons/icon-192.png" alt="">
<h1>Sei offline</h1><p>PetHealth ha bisogno di internet per mostrare il libretto del tuo animale. Controlla la connessione e riprova.<br><br>Per vederlo anche senza internet, attiva «Libretto senza internet» in Menù → App e notifiche (basta farlo una volta, con la connessione attiva).</p>
<button onclick="location.reload()">Riprova</button></div></body></html>"""

def _cartella_pwa():
    for base in ("/var/lib/pethealth-pwa", os.path.join(os.getcwd(), "pwa")):
        try:
            os.makedirs(base, exist_ok=True)
            if os.access(base, os.W_OK):
                return base
        except Exception:
            continue
    return None

def prepara_file_pwa():
    """Scrive manifest, service worker, icone e pagina offline (solo se la versione è cambiata)."""
    try:
        cart = _cartella_pwa()
        if not cart:
            return
        marcatore = os.path.join(cart, "versione.txt")
        if os.path.exists(marcatore):
            with open(marcatore, "r", encoding="utf-8") as f:
                if f.read().strip() == PWA_VERSIONE:
                    return

        def scrivi(percorso, dati):
            os.makedirs(os.path.dirname(percorso), exist_ok=True)
            tmp = percorso + ".tmp"
            with open(tmp, "wb") as f:
                f.write(dati if isinstance(dati, bytes) else dati.encode("utf-8"))
            os.replace(tmp, percorso)

        master = Image.open(io.BytesIO(base64.b64decode(_PWA_ICONA_B64))).convert("RGB")
        def png(lato):
            buf = io.BytesIO()
            master.resize((lato, lato), Image.LANCZOS).save(buf, format="PNG", optimize=True)
            return buf.getvalue()
        for nome, lato in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180), ("favicon-32.png", 32)):
            scrivi(os.path.join(cart, "pwa-icons", nome), png(lato))
        # versione «maskable» (Android ritaglia l'icona in cerchio/quadrato arrotondato): il logo è più piccolo, così non viene tagliato
        master_m = Image.open(io.BytesIO(base64.b64decode(_PWA_ICONA_MASK_B64))).convert("RGB")
        for nome, lato in (("icon-maskable-192.png", 192), ("icon-maskable-512.png", 512)):
            buf_m = io.BytesIO(); master_m.resize((lato, lato), Image.LANCZOS).save(buf_m, format="PNG", optimize=True)
            scrivi(os.path.join(cart, "pwa-icons", nome), buf_m.getvalue())

        manifest = {
            "id": "/", "name": "PetHealth – Wellness & Care", "short_name": "PetHealth",
            "description": "Il libretto sanitario digitale del tuo animale: vaccini, terapie, peso e promemoria.",
            "lang": "it", "dir": "ltr", "start_url": "/", "scope": "/", "display": "standalone",
            "background_color": "#D0EBF7", "theme_color": "#D0EBF7", "categories": ["health", "lifestyle"],
            "icons": [
                {"src": "/pwa-icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                {"src": "/pwa-icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                {"src": "/pwa-icons/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
                {"src": "/pwa-icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
            ],
        }
        scrivi(os.path.join(cart, "manifest.webmanifest"), json.dumps(manifest, ensure_ascii=False, indent=2))
        scrivi(os.path.join(cart, "sw.js"), _PWA_SW.replace("__V__", "v" + PWA_VERSIONE))
        scrivi(os.path.join(cart, "offline.html"), _PWA_OFFLINE)
        scrivi(marcatore, PWA_VERSIONE)
    except Exception:
        pass

prepara_file_pwa()

# --------------------------- LIBRETTO SENZA INTERNET ---------------------------
# Copia di SOLA LETTURA del libretto, salvata nel dispositivo (Cache API) solo se l'utente la attiva su quel dispositivo.
# Il service worker la mostra quando manca la connessione. Viene cancellata a ogni uscita dall'account.
JS_OFFLINE_PULISCI = ("<script>(function(){var w=window.parent||window;try{(w.caches||caches).delete('ph-libretto');}catch(e){}"
                      "try{w.localStorage.removeItem('ph_off_hash');}catch(e){}"
                      "try{w.document.cookie='ph_offline=; Max-Age=0; Path=/; Secure; SameSite=Lax';}catch(e){}})();</script>")

def offline_attivo():
    """True se su QUESTO dispositivo l'utente ha attivato il libretto senza internet (cookie letto a inizio sessione)."""
    ov = st.session_state.get("off_stato")
    if ov is not None:
        return bool(ov)
    try:
        return st.context.cookies.get("ph_offline") == "1"
    except Exception:
        return False

def js_offline_cookie(attivo):
    val = "ph_offline=1; Max-Age=31536000; Path=/; Secure; SameSite=Lax" if attivo else "ph_offline=; Max-Age=0; Path=/; Secure; SameSite=Lax"
    return "<script>try{(window.parent||window).document.cookie=" + json.dumps(val) + ";}catch(e){}</script>"

def telefono_per_chiamata(grezzo):
    """Numero pulito per il collegamento «tel:» (solo cifre ed eventuale + iniziale). Stringa vuota se non sembra un numero."""
    s = str(grezzo or "").strip()
    cifre = re.sub(r"\D", "", s)
    if not (6 <= len(cifre) <= 15):
        return ""
    return ("+" if s.startswith("+") else "") + cifre

def clinica_fiducia(user_db):
    c = (user_db.get("clinica_fiducia") or {}) if isinstance(user_db, dict) else {}
    return c if isinstance(c, dict) and (c.get("nome") or c.get("telefono")) else {}

def html_pulsante_chiama(telefono, grande=True):
    tel = telefono_per_chiamata(telefono)
    if not tel:
        return ""
    return (f'<a href="tel:{html_escape(tel)}" style="display:inline-flex;align-items:center;gap:8px;background:#1FA0E3;color:#fff !important;'
            f'-webkit-text-fill-color:#fff;padding:{"14px 24px" if grande else "10px 18px"};min-height:48px;border-radius:99px;text-decoration:none !important;font-weight:700;'
            f'font-size:1.05rem;margin:6px 8px 6px 0;box-sizing:border-box">📞 Chiama {html_escape(str(telefono).strip())}</a>')

def html_libretto_offline(user_db):
    """Pagina HTML autonoma (niente file esterni) con il libretto di tutti gli animali dell'account, in sola lettura."""
    e = lambda v: html_escape("" if v is None else str(v))
    def riga(titolo, valore):
        return f"<p><b>{e(titolo)}:</b> {e(valore)}</p>" if valore not in (None, "", "—") else ""
    blocchi = []
    for n, pet in enumerate(user_db.get("lista_animali") or []):
        ana = (user_db.get("db_anagrafica") or {}).get(pet, {}) or {}
        parti = [f"<details{' open' if n == 0 else ''}><summary>{e(pet)}</summary><div class='sez'>"]
        parti.append("<h3>Anagrafica</h3>" + (
            riga("Specie", ana.get("tipo_animale")) + riga("Razza", ana.get("razza")) + riga("Sesso", ana.get("sesso"))
            + riga("Nato il", data_ui(ana.get("data_nascita")) if ana.get("data_nascita") else "") + riga("Microchip", ana.get("microchip"))
            + riga("Segni particolari", ana.get("segni_particolari")) or "<p class='v'>Nessun dato.</p>"))
        visite = sorted((user_db.get("db_visite") or {}).get(pet, []), key=lambda v: str(v.get("data", "")), reverse=True)
        richiami = [v for v in visite if richiamo_attivo(v) and str(v.get("prossimo_controllo_data"))[:10] >= date.today().isoformat()]
        if richiami:
            parti.append("<h3>Richiami in programma</h3><ul>" + "".join(
                f"<li><b>{e(data_ui(v.get('prossimo_controllo_data')))}</b> · {e(descrizione_richiamo(v))}</li>" for v in sorted(richiami, key=lambda v: str(v.get("prossimo_controllo_data")))) + "</ul>")
        parti.append("<h3>Visite e vaccini</h3>")
        voci = []
        for v in visite:
            extra = []
            if v.get("nome_vaccino"):
                extra.append("vaccino " + e(v["nome_vaccino"]) + (f", lotto {e(v['lotto_vaccino'])}" if v.get("lotto_vaccino") else "")
                             + (f", scade {e(data_ui(v['scadenza_vaccino']))}" if v.get("scadenza_vaccino") else ""))
            voci.append(f"<li><b>{e(data_ui(v.get('data', '')))}</b> · {e(v.get('tipo', ''))} · {e(v.get('veterinario', '') or '—')}"
                        + (" · " + "; ".join(extra) if extra else "")
                        + (f"<br><span class='v'>{e(v['diagnosi'])}</span>" if v.get("diagnosi") else "") + "</li>")
        parti.append("<ul>" + "".join(voci) + "</ul>" if voci else "<p class='v'>Nessuna visita registrata.</p>")
        parti.append("<h3>Terapie</h3>")
        voci = []
        for t in sorted((user_db.get("db_terapie") or {}).get(pet, []), key=lambda t: str(t.get("data_inizio", "")), reverse=True):
            dett = [t.get("dosaggio", ""), ", ".join(orari_terapia(t)), t.get("periodo", ""), descrizione_pasto(t)]
            voci.append(f"<li><b>{e(t.get('farmaco', ''))}</b> · " + " · ".join(e(x) for x in dett if x)
                        + (f" · ricetta elettronica n. {e(t['rev_numero'])}" if t.get("rev_numero") else "")
                        + (f"<br><span class='v'>{e(t['note'])}</span>" if t.get("note") else "") + "</li>")
        parti.append("<ul>" + "".join(voci) + "</ul>" if voci else "<p class='v'>Nessuna terapia registrata.</p>")
        parti.append("<h3>Peso</h3>")
        pesi = sorted((user_db.get("db_peso") or {}).get(pet, []), key=lambda p: str(p.get("data", "")), reverse=True)[:15]
        parti.append("<ul>" + "".join(f"<li>{e(data_ui(p.get('data', '')))}: <b>{e(fmt_peso(p.get('peso_kg')))}</b></li>" for p in pesi) + "</ul>"
                     if pesi else "<p class='v'>Nessuna pesata.</p>")
        parti.append("</div></details>")
        blocchi.append("".join(parti))
    corpo = "".join(blocchi) or "<p>Non c'è ancora nessun animale nel libretto.</p>"
    _cl = clinica_fiducia(user_db)
    if _cl:
        corpo = ("<details open><summary>🏥 La mia clinica di fiducia</summary><div class='sez'>"
                 + (f"<p><b>{e(_cl.get('nome'))}</b></p>" if _cl.get("nome") else "")
                 + (f"<p>{e(_cl.get('via'))}</p>" if _cl.get("via") else "")
                 + (f"<p style='margin-top:10px'>{html_pulsante_chiama(_cl.get('telefono'), False)}</p>" if telefono_per_chiamata(_cl.get("telefono")) else "")
                 + "</div></details>") + corpo
    return ('<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>PetHealth · Libretto offline</title><style>'
            'body{margin:0;background:#CFE9F8;color:#14291E;font:16px/1.5 Helvetica,"Helvetica Neue",Arial,"Liberation Sans",sans-serif;padding:0 16px 40px}'
            '.top{max-width:720px;margin:0 auto}h1{font:700 1.6rem/1.2 Helvetica,"Helvetica Neue",Arial,"Liberation Sans",sans-serif;margin:22px 0 6px}'
            '.avv{background:#FFF7DD;border:1px solid #E6C766;border-radius:12px;padding:12px 14px;margin:12px 0 18px;font-size:.95rem}'
            'details{background:#fff;border-radius:14px;margin:0 0 12px;padding:4px 16px;box-shadow:0 1px 3px rgba(20,41,30,.12)}'
            'summary{font-weight:700;font-size:1.2rem;padding:12px 0;cursor:pointer}h3{font-size:1rem;color:#0369A1;margin:18px 0 6px}'
            'p{margin:3px 0}ul{margin:0;padding-left:20px}li{margin:0 0 8px}.v{color:#2B4538;font-size:.92rem}'
            'button{background:#1FA0E3;color:#fff;border:0;border-radius:99px;font:700 16px Helvetica,"Helvetica Neue",Arial,"Liberation Sans",sans-serif;padding:13px 24px;min-height:48px;margin-top:6px}'
            '.sez{padding-bottom:12px}</style></head><body><div class="top"><h1>🩺 Libretto sanitario</h1>'
            '<div class="avv"><b>Sei offline.</b> Questa è una copia di sola lettura, salvata il __AGG__. '
            'Non puoi modificare nulla finché non torna la connessione.</div>' + corpo +
            '<button onclick="location.reload()">Riprova a connetterti</button>'
            '<p class="v" style="margin-top:18px">Le informazioni sono inserite dal proprietario. '
            'Non sostituiscono la cartella clinica.</p></div></body></html>')

def js_offline_salva(html, hash_):
    """Salva (o aggiorna) la copia nel dispositivo. Scrive solo se il contenuto è cambiato."""
    return ("<script>(function(){var w=window.parent||window;var H=" + json.dumps(hash_) + ";var P=" + json.dumps(html).replace("</", "<\\/") + ";"
            "try{if(w.localStorage.getItem('ph_off_hash')===H){return;}}catch(e){}"
            "var agg=new Date().toLocaleString('it-IT',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});"
            "var corpo=P.replace('__AGG__',agg);var C=(w.caches||window.caches);if(!C){return;}"
            "C.open('ph-libretto').then(function(c){return c.put('/offline-libretto',new Response(corpo,{headers:{'Content-Type':'text/html; charset=utf-8'}}));})"
            ".then(function(){try{w.localStorage.setItem('ph_off_hash',H);}catch(e){}}).catch(function(){});})();</script>")

def allinea_offline_account(login_email):
    """La scelta «libretto senza internet» vale per l'account: attivata da un dispositivo, si attiva da sola
    su ogni altro dispositivo dove l'utente accede (e si spegne ovunque se la disattiva). Non serve nessun permesso."""
    try:
        if login_email == "demo@pethealth.it":
            return
        u = st.session_state.db_users.get(login_email)
        if not isinstance(u, dict):
            return
        pref = (u.get("preferenze") or {}).get("offline")
        qui = offline_attivo()
        if pref is None:
            if qui:                                    # chi l'aveva già attivata prima: la ricordo per l'account
                u.setdefault("preferenze", {})["offline"] = True
                salva_dati()
        elif pref and not qui:
            st.session_state["off_stato"] = True
            st.session_state.pop("off_ultimo_hash", None)
            components.html(js_offline_cookie(True), height=0, width=0)
        elif pref is False and qui:
            st.session_state["off_stato"] = False
            st.session_state.pop("off_ultimo_hash", None)
            components.html(js_offline_cookie(False) + JS_OFFLINE_PULISCI, height=0, width=0)
    except Exception:
        pass

def sincronizza_offline(user_db):
    """Se l'utente ha attivato la funzione su questo dispositivo, tiene aggiornata la copia del libretto."""
    if not offline_attivo():
        return
    try:
        html = html_libretto_offline(user_db)
        h = hashlib.sha256(html.encode("utf-8")).hexdigest()[:20]
        if st.session_state.get("off_ultimo_hash") != h:
            components.html(js_offline_salva(html, h), height=0, width=0)
            st.session_state["off_ultimo_hash"] = h
    except Exception:
        pass

# Accesso che resta attivo su questo dispositivo: il cookie viene scritto/cancellato dopo il login o il logout.
_canc_ck = st.session_state.pop("ph_cookie_cancella", False)
if _canc_ck:
    st.session_state.pop("ph_cookie_ripeti", None)
    st.session_state.pop("ph_cookie_scrivi", None)
if st.session_state.get("ph_cookie_scrivi"):
    st.session_state["ph_cookie_ripeti"] = (st.session_state.pop("ph_cookie_scrivi"), 4)
_rip_ck = st.session_state.get("ph_cookie_ripeti")
if _rip_ck:
    _tok_ck, _n_ck = _rip_ck
    _ck_js = json.dumps(f"ph_sess={_tok_ck}; Max-Age={30 * 86400}; Path=/; Secure; SameSite=Lax")
    components.html("<script>try{window.parent.document.cookie=" + _ck_js + ";}catch(e){try{document.cookie=" + _ck_js + ";}catch(e2){}}</script>", height=0, width=0)
    st.session_state["ph_cookie_ripeti"] = (_tok_ck, _n_ck - 1) if _n_ck > 1 else None
if _canc_ck:
    components.html("<script>try{window.parent.document.cookie='ph_sess=; Max-Age=0; Path=/; Secure; SameSite=Lax';}catch(e){}</script>", height=0, width=0)
    components.html(JS_OFFLINE_PULISCI, height=0, width=0)
    st.session_state.pop("off_ultimo_hash", None)
    st.session_state["off_stato"] = False

DATA_FILE = "data_pethealth.json"

ITERAZIONI_PASSWORD = 600_000          # valore consigliato oggi per PBKDF2-SHA256 (le password vecchie si aggiornano da sole al primo accesso)

def hash_password(password, salt=None, iterazioni=None):
    """Hash PBKDF2-SHA256 con sale casuale (formato pbkdf2s$iterazioni$sale$hash). Mai la password in chiaro."""
    salt = salt or secrets.token_hex(16)
    it = int(iterazioni or ITERAZIONI_PASSWORD)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), it).hex()
    return f"pbkdf2s${it}${salt}${h}"

def password_da_aggiornare(memorizzato):
    """True se l'impronta salvata è di un formato più vecchio o con meno iterazioni di quelle attuali."""
    m = str(memorizzato or "")
    if not m.startswith("pbkdf2s$"):
        return True
    try:
        return int(m.split("$")[1]) < ITERAZIONI_PASSWORD
    except Exception:
        return True

def verifica_password(password, memorizzato):
    """Controlla la password. Accetta anche i formati vecchi (pbkdf2 a 200.000 giri e SHA-256 semplice)."""
    memorizzato = memorizzato or ""
    password = password or ""
    if memorizzato.startswith("pbkdf2s$"):
        try:
            _, it, salt, _h = memorizzato.split("$", 3)
            return hmac.compare_digest(hash_password(password, salt, int(it)), memorizzato)
        except Exception:
            return False
    if memorizzato.startswith("pbkdf2$"):
        try:
            _, salt, h_vecchio = memorizzato.split("$", 2)
        except ValueError:
            return False
        calcolato = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000).hex()
        return hmac.compare_digest(calcolato, h_vecchio)
    vecchio = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(vecchio, memorizzato)

_PASSWORD_BANALI = {
    "password", "password1", "password12", "password123", "password1234", "passw0rd", "12345678", "123456789", "1234567890", "12345678910",
    "qwertyuiop", "qwerty123", "qwertyuiop1", "asdfghjkl", "asdfghjkl1", "iloveyou", "letmein123", "welcome123", "admin12345", "abcd123456",
    "0123456789", "1q2w3e4r5t", "1qaz2wsx3e", "pethealth", "pethealth1", "pethealth123", "veterinario", "veterinario1", "cane123456", "gatto12345",
    "ciao123456", "benvenuto1", "juventus1", "milan12345", "inter123456", "napoli1926", "forzaroma1", "password!", "password2024", "password2025", "password2026",
}

@st.cache_resource(show_spinner=False)
def _cache_password_violate():
    return {}

def password_violata(password):
    """True se la password compare in fughe di dati pubbliche. Si invia solo un frammento (5 caratteri) dell'impronta SHA-1: il servizio non
    può risalire alla password. Se il servizio non risponde, il controllo viene saltato (non si blocca mai la registrazione)."""
    try:
        sha = hashlib.sha1(str(password).encode("utf-8")).hexdigest().upper()
        pre, suf = sha[:5], sha[5:]
        cache = _cache_password_violate().setdefault("hibp", {})
        if pre not in cache:
            import urllib.request
            rich = urllib.request.Request("https://api.pwnedpasswords.com/range/" + pre, headers={"User-Agent": "PetHealth", "Add-Padding": "true"})
            with urllib.request.urlopen(rich, timeout=3) as r:
                cache[pre] = r.read().decode("utf-8", "ignore")
            if len(cache) > 500:
                cache.pop(next(iter(cache)))
        for riga in cache[pre].splitlines():
            h, _, n = riga.partition(":")
            if h.strip() == suf and int(n.strip() or 0) > 0:
                return True
    except Exception:
        return False
    return False

def controlla_password_nuova(password, email=""):
    """Restituisce il messaggio d'errore se la password scelta è troppo debole, altrimenti None."""
    p = password or ""
    if len(p) < 10:
        return "La password deve avere almeno 10 caratteri."
    if len(p) > 200:
        return "La password è troppo lunga (massimo 200 caratteri)."
    b = p.lower()
    if b in _PASSWORD_BANALI or len(set(b)) < 5:
        return "Questa password è troppo semplice o troppo comune: scegline un'altra (meglio una frase facile da ricordare)."
    if p.isdigit():
        return "Una password di sole cifre è facile da indovinare: aggiungi lettere."
    loc = str(email or "").split("@")[0].lower()
    if len(loc) >= 4 and loc in b:
        return "La password non deve contenere il tuo indirizzo email."
    if password_violata(p):
        return "Questa password è già finita in fughe di dati pubbliche: gli hacker la provano per prima. Scegline un'altra (meglio una frase lunga)."
    return None

@st.cache_resource(show_spinner=False)
def _memoria_archivio():
    return {"chiave": None, "dati": None, "lock": threading.Lock()}

def carica_dati():
    """Carica i dati del database da file JSON locale se esistente.
    L'archivio viene riletto solo quando il file cambia (all'interno di un singolo clic viene letto più volte)."""
    if os.path.exists(DATA_FILE):
        try:
            try:
                mem = _memoria_archivio()
                if not isinstance(mem, dict) or "lock" not in mem or "chiave" not in mem:
                    mem = None
            except Exception:
                mem = None
            if mem is not None:
                stt = os.stat(DATA_FILE)
                chiave = (os.path.abspath(DATA_FILE), stt.st_mtime_ns, stt.st_size, stt.st_ino)
                with mem["lock"]:
                    if mem["chiave"] == chiave and mem["dati"] is not None:
                        return copy.deepcopy(mem["dati"])
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    dati = json.load(f)
                with mem["lock"]:
                    mem["chiave"], mem["dati"] = chiave, dati
                return copy.deepcopy(dati)
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def _email_mie():
    """Gli account che QUESTA sessione ha il diritto di scrivere: quello collegato e quello in attivazione."""
    return {e for e in (st.session_state.get("logged_user_email"), st.session_state.get("account_attivo"),
                        st.session_state.get("verification_pending_email")) if e}

def aggiorna_altri_utenti_da_disco():
    """Porta in sessione gli account degli altri utenti, così la sessione non lavora su copie vecchie."""
    su_disco = carica_dati() or {}
    mie = _email_mie()
    utenti = st.session_state.setdefault("db_users", {})
    for email, dati_utente in (su_disco.get("users", {}) or {}).items():
        if email not in mie:
            utenti[email] = dati_utente
    for sigla in (su_disco.get("eliminati", {}) or {}):
        for email in [e for e in utenti if e not in mie and sigla_email(e) == sigla]:
            utenti.pop(email, None)
    vet = st.session_state.setdefault("db_veterinari", {})
    for k, v in (su_disco.get("db_veterinari", {}) or {}).items():
        vet[k] = v

def sigla_email(email):
    """Impronta dell'email (non reversibile): serve solo a ricordare che un account è stato eliminato."""
    return hashlib.sha256(str(email).strip().lower().encode("utf-8")).hexdigest()[:24]

@st.cache_resource(show_spinner=False)
def _lock_globale():
    return threading.RLock()

def _lock_disco():
    """Un solo salvataggio alla volta in tutto il programma (più persone possono usare l'app insieme)."""
    try:
        blocco = _lock_globale()
        return blocco if hasattr(blocco, "__enter__") else contextlib.nullcontext()
    except Exception:
        return contextlib.nullcontext()

def _scrivi_archivio(dati):
    tmp = DATA_FILE + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)      # file riservato: lo legge solo l'utente dell'app
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

def salva_dati(extra_email=None):
    with _lock_disco():
        return _salva_dati_interno(extra_email)

def _salva_dati_interno(extra_email=None):
    """SALVATAGGIO SICURO: rilegge l'archivio più recente e sovrascrive soltanto l'account di chi sta lavorando.
    Così due persone che usano l'app nello stesso momento non cancellano più i dati l'una dell'altra."""
    mie = _email_mie()
    if extra_email:
        mie.add(extra_email)
    su_disco = carica_dati() or {}
    utenti = dict(su_disco.get("users", {}) or {})
    eliminati = dict(su_disco.get("eliminati", {}) or {})
    sessione = st.session_state.get("db_users", {})
    for email in mie:
        if email in sessione and sigla_email(email) not in eliminati:   # un account eliminato non risorge da una sessione vecchia
            nuovo = sessione[email]
            if email in utenti:                                       # i dispositivi collegati si cambiano solo con _aggiorna_sessioni
                nuovo = dict(nuovo)
                nuovo["sessioni_dispositivo"] = (utenti[email].get("sessioni_dispositivo") or {})
            utenti[email] = nuovo
    vet = dict(su_disco.get("db_veterinari", {}) or {})
    vet.update(st.session_state.get("db_veterinari", {}))
    # Richieste di firma: lo stato più avanzato vince (una conferma non torna mai "in attesa")
    ordine = {"in_attesa": 0, "annullata": 1, "rifiutata": 2, "confermata": 3}
    richieste = dict(su_disco.get("richieste_firma", {}) or {})
    for token, r in st.session_state.get("richieste_firma", {}).items():
        if sigla_email(r.get("email_owner", "")) in eliminati:
            continue
        d = richieste.get(token)
        if d is None or ordine.get(r.get("stato"), 0) >= ordine.get(d.get("stato"), 0):
            richieste[token] = r
    chiave_sig = su_disco.get("chiave_sigillo") or st.session_state.get("chiave_sigillo")
    dati = {"users": utenti, "db_veterinari": vet, "richieste_firma": richieste, "chiave_sigillo": chiave_sig, "eliminati": eliminati}
    try:
        _scrivi_archivio(dati)
    except Exception as e:
        print(f"[PetHealth] errore di salvataggio: {e!r}", file=sys.stderr)      # il dettaglio resta nel registro del server, non sullo schermo
        st.error("Non siamo riusciti a salvare i dati. Riprova tra un momento; se succede ancora scrivi all'assistenza.")
        return
    for email, dati_utente in utenti.items():
        if email not in mie:
            sessione[email] = dati_utente
    st.session_state["richieste_firma"] = richieste
    st.session_state["chiave_sigillo"] = chiave_sig

if "db_users" not in st.session_state or "db_veterinari" not in st.session_state:
    dati_salvati = carica_dati()
    if dati_salvati and "users" in dati_salvati:
        st.session_state.db_users = dati_salvati.get("users", {})
        st.session_state.db_veterinari = dati_salvati.get("db_veterinari", {})
    else:
        st.session_state.db_users = {}
        st.session_state.db_veterinari = {}
        salva_dati()

_d_iniz = carica_dati() or {}
st.session_state.setdefault("richieste_firma", dict(_d_iniz.get("richieste_firma", {}) or {}))
st.session_state.setdefault("chiave_sigillo", _d_iniz.get("chiave_sigillo"))

if "logged_user_email" not in st.session_state:
    st.session_state.logged_user_email = None

if "sezione_attiva" not in st.session_state:
    st.session_state.sezione_attiva = "dashboard"

if "verification_pending_email" not in st.session_state:
    st.session_state.verification_pending_email = None

_SOTTO_IMPOSTAZIONI = (
    ("condividi", "🔗 Condivisione e QR"),
    ("installa", "📲 App e notifiche"),
    ("privacy", "🔐 Account, privacy e aiuto"),
)
if st.session_state.get("sezione_attiva") in ("condividi", "installa", "privacy"):
    st.session_state["impost_sub"] = st.session_state.sezione_attiva
    st.session_state.sezione_attiva = "impostazioni"
if st.session_state.get("impost_sub") not in ("condividi", "installa", "privacy"):
    st.session_state["impost_sub"] = "condividi"

def nome_proprio(nome_completo):
    """Il primo nome dell'utente (senza cognome); vuoto se il nome non c'è o è un indirizzo email."""
    n = str(nome_completo or "").strip()
    if not n or "@" in n:
        return ""
    return n.split()[0]

def testo_messaggio_angelo(nome_completo):
    p = nome_proprio(nome_completo)
    corpo = ("per quanto doloroso in questo momento ricorda sempre che i nostri amici a 4 zampe non ci abbandonano mai veramente, "
             "ma ci proteggono da lassù e anche se noi non li vediamo loro ci sono, chi portiamo nel nostro cuore per davvero "
             "non ci abbandona mai veramente.")
    return f"{p}, {corpo}" if p else corpo[0].upper() + corpo[1:]

def registra_messaggio_angelo(pet, nome_completo):
    """Dopo la registrazione del decesso: porta l'utente in «I nostri angeli a 4 zampe» con il messaggio di vicinanza."""
    st.session_state["messaggio_angelo"] = {"pet": pet, "testo": testo_messaggio_angelo(nome_completo)}
    st.session_state.sezione_attiva = "angeli"
    st.rerun()

def mostra_messaggio_angelo():
    m = st.session_state.pop("messaggio_angelo", None)
    if not m:
        return
    st.markdown(
        '<div class="wellness-card" style="border-left:5px solid #B8975A !important;text-align:center">'
        '<div style="font-size:2.2rem;line-height:1">🌈</div>'
        f'<p style="margin:10px 0 4px 0"><b>{html_escape(str(m.get("pet", "")))}</b> è ora nel Registro degli Angeli.</p>'
        f'<p style="font-size:1.08rem;line-height:1.6;margin:8px 0 2px 0">{html_escape(str(m.get("testo", "")))}</p></div>',
        unsafe_allow_html=True)

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
  button { flex: 1; min-width: 110px; border: none; border-radius: 10px; padding: 12px 14px; font-size: 15px; font-weight: 700; cursor: pointer; color: #fff; background: #1FA0E3; }
  button.sec { background: #1FA0E3; }
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
  button { flex: 1; min-width: 130px; border: none; border-radius: 10px; padding: 11px 12px; font-size: 14px; font-weight: 700; cursor: pointer; color: #fff; background: #1FA0E3; }
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
    """Crea (se serve) la cartella del componente e lo registra in Streamlit.
    Prova più posizioni: sul server il servizio può scrivere solo nella sua cartella dati."""
    import tempfile
    basi = [os.path.dirname(os.path.abspath(__file__)), os.getcwd(),
            os.path.join(tempfile.gettempdir(), "pethealth_componenti"),
            os.path.join(os.path.expanduser("~"), ".pethealth_componenti")]
    ultimo_errore = None
    for base in basi:
        try:
            cartella = os.path.join(base, sottocartella)
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
        except Exception as e:
            ultimo_errore = e
    raise ultimo_errore

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
    utente_corrente = st.session_state.db_users[st.session_state.get("account_attivo") or st.session_state.logged_user_email]
    utente_corrente["pet_selezionato"] = nome
    st.session_state["pet_select_forza"] = nome      # la barra laterale lo applica al prossimo ciclo
    salva_dati()
    st.rerun()


def azzera_scansione(chiave):
    """Svuota il riquadro di scansione e chiude la relativa scheda (da chiamare dopo il salvataggio)."""
    k = f"scan_cnt_{chiave}"
    st.session_state[k] = st.session_state.get(k, 0) + 1
    chiudi_scheda(chiave)

def chiudi_scheda(chiave):
    st.session_state.pop(f"scheda_aperta_{chiave}", None)

def scheda_a_comparsa(chiave, titolo):
    """Scheda che si apre con un tocco e RESTA aperta finché l'utente non la richiude o non salva.
    Al posto dell'expander: su Android, mentre si usa la fotocamera, la pagina si ricarica e l'expander tornava chiuso."""
    k = f"scheda_aperta_{chiave}"
    aperta = bool(st.session_state.get(k, False))
    if st.button(("🔽 " if aperta else "▶️ ") + titolo, key=f"scheda_btn_{chiave}", use_container_width=True):
        st.session_state[k] = not aperta
        st.rerun()
    return aperta

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

def data_ui(valore):
    """Data da mostrare a schermo: 2024-03-05 -> 05/03/2024 (se non è una data, resta com'è)."""
    try:
        return date.fromisoformat(str(valore)[:10]).strftime("%d/%m/%Y")
    except Exception:
        return "" if valore is None else str(valore)

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
            ])
        storia.append(tabella_elenco(["Data", "Vaccino", "Lotto", "Scadenza"], righe_vac,
                                     [2.6 * cm, W - 2.6 * cm - 3.2 * cm - 2.6 * cm, 3.2 * cm, 2.6 * cm]))
        storia.append(Spacer(1, 10))

    if visite:
        sottotitolo("Dettaglio delle visite")
        for v in visite:
            testata = Table([[P(f"{_data_it(v.get('data'))} &nbsp;-&nbsp; {_pdf_txt(v.get('tipo'))}", "testata")]],
                            colWidths=[W])
            testata.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E0F2FE")),
                ("BOX", (0, 0), (-1, -1), 0.6, bordo), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            righe_v = [("Veterinario / clinica", _pdf_txt(v.get("veterinario")))]
            if v.get("nome_vaccino") or v.get("tipo") == "Vaccinazione":
                righe_v.append(("Vaccino", _pdf_txt(v.get("nome_vaccino"))))
                righe_v.append(("Lotto", _pdf_txt(v.get("lotto_vaccino"))))
                if v.get("scadenza_vaccino"):
                    righe_v.append(("Scadenza vaccino", _data_it(v.get("scadenza_vaccino"))))
            if richiamo_attivo(v):
                righe_v.append(("Richiamo previsto", _pdf_txt(f"{_data_it(v.get('prossimo_controllo_data'))} - {descrizione_richiamo(v)}")))
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

    storia.append(P("Le informazioni sono inserite dal proprietario. Documento generato automaticamente da PetHealth.", "piccolo"))

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

_RE_B64 = re.compile(r"^[A-Za-z0-9+/=\s]*$")

def _b64_sicuro(b64_img):
    """Un'immagine salvata entra in una pagina HTML solo se è davvero base64 puro (niente virgolette o simboli)."""
    s = str(b64_img or "")
    return s if _RE_B64.match(s) else ""

def html_foto_animale(b64_img, specie, nome, dimensione=116):
    """Foto tonda con cornice dorata; se manca la foto mostra un segnaposto con l'emoji della specie."""
    b64_img = _b64_sicuro(b64_img)
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


# ---------------------------------------------------------------------------
# REFERTI: più pagine, ritaglio di ogni pagina, download in un secondo momento.
# I file stanno in una cartella riservata "referti" accanto ai dati (non dentro il file JSON, che resterebbe pesante):
# nella visita si conserva solo l'elenco {id, ext, nome}. Si leggono soltanto tramite la visita del proprietario.
# ---------------------------------------------------------------------------
MAX_PAGINE_REFERTO = 12
MAX_BYTE_PAGINA_REFERTO = 15 * 1024 * 1024
_RE_ID_REFERTO = re.compile(r"^[0-9a-f]{32}$")

def _cartella_referti():
    base = os.environ.get("PETHEALTH_DIR") or os.path.dirname(os.path.abspath(DATA_FILE))
    cart = os.path.join(base, "referti")
    os.makedirs(cart, mode=0o700, exist_ok=True)
    return cart

def elabora_pagina_referto(raw_bytes):
    """Pagina di referto pronta da conservare: orientamento corretto, max 2000 px (testo leggibile), JPEG leggero."""
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        sfondo = Image.new("RGB", img.size, (255, 255, 255))
        sfondo.paste(img, mask=img.split()[-1])
        img = sfondo
    else:
        img = img.convert("RGB")
    img.thumbnail((2000, 2000))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    return buf.getvalue()

def salva_pagine_referto(pagine):
    """Scrive su disco le pagine pronte [{bytes, ext, nome}]. Restituisce l'elenco da conservare nella visita."""
    salvati = []
    try:
        cart = _cartella_referti()
        for p in pagine:
            idf = secrets.token_hex(16)
            ext = "pdf" if p.get("ext") == "pdf" else "jpg"
            fd = os.open(os.path.join(cart, f"{idf}.{ext}"), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(p["bytes"])
            salvati.append({"id": idf, "ext": ext, "nome": str(p.get("nome", ""))[:80]})
    except OSError:
        elimina_file_referti({"referti": salvati})
        raise
    return salvati

def leggi_pagina_referto(meta):
    idf, ext = str((meta or {}).get("id", "")), (meta or {}).get("ext")
    if not _RE_ID_REFERTO.match(idf) or ext not in ("jpg", "pdf"):
        return None
    try:
        with open(os.path.join(_cartella_referti(), f"{idf}.{ext}"), "rb") as f:
            return f.read()
    except OSError:
        return None

def elimina_file_referti(v):
    """Toglie dal disco le pagine allegate a una visita (referti) o a una fattura (documenti)."""
    for campo in ("referti", "documenti"):
        for m in (v.get(campo) or []):
            idf, ext = str((m or {}).get("id", "")), (m or {}).get("ext")
            if _RE_ID_REFERTO.match(idf) and ext in ("jpg", "pdf"):
                try:
                    os.remove(os.path.join(_cartella_referti(), f"{idf}.{ext}"))
                except OSError:
                    pass

def elimina_file_referti_utente(u):
    """Quando un account viene eliminato spariscono anche tutti i suoi referti."""
    for campo in ("db_visite", "db_fatture"):
        for voci in (u.get(campo) or {}).values():
            for v in voci:
                elimina_file_referti(v)
    for a in (u.get("angeli_archiviati") or {}).values() if isinstance(u.get("angeli_archiviati"), dict) else (u.get("angeli_archiviati") or []):
        for campo in ("visite", "fatture"):
            for v in (a.get(campo) or []):
                elimina_file_referti(v)

def scegli_pagine_referto(chiave, titolo="📄 Referto o esiti degli esami (facoltativo)",
                          descrizione="Se l'esito è stampato su più fogli, aggiungi tutte le pagine: restano nell'ordine in cui le scegli. "
                                      "Di ogni foto puoi tenere solo il foglio, senza il tavolo intorno."):
    """Scelta delle pagine di un documento (referto, fattura): più file o foto, ritaglio di ogni foto, fotocamera. Restituisce [{bytes, ext, nome}]."""
    st.markdown(f"##### {titolo}")
    st.caption(descrizione)
    k_cam, k_cnt = f"ref_cam_{chiave}", f"ref_camcnt_{chiave}"
    scattate = st.session_state.setdefault(k_cam, [])
    caricati = st.file_uploader("Carica le pagine (foto o PDF, anche più di una)",
                                type=["pdf", "png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key=f"ref_up_{chiave}")
    st.caption("💡 Da telefono puoi scegliere più foto dalla galleria, oppure scattarle al momento qui sotto.")
    if scheda_a_comparsa(f"refcam_{chiave}", "📷 Scatta una pagina con la fotocamera"):
        n_cam = st.session_state.get(k_cnt, 0)
        foto = st.camera_input("Inquadra il foglio e scatta", key=f"ref_camw_{chiave}_{n_cam}")
        if foto is not None and st.button("➕ Aggiungi questa pagina", key=f"ref_camadd_{chiave}_{n_cam}"):
            scattate.append(foto.getvalue())
            st.session_state[k_cnt] = n_cam + 1
            st.rerun()

    da_file = [(f.name, f.getvalue()) for f in (caricati or [])]
    elementi = da_file + [(f"Foto {i}.jpg", b) for i, b in enumerate(scattate, 1)]
    if len(elementi) > MAX_PAGINE_REFERTO:
        st.warning(f"Si possono allegare al massimo {MAX_PAGINE_REFERTO} pagine per volta: le altre vengono ignorate.")
        elementi = elementi[:MAX_PAGINE_REFERTO]

    pronte = []
    for i, (nome, grezza) in enumerate(elementi, 1):
        with st.container(border=True):
            st.markdown(f"**Pagina {i}**")
            st.caption(str(nome)[:80])
            if len(grezza) > MAX_BYTE_PAGINA_REFERTO:
                st.warning("Questo file è troppo grande (massimo 15 MB): non verrà allegato.")
                continue
            if grezza[:5] == b"%PDF-":
                st.caption("📎 File PDF: verrà allegato così com'è (i PDF non si possono ritagliare).")
                pronte.append({"bytes": grezza, "ext": "pdf", "nome": nome})
            else:
                try:
                    Image.open(io.BytesIO(grezza)).load()
                except Exception:
                    st.warning("Non riesco a leggere questo file: prova con una foto JPG o PNG.")
                    continue
                sigla = hashlib.md5(grezza).hexdigest()[:8]
                lavoro = grezza
                if st.checkbox("✂️ Ritaglia questa pagina", key=f"ref_cr_{chiave}_{i}_{sigla}"):
                    try:
                        box_iniziale = [0.02, 0.02, 0.98, 0.98]
                        box_scelto = box_iniziale
                        if _cropper is not None:
                            st.caption("Trascina gli angoli e i bordi del riquadro verde: tieni solo il foglio.")
                            sel = _cropper(key=f"ref_cropper_{chiave}_{i}_{sigla}", src=anteprima_foto_ritaglio(grezza),
                                           box=box_iniziale, default=None)
                            if sel and sel.get("box") and len(sel["box"]) == 4:
                                box_scelto = sel["box"]
                        else:
                            sx = st.slider("Ritaglio orizzontale (%)", 0, 100, (2, 98), key=f"ref_sx_{chiave}_{i}_{sigla}")
                            sy = st.slider("Ritaglio verticale (%)", 0, 100, (2, 98), key=f"ref_sy_{chiave}_{i}_{sigla}")
                            if sx[1] - sx[0] >= 3 and sy[1] - sy[0] >= 3:
                                box_scelto = [sx[0] / 100, sy[0] / 100, sx[1] / 100, sy[1] / 100]
                        lavoro = ritaglia_bytes(grezza, box_scelto)
                    except Exception as e:
                        st.warning(f"Ritaglio non disponibile per questa foto: {e}")
                        lavoro = grezza
                try:
                    pagina = elabora_pagina_referto(lavoro)
                except Exception:
                    st.warning("Non riesco a leggere questo file: prova con una foto JPG o PNG.")
                    continue
                st.image(pagina, width=220)
                pronte.append({"bytes": pagina, "ext": "jpg", "nome": nome})
            if i > len(da_file):
                if st.button("🗑️ Togli questa foto", key=f"ref_camdel_{chiave}_{i}"):
                    scattate.pop(i - len(da_file) - 1)
                    st.rerun()
    if pronte:
        st.success(f"✅ {len(pronte)} {'pagina pronta' if len(pronte) == 1 else 'pagine pronte'}: verranno allegate quando salvi la visita.")
    return pronte

def pdf_unico_da_pagine(pagine_jpg):
    """Unisce più pagine-immagine in un solo PDF (A4 circa)."""
    imgs = [Image.open(io.BytesIO(b)).convert("RGB") for b in pagine_jpg]
    buf = io.BytesIO()
    imgs[0].save(buf, format="PDF", save_all=True, append_images=imgs[1:], resolution=170.0)
    return buf.getvalue()

def zip_da_pagine(elenco):
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for nome, dati in elenco:
            z.writestr(nome, dati)
    return buf.getvalue()

def _bottone_scarica(etichetta, dati, nome, mime, chiave, **kw):
    """Download che non ricarica la pagina (se la versione di Streamlit lo permette)."""
    try:
        return st.download_button(etichetta, data=dati, file_name=nome, mime=mime, key=chiave, on_click="ignore", **kw)
    except TypeError:
        return st.download_button(etichetta, data=dati, file_name=nome, mime=mime, key=chiave, **kw)

def mostra_referti_visita(v, chiave, pet):
    """Nella scheda della visita: elenco dei referti allegati con anteprima e download (singole pagine o tutto insieme)."""
    mostra_allegati(v, chiave, pet, "referti", "referto", "Referti allegati", "Referto")

def mostra_allegati(v, chiave, pet, campo, campo_vecchio, titolo, prefisso, cosa="referto"):
    """Allegati di una visita o di una fattura con anteprima e download (singole pagine o tutto insieme)."""
    referti = [m for m in (v.get(campo) or []) if isinstance(m, dict)]
    if not referti:
        if v.get(campo_vecchio):                                 # registrati prima: era salvato solo il nome del file
            st.caption(f"📄 Allegato: {v[campo_vecchio]}")
        return
    n = len(referti)
    if not scheda_a_comparsa(f"refv_{chiave}", f"📥 {titolo} ({n} {'pagina' if n == 1 else 'pagine'})"):
        return
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", f"{prefisso}_{pet}_{v.get('data', '')}").strip("_")
    pagine = [(m, leggi_pagina_referto(m)) for m in referti]
    mancanti = [m for m, d in pagine if d is None]
    pagine = [(m, d) for m, d in pagine if d is not None]
    if mancanti:
        st.warning(f"{len(mancanti)} {'pagina non è più disponibile' if len(mancanti) == 1 else 'pagine non sono più disponibili'}.")
    if not pagine:
        return
    if len(pagine) > 1:
        if all(m["ext"] == "jpg" for m, _d in pagine):
            try:
                _bottone_scarica("⬇️ Scarica tutte le pagine in un unico PDF", pdf_unico_da_pagine([d for _m, d in pagine]),
                                 f"{base}.pdf", "application/pdf", f"refdl_pdf_{chiave}", type="primary", use_container_width=True)
            except Exception:
                pass
        else:
            _bottone_scarica("⬇️ Scarica tutte le pagine (file ZIP)",
                             zip_da_pagine([(f"{base}_pagina{i}.{m['ext']}", d) for i, (m, d) in enumerate(pagine, 1)]),
                             f"{base}.zip", "application/zip", f"refdl_zip_{chiave}", type="primary", use_container_width=True)
    for i, (m, d) in enumerate(pagine, 1):
        etichetta = f"⬇️ Scarica il {cosa}" if len(pagine) == 1 else f"⬇️ Pagina {i}"
        _bottone_scarica(etichetta + (" (PDF)" if m["ext"] == "pdf" else ""), d,
                         f"{base}_pagina{i}.{m['ext']}", "application/pdf" if m["ext"] == "pdf" else "image/jpeg",
                         f"refdl_{chiave}_{i}", use_container_width=True)
    if st.checkbox("👁️ Mostra le pagine qui sotto", key=f"refprev_{chiave}"):
        for i, (m, d) in enumerate(pagine, 1):
            if m["ext"] == "jpg":
                st.caption(f"Pagina {i}")
                st.image(d)
            else:
                st.caption(f"Pagina {i}: file PDF, usa il pulsante di download.")


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
            .btn-action { background-color: #1FA0E3; color: #ffffff !important; border: none; padding: 12px 18px; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 0.95rem; flex: 1; min-width: 160px; box-shadow: 0 4px 6px rgba(0,0,0,0.15); transition: background-color 0.2s; }
            .btn-action:hover { opacity: 0.9; }
            .btn-action:active { transform: scale(0.98); }
            .btn-sec { background-color: #1FA0E3 !important; }
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
    testo = f"🐾 *PetHealth - Promemoria Visita*\n\n🐶 *Animale:* {animale}\n🏥 *Prestazione:* {tipo_visita}\n📅 *Data:* {data_ui(data_visita)}\n"
    if veterinario: testo += f"🩺 *Veterinario:* {veterinario}\n"
    if note: testo += f"📝 *Note:* {note}\n"
    testo += "\n⚠️ *Ricordati di confermare o presentarti all'appuntamento!*"
    numero_pulito = "".join(filter(str.isdigit, str(numero)))
    return f"https://api.whatsapp.com/send?phone={numero_pulito}&text={urllib.parse.quote(testo)}" if numero_pulito else f"https://api.whatsapp.com/send?text={urllib.parse.quote(testo)}"

# ---- Terapie: posologia guidata, più orari al giorno, rapporto con la pappa, notifica 10 minuti prima ----
_FORME_SOLIDE = {"Pastiglia / compressa": ("pastiglia", "pastiglie", "f"), "Capsula": ("capsula", "capsule", "f"),
                 "Bustina": ("bustina", "bustine", "f"), "Fiala": ("fiala", "fiale", "f"), "Pipetta": ("pipetta", "pipette", "f")}
_FORME_CUCCHIAI = {"Cucchiaino": ("cucchiaino", "cucchiaini", "m"), "Cucchiaio": ("cucchiaio", "cucchiai", "m")}
FORME_TERAPIA = list(_FORME_SOLIDE) + list(_FORME_CUCCHIAI) + ["Millilitri (ml)", "Gocce", "Altro (scrivo io)"]
QUANTITA_TERAPIA = [0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5]
PASTO_TERAPIA = ["Indifferente", "Prima della pappa", "Insieme alla pappa", "Dopo la pappa", "A stomaco vuoto (lontano dai pasti)"]
ORARI_PREDEFINITI = ["08:00", "20:00", "14:00", "22:00"]

def _num_terapia(x):
    return (f"{x:g}").replace(".", ",")

def testo_quantita(qta, forma):
    """«mezza pastiglia», «1 cucchiaino e mezzo», «2,5 ml», «5 gocce»..."""
    if forma == "Millilitri (ml)":
        return f"{_num_terapia(qta)} ml"
    if forma == "Gocce":
        return "1 goccia" if qta == 1 else f"{_num_terapia(qta)} gocce"
    sing, plur, gen = (_FORME_SOLIDE.get(forma) or _FORME_CUCCHIAI.get(forma))
    f = gen == "f"
    intero, mezzo = int(qta), (qta - int(qta)) == 0.5
    if qta == 0.25: return f"un quarto di {sing}"
    if qta == 0.5: return f"{'mezza' if f else 'mezzo'} {sing}"
    if qta == 0.75: return f"tre quarti di {sing}"
    if qta == 1: return f"{'una' if f else 'un'} {sing}"
    if qta == 1.5: return f"{'una' if f else 'un'} {sing} e {'mezza' if f else 'mezzo'}"
    nome = plur if qta > 1 else sing
    return f"{intero} {nome}" + (f" e {'mezza' if f else 'mezzo'}" if mezzo else "")

def testo_posologia(forma, qta, conc="", farmaco="", libero=""):
    """Compone la posologia leggibile: «mezza pastiglia da 50 mg», «1 cucchiaino di Sciroppo (5 mg/ml)»."""
    if forma == "Altro (scrivo io)":
        return (libero or "").strip()
    base = testo_quantita(qta, forma)
    conc = (conc or "").strip()
    if forma in _FORME_SOLIDE:
        return f"{base} da {conc}" if conc else base
    nome = (farmaco or "").strip()
    out = f"{base} di {nome}" if nome else base
    return f"{out} ({conc})" if conc else out

def orari_terapia(t):
    """Elenco degli orari HH:MM validi di una terapia (le vecchie terapie hanno un solo orario, a volte scritto a parole)."""
    grezzi = t.get("orari") or [t.get("orario")]
    validi = []
    for o in grezzi:
        o = str(o or "").strip()
        if re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", o):
            validi.append(o.zfill(5))
    return validi

def descrizione_pasto(t):
    pasto = (t.get("pasto") or "").strip()
    return "" if not pasto or pasto == "Indifferente" else pasto

def mostra_dettagli_terapia(pet, t, idx, sede):
    """Dettagli di una terapia + interruttore della notifica + eliminazione."""
    orari = orari_terapia(t)
    st.write(f"**Dose / Quantità:** {t.get('dosaggio', '')}")
    st.write(f"**Orari di somministrazione:** {', '.join(orari) if orari else (t.get('orario') or 'Non specificato')}")
    if descrizione_pasto(t):
        st.write(f"**Rispetto alla pappa:** {descrizione_pasto(t)}")
    st.write(f"**Periodo:** {t.get('periodo', '')}")
    if t.get("note"):
        st.write(f"**Note:** {t['note']}")
    if t.get("rev_numero"):
        st.write(f"**Ricetta elettronica (REV):** n. {t['rev_numero']}" + (f" · PIN {t['rev_pin']}" if t.get("rev_pin") else ""))
    mostra_immagine_salvata(t.get("etichetta_farmaco"), "🏷️ Etichetta del farmaco")
    nuovo = st.checkbox("🔔 Avvisami con una notifica 10 minuti prima", value=bool(t.get("notifica")), key=f"ter_not_{sede}_{idx}",
                        help="L'app ti manda la notifica con la dose da dare. Attiva le notifiche da «App e notifiche».")
    if nuovo != bool(t.get("notifica")):
        t["notifica"] = nuovo
        salva_dati()
    if nuovo and not orari:
        st.caption("⚠️ Per ricevere la notifica serve un orario preciso (es. 08:30): questa terapia ha un orario scritto a parole.")
    mostra_pulsanti_promemoria_terapia(pet, t.get("farmaco", ""), t.get("dosaggio", ""), t.get("orario", ""), t.get("note", ""))
    if not ospite_solo_aggiunta() and st.button("🗑️ Elimina Terapia", key=f"del_ter_{sede}_{idx}"):
        user_db["db_terapie"][pet].pop(idx)
        salva_dati(); st.rerun()

def mostra_pulsanti_promemoria_terapia(animale, farmaco, dosaggio, orario, note=""):
    user_data = st.session_state.db_users.get(st.session_state.get("account_attivo") or st.session_state.logged_user_email, {})
    num1 = user_data.get("numero_whatsapp", "")
    num2 = user_data.get("numero_whatsapp_2", "")
    if num1 and num2:
        c1, c2 = st.columns(2)
        with c1: st.link_button("📲 WhatsApp (Num 1)", url=genera_link_whatsapp(num1, animale, farmaco, dosaggio, orario, note))
        with c2: st.link_button("📲 WhatsApp (Num 2)", url=genera_link_whatsapp(num2, animale, farmaco, dosaggio, orario, note))
    else:
        st.link_button("📲 Invia Promemoria WhatsApp", url=genera_link_whatsapp(num1 or num2, animale, farmaco, dosaggio, orario, note))

def mostra_pulsanti_promemoria_visita(animale, tipo_visita, data_visita, veterinario="", note=""):
    """I promemoria dei richiami arrivano solo come notifica dell'app (2 giorni prima), non più su WhatsApp o email."""
    d = _data_o_none(data_visita)
    if d and d >= date.today():
        st.caption(f"🔔 Riceverai una notifica dell'app 2 giorni prima ({(d - timedelta(days=2)).strftime('%d/%m/%Y')}). Attivala da «App e notifiche».")

st.markdown("""
    <style>
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

    /* Icona bilancia pesapersone di "Peso e Andamento": nera, ben visibile sullo sfondo azzurro */
    [data-testid="stSidebar"] .st-key-menu_peso [data-testid="stIconMaterial"],
    [data-testid="stSidebar"] .st-key-menu_peso button span[class*="material"] {
        color: #000000 !important; -webkit-text-fill-color: #000000 !important; opacity: 1 !important;
        font-size: 1.35rem !important; margin-right: .25rem !important;
    }
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

_FONT_TITOLI = "'Fraunces', Georgia, 'Times New Roman', serif"

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
    "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');\n"
    ".stApp { background-image: radial-gradient(1100px 520px at 88% -8%, rgba(184, 151, 90, 0.11), rgba(184, 151, 90, 0) 62%); }\n"
    + _css_area_principale([('::selection', 'background: rgba(184, 151, 90, 0.35);')])
    + "\n" + _css_area_principale(_REGOLE_GRAFICA + _REGOLE_TEMA_CHIARO) +
    "\n</style>",
    unsafe_allow_html=True
)


# ---------------------------------------------------------------------------
# REBRANDING 2026 - PetHealth Wellness & Care
# Logo, accesso verde, menù azzurro, promemoria, demo, attivazione sicura.
# ---------------------------------------------------------------------------
_LOGO_MARCHIO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAIQAAAB/CAMAAAAZz5pPAAAAkFBMVEXX7fUdLGBZao+fsMm2ydz1+fs3R3ONnLdtb3B2ialGVHsc"
    "HGyboq1KWHdlbZwqOGEYKT9WZoeIl7IMa2s2RWqjs8pHU3YAAP92h6Y4R2lZaYxvj55/f/+LmbamttG9z9oADDw7ToKYqMV///+z"
    "x9hzh6LJ2/AnNlgA//+/37/R6/cAAAADGGUFFVju+/wAC1BGOU8NAAAAMHRSTlP/+vr//w/8/wX8/AMTYR6nBGOhAppgmwGrZKYc"
    "Am0cHf//kQJXSUl6AQj/AP7+//5teWdHAAAMX0lEQVR42rVciXacuBItCQRNr7a7vcdxksksD1rw/3/3apFoNoHadjSTcxxso9u3"
    "VpWqAtWVa7W5kS/M9+1+d0v/0f/7/dbI85vN6tp3wnUIBMDr7e50ULIsLvfl4fC8e2UoN6s/BUIQ7G9PbuvhOguckwC5ho9YEI+E"
    "wOwOvP+5s/OZ/vglz5CT3TvxYb4UxGpDHByU35j2O/dYONsukDPhMNF0xICgN213IgO/UYProg30PX7S4cOq3Xf3y58HQSwICfJx"
    "aTvcQes8T9IUoCxLAEiTpNBrZQWbh/HwGgUDInSBITgKcI9MFwmUNS+AurvKNNeZZUYIRGPVYY9CefwcCHzF9gKhaZTOU96/nFiC"
    "CNJ8rQiHg3Ha82s+DAKJNA9IsZOCXefQ2Z8lMQGFgLQ4GmJjuyATmMdwq7zyN6qAAAPjRTgKxeqB/Fl1i/b6IRCPm2r7oFjNSA55"
    "GQ3B4YAc1UOUQz0gGeZ6EEjDTkwCIWQEobxyQV3myIZIkshYXQtiU5mTKKQVFvCl5cdgOHM9maBIAiBuqr1iLlGiGnXhAwi8UDT7"
    "edKMfQgFBHi4VWLtTZZeL4g+jCRz9qp2AZcxBeK/qnoWFhtblDWUn1t1WSCpRIc6VdUxDgRiOHltSD5Hg1eNRIkTPR/MlHrChFkY"
    "j0F/ngZHBmjn8Q7/m0AxAvFYmYMV3PnHFXK8CpeGHN7HEoExhhNiQG1WOdHwZSBIJJ6LzQKITXVwGNK6/NIlKIgLswDipiIeGsQA"
    "X4wBUaRscmd7GPoLGPDwTAjsn8DQorAjFDDwUZyR/BkMFxTqua8W0DPOFYoN3fWX60MXBaXI6MFX0yAeqy2HzT+HgbTThbNt11Ch"
    "q5QHzoVsEoFhMq2KsOc6t2O1gI4wnhXH/rxeDkoEou9NMeMu0wgPWxcNu63nDooWxBEVgjMYXS+GglRnSmW6G1igfQZLv71mp6VW"
    "F7XogDgwhqxcBJH7EKu9AIAySkonMewCLMURxUHhMAZxRA/BXnVRKTFL8Se+Rrsdoeg8q2OUE3fatSg8iM2rCKOolzWrcwDWIBia"
    "y7NFnYKaQypZyKoH4qb6V6xzSRhQqg6Is00oyKXdZ1aVywLhKHLqgziym7LLn4K4PHdBZLgjfrLesxwiBEJoXx0KaLWS9CpbNDHo"
    "b4hU1H0i8NF60WGwQC5UgGDYi8ZGuMpM9UCgHtbFAJdaBpEqFr7z3tD6Sn7hss9TarjjQBrns4Jll+WpOHoQj9XKxhIxBIE79lWV"
    "HqUQEclYK4QK8KYRY+FsHP0Nz3b8KIIJRx9ScePFQdEzkojRxx6DQAnFBHXLMX3rxLESZxlDxNg6JkA0OiY7Jq2w5DY3DGLj1DKv"
    "4xKCkWL+HFltfGZxECY4lxHDgpg8oi8P/NhDX5VFHRMA+IiKqnlEEJTcOrUMo6DvuO8W3eop8TdwVjavuznGbGLh8grw0phWS2iz"
    "qDb1xU/QwaCGbruNrFQWkAQoqJokgIMo5lbJ2yZB0IfJdZa16QrUnQ9uSf4AqWouOiKlTfq5gtOctIZALkifpqFYCqtqN+sk6jSz"
    "LoVxZFz2tJjC9J+4JBnwRzUXXRs82Qekwu6eixawoToA+vGASgtetwHGbdaNVNNRkepI4ESVZlzLpVqCf9DYCzeTwYTlQa77BsUh"
    "thE47nSjU+d1CUrop05blQF+svZkScawkGuhg2EqDOqEoS9DQbyv+U3mMEDHWtpMhQgQkB36PPag67bqO4LYM4gA2jrv+YCmgJ7R"
    "XpDAODBcUBQQejl+QnWLIHasEvmyNDoBEubqyhMOrZ5LsHYI4sTKn8aBELAwW9zGlzfnGBACFjUTqgPfXcF0ZWggjrjgNMxywqFR"
    "NLMC41zVtDFPxKsIFNkgooVCIx/G0DzgXXlXBdPWMQDR0XQIxYZB4mtDmZZQpvbw2oKYRjFQ9GHZACaQdJ0E0fxzmj1wwlYr2Kuh"
    "vvV/ciCPDhN80SMxyn3RFXVMfiHCVjvYzYMYUHFRTCoPpOQmFQY3naTsqSZ/JQuq0QWEbcFCsMLT8VbOL5cUI62EEL4BpLKAu5Ho"
    "maidqftQoomrByLmBExvRHNOfp4bO1C/xmaFg9EJ7XYma3QgTiKOORBQ5622MxEIge+VxquRizJfvZXIO3Ogqtn27APcLoHoBuqC"
    "7vqSNkqPF4f3unS/gTnI7DkIg20UCLa/mgM1Ch0NAvQ0Cxf+MxQZ/YbWRbJ8+LiAaBaydKglXyrdzcU8ClvIzTEsXZYMQMyeOS4x"
    "E22qGW05IRNdRlVCxUTtDkHY2IMP1MUQQ9s0MDyERd1RtCD+ZhBFTP201sOPTacOWsnITtZxlVUuG+2AD8NR59BRHYJBiM8eW6uG"
    "uZSjl2/vMZRHghjmN10Q6VgxYsh1UfQVTEYgshpgHjUkyl4Dwkaci6W4i/lE9cA3lmU9DwKGmcoSCDkhLihZ5jIrBkExAZaOr+fr"
    "QCzLWApNnGN6G50FMSwTnhtZHoT76zW1K3DZtqJse+tTK5hxVkPLUHpNK0ucdWS81uoKKkCKA3LuMAwimxXGsEJH1cupNUzDYPYq"
    "huuIDZ/AqjWnN7NXb8O3h0DkU4UjCH8yPoDiWXRTvdhFxz1xkogCMXtK4QTM2gc8lb9Wf1NgXKjmqo+BmLVSdx6m+oSpTMYNbOVs"
    "GhYnjmRY250RMnoef+tBNasXu+DgemnmLBPDSmsy/8nITXLNalW9zRUHJj1VLBOzWS5XU0kaDMKI9wxTN46fSvNaez+xlr//HAaQ"
    "Aub0jCpO3xEAV3RJHucfedBfTfhsdpC2DeVWPKYdhdKgp0DboDNL5mrbR7IPqRjBNYGjm0+oQL4pOgGBCGqpB0xq248oD+5mSkJU"
    "jGQ9BjH9A+PoAT2Da5ShbjhwHQv0ZB2KYaPwFQlixk+4q5+H9r5jVb1Lv0uQCtDNPIgARj1XU5bmAX/zg1+8yBV1uAq1xISaUYkJ"
    "cbjbjofLHRiCkNsGmwd8NwSocGlInQaIgMAZRm6qqa69v9yLOirCvhtSNYkicO64FAUgmFyiSjgiWhDfeZMZISbTG7nW6cnv5aH+"
    "SXfeaC/LwTcEvyxcz16O+3GLmsVmmhdEI/oX9mZjNF+WB09OXCCY4IGj0Ci95Hp/qMcF1tJj9D4AUb1SGMP3/QidWah0XrjOZdmG"
    "OsjzhJd0azcdCDNHYvK/FD5v205quHRov9iFkA415FpZ6YPOijzpdI6X0sAu1q+LNJwiORdhtRm3s3yrjGt2gSAXXKdI85wa6Ict"
    "5NzOnuRETTpXmKhLaZLg8DnqLto6gaBaLLQW1cEW9lFFc+K3uY2kQWEcp/qsVtUTX1f/0B/p9erHnaDrrYsfLIyXbuNbD4TRXBe0"
    "xZ/rOJNer2bda5Pt9t5tWS3sjPv+oq63JruvtqEuxH11LyYcjqdzF8jLXROJa+677885wGCS4hfn/9R/B/D1PChuI1d3gzZdGA4R"
    "3ClB8fUScaW/Rj2Zo5lrj8Vs6055vfhSCEA6yX6oMMMBBxh3bTMKS5ZafyWGwnVua4OOcaFv+xujYB2OLIlGiQL0D+EBMfy13MH+"
    "l0exUKK/DsNahm8mZDHdy++5IJlQI/2nceAZld9HdjHBw/RUA/oysVT7+ckKEUUjGLJfY30IzncgYffaofjscAW4zvVzY9FPTg/+"
    "QGjo6F27Tm+er4iFQalPN5TVdSr3I9QE8rs6mqtmfvaV+SU3PDT/9cExDxq2Ue4l6KKCk0fB6actiURuFj4IQ2bBSL9pcOi+6sWs"
    "yDkwZM48yQiVwCiXpXKRA5AglCikWOakSkZNxN1r5af8miyPHYmj9C5Zu1EVynp/m9m5vNnZQMRu7jowMLuGegkID0tqGtr0orwz"
    "c+Nwy1OSNKJ4R8OGZ+HVqnUhOe6UD5MpyYQR+CnJjCCsPjcvavaeDevu3Ro+bviB0d60KKS5JsTywwzh6Z+qOi6NrS5PzpKbJRjt"
    "HRyfu1S21njy4NlZGpvNc62VDM7KFDFJb00QquVx5pgZYjIt88uPxPqbSFcqE4fm/3LuDtiSIMJ2efU0tcF0zPx+0pnXt+4Edzti"
    "7eesiSj9dB8LIX6u/BvJ1fxzx2e9xk+U28FYt5wCM4fg+O3LJ+zNlo4rxtwjkExOpO3gtJcGdR2+vBmesN+a6Fdf9W8NmO+s58b8"
    "vnvSBKW7Mq1fkAHe+hoEV/+DB8TH3p3fDJJy//Z2h+vt7f7+3fh999chwPV/1yLZ8WlacP4AAAAASUVORK5CYII="
)

def _marchio_img(altezza):
    """Il logo dell'app (zampa con croce dentro il cerchio), con le proporzioni originali."""
    return (f'<img src="data:image/png;base64,{_LOGO_MARCHIO_B64}" alt="PetHealth" height="{altezza}" '
            f'style="height:{altezza}px;width:auto;flex:none;display:block">')

def _marchio_svg(ring, paw, cross, size):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}" aria-hidden="true" '
            f'style="flex:none;display:block">'
            f'<circle cx="32" cy="32" r="30" fill="none" stroke="{ring}" stroke-width="2.5"/>'
            f'<g fill="{paw}"><ellipse cx="19.5" cy="28" rx="3.6" ry="4.8" transform="rotate(-24 19.5 28)"/>'
            f'<ellipse cx="27.5" cy="20" rx="3.9" ry="5.2" transform="rotate(-8 27.5 20)"/>'
            f'<ellipse cx="36.5" cy="20" rx="3.9" ry="5.2" transform="rotate(8 36.5 20)"/>'
            f'<ellipse cx="44.5" cy="28" rx="3.6" ry="4.8" transform="rotate(24 44.5 28)"/>'
            f'<path d="M32 30c-7.5 0-13.5 6.6-13.5 12.2 0 4 3 6.6 7 6.6 2.4 0 3.9-1 6.5-1s4.1 1 6.5 1c4 0 7-2.6 7-6.6C45.5 36.6 39.5 30 32 30z"/></g>'
            f'<path class="ph-cross" d="M30.2 35.2h3.6v3.6h3.6v3.6h-3.6V46h-3.6v-3.6h-3.6v-3.6h3.6z" fill="{cross}"/></svg>')

_ICONA_PUNTO = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D9BF86" stroke-width="2.2" stroke-linecap="round" '
                'stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')

def hero_punti_html(punti):
    return '<ul class="ph-punti">' + "".join(f'<li>{_ICONA_PUNTO}<span>{html_escape(p)}</span></li>' for p in punti) + '</ul>'

def logo_html(sidebar=False):
    """Logo PetHealth: versione su verde (accesso) oppure bianca su azzurro (menù laterale)."""
    if sidebar:
        marchio = _marchio_img(46)
        c_health, c_tag, size = "#111111", "#0B2A3F", "1.25rem"
        c_pet = "#111111"
    else:
        marchio = _marchio_img(54)
        c_health, c_tag, size = "#111111", "#8A6A1F", "1.6rem"
        c_pet = "#111111"
    return (f'<div class="ph-logo" style="display:flex;align-items:center;gap:12px">{marchio}<div>'
            f'<div class="ph-logo-name" style="font-family:\'Fraunces\',Georgia,serif;font-weight:600;font-size:{size};line-height:1;letter-spacing:-0.02em;color:{c_pet} !important">'
            f'Pet<span class="ph-logo-health" style="color:{c_health} !important">Health</span></div>'
            f'<div class="ph-logo-tag" style="font:700 9px/1 \'Plus Jakarta Sans\',sans-serif;letter-spacing:0.26em;text-transform:uppercase;color:{c_tag} !important;margin-top:6px">Wellness &amp; Care</div>'
            f'</div></div>')

_CSS_REBRAND = (
    "\n/* ===== REBRANDING 2026 ===== */\n"
    "html, body, .stApp { font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important; }\n"
    # --- menù laterale: voci come nel prototipo (trasparenti, voce attiva evidenziata) ---
    "[data-testid=\"stSidebar\"] .stButton > button, [data-testid=\"stSidebar\"] [data-testid=\"stBaseButton-secondary\"] {\n"
    "  background: transparent !important; background-image: none !important; border: 1px solid transparent !important; box-shadow: none !important;\n"
    "  justify-content: flex-start !important; text-align: left !important; padding: 0.55rem 0.85rem !important; border-radius: 12px !important; }\n"
    "[data-testid=\"stSidebar\"] .stButton > button:hover, [data-testid=\"stSidebar\"] [data-testid=\"stBaseButton-secondary\"]:hover {\n"
    "  background: rgba(255,255,255,0.16) !important; transform: none !important; filter: none !important; }\n"
    "[data-testid=\"stSidebar\"] [data-testid=\"stBaseButton-primary\"] {\n"
    "  background: rgba(255,255,255,0.22) !important; background-image: none !important; border: 1px solid transparent !important;\n"
    "  box-shadow: inset 3px 0 0 #FFFFFF !important; justify-content: flex-start !important; text-align: left !important;\n"
    "  padding: 0.55rem 0.85rem !important; border-radius: 12px !important; }\n"
    "[data-testid=\"stSidebar\"] .stButton > button p, [data-testid=\"stSidebar\"] .stButton > button div { text-align: left !important; justify-content: flex-start !important; font-weight: 600 !important; font-size: 0.93rem !important; }\n"
    "[data-testid=\"stSidebar\"] .ph-side-logo { padding: 2px 4px 14px 4px; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.32); }\n"
    # --- blocchi della dashboard ---
    ".ph-head { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 12px; margin: 4px auto 18px auto; width: 100%; }\n"
    ".ph-head > div { text-align: center !important; width: 100%; }\n"
    ".ph-head h2, .ph-head .ph-sub { text-align: center !important; }\n"
    ".ph-head h2 { margin: 0 !important; }\n"
    ".ph-head h2::after { display: none !important; }\n"
    ".ph-head .ph-sub { color: #5B6A62 !important; margin: 4px 0 0 0 !important; font-size: 0.98rem; }\n"
    ".ph-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }\n"
    ".ph-metric { background: #FFFFFF; border: 1px solid #ECE6D6; border-radius: 22px; padding: 18px 22px; min-width: 0;\n"
    "  box-shadow: 0 1px 2px rgba(30,58,43,0.04), 0 18px 40px -26px rgba(30,58,43,0.28); }\n"
    ".ph-metric b { display: block; font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 2.1rem; line-height: 1; color: #1E3A2B; font-variant-numeric: tabular-nums; }\n"
    ".ph-metric span { font: 700 0.68rem/1 'Plus Jakarta Sans', sans-serif; letter-spacing: 0.12em; text-transform: uppercase; color: #5B6A62; display: block; margin-top: 8px; }\n"
    ".ph-rem { display: flex; gap: 12px; justify-content: space-between; align-items: center; flex-wrap: wrap; padding: 12px 16px; border-radius: 14px; border: 1px solid; margin-bottom: 10px; }\n"
    ".ph-rem.ok { background: #EEF6F1; border-color: #BFDCCB; }\n"
    ".ph-rem.warn { background: #FBF3E2; border-color: #E8CF97; }\n"
    ".ph-rem.err { background: #FBEDE6; border-color: #EDB9A2; }\n"
    ".ph-rem .quando { font: 700 0.76rem 'Plus Jakarta Sans', sans-serif; border-radius: 99px; padding: 4px 12px; background: #FFFFFF; }\n"
    ".ph-rem.ok .quando { color: #2F7D5B; } .ph-rem.warn .quando { color: #8A5A0B; } .ph-rem.err .quando { color: #B03A0B; }\n"
    "@media (max-width: 700px) { .ph-metrics { grid-template-columns: minmax(0, 1fr); } }\n"
)

_CSS_MOBILE = """
/* ===== TELEFONO / TABLET / MODALITÀ APP ===== */
html, body { -webkit-text-size-adjust: 100%; overscroll-behavior-y: none; }
.stApp { -webkit-tap-highlight-color: transparent; }
html body .stApp [data-testid="stMain"] img { max-width: 100%; height: auto; }
@media (display-mode: standalone) {
  [data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"], .stDeployButton,
  [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
}
/* La freccia che riapre il menù laterale deve restare SEMPRE visibile (sta dentro la barra in alto) */
header[data-testid="stHeader"], [data-testid="stToolbar"] { display: flex !important; visibility: visible !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {
  display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 999990 !important; }
@media (max-width: 1024px) {
  html body [data-testid="stMain"] [data-testid="stMainBlockContainer"], html body [data-testid="stMain"] .block-container {
    padding-left: 1.2rem !important; padding-right: 1.2rem !important; }
}
@media (max-width: 640px) {
  html body [data-testid="stMain"] [data-testid="stMainBlockContainer"], html body [data-testid="stMain"] .block-container {
    padding: 3.4rem 0.9rem calc(5.5rem + env(safe-area-inset-bottom, 0px)) 0.9rem !important; max-width: 100% !important; }
  html body [data-testid="stMain"] h1 { font-size: 1.85rem !important; line-height: 1.15 !important; }
  html body [data-testid="stMain"] h2 { font-size: 1.5rem !important; }
  html body [data-testid="stMain"] h3 { font-size: 1.2rem !important; }
  /* 16px nei campi: evita lo zoom automatico di iPhone quando si tocca un campo */
  input, textarea, [data-baseweb="select"] input, [data-baseweb="select"] div[value], [data-baseweb="select"] > div { font-size: 16px !important; }
  .stButton > button, [data-testid="stFormSubmitButton"] > button, [data-testid="stDownloadButton"] > button,
  [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"], [data-testid="stLinkButton"] a { min-height: 48px !important; }
  [data-testid="stMain"] .stButton > button, [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button,
  [data-testid="stMain"] [data-testid="stDownloadButton"] > button, [data-testid="stMain"] [data-testid="stLinkButton"] a { width: 100% !important; }
  [data-testid="stHorizontalBlock"] { gap: 0.6rem !important; }
  [data-testid="stExpander"] summary { min-height: 48px; align-items: center; }
  [data-testid="stSidebar"] { max-width: 88vw !important; }
  [data-testid="stSidebar"] .stButton > button { min-height: 46px !important; }
  [role="tablist"] { overflow-x: auto !important; flex-wrap: nowrap !important; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
  [role="tablist"]::-webkit-scrollbar { display: none; }
  [role="tab"] { flex: 0 0 auto; white-space: nowrap; }
  [data-testid="stDataFrame"], [data-testid="stTable"] { max-width: 100%; overflow-x: auto; }
  [data-testid="stFileUploaderDropzone"] { padding: 14px !important; }
  [data-testid="stFileUploaderDropzone"] > div { flex-wrap: wrap; gap: 8px; }
  .wellness-card { padding: 16px !important; }
  .ph-head { gap: 10px; }
  .cal-mese { padding: 8px !important; }
  [data-testid="stImage"] img { max-width: 100%; }
}
@media (max-width: 380px) {
  html body [data-testid="stMain"] h1 { font-size: 1.6rem !important; }
  html body [data-testid="stMain"] [data-testid="stMainBlockContainer"] { padding-left: 0.7rem !important; padding-right: 0.7rem !important; }
}
"""
_CSS_RESTYLING = r'''html body .stApp [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(.ph-impost-marker) [data-testid="stBaseButton-secondary"] { background: #1FA0E3 !important; border: 1px solid #1789C6 !important; box-shadow: none !important; }
html body .stApp [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(.ph-impost-marker) [data-testid="stBaseButton-secondary"] p { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
html body .stApp [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(.ph-impost-marker) [data-testid="stBaseButton-secondary"]:hover { background: #158FD0 !important; }
html body .stApp [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(.ph-impost-marker) button { min-height: 52px !important; }
:root {
--ph-forest: #1E3A2B; --ph-forest-deep: #12281D; --ph-gold: #B8975A; --ph-gold-soft: #E9DDBC; --ph-gold-light: #F3E7C4;
--ph-ivory: #F8F6F0; --ph-ink: #16251D; --ph-mute: #5B6A62; --ph-line: #E6DFCB;
--ph-field: #9DB1A4; --ph-field-hover: #5F8570; --ph-sky: #0284C7; --ph-sky-deep: #0369A1;
--ph-ease: cubic-bezier(.22, .8, .24, 1);
--ph-anim-rise: ph-rise .55s var(--ph-ease) both;
--ph-anim-pop: ph-pop .42s var(--ph-ease) both;
--ph-anim-open: ph-open .38s var(--ph-ease) both;
--ph-anim-line: ph-line .9s var(--ph-ease) .15s both;
--ph-anim-beat: ph-beat 5.5s ease-in-out 1.2s infinite;
}
@keyframes ph-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes ph-pop { from { opacity: 0; transform: scale(.97) translateY(4px); } to { opacity: 1; transform: none; } }
@keyframes ph-open { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: none; } }
@keyframes ph-line { from { width: 0; opacity: 0; } to { width: 58px; opacity: 1; } }
@keyframes ph-beat {
0%, 56%, 100% { transform: scale(1); }
62% { transform: scale(1.3); } 68% { transform: scale(1); }
74% { transform: scale(1.2); } 82% { transform: scale(1); }
}
@keyframes ph-sheen { from { transform: translateX(-120%) skewX(-18deg); } to { transform: translateX(260%) skewX(-18deg); } }
@media (prefers-reduced-motion: reduce) {
:root { --ph-anim-rise: none; --ph-anim-pop: none; --ph-anim-open: none; --ph-anim-line: none; --ph-anim-beat: none; }
}
@A, html body .stApp [data-testid="stMain"] [data-testid="stAppViewContainer"] {
background-color: var(--ph-ivory) !important;
background-image:
radial-gradient(900px 480px at 92% -6%, rgba(184, 151, 90, .13), rgba(184, 151, 90, 0) 62%),
radial-gradient(760px 520px at -8% 104%, rgba(30, 58, 43, .07), rgba(30, 58, 43, 0) 64%) !important;
background-attachment: fixed !important;
}
html body .stApp ::selection { background: rgba(184, 151, 90, .38); }
html body .stApp ::-webkit-scrollbar { width: 10px; height: 10px; }
html body .stApp ::-webkit-scrollbar-thumb { background: #CFC6AA; border-radius: 10px; border: 2px solid var(--ph-ivory); }
html body .stApp ::-webkit-scrollbar-thumb:hover { background: #B8AC88; }
html body .stApp [data-testid="stMain"] h1, html body .stApp [data-testid="stMain"] h2, html body .stApp [data-testid="stMain"] h3 {
font-family: 'Fraunces', Georgia, 'Times New Roman', serif !important; font-optical-sizing: auto;
color: var(--ph-forest) !important; font-weight: 560 !important; letter-spacing: -.018em !important; }
html body .stApp [data-testid="stMain"] h2::after { height: 2px !important; background: linear-gradient(90deg, #B8975A, rgba(184, 151, 90, 0)) !important; animation: var(--ph-anim-line); }
html body .stApp [data-testid="stMain"] [data-testid="stMarkdownContainer"] p { color: #22332A; }
html body .stApp [data-testid="stMain"] [data-testid="stCaptionContainer"] * { color: var(--ph-mute) !important; }
html body .stApp [data-testid="stMain"] .wellness-card {
position: relative; background: linear-gradient(180deg, #FFFFFF 0%, #FEFDFA 100%) !important;
border: 1px solid var(--ph-line) !important; border-radius: 22px !important;
box-shadow: inset 0 1px 0 rgba(255, 255, 255, .95), 0 1px 2px rgba(30, 58, 43, .05), 0 22px 44px -28px rgba(30, 58, 43, .30) !important;
animation: var(--ph-anim-rise); }
html body .stApp [data-testid="stMain"] .wellness-card::before {
content: ""; position: absolute; left: 26px; right: 26px; top: -1px; height: 2px; border-radius: 2px;
background: linear-gradient(90deg, rgba(184, 151, 90, 0), #B8975A 30%, #E2CE9B 50%, #B8975A 70%, rgba(184, 151, 90, 0)); opacity: .75; }
html body .stApp [data-testid="stMain"] .wellness-card h3, html body .stApp [data-testid="stMain"] .wellness-card h4 { color: var(--ph-forest) !important; }
html body .stApp [data-testid="stMain"] .ph-metric { position: relative; border-radius: 22px !important; border-color: var(--ph-line) !important; animation: var(--ph-anim-rise);
transition: transform .3s var(--ph-ease), box-shadow .3s var(--ph-ease); }
html body .stApp [data-testid="stMain"] .ph-metric:hover { transform: translateY(-3px); box-shadow: 0 1px 2px rgba(30, 58, 43, .05), 0 26px 44px -26px rgba(30, 58, 43, .38); }
html body .stApp [data-testid="stMain"] .ph-metric::after { content: ""; position: absolute; left: 22px; bottom: 0; width: 34px; height: 3px; border-radius: 3px 3px 0 0; background: var(--ph-gold); }
html body .stApp [data-testid="stMain"] .ph-metric:nth-child(2) { animation-delay: .07s; } html body .stApp [data-testid="stMain"] .ph-metric:nth-child(3) { animation-delay: .14s; }
html body .stApp [data-testid="stMain"] .ph-rem { border-radius: 16px !important; animation: var(--ph-anim-rise); transition: transform .25s var(--ph-ease), box-shadow .25s var(--ph-ease); }
html body .stApp [data-testid="stMain"] .ph-rem:hover { transform: translateX(3px); box-shadow: 0 12px 26px -18px rgba(30, 58, 43, .35); }
html body .stApp [data-testid="stMain"] .card-badge { letter-spacing: .14em !important; }
html body .stApp [data-testid="stMain"] [data-testid="stWidgetLabel"] p, html body .stApp [data-testid="stMain"] [data-testid="stWidgetLabel"] label, html body .stApp [data-testid="stMain"] label[data-testid="stWidgetLabel"] {
font-size: .86rem !important; font-weight: 650 !important; color: #2A3F33 !important; letter-spacing: .005em; margin-bottom: 4px; }
html body .stApp [data-testid="stMain"] [data-baseweb="select"] > div {
background: #FFFFFF !important; border: 1.5px solid var(--ph-field) !important; border-radius: 13px !important; min-height: 48px;
box-shadow: inset 0 1px 3px rgba(30, 58, 43, .09), 0 1px 0 rgba(255, 255, 255, .9) !important;
transition: border-color .2s var(--ph-ease), box-shadow .2s var(--ph-ease), background-color .2s var(--ph-ease) !important; }
html body .stApp [data-testid="stMain"] [data-baseweb="select"] > div:hover { border-color: var(--ph-field-hover) !important; }
html body .stApp [data-testid="stMain"] [data-baseweb="select"] > div:focus-within {
border-color: var(--ph-forest) !important; background: #FFFFFF !important;
box-shadow: 0 0 0 4px rgba(184, 151, 90, .30), inset 0 1px 2px rgba(30, 58, 43, .05) !important; }
html body .stApp [data-testid="stMain"] [data-testid="stTextInput"] div, html body .stApp [data-testid="stMain"] [data-testid="stNumberInput"] div, html body .stApp [data-testid="stMain"] [data-testid="stTextArea"] div, html body .stApp [data-testid="stMain"] [data-testid="stDateInput"] div { border: 0 !important; background: transparent !important; box-shadow: none !important; }
html body .stApp [data-testid="stMain"] [data-testid="stTextInput"] div:has(> input), html body .stApp [data-testid="stMain"] [data-testid="stNumberInput"] div:has(> input), html body .stApp [data-testid="stMain"] [data-testid="stDateInput"] div:has(> input), html body .stApp [data-testid="stMain"] [data-testid="stTextArea"] div:has(> textarea) {
border: 1.5px solid #1F2A24 !important; background: #FFFFFF !important; border-radius: 13px !important; min-height: 48px; overflow: hidden;
box-shadow: inset 0 1px 3px rgba(30, 58, 43, .10) !important; transition: border-color .2s var(--ph-ease), box-shadow .2s var(--ph-ease) !important; }
html body .stApp [data-testid="stMain"] [data-testid="stTextInput"] div:has(> input):hover, html body .stApp [data-testid="stMain"] [data-testid="stNumberInput"] div:has(> input):hover, html body .stApp [data-testid="stMain"] [data-testid="stDateInput"] div:has(> input):hover, html body .stApp [data-testid="stMain"] [data-testid="stTextArea"] div:has(> textarea):hover { border-color: #000000 !important; }
html body .stApp [data-testid="stMain"] [data-testid="stTextInput"] div:has(> input:focus), html body .stApp [data-testid="stMain"] [data-testid="stNumberInput"] div:has(> input:focus), html body .stApp [data-testid="stMain"] [data-testid="stDateInput"] div:has(> input:focus), html body .stApp [data-testid="stMain"] [data-testid="stTextArea"] div:has(> textarea:focus) {
border-color: #000000 !important; box-shadow: 0 0 0 4px rgba(184, 151, 90, .40) !important; }
html body .stApp [data-testid="stMain"] [data-testid="stTextInput"] input, html body .stApp [data-testid="stMain"] [data-testid="stNumberInput"] input, html body .stApp [data-testid="stMain"] [data-testid="stDateInput"] input, html body .stApp [data-testid="stMain"] [data-testid="stTextArea"] textarea { border: 0 !important; background: transparent !important; box-shadow: none !important; outline: none !important; }
html body .stApp [data-testid="stMain"] [data-testid="stTextInput"] div:has(> input[aria-label*="Codice"]) { border-width: 2.5px !important; border-color: #000000 !important; background: #FFFDF6 !important; min-height: 64px; }
html body .stApp [data-testid="stMain"] [data-testid="stNumberInput"] div:has(> input) button { border: 0 !important; }
html body .stApp [data-testid="stMain"] [role="tablist"] { display: flex; gap: 6px !important; padding: 5px !important; background: #F3EEDF !important; border-radius: 99px !important; border: 0 !important; }
html body .stApp [data-testid="stMain"] [role="tablist"] > div:empty { display: none !important; }
html body .stApp [data-testid="stMain"] button[role="tab"] { flex: 1 1 0; justify-content: center !important; padding: 0 20px !important; min-height: 42px !important; margin: 0 !important; border-radius: 99px !important; background: transparent !important; color: #5B6A62 !important; font-weight: 650 !important; border: 0 !important; }
html body .stApp [data-testid="stMain"] button[role="tab"] p { color: inherit !important; -webkit-text-fill-color: inherit !important; font-weight: 650 !important; }
html body .stApp [data-testid="stMain"] button[role="tab"][aria-selected="true"] { background: #FFFFFF !important; color: #1E3A2B !important; box-shadow: 0 6px 14px -6px rgba(30, 58, 43, .35) !important; }
html body .stApp [data-testid="stMain"] [data-baseweb="base-input"] { background: transparent !important; border: 0 !important; border-radius: 12px !important; }
html body .stApp [data-testid="stMain"] [data-baseweb="select"] input { background-color: transparent !important; border-radius: 11px !important; }
html body .stApp [data-testid="stMain"] input:not([type="checkbox"]):not([type="radio"]):not([type="range"]), html body .stApp [data-testid="stMain"] textarea {
padding: .72rem .95rem !important; font-size: 1rem !important; font-weight: 500 !important; }
html body .stApp [data-testid="stMain"] input::placeholder, html body .stApp [data-testid="stMain"] textarea::placeholder { color: #7A8C82 !important; -webkit-text-fill-color: #7A8C82 !important; font-weight: 400 !important; opacity: 1 !important; }
html body .stApp [data-testid="stMain"] [data-baseweb="input"] input:disabled, html body .stApp [data-testid="stMain"] textarea:disabled { background: #F1EEE4 !important; }
html body .stApp [data-testid="stMain"] [data-testid="stNumberInput"] button { background: #F6F2E6 !important; border-radius: 9px !important; }
html body .stApp [data-testid="stMain"] [data-testid="stNumberInput"] button:hover { background: var(--ph-gold-soft) !important; }
html body .stApp [data-testid="stMain"] input[aria-label*="Codice"] {
font-size: 1.7rem !important; font-weight: 700 !important; letter-spacing: .42em !important; text-align: center !important;
height: 64px !important; padding: .4rem .6rem .4rem 1.1rem !important; font-variant-numeric: tabular-nums;
color: var(--ph-forest) !important; -webkit-text-fill-color: var(--ph-forest) !important; }
html body .stApp [data-testid="stMain"] [data-baseweb="input"]:has(input[aria-label*="Codice"]) { border-width: 2px !important; border-color: var(--ph-forest) !important; background: #FFFDF6 !important; min-height: 64px; }
html body .stApp [data-testid="stMain"] input[aria-label*="Codice"]::placeholder { letter-spacing: .2em; font-size: 1.1rem; font-weight: 500 !important; }
html body .stApp [data-testid="stMain"] label[data-baseweb="checkbox"] > span:first-child { border: 1.5px solid #7C9486 !important; border-radius: 7px !important; background: #FFFFFF !important; transition: all .18s var(--ph-ease); }
html body .stApp [data-testid="stMain"] label[data-baseweb="checkbox"]:has(input:checked) > span:first-child { background: var(--ph-forest) !important; border-color: var(--ph-forest) !important; }
html body .stApp [data-testid="stMain"] label[data-baseweb="checkbox"]:hover > span:first-child { border-color: var(--ph-forest) !important; }
html body .stApp [data-testid="stMain"] label[data-baseweb="radio"] > div:first-child { border: 1.5px solid #7C9486 !important; background-color: #FFFFFF !important; }
html body .stApp [data-testid="stMain"] label[data-baseweb="radio"]:has(input:checked) > div:first-child { background-color: var(--ph-forest) !important; border-color: var(--ph-forest) !important; }
html body .stApp [data-testid="stMain"] .stButton > button, html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-secondary"], html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-primary"],
html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button, html body .stApp [data-testid="stMain"] [data-testid="stDownloadButton"] > button {
position: relative; overflow: hidden; min-height: 46px;
background: linear-gradient(135deg, #2B5642 0%, #1E3A2B 55%, #17301F 100%) !important; border: 1px solid #14281D !important;
border-radius: 14px !important; letter-spacing: .01em;
box-shadow: inset 0 1px 0 rgba(255, 255, 255, .16), 0 10px 20px -10px rgba(20, 40, 29, .62) !important;
transition: transform .22s var(--ph-ease), box-shadow .22s var(--ph-ease), filter .22s var(--ph-ease) !important; }
html body .stApp [data-testid="stMain"] .stButton > button::after, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button::after, html body .stApp [data-testid="stMain"] [data-testid="stDownloadButton"] > button::after {
content: ""; position: absolute; top: 0; bottom: 0; left: 0; width: 38%; pointer-events: none;
background: linear-gradient(90deg, rgba(255, 255, 255, 0), rgba(255, 255, 255, .22), rgba(255, 255, 255, 0)); transform: translateX(-120%) skewX(-18deg); }
html body .stApp [data-testid="stMain"] .stButton > button:hover::after, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:hover::after, html body .stApp [data-testid="stMain"] [data-testid="stDownloadButton"] > button:hover::after {
animation: ph-sheen .85s var(--ph-ease); }
html body .stApp [data-testid="stMain"] .stButton > button:hover, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:hover, html body .stApp [data-testid="stMain"] [data-testid="stDownloadButton"] > button:hover {
transform: translateY(-2px); filter: none !important;
box-shadow: inset 0 1px 0 rgba(255, 255, 255, .2), 0 16px 26px -12px rgba(20, 40, 29, .7), 0 0 0 1px rgba(184, 151, 90, .45) !important; }
html body .stApp [data-testid="stMain"] .stButton > button:active, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:active { transform: translateY(0) scale(.985); }
html body .stApp [data-testid="stMain"] .stButton > button:focus-visible, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:focus-visible { outline: 3px solid rgba(184, 151, 90, .65) !important; outline-offset: 2px !important; }
html body .stApp [data-testid="stMain"] .stButton > button:disabled { background: #D9D4C3 !important; border-color: #CFC9B5 !important; box-shadow: none !important; }
html body .stApp [data-testid="stMain"] .stButton > button p, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button p, html body .stApp [data-testid="stMain"] [data-testid="stDownloadButton"] > button p { color: #FFFFFF !important; font-weight: 650 !important; }
html body .stApp [data-testid="stMain"] [data-testid^="stBaseLinkButton"] { border: 1.5px solid var(--ph-forest) !important; border-radius: 14px !important; min-height: 46px; }
html body .stApp [data-testid="stMain"] [data-testid="stExpander"] details { border: 1px solid var(--ph-line) !important; border-radius: 18px !important; background: #FFFFFF !important; overflow: hidden;
box-shadow: 0 1px 2px rgba(30, 58, 43, .04), 0 14px 26px -22px rgba(30, 58, 43, .25) !important; }
html body .stApp [data-testid="stMain"] [data-testid="stExpander"] details[open] { border-color: #D9CFAE !important; }
html body .stApp [data-testid="stMain"] [data-testid="stExpander"] details[open] > div, html body .stApp [data-testid="stMain"] [data-testid="stExpander"] details[open] [data-testid="stExpanderDetails"] { animation: var(--ph-anim-open); }
html body .stApp [data-testid="stMain"] [data-testid="stExpander"] summary { transition: background-color .2s var(--ph-ease); }
html body .stApp [data-testid="stMain"] [data-testid="stExpander"] summary:hover { background: #FBF8EF !important; }
html body .stApp [data-testid="stMain"] button[data-baseweb="tab"] { font-weight: 650 !important; transition: color .2s var(--ph-ease), background-color .2s var(--ph-ease); }
html body .stApp [data-testid="stMain"] button[data-baseweb="tab"]:hover { color: var(--ph-forest) !important; }
html body .stApp [data-testid="stMain"] [data-baseweb="tab-highlight"] { background-color: var(--ph-gold) !important; transition: left .35s var(--ph-ease), width .35s var(--ph-ease) !important; }
html body .stApp [data-testid="stMain"] [data-testid="stAlert"] { border-radius: 16px !important; border: 1px solid rgba(30, 58, 43, .14) !important; animation: var(--ph-anim-pop);
box-shadow: 0 10px 22px -18px rgba(30, 58, 43, .45); }
html body .stApp [data-testid="stMain"] [data-testid="stAlert"] p { font-weight: 500; }
html body .stApp [data-testid="stMain"] [data-testid="stCode"] pre, html body .stApp [data-testid="stMain"] [data-testid="stCode"] code { background: #FBF8EE !important; color: #3F3417 !important; }
html body .stApp [data-testid="stMain"] [data-testid="stCode"] { border: 1px solid var(--ph-line); border-left: 4px solid var(--ph-gold); border-radius: 12px; overflow: hidden; }
html body .stApp [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] { border: 2px dashed #C8B27A !important; background: #FCFAF3 !important; border-radius: 18px !important; transition: background-color .2s var(--ph-ease), border-color .2s var(--ph-ease); }
html body .stApp [data-testid="stMain"] [data-testid="stFileUploaderDropzone"]:hover { background: #F7F1DE !important; border-color: var(--ph-gold) !important; }
[data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] ul { border-radius: 14px !important; }
[data-baseweb="popover"] li { transition: background-color .15s var(--ph-ease); }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background: #F6F1E0 !important; }
.ph-cross { transform-box: fill-box; transform-origin: center; animation: var(--ph-anim-beat); }
[data-testid="stSidebar"] { background-image: linear-gradient(185deg, #0B8AD0 0%, #0284C7 38%, #0369A1 100%) !important; border-right: 1px solid #075985 !important;
box-shadow: 14px 0 40px -24px rgba(7, 89, 133, .55); }
[data-testid="stSidebar"] > div, [data-testid="stSidebarContent"], [data-testid="stSidebarHeader"], [data-testid="stSidebarUserContent"] { background: transparent !important; }
[data-testid="stSidebar"] .ph-side-logo { border-bottom: 1px solid rgba(243, 231, 196, .55) !important; }
[data-testid="stSidebar"] .st-key-menu_account button p { font-weight: 800 !important; font-size: 1.1rem !important; }
.st-key-torna_home_back { position: absolute !important; left: -9999px !important; top: 0 !important; width: 1px !important; height: 1px !important; overflow: hidden !important; opacity: 0 !important; }
[data-testid="stSidebar"] .stButton > button, [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
box-shadow: none !important; min-height: 44px; overflow: visible; transition: background-color .2s var(--ph-ease), transform .2s var(--ph-ease) !important; }
[data-testid="stSidebar"] .stButton > button::after { display: none !important; }
[data-testid="stSidebar"] .stButton > button:hover, [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
transform: translateX(3px) !important; box-shadow: none !important; background: rgba(255, 255, 255, .17) !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { box-shadow: inset 3px 0 0 #F3E7C4, 0 8px 18px -12px rgba(0, 0, 0, .45) !important; background: rgba(255, 255, 255, .24) !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]::after { display: none !important; }
[data-testid="stSidebar"] [data-baseweb="input"], [data-testid="stSidebar"] [data-baseweb="select"] > div { border-color: rgba(255, 255, 255, .9) !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] details { border-color: rgba(255, 255, 255, .5) !important; box-shadow: none !important; background: rgba(255, 255, 255, .13) !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background: rgba(255, 255, 255, .1) !important; }
[data-testid="stSidebar"] [data-testid="stAlert"] { animation: var(--ph-anim-pop); }
@media (max-width: 640px) {
html body .stApp [data-testid="stMain"] input[aria-label*="Codice"] { font-size: 1.5rem !important; letter-spacing: .34em !important; }
html body .stApp [data-testid="stMain"] .wellness-card::before { left: 18px; right: 18px; }
}'''

_CSS_RESTYLING_ACCESSO = r'''@keyframes ph-drift-a { 0% { transform: translate(0, 0) scale(1); } 50% { transform: translate(6vw, 5vh) scale(1.12); } 100% { transform: translate(0, 0) scale(1); } }
@keyframes ph-drift-b { 0% { transform: translate(0, 0) scale(1); } 50% { transform: translate(-7vw, -4vh) scale(1.08); } 100% { transform: translate(0, 0) scale(1); } }
@keyframes ph-hero-in { from { opacity: 0; transform: translateY(18px); filter: blur(6px); } to { opacity: 1; transform: none; filter: none; } }
@keyframes ph-card-in { from { opacity: 0; transform: translateY(26px) scale(.975); } to { opacity: 1; transform: none; } }
@keyframes ph-gold-slide { from { background-position: 0% 50%; } to { background-position: 200% 50%; } }
:root { --ph-anim-hero: ph-hero-in 1s var(--ph-ease) both; --ph-anim-card: ph-card-in 1s var(--ph-ease) .35s both; }
@media (prefers-reduced-motion: reduce) { :root { --ph-anim-hero: none; --ph-anim-card: none; } .stApp::after, .stApp::before { animation: none !important; } }
html body .stApp, html body .stApp [data-testid="stAppViewContainer"], html body .stApp [data-testid="stMain"] {
background-color: #17301F !important; background-image: linear-gradient(160deg, #1E3A2B 0%, #17301F 55%, #12281D 100%) !important; background-attachment: fixed !important; }
html body .stApp::after { content: ""; position: fixed; z-index: 0; pointer-events: none; width: 62vmax; height: 62vmax; right: -22vmax; top: -26vmax; border-radius: 50%;
background: radial-gradient(closest-side, rgba(217, 191, 134, .20), rgba(217, 191, 134, 0)); animation: ph-drift-a 26s ease-in-out infinite; }
html body .stApp [data-testid="stAppViewContainer"]::before { content: ""; position: fixed; z-index: 0; pointer-events: none; width: 54vmax; height: 54vmax; left: -20vmax; bottom: -26vmax; border-radius: 50%;
background: radial-gradient(closest-side, rgba(2, 132, 199, .24), rgba(2, 132, 199, 0)); animation: ph-drift-b 32s ease-in-out infinite; }
html body .stApp [data-testid="stMainBlockContainer"] { position: relative; z-index: 1; }
html body .stApp .ph-auth-top { animation: var(--ph-anim-hero); }
html body .stApp .ph-hero-eyebrow { animation: var(--ph-anim-hero); animation-delay: .15s; display: inline-block; }
html body .stApp .ph-hero-title { animation: var(--ph-anim-hero); animation-delay: .28s; font-weight: 560 !important; letter-spacing: -.025em !important; }
html body .stApp .ph-hero-title em, html body .stApp [data-testid="stMarkdownContainer"] .ph-hero-title em {
background: linear-gradient(100deg, #C9A85F 0%, #F3E7C4 25%, #C9A85F 50%, #F3E7C4 75%, #C9A85F 100%); background-size: 200% 100%;
-webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent !important; color: transparent !important; animation: ph-gold-slide 9s linear infinite; }
html body .stApp .ph-hero-text { animation: var(--ph-anim-hero); animation-delay: .42s; }
html body .stApp .ph-punti { animation: var(--ph-anim-hero); animation-delay: .56s; margin: 30px 0 0 0; padding: 0; list-style: none; display: grid; gap: 14px; max-width: 46ch; }
html body .stApp .ph-punti li { display: flex; align-items: flex-start; gap: 13px; color: rgba(255, 255, 255, .9) !important; -webkit-text-fill-color: rgba(255, 255, 255, .9) !important;
font-size: .98rem; line-height: 1.45; padding-top: 14px; border-top: 1px solid rgba(217, 191, 134, .28); }
html body .stApp .ph-punti li svg { flex: none; margin-top: 2px; }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) { position: relative; animation: var(--ph-anim-card);
background: linear-gradient(180deg, #FFFFFF 0%, #FEFCF7 100%) !important; border: 1px solid #D9BF86 !important; border-radius: 26px !important;
box-shadow: 0 1px 0 rgba(255, 255, 255, .9) inset, 0 30px 70px -26px rgba(0, 0, 0, .65), 0 0 0 6px rgba(217, 191, 134, .10) !important; }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker)::before { content: ""; position: absolute; left: 34px; right: 34px; top: -1px; height: 2px; border-radius: 2px;
background: linear-gradient(90deg, rgba(217, 191, 134, 0), #C9A85F 30%, #F3E7C4 50%, #C9A85F 70%, rgba(217, 191, 134, 0)); }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) [role="tablist"] { background: #F3EEDF !important; box-shadow: inset 0 1px 3px rgba(30, 58, 43, .10); }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) button[role="tab"] { transition: background-color .25s var(--ph-ease), color .25s var(--ph-ease), box-shadow .25s var(--ph-ease) !important; }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) button[role="tab"][aria-selected="true"] { box-shadow: 0 6px 14px -6px rgba(30, 58, 43, .35) !important; color: #1E3A2B !important; -webkit-text-fill-color: #1E3A2B !important; }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stTabs"] [role="tabpanel"] { animation: var(--ph-anim-open); }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stExpander"] details { border-color: #E6DFCB !important; box-shadow: none !important; }
html body .stApp .ph-demo { border-radius: 16px; background: linear-gradient(135deg, #F7F0DC, #F1E8CB); }
html body .stApp .ph-posta { border-radius: 16px; }
@media (max-width: 640px) { html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) { padding: 18px 14px 18px 14px !important; border-radius: 22px !important; } }
@media (max-width: 760px) { html body .stApp::after { width: 90vmax; height: 90vmax; } html body .stApp .ph-punti { margin-top: 22px; } }
html body .stApp [data-testid="stVerticalBlockBorderWrapper"]:has(.ph-auth-marker) { background: transparent !important; border: 0 !important; box-shadow: none !important; padding: 0 !important; border-radius: 0 !important; }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) { padding: 26px 28px 24px 28px !important; }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stButton"], html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) .stButton, html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stFormSubmitButton"] { width: 100% !important; }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stButton"] button, html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) .stButton button, html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stFormSubmitButton"] button { width: 100% !important; }
html body .stApp [data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stTextInput"] { margin-bottom: 6px; }'''

def _compatta_css(c):
    import re as _re
    c = _re.sub(r'/\*.*?\*/', '', c, flags=_re.S)
    return "\n".join(l.strip() for l in c.splitlines() if l.strip())

_CSS_SIDEBAR_CHIARA = """
html body .stApp [data-testid="stSidebar"] { background-color: #8FD0F4 !important; background-image: linear-gradient(185deg, #B6E2F8 0%, #8FD0F4 42%, #74C3EE 100%) !important;
border-right: 1px solid #5FB3E3 !important; box-shadow: 14px 0 40px -24px rgba(3, 105, 161, .35) !important; }
html body .stApp [data-testid="stSidebar"] > div, html body .stApp [data-testid="stSidebarContent"], html body .stApp [data-testid="stSidebarHeader"], html body .stApp [data-testid="stSidebarUserContent"] {
background: transparent !important; background-color: transparent !important; }
html body .stApp [data-testid="stSidebar"] h1, html body .stApp [data-testid="stSidebar"] h2, html body .stApp [data-testid="stSidebar"] h3, html body .stApp [data-testid="stSidebar"] h4,
html body .stApp [data-testid="stSidebar"] p, html body .stApp [data-testid="stSidebar"] span, html body .stApp [data-testid="stSidebar"] label, html body .stApp [data-testid="stSidebar"] li,
html body .stApp [data-testid="stSidebar"] small, html body .stApp [data-testid="stSidebar"] summary, html body .stApp [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
html body .stApp [data-testid="stSidebar"] [data-testid="stCaptionContainer"] *, html body .stApp [data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {
color: #0B2A3F !important; -webkit-text-fill-color: #0B2A3F !important; }
html body .stApp [data-testid="stSidebar"] hr { border-color: rgba(11, 42, 63, .25) !important; }
html body .stApp [data-testid="stSidebar"] .ph-side-logo { border-bottom: 1px solid rgba(11, 42, 63, .25) !important; }
html body .stApp [data-testid="stSidebar"] .stButton > button:hover, html body .stApp [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover { background: rgba(255, 255, 255, .5) !important; }
html body .stApp [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { background: rgba(255, 255, 255, .78) !important; box-shadow: inset 3px 0 0 #0369A1, 0 8px 18px -12px rgba(3, 105, 161, .45) !important; }
html body .stApp [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p { font-weight: 700 !important; }
html body .stApp [data-testid="stSidebar"] [data-baseweb="input"], html body .stApp [data-testid="stSidebar"] [data-baseweb="select"] > div { border-color: rgba(11, 42, 63, .45) !important; }
html body .stApp [data-testid="stSidebar"] [data-testid="stExpander"] details { border-color: rgba(11, 42, 63, .25) !important; background: rgba(255, 255, 255, .42) !important; }
html body .stApp [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background: rgba(255, 255, 255, .35) !important; }
html body .stApp [data-testid="stSidebar"] summary svg { fill: #0B2A3F !important; color: #0B2A3F !important; }
html body .stApp [data-testid="stSidebar"] [data-testid="stAlert"] { background-color: rgba(255, 255, 255, .6) !important; border: 1px solid rgba(11, 42, 63, .25) !important; }
html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg, html body .stApp [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] span, html body .stApp [data-testid="stSidebarHeader"] svg {
color: #0B2A3F !important; fill: #0B2A3F !important; }
"""


_SFONDO_LIBRETTO = '''
/* Sfondo su uno strato fisso a parte: il browser lo disegna una volta sola e lo scorrimento resta fluido anche sui dispositivi meno recenti. */
html { background-color: #E3F3FB !important; }
html body, html body .stApp, html body .stApp [data-testid="stAppViewContainer"], html body .stApp [data-testid="stMain"], html body .stApp section.main { background: transparent !important; background-image: none !important; }
html body::before { content: ""; position: fixed; top: 0; right: 0; bottom: 0; left: 0; z-index: -1; pointer-events: none; transform: translateZ(0);
 background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 240 240'><g fill='%230284C7' fill-opacity='.075'><g transform='translate(52 58) rotate(-18)'><ellipse cx='0' cy='9' rx='11' ry='9'/><ellipse cx='-14' cy='-6' rx='4.6' ry='6'/><ellipse cx='-5' cy='-14' rx='4.6' ry='6.4'/><ellipse cx='6' cy='-14' rx='4.6' ry='6.4'/><ellipse cx='15' cy='-6' rx='4.6' ry='6'/></g><g transform='translate(178 172) rotate(16) scale(.9)'><ellipse cx='0' cy='9' rx='11' ry='9'/><ellipse cx='-14' cy='-6' rx='4.6' ry='6'/><ellipse cx='-5' cy='-14' rx='4.6' ry='6.4'/><ellipse cx='6' cy='-14' rx='4.6' ry='6.4'/><ellipse cx='15' cy='-6' rx='4.6' ry='6'/></g></g><g fill='%2322A58A' fill-opacity='.09'><path transform='translate(176 52)' d='M-4 -13h8v9h9v8h-9v9h-8v-9h-9v-8h9z'/><path transform='translate(60 176) scale(.75)' d='M-4 -13h8v9h9v8h-9v9h-8v-9h-9v-8h9z'/></g></svg>"), radial-gradient(900px 560px at 94% -6%, rgba(31, 160, 227, .22), rgba(31, 160, 227, 0) 64%), radial-gradient(820px 600px at -6% 104%, rgba(52, 190, 160, .20), rgba(52, 190, 160, 0) 66%), radial-gradient(640px 420px at 100% 100%, rgba(184, 151, 90, .12), rgba(184, 151, 90, 0) 70%), linear-gradient(168deg, #F2FAFE 0%, #DDF0FA 52%, #E2F5EE 100%);
 background-size: 240px 240px, auto, auto, auto, auto; background-repeat: repeat, no-repeat, no-repeat, no-repeat, no-repeat; }
html body .stApp [data-testid="stHeader"] { background: transparent !important; }
'''


_CSS_BOTTONI_AZZURRI = """
html body .stApp [data-testid="stMain"] .stButton > button:not(:disabled), html body .stApp [data-testid="stDialog"] .stButton > button:not(:disabled),
html body .stApp :is([data-testid="stMain"], [data-testid="stDialog"]) :is([data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primaryFormSubmit"], [data-testid="stBaseButton-secondaryFormSubmit"], [data-testid="stDownloadButton"] > button, [data-testid="stFormSubmitButton"] > button, [data-testid="stPopoverButton"]):not(:disabled),
html body .stApp :is([data-testid="stMain"], [data-testid="stDialog"]) [data-testid="stLinkButton"] a {
background: #1FA0E3 !important; background-image: none !important; border: 1px solid #1789C6 !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important;
box-shadow: 0 6px 14px -8px rgba(23, 137, 198, .65) !important; }
html body .stApp [data-testid="stMain"] .stButton > button:not(:disabled):hover,
html body .stApp :is([data-testid="stMain"], [data-testid="stDialog"]) :is([data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primaryFormSubmit"],
[data-testid="stBaseButton-secondaryFormSubmit"], [data-testid="stDownloadButton"] > button, [data-testid="stFormSubmitButton"] > button):not(:disabled):hover,
html body .stApp :is([data-testid="stMain"], [data-testid="stDialog"]) [data-testid="stLinkButton"] a:hover { background: #158FD0 !important; background-image: none !important; }
html body .stApp :is([data-testid="stMain"], [data-testid="stDialog"]) :is(.stButton > button, [data-testid="stFormSubmitButton"] > button, [data-testid="stDownloadButton"] > button, [data-testid^="stBaseButton-primary"], [data-testid^="stBaseButton-secondary"], [data-testid="stPopoverButton"], [data-testid="stLinkButton"] a):not(:disabled) :is(p, span, div, svg) {
color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; fill: #FFFFFF; }
"""

_CSS_TABELLA = """
.ph-tab-wrap { background: #FFFFFF; border: 1px solid #ECE6D6; border-radius: 18px; overflow: hidden; margin: 4px 0 14px 0; }
table.ph-tab { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 0.93rem; color: #1E293B; }
table.ph-tab th { text-align: left; font: 700 0.68rem/1 'Plus Jakarta Sans', sans-serif; letter-spacing: 0.1em; text-transform: uppercase; color: #5B6A62; padding: 12px 12px; background: #FBF8EE; border-bottom: 1px solid #ECE6D6; }
table.ph-tab td { padding: 10px 12px; vertical-align: middle; border-bottom: 1px solid #F1ECDD; overflow-wrap: break-word; word-break: normal; hyphens: auto; }
table.ph-tab tr:last-child td { border-bottom: 0; }
table.ph-tab th:first-child, table.ph-tab td:first-child { width: 27%; }
table.ph-tab th:last-child, table.ph-tab td:last-child { width: 86px; text-align: center; }
table.ph-tab td b { color: #1E3A2B; font-weight: 700; display: block; }
table.ph-tab .ph-tab-sub { display: block; color: #5B6A62; font-size: 0.82rem; margin-top: 2px; }
table.ph-tab .ph-tab-vuota { color: #A9A38C; }
img.ph-mini { width: 64px; height: 64px; object-fit: contain; border-radius: 10px; border: 1px solid #ECE6D6; background: #FFFFFF; display: block; margin: 0 auto; }
@media (max-width: 640px) {
  table.ph-tab { font-size: 0.86rem; }
  table.ph-tab th, table.ph-tab td { padding: 8px 8px; }
  table.ph-tab th:last-child, table.ph-tab td:last-child { width: 64px; }
  table.ph-tab th:first-child, table.ph-tab td:first-child { width: 28%; }
  img.ph-mini { width: 52px; height: 52px; }
}
"""

st.markdown("<style>" + _compatta_css(_css_area_principale([
    ('.wellness-card', 'border-radius: 22px !important;'),
    ('[data-testid="stExpander"] details', 'border-radius: 16px !important;'),
]) + _CSS_REBRAND + _CSS_MOBILE + _CSS_RESTYLING + _CSS_TABELLA + _CSS_SIDEBAR_CHIARA + _CSS_BOTTONI_AZZURRI + _SFONDO_LIBRETTO) + "</style>", unsafe_allow_html=True)

_MINIATURE = {}

def miniatura_b64(b64, lato=120):
    """Piccola anteprima (JPEG, base64) di un'immagine salvata; stringa vuota se non c'è o non si legge."""
    if not b64:
        return ""
    chiave = hashlib.md5(str(b64).encode("ascii", "ignore")).hexdigest()
    if chiave in _MINIATURE:
        return _MINIATURE[chiave]
    try:
        img = Image.open(io.BytesIO(base64.b64decode(b64)))
        img.load()
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            fondo = Image.new("RGB", img.size, (255, 255, 255))
            fondo.paste(img, mask=img.split()[-1])
            img = fondo
        else:
            img = img.convert("RGB")
        img.thumbnail((lato, lato))
        buf = io.BytesIO(); img.save(buf, format="JPEG", quality=72)
        out = base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        out = ""
    if len(_MINIATURE) > 300:
        _MINIATURE.clear()
    _MINIATURE[chiave] = out
    return out

def tabella_html(intestazioni, righe):
    """Tabella della dashboard (HTML su una riga, niente righe vuote). Ogni riga: lista di celle già pronte (HTML sicuro)."""
    th = "".join(f"<th>{html_escape(h)}</th>" for h in intestazioni)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in righe)
    return f'<div class="ph-tab-wrap"><table class="ph-tab"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'

def cella_miniatura(b64, descrizione):
    mini = miniatura_b64(b64)
    if not mini:
        return '<span class="ph-tab-vuota">—</span>'
    return f'<img class="ph-mini" alt="{html_escape(descrizione)}" src="data:image/jpeg;base64,{mini}">'

def tabella_visite_html(visite, ana=None):
    righe = []
    for v in visite:
        titolo = html_escape(v.get("tipo", ""))
        sotto = []
        if v.get("nome_vaccino"):
            sotto.append("💉 " + html_escape(v.get("nome_vaccino")) + (f" · lotto {html_escape(v.get('lotto_vaccino'))}" if v.get("lotto_vaccino") else ""))
        if v.get("veterinario"):
            sotto.append(html_escape(v.get("veterinario")))
        if richiamo_attivo(v):
            sotto.append("🔔 richiamo " + html_escape(data_ui(v.get("prossimo_controllo_data"))))
        cella = f"<b>{titolo}</b>" + "".join(f'<span class="ph-tab-sub">{x}</span>' for x in sotto)
        righe.append([html_escape(data_ui(v.get("data", ""))), cella,
                      cella_miniatura(v.get("etichetta_vaccino"), "Etichetta del vaccino")])
    return tabella_html(["Data", "Visita", "Etichetta"], righe)

def tabella_terapie_html(terapie):
    righe = []
    for t in terapie:
        orari = orari_terapia(t)
        quando = ", ".join(orari) if orari else (t.get("orario") or "")
        cella2 = (f"<b>{html_escape(t.get('dosaggio', ''))}</b>" + (f'<span class="ph-tab-sub">⏰ {html_escape(quando)}</span>' if quando else "")
                  + f'<span class="ph-tab-sub">{html_escape(t.get("periodo", ""))}</span>')
        righe.append([f"<b>💊 {html_escape(t.get('farmaco', ''))}</b>", cella2, cella_miniatura(t.get("etichetta_farmaco"), "Etichetta del farmaco")])
    return tabella_html(["Farmaco", "Dose e orari", "Etichetta"], righe)


def vai_da_menu_urgenze():
    """Scelta nel menù a tendina «Urgenze & Cliniche 24H» (viene chiamata solo quando l'utente sceglie davvero una voce)."""
    scelta = st.session_state.get(st.session_state.get("_menu_urg_chiave", ""))
    if scelta in ("urgenze", "smarrito"):
        st.session_state.sezione_attiva = scelta
        st.session_state.trigger_close_sidebar = True

def voce_menu(etichetta, sezione, icona=None):
    """Voce del menù laterale: quella della sezione aperta è evidenziata."""
    attiva = st.session_state.get("sezione_attiva") == sezione
    kw = {"icon": icona} if icona else {}
    if st.button(etichetta, key=f"menu_{sezione}", type="primary" if attiva else "secondary", **kw):
        cambia_sezione(sezione)

# ---------------------------------------------------------------------------
# DASHBOARD: intestazione, numeri e promemoria
# ---------------------------------------------------------------------------
def mostra_intestazione_dashboard(user_db, pet, visite, terapie):
    ana = (user_db.get("db_anagrafica", {}) or {}).get(pet, {}) or {}
    foto = html_foto_animale(ana.get("foto_animale", ""), ana.get("tipo_animale", ""), pet, 92)
    sub = " · ".join([x for x in [ana.get("tipo_animale"), ana.get("razza"), ana.get("sesso")] if x]) or "Libretto sanitario"
    st.markdown(f'<div class="ph-head">{foto}<div><h2>{html_escape(pet)}</h2><p class="ph-sub">{html_escape(sub)}</p></div></div>',
                unsafe_allow_html=True)

    pesi = [p for p in sorted((user_db.get("db_peso", {}) or {}).get(pet, []), key=lambda p: str(p.get("data", "")))
            if isinstance(p.get("peso_kg"), (int, float)) and p["peso_kg"] > 0]
    ultimo = fmt_peso(pesi[-1]["peso_kg"]) if pesi else "—"
    st.markdown(
        '<div class="ph-metrics">'
        f'<div class="ph-metric"><b>{html_escape(str(ultimo))}</b><span>Ultimo peso</span></div>'
        f'<div class="ph-metric"><b>{len(visite)}</b><span>Visite e vaccini</span></div>'
        f'<div class="ph-metric"><b>{len(terapie)}</b><span>Terapie registrate</span></div>'
        '</div>', unsafe_allow_html=True)

    oggi = date.today()
    promemoria = []
    for v in visite:
        if richiamo_attivo(v):
            d = _data_o_none(v.get("prossimo_controllo_data"))
            promemoria.append(((d - oggi).days, descrizione_richiamo(v), d, True))
        elif "richiamo" not in v and not v.get("prossimo_controllo_data") and v.get("scadenza_vaccino"):
            d = _data_o_none(v.get("scadenza_vaccino"))   # vecchie visite: come prima, si usa la scadenza del vaccino
            if d:
                promemoria.append(((d - oggi).days, f"{v.get('nome_vaccino') or v.get('tipo', 'Vaccino')} · scadenza", d, False))
    promemoria.sort(key=lambda x: x[0])
    st.markdown("### ⏰ Promemoria")
    righe = []
    for giorni, testo, d, e_richiamo in promemoria:
        if giorni > 90 and not e_richiamo:
            continue
        classe = "err" if giorni < 0 else ("warn" if giorni <= 30 else "ok")
        testo = ("🔔 " + testo) if e_richiamo else testo
        quando = f"scaduto da {-giorni} giorni" if giorni < 0 else ("oggi" if giorni == 0 else f"tra {giorni} giorni")
        righe.append(f'<div class="ph-rem {classe}"><div><b>{html_escape(testo)}</b><div style="font-size:0.85rem;color:#5B6A62">{d.strftime("%d/%m/%Y")}</div></div>'
                     f'<span class="quando">{quando}</span></div>')
    st.markdown("".join(righe) if righe else '<div class="ph-rem ok"><b>Nessun richiamo in programma: tutto in regola.</b></div>',
                unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SICUREZZA DEGLI ACCESSI: limite ai tentativi sbagliati (per account e per indirizzo di rete)
# ---------------------------------------------------------------------------
LIMITI_TENTATIVI = {"id": (5, 900), "ip": (40, 900)}      # (errori ammessi, finestra in secondi)
# Dove l'app invia un'email a un indirizzo scelto da chi scrive, i limiti sono più stretti: nessuno deve poter usare PetHealth per riempire di messaggi la casella di un altro.
LIMITI_AMBITO = {
    "registra": {"ip": (10, 3600)},
    "reinvio": {"id": (4, 3600), "ip": (10, 3600)},
    "reset-richiesta": {"id": (4, 3600), "ip": (10, 3600)},
    "invito": {"id": (10, 3600), "ip": (20, 3600)},
    "pdf-email": {"id": (6, 3600), "ip": (15, 3600)},
    "smarrito": {"id": (3, 86400), "ip": (8, 86400)},
    "totp-invio": {"id": (5, 3600), "ip": (15, 3600)},   # email col codice della verifica in due passaggi: 5 all'ora per account
    "totp": {"id": (5, 900), "ip": (30, 900)},         # codici della verifica in due passaggi: 5 errori ogni 15 minuti per account      # al massimo 3 segnalazioni al giorno per account
}

@st.cache_resource(show_spinner=False)
def _registro_tentativi():
    return {"lock": threading.Lock(), "voci": {}}

def _ip_client():
    try:
        h = st.context.headers
        return h.get("Cf-Connecting-Ip") or str(h.get("X-Forwarded-For") or "").split(",")[0].strip() or ""
    except Exception:
        return ""

def _chiavi_tentativi(ambito, ident):
    lim = {**LIMITI_TENTATIVI, **LIMITI_AMBITO.get(ambito, {})}
    chiavi = [(f"id|{ambito}|{str(ident).strip().lower()}", lim["id"])]
    ip = _ip_client()
    if ip:
        chiavi.append((f"ip|{ambito}|{ip}", lim["ip"]))
    return chiavi

def secondi_blocco(ambito, ident):
    """0 se si può provare, altrimenti i secondi da aspettare."""
    reg, ora, attesa = _registro_tentativi(), datetime.now().timestamp(), 0
    with reg["lock"]:
        for chiave, (massimo, finestra) in _chiavi_tentativi(ambito, ident):
            voci = [t for t in reg["voci"].get(chiave, []) if ora - t < finestra]
            reg["voci"][chiave] = voci
            if len(voci) >= massimo:
                attesa = max(attesa, int(voci[0] + finestra - ora) + 1)
    return attesa

def log_sicurezza(evento, ident=""):
    """Riga nel registro del server (journalctl -u pethealth): serve a vedere gli attacchi. L'identificativo è un'impronta, non l'email."""
    try:
        impronta = hashlib.sha256(str(ident).strip().lower().encode("utf-8")).hexdigest()[:10]
        print(f"[SICUREZZA] evento={evento} id={impronta} ip={_ip_client() or '-'}", file=sys.stderr, flush=True)
    except Exception:
        pass

def registra_fallimento(ambito, ident):
    log_sicurezza("tentativo:" + str(ambito), ident)
    reg, ora = _registro_tentativi(), datetime.now().timestamp()
    with reg["lock"]:
        for chiave, _lim in _chiavi_tentativi(ambito, ident):
            reg["voci"].setdefault(chiave, []).append(ora)
        if len(reg["voci"]) > 20000:                       # pulizia: via le voci vecchie
            reg["voci"] = {k: [t for t in v if ora - t < 3600] for k, v in reg["voci"].items()}
            reg["voci"] = {k: v for k, v in reg["voci"].items() if v}

def azzera_tentativi(ambito, ident):
    reg = _registro_tentativi()
    with reg["lock"]:
        reg["voci"].pop(f"id|{ambito}|{str(ident).strip().lower()}", None)

def testo_attesa(secondi):
    minuti = max(1, round(secondi / 60))
    return f"Troppi tentativi. Per sicurezza riprova tra {minuti} minut{'o' if minuti == 1 else 'i'}."

# ---------------------------------------------------------------------------
# EMAIL (codici di attivazione e recupero password) e impostazioni del titolare
# ---------------------------------------------------------------------------
def _cfg(nome, predefinito=""):
    try:
        return str(st.secrets.get(nome, predefinito) or predefinito).strip()
    except Exception:
        return predefinito

def email_configurata():
    try:
        cfg = st.secrets["smtp"]
        return bool(cfg.get("host") and cfg.get("user") and cfg.get("password"))
    except Exception:
        return False

def _host_richiesta():
    try:
        h = st.context.headers
        return str(h.get("X-Forwarded-Host") or h.get("Host") or "").split(",")[0].split(":")[0].strip().lower()
    except Exception:
        return "?"

def _host_locale(host):
    """True per localhost e indirizzi di casa (prove in rete locale); False per qualunque nome di sito pubblico. Host assente: prova locale."""
    if not host:
        return True
    return bool(host in ("localhost", "::1") or host.endswith(".local") or re.fullmatch(r"(127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)", host))

def modalita_prova():
    """Solo per le prove: mostra a schermo i codici al posto dell'email. Funziona SOLO da localhost o dalla rete di casa:
    sul sito pubblico è spenta anche se resta accesa per errore nelle impostazioni (altrimenti chiunque potrebbe rubare un account)."""
    try:
        return bool(st.secrets.get("modalita_prova", False)) and _host_locale(_host_richiesta())
    except Exception:
        return False

def contatto_assistenza():
    return _cfg("assistenza_email") or _cfg("titolare_email")

def invia_email(destinatario, oggetto, testo, allegato=None, nome_allegato="allegato.pdf", rispondi_a=None, html=None):
    try:
        cfg = st.secrets["smtp"]
        msg = EmailMessage()
        msg["Subject"] = oggetto
        msg["From"] = cfg.get("from", cfg["user"])
        msg["To"] = destinatario
        if rispondi_a:
            msg["Reply-To"] = rispondi_a
        msg.set_content(testo)
        if html:
            msg.add_alternative(html, subtype="html")          # versione con pulsante cliccabile; il testo semplice resta per chi non vede l'HTML
        if allegato:
            msg.add_attachment(allegato, maintype="application", subtype="pdf", filename=nome_allegato)
        porta = int(cfg.get("port", 465))
        if porta == 587:
            with smtplib.SMTP(cfg["host"], porta, timeout=15) as srv:
                srv.starttls(); srv.login(cfg["user"], cfg["password"]); srv.send_message(msg)
        else:
            with smtplib.SMTP_SSL(cfg["host"], porta, timeout=15) as srv:
                srv.login(cfg["user"], cfg["password"]); srv.send_message(msg)
        return True
    except Exception:
        return False

def invia_email_attivazione(destinatario, nome, codice):
    return invia_email(destinatario, "Il tuo codice di attivazione PetHealth",
                       f"Ciao {nome},\n\nil tuo codice di attivazione PetHealth è: {codice}\nÈ valido 15 minuti.\n\nSe non hai richiesto tu la registrazione ignora questo messaggio.")

def invia_email_reset(destinatario, nome, codice):
    return invia_email(destinatario, "Recupero password PetHealth",
                       f"Ciao {nome},\n\nil tuo codice per scegliere una nuova password è: {codice}\nÈ valido 15 minuti e si può usare una volta sola.\n\n"
                       "Se non l'hai richiesto tu, ignora questo messaggio: la tua password non è stata cambiata.")

# --- codici per il recupero password (salvati solo come impronta, mai in chiaro) ---
def _hash_codice_reset(ident, codice):
    return hmac.new(_chiave_sigillo(), f"reset|{ident}|{codice}".encode("utf-8"), hashlib.sha256).hexdigest()

def emetti_codice_reset(rec, ident):
    codice = f"{secrets.randbelow(10 ** 6):06d}"
    rec["reset_pw"] = {"h": _hash_codice_reset(ident, codice),
                       "scad": (datetime.now() + timedelta(minutes=15)).isoformat(timespec="seconds"), "tent": 0}
    return codice

def controlla_codice_reset(rec, ident, codice):
    """(True, "") se il codice è giusto; altrimenti (False, messaggio)."""
    r = rec.get("reset_pw") or {}
    generico = "Codice non valido o scaduto: richiedine uno nuovo."
    if not r:
        return False, generico
    try:
        scaduto = datetime.now() > datetime.fromisoformat(r.get("scad", ""))
    except Exception:
        scaduto = True
    if scaduto or r.get("tent", 0) >= 5:
        rec.pop("reset_pw", None)
        return False, generico
    if not hmac.compare_digest(_hash_codice_reset(ident, str(codice).strip()), r.get("h", "")):
        r["tent"] = r.get("tent", 0) + 1
        return False, "Codice non corretto."
    return True, ""

def richiedi_reset_proprietario(email_c):
    """Se l'account esiste e non è in attesa, manda il codice. All'utente la risposta è sempre la stessa."""
    _chiave_sigillo()          # prima la chiave (se serve la crea e salva), poi si lavora sull'account
    u = st.session_state.db_users.get(email_c)
    if not u or u.get("stato") == "in_attesa":
        return
    codice = emetti_codice_reset(u, email_c)
    salva_dati(extra_email=email_c)
    invia_email_reset(email_c, u.get("nome", ""), codice)
    return codice

# ---------------------------------------------------------------------------
# ACCOUNT: esportazione dati, eliminazione definitiva
# ---------------------------------------------------------------------------
VERSIONE_INFORMATIVA = "2026-10-17"



def pulisci_account_non_attivati(giorni=7):
    """Toglie dall'archivio gli account che non hanno mai inserito il codice di attivazione entro `giorni` giorni. Gira al massimo ogni 6 ore."""
    reg = _registro_tentativi()
    ora = datetime.now().timestamp()
    ultima = reg.get("ultima_pulizia", 0)
    if not isinstance(ultima, (int, float)):
        ultima = 0
    if ora - ultima < 6 * 3600:
        return 0
    reg["ultima_pulizia"] = ora
    limite = str(date.today() - timedelta(days=giorni))
    tolti = 0
    with _lock_disco():
        su = carica_dati() or {}
        utenti = su.get("users", {}) or {}
        vecchi = [e for e, u in utenti.items() if u.get("stato") == "in_attesa" and str(u.get("data_registrazione", "9999")) < limite]
        for e in vecchi:
            utenti.pop(e, None); tolti += 1
        if tolti:
            _scrivi_archivio(su)
    for e in list(st.session_state.get("db_users", {})):
        u = st.session_state.db_users.get(e) or {}
        if u.get("stato") == "in_attesa" and str(u.get("data_registrazione", "9999")) < limite:
            st.session_state.db_users.pop(e, None)
    return tolti

def account_eliminato_su_disco(email):
    return sigla_email(email) in ((carica_dati() or {}).get("eliminati", {}) or {})

def riabilita_email(email):
    """Chi si è cancellato può registrarsi di nuovo con la stessa email."""
    su_disco = carica_dati()
    if su_disco and sigla_email(email) in (su_disco.get("eliminati", {}) or {}):
        su_disco["eliminati"].pop(sigla_email(email), None)
        _scrivi_archivio(su_disco)

def elimina_account_definitivo(email):
    with _lock_disco():
        return _elimina_account_interno(email)

def _elimina_account_interno(email):
    su_disco = carica_dati() or {}
    utenti = dict(su_disco.get("users", {}) or {})
    try:
        elimina_file_referti_utente(utenti.get(email) or {})
    except Exception:
        pass
    utenti.pop(email, None)
    for _u2 in utenti.values():                                  # esce dalle famiglie a cui partecipava
        _f2 = _u2.get("famiglia") or {}
        (_f2.get("membri") or {}).pop(email, None)
        (_f2.get("inviti") or {}).pop(email, None)
    richieste = {t: r for t, r in (su_disco.get("richieste_firma", {}) or {}).items() if r.get("email_owner") != email}
    eliminati = dict(su_disco.get("eliminati", {}) or {})
    eliminati[sigla_email(email)] = str(date.today())
    _scrivi_archivio({"users": utenti, "db_veterinari": su_disco.get("db_veterinari", {}) or {}, "richieste_firma": richieste,
                      "chiave_sigillo": su_disco.get("chiave_sigillo") or st.session_state.get("chiave_sigillo"), "eliminati": eliminati})
    st.session_state.db_users.pop(email, None)
    st.session_state["richieste_firma"] = richieste

def esporta_dati_utente(email, u):
    escluse = {"password", "codice_conferma", "codice_scadenza", "reset_pw", "sessioni_dispositivo"}
    pacchetto = {"esportato_il": datetime.now().isoformat(timespec="seconds"), "servizio": "PetHealth", "email": email,
                 "dati": {k: v for k, v in u.items() if k not in escluse}, }
    return json.dumps(pacchetto, ensure_ascii=False, indent=2).encode("utf-8")


# ---------------------------------------------------------------------------
# PAGINE LEGALI E AIUTO (pubbliche) + SEZIONE «ACCOUNT, PRIVACY E AIUTO» (per chi ha fatto l'accesso)
# I dati del titolare si impostano nei Secrets: titolare_nome, titolare_indirizzo, titolare_email, titolare_piva, assistenza_email
# ---------------------------------------------------------------------------
def _titolare():
    return {
        "nome": _cfg("titolare_nome") or "[nome del titolare: da compilare nei Secrets]",
        "indirizzo": _cfg("titolare_indirizzo") or "[indirizzo: da compilare nei Secrets]",
        "email": _cfg("titolare_email") or _cfg("assistenza_email") or "[email: da compilare nei Secrets]",
        "piva": _cfg("titolare_piva"),
    }

def testo_privacy():
    t = _titolare()
    piva = f" · P.IVA / C.F. {t['piva']}" if t["piva"] else ""
    return f"""
**Versione {VERSIONE_INFORMATIVA}** · Informativa ai sensi degli artt. 13-14 del Regolamento UE 2016/679 (GDPR)

### 1. Chi tratta i tuoi dati
Titolare del trattamento: **{t['nome']}**{piva}, {t['indirizzo']}. Contatto privacy: **{t['email']}**.

### 2. Quali dati raccogliamo
- **Account**: nome e cognome, indirizzo email, numero di cellulare, password (conservata solo in forma cifrata, non leggibile da nessuno).
- **Libretto dei tuoi animali**: anagrafica, microchip, visite, vaccini, terapie, peso, fatture, foto e documenti che carichi tu.
- **Segnalazioni di animale smarrito** (solo se le fai tu): i dati dell'animale, l'ultimo luogo in cui è stato visto e i soli contatti che scegli di mostrare. In più, la **provincia** che indichi nel tuo profilo.
- **Dati tecnici**: un cookie tecnico che ti mantiene connesso su un dispositivo, e, solo se la attivi tu, una copia di sola lettura del libretto salvata nel dispositivo per consultarlo senza internet (si cancella quando esci), l'iscrizione alle notifiche (se la attivi) e i registri tecnici del server (indirizzo di rete, orario), necessari a sicurezza e funzionamento.

Il libretto riguarda gli **animali**, ma contiene comunque dati personali tuoi (ad esempio le spese e i recapiti). Ti chiediamo di non inserire dati sanitari tuoi o di altre persone.

### 3. Perché li usiamo e su quale base
- Creare e gestire il tuo account e il libretto, inviarti i promemoria: **esecuzione del servizio che hai richiesto** (art. 6.1.b GDPR).
- Inviarti le **notifiche** sul telefono: **il tuo consenso** (art. 6.1.a), che dai attivandole e puoi revocare in ogni momento.
- Pubblicare la tua segnalazione di animale smarrito e avvisare gli utenti della provincia: **il tuo consenso** (art. 6.1.a), dato inviando la segnalazione. La segnalazione resta visibile fino a quando premi «Ritrovato» (o per 90 giorni al massimo). Puoi scegliere di non ricevere gli avvisi degli altri dalla sezione «Animale smarrito».
- Sicurezza, prevenzione degli abusi e dei tentativi di accesso non autorizzato: **legittimo interesse** (art. 6.1.f).
- Obblighi di legge, se previsti: art. 6.1.c.

Non vendiamo i tuoi dati e non li usiamo per pubblicità o profilazione.

### 4. Con chi li condividiamo
- **Le persone che inviti** (familiari), che vedono e aggiornano i tuoi libretti; e **chiunque riceva un link per il veterinario o inquadri il QR di un animale** che crei tu, limitatamente ai dati che scegli di rendere visibili. Puoi revocare inviti e link in ogni momento.
- **Servizio di controllo delle password violate** (Have I Been Pwned): quando scegli una password, riceve solo un frammento anonimo di 5 caratteri della sua impronta, da cui non può ricostruirla né sapere chi sei.
- **Fornitori tecnici** che ci permettono di far funzionare il servizio (collegamento internet e protezione del sito, invio delle email, servizi di notifica dei produttori dei telefoni). Operano come responsabili del trattamento e, se hanno sede fuori dallo Spazio Economico Europeo, con le garanzie previste dal GDPR (ad esempio clausole contrattuali standard).
- Autorità, solo se la legge lo impone.

### 5. Quanto li conserviamo
Finché mantieni l'account. Quando lo elimini (sezione «Account, privacy e aiuto») i dati vengono cancellati subito dal servizio; le eventuali copie di sicurezza vengono sovrascritte entro 30 giorni. Gli account inattivi per lungo tempo possono essere eliminati dopo un avviso via email.

### 6. I tuoi diritti
Puoi in ogni momento **accedere** ai dati, **scaricarli** in formato leggibile (portabilità), **correggerli**, **cancellarli**, **limitarne** o **opporti** al trattamento. Esportazione ed eliminazione sono disponibili da soli nella sezione «Account, privacy e aiuto»; per tutto il resto scrivi a **{t['email']}**. Se ritieni che i tuoi diritti non siano rispettati puoi proporre reclamo al **Garante per la protezione dei dati personali** (www.garanteprivacy.it).

### 7. Sicurezza
Password cifrate, collegamento protetto (HTTPS), limite ai tentativi di accesso, codici di recupero a tempo, accesso ai dati limitato a chi è autorizzato. Nessun sistema è sicuro al 100%: se dovesse verificarsi una violazione che ti riguarda, ti avviseremo come previsto dalla legge.

### 8. Età minima
Il servizio è riservato a persone che hanno compiuto 18 anni.

*Questa informativa può essere aggiornata: la versione in vigore è sempre quella di questa pagina e le modifiche rilevanti ti saranno comunicate.*
"""

def testo_termini():
    t = _titolare()
    return f"""
**Versione {VERSIONE_INFORMATIVA}**

### 1. Che cos'è PetHealth
PetHealth è un **libretto sanitario digitale** in cui tieni in ordine vaccini, visite, terapie, peso e spese dei tuoi animali e ricevi promemoria. Il servizio è gestito da **{t['nome']}** ({t['indirizzo']}).

### 2. Che cosa PetHealth non è
- **Non è un servizio veterinario** e non fornisce diagnosi, cure o consigli medici. Per ogni decisione sulla salute del tuo animale rivolgiti a un veterinario.
- Il libretto digitale è compilato da te: **non sostituisce** il passaporto europeo per animali da compagnia, il libretto cartaceo o altri documenti ufficiali richiesti dalla legge, da autorità o per i viaggi.

### 3. Promemoria e notifiche
I promemoria (richiami, terapie) sono un **aiuto**, non una garanzia: possono non arrivare o arrivare in ritardo per cause tecniche, impostazioni del telefono, mancanza di rete o dati inseriti in modo errato. Resta tua la responsabilità di rispettare date e dosi indicate dal veterinario.

### 4. Il tuo account
Devi avere almeno 18 anni, fornire dati veritieri e custodire la password. Sei responsabile delle attività svolte con il tuo account. Puoi eliminarlo in qualsiasi momento dalla sezione «Account, privacy e aiuto».

### 5. Contenuti che inserisci
I dati e i documenti che carichi restano tuoi. Ci autorizzi a conservarli e mostrarli solo per far funzionare il servizio. Non caricare contenuti illeciti, che violino diritti di altri o che contengano malware.

### 6. Uso corretto
Non è consentito tentare di accedere ad account altrui, aggirare i limiti di sicurezza, sovraccaricare il servizio o usarlo per attività illecite. Possiamo sospendere gli account che violano queste regole.

### 7. Disponibilità e responsabilità
Facciamo il possibile perché il servizio sia sempre disponibile e i dati al sicuro, ma può essere interrotto per manutenzione o guasti. Nei limiti consentiti dalla legge, non rispondiamo di danni indiretti o derivanti da mancata o ritardata ricezione dei promemoria, da dati inseriti in modo errato o da decisioni prese sulla base delle informazioni nell'app. Restano ferme le tutele inderogabili previste dalla legge per i consumatori.

### 8. Modifiche
Possiamo aggiornare questi termini; le modifiche rilevanti ti saranno comunicate. Continuando a usare il servizio accetti la versione aggiornata.

### 9. Legge applicabile
Si applica la legge italiana. Per i consumatori resta competente il foro del luogo di residenza o domicilio.

### 10. Contatti
**{t['email']}**
"""

def testo_aiuto():
    c = contatto_assistenza() or "[email assistenza: da compilare nei Secrets]"
    return f"""
### Domande frequenti

**Ho dimenticato la password.**
Nella pagina di accesso apri «Password dimenticata?», scrivi la tua email: ti arriva un codice a 6 cifre, valido 15 minuti, con cui scegli una nuova password.

**Non mi arriva l'email con il codice.**
Controlla la cartella spam/promozioni. Se dopo qualche minuto non c'è, richiedi un nuovo codice (massimo 5 richieste ogni 15 minuti) o scrivici a **{c}**.

**Come ricevo le notifiche sul telefono?**
Apri il menù → «App e notifiche». Su iPhone l'app va prima aggiunta alla schermata Home (Condividi → Aggiungi a Home), poi si attivano le notifiche da lì.

**Posso vedere il libretto senza internet?**
Sì, in sola lettura. Menù → «App e notifiche» → «Libretto senza internet», da attivare una volta su ogni dispositivo con la connessione attiva. Poi, se manca la rete, l'app mostra la copia salvata (con la data dell'ultimo aggiornamento). Non puoi modificare nulla finché non torna internet. Su iPhone aggiungi prima l'app alla schermata Home. Uscendo dall'account la copia viene cancellata dal dispositivo.

**I promemoria dei richiami e delle terapie quando arrivano?**
Richiami: 2 giorni prima, dalle 9:00. Terapie: 10 minuti prima di ogni somministrazione. Compaiono solo se hai attivato la casella del richiamo o impostato la notifica sulla terapia.

**Che valore ha il libretto digitale?**
È un archivio che compili tu, utile da consultare e da mostrare al veterinario. Non sostituisce il passaporto europeo o i documenti ufficiali.

**Come scarico i miei dati?**
Menù → «Account, privacy e aiuto» → scheda Account → «Scarica i miei dati».

**Come condivido il libretto con un familiare o con il veterinario?**
Menù → «Condivisione e QR». Con «Famiglia» inviti una persona (vede e aggiorna i tuoi libretti); con «Per il veterinario» crei un link temporaneo di sola lettura.

**Dove trovo il QR per la medaglietta?**
Menù → «Animale smarrito» → scheda «Medaglietta QR»: crei la scheda, scarichi il QR da stampare e, se l'animale si perde, lo segni come smarrito.

**Come segnalo un animale smarrito?**
Menù → «Animale smarrito» → «Segnala smarrimento». Scegli i contatti da mostrare e l'ultimo luogo in cui l'hai visto: la segnalazione compare a tutti gli utenti e chi è nella provincia indicata riceve una notifica. Quando lo ritrovi premi «Ritrovato» e l'avviso sparisce per tutti.

**Come elimino il mio account?**
Stessa sezione: richiede la password e la parola ELIMINA. L'eliminazione è definitiva.

**Contatti**
Per qualsiasi problema scrivici a **{c}**: rispondiamo appena possibile.
"""

_TITOLI_PAGINE = {"privacy": "Informativa sulla privacy", "termini": "Termini di utilizzo", "aiuto": "Aiuto e domande frequenti"}

def mostra_testo_legale(pagina):
    st.markdown({"privacy": testo_privacy, "termini": testo_termini, "aiuto": testo_aiuto}[pagina]())

def mostra_pagina_pubblica(pagina):
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],[data-testid='stExpandSidebarButton'],"
                "[data-testid='collapsedControl']{display:none !important}</style>", unsafe_allow_html=True)
    st.markdown('<div style="padding:4px 0 18px 0">' + logo_html() + '</div>', unsafe_allow_html=True)
    st.markdown(f"## {_TITOLI_PAGINE[pagina]}")
    mostra_testo_legale(pagina)
    st.markdown('<hr><a href="./" target="_self">← Torna a PetHealth</a> · <a href="?pagina=privacy" target="_self">Privacy</a> · '
                '<a href="?pagina=termini" target="_self">Termini</a> · <a href="?pagina=aiuto" target="_self">Aiuto</a>', unsafe_allow_html=True)

def link_legali_html():
    return ('<div style="text-align:center;font-size:0.85rem;margin-top:14px">'
            '<a href="?pagina=privacy" target="_blank">Privacy</a> · <a href="?pagina=termini" target="_blank">Termini</a> · '
            '<a href="?pagina=aiuto" target="_blank">Aiuto</a></div>')

# ---------------------------------------------------------------------------
# VERIFICA IN DUE PASSAGGI (TOTP, standard RFC 6238: Google Authenticator, Microsoft Authenticator, Authy, 1Password...)
# ---------------------------------------------------------------------------
def totp_nuovo_segreto():
    return base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")

def _totp_codice(segreto, contatore):
    chiave = base64.b32decode(str(segreto).upper() + "=" * (-len(str(segreto)) % 8))
    h = hmac.new(chiave, struct.pack(">Q", int(contatore)), "sha1").digest()
    o = h[-1] & 15
    return f"{(struct.unpack('>I', h[o:o + 4])[0] & 0x7FFFFFFF) % 1_000_000:06d}"

def totp_verifica(t, codice, adesso=None):
    """Codice a 6 cifre valido (30 secondi, tolleranza di un passo) e MAI già usato: un codice spiato non si può riutilizzare."""
    c = re.sub(r"\s", "", str(codice or ""))
    if not isinstance(t, dict) or not t.get("segreto") or not re.fullmatch(r"\d{6}", c):
        return False
    passo = int((adesso if adesso is not None else datetime.now().timestamp()) // 30)
    for d in (0, -1, 1):
        k = passo + d
        if k > int(t.get("ultimo", -1)) and hmac.compare_digest(_totp_codice(t["segreto"], k), c):
            t["ultimo"] = k
            return True
    return False

def _impronta_recupero(codice):
    return hashlib.sha256(re.sub(r"[^0-9a-f]", "", str(codice).lower()).encode("ascii")).hexdigest()

def totp_nuovi_codici_recupero(t):
    """8 codici monouso per quando non si ha il telefono. In archivio restano solo le impronte."""
    codici = [secrets.token_hex(6) for _ in range(8)]
    t["recupero"] = [_impronta_recupero(c) for c in codici]
    return [f"{c[:6]}-{c[6:]}" for c in codici]

def totp_usa_recupero(t, codice):
    if not isinstance(t, dict) or not re.fullmatch(r"[0-9a-fA-F]{6}[-\s]?[0-9a-fA-F]{6}", str(codice or "").strip()):
        return False
    imp = _impronta_recupero(codice)
    for x in list(t.get("recupero") or []):
        if hmac.compare_digest(x, imp):
            t["recupero"].remove(x)
            return True
    return False

def totp_attivo(u):
    t = (u.get("totp") if isinstance(u, dict) else None) or {}
    return bool(t.get("attivo") and (t.get("segreto") or t.get("metodo") == "email"))

def totp_metodo(u):
    """'email' = il codice arriva per email; 'app' = app di autenticazione (Google Authenticator ecc.)."""
    return "email" if isinstance(u, dict) and (u.get("totp") or {}).get("metodo") == "email" else "app"

def _email_mascherata(e):
    nome, _, dom = str(e).partition("@")
    return (nome[:1] + "***@" + dom) if dom else "la tua email"

def _hash_codice_2fa(email, codice):
    return hmac.new(_chiave_sigillo(), f"2fa-email|{str(email).strip().lower()}|{codice}".encode("utf-8"), hashlib.sha256).hexdigest()

def invia_codice_2fa(email, nome=""):
    """Manda per email un codice a 6 cifre (10 minuti, una volta sola). Ritorna (pratica, errore): la pratica va tenuta nella sessione, in archivio non resta nulla."""
    attesa = secondi_blocco("totp-invio", email)
    if attesa:
        return None, testo_attesa(attesa)
    if not email_configurata() and not modalita_prova():
        return None, "L'invio dell'email non è al momento disponibile. Usa un codice di recupero oppure scrivi all'assistenza."
    codice = f"{secrets.randbelow(10 ** 6):06d}"
    registra_fallimento("totp-invio", email)                      # conta ogni invio: nessuno può usarci per riempire una casella
    if modalita_prova():
        st.info(f"[PROVA] Codice: {codice}")
    elif not invia_email(email, "Il tuo codice di accesso PetHealth",
                         f"Ciao {nome or ''},\n\nil tuo codice di verifica PetHealth è: {codice}\nÈ valido 10 minuti e si può usare una volta sola.\n\n"
                         "Se non stai accedendo o attivando la sicurezza tu, qualcuno conosce la tua password: cambiala subito dalle impostazioni."):
        return None, "Non sono riuscito a inviare l'email. Riprova tra poco oppure usa un codice di recupero."
    ora = datetime.now().timestamp()
    return {"h": _hash_codice_2fa(email, codice), "scade": ora + 600, "invio": ora}, None

def codice_email_ok(pratica, email, codice):
    c = re.sub(r"\s", "", str(codice or ""))
    if not isinstance(pratica, dict) or not re.fullmatch(r"\d{6}", c) or datetime.now().timestamp() > float(pratica.get("scade", 0)):
        return False
    return hmac.compare_digest(str(pratica.get("h", "")), _hash_codice_2fa(email, c))

def _secondo_fattore_ok(t, email, codice, pratica=None, ammetti_recupero=True):
    """Codice giusto per questo account, qualunque sia il metodo scelto (app o email)."""
    if (t or {}).get("metodo") == "email":
        if codice_email_ok(pratica, email, codice):
            return True
    elif totp_verifica(t, codice):
        return True
    return bool(ammetti_recupero and totp_usa_recupero(t, codice))

def _dispositivo_mobile():
    """True se la pagina e' aperta da telefono/tablet (Android, iPhone, iPad). Il computer e gli altri casi dubbi restano 'desktop'."""
    try:
        ua = str(st.context.headers.get("User-Agent") or "").lower()
    except Exception:
        return False
    return any(x in ua for x in ("android", "iphone", "ipad", "ipod", "mobile"))

def _png_qr(testo):
    try:
        import qrcode
        b = io.BytesIO()
        qrcode.make(testo).convert("RGB").resize((420, 420), Image.NEAREST).save(b, format="PNG")
        return b.getvalue()
    except Exception:
        return None

def completa_accesso(email, ricorda):
    st.session_state.logged_user_email = email
    st.session_state.sezione_attiva = "dashboard"
    st.session_state.ph_no_autologin = False
    if ricorda:
        st.session_state.ph_cookie_scrivi = crea_sessione_dispositivo(email)
    log_sicurezza("accesso", email)
    salva_dati()
    st.rerun()

def mostra_login_2fa(p2):
    """Secondo passaggio dell'accesso: la password era giusta, ora serve il codice dell'app di autenticazione (o un codice di recupero)."""
    email = p2.get("email", "")
    st.markdown("#### 🛡️ Verifica in due passaggi")
    rec0 = st.session_state.db_users.get(email) or {}
    per_email = totp_metodo(rec0) == "email"
    if per_email:
        if p2.get("errore_invio"):
            st.error(p2["errore_invio"])
        else:
            st.caption(f"Ti abbiamo mandato un codice a 6 cifre a {_email_mascherata(email)}. Controlla la posta (anche lo spam) e scrivilo qui. "
                       "Vale 10 minuti.")
    else:
        st.caption("Apri l'app di autenticazione sul telefono e scrivi il codice a 6 cifre di PetHealth. "
                   "Se non hai il telefono usa uno dei codici di recupero (formato abcdef-123456).")
    with st.form("form_login_2fa"):
        cod = st.text_input("Codice", max_chars=14, placeholder="123456", autocomplete="one-time-code")
        conferma = st.form_submit_button("Conferma e accedi")
    if conferma:
        attesa = secondi_blocco("totp", email)
        rec = st.session_state.db_users.get(email)
        if attesa:
            st.error(testo_attesa(attesa))
        elif rec and totp_attivo(rec) and _secondo_fattore_ok(rec["totp"], email, cod, p2.get("pratica")):
            azzera_tentativi("totp", email)
            salva_dati(extra_email=email)                 # registra il codice usato: non vale una seconda volta
            st.session_state.pop("login_2fa", None)
            completa_accesso(email, bool(p2.get("ricorda")))
        else:
            registra_fallimento("totp", email)
            st.error("Codice non corretto o già usato. Controlla l'ora del telefono e riprova.")
    if per_email and st.button("Invia di nuovo il codice", key="login_2fa_reinvia"):
        vecchia = p2.get("pratica") or {}
        if datetime.now().timestamp() - float(vecchia.get("invio", 0)) < 60:
            st.info("Attendi un minuto prima di chiedere un nuovo codice.")
        else:
            p2["pratica"], p2["errore_invio"] = invia_codice_2fa(email, rec0.get("nome", ""))
            p2["quando"] = datetime.now().timestamp()
            st.rerun()
    if st.button("← Torna all'accesso", key="login_2fa_indietro"):
        st.session_state.pop("login_2fa", None)
        st.rerun()

def chiudi_altri_dispositivi(email):
    """Alla attivazione della verifica in due passaggi: tutti gli altri dispositivi già collegati (telefoni, computer)
    devono rifare l'accesso, così da subito anche loro chiedono il secondo codice. Questo dispositivo resta collegato."""
    mio_jti = st.session_state.get("ph_jti")
    try:
        _aggiorna_sessioni(email, lambda s_: [s_.pop(k) for k in [k for k in s_ if k != mio_jti]])
    except Exception:
        pass

def mostra_2fa_account(email, u, titolo=True):
    if titolo:
        st.markdown("#### 🛡️ Verifica in due passaggi")
    t = u.get("totp") or {}
    nuovi = st.session_state.get(f"totp_codici_mostra_{email}")
    if nuovi:
        st.warning("**Salva subito questi codici di recupero** (screenshot, gestore di password o carta in un posto sicuro). "
                   "Ognuno vale una volta sola e ti serve se perdi il telefono. Non verranno mostrati di nuovo.")
        st.info("La verifica vale per **tutti** i tuoi dispositivi, telefono e computer. Quelli già collegati dovranno rifare l'accesso e useranno anche loro il secondo codice.")
        st.code("\n".join(nuovi), language=None)
        if st.button("Ho salvato i codici", key="totp_codici_ok"):
            st.session_state.pop(f"totp_codici_mostra_{email}", None)
            st.rerun()
    if st.session_state.pop(f"totp_appena_{email}", False):
        st.info("Verifica attivata. Vale per **tutti** i tuoi dispositivi, telefono e computer: quelli già collegati dovranno rifare l'accesso e riceveranno il codice per email.")
    if totp_attivo(u):
        per_email = totp_metodo(u) == "email"
        chiave_p = f"totp_email_acc_{email}"
        if per_email:
            st.success(f"Attiva. All'accesso ti mandiamo un codice per email a {_email_mascherata(email)}. La verifica vale per tutti i tuoi dispositivi.")
            st.caption("Per disattivarla ti serve la password e un codice: tocca il pulsante, poi scrivi il codice che ricevi per email.")
            if st.button("📧 Inviami un codice per email", key="totp_acc_invia"):
                vecchia = st.session_state.get(chiave_p) or {}
                if datetime.now().timestamp() - float(vecchia.get("invio", 0)) < 60:
                    st.info("Attendi un minuto prima di chiedere un nuovo codice.")
                else:
                    pr, err = invia_codice_2fa(email, u.get("nome", ""))
                    if err:
                        st.error(err)
                    else:
                        st.session_state[chiave_p] = pr
                        st.success("Codice inviato: controlla la tua email.")
        else:
            st.success(f"Attiva. All'accesso serve anche il codice dell'app di autenticazione. Codici di recupero rimasti: {len(t.get('recupero') or [])}.")
        with (st.form("form_totp_rigenera") if not per_email else st.container()):
            c1 = "" if per_email else st.text_input("Codice dell'app per creare nuovi codici di recupero", max_chars=8, key="totp_rig_cod")
            if per_email:
                pass
            elif st.form_submit_button("Genera nuovi codici di recupero"):
                attesa = secondi_blocco("totp", email)
                if attesa:
                    st.error(testo_attesa(attesa))
                elif _secondo_fattore_ok(t, email, c1, st.session_state.get(chiave_p), ammetti_recupero=False):
                    st.session_state[f"totp_codici_mostra_{email}"] = totp_nuovi_codici_recupero(t)
                    salva_dati(); log_sicurezza("2fa_codici_rigenerati", email); st.rerun()
                else:
                    registra_fallimento("totp", email); st.error("Codice non corretto.")
        with st.form("form_totp_off"):
            pw = st.text_input("Password", type="password", key="totp_off_pw")
            c2 = st.text_input("Codice ricevuto per email" if per_email else "Codice dell'app (o di recupero)", max_chars=14, key="totp_off_cod")
            if st.form_submit_button("Disattiva la verifica in due passaggi"):
                attesa = secondi_blocco("totp", email)
                if attesa:
                    st.error(testo_attesa(attesa))
                elif verifica_password(pw, u.get("password", "")) and _secondo_fattore_ok(t, email, c2, st.session_state.get(chiave_p)):
                    u.pop("totp", None)
                    salva_dati(); log_sicurezza("2fa_disattivata", email)
                    st.success("Verifica in due passaggi disattivata."); st.rerun()
                else:
                    registra_fallimento("totp", email); st.error("Password o codice non corretti.")
        return
    st.caption("Con la password, un hacker potrebbe entrare nel tuo account se la scopre. Con la verifica in due passaggi, a ogni accesso serve anche un codice che "
               "ogni volta ti arriva per email. È la protezione più efficace che esista per un account. "
               "La attivi una volta sola, da qualsiasi dispositivo: vale in automatico per tutti i tuoi dispositivi, telefoni e computer.")
    seg = st.session_state.get(f"totp_nuovo_segreto_{email}")
    chiave_att = f"totp_email_att_{email}"
    pratica = st.session_state.get(chiave_att)
    if pratica and not seg:
        st.markdown(f"Ti abbiamo mandato un codice a 6 cifre a **{_email_mascherata(email)}**. Controlla la posta (anche lo spam) e scrivilo qui sotto. Vale 10 minuti.")
        with st.form("form_totp_email_on"):
            ce = st.text_input("Codice ricevuto per email", max_chars=8, key="totp_email_cod")
            if st.form_submit_button("Conferma e attiva"):
                attesa = secondi_blocco("totp", email)
                if attesa:
                    st.error(testo_attesa(attesa))
                elif codice_email_ok(pratica, email, ce):
                    azzera_tentativi("totp", email)
                    nuovo = {"attivo": True, "metodo": "email", "attivata": str(date.today())}
                    u["totp"] = nuovo
                    st.session_state.pop(chiave_att, None)
                    salva_dati(); log_sicurezza("2fa_attivata_email", email); chiudi_altri_dispositivi(email)
                    st.session_state[f"totp_appena_{email}"] = True; st.rerun()
                else:
                    registra_fallimento("totp", email); st.error("Codice non corretto o scaduto. Controlla l'email più recente.")
        c_a, c_b = st.columns(2)
        with c_a:
            if st.button("Invia di nuovo il codice", key="totp_email_reinvia", use_container_width=True):
                if datetime.now().timestamp() - float(pratica.get("invio", 0)) < 60:
                    st.info("Attendi un minuto prima di chiedere un nuovo codice.")
                else:
                    pr, err = invia_codice_2fa(email, u.get("nome", ""))
                    if err:
                        st.error(err)
                    else:
                        st.session_state[chiave_att] = pr; st.rerun()
        with c_b:
            if st.button("Annulla", key="totp_email_annulla", use_container_width=True):
                st.session_state.pop(chiave_att, None); st.rerun()
        return
    if not seg:
        if _dispositivo_mobile():
            if st.button("🛡️ Attiva la verifica in due passaggi", key="totp_avvia_email", use_container_width=True):
                pr, err = invia_codice_2fa(email, u.get("nome", ""))
                if err:
                    st.error(err)
                else:
                    st.session_state[chiave_att] = pr; st.rerun()
        elif st.button("🛡️ Attiva la verifica in due passaggi", key="totp_avvia_email", use_container_width=True):
            pr, err = invia_codice_2fa(email, u.get("nome", ""))
            if err:
                st.error(err)
            else:
                st.session_state[chiave_att] = pr; st.rerun()
        return
    uri = f"otpauth://totp/PetHealth:{urllib.parse.quote(email)}?secret={seg}&issuer=PetHealth&algorithm=SHA1&digits=6&period=30"
    chiave_leggibile = " ".join(seg[i:i + 4] for i in range(0, len(seg), 4))
    if _dispositivo_mobile():
        # Dal telefono non si puo' inquadrare il QR che si ha sullo stesso schermo: niente QR, ma il pulsante che apre l'app
        # di autenticazione gia' compilata e, in alternativa, la chiave da copiare e incollare.
        st.markdown("**1.** Installa un'app di autenticazione (Google Authenticator, Microsoft Authenticator, Authy, 1Password) se non l'hai già.")
        st.markdown("**2.** Tocca il pulsante: si apre l'app e aggiunge PetHealth da sola.")
        try:
            st.link_button("🔐 Apri nell'app di autenticazione", uri, use_container_width=True)
        except Exception:
            pass
        st.caption("Se il pulsante non apre l'app, fai così: copia la chiave qui sotto con l'icona a destra, apri l'app e scegli "
                   "«Inserisci chiave di configurazione» (o «Inserisci manualmente»). Come nome scrivi PetHealth e incolla la chiave.")
        st.code(chiave_leggibile, language=None)
    else:
        st.markdown("**1.** Installa un'app di autenticazione (Google Authenticator, Microsoft Authenticator, Authy, 1Password) e inquadra questo QR. "
                    "Dal telefono con cui stai guardando lo schermo, copia la chiave qui sotto e incollala nell'app («inserisci chiave di configurazione»).")
        png = _png_qr(uri)
        if png:
            st.image(png, width=220)
        st.code(chiave_leggibile, language=None)
    with st.form("form_totp_on"):
        c0 = st.text_input("**2.** Scrivi il codice a 6 cifre che mostra l'app", max_chars=8, key="totp_on_cod")
        if st.form_submit_button("Conferma e attiva"):
            attesa = secondi_blocco("totp", email)
            nuovo = {"segreto": seg, "ultimo": -1}
            if attesa:
                st.error(testo_attesa(attesa))
            elif totp_verifica(nuovo, c0):
                nuovo["attivo"] = True
                nuovo["attivata"] = str(date.today())
                u["totp"] = nuovo
                st.session_state[f"totp_codici_mostra_{email}"] = totp_nuovi_codici_recupero(nuovo)
                st.session_state.pop(f"totp_nuovo_segreto_{email}", None)
                salva_dati(); log_sicurezza("2fa_attivata", email); chiudi_altri_dispositivi(email); st.rerun()
            else:
                registra_fallimento("totp", email); st.error("Codice non corretto: controlla di aver inquadrato il QR giusto e che l'ora del telefono sia automatica.")
    if st.button("Annulla", key="totp_annulla"):
        st.session_state.pop(f"totp_nuovo_segreto_{email}", None)
        st.rerun()

def mostra_invito_2fa(login_email, profilo):
    """Invito discreto in dashboard finché la verifica in due passaggi non è attiva."""
    if totp_attivo(profilo) or st.session_state.get("totp_invito_chiuso"):
        return
    st.info("🛡️ **Proteggi il tuo account** con la verifica in due passaggi: ci vuole un minuto e rende inutile una password rubata.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Attivala ora", key="totp_invito_ora", use_container_width=True):
            st.session_state["account_scheda"] = "2fa"
            cambia_sezione("account")
    with c2:
        if st.button("Più tardi", key="totp_invito_dopo", use_container_width=True):
            st.session_state["totp_invito_chiuso"] = True
            st.rerun()

def scheda_account(chiave, titolo):
    """Scheda a comparsa della pagina Account: se ne apre una sola alla volta."""
    aperta = st.session_state.get("account_scheda") == chiave
    if st.button(("🔽 " if aperta else "▶️ ") + titolo, key=f"acc_scheda_{chiave}", use_container_width=True):
        st.session_state["account_scheda"] = None if aperta else chiave
        st.rerun()
    return aperta

def mostra_pagina_account(email, u):
    """Dati dell'account: scarica i dati, cambia password, verifica a due fattori, elimina l'account."""
    if True:
        st.markdown(f"**{u.get('nome', '')}** · {email}")
        st.caption("Tocca una scheda per aprirla: si apre una sezione alla volta.")
        if scheda_account("pw", "🔑 Cambia password"):
            with st.form("form_cambia_pw"):
                vecchia = st.text_input("Password attuale", type="password")
                nuova = st.text_input("Nuova password (min. 10 caratteri)", type="password")
                nuova2 = st.text_input("Ripeti la nuova password", type="password")
                if st.form_submit_button("Aggiorna password"):
                    attesa = secondi_blocco("cambia-pw", email)
                    if attesa:
                        st.error(testo_attesa(attesa))
                    elif not verifica_password(vecchia, u.get("password", "")):
                        registra_fallimento("cambia-pw", email)
                        st.error("La password attuale non è corretta.")
                    elif controlla_password_nuova(nuova, email):
                        st.error(controlla_password_nuova(nuova, email))
                    elif nuova != nuova2:
                        st.error("Le due password nuove non coincidono.")
                    else:
                        azzera_tentativi("cambia-pw", email)
                        u["password"] = hash_password(nuova)
                        salva_dati()
                        log_sicurezza("password_cambiata", email)
                        mio_jti = st.session_state.get("ph_jti")
                        _aggiorna_sessioni(email, lambda s: [s.pop(k) for k in [k for k in s if k != mio_jti]])   # gli altri dispositivi devono rifare l'accesso
                        st.success("Password aggiornata. Gli altri dispositivi dovranno rifare l'accesso.")

        if email != "demo@pethealth.it":
            if scheda_account("2fa", "🛡️ Verifica in due passaggi" + (" · attiva" if totp_attivo(u) else " · non attiva")):
                mostra_2fa_account(email, u, titolo=False)

        if scheda_account("dati", "📦 I tuoi dati"):
            st.caption("Scarica una copia completa di tutto ciò che PetHealth conserva sul tuo account, in formato leggibile (JSON).")
            st.download_button("⬇️ Scarica i miei dati", data=esporta_dati_utente(email, u),
                              file_name=f"pethealth-i-miei-dati-{date.today().isoformat()}.json", mime="application/json", key="scarica_dati")

        if scheda_account("elimina", "🗑️ Elimina l'account"):
            if email == "demo@pethealth.it":
                st.info("L'account di prova non può essere eliminato.")
            else:
                st.warning("L'eliminazione è **definitiva**: account, animali, visite, terapie, fatture e documenti vengono cancellati e non si possono recuperare. "
                           "Chi condivide i libretti con te perderà l'accesso. Se vuoi, scarica prima i tuoi dati qui sopra.")
                with st.form("form_elimina_account"):
                    pw = st.text_input("La tua password", type="password", key="elim_pw")
                    conf = st.text_input("Per confermare scrivi ELIMINA", key="elim_conf")
                    if st.form_submit_button("Elimina definitivamente il mio account"):
                        attesa = secondi_blocco("elimina", email)
                        if attesa:
                            st.error(testo_attesa(attesa))
                        elif not verifica_password(pw, u.get("password", "")):
                            registra_fallimento("elimina", email)
                            st.error("Password non corretta.")
                        elif conf.strip().upper() != "ELIMINA":
                            st.error("Scrivi la parola ELIMINA per confermare.")
                        else:
                            elimina_account_definitivo(email)
                            azzera_tentativi("elimina", email)
                            st.session_state.logged_user_email = None
                            st.session_state.verification_pending_email = None
                            st.session_state.ph_no_autologin = True
                            st.session_state.ph_cookie_cancella = True
                            st.session_state.account_eliminato = True
                            st.rerun()

def mostra_sezione_account(email, u):
    st.markdown("<h2 style='color: #1E3A2B;'>🔐 Account, privacy e aiuto</h2>", unsafe_allow_html=True)
    t_acc, t_priv, t_term, t_aiuto = st.tabs(["Account", "Informativa", "Termini", "Aiuto"])
    with t_acc:
        mostra_pagina_account(email, u)
    with t_priv:
        mostra_testo_legale("privacy")
    with t_term:
        mostra_testo_legale("termini")
    with t_aiuto:
        mostra_testo_legale("aiuto")

# ---------------------------------------------------------------------------
# FASE 2: famiglia, link per il veterinario, QR animale smarrito, registro delle dosi
# ---------------------------------------------------------------------------
def _b64e(s):
    return base64.urlsafe_b64encode(str(s).encode("utf-8")).decode("ascii").rstrip("=")

def _b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)).decode("utf-8")

def email_dati():
    """Account che contiene i dati in uso: il proprio o quello di una famiglia a cui si partecipa."""
    return st.session_state.get("account_attivo") or st.session_state.get("logged_user_email")

def ospite_solo_aggiunta():
    """True quando si stanno usando i libretti di un altro (condivisione): chi è ospite può solo AGGIUNGERE
    visite, terapie, pesate, fatture e spese. Non può eliminare né modificare ciò che c'è già."""
    att = st.session_state.get("account_attivo")
    return bool(att and att != st.session_state.get("logged_user_email"))

def _param_url(nome):
    try:
        v = st.query_params.get(nome)
    except Exception:
        return None
    return v if isinstance(v, str) and v else None

def url_invito_famiglia():
    """Indirizzo completo (con https://) che porta direttamente all'invito: funziona anche prima dell'accesso."""
    base = _cfg("app_url").strip().rstrip("/") or "https://pethealthvet.it"
    if not re.match(r"^https?://", base, re.I):
        base = "https://" + base
    return f"{base}/?vai=famiglia"

def url_pubblico(param, token):
    base = _cfg("app_url").rstrip("/")
    return f"{base}/?{param}={token}" if base else f"?{param}={token}"

def _nome_di(email):
    u = st.session_state.db_users.get(email) or {}
    return u.get("nome") or email

def modifica_account_su_disco(email, fn):
    """Legge l'archivio, applica fn(record) a quell'account e riscrive: sicuro anche se un familiare lavora nello stesso momento."""
    with _lock_disco():
        su = carica_dati() or {}
        rec = (su.get("users", {}) or {}).get(email)
        if rec is None:
            return False
        fn(rec)
        _scrivi_archivio(su)
        st.session_state.db_users[email] = rec
    return True

# --------------------------- FAMIGLIA ---------------------------
MAX_FAMILIARI = 5
GIORNI_INVITO = 14

def _scaduto(iso):
    try:
        return datetime.now() > datetime.fromisoformat(str(iso))
    except Exception:
        return True

def famiglie_di(email):
    """[(email_proprietario, nome)] dei libretti a cui `email` partecipa come familiare."""
    su = (carica_dati() or {}).get("users", {}) or {}
    return [(e, u.get("nome") or e) for e, u in su.items()
            if e != email and email in ((u.get("famiglia") or {}).get("membri") or {})]

def inviti_ricevuti(email):
    su = (carica_dati() or {}).get("users", {}) or {}
    out = []
    for e, u in su.items():
        inv = ((u.get("famiglia") or {}).get("inviti") or {}).get(email)
        if inv and not _scaduto(inv.get("scad")):
            out.append((e, u.get("nome") or e))
    return out

def risolvi_account_attivo(login):
    """Quale account contiene i dati che si stanno guardando: il proprio o quello di una famiglia a cui si partecipa."""
    su = (carica_dati() or {}).get("users", {}) or {}
    mio = su.get(login)
    if mio and ((mio.get("famiglia") or {}).get("membri") or (mio.get("famiglia") or {}).get("inviti")):
        st.session_state.db_users[login] = mio          # altri usano questo account: si parte sempre dalla versione più recente
    att = st.session_state.get("account_attivo")
    if not st.session_state.get("_fam_auto"):
        # Una sola volta per sessione: chi non ha ancora nessun animale suo trova subito il libretto condiviso.
        # Chi ne ha uno proprio parte dal proprio (primo libretto); quello condiviso resta il secondo, nel selettore «Libretti di».
        st.session_state["_fam_auto"] = True
        if not att and not ((mio or {}).get("lista_animali") or (st.session_state.db_users.get(login) or {}).get("lista_animali")):
            fam = famiglie_di(login)
            if fam:
                att = fam[0][0]
                st.session_state.account_attivo = att
                st.session_state.pop("pet_select", None)
    if att and att != login:
        prop = su.get(att)
        if not prop or login not in ((prop.get("famiglia") or {}).get("membri") or {}):
            st.session_state.account_attivo = None
            st.session_state["accesso_revocato"] = (prop or {}).get("nome") or att
            return login
        st.session_state.db_users[att] = prop
        return att
    return login

def invita_familiare(owner, destinatario):
    dest = str(destinatario).strip().lower()
    if "@" not in dest or "." not in dest.split("@")[-1]:
        return False, "Scrivi un indirizzo email valido."
    if dest == owner:
        return False, "Questo è già il tuo indirizzo."
    esito = {}
    def _agg(rec):
        fam = rec.setdefault("famiglia", {})
        membri, inviti = fam.setdefault("membri", {}), fam.setdefault("inviti", {})
        for e in [e for e, i in inviti.items() if _scaduto(i.get("scad"))]:
            inviti.pop(e, None)
        if dest in membri:
            esito["m"] = "Questa persona fa già parte della tua famiglia."
        elif len(membri) + len(inviti) >= MAX_FAMILIARI:
            esito["m"] = f"Puoi condividere con al massimo {MAX_FAMILIARI} persone (inviti compresi)."
        else:
            inviti[dest] = {"scad": (datetime.now() + timedelta(days=GIORNI_INVITO)).isoformat(timespec="seconds"), "da": rec.get("nome", "")}
    if not modifica_account_su_disco(owner, _agg):
        return False, "Account non trovato."
    if "m" in esito:
        return False, esito["m"]
    nome = _nome_di(owner)
    link = url_invito_famiglia()
    testo = (f"Ciao,\n\n{nome} vuole condividere con te i libretti sanitari dei suoi animali su PetHealth.\n\n"
             f"Per accettare l'invito apri questo indirizzo:\n{link}\n\n"
             "COME ATTIVARE LA CONDIVISIONE\n"
             f"1. Apri l'indirizzo qui sopra (dal telefono o dal computer).\n"
             f"2. Se hai già un account PetHealth: accedi con questo stesso indirizzo email ({dest}).\n"
             f"   Se NON hai ancora un account: tocca «Registrati» e crealo usando proprio questo indirizzo email ({dest}), "
             "altrimenti l'invito non viene riconosciuto. Poi conferma la tua email se richiesto.\n"
             f"3. Dopo l'accesso vedrai l'avviso «Hai 1 invito da accettare»: tocca «Accetta l'invito». "
             "(Lo trovi anche nel menu e in «Condivisione e QR» → Famiglia.)\n"
             f"4. Fatto: da quel momento vedi i libretti di {nome}. Per tornare ai tuoi, scegli il tuo nome nel selettore dell'account nel menu.\n\n"
             "COSA PUOI FARE\n"
             "Puoi aggiungere visite, terapie e somministrazioni, pesate, fatture e spese. "
             f"Per sicurezza non puoi eliminare né modificare ciò che {nome} ha già inserito, né cambiare la sua password o il suo account.\n\n"
             "L'invito vale 14 giorni. Se non conosci questa persona ignora il messaggio.")
    n_h, l_h, d_h = html_escape(str(nome)), html_escape(link, quote=True), html_escape(dest)
    html = (f'<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#1E3A2B;background:#FFFFFF;line-height:1.5">'
            f'<h2 style="margin:0 0 16px 0;color:#1E3A2B">PetHealth</h2>'
            f'<p>Ciao,</p><p><b>{n_h}</b> vuole condividere con te i libretti sanitari dei suoi animali su PetHealth.</p>'
            f'<p style="margin:24px 0"><a href="{l_h}" style="display:inline-block;background:#1E3A2B;color:#FFFFFF;padding:13px 24px;border-radius:8px;text-decoration:none;font-weight:bold">Apri PetHealth e accetta l\'invito</a></p>'
            f'<h3 style="margin:24px 0 8px 0;color:#1E3A2B">Come attivare la condivisione</h3>'
            f'<ol style="padding-left:20px;margin:0">'
            f'<li style="margin-bottom:8px">Tocca il pulsante qui sopra (dal telefono o dal computer).</li>'
            f'<li style="margin-bottom:8px"><b>Hai già un account PetHealth?</b> Accedi con questo indirizzo email: <b>{d_h}</b>.<br>'
            f'<b>Non hai ancora un account?</b> Tocca «Registrati» e crealo usando <b>proprio questo indirizzo email</b> ({d_h}), '
            f'altrimenti l\'invito non viene riconosciuto. Conferma la tua email se richiesto.</li>'
            f'<li style="margin-bottom:8px">Dopo l\'accesso vedrai l\'avviso <b>«Hai 1 invito da accettare»</b>: tocca <b>«Accetta l\'invito»</b>. '
            f'(Lo trovi anche nel menu e in «Condivisione e QR» → Famiglia.)</li>'
            f'<li style="margin-bottom:8px">Fatto: da quel momento vedi i libretti di {n_h}. Per tornare ai tuoi, scegli il tuo nome nel selettore dell\'account nel menu.</li></ol>'
            f'<h3 style="margin:24px 0 8px 0;color:#1E3A2B">Cosa puoi fare</h3>'
            f'<p style="margin:0">Puoi <b>aggiungere</b> visite, terapie e somministrazioni, pesate, fatture e spese. '
            f'Per sicurezza <b>non puoi eliminare né modificare</b> ciò che {n_h} ha già inserito, né cambiare la sua password o il suo account.</p>'
            f'<p style="margin-top:20px">L\'invito vale 14 giorni.</p>'
            f'<p style="font-size:13px;color:#555555">Se il pulsante non funziona, copia questo indirizzo nel browser:<br><a href="{l_h}">{l_h}</a></p>'
            f'<p style="font-size:13px;color:#555555">Se non conosci questa persona ignora il messaggio.</p></div>')
    st.session_state["_invito_email_inviata"] = bool(invia_email(dest, f"{nome} ti invita su PetHealth", testo, html=html))
    return True, "Invito creato."

def annulla_invito(owner, dest):
    modifica_account_su_disco(owner, lambda r: ((r.get("famiglia") or {}).get("inviti") or {}).pop(dest, None))

def accetta_invito(owner, io):
    esito = {}
    def _acc(rec):
        fam = rec.setdefault("famiglia", {})
        inv = (fam.get("inviti") or {}).get(io)
        if not inv or _scaduto(inv.get("scad")):
            esito["m"] = "Invito scaduto o non più valido."
            return
        fam.setdefault("membri", {})[io] = {"nome": _nome_di(io), "dal": str(date.today())}
        fam["inviti"].pop(io, None)
    modifica_account_su_disco(owner, _acc)
    return esito.get("m")

def rifiuta_invito(owner, io):
    annulla_invito(owner, io)

def mostra_avviso_inviti(login, prefisso, nel_menu=False):
    """Avviso «hai un invito da accettare» con i pulsanti per accettare o rifiutare subito (senza aprire altre pagine).
    Dopo la scelta l'avviso sparisce, perché l'invito non è più in attesa."""
    inviti = inviti_ricevuti(login)
    if not inviti:
        return
    for prop, nome in inviti:
        messaggio = f"📨 Hai 1 invito da accettare: **{nome}** vuole condividere con te i suoi libretti. Potrai vederli e aggiornarli."
        (st.warning if nel_menu else st.info)(messaggio)
        if st.button("✅ Accetta l'invito", key=f"{prefisso}_acc_{prop}", type="primary", use_container_width=True):
            m = accetta_invito(prop, login)
            if m:
                st.error(m)
            else:
                st.session_state.account_attivo = prop
                st.session_state.sezione_attiva = "dashboard"
                st.session_state.pop("pet_select", None)
                st.session_state.trigger_close_sidebar = True
                st.rerun()
        if st.button("Rifiuta", key=f"{prefisso}_rif_{prop}", use_container_width=True):
            rifiuta_invito(prop, login)
            st.session_state.trigger_close_sidebar = True
            st.rerun()

def rimuovi_familiare(owner, membro):
    modifica_account_su_disco(owner, lambda r: ((r.get("famiglia") or {}).get("membri") or {}).pop(membro, None))

def lascia_famiglia(owner, io):
    rimuovi_familiare(owner, io)
    if st.session_state.get("account_attivo") == owner:
        st.session_state.account_attivo = None

# --------------------------- LINK PER IL VETERINARIO ---------------------------
OPZIONI_LINK = {"24 ore": 1, "7 giorni": 7, "30 giorni": 30}

def _hash_lid(lid):
    return hashlib.sha256(str(lid).encode("utf-8")).hexdigest()[:32]

def crea_link_veterinario(email, u, pet, giorni):
    lid = secrets.token_urlsafe(16)
    link = u.setdefault("link_veterinario", {})
    for k in [k for k, v in link.items() if _scaduto(v.get("scad"))]:
        link.pop(k, None)
    while len(link) >= 20:
        link.pop(sorted(link.items(), key=lambda x: x[1].get("scad", ""))[0][0], None)
    link[_hash_lid(lid)] = {"pet": pet, "creato": str(date.today()),
                            "scad": (datetime.now() + timedelta(days=giorni)).isoformat(timespec="seconds")}
    salva_dati()
    return f"{_b64e(email)}.{lid}"

def trova_link_veterinario(token):
    """(email, record_account, pet, scadenza) se il link è valido, altrimenti None. Legge sempre dall'archivio."""
    try:
        b, lid = str(token).split(".", 1)
        email = _b64d(b)
    except Exception:
        return None
    rec = ((carica_dati() or {}).get("users", {}) or {}).get(email)
    if not rec:
        return None
    voce = (rec.get("link_veterinario") or {}).get(_hash_lid(lid))
    if not voce or _scaduto(voce.get("scad")) or voce.get("pet") not in (rec.get("lista_animali") or []):
        return None
    return email, rec, voce["pet"], voce["scad"]

def _md(testo):
    """Rende innocuo per Markdown un testo scritto da altri (niente link, immagini, titoli o HTML inseriti a mano)."""
    return re.sub(r"([\\`*_{}\[\]()#+!|<>~:$&])", r"\\\1", str(testo if testo is not None else ""))

def _riga_visita_pubblica(v):
    extra = []
    if v.get("nome_vaccino"):
        extra.append(f"vaccino {_md(v['nome_vaccino'])}" + (f", lotto {_md(v['lotto_vaccino'])}" if v.get("lotto_vaccino") else "")
                     + (f", scade {_md(data_ui(v['scadenza_vaccino']))}" if v.get("scadenza_vaccino") else ""))
    firma = ""
    return (f"**{_md(data_ui(v.get('data', '')))}** · {_md(v.get('tipo', ''))} · {_md(v.get('veterinario', '') or '—')}"
            + (f" · {'; '.join(extra)}" if extra else "") + firma + (f"  \n{_md(v['diagnosi'])}" if v.get("diagnosi") else ""))

def mostra_libretto_condiviso(token):
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],[data-testid='stExpandSidebarButton'],"
                "[data-testid='collapsedControl']{display:none !important}</style>", unsafe_allow_html=True)
    st.markdown('<div style="padding:4px 0 18px 0">' + logo_html() + '</div>', unsafe_allow_html=True)
    ip = _ip_client() or "anon"
    attesa = secondi_blocco("link-pubblico", ip)
    if attesa:
        st.error(testo_attesa(attesa)); return
    trovato = trova_link_veterinario(token)
    if not trovato:
        registra_fallimento("link-pubblico", ip)
        st.error("Questo link non è valido, è scaduto oppure è stato revocato. Chiedi al proprietario di crearne uno nuovo.")
        return
    email, rec, pet, scad = trovato
    ana = (rec.get("db_anagrafica") or {}).get(pet, {}) or {}
    st.markdown(f"## 🩺 Libretto sanitario di {_md(pet)}")
    st.caption(f"Consultazione in sola lettura, condivisa dal proprietario. Il link scade il {datetime.fromisoformat(scad).strftime('%d/%m/%Y alle %H:%M')}.")
    st.markdown("### Anagrafica")
    righe = [("Specie", ana.get("tipo_animale")), ("Razza", ana.get("razza")), ("Sesso", ana.get("sesso")), ("Nato il", data_ui(ana.get("data_nascita"))),
             ("Microchip", ana.get("microchip")), ("Segni particolari", ana.get("segni_particolari"))]
    st.markdown("\n".join(f"- **{k}:** {_md(v)}" for k, v in righe if v) or "_Nessun dato._")
    st.markdown("### Visite e vaccini")
    visite = sorted((rec.get("db_visite") or {}).get(pet, []), key=lambda v: str(v.get("data", "")), reverse=True)
    for v in visite:
        st.markdown("- " + _riga_visita_pubblica(v))
    if not visite:
        st.caption("Nessuna visita registrata.")
    st.markdown("### Terapie")
    terapie = sorted((rec.get("db_terapie") or {}).get(pet, []), key=lambda t: str(t.get("data_inizio", "")), reverse=True)
    for t in terapie:
        dett = [_md(t.get("dosaggio", "")), _md(", ".join(orari_terapia(t))), _md(t.get("periodo", "")), _md(descrizione_pasto(t))]
        extra = f" · ricetta elettronica n. {_md(t['rev_numero'])}" if t.get("rev_numero") else ""
        st.markdown(f"- **{_md(t.get('farmaco', ''))}** · " + " · ".join(x for x in dett if x) + extra + (f"  \n{_md(t['note'])}" if t.get("note") else ""))
    if not terapie:
        st.caption("Nessuna terapia registrata.")
    st.markdown("### Peso")
    pesi = sorted((rec.get("db_peso") or {}).get(pet, []), key=lambda p: str(p.get("data", "")), reverse=True)[:10]
    st.markdown("\n".join(f"- {_md(data_ui(p.get('data', '')))}: **{_md(str(p.get('peso_kg', '')).replace('.', ','))} kg**" for p in pesi) or "_Nessuna pesata._")
    if REPORTLAB_OK:
        if st.button("📘 Prepara il PDF del libretto", key="pdf_condiviso"):
            try:
                st.session_state["pdf_condiviso_bytes"] = genera_pdf_libretto(pet, rec, includi_fatture=False)
            except Exception:
                st.error("Non è stato possibile creare il PDF.")
        if st.session_state.get("pdf_condiviso_bytes"):
            st.download_button("⬇️ Scarica il PDF", data=st.session_state["pdf_condiviso_bytes"], file_name=f"libretto-{date.today().isoformat()}.pdf",
                               mime="application/pdf", key="pdf_condiviso_dl")
    st.caption("Le informazioni sono inserite dal proprietario. Non sostituiscono la cartella clinica.")

# --------------------------- QR ANIMALE SMARRITO ---------------------------
def _scheda_qr(u, pet):
    for sid, s in (u.get("qr_schede") or {}).items():
        if s.get("pet") == pet:
            return sid, s
    return None, None

def crea_scheda_qr(email, u, pet):
    sid, s = _scheda_qr(u, pet)
    if sid:
        return sid
    sid = secrets.token_urlsafe(9)
    u.setdefault("qr_schede", {})[sid] = {"pet": pet, "attivo": True, "smarrito": False, "tel": True, "email": False, "chip": True,
                                          "messaggio": "", "creata": str(date.today())}
    salva_dati()
    return sid

def _cifre_tel(num):
    s = re.sub(r"[^\d+]", "", str(num or ""))
    if s.startswith("00"):
        s = "+" + s[2:]
    if not s.startswith("+") and len(s) in (9, 10) and s.startswith(("3", "0")):
        s = "+39" + s
    return s

def mostra_scheda_smarrito(token):
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],[data-testid='stExpandSidebarButton'],"
                "[data-testid='collapsedControl']{display:none !important}</style>", unsafe_allow_html=True)
    st.markdown('<div style="padding:4px 0 18px 0">' + logo_html() + '</div>', unsafe_allow_html=True)
    ip = _ip_client() or "anon"
    attesa = secondi_blocco("link-pubblico", ip)
    if attesa:
        st.error(testo_attesa(attesa)); return
    rec = s = None
    try:
        b, sid = str(token).split(".", 1)
        email = _b64d(b)
        rec = ((carica_dati() or {}).get("users", {}) or {}).get(email)
        s = ((rec or {}).get("qr_schede") or {}).get(sid)
    except Exception:
        pass
    if not rec or not s or not s.get("attivo") or s.get("pet") not in (rec.get("lista_animali") or []):
        registra_fallimento("link-pubblico", ip)
        st.error("Questa scheda non è disponibile.")
        return
    pet = s["pet"]
    ana = (rec.get("db_anagrafica") or {}).get(pet, {}) or {}
    if s.get("smarrito"):
        st.markdown(f"<div style='background:#B91C1C;color:#fff;border-radius:14px;padding:16px 18px;font-size:1.25rem;font-weight:700'>"
                    f"🚨 {html_escape(pet)} è smarrito{(' dal ' + html_escape(str(s.get('smarrito_dal', '')))) if s.get('smarrito_dal') else ''}. Aiutami a tornare a casa!</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(f"## 👋 Ciao, sono {html_escape(pet)}!")
        st.write("Se mi hai trovato e sono da solo, avvisa la mia famiglia: grazie!")
    mostra_immagine_salvata(ana.get("foto_animale"), pet, larghezza=280)
    righe = [("Specie", ana.get("tipo_animale")), ("Razza", ana.get("razza")), ("Sesso", ana.get("sesso")),
             ("Segni particolari", ana.get("segni_particolari")), ("Microchip", ana.get("microchip") if s.get("chip") else "")]
    st.markdown("\n".join(f"- **{k}:** {_md(v)}" for k, v in righe if v))
    if s.get("messaggio"):
        st.info(_md(s["messaggio"]))
    tel = _cifre_tel(rec.get("numero_whatsapp")) if s.get("tel") else ""
    if tel:
        st.markdown(f"<a href='tel:{html_escape(tel)}' style='display:inline-block;background:#1FA0E3;color:#fff;padding:12px 20px;border-radius:12px;text-decoration:none;font-weight:700;margin:6px 8px 6px 0'>📞 Chiama la mia famiglia</a>"
                    f"<a href='https://wa.me/{html_escape(tel.lstrip('+'))}?text={urllib.parse.quote('Ho trovato ' + pet + ' (scheda PetHealth).')}' target='_blank' rel='noopener noreferrer' "
                    "style='display:inline-block;background:#1FA0E3;color:#fff;padding:12px 20px;border-radius:12px;text-decoration:none;font-weight:700;margin:6px 0'>💬 Scrivi su WhatsApp</a>",
                    unsafe_allow_html=True)
    if s.get("email") and rec.get("email"):
        st.markdown(f"✉️ Email: **{html_escape(rec['email'])}**")
    if not tel and not (s.get("email") and rec.get("email")):
        st.warning("Il proprietario non ha indicato un contatto su questa scheda. Se puoi, porta l'animale da un veterinario: può leggere il microchip.")
    st.caption("Scheda creata con PetHealth. Se l'animale ha un microchip, ogni veterinario o ambulatorio può leggerlo e risalire al proprietario.")

def immagine_medaglietta(url, pet):
    """Cartoncino stampabile con il QR (PNG)."""
    try:
        import qrcode
        from PIL import ImageDraw, ImageFont
        qr = qrcode.make(url).convert("RGB").resize((700, 700), Image.NEAREST)
        img = Image.new("RGB", (900, 1100), "white")
        d = ImageDraw.Draw(img)
        def font(px, grassetto=False):
            for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if grassetto else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                      "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if grassetto else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
                      "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if grassetto else "/System/Library/Fonts/Supplemental/Arial.ttf"):
                try:
                    return ImageFont.truetype(p, px)
                except Exception:
                    continue
            try:
                return ImageFont.load_default(size=px)
            except Exception:
                return ImageFont.load_default()
        def centrato(testo, y, f, colore="#1E3A2B"):
            w = d.textlength(testo, font=f)
            d.text(((900 - w) / 2, y), testo, font=f, fill=colore)
        d.rounded_rectangle((10, 10, 889, 1089), radius=40, outline="#1E3A2B", width=8)
        centrato("Se mi hai trovato", 50, font(54, True))
        centrato("inquadra il QR", 125, font(54, True))
        img.paste(qr, (100, 230))
        centrato(pet[:22], 960, font(70, True), "#0369A1")
        centrato("PetHealth", 1040, font(28), "#64748B")
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None

# --------------------------- REGISTRO DOSI ---------------------------
def chiave_terapia(t):
    return f"{t.get('farmaco', '')}|{t.get('data_inizio', '')}"

def terapia_ancora_attiva(t, oggi=None):
    """True finché la terapia non è scaduta: dal giorno dopo la data di fine esce dalla dashboard (resta nello storico di «Terapie e Farmaci»).
    Se la data di fine manca o non è leggibile la terapia resta visibile (meglio una voce in più che una dose dimenticata)."""
    oggi = oggi or date.today()
    if not t.get("data_fine"):                    # terapia senza data di fine (vecchi inserimenti): resta finché non la chiudi tu
        return True
    try:
        fin = date.fromisoformat(str(t.get("data_fine"))[:10])
    except Exception:
        return True
    return fin >= oggi

def dosi_attive_oggi(terapie, oggi):
    out = []
    for t in terapie or []:
        try:
            ini = date.fromisoformat(str(t.get("data_inizio") or "")[:10])
            fin = date.fromisoformat(str(t.get("data_fine") or t.get("data_inizio") or "")[:10])
        except Exception:
            continue
        if ini <= oggi <= fin:
            out.extend((ora, t) for ora in orari_terapia(t))
    return sorted(out, key=lambda x: x[0])

def mostra_dosi_oggi(u, pet, chi, prefisso):
    oggi = date.today()
    dosi = dosi_attive_oggi((u.get("db_terapie") or {}).get(pet, []), oggi)
    reg = (u.setdefault("db_somministrazioni", {})).setdefault(pet, [])
    if not dosi:
        return
    fatte = sum(1 for ora, t in dosi if any(r["k"] == chiave_terapia(t) and r["data"] == str(oggi) and r["ora"] == ora for r in reg))
    st.markdown(f"#### ✅ Dosi di oggi · {fatte} di {len(dosi)} date")
    adesso = datetime.now().strftime("%H:%M")
    for i, (ora, t) in enumerate(dosi):
        k = chiave_terapia(t)
        voce = next((r for r in reg if r["k"] == k and r["data"] == str(oggi) and r["ora"] == ora), None)
        c1, c2 = st.columns([4, 1.4])
        with c1:
            testo = (f"**{html_escape(str(ora))}** · {html_escape(str(t.get('farmaco', '')))} — {html_escape(str(t.get('dosaggio', '')))}"
                     + (f" · {html_escape(descrizione_pasto(t))}" if descrizione_pasto(t) else ""))
            if voce:
                st.markdown(f"✅ {testo}  \n<span style='color:#166534;font-size:0.85rem'>data alle {html_escape(str(voce.get('quando', ''))[11:16])} da {html_escape(str(voce.get('da', '')))}</span>", unsafe_allow_html=True)
            else:
                st.markdown(("⏰ " if ora <= adesso else "🕒 ") + testo)
        with c2:
            if voce:
                if st.button("Annulla", key=f"dose_no_{prefisso}_{i}_{ora}"):
                    reg.remove(voce); salva_dati(); st.rerun()
            elif st.button("✔ Data", key=f"dose_si_{prefisso}_{i}_{ora}"):
                reg.append({"k": k, "farmaco": t.get("farmaco", ""), "data": str(oggi), "ora": ora,
                            "quando": datetime.now().isoformat(timespec="seconds"), "da": chi})
                limite = str(oggi - timedelta(days=120))
                reg[:] = [r for r in reg if r.get("data", "") >= limite]
                salva_dati(); st.rerun()
    storico = sorted(reg, key=lambda r: r.get("quando", ""), reverse=True)[:30]
    if storico:
        with st.expander("Storico delle somministrazioni", expanded=False):
            for r in storico:
                st.markdown(f"- {r['data'][8:10]}/{r['data'][5:7]} {r['ora']} · {r.get('farmaco', '')} — data alle {r.get('quando', '')[11:16]} da {r.get('da', '')}")

# ---------------------------------------------------------------------------
# ANIMALE SMARRITO: segnalazioni condivise tra gli utenti, avviso per provincia, «Ritrovato»
# Ogni segnalazione vive nell'account di chi la crea (così sparisce con l'account) e contiene SOLO
# i dati che il proprietario ha scelto di mostrare. Il servizio notifiche legge lo stesso archivio.
# ---------------------------------------------------------------------------
PROVINCE_IT = {
    "AG": "Agrigento", "AL": "Alessandria", "AN": "Ancona", "AO": "Aosta", "AP": "Ascoli Piceno", "AQ": "L'Aquila",
    "AR": "Arezzo", "AT": "Asti", "AV": "Avellino", "BA": "Bari", "BG": "Bergamo", "BI": "Biella", "BL": "Belluno",
    "BN": "Benevento", "BO": "Bologna", "BR": "Brindisi", "BS": "Brescia", "BT": "Barletta-Andria-Trani", "BZ": "Bolzano",
    "CA": "Cagliari", "CB": "Campobasso", "CE": "Caserta", "CH": "Chieti", "CL": "Caltanissetta", "CN": "Cuneo",
    "CO": "Como", "CR": "Cremona", "CS": "Cosenza", "CT": "Catania", "CZ": "Catanzaro", "EN": "Enna",
    "FC": "Forlì-Cesena", "FE": "Ferrara", "FG": "Foggia", "FI": "Firenze", "FM": "Fermo", "FR": "Frosinone",
    "GE": "Genova", "GO": "Gorizia", "GR": "Grosseto", "IM": "Imperia", "IS": "Isernia", "KR": "Crotone", "LC": "Lecco",
    "LE": "Lecce", "LI": "Livorno", "LO": "Lodi", "LT": "Latina", "LU": "Lucca", "MB": "Monza e Brianza", "MC": "Macerata",
    "ME": "Messina", "MI": "Milano", "MN": "Mantova", "MO": "Modena", "MS": "Massa-Carrara", "MT": "Matera",
    "NA": "Napoli", "NO": "Novara", "NU": "Nuoro", "OG": "Ogliastra", "OR": "Oristano", "OT": "Gallura (Olbia-Tempio)",
    "PA": "Palermo", "PC": "Piacenza", "PD": "Padova", "PE": "Pescara", "PG": "Perugia", "PI": "Pisa", "PN": "Pordenone",
    "PO": "Prato", "PR": "Parma", "PT": "Pistoia", "PU": "Pesaro e Urbino", "PV": "Pavia", "PZ": "Potenza",
    "RA": "Ravenna", "RC": "Reggio Calabria", "RE": "Reggio Emilia", "RG": "Ragusa", "RI": "Rieti", "RM": "Roma",
    "RN": "Rimini", "RO": "Rovigo", "SA": "Salerno", "SI": "Siena", "SO": "Sondrio", "SP": "La Spezia", "SR": "Siracusa",
    "SS": "Sassari", "SU": "Sud Sardegna", "SV": "Savona", "TA": "Taranto", "TE": "Teramo", "TN": "Trento", "TO": "Torino",
    "TP": "Trapani", "TR": "Terni", "TS": "Trieste", "TV": "Treviso", "UD": "Udine", "VA": "Varese",
    "VB": "Verbano-Cusio-Ossola", "VC": "Vercelli", "VE": "Venezia", "VI": "Vicenza", "VR": "Verona",
    "VS": "Medio Campidano", "VT": "Viterbo",
}
SMARRIMENTO_GIORNI = 90          # dopo questo tempo l'avviso scompare da solo (se ci si dimentica di premere «Ritrovato»)
_NESSUNA_PROVINCIA = "— scegli —"

def etichetta_provincia(sigla):
    return f"{sigla} – {PROVINCE_IT[sigla]}" if sigla in PROVINCE_IT else _NESSUNA_PROVINCIA

def opzioni_province():
    return [_NESSUNA_PROVINCIA] + [etichetta_provincia(k) for k in sorted(PROVINCE_IT, key=lambda x: PROVINCE_IT[x])]

def sigla_da_etichetta(testo):
    k = str(testo or "").split(" ")[0].upper()
    return k if k in PROVINCE_IT else ""

def _adesso_utc():
    return datetime.now(timezone.utc)

def _momento_smarrimento(r):
    try:
        t = datetime.fromisoformat(str(r.get("creato")))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def smarrimento_attivo(r):
    if not isinstance(r, dict) or r.get("stato") != "attivo":
        return False
    t = _momento_smarrimento(r)
    return bool(t) and (_adesso_utc() - t) < timedelta(days=SMARRIMENTO_GIORNI)

def smarrimento_in_corso(user_db, pet):
    for sid, r in (user_db.get("smarrimenti") or {}).items():
        if r.get("pet") == pet and smarrimento_attivo(r):
            return sid, r
    return None, None

@st.cache_resource(show_spinner=False)
def _cache_smarrimenti():
    return {}

def invalida_smarrimenti():
    _cache_smarrimenti().setdefault("sm_cache", {"t": 0.0, "voci": []})["t"] = 0.0

def elenca_smarrimenti():
    """Tutte le segnalazioni attive di tutti gli utenti, dalla più recente (riletta dal disco al massimo ogni 15 secondi)."""
    c = _cache_smarrimenti().setdefault("sm_cache", {"t": 0.0, "voci": []})
    ora = datetime.now().timestamp()
    if ora - c["t"] < 15:
        return c["voci"]
    dati = carica_dati() or {}
    eliminati = dati.get("eliminati") or {}
    voci = []
    for email, u in (dati.get("users") or {}).items():
        if not isinstance(u, dict) or u.get("stato") not in (None, "attivo") or sigla_email(email) in eliminati:
            continue
        for sid, r in (u.get("smarrimenti") or {}).items():
            if smarrimento_attivo(r):
                voci.append({**r, "id": sid, "_proprietario": email})
    voci.sort(key=lambda r: str(r.get("creato")), reverse=True)
    c["t"], c["voci"] = ora, voci[:300]
    return c["voci"]

def smarrimenti_della_provincia(sigla, escludi_email=None):
    return [r for r in elenca_smarrimenti() if sigla and r.get("provincia") == sigla and r.get("_proprietario") != escludi_email]

def _pulisci_vecchi_smarrimenti(user_db):
    lim = _adesso_utc() - timedelta(days=SMARRIMENTO_GIORNI + 90)
    for sid in [k for k, r in (user_db.get("smarrimenti") or {}).items()
                if (_momento_smarrimento(r) or _adesso_utc()) < lim]:
        user_db["smarrimenti"].pop(sid, None)

def segnala_smarrimento(user_db, pet, luogo, sigla, giorno, ora, note, contatti, mostra_chip, mostra_foto):
    """Crea la segnalazione con una copia dei SOLI dati scelti; se c'è la scheda QR la mette in «smarrito»."""
    ana = (user_db.get("db_anagrafica") or {}).get(pet, {}) or {}
    foto = miniatura_b64(ana.get("foto_animale"), 160) if mostra_foto else ""
    sid = secrets.token_urlsafe(8)
    user_db.setdefault("smarrimenti", {})[sid] = {
        "stato": "attivo", "creato": _adesso_utc().isoformat(timespec="seconds"), "pet": pet,
        "specie": ana.get("tipo_animale", ""), "razza": ana.get("razza", ""), "sesso": ana.get("sesso", ""),
        "segni": str(ana.get("segni_particolari") or "")[:200],
        "microchip": str(ana.get("microchip") or "") if mostra_chip else "", "foto": foto,
        "luogo": luogo[:120], "provincia": sigla, "data": str(giorno), "ora": ora, "note": note[:300],
        "contatti": {k: v for k, v in contatti.items() if v},
    }
    _sid, scheda = _scheda_qr(user_db, pet)
    if scheda:
        scheda["smarrito"] = True
        scheda["smarrito_dal"] = str(date.today())
    _pulisci_vecchi_smarrimenti(user_db)
    salva_dati()
    invalida_smarrimenti()
    return sid

def segna_ritrovato(user_db, sid):
    r = (user_db.get("smarrimenti") or {}).get(sid)
    if not r:
        return False
    r["stato"] = "ritrovato"
    r["ritrovato_il"] = _adesso_utc().isoformat(timespec="seconds")
    _sid, scheda = _scheda_qr(user_db, r.get("pet"))
    if scheda:
        scheda["smarrito"] = False
    salva_dati()
    invalida_smarrimenti()
    return True

_RE_B64 = re.compile(r"^[A-Za-z0-9+/=]{20,}$")

def html_card_smarrimento(r, mia=False):
    """Scheda di una segnalazione, su una sola riga di HTML (così Streamlit non la scambia per testo)."""
    h = html_escape
    foto = str(r.get("foto") or "")
    img = (f'<img src="data:image/jpeg;base64,{foto}" alt="" style="width:88px;height:88px;object-fit:cover;border-radius:14px;flex:none;border:1px solid #E5E7EB"/>'
           if _RE_B64.match(foto) else
           '<div style="width:88px;height:88px;border-radius:14px;background:#FEE2E2;display:flex;align-items:center;justify-content:center;font-size:2rem;flex:none">🐾</div>')
    sotto = " · ".join(x for x in [r.get("specie"), r.get("razza"), r.get("sesso") if r.get("sesso") != "Non specificato" else ""] if x)
    quando = data_ui(r.get("data")) + (f" alle {h(str(r.get('ora')))}" if r.get("ora") else "")
    righe = [f'<div style="font-size:1.15rem;font-weight:800;color:#B91C1C">🚨 {h(str(r.get("pet", "")))}</div>']
    if sotto:
        righe.append(f'<div style="color:#374151;font-size:.92rem">{h(sotto)}</div>')
    righe.append(f'<div style="margin-top:6px;color:#111827"><b>📍 Visto l\'ultima volta:</b> {h(str(r.get("luogo", "")))} ({h(str(r.get("provincia", "")))}) · {quando}</div>')
    if r.get("segni"):
        righe.append(f'<div style="color:#374151;font-size:.92rem">🔎 {h(str(r["segni"]))}</div>')
    if r.get("microchip"):
        righe.append(f'<div style="color:#374151;font-size:.92rem">🏷️ Microchip: {h(str(r["microchip"]))}</div>')
    if r.get("note"):
        righe.append(f'<div style="color:#374151;font-size:.92rem;margin-top:4px">💬 {h(str(r["note"]))}</div>')
    c = r.get("contatti") or {}
    if mia:
        righe.append('<div style="margin-top:8px;color:#0369A1;font-weight:700">È la tua segnalazione</div>')
    else:
        if c.get("nome"):
            righe.append(f'<div style="margin-top:6px;color:#111827">👤 Contatto: <b>{h(str(c["nome"]))}</b></div>')
        bott = []
        tel = _cifre_tel(c.get("tel")) if c.get("tel") else ""
        stile = "display:inline-block;color:#fff;padding:10px 16px;border-radius:12px;text-decoration:none;font-weight:700;margin:6px 8px 0 0;"
        if tel:
            righe.append(f'<div style="color:#111827">📞 {h(tel)}</div>')
            bott.append(f'<a href="tel:{h(tel)}" style="{stile}background:#0369A1">📞 Chiama</a>')
            bott.append(f'<a href="https://wa.me/{h(tel.lstrip("+"))}?text={urllib.parse.quote("Ho visto " + str(r.get("pet", "")) + " (avviso PetHealth).")}" '
                        f'target="_blank" rel="noopener noreferrer" style="{stile}background:#16A34A">💬 WhatsApp</a>')
        if c.get("email"):
            righe.append(f'<div style="color:#111827">✉️ {h(str(c["email"]))}</div>')
            bott.append(f'<a href="mailto:{h(str(c["email"]))}?subject={urllib.parse.quote("Ho visto " + str(r.get("pet", "")))}" style="{stile}background:#475569">✉️ Scrivi</a>')
        if bott:
            righe.append("<div>" + "".join(bott) + "</div>")
    return (f'<div style="display:flex;gap:14px;align-items:flex-start;background:#fff;border:1px solid #FCA5A5;border-left:6px solid #DC2626;'
            f'border-radius:16px;padding:14px;margin:0 0 12px 0">{img}<div style="min-width:0;flex:1;overflow-wrap:anywhere">' + "".join(righe) + '</div></div>')

def mostra_avviso_smarrimenti_dashboard(login_email, user_email, profilo):
    """Riquadro in cima alla dashboard: animali smarriti nella provincia dell'utente."""
    sigla = profilo.get("provincia", "")
    n = len(smarrimenti_della_provincia(sigla, escludi_email=user_email)) if sigla else 0
    if not n:
        return
    st.markdown('<div style="background:#FEF2F2;border:1px solid #FCA5A5;border-left:6px solid #DC2626;border-radius:14px;padding:12px 16px;margin:0 0 10px 0;color:#7F1D1D">'
                f'<b>🚨 {n} animal{"e smarrito" if n == 1 else "i smarriti"} nella tua provincia ({html_escape(sigla)})</b><br/>'
                'Se ne hai visto uno, puoi contattare subito il proprietario.</div>', unsafe_allow_html=True)
    if st.button("🐾 Vedi le segnalazioni", key="dash_vedi_smarriti"):
        cambia_sezione("smarrito")

def mostra_sezione_smarrito(login_email, user_email, user_db, pet_selected, nome_login):
    profilo = st.session_state.db_users[login_email]
    if st.session_state.get("sm_flash"):
        st.success(st.session_state.pop("sm_flash"))

    # --- le mie segnalazioni attive, sempre in cima, con il pulsante «Ritrovato»
    for sid, r in [(k, v) for k, v in (user_db.get("smarrimenti") or {}).items() if smarrimento_attivo(v)]:
        st.markdown(html_card_smarrimento(r, mia=True), unsafe_allow_html=True)
        if st.session_state.get(f"sm_conf_{sid}"):
            st.warning(f"Confermi che {r.get('pet')} è stato ritrovato? L'avviso sparirà per tutti gli utenti.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Sì, è stato ritrovato", key=f"sm_si_{sid}", type="primary", use_container_width=True):
                    segna_ritrovato(user_db, sid)
                    st.session_state.pop(f"sm_conf_{sid}", None)
                    st.session_state["sm_flash"] = f"🎉 Che bella notizia! L'avviso di {r.get('pet')} è stato tolto per tutti."
                    st.rerun()
            with c2:
                if st.button("Annulla", key=f"sm_no_{sid}", use_container_width=True):
                    st.session_state.pop(f"sm_conf_{sid}", None)
                    st.rerun()
        elif st.button("✅ Ritrovato", key=f"sm_trovato_{sid}", type="primary", use_container_width=True):
            st.session_state[f"sm_conf_{sid}"] = True
            st.rerun()

    t_bac, t_seg, t_qr = st.tabs(["📢 Segnalazioni", "🚨 Segnala smarrimento", "🏷️ Medaglietta QR"])

    # ------------------------------------------------------------ bacheca
    with t_bac:
        st.caption("Gli animali smarriti segnalati dagli utenti di PetHealth. Quando un animale viene ritrovato l'avviso sparisce da solo.")
        opz = opzioni_province()
        att = etichetta_provincia(profilo.get("provincia", ""))
        scelta = st.selectbox("📍 La mia provincia", opz, index=opz.index(att) if att in opz else 0, key=f"sm_prov_profilo_{login_email}",
                              help="Serve per mostrarti le segnalazioni vicino a te e per avvisarti quando un animale si perde nella tua provincia.")
        nuova = sigla_da_etichetta(scelta)
        if nuova != profilo.get("provincia", ""):
            profilo["provincia"] = nuova
            salva_dati()
            st.rerun()
        vuole = profilo.get("avvisi_smarriti", True) is not False
        nuovo_vuole = st.checkbox("🔔 Avvisami quando un animale si smarrisce nella mia provincia", value=vuole, key=f"sm_avvisi_{login_email}",
                                  help="L'avviso arriva come notifica sul telefono. Attiva le notifiche da «App e notifiche».")
        if nuovo_vuole != vuole:
            profilo["avvisi_smarriti"] = nuovo_vuole
            salva_dati()
        sigla = profilo.get("provincia", "")
        voci = elenca_smarrimenti()
        if sigla:
            ambito = st.radio("Mostra", [f"La mia provincia ({sigla})", "Tutta Italia"], horizontal=True, key=f"sm_filtro_{login_email}", label_visibility="collapsed")
            if ambito != "Tutta Italia":
                voci = [r for r in voci if r.get("provincia") == sigla]
        else:
            st.info("Scegli la tua provincia qui sopra: vedrai le segnalazioni vicino a te e riceverai gli avvisi. Intanto ecco tutte le segnalazioni.")
        if not voci:
            st.success("🙂 Non ci sono animali smarriti segnalati." if not sigla else "🙂 Nessun animale smarrito segnalato in questa zona.")
        for r in voci[:50]:
            st.markdown(html_card_smarrimento(r, mia=(r.get("_proprietario") == user_email)), unsafe_allow_html=True)

    # ------------------------------------------------------------ nuova segnalazione
    with t_seg:
        animali = user_db.get("lista_animali") or []
        if not animali:
            st.info("Registra prima un animale.")
        else:
            st.caption("Compila i dati: appena confermi, la segnalazione compare nella sezione di tutti gli utenti e gli utenti della provincia "
                       "dove è stato visto ricevono una notifica con la scheda dell'animale e i contatti che scegli qui sotto.")
            pet = st.selectbox("Quale animale è smarrito?", animali, index=animali.index(pet_selected) if pet_selected in animali else 0, key=f"sm_pet_{user_email}")
            gia, _r = smarrimento_in_corso(user_db, pet)
            if gia:
                st.info(f"{pet} risulta già segnalato come smarrito. Quando torna a casa premi «Ritrovato» qui sopra.")
            else:
                ana = (user_db.get("db_anagrafica") or {}).get(pet, {}) or {}
                tel_pref = ana.get("proprietario_telefono") or user_db.get("numero_whatsapp", "") or ""
                nome_pref = ana.get("proprietario_nome") or user_db.get("nome") or nome_login or ""
                opz = opzioni_province()
                att = etichetta_provincia(profilo.get("provincia", ""))
                with st.form("sm_form"):
                    st.markdown("**Cosa vuoi che vedano gli altri utenti di te**")
                    c_nome = st.checkbox("Mostra il mio nome", value=True)
                    f_nome = st.text_input("Il tuo nome", value=nome_pref, max_chars=60)
                    c_tel = st.checkbox("Mostra il mio telefono", value=bool(tel_pref))
                    f_tel = st.text_input("Il tuo telefono", value=tel_pref, max_chars=20, placeholder="es. 333 1234567")
                    c_mail = st.checkbox("Mostra la mia email", value=False)
                    f_mail = st.text_input("La tua email", value=login_email, max_chars=120)
                    st.markdown("**Dove è stato visto l'ultima volta**")
                    f_luogo = st.text_input("Luogo*", max_chars=120, placeholder="es. Parco Sempione, Milano")
                    f_prov = st.selectbox("Provincia*", opz, index=opz.index(att) if att in opz else 0,
                                          help="Gli utenti di questa provincia riceveranno l'avviso.")
                    f_giorno = st.date_input("Giorno", value=date.today(), min_value=date.today() - timedelta(days=30),
                                             max_value=date.today(), format="DD/MM/YYYY")
                    f_ora = st.text_input("Ora circa (facoltativa)", max_chars=5, placeholder="es. 18:30")
                    f_note = st.text_area("Note per chi lo vede (facoltative)", max_chars=300,
                                          placeholder="es. Ha il collare rosso, è timido: non rincorrerlo, chiamami")
                    c_chip = c_foto = False
                    if ana.get("microchip"):
                        c_chip = st.checkbox("Mostra il numero di microchip", value=True)
                    if ana.get("foto_animale"):
                        c_foto = st.checkbox("Mostra la foto dell'animale", value=True)
                    st.caption("Inviando, i dati dell'animale e i contatti spuntati saranno visibili agli utenti di PetHealth, e gli utenti della provincia indicata riceveranno una notifica.")
                    invia = st.form_submit_button("🚨 Invia la segnalazione", type="primary")
                if invia:
                    sigla_v = sigla_da_etichetta(f_prov)
                    tel_ok = bool(c_tel) and len(re.sub(r"\D", "", f_tel or "")) >= 6
                    mail_ok = bool(c_mail) and bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", (f_mail or "").strip()))
                    attesa = secondi_blocco("smarrito", login_email)
                    if attesa:
                        st.error("Hai già inviato diverse segnalazioni oggi. Per sicurezza riprova più tardi o scrivi all'assistenza.")
                    elif len([1 for _r in (user_db.get("smarrimenti") or {}).values() if smarrimento_attivo(_r)]) >= 2:
                        st.error("Hai già due animali segnalati come smarriti. Quando uno viene ritrovato premi «Ritrovato», poi potrai segnalarne un altro.")
                    elif len((f_luogo or "").strip()) < 3:
                        st.error("⚠️ Scrivi dove è stato visto l'ultima volta (almeno il nome del posto o della via).")
                    elif not sigla_v:
                        st.error("⚠️ Scegli la provincia: serve per avvisare gli utenti della zona.")
                    elif (f_ora or "").strip() and not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", f_ora.strip()):
                        st.error("⚠️ L'ora va scritta così: 18:30 (oppure lasciala vuota).")
                    elif c_tel and not tel_ok:
                        st.error("⚠️ Il numero di telefono non sembra completo.")
                    elif c_mail and not mail_ok:
                        st.error("⚠️ L'indirizzo email non sembra corretto.")
                    elif not (tel_ok or mail_ok):
                        st.error("⚠️ Spunta almeno un contatto (telefono o email), altrimenti nessuno potrà avvisarti.")
                    else:
                        ora_v = f_ora.strip().zfill(5) if (f_ora or "").strip() else ""
                        contatti = {"nome": (f_nome or "").strip()[:60] if c_nome else "",
                                    "tel": (f_tel or "").strip()[:20] if tel_ok else "",
                                    "email": (f_mail or "").strip()[:120] if mail_ok else ""}
                        registra_fallimento("smarrito", login_email)
                        segnala_smarrimento(user_db, pet, f_luogo.strip(), sigla_v, f_giorno, ora_v, (f_note or "").strip(), contatti, bool(c_chip), bool(c_foto))
                        st.session_state["sm_flash"] = (f"🚨 Segnalazione inviata per {pet}. Gli utenti di {sigla_v} riceveranno l'avviso entro un minuto "
                                                        "(se hanno attivato le notifiche) e la vedono nella sezione «Animale smarrito».")
                        st.rerun()

    # ------------------------------------------------------------ medaglietta QR
    with t_qr:
        st.caption("Il QR sulla medaglietta permette a chi trova il tuo animale di vedere la sua scheda e contattarti, anche senza app.")
        mostra_tab_smarrito(user_email, user_db, pet_selected)

# --------------------------- SEZIONE «CONDIVISIONE E QR» ---------------------------
def mostra_tab_smarrito(user_email, user_db, pet):
    """Scheda con QR per l'animale smarrito (si trova nella voce di menù «Animale smarrito», scheda «Medaglietta QR»)."""
    if not pet:
        st.info("Registra prima un animale.")
    else:
        sid, s = _scheda_qr(user_db, pet)
        st.markdown(f"#### Scheda con QR · {pet}")
        st.caption("Stampa il QR su una medaglietta o sul collare: chi lo inquadra vede la scheda di tuo animale e i contatti che scegli qui sotto. Non serve alcuna app.")
        if not s:
            if st.button("Crea la scheda QR", key="crea_qr"):
                crea_scheda_qr(user_email, user_db, pet); st.rerun()
        else:
            s["attivo"] = st.checkbox("Scheda attiva (visibile a chi inquadra il QR)", value=bool(s.get("attivo")), key=f"qr_att_{sid}")
            nuovo_sm = st.checkbox("🚨 Segna come SMARRITO (mostra un avviso rosso)", value=bool(s.get("smarrito")), key=f"qr_sm_{sid}")
            if nuovo_sm and not s.get("smarrito"):
                s["smarrito_dal"] = str(date.today())
            s["smarrito"] = nuovo_sm
            s["tel"] = st.checkbox("Mostra il mio numero di telefono", value=bool(s.get("tel")), key=f"qr_tel_{sid}")
            s["email"] = st.checkbox("Mostra la mia email", value=bool(s.get("email")), key=f"qr_em_{sid}")
            s["chip"] = st.checkbox("Mostra il numero di microchip", value=bool(s.get("chip")), key=f"qr_chip_{sid}")
            s["messaggio"] = st.text_input("Messaggio per chi trova l'animale (facoltativo)", value=s.get("messaggio", ""), max_chars=200, key=f"qr_msg_{sid}",
                                           placeholder="es. Ha bisogno di una terapia: chiamami subito")
            if st.button("Salva la scheda", key=f"qr_salva_{sid}"):
                salva_dati(); st.success("Scheda salvata.")
            if s.get("tel") and not user_db.get("numero_whatsapp"):
                st.warning("Nel tuo profilo non c'è un numero di telefono: la scheda non mostrerà contatti telefonici.")
            url = url_pubblico("animale", f"{_b64e(user_email)}.{sid}")
            st.code(url, language=None)
            if s.get("smarrito"):
                st.caption("🚨 Diffondi subito l'avviso con:")
                _msg_sm = f"🚨 ANIMALE SMARRITO: {pet}. Se l'hai visto o trovato, guarda qui la sua scheda e contattami: {url}"
                _b1, _b2, _b3 = st.columns(3)
                with _b1:
                    st.link_button("✉️ Email", "mailto:?subject=" + urllib.parse.quote(f"Animale smarrito: {pet}") + "&body=" + urllib.parse.quote(_msg_sm), use_container_width=True)
                with _b2:
                    st.link_button("💬 WhatsApp", "https://wa.me/?text=" + urllib.parse.quote(_msg_sm), use_container_width=True)
                with _b3:
                    st.link_button("✈️ Telegram", "https://t.me/share/url?url=" + urllib.parse.quote(url) + "&text=" + urllib.parse.quote(f"🚨 ANIMALE SMARRITO: {pet}. Se l'hai visto o trovato, contattami da qui:"), use_container_width=True)
            png = immagine_medaglietta(url, pet)
            if png:
                st.image(png, width=260)
                st.download_button("⬇️ Scarica il QR da stampare", data=png, file_name=f"qr-{re.sub(r'[^A-Za-z0-9]+', '-', pet)}.png", mime="image/png", key="qr_dl")
            if not ospite_solo_aggiunta() and st.button("Elimina la scheda (il QR stampato smette di funzionare)", key=f"qr_del_{sid}"):
                user_db["qr_schede"].pop(sid, None); salva_dati(); st.rerun()

def mostra_sezione_condividi(login, user_email, user_db, pet):
    st.markdown("<h2 style='color: #1E3A2B;'>🔗 Condivisione e QR</h2>", unsafe_allow_html=True)
    if login == "demo@pethealth.it":
        st.info("Queste funzioni non sono disponibili nell'account di prova: registrati per usarle.")
        return
    t_fam, t_vet = st.tabs(["👪 Famiglia", "🩺 Per il veterinario"])
    io = st.session_state.db_users[login]

    with t_fam:
        for prop, nome in inviti_ricevuti(login):
            st.info(f"📨 **{nome}** ti invita a condividere i suoi libretti. Potrai vederli e aggiornarli.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Accetta", key=f"acc_{prop}"):
                    m = accetta_invito(prop, login)
                    if m: st.error(m)
                    else:
                        st.session_state.account_attivo = prop; st.session_state.sezione_attiva = "dashboard"
                        st.session_state.pop("pet_select", None); st.rerun()
            with c2:
                if st.button("Rifiuta", key=f"rif_{prop}"):
                    rifiuta_invito(prop, login); st.rerun()
        st.markdown("#### Persone con cui condividi i tuoi libretti")
        st.caption("Chi inviti vede e aggiorna i tuoi libretti con il proprio account, e riceve le stesse notifiche dei richiami e delle terapie. "
                   "La condivisione parte solo quando la persona accetta l'invito. Non può cambiare la tua password né eliminare il tuo account. "
                   "Puoi revocare il permesso quando vuoi: da quel momento non vede più i tuoi libretti.")
        if st.session_state.get("famiglia_flash"):
            st.success(st.session_state.pop("famiglia_flash"))
        fam = io.get("famiglia") or {}
        _membri = fam.get("membri") or {}
        _in_attesa = {e: inv for e, inv in (fam.get("inviti") or {}).items() if not _scaduto(inv.get("scad"))}
        if not _membri and not _in_attesa:
            st.info("Al momento non condividi i tuoi libretti con nessuno.")
        for e, m in _membri.items():
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"👤 **{m.get('nome', e)}** · {e}")
                st.caption(f"✅ Condivisione attiva dal {_data_it(m.get('dal', ''))}")
            with c2:
                if not st.session_state.get(f"conf_rev_{e}"):
                    if st.button("Revoca", key=f"rim_{e}", use_container_width=True):
                        st.session_state[f"conf_rev_{e}"] = True; st.rerun()
            if st.session_state.get(f"conf_rev_{e}"):
                st.warning(f"Vuoi revocare la condivisione con **{m.get('nome', e)}**? Da subito non vedrà più i tuoi libretti. Potrai invitarla di nuovo quando vuoi.")
                r1, r2 = st.columns(2)
                with r1:
                    if st.button("Sì, revoca", key=f"rev_si_{e}", type="primary", use_container_width=True):
                        st.session_state.pop(f"conf_rev_{e}", None)
                        rimuovi_familiare(login, e)
                        st.session_state["famiglia_flash"] = f"Hai revocato la condivisione con {m.get('nome', e)}."
                        st.rerun()
                with r2:
                    if st.button("No, mantieni", key=f"rev_no_{e}", use_container_width=True):
                        st.session_state.pop(f"conf_rev_{e}", None); st.rerun()
        for e, inv in _in_attesa.items():
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"⏳ **{e}**")
                st.caption("Invito in attesa: la condivisione parte solo se la persona accetta.")
            with c2:
                if st.button("Revoca invito", key=f"ann_{e}", use_container_width=True):
                    annulla_invito(login, e)
                    st.session_state["famiglia_flash"] = f"Invito a {e} annullato."
                    st.rerun()
        with st.form("form_invito"):
            dest = st.text_input("Email della persona da invitare")
            if st.form_submit_button("Invia invito"):
                attesa = secondi_blocco("invito", login)
                if attesa:
                    st.error(testo_attesa(attesa))
                else:
                    registra_fallimento("invito", login)
                    ok_i, msg_i = invita_familiare(login, dest)
                    if ok_i:
                        st.success("Invito creato. La persona lo trova in «Condivisione e QR» → Famiglia dopo l'accesso (anche registrandosi con questa email)." +
                                   (" Le abbiamo mandato anche un'email con il link per aprirlo." if st.session_state.get("_invito_email_inviata") else
                                    " L'email non è partita: avvisala tu, l'invito resta valido 14 giorni."))
                    else:
                        st.error(msg_i)
        altre = famiglie_di(login)
        if altre:
            st.markdown("#### Libretti condivisi con me")
            for prop, nome in altre:
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"🏠 Famiglia di **{nome}** ({prop})")
                with c2:
                    if st.button("Lascia", key=f"lascia_{prop}"):
                        lascia_famiglia(prop, login); st.session_state.pop("pet_select", None); st.rerun()

    with t_vet:
        if not pet:
            st.info("Registra prima un animale.")
        else:
            st.markdown(f"#### Link per il veterinario · {pet}")
            st.caption("Crea un link temporaneo: chi lo riceve vede il libretto di sola lettura (anagrafica, visite, vaccini, terapie, peso) senza account. "
                       "Non include fatture né il tuo numero di telefono. Puoi revocarlo in ogni momento.")
            durata = st.selectbox("Il link vale per", list(OPZIONI_LINK), index=1, key="durata_link")
            if st.session_state.get("link_revocato_flash"):
                st.success(st.session_state.pop("link_revocato_flash"))
            if st.button("Crea il link", key="crea_link"):
                _tok = crea_link_veterinario(user_email, user_db, pet, OPZIONI_LINK[durata])
                st.session_state["ultimo_link"] = {"pet": pet, "url": url_pubblico("libretto", _tok), "k": _hash_lid(_tok.rsplit(".", 1)[-1])}
            ul = st.session_state.get("ultimo_link")
            # il link (e il suo QR) si mostrano solo finché esiste davvero: se è stato revocato o è scaduto spariscono
            if ul and ul.get("k") not in (user_db.get("link_veterinario") or {}):
                st.session_state.pop("ultimo_link", None)
                ul = None
            if ul and ul.get("pet") == pet:
                st.success("Link creato. Copialo, oppure scegli come inviarlo al veterinario:")
                st.code(ul["url"], language=None)
                _testo = f"Libretto sanitario di {pet}: {ul['url']}"
                st.caption("Invia il libretto con:")
                b_em, b_wa, b_tg = st.columns(3)
                with b_em:
                    st.link_button("✉️ Email", "mailto:?subject=" + urllib.parse.quote(f"Libretto sanitario di {pet}") + "&body=" + urllib.parse.quote(_testo), use_container_width=True)
                with b_wa:
                    st.link_button("💬 WhatsApp", "https://wa.me/?text=" + urllib.parse.quote(_testo), use_container_width=True)
                with b_tg:
                    st.link_button("✈️ Telegram", "https://t.me/share/url?url=" + urllib.parse.quote(ul["url"]) + "&text=" + urllib.parse.quote(f"Libretto sanitario di {pet}"), use_container_width=True)
                png = qr_png(ul["url"])
                if png:
                    st.image(png, width=160, caption="Oppure fai inquadrare questo QR")
            attivi = [(k, v) for k, v in (user_db.get("link_veterinario") or {}).items() if v.get("pet") == pet and not _scaduto(v.get("scad"))]
            if attivi:
                st.markdown("**Link attivi**")
                for k, v in attivi:
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"Creato il {data_ui(v.get('creato', ''))} · scade il {datetime.fromisoformat(v['scad']).strftime('%d/%m/%Y %H:%M')}")
                    with c2:
                        if st.button("Revoca", key=f"rev_{k}"):
                            user_db["link_veterinario"].pop(k, None)
                            _ul = st.session_state.get("ultimo_link")
                            if _ul and (_ul.get("k") == k or not _ul.get("k")):
                                st.session_state.pop("ultimo_link", None)      # sparisce anche il QR appena creato
                            st.session_state["link_revocato_flash"] = "Link revocato: il link e il suo QR code non funzionano più."
                            salva_dati(); st.rerun()

# ---------------------------------------------------------------------------
# ATTIVAZIONE ACCOUNT: codice a 6 cifre inviato per email (mai mostrato a schermo se l'email è configurata)
# Per attivare l'invio aggiungi nel file dei segreti la sezione [smtp] (host, port, user, password, from).
# ---------------------------------------------------------------------------
def nuovo_codice_attivazione(email_c):
    """Crea un nuovo codice per l'account, lo salva con scadenza e prova a inviarlo. Restituisce True se inviato per email."""
    codice = f"{secrets.randbelow(10 ** 6):06d}"
    u = st.session_state.db_users[email_c]
    u["codice_conferma"] = codice
    u["codice_scadenza"] = (datetime.now() + timedelta(minutes=15)).isoformat()
    st.session_state.verification_pending_email = email_c
    salva_dati(extra_email=email_c)
    inviata = invia_email_attivazione(email_c, u.get("nome", ""), codice)
    st.session_state.posta_demo = {"email": email_c, "codice": codice} if (modalita_prova() and not inviata) else None
    return inviata

# ---------------------------------------------------------------------------
# ACCOUNT DEMO (Luna e Micio)
# ---------------------------------------------------------------------------
def _dati_demo():
    oggi = date.today()
    g = lambda n: str(oggi + timedelta(days=n))
    return {
        "nome": "Giulia Rossi", "email": "demo@pethealth.it", "password": hash_password(secrets.token_hex(12)),
        "numero_whatsapp": "", "numero_whatsapp_2": "", "stato": "attivo", "data_registrazione": str(oggi),
        "lista_animali": ["Luna", "Micio"], "pet_selezionato": "Luna",
        "db_anagrafica": {
            "Luna": {"tipo_animale": "Cane", "nome": "Luna", "razza": "Labrador", "sesso": "Femmina", "data_nascita": "2022-04-12",
                     "microchip": "380260000123456", "microchip_foto": "", "segni_particolari": "", "proprietario_nome": "Giulia Rossi",
                     "proprietario_indirizzo": "", "proprietario_telefono": "", "proprietario_citta": "", "foto_animale": ""},
            "Micio": {"tipo_animale": "Gatto", "nome": "Micio", "razza": "Europeo", "sesso": "Maschio", "data_nascita": "2020-09-03",
                      "microchip": "380260000654321", "microchip_foto": "", "segni_particolari": "", "proprietario_nome": "Giulia Rossi",
                      "proprietario_indirizzo": "", "proprietario_telefono": "", "proprietario_citta": "", "foto_animale": ""},
        },
        "db_visite": {"Luna": [
            {"data": g(-340), "tipo": "Vaccinazione", "veterinario": "Dott. Rossi", "diagnosi": "Richiamo antirabbica", "referto": None,
             "certificata": False, "num_ordine_vet": "", "provincia_vet": "", "vet_id_permanente": None, "codice_certificato": None,
             "nome_vaccino": "Antirabbica", "lotto_vaccino": "A1234", "scadenza_vaccino": g(400), "etichetta_vaccino": "",
             "richiamo": True, "prossimo_controllo_data": g(12), "prossimo_controllo_tipo": "Richiamo antirabbica"},
            {"data": g(-200), "tipo": "Vaccinazione", "veterinario": "Dott.ssa Neri", "diagnosi": "Polivalente", "referto": None,
             "certificata": False, "num_ordine_vet": "", "provincia_vet": "", "vet_id_permanente": None, "codice_certificato": None,
             "nome_vaccino": "Polivalente (DHPP)", "lotto_vaccino": "B778", "scadenza_vaccino": g(300), "etichetta_vaccino": "",
             "richiamo": True, "prossimo_controllo_data": g(-5), "prossimo_controllo_tipo": "Richiamo polivalente"},
            {"data": g(-60), "tipo": "Visita di controllo", "veterinario": "Dott. Rossi", "diagnosi": "Controllo annuale, tutto nella norma", "referto": None,
             "certificata": False, "num_ordine_vet": "", "provincia_vet": "", "vet_id_permanente": None, "codice_certificato": None,
             "nome_vaccino": "", "lotto_vaccino": "", "scadenza_vaccino": "", "etichetta_vaccino": "",
             "richiamo": True, "prossimo_controllo_data": g(150), "prossimo_controllo_tipo": "Controllo annuale"}]},
        "db_terapie": {"Luna": [{"farmaco": "Antiparassitario spot-on", "dosaggio": "1 pipetta", "orario": "Mattina",
                                 "periodo": "Una volta al mese", "data_inizio": g(-5), "note": "", "ricetta": None}]},
        "db_peso": {"Luna": [{"data": g(-150), "peso_kg": 10.8, "note": ""}, {"data": g(-110), "peso_kg": 11.4, "note": ""},
                             {"data": g(-70), "peso_kg": 11.9, "note": ""}, {"data": g(-35), "peso_kg": 12.1, "note": ""},
                             {"data": g(-3), "peso_kg": 12.4, "note": ""}],
                    "Micio": [{"data": g(-20), "peso_kg": 4.6, "note": ""}]},
        "db_calori": {"Luna": [{"inizio": g(-130), "fine": g(-118), "note": ""}, {"inizio": g(-62), "fine": g(-50), "note": ""}]},
        "db_fatture": {}, "angeli_archiviati": {},
    }


# ---------------------------------------------------------------------------
# ACCESSO CHE RESTA ATTIVO SU QUESTO DISPOSITIVO (30 giorni)
# Nel telefono resta solo un codice casuale firmato; sul server si può revocare in ogni momento (logout / «Esci da tutti i dispositivi»).
# ---------------------------------------------------------------------------
GIORNI_SESSIONE_DISPOSITIVO = 30

def _firma_sessione(email, jti):
    return hmac.new(_chiave_sigillo(), f"sess|{email}|{jti}".encode("utf-8"), hashlib.sha256).hexdigest()[:40]

def _leggi_cookie_sessione():
    """Restituisce (email, jti, firma) dal cookie del dispositivo, oppure (None, None, None)."""
    try:
        tok = st.context.cookies.get("ph_sess")
    except Exception:
        tok = None
    try:
        if not tok or str(tok).count(".") != 2:
            return None, None, None
        b64, jti, firma = str(tok).split(".")
        email = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4)).decode("utf-8")
        return email, jti, firma
    except Exception:
        return None, None, None

def _aggiorna_sessioni(email, fn):
    """Cambia l'elenco dei dispositivi collegati direttamente nell'archivio: un'altra scheda o un altro telefono
    con una copia vecchia dell'account non può più cancellare per sbaglio il «resta connesso» degli altri."""
    u = st.session_state.db_users.get(email)
    with _lock_disco():
        su = carica_dati() or {}
        rec = (su.get("users", {}) or {}).get(email)
        if rec is None:                                   # account presente solo in sessione (prove)
            if u is not None:
                fn(u.setdefault("sessioni_dispositivo", {}))
            return
        sess = rec.setdefault("sessioni_dispositivo", {})
        fn(sess)
        _scrivi_archivio(su)
    if u is not None:
        u["sessioni_dispositivo"] = dict(sess)

def crea_sessione_dispositivo(email):
    """Crea il codice per «resta connesso» e lo registra nell'account. Restituisce il testo del cookie."""
    jti = secrets.token_urlsafe(16)
    def _agg(sess):
        adesso = datetime.now()
        for k in [k for k, scad in sess.items() if str(scad) < adesso.isoformat(timespec="seconds")]:
            sess.pop(k, None)
        while len(sess) >= 10:                      # al massimo 10 dispositivi: si toglie il più vecchio
            sess.pop(sorted(sess.items(), key=lambda x: x[1])[0][0], None)
        sess[jti] = (adesso + timedelta(days=GIORNI_SESSIONE_DISPOSITIVO)).isoformat(timespec="seconds")
    _aggiorna_sessioni(email, _agg)
    st.session_state.ph_jti = jti
    b64 = base64.urlsafe_b64encode(email.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{b64}.{jti}.{_firma_sessione(email, jti)}"

def utente_da_cookie():
    """Se il dispositivo ha un cookie valido restituisce (email, jti), altrimenti (None, None)."""
    email, jti, firma = _leggi_cookie_sessione()
    if not email or not hmac.compare_digest(_firma_sessione(email, jti), firma or ""):
        return None, None
    u = st.session_state.db_users.get(email)
    if not u or u.get("stato") not in (None, "attivo"):
        return None, None
    scad = (u.get("sessioni_dispositivo") or {}).get(jti)
    if not scad or str(scad) < datetime.now().isoformat(timespec="seconds"):
        return None, None
    return email, jti

def token_push(email):
    """Gettone firmato (valido 30 minuti) con cui il telefono si iscrive alle notifiche del proprio account."""
    scad = int(datetime.now().timestamp()) + 30 * 60
    firma = hmac.new(_chiave_sigillo(), f"push|{email}|{scad}".encode("utf-8"), hashlib.sha256).hexdigest()[:40]
    b64 = base64.urlsafe_b64encode(email.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{b64}.{scad}.{firma}"

_HTML_NOTIFICHE = r"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1E293B}
.c{background:#F4EEDD;border:1.5px solid #B8975A;border-radius:16px;padding:16px}
#s{font-size:15px;line-height:1.45;margin:0 0 12px}
button{font:700 15px -apple-system,sans-serif;border:0;border-radius:99px;padding:13px 20px;min-height:46px;margin:0 8px 8px 0;cursor:pointer}
.p,.g{background:#1FA0E3;color:#fff}
button:disabled{opacity:.55}
</style></head><body><div class="c"><p id="s">Controllo…</p><div id="b"></div></div>
<script>
(function () {
  var TOKEN = "__TOKEN__";
  var P; try { void window.parent.document; P = window.parent; } catch (e) { P = window; }
  var s = document.getElementById("s"), b = document.getElementById("b");
  var ua = P.navigator.userAgent || "";
  var ios = /iPad|iPhone|iPod/.test(ua) || (P.navigator.platform === "MacIntel" && P.navigator.maxTouchPoints > 1);
  var standalone = false; try { standalone = P.matchMedia("(display-mode: standalone)").matches || P.navigator.standalone === true; } catch (e) {}
  function u8(t) { t = t.replace(/-/g, "+").replace(/_/g, "/"); var r = atob(t + "===".slice((t.length + 3) % 4)); var a = new Uint8Array(r.length); for (var i = 0; i < r.length; i++) a[i] = r.charCodeAt(i); return a; }
  function btn(testo, classe, fn) { var x = document.createElement("button"); x.textContent = testo; x.className = classe; x.onclick = function () { x.disabled = true; Promise.resolve(fn()).catch(function (e) { s.textContent = "Qualcosa non ha funzionato: " + (e && e.message ? e.message : e); }).then(function () { x.disabled = false; }); }; b.appendChild(x); }
  function api(path, corpo) { corpo.token = TOKEN; return P.fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { j.status = r.status; return j; }); }); }
  function registrazione() {
    var pronta = P.navigator.serviceWorker.ready;
    var attesa = new Promise(function (_, no) { setTimeout(function () { no(new Error("l'app non è ancora pronta: ricarica la pagina e riprova")); }, 10000); });
    return Promise.race([pronta, attesa]);
  }
  function mostra() {
    b.innerHTML = "";
    if (!("serviceWorker" in P.navigator) || !("PushManager" in P) || !("Notification" in P)) {
      s.textContent = (ios && !standalone)
        ? "Su iPhone le notifiche funzionano solo dall'app installata: aggiungi PetHealth alla schermata Home (vedi le istruzioni qui sopra), aprila da lì e torna in questa pagina."
        : "Questo dispositivo o questo browser non supporta le notifiche.";
      return;
    }
    if (P.Notification.permission === "denied") {
      s.textContent = "Le notifiche per PetHealth sono bloccate. Riattivale dalle impostazioni del telefono (Impostazioni → Notifiche → PetHealth, oppure le impostazioni del sito in Chrome) e ricarica la pagina.";
      return;
    }
    registrazione().then(function (reg) { return reg.pushManager.getSubscription(); }).then(function (sub) {
      if (sub) {
        s.textContent = "✅ Notifiche attive su questo dispositivo. Riceverai un avviso 2 giorni prima di ogni richiamo.";
        btn("Invia una notifica di prova", "g", function () { return api("/push/prova", {}).then(function (r) { s.textContent = r.ok ? "Notifica inviata: dovrebbe comparire tra qualche secondo." : (r.errore || "Invio non riuscito: prova a disattivare e riattivare le notifiche."); }); });
        btn("Disattiva", "g", function () { return api("/push/disiscrivi", { endpoint: sub.endpoint }).then(function () { return sub.unsubscribe(); }).then(mostra); });
      } else {
        s.textContent = "Attiva le notifiche per ricevere un avviso 2 giorni prima di ogni richiamo o controllo che hai segnato.";
        btn("🔔 Attiva le notifiche su questo dispositivo", "p", attiva);
      }
    }).catch(function (e) { s.textContent = e && e.message ? e.message : "Impossibile controllare le notifiche."; });
  }
  function attiva() {
    return P.Notification.requestPermission().then(function (perm) {
      if (perm !== "granted") { s.textContent = "Senza il permesso non posso mandarti le notifiche. Puoi riprovare quando vuoi."; return; }
      return Promise.all([registrazione(), P.fetch("/push/chiave").then(function (r) { return r.json(); })]).then(function (x) {
        var reg = x[0], chiave = u8(x[1].chiave);
        return reg.pushManager.getSubscription().then(function (vecchia) { return vecchia ? vecchia.unsubscribe() : true; })
          .then(function () { return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: chiave }); })
          .then(function (sub) { return api("/push/iscrivi", { subscription: sub.toJSON() }); })
          .then(function (r) { if (r.status !== 200) { throw new Error(r.errore || "iscrizione non riuscita"); } mostra(); });
      });
    });
  }
  mostra();
})();
</script></body></html>"""

def notifiche_account_attive(email):
    """True se almeno un dispositivo di questo account ha attivato le notifiche (le iscrizioni le tiene il servizio notifiche)."""
    try:
        cart = os.environ.get("PETHEALTH_DIR") or os.path.dirname(os.path.abspath(DATA_FILE))
        p = os.path.join(cart, "push_iscrizioni.json")
        stt = os.stat(p)
        cache = st.session_state.get("_push_cache")
        if not cache or cache[0] != (stt.st_mtime_ns, stt.st_size):
            with open(p, "r", encoding="utf-8") as f:
                dati = json.load(f) or {}
            cache = ((stt.st_mtime_ns, stt.st_size), dati)
            st.session_state["_push_cache"] = cache
        return bool(cache[1].get(email))
    except Exception:
        return False

_JS_AUTO_NOTIFICHE = r"""
(function () {
  var TOKEN = "__TOKEN__", ID = "ph-push-banner";
  if (document.getElementById(ID)) return;
  function risolto() { try { document.cookie = "ph_push_ok=1; Max-Age=31536000; Path=/; Secure; SameSite=Lax"; } catch (e) {} }
  function rimuovi() { var e = document.getElementById(ID); if (e && e.parentNode) e.parentNode.removeChild(e); }
  function u8(t) { t = t.replace(/-/g, "+").replace(/_/g, "/"); var r = atob(t + "===".slice((t.length + 3) % 4)); var a = new Uint8Array(r.length); for (var i = 0; i < r.length; i++) a[i] = r.charCodeAt(i); return a; }
  var ua = navigator.userAgent || "";
  var ios = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  var standalone = false; try { standalone = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true; } catch (e) {}
  var rifiutato = false; try { rifiutato = localStorage.getItem("ph_push_no") === "1"; } catch (e) {}
  if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) { risolto(); return; }
  if (ios && !standalone) { risolto(); return; }
  if (Notification.permission === "denied") { risolto(); return; }
  function pronta() {
    var attesa = new Promise(function (_, no) { setTimeout(function () { no(new Error("non pronta")); }, 10000); });
    return Promise.race([navigator.serviceWorker.ready, attesa]);
  }
  function iscrivi(reg) {
    return fetch("/push/chiave").then(function (r) { return r.json(); }).then(function (k) {
      return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: u8(k.chiave) });
    }).then(function (sub) {
      return fetch("/push/iscrivi", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token: TOKEN, subscription: sub.toJSON() }) });
    });
  }
  // Avviso FISSO in basso allo schermo: non occupa spazio nella pagina e non sposta nulla.
  function banner(testo, bottoni) {
    rimuovi();
    var d = document.createElement("div"); d.id = ID;
    d.setAttribute("style", "position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom, 0px));max-width:560px;margin:0 auto;z-index:2147483000;" +
      "background:#F4EEDD;border:1.5px solid #B8975A;border-radius:16px;padding:14px;box-shadow:0 10px 30px rgba(20,41,30,.25);" +
      "font:15px/1.45 Helvetica,Arial,sans-serif;color:#1E293B;");
    var p = document.createElement("p"); p.setAttribute("style", "margin:0 0 10px"); p.textContent = testo; d.appendChild(p);
    (bottoni || []).forEach(function (b) {
      var x = document.createElement("button"); x.type = "button"; x.textContent = b.t;
      x.setAttribute("style", "font:700 15px Helvetica,Arial,sans-serif;border:0;border-radius:99px;padding:12px 18px;min-height:46px;margin:0 8px 4px 0;cursor:pointer;" +
        (b.p ? "background:#1FA0E3;color:#fff" : "background:#E2E8F0;color:#1E293B"));
      x.onclick = b.f; d.appendChild(x);
    });
    document.body.appendChild(d);
  }
  pronta().then(function (reg) {
    return reg.pushManager.getSubscription().then(function (sub) {
      if (sub) { risolto(); return; }                                             // questo dispositivo è già a posto
      if (Notification.permission === "granted") { return iscrivi(reg).then(risolto); }   // permesso già dato: lo attivo in silenzio
      if (rifiutato) { risolto(); return; }
      banner("🔔 Hai già attivato le notifiche dei richiami con il tuo account. Attivale anche su questo dispositivo: basta un tocco.", [
        { t: "Attiva su questo dispositivo", p: true, f: function () {
            Notification.requestPermission().then(function (perm) {
              if (perm !== "granted") { banner("Senza il permesso questo dispositivo non può ricevere le notifiche.", [{ t: "Chiudi", f: function () { risolto(); rimuovi(); } }]); return; }
              return iscrivi(reg).then(function () { risolto(); banner("✅ Notifiche attive anche su questo dispositivo.", []); setTimeout(rimuovi, 3500); });
            }).catch(function () {});
        } },
        { t: "Non ora", f: function () { try { localStorage.setItem("ph_push_no", "1"); } catch (e) {} risolto(); rimuovi(); } }
      ]);
    });
  }).catch(function () {});
})();
"""

def push_dispositivo_a_posto():
    """True se su QUESTO dispositivo la questione notifiche è già risolta (attive, rifiutate o non supportate): niente riquadro e niente spazio."""
    v = st.session_state.get("_push_ok")
    if v is None:
        try:
            v = st.context.cookies.get("ph_push_ok") == "1"
        except Exception:
            v = False
        st.session_state["_push_ok"] = v
    return bool(v)

def blocco_auto_notifiche(email):
    """Piccolo script senza spazio: costruisce nella pagina un avviso fisso in basso (e gira nel contesto della pagina, non dell'iframe)."""
    logica = _JS_AUTO_NOTIFICHE.replace("__TOKEN__", token_push(email))
    return ("<script>(function(){var P;try{void window.parent.document;P=window.parent;}catch(e){P=window;}"
            "try{(new P.Function(" + json.dumps(logica) + "))();}catch(e){}})();</script>")

def blocco_notifiche(email):
    return _HTML_NOTIFICHE.replace("__TOKEN__", token_push(email))

def revoca_sessione_dispositivo(email, tutte=False):
    if not st.session_state.db_users.get(email):
        return
    mio = st.session_state.get("ph_jti")
    e2, jti2, _ = _leggi_cookie_sessione()
    def _agg(sess):
        if tutte:
            sess.clear()
        else:
            sess.pop(mio, None)
            if e2 == email:
                sess.pop(jti2, None)
    _aggiorna_sessioni(email, _agg)
    st.session_state.ph_jti = None

def entra_con_demo():
    email = "demo@pethealth.it"
    st.session_state.db_users[email] = _dati_demo()
    st.session_state.logged_user_email = email
    st.session_state.sezione_attiva = "dashboard"
    salva_dati()
    st.rerun()

# ---------------------------------------------------------------------------
# CHIAVE SEGRETA (usata per firmare sessioni, codici e notifiche)
# ---------------------------------------------------------------------------

def _chiave_sigillo():
    """Chiave segreta con cui si firmano i sigilli. Meglio impostarla nei Secrets (sigillo_chiave)."""
    try:
        k = st.secrets["sigillo_chiave"]
        if k:
            return str(k).encode("utf-8")
    except Exception:
        pass
    k = st.session_state.get("chiave_sigillo")
    if not k:
        k = (carica_dati() or {}).get("chiave_sigillo") or secrets.token_hex(32)
        st.session_state.chiave_sigillo = k
        salva_dati()
        k = st.session_state.get("chiave_sigillo") or k
    return str(k).encode("utf-8")

def qr_png(testo):
    try:
        import qrcode
        img = qrcode.make(testo)
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None

# ---------------------------------------------------------------------------
# RICHIAMI (promemoria di un controllo futuro) ed ELIMINAZIONE delle visite
# ---------------------------------------------------------------------------
def richiamo_attivo(v):
    """True se la visita ha un richiamo da fare (con una data valida)."""
    if not _data_o_none(v.get("prossimo_controllo_data")):
        return False
    if "richiamo" in v:
        return bool(v.get("richiamo"))
    return True   # visite vecchie che avevano già una data di prossimo controllo

def descrizione_richiamo(v):
    base = (v.get("prossimo_controllo_tipo") or "").strip()
    if not base:
        base = "Richiamo vaccino" if v.get("tipo") == "Vaccinazione" else "Richiamo / controllo"
    nome = (v.get("nome_vaccino") or "").strip()
    return f"{base} ({nome})" if nome and nome.lower() not in base.lower() else base

def campi_richiamo(chiave, tipo_visita):
    """Casella «serve un richiamo» + data + descrizione. Restituisce (attivo, data, descrizione)."""
    attivo = st.checkbox("🔔 Serve un richiamo / un controllo futuro", key=f"{chiave}_ric_on",
                         help="Se la spunti compare un promemoria nella dashboard e l'app ti manda una notifica 2 giorni prima della data che scegli.")
    if not attivo:
        return False, None, ""
    giorni = 365 if tipo_visita == "Vaccinazione" else 30
    c1, c2 = st.columns(2)
    with c1:
        data_r = st.date_input("Data del richiamo", format="DD/MM/YYYY", value=date.today() + timedelta(days=giorni),
                               min_value=date.today(), key=f"{chiave}_ric_data")
    with c2:
        desc = st.text_input("Che richiamo è? (facoltativo)", key=f"{chiave}_ric_desc",
                             placeholder="es. Richiamo antirabbica")
    st.caption("Il promemoria comparirà nella dashboard e l'app ti avviserà con una notifica 2 giorni prima (attivala da «App e notifiche»). La data la scegli tu e si può cambiare in qualsiasi momento.")
    return True, data_r, desc.strip()

def modifica_richiamo_visita(v, chiave):
    """Imposta, cambia o toglie il richiamo di una visita già registrata."""
    if ospite_solo_aggiunta():
        mostra_riga_richiamo(v)
        return
    attivo_ora = richiamo_attivo(v)
    c_on = st.checkbox("🔔 Serve un richiamo", value=attivo_ora, key=f"ric_ed_on_{chiave}")
    nuova_data, nuovo_tipo = None, ""
    if c_on:
        d0 = _data_o_none(v.get("prossimo_controllo_data")) or (date.today() + timedelta(days=30))
        c1, c2 = st.columns(2)
        with c1:
            nuova_data = st.date_input("Data del richiamo", format="DD/MM/YYYY", value=d0, key=f"ric_ed_data_{chiave}")
        with c2:
            nuovo_tipo = st.text_input("Che richiamo è?", value=v.get("prossimo_controllo_tipo", "") or "", key=f"ric_ed_tipo_{chiave}")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💾 Salva richiamo", key=f"ric_ed_salva_{chiave}"):
            v["richiamo"] = bool(c_on)
            v["prossimo_controllo_data"] = str(nuova_data) if (c_on and nuova_data) else ""
            v["prossimo_controllo_tipo"] = nuovo_tipo.strip() if c_on else ""
            v["richiamo_da"] = "proprietario" if c_on else ""
            salva_dati(); st.rerun()
    with b2:
        if attivo_ora and st.button("✔ Richiamo eseguito", key=f"ric_ed_fatto_{chiave}"):
            v["richiamo"] = False
            v["richiamo_eseguito_il"] = str(date.today())
            salva_dati(); st.rerun()

def mostra_riga_richiamo(v):
    """Riga di sola lettura con il richiamo programmato (se c'è)."""
    if not richiamo_attivo(v):
        return
    d = _data_o_none(v.get("prossimo_controllo_data"))
    giorni = (d - date.today()).days
    quando = f"scaduto da {-giorni} giorni" if giorni < 0 else ("oggi" if giorni == 0 else f"tra {giorni} giorni")
    da = " · deciso dal veterinario" if v.get("richiamo_da") == "veterinario" else ""
    st.info(f"🔔 **{descrizione_richiamo(v)}** · {d.strftime('%d/%m/%Y')} ({quando}){da}")

def elimina_visita(lista, v):
    if ospite_solo_aggiunta():
        return
    """Toglie la visita dal libretto e annulla l'eventuale richiesta di firma ancora in attesa."""
    elimina_file_referti(v)
    for i, x in enumerate(lista):
        if x is v:
            lista.pop(i)
            break
    else:
        idp = v.get("id_prestazione")
        if idp:
            lista[:] = [x for x in lista if x.get("id_prestazione") != idp]
    salva_dati()

def pulsante_elimina_visita(lista, v, chiave):
    """Pulsante «Elimina» con conferma. Dopo l'eliminazione sparisce anche dalla dashboard."""
    if ospite_solo_aggiunta():
        return
    k_conf = f"conf_del_vis_{chiave}"
    if not st.session_state.get(k_conf):
        if st.button("🗑️ Elimina questa visita", key=f"del_vis_{chiave}"):
            st.session_state[k_conf] = True
            st.rerun()
        return
    st.warning("Vuoi eliminare questa visita? L'operazione non si può annullare.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Sì, elimina", key=f"del_vis_si_{chiave}", type="primary"):
            st.session_state.pop(k_conf, None)
            elimina_visita(lista, v)
            st.session_state.visita_flash = "Visita eliminata."
            st.rerun()
    with c2:
        if st.button("No, tienila", key=f"del_vis_no_{chiave}"):
            st.session_state.pop(k_conf, None)
            st.rerun()

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


_CSS_ACCESSO_AZZURRO = r'''
html body .stApp, html body .stApp [data-testid="stAppViewContainer"], html body .stApp [data-testid="stMain"] {
background-color: #CFE9F8 !important; background-image: linear-gradient(160deg, #DDF0FB 0%, #CBE7F7 55%, #B9DDF3 100%) !important; background-attachment: fixed !important; }
html body .stApp .ph-hero-eyebrow { color: #8A6A1F !important; }
html body .stApp .ph-hero-title, html body .stApp [data-testid="stMarkdownContainer"] .ph-hero-title { color: #14291E !important; -webkit-text-fill-color: #14291E !important; }
html body .stApp .ph-hero-title em, html body .stApp [data-testid="stMarkdownContainer"] .ph-hero-title em {
background: linear-gradient(100deg, #8A6A1F 0%, #C09A3E 25%, #8A6A1F 50%, #C09A3E 75%, #8A6A1F 100%); background-size: 200% 100%;
-webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent !important; color: transparent !important; }
html body .stApp .ph-hero-text, html body .stApp [data-testid="stMarkdownContainer"] p.ph-hero-text { color: #14291E !important; -webkit-text-fill-color: #14291E !important; opacity: 1; }
html body .stApp .ph-punti li { color: #14291E !important; -webkit-text-fill-color: #14291E !important; border-top-color: rgba(138, 106, 31, .38); }
html body .stApp .ph-punti li svg { stroke: #8A6A1F; }
html body .stApp .ph-logo .ph-logo-name { color: #111111 !important; -webkit-text-fill-color: #111111 !important; }
html body .stApp .ph-logo .ph-logo-health { color: #111111 !important; -webkit-text-fill-color: #111111 !important; }
html body .stApp .ph-logo .ph-logo-tag { color: #8A6A1F !important; -webkit-text-fill-color: #8A6A1F !important; }
html body .stApp [data-testid="stMain"] .stButton > button, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button,
html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-primary"], html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-secondary"],
html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-primaryFormSubmit"], html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-secondaryFormSubmit"] {
background: #1FA0E3 !important; background-image: none !important;
border: 1px solid #1789C6 !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; box-shadow: 0 6px 14px -6px rgba(3, 105, 161, .55) !important; }
html body .stApp [data-testid="stMain"] .stButton > button:hover, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:hover,
html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-primary"]:hover, html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover,
html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-primaryFormSubmit"]:hover, html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-secondaryFormSubmit"]:hover {
background: #158FD0 !important; background-image: none !important; }
html body .stApp [data-testid="stMain"] .stButton > button p, html body .stApp [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button p,
html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-secondary"] p, html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-primary"] p,
html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-secondaryFormSubmit"] p, html body .stApp [data-testid="stMain"] [data-testid="stBaseButton-primaryFormSubmit"] p { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
'''

_CSS_ACCESSO = """
.stApp, [data-testid="stAppViewContainer"], section.main, [data-testid="stMain"] {
    background-color: #1E3A2B !important; background-image: none !important; }
.stApp::before { content: ""; position: fixed; left: 0; top: 0; bottom: 0; width: 10px; background: #0284C7; z-index: 999; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container { max-width: 1100px !important; padding-top: 1.4rem !important; }
.ph-auth-top { padding: 4px 0 28px 0; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.ph-auth-marker) {
    background: #FFFFFF !important; border: 1px solid #D9BF86 !important; border-radius: 22px !important;
    padding: 14px 16px 18px 16px !important; box-shadow: 0 24px 60px -20px rgba(0,0,0,0.55) !important; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.ph-auth-marker) [data-testid="stForm"] {
    border: none !important; box-shadow: none !important; padding: 0 !important; background: transparent !important; }
[data-baseweb="tab-list"] { background: #F1ECDD !important; border-radius: 99px !important; padding: 4px !important; gap: 2px !important; }
button[data-baseweb="tab"] { flex: 1 1 0 !important; justify-content: center !important; border-radius: 99px !important; height: 40px !important;
    background: transparent !important; color: #5B6A62 !important; }
button[data-baseweb="tab"][aria-selected="true"] { background: #FFFFFF !important; color: #1E293B !important; box-shadow: 0 2px 8px -2px rgba(0,0,0,0.2) !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
.ph-hero-eyebrow { font: 700 11px/1 'Plus Jakarta Sans', sans-serif; letter-spacing: 0.16em; text-transform: uppercase; color: #D9BF86 !important; }
/* --- testi chiari sul verde (regole forti: battono il colore scuro globale dei paragrafi) --- */
html body .stApp .ph-hero-title, html body .stApp [data-testid="stMarkdownContainer"] .ph-hero-title {
    font-family: 'Fraunces', Georgia, serif !important; font-weight: 600 !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important;
    font-size: clamp(2.2rem, 5vw, 4.3rem) !important; line-height: 1.08 !important; margin: 18px 0 0 0 !important; padding: 0 !important; letter-spacing: -0.02em !important; }
html body .stApp .ph-hero-title em, html body .stApp [data-testid="stMarkdownContainer"] .ph-hero-title em {
    color: #D9BF86 !important; -webkit-text-fill-color: #D9BF86 !important; font-weight: 400 !important; font-style: italic !important; }
html body .stApp .ph-hero-text, html body .stApp [data-testid="stMarkdownContainer"] p.ph-hero-text {
    color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-size: 1.1rem !important; max-width: 46ch; margin: 22px 0 0 0 !important; opacity: 0.92; }
html body .stApp .ph-logo .ph-logo-name { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }
html body .stApp .ph-logo .ph-logo-health { color: #8FD3F8 !important; -webkit-text-fill-color: #8FD3F8 !important; }
html body .stApp .ph-logo .ph-logo-tag { color: #D9BF86 !important; -webkit-text-fill-color: #D9BF86 !important; }
/* --- la scheda bianca è la colonna di destra: schede e moduli stanno sempre su fondo chiaro --- */
[data-testid="stColumn"]:has(.ph-auth-marker) {
    background: #FFFFFF !important; border: 1px solid #D9BF86 !important; border-radius: 22px !important;
    padding: 14px 16px 18px 16px !important; box-shadow: 0 24px 60px -20px rgba(0,0,0,0.55) !important; }
[data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stVerticalBlockBorderWrapper"] { border: none !important; background: transparent !important; box-shadow: none !important; padding: 0 !important; }
[data-testid="stColumn"]:has(.ph-auth-marker) [role="tablist"] { background: #F1ECDD !important; border-radius: 99px !important; padding: 4px !important; gap: 2px !important; }
[data-testid="stColumn"]:has(.ph-auth-marker) button[role="tab"] { flex: 1 1 0 !important; justify-content: center !important; border-radius: 99px !important; height: 40px !important;
    background: transparent !important; color: #5B6A62 !important; -webkit-text-fill-color: #5B6A62 !important; }
[data-testid="stColumn"]:has(.ph-auth-marker) button[role="tab"] p { color: inherit !important; -webkit-text-fill-color: inherit !important; }
[data-testid="stColumn"]:has(.ph-auth-marker) button[role="tab"][aria-selected="true"] { background: #FFFFFF !important; color: #0369A1 !important;
    -webkit-text-fill-color: #0369A1 !important; box-shadow: 0 2px 8px -2px rgba(0,0,0,0.2) !important; }
[data-testid="stColumn"]:has(.ph-auth-marker) [data-testid="stForm"] { border: none !important; box-shadow: none !important; padding: 0 !important; background: transparent !important; }
.ph-posta { background: #F4EEDD; border: 1.5px dashed #B8975A; border-radius: 14px; padding: 14px 16px; margin: 10px 0 14px 0; color: #1E293B; }
.ph-posta code { font-size: 1.5rem !important; letter-spacing: 0.2em; background: #FFFFFF !important; color: #0369A1 !important; padding: 4px 12px !important; }
.ph-demo { background: #F4EEDD; border: 1px solid #B8975A; border-radius: 16px; padding: 14px 16px; margin-top: 18px; color: #1E293B; font-size: 0.9rem; }
"""

try:
    _pag_pub = st.query_params.get("pagina")
except Exception:
    _pag_pub = None
if isinstance(_pag_pub, str) and _pag_pub in _TITOLI_PAGINE:
    mostra_pagina_pubblica(_pag_pub)
    st.stop()
if _param_url("libretto"):
    mostra_libretto_condiviso(_param_url("libretto"))
    st.stop()
if _param_url("animale"):
    mostra_scheda_smarrito(_param_url("animale"))
    st.stop()

if st.session_state.logged_user_email is None and not st.session_state.get("ph_no_autologin"):
    _em_ck, _jti_ck = utente_da_cookie()
    if _em_ck:
        st.session_state.logged_user_email = _em_ck
        st.session_state.ph_jti = _jti_ck
        st.session_state.sezione_attiva = "dashboard"

if st.session_state.logged_user_email is None:
    aggiorna_altri_utenti_da_disco()
    if not st.session_state.get("off_pulito"):                      # nessun accesso: sul dispositivo non resta nessuna copia del libretto
        st.session_state["off_pulito"] = True
        components.html(JS_OFFLINE_PULISCI, height=0, width=0)
    st.markdown("<style>" + _compatta_css(_CSS_ACCESSO + _CSS_RESTYLING_ACCESSO + _CSS_ACCESSO_AZZURRO + _SFONDO_LIBRETTO) + "</style>", unsafe_allow_html=True)
    try:
        pulisci_account_non_attivati()
    except Exception as _e:
        print(f"[PetHealth] pulizia account non attivati: {_e!r}", file=sys.stderr)
    st.markdown('<div class="ph-auth-top">' + logo_html() + '</div>', unsafe_allow_html=True)

    col_hero, col_card = st.columns([1.1, 0.9], gap="large")
    with col_hero:
        st.markdown(
            '<div style="padding-top:2.2rem">'
            '<span class="ph-hero-eyebrow">Area riservata</span>'
            '<h1 class="ph-hero-title">'
            'Bentornato,<br><em>libretto alla mano.</em></h1>'
            '<p class="ph-hero-text">'
            'Vaccini, terapie, peso e calore di ogni animale, sempre aggiornati e con i promemoria al posto giusto.</p>'
            + hero_punti_html(["Vaccini e richiami sempre sotto controllo", "Terapie con promemoria sul telefono",
                               "Libretto condiviso con la famiglia e con il veterinario"]) + '</div>',
            unsafe_allow_html=True)

    with col_card:
        with st.container(border=True):
            st.markdown('<span class="ph-auth-marker"></span>', unsafe_allow_html=True)
            if st.session_state.pop("account_eliminato", False):
                st.success("Il tuo account e tutti i tuoi dati sono stati eliminati. Grazie per aver usato PetHealth.")
            _p2 = st.session_state.get("login_2fa")
            if _p2 and datetime.now().timestamp() - float(_p2.get("quando", 0)) > float(_p2.get("durata", 300)):      # il secondo passaggio vale 5 minuti (10 se il codice arriva per email)
                st.session_state.pop("login_2fa", None)
                _p2 = None
            if _p2:
                mostra_login_2fa(_p2)
                st.stop()
            auth_tab1, auth_tab2, auth_tab3 = st.tabs(["Accedi", "Registrati", "Attiva"])

            # SCHEDA ACCESSO
            with auth_tab1:
                st.write("")
                with st.form("form_login"):
                    login_email = st.text_input("Email", placeholder="es. mario.rossi@email.it")
                    login_pass = st.text_input("Password", type="password", placeholder="••••••••")
                    login_ricorda = st.checkbox("Resta connesso su questo dispositivo", value=True,
                                                help="Non dovrai rifare l'accesso ogni volta. Sui dispositivi di altri togli la spunta.")
                    btn_login = st.form_submit_button("Accedi")
                    if btn_login:
                        email_clean = login_email.strip().lower()
                        attesa = secondi_blocco("login", email_clean)
                        if attesa:
                            st.error(testo_attesa(attesa))
                        else:
                            users_db = st.session_state.db_users
                            user_info = users_db.get(email_clean)
                            if not user_info or account_eliminato_su_disco(email_clean) or not verifica_password(login_pass, user_info.get("password", "")):
                                registra_fallimento("login", email_clean)
                                st.error("Email o password non corretti.")
                            elif user_info.get("stato") == "in_attesa":
                                azzera_tentativi("login", email_clean)
                                st.warning("Il tuo profilo richiede prima l'attivazione: apri la scheda «Attiva».")
                                st.session_state.verification_pending_email = email_clean
                            else:
                                azzera_tentativi("login", email_clean)
                                if password_da_aggiornare(user_info.get("password", "")):
                                    user_info["password"] = hash_password(login_pass)   # aggiorna i vecchi account al formato attuale
                                    salva_dati(extra_email=email_clean)
                                if totp_attivo(user_info):                                # password giusta: manca ancora il secondo codice
                                    _p2n = {"email": email_clean, "ricorda": bool(login_ricorda), "quando": datetime.now().timestamp()}
                                    if totp_metodo(user_info) == "email":
                                        _p2n["pratica"], _p2n["errore_invio"] = invia_codice_2fa(email_clean, user_info.get("nome", ""))
                                        _p2n["durata"] = 600
                                    st.session_state["login_2fa"] = _p2n
                                    st.rerun()
                                completa_accesso(email_clean, login_ricorda)

                # PASSWORD DIMENTICATA (proprietari): codice a 6 cifre per email, mai mostrato a schermo
                with st.expander("Password dimenticata?", expanded=bool(st.session_state.get("reset_fase"))):
                    if not email_configurata() and not modalita_prova():
                        st.info("Il recupero automatico non è al momento disponibile. Scrivi a " + (contatto_assistenza() or "l'assistenza") + " e ti aiutiamo noi.")
                    else:
                        fase = st.session_state.get("reset_fase")
                        if not fase:
                            with st.form("form_reset_1"):
                                r_email = st.text_input("La tua email", key="reset_email_in")
                                if st.form_submit_button("Inviami il codice"):
                                    em = r_email.strip().lower()
                                    attesa = secondi_blocco("reset-richiesta", em)
                                    if "@" not in em:
                                        st.error("Inserisci l'email con cui ti sei registrato.")
                                    elif attesa:
                                        st.error(testo_attesa(attesa))
                                    else:
                                        registra_fallimento("reset-richiesta", em)       # ogni richiesta conta: al massimo 5 ogni 15 minuti
                                        codice = richiedi_reset_proprietario(em)
                                        st.session_state.reset_codice_prova = codice if modalita_prova() else None
                                        st.session_state.reset_fase = em
                                        st.rerun()
                        else:
                            st.success("Se l'indirizzo è registrato, ti abbiamo inviato un codice di 6 cifre: vale 15 minuti. Controlla anche lo spam.")
                            if st.session_state.get("reset_codice_prova"):
                                st.info("Modalità prova · codice: " + st.session_state["reset_codice_prova"])
                            with st.form("form_reset_2"):
                                c_cod = st.text_input("Codice (6 cifre)", max_chars=8)
                                n1 = st.text_input("Nuova password (min. 10 caratteri)", type="password", key="reset_n1")
                                n2 = st.text_input("Ripeti la nuova password", type="password", key="reset_n2")
                                if st.form_submit_button("Imposta la nuova password"):
                                    attesa = secondi_blocco("reset-codice", fase)
                                    rec = st.session_state.db_users.get(fase)
                                    if attesa:
                                        st.error(testo_attesa(attesa))
                                    elif n1 != n2:
                                        st.error("Le due password non coincidono.")
                                    elif controlla_password_nuova(n1, fase):
                                        st.error(controlla_password_nuova(n1, fase))
                                    elif not rec:
                                        registra_fallimento("reset-codice", fase)
                                        st.error("Codice non valido o scaduto: richiedine uno nuovo.")
                                    else:
                                        ok_cod, msg_cod = controlla_codice_reset(rec, fase, c_cod)
                                        if not ok_cod:
                                            registra_fallimento("reset-codice", fase)
                                            salva_dati(extra_email=fase)
                                            st.error(msg_cod)
                                        else:
                                            rec["password"] = hash_password(n1)
                                            rec.pop("reset_pw", None)
                                            salva_dati(extra_email=fase)
                                            _aggiorna_sessioni(fase, lambda s: s.clear())          # tutti i dispositivi devono rifare l'accesso
                                            azzera_tentativi("reset-codice", fase); azzera_tentativi("login", fase)
                                            st.session_state.reset_fase = None
                                            st.session_state.reset_codice_prova = None
                                            st.success("Password cambiata. Ora puoi accedere con la nuova password.")
                            if st.button("Ricomincia", key="reset_ricomincia"):
                                st.session_state.reset_fase = None
                                st.rerun()

            # SCHEDA REGISTRAZIONE
            with auth_tab2:
                st.write("")
                with st.form("form_registrazione"):
                    reg_nome = st.text_input("Nome e cognome*", placeholder="es. Mario Rossi")
                    reg_email = st.text_input("Email*", placeholder="es. mario.rossi@email.it")
                    reg_telefono = st.text_input("Cellulare / WhatsApp*", placeholder="es. +39 333 1234567")
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        reg_pass = st.text_input("Password (min. 10)*", type="password")
                    with col_p2:
                        reg_pass_conf = st.text_input("Conferma password*", type="password")
                    st.markdown('<div style="font-size:0.85rem">Leggi l\'<a href="?pagina=privacy" target="_blank">informativa privacy</a> e i '
                                '<a href="?pagina=termini" target="_blank">termini di utilizzo</a>.</div>', unsafe_allow_html=True)
                    reg_privacy = st.checkbox("Ho letto l'informativa privacy e accetto i termini di utilizzo. Dichiaro di avere almeno 18 anni.")
                    btn_register = st.form_submit_button("Crea account")
                    if btn_register:
                        email_c = reg_email.strip().lower()
                        attesa = secondi_blocco("registra", email_c)
                        if attesa:
                            st.error(testo_attesa(attesa))
                        elif not reg_nome.strip() or not email_c or "@" not in email_c or not reg_pass or not reg_telefono.strip():
                            st.error("Compila tutti i campi obbligatori marcati con (*).")
                        elif reg_pass != reg_pass_conf:
                            st.error("Le password inserite non corrispondono.")
                        elif controlla_password_nuova(reg_pass, email_c):
                            st.error(controlla_password_nuova(reg_pass, email_c))
                        elif not reg_privacy:
                            st.error("Serve il consenso all'informativa privacy e ai termini.")
                        else:
                            registra_fallimento("registra", email_c)                # ogni registrazione conta per il limite
                            if account_eliminato_su_disco(email_c):
                                st.session_state.db_users.pop(email_c, None)         # chi si era cancellato può tornare
                            if email_c in st.session_state.db_users:
                                st.error("Esiste già un profilo con questa email.")
                            else:
                                riabilita_email(email_c)
                                st.session_state.db_users[email_c] = {
                                    "nome": reg_nome.strip(), "email": email_c, "password": hash_password(reg_pass),
                                    "numero_whatsapp": reg_telefono.strip(), "numero_whatsapp_2": "", "stato": "in_attesa",
                                    "consenso_privacy": str(date.today()), "versione_informativa": VERSIONE_INFORMATIVA,
                                    "data_registrazione": str(date.today()),
                                    "lista_animali": [], "pet_selezionato": None, "db_visite": {}, "db_terapie": {},
                                    "db_fatture": {}, "db_peso": {}, "db_calori": {}, "db_anagrafica": {}, "angeli_archiviati": {}
                                }
                                inviata = nuovo_codice_attivazione(email_c)
                                if inviata:
                                    st.success("Account creato. Ti abbiamo inviato il codice di attivazione per email: inseriscilo nella scheda «Attiva».")
                                elif modalita_prova():
                                    st.success("Account creato (modalità prova). Apri la scheda «Attiva»: il codice è mostrato lì.")
                                else:
                                    st.error("Account creato, ma non siamo riusciti a inviare l'email con il codice. Riprova più tardi dalla scheda «Attiva» "
                                             "(«Invia un nuovo codice») oppure scrivi a " + (contatto_assistenza() or "l'assistenza") + ".")

            # SCHEDA ATTIVAZIONE
            with auth_tab3:
                st.write("")
                target_email = st.session_state.get("verification_pending_email") or ""
                posta = st.session_state.get("posta_demo")
                if posta and posta.get("email") == target_email and modalita_prova():
                    st.markdown(
                        '<div class="ph-posta"><b>Modalità prova · posta simulata</b><br>'
                        'Questo riquadro compare solo con «modalita_prova» attiva. In produzione il codice arriva solo nella tua casella email.'
                        f'<div style="margin-top:8px"><code>{html_escape(posta["codice"])}</code></div></div>', unsafe_allow_html=True)
                with st.form("form_attivazione"):
                    att_email = st.text_input("Email", value=target_email)
                    att_codice = st.text_input("Codice di attivazione (6 cifre)", max_chars=8)
                    btn_att = st.form_submit_button("Attiva e accedi")
                    if btn_att:
                        em = att_email.strip().lower()
                        attesa = secondi_blocco("attivazione", em)
                        u = st.session_state.db_users.get(em)
                        if attesa:
                            st.error(testo_attesa(attesa))
                        elif not u:
                            registra_fallimento("attivazione", em)
                            st.error("Account non trovato.")
                        elif u.get("stato") == "attivo":
                            st.success("Questo account è già attivo: usa la scheda «Accedi».")
                        else:
                            scad = u.get("codice_scadenza")
                            scaduto = False
                            try:
                                scaduto = bool(scad) and datetime.now() > datetime.fromisoformat(scad)
                            except Exception:
                                scaduto = False
                            if scaduto:
                                st.error("Codice scaduto: richiedine uno nuovo.")
                            elif not att_codice.strip() or not hmac.compare_digest(att_codice.strip().upper(), str(u.get("codice_conferma", "")).upper()):
                                registra_fallimento("attivazione", em)
                                st.error("Codice non corretto.")
                            else:
                                azzera_tentativi("attivazione", em)
                                st.session_state.verification_pending_email = em
                                u["stato"] = "attivo"
                                u.pop("codice_conferma", None); u.pop("codice_scadenza", None)
                                st.session_state.logged_user_email = em
                                st.session_state.sezione_attiva = "dashboard"
                                st.session_state.posta_demo = None
                                st.session_state.ph_no_autologin = False
                                salva_dati()
                                st.session_state.ph_cookie_scrivi = crea_sessione_dispositivo(em)
                                st.rerun()
                if st.button("Invia un nuovo codice", key="reinvia_codice"):
                    em = (target_email or "").strip().lower()
                    attesa = secondi_blocco("reinvio", em)
                    if attesa:
                        st.error(testo_attesa(attesa))
                    elif em in st.session_state.db_users and st.session_state.db_users[em].get("stato") != "attivo":
                        registra_fallimento("reinvio", em)
                        inviata = nuovo_codice_attivazione(em)
                        if inviata:
                            st.success("Nuovo codice inviato per email.")
                        elif modalita_prova():
                            st.rerun()
                        else:
                            st.error("Invio dell'email non riuscito. Riprova tra poco o scrivi a " + (contatto_assistenza() or "l'assistenza") + ".")
                    else:
                        st.error("Inserisci prima l'email con cui ti sei registrato.")

            st.markdown('<div class="ph-demo"><b>Provalo subito.</b> Carica un account di esempio con Luna e Micio.</div>', unsafe_allow_html=True)
            if st.button("Entra con la demo", key="btn_demo"):
                entra_con_demo()
            st.markdown(link_legali_html(), unsafe_allow_html=True)

    st.stop()

user_email = st.session_state.logged_user_email
if user_email not in st.session_state.db_users or account_eliminato_su_disco(user_email):
    # l'account non esiste più (eliminato da questo o da un altro dispositivo): si esce
    st.session_state.db_users.pop(user_email, None)
    st.session_state.logged_user_email = None
    st.session_state.ph_no_autologin = True
    st.session_state.ph_cookie_cancella = True
    st.rerun()
login_email = user_email                                   # chi ha fatto l'accesso
user_email = risolvi_account_attivo(login_email)           # di chi sono i libretti che sta guardando
user_db = st.session_state.db_users[user_email]
st.session_state["off_pulito"] = False
allinea_offline_account(login_email)
sincronizza_offline(user_db)
nome_login = st.session_state.db_users[login_email].get("nome") or login_email
if _param_url("vai") == "smarrito":                          # arrivo dalla notifica «animale smarrito»
    st.session_state.sezione_attiva = "smarrito"
    try:
        del st.query_params["vai"]
    except Exception:
        pass
elif _param_url("vai") == "famiglia":                        # arrivo dal link dell'email d'invito
    st.session_state.sezione_attiva = "impostazioni"
    st.session_state["impost_sub"] = "condividi"
    try:
        del st.query_params["vai"]
    except Exception:
        pass

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
    st.markdown('<div class="ph-side-logo">' + logo_html(sidebar=True) + '</div>', unsafe_allow_html=True)
    st.caption("UTENTE REGISTRATO")
    voce_menu("👤 " + re.sub(r"([\\`*_\[\]~:<>$])", r"\\\1", str(nome_login)), "account")   # il nome utente apre l'account
    _inv_ric = inviti_ricevuti(login_email)
    if _inv_ric:
        mostra_avviso_inviti(login_email, "menu_inv", nel_menu=True)
    _fam_mie = famiglie_di(login_email)
    if _fam_mie:
        _opz_acc = [login_email] + [e for e, _n in _fam_mie]
        _nomi_acc = {login_email: "I miei libretti", **{e: f"Condiviso da {n}" for e, n in _fam_mie}}
        _sel_acc = st.selectbox("Libretti di", _opz_acc, index=_opz_acc.index(user_email) if user_email in _opz_acc else 0,
                                format_func=lambda e: _nomi_acc.get(e, e))
        if _sel_acc != user_email:
            st.session_state.account_attivo = None if _sel_acc == login_email else _sel_acc
            st.session_state.sezione_attiva = "dashboard"
            st.session_state.pop("pet_select", None)
            st.rerun()
    
    if not ospite_solo_aggiunta():
        voce_menu("🏥 La mia clinica di fiducia", "clinica")
    _n_sm = len(smarrimenti_della_provincia(st.session_state.db_users[login_email].get("provincia", ""), escludi_email=user_email)) \
        if login_email != "demo@pethealth.it" else 0
    # «Urgenze»: menù a tendina identico al selettore del libretto attivo; nel riquadro c'è scritto «Urgenze», le voci sono «Cliniche H24» (pagina urgenze) e «Animale smarrito»
    _sez_att = st.session_state.get("sezione_attiva")
    _opz_urg = ["urgenze", "smarrito"]
    _nomi_urg = {"urgenze": "🚨 Cliniche H24", "smarrito": "🐾 Animale smarrito" + (f" ({_n_sm})" if _n_sm else "")}
    _k_urg = f"menu_urg_{_sez_att if _sez_att in _opz_urg else 'nessuna'}"
    st.session_state["_menu_urg_chiave"] = _k_urg
    st.selectbox("Urgenze, cliniche H24 e animale smarrito", _opz_urg, index=1 if _sez_att == "smarrito" else None,
                 format_func=lambda s: _nomi_urg.get(s, s), placeholder="🚨 Urgenze", key=_k_urg,
                 label_visibility="collapsed", on_change=vai_da_menu_urgenze)
    voce_menu("⚙️ Impostazioni", "impostazioni")

    if st.button("🚪 Logout / Esci"):
        revoca_sessione_dispositivo(login_email)
        st.session_state.account_attivo = None
        st.session_state.logged_user_email = None
        st.session_state.ph_no_autologin = True
        st.session_state.ph_cookie_cancella = True
        st.rerun()
        
    st.markdown("---")
    
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
    
    voce_menu("🏠 Home", "dashboard")
    if not ospite_solo_aggiunta():
        voce_menu("📋 Anagrafica Pet & Proprietario", "anagrafica")
    voce_menu("🏥 Visite e Clinica", "visite")
    voce_menu("💊 Terapie e Farmaci", "terapie")
    voce_menu("Peso e Andamento", "peso", icona=":material/monitor_weight:")
    sesso_selezionato = (user_db["db_anagrafica"].get(pet_selected, {}) or {}).get("sesso") if pet_selected else None
    if sesso_selezionato == "Femmina" and not ospite_solo_aggiunta():
        voce_menu("🌸 Calore e Calendario", "calore")
    voce_menu("📄 Fatture e Spese", "fatture")
    voce_menu("📘 Libretto PDF (scarica)", "pdf_libretto")
    if not ospite_solo_aggiunta():
        voce_menu("🌈 I nostri angeli a 4 zampe", "angeli")
        st.write("")
        voce_menu("➕ Registra Nuovo Animale", "nuovo_animale")

if st.session_state.get("accesso_revocato"):
    st.warning(f"**{st.session_state.pop('accesso_revocato')}** ha interrotto la condivisione dei suoi libretti: ora vedi di nuovo solo i tuoi.")
if user_email != login_email:
    st.info(f"👪 Stai usando i libretti di **{user_db.get('nome', user_email)}**. Puoi **aggiungere** visite, terapie, pesate, fatture e spese; "
            "non puoi eliminare né modificare ciò che è già stato inserito. Per registrare un tuo animale scegli «I miei libretti» nel menu.")
    if st.session_state.sezione_attiva in ("anagrafica", "calore", "clinica", "angeli", "nuovo_animale"):
        st.session_state.sezione_attiva = "dashboard"
        st.warning("Quella sezione può essere modificata solo da chi ha creato il libretto.")

# Tasto «indietro» del telefono/browser: lo script in fondo alla pagina "preme" questo pulsante nascosto e riporta alla schermata iniziale.
if st.button("Torna alla schermata iniziale", key="torna_home_back"):
    if st.session_state.get("sezione_attiva") != "dashboard":
        cambia_sezione("dashboard")

_vista_impost = None
if st.session_state.get("sezione_attiva") == "passaporto":      # sezione tolta: chi ci arriva torna al riepilogo
    st.session_state.sezione_attiva = "dashboard"
if st.session_state.sezione_attiva == "impostazioni":
    st.markdown("<h2 style='color: #1E3A2B;'>⚙️ Impostazioni</h2>", unsafe_allow_html=True)
    _cols_imp = st.columns(3)
    with _cols_imp[0]:
        st.markdown('<span class="ph-impost-marker"></span>', unsafe_allow_html=True)
    for _col, (_k, _et) in zip(_cols_imp, _SOTTO_IMPOSTAZIONI):
        with _col:
            if st.button(_et, key=f"imp_{_k}", use_container_width=True,
                         type="primary" if st.session_state.get("impost_sub") == _k else "secondary"):
                st.session_state["impost_sub"] = _k
                st.rerun()
    st.markdown("---")
    _vista_impost = st.session_state.get("impost_sub")

if st.session_state.sezione_attiva == "dashboard":
    if pet_selected:
        terapie_pet = user_db["db_terapie"].get(pet_selected, [])
        visite_pet = user_db["db_visite"].get(pet_selected, [])
        if st.session_state.get("visita_flash"):
            st.success(st.session_state.pop("visita_flash"))
        if login_email != "demo@pethealth.it":
            mostra_invito_2fa(login_email, st.session_state.db_users[login_email])
            mostra_avviso_smarrimenti_dashboard(login_email, user_email, st.session_state.db_users[login_email])
            if _inv_ric:
                mostra_avviso_inviti(login_email, "dash_inv")
        if login_email != "demo@pethealth.it" and notifiche_account_attive(login_email) and not push_dispositivo_a_posto():
            components.html(blocco_auto_notifiche(login_email), height=0, width=0)
        mostra_intestazione_dashboard(user_db, pet_selected, visite_pet, terapie_pet)
        if True:   # terapie in somministrazione a tutta larghezza (prima)
            st.markdown(f"""
                <div class="wellness-card">
                    <span class="card-badge badge-purple">TERAPIE ATTIVE</span>
                    <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">💊 In Somministrazione</h3>
                </div>
            """, unsafe_allow_html=True)
            
            mostra_dosi_oggi(user_db, pet_selected, nome_login, "dash")
            _oggi_ter = date.today()
            _ter_attive = [(i, t) for i, t in enumerate(terapie_pet) if terapia_ancora_attiva(t, _oggi_ter)]    # in dashboard solo le somministrazioni in corso
            if _ter_attive:
                terapie_ordinate = sorted(_ter_attive, key=lambda x: x[1].get('data_inizio', ''), reverse=True)
                st.markdown(tabella_terapie_html([t for _i, t in terapie_ordinate[:15]]), unsafe_allow_html=True)
                if len(terapie_ordinate) > 15:
                    st.caption(f"Qui vedi le ultime 15 di {len(terapie_ordinate)} terapie: lo storico completo è in «Terapie e Farmaci».")
                if scheda_a_comparsa("dash_terapie_dettagli", "Dettagli e azioni delle terapie"):
                    with st.container(border=True):
                        for idx, t in terapie_ordinate[:15]:
                            orario_txt = t.get('orario', 'Non specificato')
                            with st.expander(f"💊 {t['farmaco']} ({t['periodo']}) - ⏰ {orario_txt}", expanded=False):
                                mostra_dettagli_terapia(pet_selected, t, idx, "dash")
            else:
                st.info(f"Nessuna terapia attiva registrata per {pet_selected}.")
                if terapie_pet:
                    st.caption("Le terapie concluse sono nello storico di «Terapie e Farmaci».")


        if True:   # visite dell'anno a tutta larghezza (sotto le terapie)
            st.markdown(f"""
                <div class="wellness-card">
                    <span class="card-badge badge-blue">ANNO IN CORSO</span>
                    <h3 style="margin-top: 5px; margin-bottom: 15px; color: #1E3A2B;">🪵 Visite del __ANNO__</h3>
                </div>
            """.replace("__ANNO__", str(date.today().year)), unsafe_allow_html=True)
            
            _anno_rif = str(date.today().year)
            visite_anno = [(i, v) for i, v in enumerate(visite_pet) if str(v.get("data", ""))[:4] == _anno_rif]
            if visite_pet:
                visite_ordinate = sorted(visite_anno, key=lambda x: x[1].get('data', ''), reverse=True)
                _prec = len(visite_pet) - len(visite_ordinate)
                if visite_ordinate:
                    st.markdown(tabella_visite_html([v for _i, v in visite_ordinate], user_db["db_anagrafica"].get(pet_selected, {})), unsafe_allow_html=True)
                else:
                    st.info(f"Nessuna visita registrata nel {_anno_rif}.")
                if _prec > 0:
                    st.caption(f"Le altre {_prec} visite degli anni precedenti sono nello storico di «Visite e Clinica».")
                if visite_ordinate and scheda_a_comparsa("dash_visite_dettagli", "Dettagli e azioni delle visite"):
                    with st.container(border=True):
                        for idx, v in visite_ordinate:
                            with st.expander(f"🏥 {v['tipo']} - {data_ui(v['data'])}", expanded=False):
                                if v.get('veterinario'): st.write(f"**Veterinario:** {v['veterinario']}")
                                if v.get('nome_vaccino'): st.write(f"💉 **Vaccino:** {v.get('nome_vaccino')} | **Lotto:** {v.get('lotto_vaccino', 'N/D')}")
                                mostra_immagine_salvata(v.get('etichetta_vaccino'), "🏷️ Etichetta del vaccino")
                                if v.get('diagnosi'): st.write(f"**Diagnosi:** {v['diagnosi']}")
                                mostra_riga_richiamo(v)
                                if richiamo_attivo(v):
                                    mostra_pulsanti_promemoria_visita(pet_selected, descrizione_richiamo(v), v.get('prossimo_controllo_data'), v.get('veterinario', ''), v.get('diagnosi', ''))
                                    if not ospite_solo_aggiunta() and st.button("✔ Richiamo eseguito", key=f"ric_fatto_dash_{v.get('id_prestazione') or idx}"):
                                        v["richiamo"] = False; v["richiamo_eseguito_il"] = str(date.today())
                                        salva_dati(); st.rerun()
                                else:
                                    mostra_pulsanti_promemoria_visita(pet_selected, v['tipo'], v['data'], v.get('veterinario', ''), v.get('diagnosi', ''))
                                pulsante_elimina_visita(visite_pet, v, f"dash_{v.get('id_prestazione') or idx}")
            else:
                st.info(f"Nessuna visita medica registrata per {pet_selected}.")

        st.write("")
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "anagrafica":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>📋 Scheda Anagrafica - {html_escape(pet_selected)}</h2>", unsafe_allow_html=True)
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
                    <p>• <strong>Specie:</strong> {html_escape(str(anagrafica_corrente.get('tipo_animale', 'N/D')))}</p>
                    <p>• <strong>Sesso:</strong> {html_escape(str(anagrafica_corrente.get('sesso') or 'Non specificato'))}</p>
                    <p>• <strong>Razza:</strong> {html_escape(str(anagrafica_corrente.get('razza') or 'Non specificata'))}</p>
                    <p>• <strong>Data Nascita:</strong> {html_escape(data_ui(anagrafica_corrente.get('data_nascita', 'N/D')))}</p>
                    <p>• <strong>Microchip:</strong> <code>{html_escape(str(anagrafica_corrente.get('microchip') or 'Non inserito'))}</code></p>{blocco_barcode}
                    <p>• <strong>Segni Particolari:</strong> {html_escape(str(anagrafica_corrente.get('segni_particolari') or 'Nessuno'))}</p>
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
                    <h3 style="color: #1E3A2B; margin-top: 5px; margin-bottom: 12px;">{html_escape(str(anagrafica_corrente.get('proprietario_nome') or user_db.get('nome') or ''))}</h3>
                    <p>• <strong>Indirizzo:</strong> {html_escape(str(anagrafica_corrente.get('proprietario_indirizzo') or 'Non specificato'))}</p>
                    <p>• <strong>Telefono:</strong> {html_escape(str(anagrafica_corrente.get('proprietario_telefono') or 'Non specificato'))}</p>
                    <p>• <strong>Città:</strong> {html_escape(str(anagrafica_corrente.get('proprietario_citta') or 'Non specificata'))}</p>
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
        if scheda_a_comparsa(f"foto_{pet_selected}", etichetta_foto):
            with st.container(border=True):
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
                        chiudi_scheda(f"foto_{pet_selected}")
                        st.session_state["foto_flash"] = f"Foto di {pet_selected} rimossa."
                        salva_dati()
                        st.rerun()

        if scheda_a_comparsa(f"chip_edit_{pet_selected}", "✏ Modifica Anagrafica Pet e Proprietario"):
            with st.container(border=True):
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
                        e_data_nascita = st.date_input("Data di Nascita", format="DD/MM/YYYY", value=data_nascita_attuale, min_value=date(2000, 1, 1), max_value=date.today())
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
                            azzera_scansione(chiave_scan_mc)
                            salva_dati(); st.success(f"Anagrafica di {new_n} aggiornata!"); st.rerun()
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "visite":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>🏥 Visite e Clinica - {html_escape(pet_selected)}</h2>", unsafe_allow_html=True)
        if st.session_state.get("visita_flash"):
            st.success(st.session_state.pop("visita_flash"))

        if scheda_a_comparsa("vaccino", "➕ Aggiungi Nuova Visita Medica"):
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    data_visita = st.date_input("Data Visita", format="DD/MM/YYYY")
                    tipo_visita = st.selectbox("Tipo Visita", ["Controllo Generale", "Vaccinazione", "Visita Specialistica", "Urgenza", "Controllo Post-Operatorio"])
                    veterinario = st.text_input("Medico Veterinario / Clinica")
                with col2:
                    diagnosi = st.text_area("Diagnosi / Note Cliniche")
                pagine_referto = scegli_pagine_referto(f"vis{st.session_state.get('vis_cnt', 0)}")

                nome_vaccino, lotto_vaccino, scadenza_vaccino = "", "", None
                etichetta_vaccino_b64 = ""
                if tipo_visita == "Vaccinazione":
                    col_v1, col_v2, col_v3 = st.columns(3)
                    with col_v1: nome_vaccino = st.text_input("Nome Vaccino*")
                    with col_v2: lotto_vaccino = st.text_input("N° Lotto Vaccino*")
                    with col_v3: scadenza_vaccino = st.date_input("Scadenza del flacone (sull'etichetta)", format="DD/MM/YYYY")

                    st.markdown("---")
                    foto_vaccino, _codice_vaccino = scansiona_etichetta(
                        "vaccino",
                        "🏷️ Scansiona l'etichetta del vaccino",
                        "Fotografa l'adesivo del vaccino: lo sfondo viene rimosso e l'etichetta verrà salvata nella scheda di questa vaccinazione.",
                        modo_guida="etichetta"
                    )
                    etichetta_vaccino_b64 = foto_vaccino or ""
                    st.markdown("---")

                n_vis = st.session_state.get("vis_cnt", 0)
                st.markdown("---")
                ric_attivo, ric_data, ric_desc = campi_richiamo(f"vis{n_vis}", tipo_visita)
                st.markdown("---")

                if st.button("Salva Visita Medica"):
                    if ric_attivo and ric_data and ric_data < data_visita:
                        st.error("La data del richiamo non può essere prima della data della visita.")
                    else:
                        referti_salvati = []
                        if pagine_referto:
                            try:
                                referti_salvati = salva_pagine_referto(pagine_referto)
                            except OSError:
                                st.error("Non siamo riusciti a salvare il referto. Riprova tra un momento; se succede ancora scrivi all'assistenza.")
                                st.stop()
                        st.session_state.pop(f"ref_cam_vis{n_vis}", None)
                        nuova_visita = {
                            "id_prestazione": uuid.uuid4().hex, "data": str(data_visita), "tipo": tipo_visita,
                            "veterinario": veterinario, "diagnosi": diagnosi,
                            "referto": None, "referti": referti_salvati, "certificata": False,
                            "num_ordine_vet": "", "provincia_vet": "", "vet_id_permanente": None,
                            "codice_certificato": None, "nome_vaccino": nome_vaccino, "lotto_vaccino": lotto_vaccino,
                            "scadenza_vaccino": str(scadenza_vaccino) if scadenza_vaccino else "",
                            "etichetta_vaccino": etichetta_vaccino_b64,
                            "richiamo": bool(ric_attivo and ric_data),
                            "prossimo_controllo_data": str(ric_data) if (ric_attivo and ric_data) else "",
                            "prossimo_controllo_tipo": ric_desc if ric_attivo else "",
                            "richiamo_da": "proprietario" if (ric_attivo and ric_data) else ""
                        }
                        st.session_state.vis_cnt = n_vis + 1
                        if pet_selected not in user_db["db_visite"]: user_db["db_visite"][pet_selected] = []
                        user_db["db_visite"][pet_selected].append(nuova_visita)
                        azzera_scansione("vaccino")
                        st.session_state.visita_flash = "Visita registrata."
                        salva_dati(); st.rerun()

        st.markdown("### 📋 Visite Registrate")
        visite_list = user_db["db_visite"].get(pet_selected, [])
        visite_ordinate = sorted(enumerate(visite_list), key=lambda x: x[1].get('data', ''), reverse=True)
        _ana_v = user_db["db_anagrafica"].get(pet_selected, {})
        if visite_ordinate:
            st.caption(f"Storico completo: {len(visite_ordinate)} visite, dalla più recente.")
            st.markdown(tabella_visite_html([v for _i, v in visite_ordinate], _ana_v), unsafe_allow_html=True)
        else:
            st.info(f"Nessuna visita registrata per {pet_selected}.")
        for idx, v in (visite_ordinate if (visite_ordinate and scheda_a_comparsa("visite_dettagli", "Dettagli e azioni delle visite (richiami, elimina)")) else []):
            _suff_ric = f" | 🔔 richiamo {_data_it(v.get('prossimo_controllo_data'))}" if richiamo_attivo(v) else ""
            with st.expander(f"🏥 {data_ui(v['data'])} - {v['tipo']}{_suff_ric}", expanded=False):
                if v.get('veterinario'): st.write(f"**Veterinario / clinica:** {v['veterinario']}")
                if v.get('nome_vaccino'):
                    st.write(f"💉 **Vaccino:** {v.get('nome_vaccino')} | **Lotto:** {v.get('lotto_vaccino', 'N/D')}")
                mostra_immagine_salvata(v.get('etichetta_vaccino'), "🏷️ Etichetta del vaccino")
                if v.get('diagnosi'): st.write(f"**Diagnosi:** {v['diagnosi']}")
                chiave_v = v.get("id_prestazione") or f"{pet_selected}_{idx}"
                mostra_referti_visita(v, chiave_v, pet_selected)
                st.markdown("**🔔 Richiamo**")
                modifica_richiamo_visita(v, chiave_v)
                if richiamo_attivo(v):
                    mostra_pulsanti_promemoria_visita(pet_selected, descrizione_richiamo(v), v.get('prossimo_controllo_data'), v.get('veterinario', ''), v.get('diagnosi', ''))
                else:
                    mostra_pulsanti_promemoria_visita(pet_selected, v['tipo'], v['data'], v.get('veterinario', ''), v.get('diagnosi', ''))
                st.markdown("---")
                pulsante_elimina_visita(visite_list, v, f"pag_{chiave_v}")
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "terapie":
    if pet_selected:
        st.markdown(f"<h2 style='color: #1E3A2B;'>💊 Terapie e Farmaci - {html_escape(pet_selected)}</h2>", unsafe_allow_html=True)
        with st.expander("🔍 Scansiona Barcode Farmaco", expanded=False):
            mostra_scansionatore_barre("📷 Lettore Codici Farmaci")

        if scheda_a_comparsa("terapia_nuova", "➕ Nuova Terapia o Prescrizione"):
            with st.container(border=True):
                n_t = st.session_state.get("ter_cnt", 0)
                col1, col2 = st.columns(2)
                with col1:
                    nome_farmaco = st.text_input("Nome del Farmaco*", key=f"ter_nome_{n_t}")
                    forma = st.selectbox("Come si somministra?", FORME_TERAPIA, key=f"ter_forma_{n_t}")
                    qta, libero = 1, ""
                    if forma == "Altro (scrivo io)":
                        libero = st.text_input("Posologia*", placeholder="es. 1 pipetta sul collo", key=f"ter_libero_{n_t}")
                    elif forma == "Millilitri (ml)":
                        qta = st.number_input("Quanti ml?", min_value=0.1, max_value=500.0, value=1.0, step=0.5, key=f"ter_qml_{n_t}")
                    elif forma == "Gocce":
                        qta = st.number_input("Quante gocce?", min_value=1, max_value=200, value=5, step=1, key=f"ter_qgo_{n_t}")
                    else:
                        qta = st.selectbox("Quanta ne serve per volta?", QUANTITA_TERAPIA, index=3,
                                           format_func=lambda x: testo_quantita(x, forma), key=f"ter_qta_{n_t}")
                    conc = ""
                    if forma != "Altro (scrivo io)":
                        conc = st.text_input("Dosaggio della confezione (facoltativo)", placeholder="es. 50 mg", key=f"ter_conc_{n_t}")
                    dosaggio = testo_posologia(forma, qta, conc, nome_farmaco, libero)
                    if dosaggio:
                        st.info(f"💬 Nella notifica leggerai: **{dosaggio}**")
                    is_multigiorno = st.checkbox("📅 Terapia somministrata per più giorni?", key=f"ter_multi_{n_t}")
                    data_inizio = st.date_input("Data Inizio Terapia", format="DD/MM/YYYY", value=date.today(), key=f"ter_inizio_{n_t}")
                    data_fine = st.date_input("Data Fine Terapia", format="DD/MM/YYYY", value=date.today() + timedelta(days=7), key=f"ter_fine_{n_t}") if is_multigiorno else data_inizio
                with col2:
                    volte = st.selectbox("Quante volte al giorno?", [1, 2, 3, 4], key=f"ter_volte_{n_t}")
                    orari_scelti = []
                    for i in range(int(volte)):
                        o = st.time_input(f"Orario {i + 1}", value=datetime.strptime(ORARI_PREDEFINITI[i], "%H:%M").time(), key=f"ter_ora_{n_t}_{i}")
                        orari_scelti.append(o.strftime("%H:%M"))
                    pasto = st.selectbox("Rispetto alla pappa", PASTO_TERAPIA, key=f"ter_pasto_{n_t}",
                                         help="Se va data prima o dopo la pappa, scrivi come orario quello in cui darai il farmaco.")
                    notifica = st.checkbox("🔔 Avvisami con una notifica 10 minuti prima", value=True, key=f"ter_notifica_{n_t}",
                                           help="Serve aver attivato le notifiche da «App e notifiche».")
                    note_somm = st.text_area("Istruzioni e Note", key=f"ter_note_{n_t}")
                    ricetta = st.file_uploader("Allega Ricetta Medica", type=["pdf", "png", "jpg"], key=f"t_ric_{n_t}")
                    rev_numero = st.text_input("Ricetta elettronica (REV): numero", key=f"ter_rev_{n_t}", placeholder="facoltativo")
                    rev_pin = st.text_input("PIN della ricetta elettronica", key=f"ter_revpin_{n_t}", placeholder="facoltativo")

                foto_farmaco = None
                if scheda_a_comparsa("farmaco", "🏷️ Aggiungi la foto dell'etichetta del farmaco (facoltativa)"):
                    with st.container(border=True):
                        foto_farmaco, _cod_f = scansiona_etichetta(
                            "farmaco", "🏷️ Etichetta del farmaco",
                            "Fotografa la scatola o l'etichetta del farmaco: lo sfondo viene tolto e la miniatura comparirà nella tabella della dashboard.",
                            modo_guida="etichetta")

                if st.button("Salva Terapia"):
                    if not nome_farmaco.strip() or not dosaggio.strip():
                        st.error("Inserisci il nome del farmaco e la quantità da dare.")
                    elif data_fine < data_inizio:
                        st.error("La data di fine non può essere prima di quella di inizio.")
                    elif len(set(orari_scelti)) < len(orari_scelti):
                        st.error("Gli orari devono essere diversi tra loro.")
                    else:
                        orari_ord = sorted(orari_scelti)
                        periodo_txt = f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}" if is_multigiorno else f"Dose Unica ({data_inizio.strftime('%d/%m/%Y')})"
                        nuova_terapia = {
                            "farmaco": nome_farmaco.strip(), "dosaggio": dosaggio.strip(), "orario": ", ".join(orari_ord), "orari": orari_ord,
                            "periodo": periodo_txt, "data_inizio": str(data_inizio), "data_fine": str(data_fine),
                            "pasto": "" if pasto == "Indifferente" else pasto, "notifica": bool(notifica),
                            "note": note_somm, "ricetta": ricetta.name if ricetta else None,
                            "rev_numero": rev_numero.strip(), "rev_pin": rev_pin.strip(),
                            "etichetta_farmaco": foto_farmaco or ""
                        }
                        if pet_selected not in user_db["db_terapie"]: user_db["db_terapie"][pet_selected] = []
                        user_db["db_terapie"][pet_selected].append(nuova_terapia)
                        st.session_state.ter_cnt = n_t + 1
                        azzera_scansione("farmaco"); chiudi_scheda("terapia_nuova")
                        salva_dati(); st.success("Terapia salvata con successo!"); st.rerun()

        mostra_dosi_oggi(user_db, pet_selected, nome_login, "pag")
        st.markdown("### 📋 Terapie Programmate")
        terapie_list = user_db["db_terapie"].get(pet_selected, [])
        terapie_ordinate = sorted(enumerate(terapie_list), key=lambda x: x[1].get('data_inizio', ''), reverse=True)
        if terapie_ordinate:
            st.caption(f"Storico completo: {len(terapie_ordinate)} terapie, dalla più recente.")
            st.markdown(tabella_terapie_html([t for _i, t in terapie_ordinate]), unsafe_allow_html=True)
            if scheda_a_comparsa("terapie_dettagli", "Dettagli e azioni delle terapie (promemoria, elimina)"):
                for idx, t in terapie_ordinate:
                    with st.expander(f"💊 {t['farmaco']} - Dose: {t['dosaggio']} ({t['periodo']})", expanded=False):
                        mostra_dettagli_terapia(pet_selected, t, idx, "pag")
        else:
            st.info(f"Nessuna terapia registrata per {pet_selected}.")
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
                data_peso = st.date_input("Data della pesata", format="DD/MM/YYYY", value=date.today(), min_value=date(2000, 1, 1),
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
                    if not ospite_solo_aggiunta() and st.button("🗑️ Elimina pesata", key=f"del_peso_{idx}"):
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
                    inizio_nuovo = st.date_input("Data di inizio", format="DD/MM/YYYY", value=oggi_c, min_value=date(2000, 1, 1),
                                                 max_value=oggi_c, key=f"cal_ini_{n_c}")
                    in_corso_nuovo = st.checkbox("Il calore è ancora in corso", value=True, key=f"cal_corso_{n_c}")
                with col_c2:
                    if in_corso_nuovo:
                        fine_nuovo = None
                    else:
                        fine_nuovo = st.date_input("Data di fine", format="DD/MM/YYYY", value=inizio_nuovo, min_value=inizio_nuovo,
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
        st.markdown(f"<h2 style='color: #1E3A2B;'>📄 Fatture e Spese - {html_escape(pet_selected)}</h2>", unsafe_allow_html=True)
        if st.session_state.get("fattura_flash"):
            st.success(st.session_state.pop("fattura_flash"))
        if scheda_a_comparsa("fattura_nuova", "➕ Carica Nuova Fattura"):
            with st.container(border=True):
                n_fat = st.session_state.get("fat_cnt", 0)
                col1, col2 = st.columns(2)
                with col1:
                    data_spesa = st.date_input("Data Documento", format="DD/MM/YYYY")
                    categoria_spesa = st.selectbox("Categoria", ["Visita Veterinaria", "Farmaci", "Esami", "Chirurgia", "Cibo / Integratori"])
                    importo = st.number_input("Importo (€)", min_value=0.0, step=0.5, format="%.2f")
                with col2:
                    fornitore = st.text_input("Clinica / Farmacia")
                pagine_fattura = scegli_pagine_referto(
                    f"fat{n_fat}", "🧾 Ricevuta o fattura (facoltativo)",
                    "Se il documento ha più fogli, aggiungi tutte le pagine: restano nell'ordine in cui le scegli. "
                    "Di ogni foto puoi tenere solo il foglio, senza il tavolo intorno.")

                if st.button("Salva Fattura"):
                    documenti_salvati = []
                    if pagine_fattura:
                        try:
                            documenti_salvati = salva_pagine_referto(pagine_fattura)
                        except OSError:
                            st.error("Non siamo riusciti a salvare il documento. Riprova tra un momento; se succede ancora scrivi all'assistenza.")
                            st.stop()
                    st.session_state.pop(f"ref_cam_fat{n_fat}", None)
                    st.session_state.fat_cnt = n_fat + 1
                    nuova_fattura = {"id": uuid.uuid4().hex, "data": str(data_spesa), "categoria": categoria_spesa, "importo": importo,
                                     "fornitore": fornitore, "documento": None, "documenti": documenti_salvati}
                    if pet_selected not in user_db["db_fatture"]: user_db["db_fatture"][pet_selected] = []
                    user_db["db_fatture"][pet_selected].append(nuova_fattura)
                    st.session_state["fattura_flash"] = "Fattura salvata!"
                    salva_dati(); st.rerun()

        st.markdown("### 📋 Fatture Registrate")
        _lista_fatt = user_db["db_fatture"].get(pet_selected, [])
        if not _lista_fatt:
            st.info(f"Nessuna fattura registrata per {pet_selected}.")
        for idx, f in enumerate(_lista_fatt):
            _kf = f.get("id") or f"{pet_selected}_{idx}"
            with st.expander(f"📄 €{f['importo']:.2f} - {f['categoria']} ({data_ui(f['data'])})", expanded=False):
                st.write(f"**Fornitore:** {f['fornitore']}")
                mostra_allegati(f, f"fat_{_kf}", pet_selected, "documenti", "documento", "Documento allegato", "Fattura", "documento")
                if ospite_solo_aggiunta():
                    pass
                elif not st.session_state.get(f"conf_del_fat_{_kf}"):
                    if st.button("🗑️ Elimina questa fattura", key=f"del_fat_{_kf}"):
                        st.session_state[f"conf_del_fat_{_kf}"] = True; st.rerun()
                else:
                    st.warning("Vuoi eliminare questa fattura e i suoi allegati? L'operazione non si può annullare.")
                    d1, d2 = st.columns(2)
                    with d1:
                        if st.button("Sì, elimina", key=f"del_fat_si_{_kf}", type="primary"):
                            st.session_state.pop(f"conf_del_fat_{_kf}", None)
                            elimina_file_referti(f)
                            _lista_fatt[:] = [x for x in _lista_fatt if x is not f]
                            st.session_state["fattura_flash"] = "Fattura eliminata."
                            salva_dati(); st.rerun()
                    with d2:
                        if st.button("No, tienila", key=f"del_fat_no_{_kf}"):
                            st.session_state.pop(f"conf_del_fat_{_kf}", None); st.rerun()
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "account":
    st.markdown("<h2 style='color: #1E3A2B;'>👤 Il mio account</h2>", unsafe_allow_html=True)
    st.caption("I tuoi dati, la password, la verifica a due fattori e l'eliminazione dell'account.")
    mostra_pagina_account(login_email, st.session_state.db_users[login_email])

elif st.session_state.sezione_attiva == "clinica":
    st.markdown("<h2 style='color: #1E3A2B;'>🏥 La mia clinica di fiducia</h2>", unsafe_allow_html=True)
    st.caption("Scrivi qui i dati della clinica o dello studio veterinario di cui ti fidi: li ritrovi sempre a portata di mano e, con un tocco sul numero, parte la telefonata.")
    _cl = clinica_fiducia(user_db)
    if _cl:
        _via = str(_cl.get("via", "")).strip()
        _maps = ("https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote_plus((str(_cl.get("nome", "")) + " " + _via).strip())) if _via else ""
        st.markdown(
            '<div class="wellness-card"><span class="card-badge badge-blue">CLINICA DI FIDUCIA</span>'
            f'<h3 style="margin:6px 0 4px 0">{html_escape(str(_cl.get("nome", "")) or "Clinica")}</h3>'
            + (f'<p style="margin:2px 0">📍 {html_escape(_via)}</p>' if _via else "")
            + f'<div style="margin-top:10px">{html_pulsante_chiama(_cl.get("telefono"))}'
            + (f'<a href="{html_escape(_maps, quote=True)}" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;background:#E2F1FB;color:#0B4A6F !important;'
               'padding:14px 22px;min-height:48px;border-radius:99px;text-decoration:none !important;font-weight:700;margin:6px 0;box-sizing:border-box">🗺️ Apri su Maps</a>' if _maps else "")
            + '</div></div>', unsafe_allow_html=True)
        if not telefono_per_chiamata(_cl.get("telefono")):
            st.warning("Il numero di telefono salvato non sembra valido: modificalo qui sotto per poter chiamare con un tocco.")
    with st.expander("✏️ Modifica i dati della clinica" if _cl else "➕ Inserisci la tua clinica di fiducia", expanded=not _cl):
        with st.form("form_clinica"):
            _n = st.text_input("Nome della clinica o dello studio*", value=str(_cl.get("nome", "")), max_chars=120)
            _v = st.text_input("Via e città", value=str(_cl.get("via", "")), max_chars=200, placeholder="es. Via Roma 12, Verona")
            _t = st.text_input("Numero di telefono*", value=str(_cl.get("telefono", "")), max_chars=30, placeholder="es. 045 1234567 oppure +39 345 1234567")
            _salva = st.form_submit_button("Salva la clinica")
        if _salva:
            if not _n.strip():
                st.error("Scrivi il nome della clinica.")
            elif not telefono_per_chiamata(_t):
                st.error("Scrivi un numero di telefono valido (da 6 a 15 cifre, con o senza prefisso).")
            else:
                user_db["clinica_fiducia"] = {"nome": _n.strip(), "via": _v.strip(), "telefono": _t.strip()}
                salva_dati(); st.success("Clinica salvata."); st.rerun()
    if _cl:
        if st.session_state.get("conf_del_clinica"):
            st.warning("Vuoi togliere la clinica di fiducia?")
            _c1, _c2 = st.columns(2)
            with _c1:
                if st.button("Sì, togli", key="del_clinica_si", type="primary"):
                    user_db.pop("clinica_fiducia", None); st.session_state.pop("conf_del_clinica", None)
                    salva_dati(); st.rerun()
            with _c2:
                if st.button("No, tienila", key="del_clinica_no"):
                    st.session_state.pop("conf_del_clinica", None); st.rerun()
        elif st.button("🗑️ Togli la clinica", key="del_clinica"):
            st.session_state["conf_del_clinica"] = True; st.rerun()

elif st.session_state.sezione_attiva == "urgenze":
    st.markdown("<h2 style='color: #1E3A2B;'>🚨 Urgenze & Cliniche Veterinarie 24H</h2>", unsafe_allow_html=True)
    citta_ricerca = st.text_input("📍 Inserisci la Città o Località di Vacanza:", placeholder="es. Rimini, Olbia, Roma...")
    q = urllib.parse.quote_plus(f"pronto soccorso veterinario 24 ore a {citta_ricerca.strip()}" if citta_ricerca else "pronto soccorso veterinario 24 ore vicino a me")
    st.link_button(f"🗺️ Apri Mappa Cliniche 24H per '{citta_ricerca or 'posizione attuale'}' su Google Maps", f"https://www.google.com/maps/search/?api=1&query={q}")

elif st.session_state.sezione_attiva == "smarrito":
    st.markdown("<h2 style='color: #1E3A2B;'>🐾 Animale smarrito</h2>", unsafe_allow_html=True)
    if login_email == "demo@pethealth.it":
        st.info("Queste funzioni non sono disponibili nell'account di prova: registrati per usarle.")
    else:
        mostra_sezione_smarrito(login_email, user_email, user_db, pet_selected, nome_login)

elif st.session_state.sezione_attiva == "angeli":
    st.markdown("<h2 style='color: #1E3A2B;'>🌈 I Nostri Angeli a 4 Zampe</h2>", unsafe_allow_html=True)
    mostra_messaggio_angelo()
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

    if pet_selected:
        st.markdown("---")
        with st.expander(f"🌈 Registra il decesso di {pet_selected}", expanded=False):
            st.caption("L'animale viene spostato nel Registro degli Angeli, con tutta la sua cartella clinica. Potrai ripristinarlo in qualsiasi momento.")
            date_decesso = st.date_input("Data del decesso", format="DD/MM/YYYY", key="data_decesso")
            certificato = st.file_uploader("Allega il certificato di morte (facoltativo)", type=["pdf", "png", "jpg"], key="cert_morte")
            conferma_dec = st.checkbox(f"Confermo il decesso di {pet_selected}", key="conf_decesso")
            if st.button("Conferma e archivia nel Registro degli Angeli", key="btn_decesso"):
                if not conferma_dec:
                    st.error("Spunta la casella per confermare.")
                else:
                    user_db["angeli_archiviati"][pet_selected] = {
                        "data_decesso": str(date_decesso),
                        "certificato": certificato.name if certificato else "Non allegato",
                        "registrato_da": "proprietario",
                        "visite": user_db["db_visite"].pop(pet_selected, []),
                        "terapie": user_db["db_terapie"].pop(pet_selected, []),
                        "fatture": user_db["db_fatture"].pop(pet_selected, []),
                        "peso": user_db["db_peso"].pop(pet_selected, []),
                        "calori": user_db["db_calori"].pop(pet_selected, []),
                        "anagrafica": user_db["db_anagrafica"].pop(pet_selected, {})
                    }
                    user_db["lista_animali"].remove(pet_selected)
                    user_db["pet_selezionato"] = user_db["lista_animali"][0] if user_db["lista_animali"] else None
                    salva_dati(); registra_messaggio_angelo(pet_selected, nome_login)

elif _vista_impost == "installa":
    st.markdown("<h2 style='color: #1E3A2B;'>📲 App e notifiche</h2>", unsafe_allow_html=True)
    try:
        _url_app = str(st.secrets.get("app_url", "") or "").strip()
    except Exception:
        _url_app = ""
    _url_app = _url_app or "https://pethealthvet.it"
    st.write("PetHealth si installa sul telefono come una vera app: ha la sua icona, si apre a schermo intero e **si aggiorna da sola**, "
             "senza passare dall'App Store o da Google Play. La versione per computer resta sempre disponibile.")
    c_qr, c_txt = st.columns([1, 2])
    with c_qr:
        _png_qr = qr_png(_url_app)
        if _png_qr:
            st.image(_png_qr, width=170)
        st.caption("Inquadra il codice con la fotocamera del telefono.")
    with c_txt:
        st.markdown(f"**Indirizzo:** `{_url_app}`")
        st.caption("Aprilo dal telefono, poi segui i passi qui sotto. Se vedi comparire in basso il riquadro «Installa PetHealth», basta toccare Installa.")
    t_ios, t_and, t_pc = st.tabs(["🍎 iPhone / iPad", "🤖 Android", "💻 Computer"])
    with t_ios:
        st.markdown("1. Apri l'indirizzo con **Safari** (va bene anche Chrome).\n"
                    "2. Tocca **Condividi**, il quadrato con la freccia verso l'alto.\n"
                    "3. Scorri e tocca **Aggiungi alla schermata Home**.\n"
                    "4. Tocca **Aggiungi**. L'icona PetHealth compare tra le tue app.")
    with t_and:
        st.markdown("1. Apri l'indirizzo con **Chrome**.\n"
                    "2. Tocca **Installa** nel riquadro in basso, oppure i tre puntini ⋮ in alto a destra.\n"
                    "3. Scegli **Installa app** (o **Aggiungi a schermata Home**) e conferma.\n"
                    "4. L'icona PetHealth compare tra le tue app.")
    with t_pc:
        st.markdown("- **Chrome o Edge:** nella barra degli indirizzi clicca l'icona di installazione (un monitor con una freccia), poi **Installa**.\n"
                    "- **Safari su Mac:** menu **File → Aggiungi al Dock**.\n"
                    "- Oppure usa semplicemente il sito dal browser: è identico.")
    st.info("Ogni nuova versione di PetHealth è già disponibile nell'app installata: non devi riscaricare nulla.")
    st.markdown("---")
    st.markdown("#### 🔔 Notifiche dei richiami")
    st.caption("**Richiami e controlli:** se li segni, l'app ti manda una notifica 2 giorni prima della data (dalle 9 del mattino). "
               "**Terapie:** per ogni farmaco con la notifica attiva, l'app ti avvisa 10 minuti prima di ogni somministrazione, con la dose da dare. "
               "Non arriva nessun messaggio WhatsApp o email, e senza la casella spuntata non parte nessun avviso.")
    if notifiche_account_attive(login_email):
        st.caption("Le notifiche sono già attive sul tuo account: sugli altri tuoi dispositivi basta aprire PetHealth e toccare «Attiva su questo dispositivo» "
                   "(se il telefono o il computer le aveva già autorizzate, si attivano da sole). Il browser chiede sempre un tocco la prima volta.")
    components.html(blocco_notifiche(login_email), height=250)
    st.markdown("---")
    st.markdown("#### 📴 Libretto senza internet")
    st.caption("Salva sul dispositivo una copia di **sola lettura** del libretto (anagrafica, visite e vaccini, terapie, peso, richiami; senza fatture né foto). "
               "Se manca la connessione, l'app installata la mostra al posto del messaggio di errore. Si aggiorna da sola ogni volta che apri l'app con internet "
               "e viene cancellata quando esci dall'account. La attivi una volta sola: da quel momento si attiva da sola su ogni dispositivo dove accedi "
               "(telefoni e computer), basta aprire PetHealth con la connessione attiva. Se la disattivi, si spegne su tutti.")
    _off_prima = offline_attivo()
    _off_nuovo = st.toggle("Tieni una copia del libretto su questo dispositivo", value=_off_prima, key="tg_offline")
    if _off_nuovo != _off_prima:
        st.session_state["off_stato"] = _off_nuovo
        st.session_state.pop("off_ultimo_hash", None)
        if login_email != "demo@pethealth.it":
            st.session_state.db_users[login_email].setdefault("preferenze", {})["offline"] = bool(_off_nuovo)
            salva_dati()
        components.html(js_offline_cookie(_off_nuovo) + ("" if _off_nuovo else JS_OFFLINE_PULISCI), height=0, width=0)
        if _off_nuovo:
            sincronizza_offline(user_db)
    if offline_attivo():
        st.success("Attivo su questo dispositivo e su tutti quelli dove accedi con il tuo account. Per vederlo senza internet apri PetHealth come sempre: se non c'è connessione compare la copia. "
                   "Su iPhone aggiungi prima l'app alla schermata Home.")
    st.markdown("---")
    st.markdown("#### 🔐 Accesso su questo dispositivo")
    n_disp = len((st.session_state.db_users[login_email].get("sessioni_dispositivo") or {}))
    st.caption(f"Con «Resta connesso» attivo l'app non ti chiede la password ogni volta. Dispositivi collegati al tuo account: **{n_disp}**.")
    if st.button("Esci da tutti i dispositivi", key="esci_tutti"):
        revoca_sessione_dispositivo(login_email, tutte=True)
        st.session_state.account_attivo = None
        st.session_state.logged_user_email = None
        st.session_state.ph_no_autologin = True
        st.session_state.ph_cookie_cancella = True
        st.rerun()

elif _vista_impost == "privacy":
    mostra_sezione_account(login_email, st.session_state.db_users[login_email])

elif _vista_impost == "condividi":
    mostra_sezione_condividi(login_email, user_email, user_db, pet_selected)

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
                st.markdown("---")
                st.markdown("#### 📤 Condividi il PDF")
                st.caption("Scegli con chi e come condividerlo.")
                modo_cond = st.radio("Come vuoi condividerlo?", ["✉️ Email", "🔳 QR code", "💬 WhatsApp"], horizontal=True, key="pdf_modo_cond")
                if modo_cond.startswith("✉️"):
                    if not email_configurata():
                        st.info("L'invio per email non è attivo su questo servizio: scegli QR code o WhatsApp, oppure scarica il PDF e allegalo tu.")
                    else:
                        dest_pdf = st.text_input("Email del destinatario", key="pdf_email_dest", placeholder="es. veterinario@studio.it")
                        if st.button("✉️ Invia il PDF per email", key="pdf_email_invia"):
                            d_ok = str(dest_pdf).strip().lower()
                            if "@" not in d_ok or "." not in d_ok.split("@")[-1] or " " in d_ok:
                                st.error("Scrivi un indirizzo email valido.")
                            elif len(pdf_pronto["bytes"]) > 3_500_000:
                                st.error("Il PDF è troppo grande per l'email: scegli QR code o WhatsApp, oppure rigenera il PDF senza fatture.")
                            else:
                                attesa_pdf = secondi_blocco("pdf-email", login_email)
                                if attesa_pdf:
                                    st.error(testo_attesa(attesa_pdf))
                                else:
                                    registra_fallimento("pdf-email", login_email)
                                    inviata_pdf = invia_email(
                                        d_ok, f"Libretto sanitario di {pet_selected}",
                                        f"Buongiorno,\n\n{nome_login} ti invia in allegato il libretto sanitario di {pet_selected}, creato con PetHealth.\n"
                                        f"Se rispondi a questa email, la risposta arriva a {login_email}.\n\nPetHealth - Wellness & Care",
                                        allegato=pdf_pronto["bytes"], nome_allegato=f"Libretto_{nome_pulito}_{date.today().isoformat()}.pdf", rispondi_a=login_email)
                                    if inviata_pdf:
                                        st.success(f"PDF inviato a {d_ok}.")
                                    else:
                                        st.error("Non siamo riusciti a inviare l'email. Riprova più tardi, oppure usa il QR code o WhatsApp.")
                else:
                    st.caption("Chi riceve il link vede il libretto in sola lettura e può scaricarne il PDF (senza fatture né numero di telefono), senza creare un account. "
                               "Puoi revocarlo quando vuoi da «Impostazioni → Condivisione e QR».")
                    durata_pdf = st.selectbox("Il link vale per", list(OPZIONI_LINK), index=1, key="pdf_durata_link")
                    if st.button("🔗 Crea il link", key="pdf_crea_link"):
                        _tk = crea_link_veterinario(user_email, user_db, pet_selected, OPZIONI_LINK[durata_pdf])
                        st.session_state["pdf_link"] = {"pet": pet_selected, "url": url_pubblico("libretto", _tk), "k": _hash_lid(_tk.rsplit(".", 1)[-1])}
                    lk = st.session_state.get("pdf_link")
                    if lk and lk.get("k") not in (user_db.get("link_veterinario") or {}):
                        st.session_state.pop("pdf_link", None); lk = None
                    if lk and lk.get("pet") == pet_selected:
                        st.success("Link creato.")
                        if modo_cond.startswith("🔳"):
                            png_pdf = qr_png(lk["url"])
                            if png_pdf:
                                st.image(png_pdf, width=220, caption="Fai inquadrare questo QR con la fotocamera")
                                st.download_button("⬇️ Scarica il QR", data=png_pdf, file_name=f"qr-libretto-{nome_pulito}.png", mime="image/png", key="pdf_qr_dl")
                            st.code(lk["url"], language=None)
                        else:
                            st.link_button("💬 Invia su WhatsApp", "https://wa.me/?text=" + urllib.parse.quote(f"Libretto sanitario di {pet_selected}: {lk['url']}"), use_container_width=True)
                            st.code(lk["url"], language=None)
                        if st.button("🚫 Annulla questo link", key="pdf_revoca_link"):
                            user_db["link_veterinario"].pop(lk["k"], None)
                            st.session_state.pop("pdf_link", None)
                            salva_dati(); st.rerun()
    else:
        mostra_avviso_nessun_animale()

elif st.session_state.sezione_attiva == "nuovo_animale":
    st.markdown("<h2 style='color: #1E3A2B;'>🐾 Registra Nuovo Animale</h2>", unsafe_allow_html=True)
    st.caption("Compila la scheda anagrafica sottostante per creare il nuovo libretto sanitario digitale.")
    
    # un microchip letto dallo scanner (più in basso nella pagina) viene inserito al giro successivo
    if st.session_state.get("n_microchip_in_arrivo"):
        st.session_state["n_microchip"] = st.session_state.pop("n_microchip_in_arrivo")

    with st.container():
        st.markdown("### 🐾 1. Dati Anagrafici dell'Animale")
        c1, c2 = st.columns(2)
        with c1:
            n_nome = st.text_input("Nome dell'Animale*", placeholder="es. Luna, Max, Baffo...")
            n_specie = st.selectbox("Specie / Tipo Animale*", ["Cane", "Gatto", "Coniglio", "Uccello", "Rettile", "Altro"])
            n_sesso = st.selectbox("Sesso*", SESSI)
            n_razza = st.text_input("Razza dell'Animale", placeholder="es. Meticcio, Labradoodle, Europeo...")
        with c2:
            n_data = st.date_input("Data di Nascita Presunta / Effettiva", format="DD/MM/YYYY", value=date.today(), min_value=date(2000, 1, 1), max_value=date.today())
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
            _opz_p = opzioni_province()
            _att_p = etichetta_provincia(st.session_state.db_users[login_email].get("provincia", ""))
            n_prop_prov = st.selectbox("Provincia", _opz_p, index=_opz_p.index(_att_p) if _att_p in _opz_p else 0, key=f"n_prop_prov_{login_email}",
                                       help="Serve per l'allerta «animale smarrito» nella tua zona. Puoi cambiarla quando vuoi.")

        st.markdown("---")
        foto_chip_n, codice_chip_n = None, ""
        if scheda_a_comparsa("chip_nuovo", "📷 Scansiona il Codice a Barre del Microchip"):
            with st.container(border=True):
                foto_chip_n, codice_chip_n = scansiona_etichetta(
                    "chip_nuovo",
                    "📷 Scansiona l'adesivo del microchip",
                    "Fotografa l'adesivo del libretto cartaceo: lo sfondo viene rimosso e l'immagine verrà salvata nella scheda anagrafica.",
                    modo_guida="barcode"
                )
        if codice_microchip_valido(codice_chip_n) and st.session_state.get("ultimo_codice_chip_nuovo") != codice_chip_n:
            st.session_state["n_microchip_in_arrivo"] = codice_chip_n
            st.session_state["ultimo_codice_chip_nuovo"] = codice_chip_n
            st.rerun()

        foto_nuova_b64 = None
        if scheda_a_comparsa("foto_nuovo", "📸 Foto dell'animale (facoltativa)"):
            with st.container(border=True):
                foto_nuova_b64 = scegli_foto_animale("foto_nuovo")

        st.write("")
        if st.button("💾 Salva e Crea Libretto Sanitario", key="btn_salva_nuovo_animale", type="primary"):
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
                if sigla_da_etichetta(n_prop_prov):
                    st.session_state.db_users[login_email]["provincia"] = sigla_da_etichetta(n_prop_prov)
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

_JS_TASTO_INDIETRO = r"""
(function () {
  var SEZ = "__SEZIONE__";
  window.__phSez = SEZ;
  if (window.__phIndietro) return;
  window.__phIndietro = true;
  var H = window.history, D = window.document;
  function armato() { try { return !!(H.state && H.state.ph === "app"); } catch (e) { return false; } }
  function arma() {
    try {
      if (armato()) return;
      if (!(H.state && H.state.ph === "base")) H.replaceState({ ph: "base" }, "");
      H.pushState({ ph: "app" }, "");
    } catch (e) {}
  }
  // la voce in più nella cronologia si crea al primo tocco: così anche Chrome per Android la considera valida
  var tipi = ["pointerup", "touchend", "click", "keydown"];
  function una_volta() { tipi.forEach(function (t) { D.removeEventListener(t, una_volta, true); }); arma(); }
  tipi.forEach(function (t) { D.addEventListener(t, una_volta, true); });
  window.addEventListener("popstate", function (ev) {
    var s = ev.state;
    if (!s || s.ph !== "base") return;
    if (window.__phSez && window.__phSez !== "dashboard") {
      var b = D.querySelector(".st-key-torna_home_back button");
      if (b) {
        b.click();
        try { H.pushState({ ph: "app" }, ""); } catch (e) {}
        return;
      }
    }
    try { H.back(); } catch (e) {}      // già nella schermata iniziale: il tasto indietro esce come sempre
  });
})();
"""

def blocco_tasto_indietro(sezione):
    """Script senza spazio che gira nel contesto della pagina: il tasto indietro riporta alla schermata iniziale."""
    logica = _JS_TASTO_INDIETRO.replace("__SEZIONE__", re.sub(r"[^a-z_]", "", str(sezione)))
    return ("<script>(function(){var P;try{void window.parent.document;P=window.parent;}catch(e){P=window;}"
            "try{(new P.Function(" + json.dumps(logica) + "))();}catch(e){}})();</script>")

components.html(blocco_tasto_indietro(st.session_state.get("sezione_attiva", "dashboard")), height=0, width=0)
