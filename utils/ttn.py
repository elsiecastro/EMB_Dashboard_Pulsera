# utils/ttn.py
"""
Módulo para obtener el último paquete LoRaWAN.
Implementa dos flujos:
 - MQTT: crea un cliente que suscribe a un topic y guarda el último mensaje en data/last_lora.json
 - Webhook: alternativa: un endpoint FastAPI (receiver.py) escribirá al mismo archivo.

CONFIGURACIÓN (variables de entorno o editar aquí):
- LORA_BACKEND = "mqtt"  # o "webhook"
- MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS, MQTT_TOPIC
"""

import json
import os
import threading
import time

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "last_lora.json")
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# simple accessor; devuelve dict o None
def _read_last():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def get_lorawan_data():
    """
    Devuelve el último paquete LoRaWAN como diccionario (o None si no hay datos).
    Este dato puede ser escrito por:
      - el cliente MQTT (si seleccionas LORA_BACKEND=mqtt)
      - el receiver FastAPI (webhook)
    """
    return _read_last()


# -------------------------
# MQTT helper (background)
# -------------------------
def _start_mqtt_client_if_needed():
    """
    Para desarrollo local: si configuras LORA_BACKEND=mqtt y las variables MQTT_*,
    el cliente MQTT se levantará en background y actualizará data/last_lora.json
    """
    cfg_backend = os.environ.get("LORA_BACKEND", "mqtt").lower()
    if cfg_backend != "mqtt":
        return

    try:
        import paho.mqtt.client as mqtt
    except Exception:
        # no instalado
        return

    MQTT_HOST = os.environ.get("MQTT_HOST", "")
    MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
    MQTT_USER = os.environ.get("MQTT_USER", "")
    MQTT_PASS = os.environ.get("MQTT_PASS", "")
    MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "#")  # suscribir por defecto a todo

    if not MQTT_HOST:
        return

    client = mqtt.Client()

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS or None)

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            c.subscribe(MQTT_TOPIC)
        else:
            print("MQTT connect failed rc=", rc)

    def on_message(c, userdata, msg):
        try:
            payload_s = msg.payload.decode("utf-8")
            # TTN puede enviar JSON; guardamos raw y si tiene 'uplink_message' usamos decoded payload.
            raw = None
            try:
                raw = json.loads(payload_s)
            except Exception:
                raw = {"raw": payload_s}

            # if TTN v3 uplink_message with decoded_payload:
            data = None
            if isinstance(raw, dict) and "uplink_message" in raw:
                up = raw.get("uplink_message", {})
                # prefer decoded_payload if exists
                dec = up.get("decoded_payload")
                if dec:
                    data = dict(dec)
                else:
                    # try raw bytes base64 (user needs to implement decoder)
                    data = {"raw_uplink": up}
            else:
                data = raw

            # enrich with topic and timestamp
            out = {
                "received_topic": msg.topic,
                "payload": data,
                "timestamp": time.time()
            }

            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(out, f)
        except Exception as e:
            print("Error processing mqtt message:", e)

    client.on_connect = on_connect
    client.on_message = on_message

    def _loop():
        try:
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_forever()
        except Exception as e:
            print("MQTT client error:", e)
            time.sleep(5)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()

# start automatically if user requested mqtt backend
_start_mqtt_client_if_needed()