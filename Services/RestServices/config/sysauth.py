#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.insert(0, "/Services/Babysitter/config")

import hashlib
import ConfigParser
import datetime
import db
import logMaster
import sqlite3


class Auth(object):
    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read('/Services/RestServices/config/config.cfg')
        self.restuser = config.get('auth', 'username')
        self.restpass = config.get('auth', 'password')
        self.db = db.Db()
        self.logger = logMaster.Logger("RestServices", "/Services/RestServices/config/config.cfg")

    def validate(self, username, password, ip, url):
        password = hashlib.sha512(password).hexdigest()
        if self.db.count("SELECT IP FROM rest_badlogin WHERE IP='{0}'".format(ip)) == 3:
            msg = "IP adresiniz kalici olarak bloklanmistir.Lutfen sistem yoneticinize basvurunuz."
            return msg
        else:
            if self.restuser == username and self.restpass == password:
                return True
            elif self.restuser != username:
                msg = 'Kullanici adi sistemde yer almiyor.{0}'.format(self.__checkip(ip, url))
                return msg
            elif password != self.restpass:
                msg = 'Sifrenizi hatali girdiniz.{0}'.format(self.__checkip(ip, url))
                return msg
            elif username is None or password is None:
                msg = 'Kullanici adi ve sifre gereklidir.{0}'.format(self.__checkip(ip, url))
                return msg

    def __blockip(self, ip, url):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = 'INSERT INTO rest_badlogin (IP,TIMESTAMP) VALUES ("{0}","{1}")'.format(ip, timestamp)
        try:
            self.db.write(query)
        except sqlite3.OperationalError:
            create_table = "CREATE TABLE rest_badlogin(IP VARCHAR(200), TIMESTAMP DATETIME)"
            self.db.write(create_table)
        finally:
            self.db.write(query)
        cnt = self.db.count("SELECT IP FROM rest_badlogin WHERE IP='{0}'".format(ip))
        log = '{0} Numarası, {1} adresine gitmek isterken {2}. kez bloklandı.'.format(ip, url, cnt)
        self.logger.log_save('AUTHMASTER', 'INFO', log)

    def __checkip(self, ip, url):
        count = self.db.count("SELECT IP FROM rest_badlogin WHERE IP='{0}'".format(ip))
        if count == 0:
            self.__blockip(ip, url)
            msg = "IP numaraniz ilk kez bloklandi.2 kere daha yalis giris yaparsaniz IP adresiniz kalici bloklanacak."
            return msg
        elif count < 3 or count > 0:
            self.__blockip(ip, url)
            msg = "IP numaraniz {0} kez bloklandi.{1} kere daha yalis giris yaparsaniz IP adresiniz kalici bloklanacak.".format(
                count, 3 - count)
            return msg
