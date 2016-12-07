#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import datetime
import logMaster


class Db(object):
    def __init__(self):
        self.conn = mdb.connect(host="localhost", user="Username", passwd="PassWord", db="db")
        self.vt = self.conn.cursor()
        self.scname = "Database"

    def write(self, query):
        self.vt.execute(query)
        self.conn.commit()
        return True

    def count(self, query):
        self.vt.execute(query)
        return self.vt.rowcount

    def readt(self, query):
        self.vt.execute(query)
        return self.vt.fetchall()

    def performance_and_repair(self, logger, engine_change_for_auto_recpair=False, optimize=False, period="w"):
        if logger is None:
            raise ValueError("Logger sınıfı boş bırakılmamlıdır.")
        available_periods = {
            "d": (1, "Daily"),
            "w": (7, "Weekly"),
            "m": (30, "Monthly"),
            "y": (365, "Yearly")
        }
        if period not in available_periods:
            raise ValueError("Tanımsız kontrol periodu.Kullnılabilir periodlar: {0}.".\
                             format(", ".join(["'{0}'({1})".format(k, v[1]) for k, v in available_periods.iteritems()])))
        try:
            last_execute = self.readt("SELECT VAL FROM options WHERE OPTION='last_execute_performance_and_repair'")[0][0]
            next_execute = datetime.datetime.now() - datetime.timedelta(days=int(available_periods[period][0]))
            if datetime.datetime.strptime(last_execute, "%Y-%m-%d %H:%M:%S") > next_execute:
                return True
        except mdb.ProgrammingError:
            self.write("CREATE TABLE options(OPTION VARCHAR(500) PRIMARY KEY, VAL VARCHAR(1000))")
        table_engines = {i[0]: i[1] for i in self.readt("SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES\
                        WHERE  TABLE_SCHEMA = 'sensorMetric';")}
        auto_repairable_engine = ["MyISAM"]
        table_names = [i[0] for i in self.readt("SHOW TABLES")]
        must_repair_table = {}
        for table in table_names:
            for i in self.readt("CHECK TABLE {0}".format(table)):
                if i[2] in ["error", "warning"]:
                    must_repair_table[i[0]] = i[3]
        if len(must_repair_table) > 0:
            msg = "Veri tabanında yer alan bazı tablolarda hatalar bulundu.Mutlaka tamir edilmeli.Tablo isimleri ve bulunan hatalar ; {0} .\
                  ".format(", ".join(["{0} : {1}".format(k.split(".")[1], v) for k, v in must_repair_table.iteritems()]))
            logger.log_save(self.scname, "WARNING", msg)
            if not engine_change_for_auto_recpair:
                msg = "Bazı tablolar otomatik tamir etmek için uygun engine'e sahip değil.Lütfen 'engine_change_for_auto_recpair' parametresini etkinleştirin.Otomatik tamir edilemeyen tablolar ; {0} .\
                        ".format(
                    ", ".join([k for k, v in table_engines.iteritems() if v not in auto_repairable_engine]))
                logger.log_save(self.scname, "ERROR", msg)
                if not optimize:
                    return True
            msg = "Tabloların onarılması işlemine başlanıyor.Engine değişikliği yapılacak tablolar ; {0} .Onarılacak tablolar ; {1}\
                  ".format(", ".join([k for k, v in table_engines.iteritems() if v not in auto_repairable_engine]),\
                           ", ".join([k.split(".")[1] for k, v in must_repair_table.iteritems()]))
            logger.log_save(self.scname, "INFO", msg)
            result_repair = {}
            for k, v in must_repair_table.iteritems():
                self.write("ALTER TABLE {0} ENGINE={1}".format(k, auto_repairable_engine))
                result = self.readt("REPAIR TABLE {0}".format(k))
                result_repair[k] = result[0][3] if len(result) == 1 else result[-1][3]
            msg = "Onarım işlemi bitirildi.Sonuçlar ; {0} .".format(", ".join(["{0} : {1}".format(k.split(".")[1], v) for k, v in result_repair.iteritems()]))
            logger.log_save(self.scname, "INFO", msg)
        if optimize:
            msg = "Tüm tablolar çalışır durumda ve sağlıklı.Optimizasyon işlemine başlanıyor."
            logger.log_save(self.scname, "INFO", msg)
            result_optimize = {}
            for table in table_names:
                result = self.readt("OPTIMIZE TABLE {0}".format(table))
                result_optimize[table] = result[0][3] if len(result) == 1 else result[-1][3]
            msg = "Optimizasyon işlemi bitirildi.Sonuçlar ; {0} .".format(
                ", ".join(["{0} : {1}".format(k, v) for k, v in result_optimize.iteritems()]))
            logger.log_save(self.scname, "INFO", msg)
        timestamp = datetime.datetime.now()
        try:
            self.write("INSERT INTO options values('last_execute_performance_and_repair', '{0}')".format(timestamp))
        except mdb.IntegrityError:
            self.write("UPDATE options SET last_execute_performance_and_repair='{0}'".format(timestamp))
        self.conn.commit()

if __name__ == "__main__":
    db = Db()
    watcher = "Babysitter"
    logger = logMaster.Logger(watcher, "/Services/Babysitter/config/config.cfg")
    db.performance_and_repair(logger, optimize=True)
