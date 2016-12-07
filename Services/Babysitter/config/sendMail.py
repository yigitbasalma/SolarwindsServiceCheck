#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
import ConfigParser
import logMaster


class Mail(object):
    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read("/Services/CouchWatcher/config/config.cfg")
        self.email = config.get("mail", "account")
        self.password = config.get("mail", "password")
        self.server = config.get("mail", "server")
        self.port = config.get("mail", "port")
        session = smtplib.SMTP(self.server, self.port)
        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(self.email, self.password)
        self.session = session
        self.logger = logMaster.Logger()
        self.service = "Mail Sender"

    def send_message(self, subject, body, mailfrom, mailto):
        self.mailto = mailto
        self.mailfrom = mailfrom
        headers = [
            "From: " + self.mailfrom,
            "Subject: " + subject,
            "To: " + self.mailto]
        headers = "\r\n".join(headers)
        try:
            self.session.sendmail(
                self.email,
                self.mailto,
                headers + "\r\n\r\n" + body)
            log = "{0} Adresine gönderim başarılı.".format(self.mailto)
            self.logger.log_save(self.service, "INFO", log)
            return "True"
        except:
            log = "{0} Adresine gönderim hata ile karşılaştı.".format(self.mailto)
            self.logger.log_save(self.service, "INFO", log)
            return "False"
