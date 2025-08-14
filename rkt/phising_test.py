import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import sys
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phishing_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

class PhishingTestSuite:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.phishing_templates = [
            {
                'subject': 'Acil Şifre Güncelleme Gerekiyor',
                'body': """Sayın {name},\n\nHesabınızın güvenliği için şifrenizi acilen güncellemeniz gerekmektedir. 
                Lütfen aşağıdaki bağlantıya tıklayarak şifrenizi güncelleyin:\n\n{link}\n\nSaygılar,\nIT Ekibi"""
            },
            {
                'subject': 'Hesap Doğrulama Bildirimi',
                'body': """Merhaba {name},\n\nHesabınızın doğrulama işlemi tamamlanmadı. 
                Doğrulamayı tamamlamak için lütfen aşağıdaki bağlantıya tıklayın:\n\n{link}\n\nTeşekkürler,\nDestek Ekibi"""
            }
        ]

    def generate_random_string(self, length=10):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def create_phishing_email(self, recipient_name, recipient_email):
        template = random.choice(self.phishing_templates)
        fake_link = f"http://test-{self.generate_random_string()}.safe-login.com"
        
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = template['subject']
        
        body = template['body'].format(name=recipient_name, link=fake_link)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        return msg, fake_link

    def send_email(self, recipient_name, recipient_email):
        try:
            msg, fake_link = self.create_phishing_email(recipient_name, recipient_email)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                logger.info(f"Phishing test email sent to {recipient_email}. Fake link: {fake_link}")
                
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Phishing Test Suite for Employee Awareness')
    parser.add_argument('--smtp-server', required=True, help='SMTP server address')
    parser.add_argument('--smtp-port', type=int, required=True, help='SMTP server port')
    parser.add_argument('--sender-email', required=True, help='Sender email address')
    parser.add_argument('--sender-password', required=True, help='Sender email password')
    parser.add_argument('--recipient-list', required=True, help='File containing recipient names and emails')
    
    args = parser.parse_args()
    
    phishing_test = PhishingTestSuite(
        args.smtp_server,
        args.smtp_port,
        args.sender_email,
        args.sender_password
    )
    
    try:
        with open(args.recipient_list, 'r', encoding='utf-8') as file:
            for line in file:
                name, email = line.strip().split(',')
                phishing_test.send_email(name, email)
    except FileNotFoundError:
        logger.error(f"Recipient list file {args.recipient_list} not found")
    except Exception as e:
        logger.error(f"Error processing recipient list: {str(e)}")

if __name__ == "__main__":
    main()