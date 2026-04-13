import requests
import json

SCORING_URI = "https://airqualitymlgroup6-enazw.qatarcentral.inference.ml.azure.com/score"
API_KEY = "41dZze0UB0ldvyC705xGMX8lChsPD7uuSFiTy1h2eysxY58lACHHJQQJ99CDAAAAAAAAAAAAINFRAZML1wWl"

def run_inference(test_aqi_value):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # We send both formats to ensure compatibility with different score.py versions
    payload = {
        "aqi": test_aqi_value,
        "data": [test_aqi_value] 
    }
    
    try:
        response = requests.post(SCORING_URI, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, str):
                result = json.loads(result)
            
            # --- Key Mapping Logic ---
            # This checks if the cloud sent 'predicted_aqi_next_hour' OR 'prediction'
            forecast = result.get('predicted_aqi_next_hour') or result.get('prediction')
            input_val = result.get('current_aqi') or test_aqi_value
            status = result.get('status')
            
            print("\n" + "="*40)
            print("   AZURE ML COGNITIVE ENGINE OUTPUT")
            print("="*40)
            print(f"Input AQI:          {input_val}")
            print(f"Safety Ceiling:     {result.get('dynamic_threshold', 'Calculated at Runtime')}")
            print(f"System Status:      [{status}]")
            print(f"1-Hour Forecast:    {forecast}")
            print(f"Calculated Trend:   {result.get('trend', 'Analyzing...')}")
            print(f"Alert Triggered:    {result.get('action_required', 'False')}")
            print("="*40 + "\n")
            
        else:
            print(f"Request failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    run_inference(150.0)
