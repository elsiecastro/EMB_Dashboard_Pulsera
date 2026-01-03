import streamlit as st
import json

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

source = st.session_state.get("data_source", "DEMO")

if not st.session_state.get("authenticated", False):
    st.stop()

with open("data/bomberos.json", "r", encoding="utf-8") as f:
    bomberos = json.load(f)["bomberos"]

st.title("🚨 Alertas Globales")

for b in bomberos:
    for alerta in b["alertas"]:
        st.warning(f"{b['nombre']} ({b['id']}): {alerta}")