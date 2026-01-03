import streamlit as st
import json

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

source = st.session_state.get("data_source", "DEMO")

if not st.session_state.get("authenticated", False):
    st.stop()

st.set_page_config(page_title="Misiones", layout="wide")

# -------- Cargar datos --------
with open("data/misiones.json", "r", encoding="utf-8") as f:
    misiones = json.load(f)

with open("data/bomberos.json", "r", encoding="utf-8") as f:
    bomberos_raw = json.load(f)["bomberos"]

# 🔑 indexar bomberos por ID
bomberos = {b["id"]: b for b in bomberos_raw}

st.title("🚨 MISIONES ACTIVAS")
st.markdown("---")

mision_id = st.selectbox(
    "Selecciona una misión",
    list(misiones.keys()),
    format_func=lambda x: misiones[x]["nombre"]
)

mision = misiones[mision_id]

st.subheader(mision["nombre"])
st.caption(f"Tipo de incendio: {mision['tipo']}")
st.markdown("---")

for categoria, equipos in mision["equipos"].items():
    st.markdown(f"### 🔹 {categoria}")

    for equipo, lista in equipos.items():
        with st.expander(f"🚒 {equipo}"):
            for bid in lista:
                b = bomberos.get(bid)
                nombre = b["nombre"] if b else "No registrado"

                if st.button(f"👨‍🚒 {nombre} ({bid})", key=f"{mision_id}-{bid}"):
                    st.session_state["bombero_id"] = bid
                    st.switch_page("pages/3_Bomberos.py")