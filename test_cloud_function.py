import requests
import datetime as dt

if __name__ == "__main__":
    start_time = dt.datetime.now()
    print("Started at ", start_time)

    lei_web_api_url = 'https://europe-west1-lorelee-keep-312708.cloudfunctions.net/search-lei'

    payload = {
        "legal_entity_name": "xyz",
        "country_code": "PL"
    }
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.request("POST", lei_web_api_url, json=payload, headers=headers)

    print(response.text)
    print('------------------------------------------------')
    print('We are done. That is all, folks!')
    finish_time = dt.datetime.now()
    print("Finished at ", finish_time)
    elapsed = finish_time - start_time
    print("Elapsed time: ", elapsed)
