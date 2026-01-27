import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

class OTPService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.otp_storage = {}
    
    def generate_otp(self):
        return str(random.randint(100000, 999999))
    
    def send_otp(self, email):
        otp = self.generate_otp()
        
        self.otp_storage[email] = {
            'otp': otp,
            'expires_at': time.time() + 300,
            'attempts': 0
        }
        
        if self.email_user and self.email_password:
            try:
                msg = MIMEMultipart()
                msg['From'] = self.email_user
                msg['To'] = email
                msg['Subject'] = "Ledgerit - Email Verification Code"
                
                body = f"""
                <html>
                <body>
                    <h2>Ledgerit Email Verification</h2>
                    <p>Your verification code is: <strong>{otp}</strong></p>
                    <p>This code will expire in 5 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(body, 'html'))
                
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                server.quit()
                
                return True, "OTP sent to your email"
            except Exception as e:
                print(f"Email error: {e}")
                print(f"DEV MODE - OTP for {email}: {otp}")
                return True, f"OTP sent (Dev mode: {otp})"
        else:
            print(f"DEV MODE - OTP for {email}: {otp}")
            return True, f"OTP sent (Dev mode: {otp})"
    
    def verify_otp(self, email, otp):
        if email not in self.otp_storage:
            return False, "OTP not found or expired"
        
        stored_data = self.otp_storage[email]
        
        if time.time() > stored_data['expires_at']:
            del self.otp_storage[email]
            return False, "OTP expired"
        
        if stored_data['attempts'] >= 3:
            del self.otp_storage[email]
            return False, "Too many attempts"
        
        if stored_data['otp'] == otp:
            del self.otp_storage[email]
            return True, "OTP verified successfully"
        else:
            stored_data['attempts'] += 1
            return False, "Invalid OTP"

otp_service = OTPService()