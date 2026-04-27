import os
import google.generativeai as genai
from PIL import Image
import json
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def verify_infringement(image_path):
    """
    Uses Gemini Vision to verify if an image contains sports IP infringement.
    """
    if not model:
        return {"error": "Gemini API key not configured"}

    try:
        img = Image.open(image_path)
        prompt = """
        Analyze this image for sports copyright infringement. 
        1. Does it appear to be a live sports broadcast?
        2. Identify any broadcaster logos (e.g., Sky Sports, ESPN, Star Sports, NBC).
        3. Identify the teams or event if possible.
        4. Look for 'pirate' indicators like screen-recording artifacts, social media overlays on top of the match, or blurred logos.
        
        Return the result in JSON format with keys: 
        'is_infringing' (boolean), 
        'confidence' (0-1), 
        'broadcaster_logo', 
        'event_details', 
        'analysis_notes'.
        """
        
        response = model.generate_content([prompt, img])
        # Clean the response text to ensure valid JSON
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

def generate_risk_summary(incident_data):
    """
    Generates a high-level executive summary of a detection incident.
    """
    if not model:
        return "AI Summary unavailable (API Key missing)."

    try:
        prompt = f"""
        Summarize this sports IP infringement incident for a security dashboard.
        Incident Data: {json.dumps(incident_data)}
        
        Focus on:
        - The scale of the leak (views/likes).
        - The platform (TikTok, Instagram, etc.).
        - The specific IP being violated.
        - A recommended enforcement action.
        
        Keep it concise and professional (2-3 sentences).
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def draft_dmca_notice(incident_data):
    """
    Drafts a professional DMCA takedown notice.
    """
    if not model:
        return "DMCA drafting unavailable."

    try:
        prompt = f"""
        Draft a professional DMCA Takedown Notice for the following incident:
        {json.dumps(incident_data)}
        
        Include:
        - Clear identification of the copyrighted work (Sports Broadcast).
        - Identification of the infringing material (URL).
        - Standard legal language (good faith belief, accuracy under penalty of perjury).
        - A placeholder for the signature.
        
        Format it as a formal letter.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error drafting DMCA: {str(e)}"
