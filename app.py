# app.py
import streamlit as st
import pandas as pd
import time
import json
import os
from streamlit_autorefresh import st_autorefresh
from utils.demo import get_demo_data
from utils.ttn import get_lorawan_data

st.set_page_config(page_title="Pulsera Bombero - Monitor", layout="wide", page_icon="🚒")

st.sidebar.title("⚙️ Configuración")
modo = st.sidebar.radio("Selecciona el modo:", ("Demo", "LoRaWAN (Real)"))
refresh_rate = st.sidebar.slider("Refrescar cada (segundos)", 1, 5, 2)

# autorefresh
st_autorefresh(interval=refresh_rate * 1000, key="autorefresh")

st.title("🚒 Pulsera de Seguridad — Dashboard")

# Obtener datos según modo
data = None
if modo == "Demo":
    data = get_demo_data()
else:
    # modo real: leer último paquete escrito por utils/ttn.py (MQTT) o receiver.py (Webhook)
    lr = get_lorawan_data()
    if lr is None:
        st.warning("⚠ No se han recibido paquetes LoRaWAN todavía. Esperando conexión...")
        st.stop()
    # ttndata puede venir en varias formas; normalizamos
    # si file contiene {"payload": {...}, "received": {...}}
    if isinstance(lr, dict) and "payload" in lr:
        payload = lr["payload"]
        # si payload ya es dict de sensores, úsalo
        # si viene en estructura nested, intenta hallar keys comunes
        if isinstance(payload, dict):
            # ejemplo común: payload may have temperature, heart_rate, smoke, lat, lon
            data = {}
            # mapping heurístico --- adapta según cómo tu dispositivo envia
            for k in ("temperature","temp","t"):
                if k in payload:
                    data["temperature"] = payload[k]
                    break
            for k in ("heart_rate","hr","pulse"):
                if k in payload:
                    data["heart_rate"] = payload[k]
                    break
            for k in ("smoke","co","gas","air_quality"):
                if k in payload:
                    data["smoke"] = payload[k]
                    break
            # gps
            if "lat" in payload and "lon" in payload:
                data["lat"] = float(payload["lat"])
                data["lon"] = float(payload["lon"])
            else:
                # a veces GPS está en payload['gps'] = {"lat":..., "lon":...}
                gps = payload.get("gps") or payload.get("location")
                if isinstance(gps, dict):
                    data["lat"] = float(gps.get("lat", 0))
                    data["lon"] = float(gps.get("lon", 0))
            # movement / accel
            for k in ("movement","motion","accel_mag"):
                if k in payload:
                    data["movement"] = payload[k]
                    break
            # battery
            if "battery" in payload:
                data["battery"] = payload["battery"]
            # fallback: if payload seems entire sensor dict
            # embed timestamp
            data["timestamp"] = lr.get("timestamp", time.time())
            # if some keys missing, try raw payload root
            if "temperature" not in data and isinstance(payload, dict):
                # try find numeric fields
                for k,v in payload.items():
                    if isinstance(v, (int,float)) and k.lower().find("temp")>=0:
                        data["temperature"] = v
            # If still empty set entire payload into 'raw'
            if not data:
                data = {"raw_payload": payload, "timestamp": lr.get("timestamp", time.time())}
    else:
        # legacy shape or direct sensor dict
        data = lr

# --- ahora mostramos la UI si data existe ---
if data is None:
    st.warning("No hay datos disponibles.")
    st.stop()

# Normalize keys for demo (demo returns lat/lon etc.)
def get_key(d,k,default=None):
    return d.get(k, default) if isinstance(d, dict) else default

# top cards
col1, col2, col3, col4 = st.columns([1,1,1,1])
temp = get_key(data, "temperature", "—")
smoke = get_key(data, "smoke", "—")
hr = get_key(data, "heart_rate", "—")
bat = get_key(data, "battery", "—")

col1.metric("🌡 Temperatura (°C)", f"{temp}")
col2.metric("🌫 Humo / Air", f"{smoke}")
col3.metric("❤️ Ritmo cardiaco (bpm)", f"{hr}")
col4.metric("🔋 Batería (%)", f"{bat}")

# mapa
st.subheader("📍 Ubicación")
lat = get_key(data, "lat", None)
lon = get_key(data, "lon", None)
if lat and lon:
    df_map = pd.DataFrame({"lat":[lat],"lon":[lon]})
    st.map(df_map, zoom=15)
else:
    st.info("GPS no disponible en el paquete actual.")

# alertas
st.subheader("⚠️ Alertas")
alert_msgs = []
try:
    if isinstance(temp,(int,float)) and float(temp) >= 50:
        alert_msgs.append(("🔥 ALTA TEMPERATURA", "danger"))
    if isinstance(smoke,(int,float)) and float(smoke) >= 70:
        alert_msgs.append(("🌫 NIVELES ALTOS DE HUMO", "danger"))
    if isinstance(hr,(int,float)) and (int(hr) >= 150 or int(hr) <= 40):
        alert_msgs.append(("⚠ Ritmo cardiaco anómalo", "warning"))
    if isinstance(get_key(data,"movement", None), (int,float)) and int(get_key(data,"movement")) <= 1:
        alert_msgs.append(("🟡 Movimiento bajo - posible inmovilidad", "warning"))
except Exception:
    pass

if not alert_msgs:
    st.success("🟢 Estado normal")
else:
    for m,level in alert_msgs:
        if level=="danger":
            st.error(m)
        else:
            st.warning(m)

# gráfico de ritmo cardiaco histórico (si demo, pintamos serie; si real, intentamos leer 'history' en payload)
st.subheader("📈 Ritmo cardíaco - últimos segundos")
hr_series = None
# si demo: generamos una mini-serie
if modo == "Demo":
    import random
    hr_series = [int(get_key(data,"heart_rate",80) + random.randint(-6,6)) for _ in range(30)]
else:
    # si la carga real tiene 'heart_history' o 'hr_values', úsala
    payload = get_key(data, "raw_payload", None) or get_key(data, "payload", None)
    if isinstance(payload, dict):
        hr_series = payload.get("hr_values") or payload.get("heart_history") or payload.get("hr_series")
    if not hr_series:
        # fallback: repetir valor actual
        hr_series = [int(get_key(data,"heart_rate",80))]*30

st.line_chart(hr_series)

# registro del paquete (útil para jurados devs)
st.subheader("📦 Último paquete (raw)")
st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")

# footer: instrucciones rápidas
st.markdown("---")
st.caption("Modo demo = datos generados. Modo LoRaWAN = lee el último paquete depositado por MQTT o Webhook en data/last_lora.json.")