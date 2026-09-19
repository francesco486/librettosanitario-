# CSS Custom con Sidebar SEMPRE APERTA su Desktop e adattabile su Mobile
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Font Globale e Sfondo Pagina */
    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F8F7F2 !important;
        color: #1e293b !important;
    }

    /* Reset altezze linea */
    p, span, label, h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        line-height: 1.45 !important;
    }

    /* Nascondi solo MainMenu e Footer */
    #MainMenu, footer {
        visibility: hidden;
    }

    /* Header trasparente */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Sidebar Scuro Verde Foresta */
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

    /* ----------------------------------------------------------------- */
    /* DESKTOP: BLOCCO SIDEBAR PERMANENTE (NASCONDE PULSANTE DI CHIUSURA) */
    /* ----------------------------------------------------------------- */
    @media (min-width: 768px) {
        /* Nasconde sia il tasto di chiusura che di riapertura */
        [data-testid="stSidebarCollapseButton"], 
        [data-testid="stSidebarToggle"], 
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Forza la sidebar ad essere sempre visibile */
        section[data-testid="stSidebar"] {
            display: block !important;
            min-width: 21rem !important;
            max-width: 21rem !important;
        }
    }

    /* HERO BANNER */
    .hero-card {
        background: linear-gradient(135deg, #1E3A2B 0%, #2D4A3E 100%);
        padding: 26px 24px;
        border-radius: 18px;
        color: #FFFFFF !important;
        box-shadow: 0 8px 20px rgba(30, 58, 43, 0.12);
        margin-bottom: 22px;
        border: 1px solid #2D4A3E;
    }

    .hero-title {
        color: #FFFFFF !important;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        margin: 0 0 8px 0 !important;
    }

    .hero-subtitle {
        color: #D2E3D8 !important;
        font-size: 0.98rem !important;
        margin: 0 !important;
        font-weight: 400 !important;
    }

    /* WELLNESS CARD */
    .wellness-card {
        background-color: #FFFFFF !important;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #E2E8E4 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
        margin-bottom: 16px;
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
    .badge-rose { background-color: #fce7f3; color: #9d174d; }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }

    /* BANNER SPAZIO ANGELI */
    .angeli-text {
        font-size: 1.05rem;
        font-style: italic;
        color: #831843 !important;
        text-align: center;
        margin-bottom: 1.8rem;
        padding: 18px;
        background-color: #fce7f3 !important;
        border-radius: 16px;
        border-left: 6px solid #db2777;
    }

    /* INPUT E FORM */
    label, div[data-testid="stWidgetLabel"] p {
        color: #1E3A2B !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        margin-bottom: 6px !important;
    }

    .stTextInput input, 
    .stTextArea textarea, 
    .stSelectbox > div > div, 
    .stNumberInput input,
    .stDateInput input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        padding: 10px 14px !important;
    }

    /* TAB (ACCEDI / REGISTRATI) */
    div[data-testid="stTabs"] {
        background-color: transparent !important;
    }

    div[data-baseweb="tab-list"] {
        gap: 12px !important;
        background-color: transparent !important;
        border-bottom: none !important;
        justify-content: center !important;
    }

    [data-baseweb="tab"],
    button[data-baseweb="tab"],
    button[role="tab"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        padding: 8px 20px !important;
        border: 2px solid #D32F2F !important;
        height: auto !important;
        cursor: pointer !important;
    }

    [data-baseweb="tab"] *,
    button[data-baseweb="tab"] *,
    button[role="tab"] *,
    [data-baseweb="tab"] p, 
    [data-baseweb="tab"] span,
    [data-baseweb="tab"] div,
    [aria-selected="true"] p, 
    [aria-selected="false"] p,
    [aria-selected="true"] span,
    [aria-selected="false"] span {
        color: #D32F2F !important;
        -webkit-text-fill-color: #D32F2F !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
    }

    [data-baseweb="tab"][aria-selected="true"],
    button[role="tab"][aria-selected="true"] {
        background-color: #FFEBEE !important;
        border: 2px solid #B71C1C !important;
    }

    /* PULSANTI FORM E SIDEBAR */
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

    div[data-testid="stFormSubmitButton"] > button:hover p,
    div[data-testid="stFormSubmitButton"] > button:hover span,
    .stButton > button:hover p,
    .stButton > button:hover span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
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

    /* EXPANDER */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 14px !important;
        margin-bottom: 12px !important;
    }

    div[data-testid="stExpander"] summary p {
        color: #1E3A2B !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)
