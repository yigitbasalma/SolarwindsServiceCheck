#!/usr/bin/env python
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
logger = logMaster.Logger("ElasticsearchWatcher", "/Services/ElasticsearchWatcher/config/config.cfg")
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
                logger.log_save("ElasticsearchWatcher Main Process", "ERROR", msg)
                sys.exit(1)
            config.read("/Services/ElasticsearchWatcher/config/config.cfg")
            try:
                system_list = config.get("env", "system_members").split(",")
            except:
                system_list = [config.get("env", "system_members")]
            for el_server in system_list:
                status = calc.calc(el_server)
                service = "Elastic Search Watcher (%s)" % el_server
                if status[0]:
                    pass
                else:
                    db.write("UPDATE {0} SET STATUS='Down' WHERE HOSYNAME='{1}'".format(status[2], status[1]))
                    msg = "'{0}' isimli queue ulaşılamaz durumda.Lütfen kontrol ediniz.".format(status[1])
                    logger.log_save(service, "ERROR", msg)
            time.sleep(30)
    except KeyboardInterrupt:
        print "\n\tScript sonlandırıldı.Görüşmek Üzere =)\n"
        sys.exit(0)
