
        
        

# internal-sheduler-server\Internal-server\Modules\send_email.py
import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../', "../", "../", 'Keys', 'env.env'))

diretorio_script = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
os.makedirs(os.path.join(diretorio_script, '../', "../", "../", 'Logs'), exist_ok=True)
file_handler = logging.FileHandler(os.path.join(diretorio_script, '../', "../", "../", 'Logs', 'send_email.log'))
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__),
    "../", "../", "../",
    "Keys", 
    "keys.env"
    ))

def SendEmail(
    appname="Media Cuts Studio",
    Subject="Assunto do email",
    body="email a ser enviado",
    user_email_origin="example@gmail.com",
    SMTP_ADM=os.getenv("SMTP_USER"),
    SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
    SMTP_HOST=os.getenv("SMTP_HOST"),
    SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
    use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
    ):
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as SMTP_server:
        SMTP_server.connect(SMTP_HOST, SMTP_PORT)
        if use_tls:
            SMTP_server.starttls()
        SMTP_server.login(SMTP_ADM, SMTP_PASSWORD)
        MIME_server = MIMEMultipart()
        MIME_server['From'] = f"{appname} <{SMTP_ADM}>"
        MIME_server['To'] = user_email_origin
        try:    
            MIME_server['Subject'] = Subject
            MIME_server.attach(MIMEText(body, "plain"))
            SMTP_server.sendmail(SMTP_ADM, user_email_origin, MIME_server.as_string()) 
            logger.info(f"Email  enviado com sucesso!")
            SMTP_server.quit()
        except Exception as eerrorsendemail:
            logger.warning(f"erro ao enviar o email de sinalizacao de erro {eerrorsendemail}")
