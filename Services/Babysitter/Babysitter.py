#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import ConfigParser
import config.logMaster as logMaster
import config.db as db
import config.DesginRestAPI as DesginRestAPI
import requests
import re

from subprocess import PIPE, Popen
from datetime import datetime, timedelta

config = ConfigParser.ConfigParser()
db = db.Db()
creator = DesginRestAPI.RestCreator()
watcher = "Babysitter"
logger = logMaster.Logger(watcher, "/Services/Babysitter/config/config.cfg")


def process_watcher():
    config.read("/Services/Babysitter/config/config.cfg")
    process_names = config.get("env", "script_files").split(",")
    pid = re.compile("[0-9]+")
    for process in process_names:
        controller = "ps -ef | grep \"%s\" | grep -v grep | awk -F \" \" '{print$2}'" % process
        cmd = Popen(controller, shell=True, stderr=PIPE, stdout=PIPE).communicate()[0].strip()
        if not bool(pid.match(cmd)):
            msg = "{0} isimli uygulama down görünüyor.Yeniden açılma işlemi yapılacak.".format(process.split("/")[-1])
            logger.log_save(watcher, "WARNING", msg)
            start_process = "nohup /usr/bin/python {0} > /Services/services.out 2>&1 > /dev/null &".format(process)
            Popen(start_process, shell=True, stdout=PIPE, stderr=PIPE)
            time.sleep(1)
            cmd = Popen(controller, shell=True, stderr=PIPE, stdout=PIPE).communicate()[0].strip()
            if bool(pid.match(cmd)):
                msg = "{0} isimli uygulama açıldı.".format(process.split("/")[-1])
                logger.log_save(watcher, "INFO", msg)
            else:
                msg = "{0} isimli uygulama açılırken hata yaşandı.Lütfen elle çalıştırmayı deneyin. {1}".format(\
                    process.split("/")[-1], cmd)
                logger.log_save(watcher, "ERROR", msg)


def discover_new_endpoints():
    config.read("/Services/Babysitter/config/config.cfg")
    discoverable_list = config.get("rest_creator", "endpoint_names").split(",")
    for system in discoverable_list:
        try:
            config.get(system, "new")
            creator.create_script_file()
            logger.log_save(watcher, "INFO", "'{0}' sistemi icin yeni bir endpoint olusturuldu.".format(system))
            config.remove_option(system, "new")
            with open("/Services/Babysitter/config/config.cfg", "wb") as mainconfig:
                config.write(mainconfig)
        except ConfigParser.NoOptionError:
            pass
    return True


def health_check_restapi():
    config.read("/Services/Babysitter/config/config.cfg")
    ha_url = "http://{0}".format(config.get("env", "ha_url"))
    ha_timeout = int(config.get("env", "ha_timeout"))
    try:
        requests.get(ha_url, timeout=ha_timeout)
        return True
    except requests.exceptions.Timeout:
        logger.log_save(watcher, "ERROR", "RestAPI yeniden ayağa kaldırılıyor.")
        command = "/etc/init.d/solarwinds_services RestServices restart"
        Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        return True


def delete_old_systems_or_servers():
    config.read("/Services/Babysitter/config/config.cfg")
    threshold = datetime.now() - timedelta(hours=int(config.get("env", "error_time_threshold")))
    config_files = config.get("env", "config_files").split(",")
    for sys_config in config_files:
        main_system_name = sys_config.split("/")[2]
        config.read(sys_config)
        system_list = config.get("env", "system_members").split(",")
        for system in system_list:
            if main_system_name == "RabbitMqWatcher":
                table = "{0}_nodes".format(config.get(system, "table"))
            else:
                table = config.get(system, "table")
            counter = 0
            all_servers = db.count("SELECT STATUS FROM {0}".format(table))
            if main_system_name == "ElasticsearchWatcher":
                query = "SELECT HOST_UNIQUE_NAME,LAST_MIDFIED FROM {0} WHERE STATUS='Down'".format(table)
                delete_key = "HOST_UNIQUE_NAME"
            else:
                query = "SELECT HOSTNAME,LAST_MIDFIED FROM {0} WHERE STATUS='Down'".format(table)
                delete_key = "HOSTNAME"
            if db.count(query) > 0:
                for i in db.readt(query):
                    if i[1] <= threshold:
                        log = "{0} > {1} > {2} isimli sunucu 48 saatten uzun süredir down.Sunucu siliniyor.".format(
                            main_system_name, system, i[0])
                        delete_server = "DELETE FROM {0} WHERE {1}='{2}'".format(table, delete_key, i[0])
                        try:
                            db.write(delete_server)
                            counter += 1
                            logger.log_save(watcher, "WARNING", log)
                        except:
                            log = "{0} > {1} > {2} isimli sunucu 48 saatten uzun süredir down.Sunucu silinirken hata oluştu.".format(
                                main_system_name, system, i[0])
                            logger.log_save(watcher, "ERROR", log)
            if all_servers == counter:
                log = "{0} > {1} sistemi artık kullanılmıyor.Silinmek üzere işaretlendi.".format(main_system_name,
                                                                                                 system)
                try:
                    config.set(system, "deleted", "True")
                    with open(sys_config, 'wb') as configfile:
                        config.write(configfile)
                    logger.log_save(watcher, "WARNING", log)
                except:
                    log = "{0} > {1} sistemi artık kullanılmıyor.Silinmek üzere işaretlenirken hata oluştu.".format(
                        main_system_name, system)
                    logger.log_save(watcher, "ERROR", log)
    return True


def main():
    config.read("/Services/Babysitter/config/config.cfg")
    system_delay_second = config.get("env", "followed_delay")
    config_files = config.get("env", "config_files").split(",")
    for sys_config in config_files:
        main_config = ConfigParser.ConfigParser()
        main_config.read(sys_config)
        main_system_name = sys_config.split("/")[2]
        system_list, new_system_list = main_config.get("env", "system_members").split(","), main_config.get("env",
                                                                                                            "system_members").split(
            ",")
        for system in system_list:
            if main_config.get(system, "deleted") == "True":
                table_name = main_config.get(system, "table")
                try:
                    new_system_list.remove(system)
                except ValueError:
                    logger.log_save(watcher, "INFO",
                                   "{0} sistemine ait olan '{1}' isimli sistem, 'system_members' altında tanımlı değildi.".format(
                                       main_system_name, system))
                try:
                    main_config.set("env", "system_members", ",".join(new_system_list))
                    main_config.remove_section(system)
                    with open(sys_config, 'wb') as configfile:
                        main_config.write(configfile)
                    config.read("/Services/Babysitter/config/config.cfg")
                    config.remove_section(system)
                    rest_members = config.get("rest_creator", "endpoint_names").split(",")
                    rest_members.remove(system)
                    config.set("rest_creator", "endpoint_names", ",".join(rest_members))
                    with open("/Services/Babysitter/config/config.cfg", "wb") as mainconfig:
                        config.write(mainconfig)
                    try:
                        if main_system_name == "RabbitMqWatcher":
                            query1 = "DROP TABLE {0}_nodes".format(table_name)
                            query2 = "DROP TABLE {0}_queues".format(table_name)
                            db.write(query1)
                            db.write(query2)
                        else:
                            query = "DROP TABLE {0}".format(table_name)
                            db.write(query)
                        creator.create_script_file()
                        logger.log_save(watcher, "INFO",
                                       "{0} sistemine ait {1} isimli config alanı / alanları silindi.".format(
                                           main_system_name, ",".join(system_list)))
                    except:
                        logger.log_save(watcher, "ERROR",
                                       "{0} sistemine ait {1} isimli tablo silinirken bir sorun oluştu.".format(
                                           main_system_name, table_name))
                        continue
                except:
                    logger.log_save(watcher, "ERROR",
                                   "{0} sistemine ait {1} isimli config alanı silinirken bir sorun oluştu.".format(
                                       main_system_name, system))
                    continue
    return system_delay_second


if __name__ == "__main__":
    try:
        while True:
            discover_new_endpoints()
            health_check_restapi()
            delete_old_systems_or_servers()
            process_watcher()
            db.performance_and_repair(logger=logger, engine_change_for_auto_recpair=True, optimize=True)
            time.sleep(int(main()))
    except KeyboardInterrupt:
        sys.exit(0)
