#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import sys

sys.path.insert(0, "/Services/Babysitter/config")

import ConfigParser
import logMaster
import requests
import math
import db
import datetime
import MySQLdb


class Calculate(object):
    """ Gerekli kaynaklarin hesaplanmasi icin kullanilmaktadir. """

    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read("/Services/ElasticsearchWatcher/config/config.cfg")
        self.logger = logMaster.Logger("ElasticsearchWatcher", "/Services/ElasticsearchWatcher/config/config.cfg")
        self.db = db.Db()
        self.timeout = int(self.config.get("env", "timeout"))

    def __check_live(self, server, port):
        url = "http://{0}:{1}".format(server, port)
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                return True, "0"
            else:
                return False, "URL adresine ulaşım başarısız.Dönüş kodu '%s'" % r.status_code
        except requests.exceptions.ConnectionError as e:
            return False, "URL adresine ulaşılmaya çalışırken tanımlanamayan bir hata oluştu. (Hata : %s)" % e
        except requests.exceptions.Timeout as e:
            return False, "URL adresine ulaşılmaya çalışırken tanımlanamayan bir hata oluştu. (Hata : %s)" % e

    @staticmethod
    def __requester(url):
        r = requests.get(url)
        return r.json(), r.status_code

    def __find_cluster_members(self):
        url = "http://{0}:{1}/_nodes/stats".format(self.server, self.port)
        try:
            r = self.__requester(url)
            if r[1] == 200:
                cluster_members = []
                a = r[0]
                for node in a["nodes"]:
                    cluster_members.append("{0}.n11.local".format(a["nodes"][node]["name"]))
                try:
                    cluster_members = set(cluster_members)
                    cluster_members.remove(self.server)
                except:
                    pass
                if len(cluster_members) > 0:
                    if self.set_conf(cluster_members, self.server_section, "clusterMembers")[0]:
                        return True, "'%s' adresi için 'clusterMembers' parametresi girildi." % self.server
                    else:
                        return False, self.set_conf(cluster_members, self.server_section, "clusterMembers")[1]
                else:
                    return True, "Sistemde cluster bulunmuyor."
            else:
                return False, "'%s' adresine ulaşmaya çaışırken %s hata kodu alındı.Lütfen kontrol ediniz." % (
                    url, r[1])
        except requests.exceptions as e:
            return False, "URL adresine ulaşılmaya çalışırken tanımlanamayan bir hata oluştu. (Hata : %s)" % e

    def __find_cluster_source(self):
        url = "http://{0}:{1}/_cluster/health?pretty".format(self.server, self.port)
        try:
            r = self.__requester(url)
            if r[1] == 200:
                a = r[0]
                cluster_name = a["cluster_name"]
                cluster_status = a["status"]
                number_of_nodes = a["number_of_nodes"]
                number_of_data_nodes = a["number_of_data_nodes"]
                return True, (number_of_data_nodes, number_of_nodes, cluster_status, cluster_name)
            else:
                return False, "'%s' adresine ulaşmaya çaışırken %s hata kodu alındı.Lütfen kontrol ediniz." % (
                    url, r[1])
        except requests.exceptions as e:
            return False, "URL adresine ulaşılmaya çalışırken tanımlanamayan bir hata oluştu. (Hata : %s)" % e

    def __find_general_source(self):
        url = "http://{0}:{1}/_stats".format(self.server, self.port)
        try:
            r = self.__requester(url)
            if r[1] == 200:
                a = r[0]
                total_shards = a["_shards"]["total"]
                successful_shards = a["_shards"]["successful"]
                docs_total = a["_all"]["total"]["docs"]["count"]
                docs_deleted = a["_all"]["total"]["docs"]["deleted"]
                return True, (total_shards, successful_shards, docs_total, docs_deleted)
            else:
                return False, "'%s' adresine ulaşmaya çaışırken %s hata kodu alındı.Lütfen kontrol ediniz." % (
                    url, r[1])
        except requests.exceptions as e:
            return False, "URL adresine ulaşılmaya çalışırken tanımlanamayan bir hata oluştu. (Hata : %s)" % e

    def __find_main_source(self):
        url = "http://{0}:{1}/_nodes/stats".format(self.server, self.port)
        try:
            r = self.__requester(url)
            if r[1] == 200:
                a = r[0]
                for i in a["nodes"]:
                    host_unique_name = i
                    target_env = a["nodes"][i]["name"]
                    hostname = a["nodes"][i]["host"]
                    is_master = a["nodes"][i]["attributes"]["master"]
                    uptime = a["nodes"][i]["os"]["uptime_in_millis"] if "uptime_in_millis" in a["nodes"][i]["os"] else 0
                    load_avg = ";".join(["{0}".format(load) for load in a["nodes"][i]["os"]["load_average"]]) if type(
                        a["nodes"][i]["os"]["load_average"]) == list else a["nodes"][i]["os"]["load_average"]
                    pys_mem_free_percent = a["nodes"][i]["os"]["mem"]["free_percent"]
                    pys_mem_usage_percent = a["nodes"][i]["os"]["mem"]["used_percent"]
                    swap_used = math.ceil(a["nodes"][i]["os"]["swap"]["used_in_bytes"] / 1024 / 1024) if int(
                        a["nodes"][i]["os"]["swap"]["used_in_bytes"]) > 0 else 0
                    swap_free = math.ceil(a["nodes"][i]["os"]["swap"]["free_in_bytes"] / 1024 / 1024) if int(
                        a["nodes"][i]["os"]["swap"]["free_in_bytes"]) > 0 else 0
                    cpu_usage_percent = a["nodes"][i]["process"]["cpu"]["percent"]
                    jvm_uptime = a["nodes"][i]["jvm"]["uptime_in_millis"]
                    jvm_heap_max = math.ceil(a["nodes"][i]["jvm"]["mem"]["heap_max_in_bytes"] / 1024 / 1024) if int(
                        a["nodes"][i]["jvm"]["mem"]["heap_max_in_bytes"]) > 0 else 0
                    jvm_heap_used_percent = a["nodes"][i]["jvm"]["mem"]["heap_used_percent"]
                    jvm_thread_count = a["nodes"][i]["jvm"]["threads"]["count"]
                    jvm_thread_peak_count = a["nodes"][i]["jvm"]["threads"]["peak_count"]
                    if self.__find_cluster_source()[0]:
                        cluster_source = self.__find_cluster_source()[1]
                        number_of_data_nodes = cluster_source[0]
                        number_of_nodes = cluster_source[1]
                        cluster_status = cluster_source[2]
                        cluster_name = cluster_source[3]
                    else:
                        return False, (self.__find_cluster_source()[1])
                    if self.__find_general_source()[0]:
                        general_source = self.__find_general_source()[1]
                        total_shards = general_source[0]
                        successful_shards = general_source[1]
                        docs_total = general_source[2]
                        docs_deleted = general_source[3]
                    else:
                        return False, (self.__find_general_source()[1])
                    total_disk = math.ceil(
                        a["nodes"][i]["fs"]["total"]["total_in_bytes"] / 1024 / 1024) if is_master == "true" else 0
                    usable_disk = math.ceil(
                        a["nodes"][i]["fs"]["total"]["available_in_bytes"] / 1024 / 1024) if is_master == "true" else 0
                    timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    try:
                        query = "INSERT INTO {27} VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}','{16}','{17}','{18}','{19}','{20}','{21}','{22}','{23}','{24}','{25}', '{26}', 'UP')".format(
                            host_unique_name, target_env, hostname, is_master, uptime, load_avg, pys_mem_free_percent,
                            pys_mem_usage_percent, swap_used, swap_free, cpu_usage_percent, jvm_uptime, jvm_heap_max,
                            jvm_heap_used_percent, jvm_thread_count, jvm_thread_peak_count, number_of_data_nodes,
                            number_of_nodes, cluster_status, cluster_name, total_shards, successful_shards, docs_total,
                            docs_deleted, total_disk, usable_disk, timestamp, self.table)
                        self.db.write(query)
                        self.logger.log_save(self.service, "INFO",
                                            "'{0}' sunucusu için değerler yazıldı.Host benzersiz ismi '{1}'".format(
                                                hostname, host_unique_name))
                    except MySQLdb.IntegrityError:
                        query = "UPDATE {27} SET TARGET_ENV='{0}', HOSTNAME='{1}', IS_MASTER='{2}', UPTIME='{3}', LOAD_AVG='{4}', PYS_MEM_FREE_PERCENT='{5}', PYS_MEM_USAGE_PERCENT='{6}', SWAP_USED='{7}', SWAP_FREE='{8}', CPU_USAGE_PERCENT='{9}', JVM_UPTIME='{10}', JVM_HEAP_MAX='{11}', JVM_HEAP_USAGE_PERCENT='{12}', JVM_THREAD_COUNT='{13}', JVM_THREAD_PEAK_COUNT='{14}', NUMBER_OF_DATA_NODES='{15}', NUMBER_OF_NODES='{16}', CLUSTER_STATUS='{17}', CLUSTER_NAME='{18}', TOTAL_SHARDS='{19}', SUCCESSFUL_SHARDS='{20}', DOCS_TOTAL='{21}', DOCS_DELETED='{22}', TOTAL_DISK='{23}', USABLE_DISK='{24}', LAST_MIDFIED='{25}', STATUS='UP' WHERE HOST_UNIQUE_NAME='{26}'".format(
                            target_env, hostname, is_master, uptime, load_avg, pys_mem_free_percent,
                            pys_mem_usage_percent, swap_used, swap_free, cpu_usage_percent, jvm_uptime, jvm_heap_max,
                            jvm_heap_used_percent, jvm_thread_count, jvm_thread_peak_count, number_of_data_nodes,
                            number_of_nodes, cluster_status, cluster_name, total_shards, successful_shards, docs_total,
                            docs_deleted, total_disk, usable_disk, timestamp, host_unique_name, self.table)
                        self.db.write(query)
                        self.logger.log_save(self.service, "INFO",
                                            "'{0}' sunucusu için değerler güncellendi.Host benzersiz ismi '{1}'".format(
                                                hostname, host_unique_name))
                    except MySQLdb.ProgrammingError:
                        create_table = "CREATE TABLE %s (HOST_UNIQUE_NAME VARCHAR(200) PRIMARY KEY, TARGET_ENV VARCHAR(100), HOSTNAME VARCHAR(150), IS_MASTER VARCHAR(5), UPTIME VARCHAR(200), LOAD_AVG VARCHAR(150), PYS_MEM_FREE_PERCENT VARCHAR(3), PYS_MEM_USAGE_PERCENT VARCHAR(3), SWAP_USED VARCHAR(150), SWAP_FREE VARCHAR(150), CPU_USAGE_PERCENT VARCHAR(3), JVM_UPTIME VARCHAR(200), JVM_HEAP_MAX VARCHAR(100), JVM_HEAP_USAGE_PERCENT VARCHAR(3), JVM_THREAD_COUNT VARCHAR(50), JVM_THREAD_PEAK_COUNT VARCHAR(50), NUMBER_OF_DATA_NODES VARCHAR(2), NUMBER_OF_NODES VARCHAR(2), CLUSTER_STATUS VARCHAR(20), CLUSTER_NAME VARCHAR(150), TOTAL_SHARDS VARCHAR(30), SUCCESSFUL_SHARDS VARCHAR(30), DOCS_TOTAL VARCHAR(30), DOCS_DELETED VARCHAR(30), TOTAL_DISK VARCHAR(100), USABLE_DISK VARCHAR(100), LAST_MIDFIED DATETIME, STATUS VARCHAR(30) DEFAULT 'UP')" % self.table
                        self.db.write(create_table)
                        query = "INSERT INTO {27} VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}','{10}','{11}','{12}','{13}','{14}','{15}','{16}','{17}','{18}','{19}','{20}','{21}','{22}','{23}','{24}','{25}', '{26}', 'UP')".format(
                            host_unique_name, target_env, hostname, is_master, uptime, load_avg, pys_mem_free_percent,
                            pys_mem_usage_percent, swap_used, swap_free, cpu_usage_percent, jvm_uptime, jvm_heap_max,
                            jvm_heap_used_percent, jvm_thread_count, jvm_thread_peak_count, number_of_data_nodes,
                            number_of_nodes, cluster_status, cluster_name, total_shards, successful_shards, docs_total,
                            docs_deleted, total_disk, usable_disk, timestamp, self.table)
                        self.db.write(query)
                        self.logger.log_save(self.service, "INFO",
                                            "'{0}' sunucusu için değerler güncellendi.Host benzersiz ismi '{1}'".format(
                                                hostname, host_unique_name))
                return True, 0
            else:
                return False, "'%s' adresine ulaşmaya çaışırken %s hata kodu alındı.Lütfen kontrol ediniz." % (
                    url, r[1])
        except requests.exceptions as e:
            return False, "URL adresine ulaşılmaya çalışırken tanımlanamayan bir hata oluştu. (Hata : %s)" % e

    def set_conf(self, conf_array, section, name=None, add=False):
        """ Tespit edilen parametrelerin, gerekli dosyalara işlenmesini sağlıyoruz. """
        th = ConfigParser.ConfigParser()
        th.read("/Services/ElasticsearchWatcher/config/config.cfg")
        try:
            if add:
                if not self.config.has_section(section):
                    th.add_section(section)
                    for k, v in conf_array.items():
                        th.set(section, k, v)
                else:
                    for k, v in conf_array.items():
                        th.set(section, k, v)
            else:
                item = ",".join(map(str, conf_array))
                th.set(section, name, item)
        except ConfigParser.NoSectionError:
            return False, "Configürasyon kayıt edilemedi.'%s' adında bir section yer almıyor." % section
        with open('/Services/ElasticsearchWatcher/config/config.cfg', 'wb') as configfile:
            th.write(configfile)
            return True, "0"

    def calc(self, server_section):
        self.config.read("/Services/ElasticsearchWatcher/config/config.cfg")
        self.server_section = server_section
        self.service = "Source Calculator (%s)" % self.server_section
        self.table = self.config.get(self.server_section, "table")
        self.port = self.config.get(self.server_section, "port")
        server = self.__check_live(self.config.get(self.server_section, "server"), self.port)
        if not server[0]:
            self.logger.log_save(self.service, "ERROR",
                "%s 'clusterMembers' içinden herhangi bir sunucuya ulaşılması denenecek." % server[1])
            try:
                self.servers = self.config.get(self.server_section, "clusterMembers").split(",")
                for i in self.servers:
                    if i != "":
                        if self.__check_live(i, self.port)[0]:
                            self.server = i
                            self.logger.log_save(self.service, "INFO",
                                                "'mainserver' olarak {0} hostname / IP adresi belirlendi.".format(i))
                            if self.__find_main_source()[0]:
                                return True, 0
                            else:
                                self.logger.log_save(self.service, "ERROR", self.__find_main_source()[1])
                                return False, i, self.table
                        elif i == self.servers[-1]:
                            if not self.__check_live(i, self.port)[0]:
                                self.logger.log_save(self.service, "FATAL",
                                                    "Cluster içinde hiçbir sunucuya ulaşılamıyor.Sunucuları kontrol ediniz.'%s'" %
                                                    self.checkLive(i, self.port)[1])
                                self.servers.append(self.config.get(self.server_section, "server"))
                                return False, i, self.table
            except:
                self.logger.log_save(self.service, "FATAL",
                                    "'clusterMembers' parametresi tanımlı değil yada sistemde cluster makina bulunmuyor.")
                return False, self.config.get(self.server_section, "server"), self.table
        else:
            self.server = self.config.get(self.server_section, "server")
            self.logger.log_save(self.service, "INFO",
                                    "'mainserver' olarak {0} hostname / IP adresi belirlendi.".format(self.server))
            if self.__find_main_source()[0]:
                a = self.__find_cluster_members()
                if a[0]:
                    self.logger.log_save(self.service, "INFO", a[1])
                    return True, 0
                else:
                    self.logger.log_save(self.service, "INFO", a[1])
                    return True, 0
            else:
                self.logger.log_save(self.service, "ERROR", self.__find_main_source()[1])
                return False, self.server, self.table