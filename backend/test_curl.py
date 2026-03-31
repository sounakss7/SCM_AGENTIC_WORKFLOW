import requests
try:
    print(requests.post('http://127.0.0.1:8000/api/place_order', json={'order_id': 'test', 'simulate_disruption': False}).json())
except Exception as e:
    print("Error:", e)
