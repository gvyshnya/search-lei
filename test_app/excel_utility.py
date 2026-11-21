import pandas
import json
import uuid

def excel_to_json(xlsx_path: str, json_path: str):
    # save excel file as json file, using pandas
    excel_data_df = pandas.read_excel(excel_file_path)
    # print(excel_data_df)
    json_str = excel_data_df.to_json(orient='records')
    
    json_data = json.loads(json_str)

    # print('Excel Sheet to JSON:')
    # print(json_data)
    json_data_list = []

    for record in json_data:
        test_case = {}
        test_case['id'] = str(uuid.uuid4())

        test_case['arguments'] ={
            "legal_entity_name": record,
	        "country_code": record
        },
        test_case['expected'] = {
        'LEI': record['LEI'],
        }
        json_data_list.append(test_case)
    
    # print(json_data_list)

    json_to_write = json.dumps(json_data_list)
    
    jsonFile = open(json_file_path, "w")
    jsonFile.write(json_to_write)
    jsonFile.close()

    print('saved as', json_file_path)

json_file_path = './data/test_cases_2.json'
excel_file_path = './data/test_cases_excel.xlsx'

excel_to_json(excel_file_path, json_file_path)