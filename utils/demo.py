import random

def get_demo_data():
    return {
        "lat": -2.146 + random.uniform(-0.0003, 0.0003),
        "lon": -79.964 + random.uniform(-0.0003, 0.0003),
        "temperature": random.randint(25, 70),
        "smoke": random.randint(0, 100),
        "heart_rate": random.randint(70, 160),
        "movement": random.randint(0, 10)
    }