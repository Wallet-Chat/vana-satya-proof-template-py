import json
import logging
import os
from typing import Dict, Any

import requests

from my_proof.models.proof_response import ProofResponse


class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])

    def generate(self) -> ProofResponse:
        """Generate proofs for all input files."""
        logging.info("Starting proof generation")

        # Iterate through files and calculate data validity
        account_email = None
        total_score = 0
        data_id_api_response = "NONE"
        id_from_json = "ENON"

        #print("API KEY from ENV: ", self.config["user_api_key"])

        for input_filename in os.listdir(self.config['input_dir']):
            input_file = os.path.join(self.config['input_dir'], input_filename)
            if os.path.splitext(input_file)[1].lower() == '.json':
                with open(input_file, 'r') as f:
                    input_data = json.load(f)

                    if input_filename == 'daily_sleep.json':
                        #print("In Daily Sleep JSON", input_data)
                        if "data" in input_data and len(input_data["data"]) > 0:
                            id_from_json = input_data["data"][0]["id"]
                            print("ID from File: ", id_from_json)
                        else:
                            print("Error: 'data' key is missing or empty in daily_sleep.json")
                        #print("ID from JSON: ", id_from_json)
                        #apikey_from_json = input_data.get('apikey', None)
                        continue

                    # elif input_filename == 'activity.json':
                    #     total_score = sum(item['score'] for item in input_data)
                    #     continue


        #grab data from the Oura API to verify:
        url = "https://api.ouraring.com/v2/usercollection/daily_sleep"

        # Make a GET request to the Oura API with the authorization token
        headers = {
            "Authorization": f"Bearer {self.config["user_api_key"]}"
        }

        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Check if the response contains data and has at least one element
            if "data" in data and len(data["data"]) > 0:
                data_id_api_response = data["data"][0]["id"]
                print("ID from API: ", data_id_api_response)
            else:
                print("Response JSON does not contain expected data:", data)
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")

        #email_matches = self.config['user_email'] == account_email
        #print("comparing data ids: ", data_id_api_response, id_from_json)
        valid_data_id = data_id_api_response == id_from_json
        #score_threshold = fetch_random_number()

        # Calculate proof-of-contribution scores: https://docs.vana.org/vana/core-concepts/key-elements/proof-of-contribution/example-implementation
        self.proof_response.ownership = 1.0 if valid_data_id else 0.0  # Does the data belong to the user? Or is it fraudulent?

        self.proof_response.quality = 1 #max(0, min(total_score / score_threshold, 1.0))  # How high quality is the data?

        self.proof_response.authenticity = 0  # How authentic is the data is (ie: not tampered with)? (Not implemented here)
        self.proof_response.uniqueness = 0  # How unique is the data relative to other datasets? (Not implemented here)

        # Calculate overall score and validity
        self.proof_response.score = 0.6 * self.proof_response.quality + 0.4 * self.proof_response.ownership
        self.proof_response.valid = valid_data_id #and total_score >= score_threshold

        # Additional (public) properties to include in the proof about the data
        self.proof_response.attributes = {
            'total_score': total_score,
            #'score_threshold': score_threshold,
            'valid_data_id': valid_data_id,
        }

        # Additional metadata about the proof, written onchain
        self.proof_response.metadata = {
            'dlp_id': self.config['dlp_id'],
        }

        return self.proof_response


def fetch_random_number() -> float:
    """Demonstrate HTTP requests by fetching a random number from random.org."""
    try:
        response = requests.get('https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new')
        return float(response.text.strip())
    except requests.RequestException as e:
        logging.warning(f"Error fetching random number: {e}. Using local random.")
        return __import__('random').random()
