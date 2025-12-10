import streamlit as st
import time
import random
import pandas as pd
from utils.demo import get_demo_data
from utils.ttn import get_lorawan_data
from streamlit_autorefresh import st_autorefresh

# ======= CONFIGURACIÓN DEL DASHBOARD ========
st.set_page_config(page_title="Monitoreo Pulsera Bombero",
                   layout="wide",
                   page_icon="🔥")

# ======= SIDEBAR ==========
st.sidebar.title("⚙️ Configuración")
modo = st.sidebar.radio(
    "Selecciona el modo:",
    ("Real (TTN/LoRaWAN)", "Demo")
)

refresh_rate = st.sidebar.slider("Refrescar cada (segundos)", 1, 10, 3)

st_autorefresh(interval=refresh_rate * 1000, key="data_refresh")

# === OBTENER DATOS ===

if modo == "Demo":
    data = get_demo_data()

else:  # MODO REAL (LoRaWAN)
    data = get_lorawan_data()

    # Si no hay datos reales → NO continuar
    if data is None:
        st.warning("⚠ No hay datos desde LoRaWAN. Esperando conexión...")
        st.stop()   # ← DETIENE el dashboard antes de usar data

# ======= INTERFAZ PRINCIPAL ==========
st.title("🚒 Panel de Monitoreo – Pulsera de Seguridad para Bomberos")

col1, col2, col3 = st.columns(3)

# Datos principales
col1.metric("Temperatura ambiente", f"{data['temperature']} °C")
col2.metric("Calidad de aire (Humo)", f"{data['smoke']}")
col3.metric("Ritmo cardíaco", f"{data['heart_rate']} bpm")

# Mapa con ubicación
st.subheader("📍 Ubicación actual del bombero")
df_map = pd.DataFrame({
    'lat': [data['lat']],
    'lon': [data['lon']]
})
st.map(df_map, zoom=15)

# Alertas
st.subheader("⚠️ Alertas")

if data['temperature'] > 50:
    st.error("🔥 Temperatura extremadamente alta")
elif data['smoke'] > 80:
    st.error("🌫️ Fuerte presencia de humo")
elif data['movement'] < 2:
    st.warning("🟡 Posible inmovilidad")
else:
    st.success("🟢 Estado normal")

# Gráfica ejemplo
st.subheader("📊 Ritmo cardíaco reciente (demo)")
hr = [random.randint(70, 140) for _ in range(30)]
st.line_chart(hr)