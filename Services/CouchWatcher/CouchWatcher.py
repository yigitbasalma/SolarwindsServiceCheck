#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import sys
sys.path.insert(0, "/Services/Babysitter/config")

import db
import logMaster
import config.sourceCalc as sourceCalc
import ConfigParser
import errorMessageTemplate
import time

from subprocess import Popen, PIPE

# ConfigParser object create
config = ConfigParser.ConfigParser()
# logMaster object create
logger = logMaster.Logger("CouchWatcher", "/Services/CouchWatcher/config/config.cfg")
# sourceCalc object create
calc = sourceCalc.Calculate()
# errorMessageTemplate object create
err_msg = errorMessageTemplate.Message()
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
                logger.log_save("CouchWatcher Main Process", "ERROR", msg)
                sys.exit(1)
            config.read("/Services/CouchWatcher/config/config.cfg")
            system_list = config.get("env", "system_members").split(",")
            for cb_server in system_list:
                service = "CouchhWatcher (%s)" % cb_server
                if calc.calc(cb_server):
                    config.read("/Services/CouchWatcher/config/config.cfg")
                    server_table = config.get(cb_server, "table")
                    cluster_on_db = [i[0] for i in db.readt("SELECT HOSTNAME FROM %s" % server_table)]
                    cluster_reel = config.get(cb_server, "allservers").split(",")
                    for i in cluster_on_db:
                        if i not in cluster_reel:
                            db.write(
                                "UPDATE {0} SET STATUS='Down', CLUSTERMEMBERSHIP='None' WHERE HOSTNAME='{1}'".format(
                                    server_table, i))
                            msg = "'{0}' hostname / IP couchbase sunucunuza erişilemiyor.Lütfen kontrol ediniz.".format(
                                i)
                            logger.log_save(service, "ERROR", msg)
            time.sleep(30)
    except KeyboardInterrupt:
        print "\n\tScript sonlandırıldı.Görüşmek Üzere =)\n"
        sys.exit(0)
