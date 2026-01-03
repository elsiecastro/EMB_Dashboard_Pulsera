import streamlit as st
import pandas as pd
import json
import numpy as np

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Detalle Misión", layout="wide")

# ------------------ Seguridad ------------------
if not st.session_state.get("authenticated", False):
    st.stop()

# ------------------ Cargar datos ------------------
with open("data/misiones.json", "r", encoding="utf-8") as f:
    misiones = json.load(f)

with open("data/bomberos.json", "r", encoding="utf-8") as f:
    bomberos_list = json.load(f)["bomberos"]

bomberos = {b["id"]: b for b in bomberos_list}

# ------------------ Selección de misión ------------------
mision_id = st.selectbox(
    "Selecciona una misión activa",
    list(misiones.keys()),
    format_func=lambda x: misiones[x]["nombre"]
)

mision = misiones[mision_id]

st.title(f"🧯 Detalle de Misión: {mision['nombre']}")
st.caption(f"Tipo de incendio: **{mision['tipo']}**")
st.markdown("---")

# ------------------ Bomberos de la misión ------------------
bomberos_mision = [b for b in bomberos_list if b["mision_id"] == mision_id]

if not bomberos_mision:
    st.warning("No hay bomberos asignados a esta misión.")
    st.stop()

# ------------------ MAPA GLOBAL ------------------
st.subheader("📍 Ubicación de bomberos en la misión")
df_map = pd.DataFrame({
    "lat": [b["ubicacion"]["lat"] for b in bomberos_mision],
    "lon": [b["ubicacion"]["lon"] for b in bomberos_mision],
    "nombre": [b["nombre"] for b in bomberos_mision]
})
st.map(df_map, zoom=13)

# ------------------ ESTADÍSTICAS ------------------
st.subheader("📊 Estadísticas de la misión")

temperaturas = [b["biometria"]["temperatura"] for b in bomberos_mision]
pulso = [b["biometria"]["pulso"] for b in bomberos_mision]
spo2 = [b["biometria"]["spo2"] for b in bomberos_mision]

alertas_count = [len(b.get("alertas", [])) for b in bomberos_mision]

col1, col2, col3, col4 = st.columns(4)
col1.metric("👨‍🚒 Bomberos activos", len(bomberos_mision))
col2.metric("🌡 Temperatura promedio", f"{np.mean(temperaturas):.1f} °C")
col3.metric("❤️ Pulso promedio", f"{np.mean(pulso):.0f} bpm")
col4.metric("🫁 SpO₂ promedio", f"{np.mean(spo2):.0f} %")

# Alertas por misión
st.subheader("🚨 Alertas en la misión")
if sum(alertas_count) > 0:
    for b in bomberos_mision:
        for a in b.get("alertas", []):
            st.error(f"{b['nombre']} ({b['id']}): {a}")
else:
    st.success("🟢 Sin alertas activas")

st.markdown("---")
