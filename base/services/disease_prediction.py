import requests

def get_disease_prediction(symptoms):
    url = 'http://localhost:5000/predict'
    response = requests.post(url, json={'symptoms': symptoms})

    if response.status_code == 200:
        return response.json().get('prediction')
    else:
        return {'error': 'Failed to get prediction'}