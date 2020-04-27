import requests
import json

def get_symptoms():
    url = "https://priaid-symptom-checker-v1.p.rapidapi.com/symptoms"

    querystring = {"format": "json", "language": "en-gb"}

    headers = {
        'x-rapidapi-host': "priaid-symptom-checker-v1.p.rapidapi.com",
        'x-rapidapi-key': "6a93fdec92mshd41a9d80e2f185bp185f6bjsn726d7dd0f858"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    # print(type(json.loads(response.text)))

    symptoms = json.loads(response.text)

    return symptoms

import pandas as pd
symptoms = get_symptoms()
df = pd.DataFrame(symptoms)
print(df)
df.to_csv('symptoms.csv')



