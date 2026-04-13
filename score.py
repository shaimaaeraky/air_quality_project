import json
import joblib
import os
import logging
import numpy as np

def init():
    """
    This function runs once when the Azure endpoint container starts.
    It loads the model and sets up the safety thresholds.
    """
    global model
    global dynamic_threshold
    
    try:
        # Load the serialized ARIMA model
        # AZUREML_MODEL_DIR is an environment variable created by Azure during deployment
        model_path = os.path.join(os.getenv('AZUREML_MODEL_DIR'), 'aqi_arima_model.pkl')
        model = joblib.load(model_path)
        
        # Define IQR Parameters based on your Historical Dataset
        # Replace these numbers with the actual 25th and 75th percentiles from your Kaggle data
        Q1 = 130 
        Q3 = 170 
        IQR = Q3 - Q1
        
        # Calculate the Dynamic Safety Ceiling (Q3 + 1.5 * IQR)
        dynamic_threshold = Q3 + (1.5 * IQR)
        
        logging.info(f"Model loaded successfully. Dynamic Safety Threshold set to: {dynamic_threshold}")
        
    except Exception as e:
        logging.error(f"Failed to load model or set thresholds in init(): {e}")

def run(raw_data):
    """
    This function runs every time your Python bridge sends a new AQI reading.
    It returns the AI forecast and the anomaly status.
    """
    try:
        # Parse the incoming JSON request from the Python bridge
        data = json.loads(raw_data)
        current_aqi = float(data.get("aqi", 0.0))
        
        # Predict the next 1 hour of AQI using the ARIMA model
        # Depending on pmdarima version, predict() returns an array or series
        forecast_array = model.predict(n_periods=1)
        predicted_aqi = float(forecast_array[0]) if isinstance(forecast_array, (list, np.ndarray)) else float(forecast_array)
        
        # Apply the IQR Anomaly Detection Logic
        is_anomaly = current_aqi > dynamic_threshold
        status = "Danger" if is_anomaly else "Safe"
        
        # Determine trend for proactive HVAC control
        trend = "rising" if predicted_aqi > current_aqi else "falling"
        
        # Construct the Cognitive Response payload
        response = {
            "current_aqi": current_aqi,
            "dynamic_threshold": dynamic_threshold,
            "predicted_aqi_next_hour": round(predicted_aqi, 2),
            "status": status,
            "trend": trend,
            "action_required": is_anomaly
        }
        
        return json.dumps(response)
        
    except Exception as e:
        # Return the error in JSON format so the bridge script doesn't crash
        error_msg = str(e)
        logging.error(f"Error during run(): {error_msg}")
        return json.dumps({"error": error_msg, "status": "Error"})
