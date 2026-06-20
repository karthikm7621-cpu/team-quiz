import i18n
import yaml
import streamlit as st
from pathlib import Path

SUPPORTED_LANGUAGES = {
    "en": "English",
    "te": "తెలుగు",
    "hi": "हिन्दी",
    "kn": "ಕನ್ನಡ",
    "ta": "தமிழ்",
}
DEFAULT_LANGUAGE = "en"

def load_translations():
    """Loads all translation files from the i18n directory."""
    i18n_dir = Path(__file__).parent
    i18n.load_path.clear() # Clear default paths
    i18n.load_path.append(str(i18n_dir))
    i18n.set("file_format", "yml")
    i18n.set("filename_format", "{locale}.{format}")

def set_language(lang_code: str = None):
    """Sets the application language based on selection or session state."""
    if lang_code and lang_code in SUPPORTED_LANGUAGES:
        st.session_state.language = lang_code
    
    # Use session state language if available, otherwise default
    current_lang = st.session_state.get("language", DEFAULT_LANGUAGE)
    i18n.set("locale", current_lang)

def t(key: str, **kwargs) -> str:
    """Gets the translation for a given key."""
    translated = i18n.t(key)
    try:
        if kwargs:
            return translated.format(**kwargs)
        return translated
    except (KeyError, ValueError, AttributeError):
        return translated

# --- Initial Setup ---
load_translations()
i18n.set("fallback", DEFAULT_LANGUAGE)

# Set initial language on first run
if "language" not in st.session_state:
    st.session_state.language = DEFAULT_LANGUAGE
set_language()