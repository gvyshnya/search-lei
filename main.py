import os
from flask import Flask, request, Response

import pandas as pd
import pdpipe as pdp
from fuzzywuzzy import fuzz

IS_LOCAL = True if os.environ.get("IS_LOCAL", "True").lower() == "true" else False
BQ_PROJECT_ID = os.environ.get("PROJECT_ID", "lorelee-keep-312708")

app = Flask(__name__)

def get_country_data(
        gcp_project_id: str,
        country_code: str
) -> pd.DataFrame:

    query = """
        SELECT * 
        FROM `{}.lei_golden.Countries` 
        WHERE 
        Alpha_2_Code = '{}';
    """.format(gcp_project_id, country_code)

    df = pd.read_gbq(
        query,
        project_id=gcp_project_id,
        dialect='standard',
    )

    return df


def country_code_is_valid(
        gcp_project_id: str,
        country_code_2_letters: str
) -> bool:

    result = True
    df = get_country_data(gcp_project_id, country_code_2_letters)
    if df.shape[0] < 1:
        # if the search request did not return any records,
        # we consider the country  code to be invalid
        result = False
    return result


def get_raw_data(
        gcp_project_id: str,
        legal_entity_name: str,
        country_code: str
) -> pd.DataFrame:
    legal_entity_name_lower = legal_entity_name.lower()

    query = """
        SELECT * 
        FROM `{}.lei_golden.Entities` 
        WHERE 
        LOWER(LegalName) LIKE '%{}%' AND 
        LegalAddress_Country = '{}';
    """.format(gcp_project_id, legal_entity_name_lower, country_code)

    df = pd.read_gbq(
        query,
        project_id=gcp_project_id,
        dialect='standard',
    )

    return df


def get_entity_fuzzy_matches(
        df: pd.DataFrame,
        entity_name: str

) -> pd.DataFrame:
    # note: more info on the fuzzy string matching metrics provided by
    # https://towardsdatascience.com/string-matching-with-fuzzywuzzy-e982c61f8a84
    df['fuzzy_token'] = entity_name.lower()

    pipe_calc = pdp.PdPipeline([
        pdp.ApplyToRows(lambda row: row['LegalName'].lower(), 'legal_name'),
        pdp.ApplyToRows(lambda row: fuzz.ratio(row['legal_name'], row['fuzzy_token']), 'fuzzy_ratio'),
        pdp.ApplyToRows(lambda row: fuzz.partial_ratio(row['legal_name'], row['fuzzy_token']), 'partial_ratio'),
        pdp.ApplyToRows(lambda row: fuzz.token_sort_ratio(row['legal_name'], row['fuzzy_token']),
                        'ignore_order_ratio'),
        pdp.ApplyToRows(lambda row: fuzz.token_set_ratio(row['legal_name'], row['fuzzy_token']),
                        'ignore_duplicate_ratio')
    ])

    df = pipe_calc.apply(df)

    return df

def get_error_message_as_json(error_text: str) -> str:
    str_json = "".join(["{\"error\": \"",  error_text, "\"}"])
    return str_json


@app.route("/", methods=["POST"])
def do_fuzzy_search(request: request):
    request_json = request.get_json(silent=True)

    legal_entity_name = request_json["legal_entity_name"]
    country_code = request_json["country_code"]

    gcp_project_id = BQ_PROJECT_ID

    if not country_code_is_valid(gcp_project_id, country_code):
        error_msg = 'Invalid country code: {}'.format(country_code)
        str_json = get_error_message_as_json(error_msg)
        return Response(status=500, response=str_json, mimetype='application/json')

    raw_df = get_raw_data(gcp_project_id, legal_entity_name, country_code)
    if raw_df.shape[0] == 0:
        error_msg = "Nothing found for country '{}' and the legal name pattern '{}'".format(country_code, legal_entity_name)
        str_json = get_error_message_as_json(error_msg)
        return Response(status=500, response=str_json, mimetype='application/json')

    cols_to_output = raw_df.columns

    matches_df = get_entity_fuzzy_matches(raw_df, legal_entity_name)

    # filter matches
    filtered_matches_df = matches_df.query("partial_ratio>70")

    if filtered_matches_df.shape[0] == 0:
        error_msg = "No matches detected for country '{}' and the legal name pattern '{}'".format(country_code, legal_entity_name)
        str_json = get_error_message_as_json(error_msg)
        return Response(status=500, response=str_json, mimetype='application/json')

    # prepare the output df
    output_df = filtered_matches_df[[c for c in matches_df.columns if c in cols_to_output]]

    # convert to a JSON records array
    str_json = output_df.to_json(orient='records')

    return Response(status=200, response=str_json, mimetype='application/json')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
