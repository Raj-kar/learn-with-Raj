from random import randint
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from keys import email, password


class SendOTP:
    def __init__(self, user_name, user_email, otp):
        self.user_name = user_name
        self.user_email = user_email
        self.otp = otp
        
        # Create message container - the correct MIME type is multipart/alternative.
        self.msg = MIMEMultipart('alternative')
        self.msg['Subject'] = "Verify Email for Registration"
        self.today = date.today().strftime("%B %d, %Y")

    def register_msgBody(self):
        # Create the body of the message (a plain-text and an HTML version).
        self.html = f"""\
        <html>
          <body style="background-color: #ebecf0;">
            <div style="background-color:#ebecf0; padding:10px 20px;">
                <div style="text-align: center;">
                    <h2 style="font-family:Georgia, 'Times New Roman', Times, serif;color:#2f2187;">
                        Welcome to <a href="https://www.python.org/">PyWorld</a>
                    </h2>
                    <img style="height: 250px;width:400px" src="https://i.ibb.co/2cpDmmj/undraw-firmfare.png"
                alt="welcome-image">
                    <p>To complete the process of Registration, you need to active your account.</p>
                    <h3>Your OTP is <a href="#"><em style="color: #6609df;">{self.otp}</em></a>.</h3> <br><br>
                    <p>If you didn't intend this, just ignore this message</p>


                    <p><a href="https://code-with-raj.herokuapp.com/">Visit</a> my website, for more awesome contents.</p>
                </div>
                <code>
                    - Python With Raj <br>
                    - <a href="https://raj-cv.herokuapp.com">Raj</a> <br>
                    - {self.today}
                </code>
            </div>
        </body>
        </html>
        """
        self.config_msg()

    def forgot_password_msgBody(self):
        self.html = f"""\
                <html>
                  <head></head>
                  <body>
                    <p>We received a request to change <em>{self.user_name}</em> account password.</p>
                    <p>To complete the process you must verify your account.</p>
                    <h3>Your OTP is <a href="#"><em>{self.otp}</em></a>.</h3> <br><br>
                    <p>If you didn't intend this, just ignore this message</p>

                    <p><a href="https://pyraj.herokuapp.com/">Visit</a> our website, for more awesome contents.</p>
                    <code>
                        - PyRaj <br>
                        - Raj <br>
                        - {self.today}
                    </code>
                </body>
                </html>
                """
        self.config_msg()

    def config_msg(self):
        # Record the MIME types of both parts - text/plain and text/html.
        self.part2 = MIMEText(self.html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        self.msg.attach(self.part2)

    def send_OTP(self):
        with smtplib.SMTP("smtp.gmail.com") as connection:
            # print("start SMPTLIB")
            connection.starttls()
            connection.login(user=email, password=password)
            # print("login successful")
            connection.sendmail(from_addr=email, to_addrs={self.user_email},
                                msg=self.msg.as_string())
            # print("send email")