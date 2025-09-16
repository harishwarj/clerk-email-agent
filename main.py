import os
import smtplib
from email.message import EmailMessage
from fastapi import FastAPI, Form, File, UploadFile
from pydantic import EmailStr
from dotenv import load_dotenv
import pypdf
import google.generativeai as genai
import io
import json

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY must be set in the .env file")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') 

app = FastAPI()

async def generate_email_content_from_pdf(pdf_content: bytes) -> dict:
    """
    Extracts text from a PDF and uses the Gemini AI to generate a subject and body.
    """
    print("Extracting text from PDF...")
    reader = pypdf.PdfReader(io.BytesIO(pdf_content))
    pdf_text = ""
    for page in reader.pages:
        pdf_text += page.extract_text()

    print("Sending PDF text to AI for analysis...")
    prompt = f"""
    You are a helpful paralegal assistant. Your task is to draft an email based on the content of an OPRA request PDF.
    
    Analyze the following text extracted from an OPRA request PDF:
    ---
    {pdf_text}
    ---
    
    Based on the text, identify the township or municipality being contacted (e.g., "Willingboro Township").
    
    Now, generate a JSON object with two keys: "subject" and "body".
    - The "subject" must be "OPRA Request: [Township Name]".
    - The "body" must be a polite, professional email that references the attached OPRA request.
    
    Your entire response must be only the JSON object.
    """
    
    response = await model.generate_content_async(prompt)
    
    ai_response_text = response.text.strip().replace('```json', '').replace('```', '')
    return json.loads(ai_response_text)


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

@app.post("/generate-and-send-opra/")
async def trigger_ai_agent(
    clerk_email: EmailStr = Form(...),
    file: UploadFile = File(...)
):
    """
    Receives a clerk's email and PDF, uses AI to generate content, then sends the email.
    """
    pdf_content = await file.read()
    
    email_content = await generate_email_content_from_pdf(pdf_content)
    
    result = send_opra_email(
        clerk_email,
        email_content["subject"],
        email_content["body"],
        pdf_content,
        file.filename
    )
    return result