import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str = None
) -> bool:
    """
    Send email via SMTP.
    Returns True if successful, False otherwise.
    """
    # Check if SMTP is configured
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        logger.warning("SMTP credentials not configured. Email not sent.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = to_email

        # Add text and HTML parts
        if text_body:
            part1 = MIMEText(text_body, 'plain')
            msg.attach(part1)
        
        part2 = MIMEText(html_body, 'html')
        msg.attach(part2)

        # Connect to SMTP server
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_verification_code_email(email: str, code: str) -> bool:
    """Send verification code email"""
    subject = "Your Scapegis verification code"
    
    # HTML version
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .code-box {{ 
                background: #f4f4f4; 
                padding: 20px; 
                text-align: center; 
                font-size: 32px; 
                font-weight: bold; 
                letter-spacing: 5px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Enter this temporary verification code to continue:</h2>
            
            <div class="code-box">{code}</div>
            
            <p>This code will expire in 10 minutes.</p>
            
            <p>If you didn't request this code, please ignore this email.</p>
            
            <p>Best,<br>The Scapegis App team</p>
            
            <div class="footer">
                This email was sent from a notification-only address that cannot accept incoming email. 
                Please do not reply to this message.
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
Enter this temporary verification code to continue:

{code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best,
The Scapegis App team

---
This email was sent from a notification-only address that cannot accept incoming email.
Please do not reply to this message.
    """
    
    return send_email(email, subject, html_body, text_body)


def send_magic_link_email(email: str, token: str) -> bool:
    """Send magic link email for admin login"""
    subject = "Your Scapegis admin login link"
    
    magic_link = f"http://localhost:3000/admin/verify?token={token}"
    
    # HTML version
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                display: inline-block;
                background: #007bff;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Admin Login Request</h2>
            
            <p>Click the button below to log in to your admin account:</p>
            
            <a href="{magic_link}" class="button">Log in to Scapegis</a>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #007bff;">{magic_link}</p>
            
            <p>This link will expire in 10 minutes.</p>
            
            <p>If you didn't request this link, please ignore this email.</p>
            
            <p>Best,<br>The Scapegis App team</p>
            
            <div class="footer">
                For security reasons, this link can only be used once.
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
Admin Login Request

Click the link below to log in to your admin account:

{magic_link}

This link will expire in 10 minutes.

If you didn't request this link, please ignore this email.

Best,
The Scapegis App team

---
For security reasons, this link can only be used once.
    """
    
    return send_email(email, subject, html_body, text_body)
