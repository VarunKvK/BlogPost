from flask import request
import pandas as pd
import os
import smtplib

FILE = "D:/VarunCodes/Python/Flask/BlogPost/User_Email.csv"
EMAIL = "testifytest3@gmail.com"
PASSWORD = "ioec iaba ahbx dsks"


class Email:
    def __init__(self):
        self.email_input = None

    def email_notifier(self):
        email = request.form.get("useremail")
        self.email_input = email
        if os.path.exists(FILE):
            df = pd.read_csv(FILE)
            new_data = pd.DataFrame({"Email": [self.email_input]})
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(FILE, index=False)
            self.email_sender()

        else:
            df = pd.DataFrame({"Email": [self.email_input]})
            df.to_csv(FILE, index=False)

    def email_sender(self):
        df = pd.read_csv(FILE)
        name = df['Email'].str.split('@').str[0]

        for index, row in df.iterrows():
            email = row['Email']
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=EMAIL, password=PASSWORD)
                connection.sendmail(from_addr=EMAIL, to_addrs=email,
                                    msg=f"Subject:Thank you for Subscribing to our NewsLetter.\n\n Hello {name.iloc[index]}, thank you for subscribing to our newsletter. ")
            print("sent")

