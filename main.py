import os
import smtplib
from email.message import EmailMessage
from fastapi import FastAPI, Form, File, UploadFile
from pydantic import EmailStr
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# --- 1. Configure Services ---
# (Gemini AI configuration has been removed)

# Create the FastAPI application
app = FastAPI()

# --- 2. Email Sending Function (no changes here) ---
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
        print(f"Successfully sent email to {recipient_email}")
        return {"status": "success", "message": f"Email sent to {recipient_email}"}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "error", "message": str(e)}

# --- 3. UPDATED API Endpoint (Now uses a preset template) ---
@app.post("/generate-and-send-opra/")
async def trigger_agent(
    clerk_email: EmailStr = Form(...),
    county: str = Form(...),
    municipality: str = Form(...),
    clerk_name: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Receives clerk details and a PDF, uses a preset template, then sends the email.
    """
    pdf_content = await file.read()
    
    # --- Create the email content from a fixed template ---
    subject = f"OPRA Request: Accident Reports for {municipality}"
    
    body = (
        f"Dear {clerk_name},\n\n"
        f"Please find our attached Open Public Records Act (OPRA) request for accident reports that occurred in {municipality}, {county}.\n\n"
        "Kindly advise if you prefer to receive these requests via email or if you now use an online portal. If you use a portal, please reply with the direct link.\n\n"
        "Thank you for your time and assistance.\n\n"
        "Sincerely,\n"
        "Nima Ameri, Esq.\n"
        "Ameri Law Firm"
    )

    # --- Send the email ---
    result = send_opra_email(
        clerk_email,
        subject,
        body,
        pdf_content,
        file.filename
    )
    return result

