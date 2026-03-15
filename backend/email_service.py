"""
Email Service for Municipal Chatbot
Sends conversation summaries via SMTP
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any, Optional

# Email configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@kitchener.ca")
FROM_NAME = os.getenv("FROM_NAME", "Kitchener City Services")


def is_email_configured() -> bool:
    """Check if email is properly configured"""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_conversation_summary(
    to_email: str,
    user_name: str,
    session_id: str,
    messages: List[Dict[str, Any]],
    started_at: str,
    ended_at: Optional[str] = None
) -> bool:
    """
    Send a conversation summary email to the user.
    
    Args:
        to_email: Recipient email address
        user_name: User's name
        session_id: Session identifier
        messages: List of message dicts with 'role' and 'content'
        started_at: Session start timestamp
        ended_at: Session end timestamp (optional)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not is_email_configured():
        print(f"Email not configured. Would send summary to {to_email}")
        print(f"Session: {session_id}, Messages: {len(messages)}")
        return False
    
    # Build message list for the email
    message_lines = []
    for msg in messages:
        role = "You" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")[:500]  # Truncate long messages
        message_lines.append(f"**{role}:** {content}\n")
    
    messages_html = "".join(
        f'<div class="message"><strong>{("You" if m.get("role") == "user" else "Assistant")}:</strong> {m.get("content", "")[:500]}</div>'
        for m in messages
    )
    
    # Format timestamps
    try:
        start_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        start_str = start_dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        start_str = started_at
    
    end_str = ended_at or "Session still active"
    if end_str != "Session still active":
        try:
            end_dt = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
            end_str = end_dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            pass
    
    # Plain text version
    plain_text = f"""Hello {user_name},

Thank you for using Kitchener City Services Chat. Here's a summary of your conversation:

Session ID: {session_id}
Date: {start_str}
Duration: {end_str}

Questions Asked and Answers Received:
{"-" * 50}
{chr(10).join(message_lines)}

{"-" * 50}
This is an automated message from the City of Kitchener.
For urgent matters, please visit kitchener.ca or call 519-741-2345.
"""
    
    # HTML version
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #006699;">Kitchener City Services - Chat Summary</h2>
        
        <p>Hello {user_name},</p>
        
        <p>Thank you for using our City Services Chat. Here's a summary of your conversation:</p>
        
        <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p><strong>Session ID:</strong> {session_id}</p>
            <p><strong>Date:</strong> {start_str}</p>
            <p><strong>Duration:</strong> {end_str}</p>
        </div>
        
        <h3>Conversation:</h3>
        {messages_html}
        
        <hr style="margin: 20px 0; border: none; border-top: 1px solid #ccc;">
        
        <p style="color: #666; font-size: 12px;">
            This is an automated message from the City of Kitchener.<br>
            For urgent matters, please visit <a href="https://kitchener.ca">kitchener.ca</a> 
            or call 519-741-2345.
        </p>
    </body>
    </html>
    """
    
    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Chat Summary - Kitchener City Services"
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        # Create secure SSL context
        context = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_welcome_email(to_email: str, user_name: str) -> bool:
    """Send a welcome email to new users"""
    if not is_email_configured():
        print(f"Email not configured. Would send welcome to {to_email}")
        return False
    
    plain_text = f"""Hello {user_name},

Welcome to Kitchener City Services Chat!

You can now chat with our AI assistant to get information about:
- Garbage and recycling schedules
- Parking permits and tickets
- Building permits
- Property taxes
- And many other city services

To start a conversation, visit our chat widget and provide your questions.

This is an automated message from the City of Kitchener.
"""
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #006699;">Welcome to Kitchener City Services!</h2>
        
        <p>Hello {user_name},</p>
        
        <p>Welcome to our new Chat service! You can now get instant answers to your questions about city services.</p>
        
        <h3>What you can ask about:</h3>
        <ul>
            <li>Garbage and recycling schedules</li>
            <li>Parking permits and tickets</li>
            <li>Building permits</li>
            <li>Property taxes</li>
            <li>City by-laws</li>
            <li>Contact information</li>
        </ul>
        
        <p>Visit our chat widget to get started!</p>
        
        <hr style="margin: 20px 0; border: none; border-top: 1px solid #ccc;">
        
        <p style="color: #666; font-size: 12px;">
            City of Kitchener<br>
            <a href="https://kitchener.ca">kitchener.ca</a> | 519-741-2345
        </p>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Welcome to Kitchener City Services Chat"
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False


if __name__ == "__main__":
    print(f"Email configured: {is_email_configured()}")
    if is_email_configured():
        print(f"SMTP Host: {SMTP_HOST}:{SMTP_PORT}")
        print(f"From: {FROM_EMAIL}")