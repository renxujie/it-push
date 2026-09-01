import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os

class EmailSender:
    def __init__(self):
        self.sender_email = os.environ.get("SENDER_EMAIL")
        self.sender_password = os.environ.get("SENDER_PASSWORD")
        self.receiver_email = os.environ.get("RECEIVER_EMAIL")
        self.smtp_server = "smtp.163.com"
        self.smtp_port = 465
    
    def send_html_email(self, subject, html_content):
        """发送HTML格式邮件"""
        if not all([self.sender_email, self.sender_password, self.receiver_email]):
            print("邮箱配置不完整，无法发送邮件")
            return False
        
        message = MIMEText(html_content, "html", "utf-8")
        message["From"] = Header(f"巨潮资讯速递<{self.sender_email}>", "utf-8")
        message["To"] = Header(self.receiver_email, "utf-8")
        message["Subject"] = Header(subject, "utf-8")
        
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.receiver_email, message.as_string())
            print("邮件发送成功")
            return True
        except Exception as e:
            print(f"邮件发送失败: {str(e)}")
            return False
