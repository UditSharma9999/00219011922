import asyncio
import os
import requests
from flask import Flask, jsonify, request
import time
from dotenv import load_dotenv

# loading environment variables
load_dotenv()


app = Flask(__name__)


TEST_SERVER_BASE_URL = os.getenv("TEST_SERVER_BASE_URL")
WINDOW_SIZE = 10
TIMEOUT_SECONDS = 0.5  # 500 ms

# List to store numbers in the window
number_window = []
access_token = os.getenv("access_token")


headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

async def fetch_numbers_from_server(endpoint):
    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()['numbers']
        else:
            return {"error": f"Failed to fetch numbers: {response.status_code}"}
    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}


@app.route('/numbers/<numberid>', methods=['GET'])
def fetch_numbers(numberid):

    # Mapping from number ID to test server endpoint
    endpoint_map = {
        'p': TEST_SERVER_BASE_URL + 'primes',
        'f': TEST_SERVER_BASE_URL + 'fibo',
        'e': TEST_SERVER_BASE_URL + 'n',
        'r': TEST_SERVER_BASE_URL + 'n'
    }
    
    if numberid not in endpoint_map:
        return jsonify({"error": "Invalid number ID"}), 400
    
    endpoint = endpoint_map[numberid]
    
    # Fetch numbers asynchronously
    async def fetch_and_update(number_window):
        
        start_time = time.time()
        result = await fetch_numbers_from_server(endpoint)
        elapsed_time = time.time() - start_time
        
        if elapsed_time > TIMEOUT_SECONDS:
            return jsonify({"error": "Request timed out"}), 500
        
        if 'error' in result:
            return jsonify(result), 500
        
        fetched_numbers = result
        
        # Update number window with unique numbers
        for num in fetched_numbers:
            if num not in number_window:
                number_window.append(int(num))
        
        if len(number_window) > WINDOW_SIZE:
            number_window = number_window[-WINDOW_SIZE:]
        
        # Calculate sum and average
        window_sum = sum(number_window)
        window_len = len(number_window)
        avg = window_sum / window_len if window_len > 0 else 0
        
        # Prepare response
        response = {
            "numbers": fetched_numbers,
            "windowPrevState": number_window[:-len(fetched_numbers)],
            "windowCurrState": number_window,
            "avg": avg
        }
        return jsonify(response)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_and_update(number_window))
    loop.close()
    return result

if __name__ == '__main__':
    app.run(debug=True)
