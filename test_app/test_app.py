import requests
import json
import datetime as dt
import pandas as pd
import collections
import json


import config as c


def get_testing_config():
    json_test_data_dict = ''

    # Opening JSON file with the test data config
    f = open(c.TESTING_JSON)
  
    # returns JSON object as 
    # a dictionary
    json_test_data_dict = json.load(f)
  
    # Closing file
    f.close()

    return json_test_data_dict

#compare two list: base and what we receive
def compare_list(l1,l2):
            if(collections.Counter(l1)==collections.Counter(l2)):
                return True
            else: 
                return False

def trigger_cloud_function(parameters):

    web_api_url = 'https://europe-west1-lorelee-keep-312708.cloudfunctions.net/search-lei'

    print("------------ Attempting to parse: ----------------")
    print(parameters)
    print()

    headers = {
        "Content-Type": "application/json",
    }
    
    response = requests.request("POST", web_api_url, json=parameters, headers=headers)
    try:
        response_dict = json.loads(response.text)
    except:
        print('failed to load cloud function result')
        response_dict = response.text
    return response_dict    


if __name__ == "__main__":
    start_time = dt.datetime.now()
    print("Started at ", start_time)

    test_case_info = get_testing_config()

    report_data = []

    for payload in test_case_info:

        service_output = trigger_cloud_function(payload['arguments'])
              
        report_dict = {
                'id': payload['id'],
                'test_passed': False,
                'comment': payload['arguments']
        }
        #check output on dictionary and word in dictionary
        if isinstance(service_output, dict):
        #check cases with mistakes in arguments
            if len(service_output.keys())==1 and compare_list (service_output.keys(),['error']):
                result_test='test case successful'
            else:
                result_test='test case failed'
    
        else:
         #cut one column with lei data   
            df=pd.DataFrame.from_records(service_output)
            col_one_list=df["LEI"].to_list()
            lei_from_test_cases=payload['expected']['LEI']       
        #compare two lists
        if compare_list(col_one_list,lei_from_test_cases):
            result_test='test case successful'
            print(result_test)
        else:
            result_test='test case failed'
            print(result_test) 
     #create report dictionary, with information below
        report_dict = {
                'id': payload['id'],
                'result': result_test,
                'comment': payload['arguments']
        }
        print(report_dict)
        report_data.append(report_dict)
        print(report_data)

        

    finish_time = dt.datetime.now()
    report_name = 'LEI_IS_test_report_{}.csv'.format(finish_time.strftime("%Y-%m-%d_%H-%M-%S"))
    report_path = "/".join([c.OUTPUT_FOLDER_PATH, report_name])
    df_final = pd.DataFrame.from_dict(report_data)
    df_final.to_csv (report_path, index = False, header=True)
        
    
    print("DONE at ", finish_time)
    elapsed = finish_time - start_time
    print("Elapsed time: ", elapsed)