# main.py

import os
import smtplib
from email.message import EmailMessage
from fastapi import FastAPI, Form, File, UploadFile
from pydantic import EmailStr
from dotenv import load_dotenv
import google.generativeai as genai
import json

# Load environment variables from .env file
load_dotenv()

# --- 1. Configure Services ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY must be set in the .env file")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') 

# Create the FastAPI application
app = FastAPI()


# --- 2. NEW AI Function: Drafts email using provided context ---
async def generate_email_content_with_ai(
    county: str,
    municipality: str,
    clerk_name: str
) -> dict:
    """
    Uses the Gemini AI to generate a subject and body based on provided details.
    """
    print(f"Sending details to AI for {municipality}, {county}...")
    
    # A more focused prompt for the AI to draft the email
    prompt = f"""
    You are a helpful paralegal assistant for the Ameri Law Firm.
    Your task is to draft a polite and professional OPRA request email.

    Use the following information:
    - County: "{county}"
    - Municipality: "{municipality}"
    - Clerk's Name: "{clerk_name}"

    Generate a JSON object with two keys: "subject" and "body".
    - The "subject" should be "OPRA Request: Accident Reports for {municipality}".
    - The "body" should be addressed to the clerk by name and mention the municipality. It should state that the OPRA request form is attached.

    Your entire response must be only the JSON object.
    """
    
    response = await model.generate_content_async(prompt)
    ai_response_text = response.text.strip().replace('```json', '').replace('```', '')
    return json.loads(ai_response_text)


# --- 3. Email Sending Function (no changes here) ---
def send_opra_email(
    recipient_email: str, 
    subject: str,
    body: str,
    pdf_content: bytes,
    pdf_filename: str
):
    """Constructs and sends the email using the generated content."""
    
    sender_email = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("APP_PASSWORD")

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = f"Ameri Law Firm <{sender_email}>"
    msg["To"] = recipient_email
    msg.add_attachment(pdf_content, maintype='application', subtype='pdf', filename=pdf_filename)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print(f"Successfully sent AI-generated email to {recipient_email}")
        return {"status": "success", "message": f"AI-generated email sent to {recipient_email}"}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "error", "message": str(e)}

# --- 4. UPDATED API Endpoint ---
@app.post("/generate-and-send-opra/")
async def trigger_ai_agent(
    clerk_email: EmailStr = Form(...),
    county: str = Form(...),
    municipality: str = Form(...),
    clerk_name: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Receives clerk details and a PDF, uses AI to generate content, then sends the email.
    """
    pdf_content = await file.read()
    
    
    email_content = await generate_email_content_with_ai(county, municipality, clerk_name)
    
   
    result = send_opra_email(
        clerk_email,
        email_content["subject"],
        email_content["body"],
        pdf_content,
        file.filename
    )
    return result