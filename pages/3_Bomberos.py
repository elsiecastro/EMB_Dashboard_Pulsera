import streamlit as st
import pandas as pd
import json
import random
import time
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh


with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ------------------ Seguridad ------------------
if not st.session_state.get("authenticated", False):
    st.stop()

st.set_page_config(page_title="Bombero", layout="wide")

# ------------------ Fuente de datos ------------------
source = st.session_state.get("data_source", "DEMO")

# ------------------ Auto refresh ------------------
refresh_rate = st.sidebar.slider("Frecuencia de actualización (s)", 1, 5, 2)
st_autorefresh(interval=refresh_rate * 1000, key="bombero_refresh")

# ------------------ Helpers ------------------
def jitter(val, delta):
    return round(val + random.uniform(-delta, delta), 3)

# ------------------ Cargar bomberos ------------------
with open("data/bomberos.json", "r", encoding="utf-8") as f:
    bomberos_raw = json.load(f)["bomberos"]

bomberos = {b["id"]: b for b in bomberos_raw}

bombero_id = st.session_state.get("bombero_id")

if not bombero_id or bombero_id not in bomberos:
    st.error("🚫 Bombero no válido o no seleccionado")
    st.stop()

b = bomberos[bombero_id]

# ------------------ Header ------------------
st.title("🚒 MONITOREO DE BOMBERO")
st.subheader(b["nombre"])
st.caption(
    f"ID: {bombero_id} | Rango: {b['rango']} | "
    f"Equipo: {b['equipo']} | Estado: {b['estado']} | "
    f"Fuente: {source}"
)
st.markdown("---")

# ====================================================
# 📡 DATOS SEGÚN FUENTE
# ====================================================

if source == "DEMO":
    bio = b["biometria"]
    ubi = b["ubicacion"]

    telemetria = {
        "timestamp": time.time(),
        "temperature": jitter(bio["temperatura"], 0.6),
        "heart_rate": int(jitter(bio["pulso"], 6)),
        "spo2": int(jitter(bio["spo2"], 1)),
        "battery": random.randint(65, 100),
        "lat": jitter(ubi["lat"], 0.0004),
        "lon": jitter(ubi["lon"], 0.0004),
        "movement": random.randint(0, 10),
        "bombero_id": bombero_id,
        "mision_id": b["mision_id"]
    }

else:
    # 🔌 LoRaWAN (placeholder realista)
    telemetria = {
        "timestamp": time.time(),
        "temperature": None,
        "heart_rate": None,
        "spo2": None,
        "battery": None,
        "lat": None,
        "lon": None,
        "movement": None,
        "bombero_id": bombero_id,
        "mision_id": b["mision_id"],
        "status": "Esperando datos desde red LoRaWAN"
    }

# ------------------ MÉTRICAS ------------------
col1, col2, col3, col4 = st.columns(4)

def metric_or_na(label, value, unit=""):
    return f"{value} {unit}" if value is not None else "—"

col1.metric("🌡 Temperatura", metric_or_na("T", telemetria["temperature"], "°C"))
col2.metric("❤️ Pulso", metric_or_na("HR", telemetria["heart_rate"], "bpm"))
col3.metric("🫁 SpO₂", metric_or_na("O2", telemetria["spo2"], "%"))
col4.metric("🔋 Batería", metric_or_na("BAT", telemetria["battery"], "%"))

st.markdown("---")

# ------------------ MAPA ------------------
st.subheader("📍 Ubicación")

if telemetria["lat"] and telemetria["lon"]:
    df_map = pd.DataFrame(
        {"lat": [telemetria["lat"]], "lon": [telemetria["lon"]]}
    )
    st.map(df_map, zoom=16)
    st.caption(f"Lat: {telemetria['lat']:.5f} | Lon: {telemetria['lon']:.5f}")
else:
    st.info("📡 GPS no disponible (LoRaWAN)")

# ------------------ GRÁFICA DE PULSO ------------------
st.subheader("📈 Ritmo cardíaco")

if telemetria["heart_rate"] is not None:
    base_hr = telemetria["heart_rate"]
    hr_series = [int(base_hr + random.randint(-7, 7)) for _ in range(30)]

    fig = go.Figure(
        data=[go.Scatter(
            y=hr_series,
            mode="lines+markers",
            line=dict(color="#00FFFF", width=3)
        )]
    )

    fig.update_layout(
        template="plotly_dark",
        yaxis_title="BPM",
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Esperando telemetría cardíaca…")

# ------------------ ALERTAS ------------------
st.subheader("🚨 Alertas")

alertas = []

if telemetria["temperature"] and telemetria["temperature"] >= 38.5:
    alertas.append("🔥 Temperatura elevada")

if telemetria["heart_rate"] and telemetria["heart_rate"] >= 150:
    alertas.append("⚠ Pulso peligrosamente alto")

if telemetria["movement"] is not None and telemetria["movement"] <= 1:
    alertas.append("🟡 Inmovilidad detectada")

if alertas:
    for a in alertas:
        st.error(a)
else:
    st.success("🟢 Estado estable")

# ------------------ LOG ------------------
st.markdown("---")
st.subheader("📦 Log de telemetría")

st.json(telemetria)