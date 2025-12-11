import streamlit as st
import pandas as pd
import time
import json
import os
import plotly.graph_objects as go # Importar Plotly
from streamlit_autorefresh import st_autorefresh
# Asegúrate de que estos módulos existen en tu carpeta 'utils'
from utils.demo import get_demo_data
from utils.ttn import get_lorawan_data

# ==== CONFIGURACIÓN INICIAL ====

# 1. CARGAR CSS NASA
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Esto es un error de desarrollo, pero se mantiene la alerta.
    st.error("Error: styles.css no encontrado. Asegúrese de que el archivo CSS esté en el mismo directorio.")
    st.stop()

st.set_page_config(page_title="PULSERA GUARDIÁN - TELEMETRÍA DE MISIÓN", layout="wide", page_icon="📡")

# Helper para obtener clave (Lógica NO MODIFICADA)
def get_key(d,k,default=None):
    return d.get(k, default) if isinstance(d, dict) else default

# --- BARRA LATERAL (CONFIGURACIÓN DE CONSOLA) ---
st.sidebar.title("⚙️ CONFIGURACIÓN DE CONSOLA")

# >>>>>>> ESTOS CONTROLES ESTÁN VISIBLES Y EN EL TOP <<<<<<<
modo = st.sidebar.radio("MODO DE OPERACIÓN:", ("Demo (Simulación)", "LoRaWAN (Misión Real)"))
refresh_rate = st.sidebar.slider("FRECUENCIA DE ACTUALIZACIÓN (s)", 1, 5, 2)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# Control de Zoom/Filtro (Interactividad simulada)
st.sidebar.markdown("---")
st.sidebar.subheader("🎛 CONTROL DE PANTALLAS")
zoom_level = st.sidebar.slider("Nivel de Zoom GPS", 14, 18, 16)
st.sidebar.caption("Modifica la vista del mapa de rastreo.")

# autorefresh
st_autorefresh(interval=refresh_rate * 1000, key="autorefresh")

# --- TÍTULO DE CONSOLA ---
st.markdown(
    """
    <div style='text-align: center;'>
        <h1>🚀 TELEMETRÍA ACTIVA — CÓDIGO GUARDIÁN</h1>
        <p style='color: #00eaff; font-size: 14px; margin-top: -10px;'>CENTRO DE CONTROL DE MISIÓN (ESTADO: EN LÍNEA)</p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---") 

# --- CARGA Y NORMALIZACIÓN DE DATOS (Lógica NO MODIFICADA) ---
data = None
if modo == "Demo (Simulación)":
    data = get_demo_data()
else:
    lr = get_lorawan_data()
    if lr is None:
        st.warning("⚠ No se han recibido paquetes LoRaWAN todavía. Esperando conexión a la red de misión...")
        st.stop()
    
    # Lógica de normalización de datos (completa y restaurada)
    if isinstance(lr, dict) and "payload" in lr:
        payload = lr["payload"]
        if isinstance(payload, dict):
            data = {}
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
            if "lat" in payload and "lon" in payload:
                data["lat"] = float(payload["lat"])
                data["lon"] = float(payload["lon"])
            else:
                gps = payload.get("gps") or payload.get("location")
                if isinstance(gps, dict):
                    data["lat"] = float(gps.get("lat", 0))
                    data["lon"] = float(gps.get("lon", 0))
            for k in ("movement","motion","accel_mag"):
                if k in payload:
                    data["movement"] = payload[k]
                    break
            if "battery" in payload:
                data["battery"] = payload["battery"]
            data["timestamp"] = lr.get("timestamp", time.time())
            if not data:
                data = {"raw_payload": payload, "timestamp": lr.get("timestamp", time.time())}
    else:
        data = lr

if data is None:
    st.warning("ERROR: Datos de misión no disponibles.")
    st.stop()


# --- ZONA SUPERIOR: MÉTRICAS CLAVE Y ALERTAS (LAYOUT PRO) ---
st.subheader("📊 MÓDULOS DE VIGILANCIA")

col_metrics, col_alerts = st.columns([3, 1])

with col_metrics:
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    temp = get_key(data, "temperature", "—")
    smoke = get_key(data, "smoke", "—")
    hr = get_key(data, "heart_rate", "—")
    bat = get_key(data, "battery", "—")
    
    kpi1.metric("🌡 TEMPERATURA", f"{temp}°C")
    kpi2.metric("🌫 NIVEL DE HUMO", f"{smoke}%")
    kpi3.metric("❤️ RITMO CARDIACO", f"{hr} bpm")
    kpi4.metric("🔋 ENERGÍA RESTANTE", f"{bat}%")

with col_alerts:
    # Contenedor visual para el panel de estado (usa estilos CSS)
    st.markdown(
        """
        <div style='background: rgba(4, 30, 60, 0.4); 
                    padding: 10px; 
                    border-radius: 8px; 
                    height: 100%;
                    border: 1px solid #00eaff55;
                    box-shadow: 0 0 10px #00eaff33;'>
            <p style='color: #5cd7ff; font-weight: bold; margin-bottom: 5px; font-size: 14px;'>ESTADO GENERAL DE LA UNIDAD:</p>
        """, 
        unsafe_allow_html=True
    )
    
    alert_msgs = []
    try:
        if isinstance(temp,(int,float)) and float(temp) >= 50:
            alert_msgs.append(("🔥 ADVERTENCIA: TEMPERATURA EXTREMADAMENTE ALTA", "danger"))
        if isinstance(smoke,(int,float)) and float(smoke) >= 70:
            alert_msgs.append(("☣ ALERTA: NIVELES ALTOS DE AGENTES TÓXICOS", "danger"))
        if isinstance(hr,(int,float)) and (int(hr) >= 150 or int(hr) <= 40):
            alert_msgs.append(("⚠ RITMO CARDIACO ANÓMALO", "warning"))
        if isinstance(get_key(data,"movement", None), (int,float)) and int(get_key(data,"movement")) <= 1:
            alert_msgs.append(("🟡 INMOVILIDAD DETECTADA", "warning"))
    except Exception:
        pass
    
    if not alert_msgs:
        st.success("🟢 SISTEMA OPERATIVO: NORMAL")
    else:
        for m,level in alert_msgs:
            if level=="danger":
                st.error(m)
            else:
                st.warning(m)
                
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 

st.markdown("---")

# --- ZONA MEDIA: PANTALLAS DE MONITOREO (MAPA Y GRÁFICO CON PLOTLY) ---
col_map, col_chart = st.columns(2)

with col_map:
    st.subheader("📡 RASTREO GEOLOCALIZACIÓN")
    lat = get_key(data, "lat", None)
    lon = get_key(data, "lon", None)

    if lat and lon:
        df_map = pd.DataFrame({"lat": [lat], "lon": [lon]})
        with st.container():
            # Usa el zoom controlado desde el sidebar
            st.map(df_map, zoom=zoom_level, use_container_width=True)
        st.markdown(f"**Coordenadas Actuales:** Lat: `{lat:.4f}`, Lon: `{lon:.4f}`")
    else:
        st.info("⚠ MÓDULO GPS: Señal no recibida. Mostrando última posición conocida o fallback.")


with col_chart:
    st.subheader("📈 TENDENCIA DE PULSO VITAL (PLOTLY PRO)")
    
    # Generación/Carga de serie histórica (Lógica NO MODIFICADA)
    hr_series = None
    if modo == "Demo (Simulación)":
        import random
        hr_series = [int(get_key(data,"heart_rate",80) + random.randint(-6,6)) for _ in range(30)]
        x_values = list(range(1, 31))
    else:
        payload = get_key(data, "raw_payload", None) or get_key(data, "payload", None)
        if isinstance(payload, dict):
            hr_series = payload.get("hr_values") or payload.get("heart_history") or payload.get("hr_series")
        if not hr_series:
            hr_series = [int(get_key(data,"heart_rate",80))]*30
        x_values = list(range(1, len(hr_series) + 1))
    
    df_hr = pd.DataFrame({"Tiempo": x_values, "Ritmo Cardiaco (bpm)": hr_series})
    
    # --- IMPLEMENTACIÓN PLOTLY CON ESTÉTICA NASA AZUL-CIAN ---
    fig = go.Figure(
        data=[go.Scatter(
            x=df_hr["Tiempo"], 
            y=df_hr["Ritmo Cardiaco (bpm)"], 
            mode='lines+markers',
            line=dict(color='#00FFFF', width=3),
            marker=dict(color='#00FFFF', size=6, line=dict(width=1, color='#00FFFF'))
        )]
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title=None,
        margin=dict(l=10, r=10, t=20, b=20),
        xaxis=dict(
            title='Tiempo (Unidades)', 
            # Corrección del error: usar formato RGBA para transparencia en Plotly
            showgrid=True, gridcolor='rgba(0, 255, 255, 0.2)', 
            zerolinecolor='#00FFFF'
        ),
        yaxis=dict(
            title='Ritmo Cardiaco (bpm)', 
            # Corrección del error: usar formato RGBA para transparencia en Plotly
            showgrid=True, gridcolor='rgba(0, 255, 255, 0.2)', 
            zerolinecolor='#00FFFF'
        ),
        font=dict(
            family="Share Tech Mono, monospace",
            color="#E0F7FF"
        )
    )
    
    # Renderizar el gráfico Plotly (proporciona interactividad por defecto)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


st.markdown("---")

# --- ZONA INFERIOR: LOGS TÉCNICOS ---
st.subheader("📦 LOG DE PAQUETE (TELEMETRÍA RAW)")
# La línea corregida del error de sintaxis (language="json")
st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")

# footer: instrucciones rápidas
st.markdown("---")
st.caption("PROTOCOLO DE TELEMETRÍA: Los datos se actualizan automáticamente cada **" + str(refresh_rate) + " segundos**.")