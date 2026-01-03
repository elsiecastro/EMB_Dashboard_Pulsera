import streamlit as st
from utils.auth import authenticate

# -------------------------------  
# Configuración de la página
# -------------------------------
st.set_page_config(
    page_title="PULSERA GUARDIÁN",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚒"
)

# -------------------------------  
# Estilos CSS
# -------------------------------
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# -------------------------------  
# Fondo animado
# -------------------------------
st.markdown(
    '<div class="background-animation"></div>',
    unsafe_allow_html=True
)

# -------------------------------  
# Sesión
# -------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "data_source" not in st.session_state:
    st.session_state.data_source = "DEMO"

# -------------------------------  
# LOGIN CENTRADO HORIZONTAL
# -------------------------------
if not st.session_state.authenticated:
    # Tres columnas para centrar horizontalmente
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🚒 Centro de Control de Misiones")
        st.subheader("🔑 Iniciar sesión")
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        if st.button("Ingresar"):
            if authenticate(user, password):
                st.session_state.authenticated = True
                st.session_state.user = user
                st.success("✅ Acceso autorizado")
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")

# -------------------------------  
# PANEL PRINCIPAL
# -------------------------------
else:
    st.success(f"Bienvenido, {st.session_state.user}")

    # -------------------------------  
    # Sidebar de navegación
    # -------------------------------
    st.sidebar.title("🛰 Panel de navegación")
    st.sidebar.info("Usa esto para cambiar entre misiones, bomberos y alertas")

    # -------------------------------  
    # Fuente de datos
    # -------------------------------
    st.subheader("📡 Fuente de datos")
    fuente = st.radio(
        "Seleccione la fuente de información:",
        ["DEMO", "LoRaWAN"],
        index=0 if st.session_state.data_source == "DEMO" else 1,
        key="data_source_radio"
    )

    st.session_state.data_source = fuente

    if fuente == "DEMO":
        st.info("🧪 Modo DEMO: datos simulados en tiempo real")
    else:
        st.warning("📡 Modo LoRaWAN: datos reales desde sensores")

    st.divider()
    st.info("Usa el menú lateral para navegar entre misiones, bomberos y alertas.")