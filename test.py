from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import smtplib
import time
from utils.words_or_other import symbols, exceptions

def test_key():
    result = ''
    for _ in range(15):
        r = random.randint(0, len(symbols) - 1)
        if _ == 1 and symbols[r] in exceptions:
            return test_key()
        result += symbols[r]
    return result

print(test_key())
    
# p = "tbdx vmcw tzkt kyky"
# smtp_server = "smtp.gmail.com"
# smtp_port = 587
# smtp_user = "defensiv2010@gmail.com"
# smtp_password = p


# sender_email = "ammo@gmail.com"
# receiver_email = "defensiv2010@gmail.com"

# message = MIMEMultipart()
# message['From'] = sender_email
# message['To'] = receiver_email
# message['Subject'] = 'TEST FROM EMAIL)'

# body = "Привет! Это тестовое письмо, отправленное без сторонних библиотек Python."
# message.attach(MIMEText(body))

# try:
#     server = smtplib.SMTP(smtp_server, smtp_port)
#     server.ehlo()
#     server.starttls()
#     server.ehlo()
#     server.login(smtp_user, smtp_password)
    
#     for i in range(10):
#         server.sendmail(sender_email, receiver_email, message.as_string())
#         print(f'Письмо отправленно {i + 1}')
# except Exception as e:
#     print(f'Ошибка не отправленно: {e}')

# finally:
#     server.quit()