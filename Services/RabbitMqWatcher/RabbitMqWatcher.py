#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import sys
sys.path.insert(0, "/Services/Babysitter/config")

import db
import logMaster
import config.sourceCalc as sourceCalc
import ConfigParser
import time

from subprocess import Popen, PIPE

# ConfigParser object create
config = ConfigParser.ConfigParser()
# logMaster object create
logger = logMaster.Logger("RabbitMqWatcher", "/Services/RabbitMqWatcher/config/config.cfg")
# sourceCalc object create
calc = sourceCalc.Calculate()
# Db object create
db = db.Db()

if __name__ == "__main__":
    try:
        while True:
            parent_control = "ps -ef | grep Babysitter.py | grep -v grep"
            pc = Popen(parent_control, shell=True, stderr=PIPE, stdout=PIPE)
            pc.communicate()[0]
            if pc.returncode != 0:
                msg = "Uygulamayı çalıştırmak için Babysitter.py scriptini çalıştırınız."
                logger.log_save("RabbitMqWatcher Main Process", "ERROR", msg)
                sys.exit(1)
            config.read("/Services/RabbitMqWatcher/config/config.cfg")
            system_list = config.get("env", "system_members").split(",")
            for rb_server in system_list:
                service = "RabbitMqWatcher (%s)" % rb_server
                if calc.calc(rb_server):
                    config.read("/Services/RabbitMqWatcher/config/config.cfg")
                    server_table = config.get(rb_server, "table")
                    clusterOnDb = [i[0] for i in db.readt("SELECT HOSTNAME FROM {0}_nodes".format(server_table))]
                    queuesOnDb = [i[0] for i in db.readt("SELECT QUEUENAME FROM {0}_queues".format(server_table))]
                    try:
                        clusterReel = ["rabbit@{0}".format(i.split(".")[0]) for i in
                                       config.get(rb_server, "allservers").split(",")]
                        for i in clusterOnDb:
                            if i not in clusterReel:
                                db.write(
                                    "UPDATE {0}_nodes SET STATUS='Down', CLUSTERMEMBERSHIP='None' WHERE HOSTNAME='{1}'".format(
                                        server_table, i))
                                msg = "'{0}' hostname / IP rabbitmq_nodes sunucunuza erişilemiyor.Lütfen kontrol ediniz.".format(
                                    i)
                                logger.log_save(service, "ERROR", msg)
                    except:
                        pass
                    try:
                        queuesReel = [i for i in config.get(rb_server, "queuenames").split(",")]
                        for i in queuesOnDb:
                            if i not in queuesReel:
                                db.write(
                                    "UPDATE {0}_queues SET STATUS='Offline', STATE='None' WHERE QUEUENAME='{1}'".format(
                                        server_table, i))
                                msg = "'{0}' isimli queue ulaşılamaz durumda.Lütfen kontrol ediniz.".format(i)
                                logger.log_save(service, "ERROR", msg)
                    except:
                        pass
            time.sleep(30)
    except KeyboardInterrupt:
        print "\n\tScript sonlandırıldı.Görüşmek Üzere =)\n"
        sys.exit(0)
