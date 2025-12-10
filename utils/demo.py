# utils/demo.py
import random
import time

def get_demo_data():
    """
    Genera datos demo realistas para la pulsera:
    - lat/lon se mueven levemente
    - temperatura, humo, ritmo cardíaco, movimiento
    """
    base = {
        "lat": -2.1460,
        "lon": -79.9640,
        "temperature": 36.0,
        "smoke": 10,
        "heart_rate": 80,
        "movement": 8,
        "battery": 90,
        "timestamp": time.time()
    }

    # pequeñas variaciones para simular tiempo real
    base["lat"] += random.uniform(-0.0008, 0.0008)
    base["lon"] += random.uniform(-0.0008, 0.0008)
    base["temperature"] = round(base["temperature"] + random.uniform(-1.5, 2.5), 1)
    base["smoke"] = int(max(0, min(100, base["smoke"] + random.randint(-5, 10))))
    base["heart_rate"] = int(max(40, min(190, base["heart_rate"] + random.randint(-6, 8))))
    base["movement"] = int(max(0, min(10, base["movement"] + random.randint(-2, 2))))
    base["battery"] = int(max(0, min(100, base["battery"] + random.randint(-1, 0))))
    return base