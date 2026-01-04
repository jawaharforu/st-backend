import json
import os
from google import genai
from google.genai import types

# API Key provided by user
# In production, this should be in .env
API_KEY = "AIzaSyDyw-xWyPA1nPCBMHS4Khk5L9ghuizBKf0"

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"FATAL ERROR: Gemini API Key configuration failed: {e}")
    client = None

# Schema definition
analysis_schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "status": types.Schema(
            type=types.Type.STRING,
            description="Overall assessment: 'NORMAL', 'CAUTION', or 'ABNORMAL'."
        ),
        "temperature_status": types.Schema(
            type=types.Type.STRING,
            description="Temperature assessment: 'NORMAL', 'CAUTION', or 'ABNORMAL'."
        ),
        "humidity_status": types.Schema(
            type=types.Type.STRING,
            description="Humidity assessment: 'NORMAL', 'CAUTION', or 'ABNORMAL'."
        ),
        "summary_for_farmer": types.Schema(
            type=types.Type.STRING,
            description="A simple summary of the incubator's health (1-2 sentences). Non-technical language only."
        ),
        "recommended_action": types.Schema(
            type=types.Type.STRING,
            description="The single most important action the farmer should take immediately. If status is NORMAL, recommend 'Keep monitoring'."
        )
    },
    required=["status", "summary_for_farmer", "recommended_action"]
)

class AIService:
    @staticmethod
    def analyze_incubator_telemetry(telemetry_data: list) -> dict:
        """
        Analyzes the incubator telemetry data using the Gemini model and returns a JSON response.
        """
        if not client:
             return {"status": "ERROR", "summary_for_farmer": "AI Service not configured.", "recommended_action": "Contact support."}

        # Convert the Python list of dicts into a JSON string
        # Limit to essential fields to save tokens if needed, but full telemetry is fine
        data_json_string = json.dumps(telemetry_data, indent=2, default=str)

        system_instruction = (
            "You are an expert incubator monitoring AI assistant for farmers. "
            "Analyze the provided JSON telemetry data (last 50 minutes) for a chick egg incubator. "
            "The ideal temperature is 98°F to 100°F. The ideal humidity is 50% to 65%. "
            "Your response MUST STRICTLY be a JSON object that adheres to the provided schema. "
            "Use non-technical, simple language for the summary and action."
        )

        prompt = (
            f"Analyze the following incubator data and provide a concise health report for the farmer: "
            f"\n\n--- TELEMETRY DATA ---\n{data_json_string}\n\n"
            f"1. Determine the overall status: NORMAL, CAUTION, or ABNORMAL."
            f"2. Summarize the condition and recommend the immediate action."
        )

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=analysis_schema,
                temperature=0.0
            )

            response = client.models.generate_content(
                model='gemini-2.0-flash-exp', # Using standard flash model or closest available
                contents=prompt,
                config=config,
            )

            analysis_result = json.loads(response.text)
            return analysis_result

        except Exception as e:
            print(f"An error occurred during API call: {e}")
            return {"status": "ERROR", "summary_for_farmer": "Could not connect to AI service.", "recommended_action": "Check network connection."}

ai_service = AIService()
