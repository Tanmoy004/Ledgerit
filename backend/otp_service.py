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
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8" />
                    <title>Ledgerit Email Verification</title>
                </head>
                <body style="margin:0; padding:0; background-color:#f4f4f4; font-family: Arial, Helvetica, sans-serif;">
                    <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4; padding:20px;">
                    <tr>
                        <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:6px; overflow:hidden;">

                            <!-- Header -->
                           <tr>
  <td style="background-color:#232f3e; padding:16px 24px;">
    <table cellpadding="0" cellspacing="0" width="100%">
      <tr>
        <td align="left" style="vertical-align:middle;">
          <img
            src="https://drive.google.com/file/d/1k2esEMDatclZNjj8d6ug--t_PoEWJsJI/view?usp=sharing"
            alt="Ledgerit"
            width="120"
            style="display:block; border:0; outline:none; text-decoration:none;"
          />
        </td>
      </tr>
    </table>
  </td>
</tr>

                            <!-- Body -->
                            <tr>
                            <td style="padding:24px; color:#111111;">
                                <p style="font-size:16px; margin:0 0 16px;">
                                Hello,
                                </p>

                                <p style="font-size:16px; margin:0 0 16px;">
                                We received a request to verify your email address for your Ledgerit account.
                                </p>

                                <p style="font-size:16px; margin:0 0 8px;">
                                Your verification code is:
                                </p>

                                <!-- OTP Box -->
                                <div style="
                                font-size:28px;
                                font-weight:bold;
                                letter-spacing:6px;
                                color:#111111;
                                background-color:#f1f3f3;
                                padding:12px 16px;
                                display:inline-block;
                                border-radius:4px;
                                margin:12px 0 20px;
                                ">
                                {otp}
                                </div>

                                <p style="font-size:14px; color:#555555; margin:0 0 16px;">
                                This code will expire in <strong>5 minutes</strong>.
                                </p>

                                <p style="font-size:14px; color:#555555; margin:0;">
                                If you did not request this code, please ignore this email.
                                </p>
                            </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                            <td style="padding:16px 24px; background-color:#f8f8f8; font-size:12px; color:#777777;">
                                <p style="margin:0;">
                                © 2026 Ledgerit. All rights reserved.
                                </p>
                            </td>
                            </tr>

                        </table>
                        </td>
                    </tr>
                    </table>
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