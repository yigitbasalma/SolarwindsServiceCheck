#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import sys

sys.path.insert(0, "/Services/Babysitter/config")

import ConfigParser
import logMaster
import requests
import errorMessageTemplate
import math
import time
import db
import datetime
import MySQLdb


class Calculate(object):
    """ Gerekli kaynaklarin hesaplanmasi icin kullanilmaktadir. """

    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.logger = logMaster.Logger("CouchWatcher", "/Services/CouchWatcher/config/config.cfg")
        self.error_msgger = errorMessageTemplate.Message()
        self.db = db.Db()
        self.config.read("/Services/CouchWatcher/config/config.cfg")
        self.timeout = int(self.config.get("env", "timeout"))

    def __check_live(self, server, bucket):
        url = "http://{0}:8091/pools/default/buckets/{1}".format(server, bucket)
        scname = "Host Checker (%s)" % self.server_section
        try:
            r = requests.get(url, auth=(self.user, self.password), timeout=self.timeout)
            if r.status_code == 200:
                return True
            else:
                self.logger.log_save(scname, "ERROR",
                                    "Sunucuya ulaşılamadı.Hata kodu => %s , Server => %s" % (r.status_code, server))
                return False
        except requests.exceptions.ConnectionError:
            self.logger.log_save(scname, "ERROR", "Bağlantı kurulurken hata oluştu.Server => %s ." % server)
            return False
        except requests.exceptions.Timeout:
            self.logger.log_save(scname, "ERROR", "Bağlantı timeout aldı.Server => %s ." % server)
            return False

    def __requester(self, url):
        r = requests.get(url, auth=(self.user, self.password))
        return r.json()

    def __set_all_server(self, bucket, cluster=False):
        url = "http://{0}:8091/pools/default/buckets/{1}".format(self.mainserver, bucket)
        r = self.__requester(url)
        v, servers = [], r["vBucketServerMap"]["serverList"]
        for i in servers:
            if i is not None:
                server = i.split(":")
                v.append(server[0])
        self.set_conf(v, self.server_section, "allservers")
        if cluster:
            return v

    def __find_cluster(self, bucket):
        """ Konfigürasyon dosyasında verilen server parametresi kullanılarak, sisteme ait diğer serverları tespit ediyoruz.
        """

        v = self.__set_all_server(bucket, cluster=True)
        v.remove(self.mainserver)
        if len(v) > 1:
            if self.set_conf(v, self.server_section, "clusterMembers"):
                self.logger.log_save(self.service, "INFO", "clusterMembers parametresi set edildi.")
            else:
                self.logger.log_save(self.service, "ERROR", "clusterMembers parametresi set edilemedi.")
        else:
            self.logger.log_save(self.service, "INFO", "Sistemde cluster bulunmuyor.")

    def __find_source(self, bucket):
        """ Ana sunucu ve cluster sunucuların kaynaklarını bulur ve belirlenen aralıklara göre eşik değerlerini belirler. """
        url, cluster = "http://{0}:8091/pools/default/buckets/{1}".format(self.mainserver, bucket), \
                       "http://{0}:8091/pools/default".format(self.mainserver)
        r, s = self.__requester(url), self.__requester(cluster)
        nodes = r["nodes"]
        cluster_HDD, cluster_RAM = {}, {}
        for k, v in s["storageTotals"]["hdd"].iteritems():
            cluster_HDD[k] = int(int(v) / 1024 / 1024)
        for k, v in s["storageTotals"]["ram"].iteritems():
            cluster_RAM[k] = int(int(v) / 1024 / 1024)
        timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        buckets = self.__find_all_buckets()
        for i in range(0, len(nodes)):
            address = nodes[i]["hostname"].split(":")[0]
            status = nodes[i]["status"]
            uptime = nodes[i]["uptime"]
            clusterMembership = nodes[i]["clusterMembership"]
            memoryTotal = math.ceil(nodes[i]["memoryTotal"] / 1024 / 1024) if "memoryTotal" in nodes[
                i] else "None"  # MB değerine çevrilmiştir.
            memoryUsed = math.ceil((nodes[i]["memoryTotal"] - nodes[i]["memoryFree"]) / 1024 / 1024) if "memoryFree" in \
                                                                                                        nodes[
                                                                                                            i] and "memoryTotal" in \
                                                                                                                   nodes[
                                                                                                                       i] else "None"  # MB değerine çevrilmiştir.
            swapTotal = math.ceil(nodes[i]["systemStats"]["swap_total"] / 1024 / 1024) if "swap_total" in nodes[i][
                "systemStats"] else "None"  # MB değerine çevrilmiştir.
            swapUsed = math.ceil(nodes[i]["systemStats"]["swap_used"] / 1024 / 1024) if "swap_used" in nodes[i][
                "systemStats"] else "None"  # MB değerine çevrilmiştir.
            cpuUtilization = math.ceil(nodes[i]["systemStats"]["cpu_utilization_rate"]) if "cpu_utilization_rate" in \
                                                                                           nodes[i][
                                                                                               "systemStats"] else "None"
            clusterCount = len(nodes)
            # clusterList = ",".join(self.allserver)
            bucketcount = len([k for k, v in buckets.iteritems()])
            bucketstats = buckets
            try:
                param = "INSERT INTO {15} VALUES (\"{0}\",\"{1}\",\"{2}\",\"{3}\",\"{4}\",\"{5}\",\"{6}\",\"{7}\",\"{8}\",\"{9}\",\"{10}\",\"{11}\",\"{12}\",\"{13}\",\"{14}\")".format(
                    address, status, clusterMembership, uptime, memoryTotal, swapTotal, memoryUsed, swapUsed,
                    cpuUtilization, bucketcount, bucketstats, clusterCount, timestamp, cluster_HDD, cluster_RAM,
                    self.table)
                self.db.write(param)
                msg = "'{0}' hostname / IP adresi için değerler DB ye yazıldı.".format(
                    nodes[i]["hostname"].split(":")[0])
                self.logger.log_save(self.service, "INFO", msg)
            except MySQLdb.IntegrityError:
                param = "UPDATE {15} SET STATUS=\"{0}\", CLUSTERMEMBERSHIP=\"{1}\", UPTIME=\"{2}\", RAM_TOTAL=\"{3}\", SWAP_TOTAL=\"{4}\", RAM_USAGE=\"{5}\", SWAP_USAGE=\"{6}\", CPU_UTILITAZION=\"{7}\", TOTAL_BUCKET=\"{8}\", BUCKET_STATS=\"{9}\", CLUSTER_COUNT=\"{10}\", LAST_MIDFIED=\"{11}\", CLUSTER_HDD_STATS=\"{12}\", CLUSTER_RAM_STATS=\"{13}\" WHERE HOSTNAME=\"{14}\"".format(
                    status, clusterMembership, uptime, memoryTotal, swapTotal, memoryUsed, swapUsed, cpuUtilization,
                    bucketcount, bucketstats, clusterCount, timestamp, cluster_HDD, cluster_RAM, address, self.table)
                self.db.write(param)
                msg = "'{0}' hostname / IP adresi için değerler update edildi.".format(
                    nodes[i]["hostname"].split(":")[0])
                self.logger.log_save(self.service, "INFO", msg)
            except MySQLdb.ProgrammingError:
                table_create = "CREATE TABLE %s (HOSTNAME varchar(40) NOT NULL PRIMARY KEY,STATUS varchar(30) DEFAULT NULL,CLUSTERMEMBERSHIP varchar(30) DEFAULT NULL,UPTIME varchar(20) DEFAULT NULL,RAM_TOTAL varchar(30) DEFAULT NULL,SWAP_TOTAL varchar(30) DEFAULT NULL,RAM_USAGE varchar(30) DEFAULT NULL,SWAP_USAGE varchar(30) DEFAULT NULL,CPU_UTILITAZION varchar(25) DEFAULT NULL,TOTAL_BUCKET varchar(5) DEFAULT NULL,BUCKET_STATS varchar(5000) DEFAULT NULL,CLUSTER_COUNT varchar(5) DEFAULT NULL,LAST_MIDFIED datetime DEFAULT NULL,CLUSTER_HDD_STATS varchar(5000) DEFAULT NULL,CLUSTER_RAM_STATS varchar(5000) DEFAULT NULL)" % self.table
                self.db.write(table_create)
                param = "INSERT INTO {15} VALUES (\"{0}\",\"{1}\",\"{2}\",\"{3}\",\"{4}\",\"{5}\",\"{6}\",\"{7}\",\"{8}\",\"{9}\",\"{10}\",\"{11}\",\"{12}\",\"{13}\",\"{14}\")".format(
                    address, status, clusterMembership, uptime, memoryTotal, swapTotal, memoryUsed, swapUsed,
                    cpuUtilization, bucketcount, bucketstats, clusterCount, timestamp, cluster_HDD, cluster_RAM,
                    self.table)
                self.db.write(param)
                msg = "'{0}' hostname / IP adresi için değerler DB ye yazıldı.{1} adında tablo oluşturuldu".format(
                    nodes[i]["hostname"].split(":")[0], self.table)
                self.logger.log_save(self.service, "INFO", msg)

    def __find_all_buckets(self):
        """ Sistem üzerinde bulunan bucket sayısı, isimleri ve "itemCount" değerleri listelenecek. """
        url = "http://{0}:8091/pools/default/buckets".format(self.mainserver)
        r = self.__requester(url)
        bucketsInformations = {}
        for i in range(0, len(r)):
            bucketsInformations["{0}".format(r[i]["name"])] = r[i]["basicStats"]["itemCount"]
        msg = "{0} tane bucket bulundu ve listelendi.Bucket isimleri '{1}'".format(len(r), ",".join(
            [k for k, v in bucketsInformations.iteritems()]))
        self.logger.log_save(self.service, "INFO", msg)
        return bucketsInformations

    def flush_bucket(self, bucket, itemcount):
        try:
            flush_addr = "http://{0}:8091/pools/default/buckets/{1}/controller/doFlush".format(self.mainserver, bucket)
            before = itemcount
            start = time.strftime("%s")
            requests.post(flush_addr, auth=(self.user, self.password))
            end = time.strftime("%s")
            msg = "'{0}' bucket flushlandı.Silinen item sayısı {1}, geçen süre (saniye) {2}".format(bucket, before,
                                                                                                    int(end) - int(
                                                                                                        start))
            self.logger.log_save(self.service, "INFO", msg)
            return True
        except requests.exceptions.ConnectionError:
            msg = "Sunucuya bağlanılamıyor.Lütfen işlemi manuel olarak gerçekleştiriniz."
            self.logger.log_save(self.service, "ERROR", msg)
            return False
        except requests.exceptions.HTTPError:
            msg = "Tanımlanamayan http kodu alındı.Lütfen işlemi manuel olarak gerçekleştiriniz."
            self.logger.log_save(self.service, "ERROR", msg)
            return False
        except requests.exceptions.Timeout:
            msg = "İstek zaman aşımına uğradı.Lütfen işlemi manuel olarak gerçekleştiriniz."
            self.logger.log_save(self.service, "ERROR", msg)
            return False
        except requests.exceptions.TooManyRedirects:
            msg = "TooManyRedirects hatası alındı.Lütfen işlemi manuel olarak gerçekleştiriniz."
            self.logger.log_save(self.service, "ERROR", msg)
            return False

    def set_conf(self, conf_array, section, name=None, add=False):
        """ Tespit edilen parametrelerin, gerekli dosyalara işlenmesini sağlıyoruz. """
        th = ConfigParser.ConfigParser()
        th.read("/Services/CouchWatcher/config/config.cfg")
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
            set_conf_err = "Configürasyon kayıt edilemedi.'{0}' adında bir section yer almıyor.".format(section)
            self.logger.log_save(self.service, "ERROR", set_conf_err)
            return False
        with open('/Services/CouchWatcher/config/config.cfg', 'wb') as configfile:
            th.write(configfile)
            return True

    def calc(self, section):
        """ Ana işlemleri yapan fonksiyon.Sunucu kontrolü,ana sunucuya ulaşılamıyorsa cluster içinden yeni sunucu seçimi ve gerekli hataların loglanması. """
        self.server_section = section
        self.service = "Source Calculator (%s)" % self.server_section
        self.user = self.config.get(self.server_section, "Cuser")
        self.password = self.config.get(self.server_section, "Cpass")
        self.table = self.config.get(self.server_section, "table")
        bucket = self.config.get(self.server_section, "default_bucket")
        status = self.__check_live(self.config.get(self.server_section, "server"), bucket)
        if not status:
            self.logger.log_save(self.service, "ERROR",
                                "{0} hostname / IP sunucunuza ulaşılamadı.'clusterMembers' içinden herhangi bir sunucuya ulaşılması denenecek.".format(
                                    self.config.get(self.server_section, "server")))
            try:
                self.servers = self.config.get(self.server_section, "clusterMembers").split(",")
                for i in self.servers:
                    if i != "":
                        if self.__check_live(i, bucket):
                            self.mainserver = i
                            self.logger.log_save(self.service, "INFO",
                                                "'mainserver' olarak {0} hostname / IP adresi belirlendi.".format(i))
                            try:
                                self.__set_all_server(bucket)
                                self.__find_source(bucket)
                                return True
                            except:
                                return False
                        elif i == self.servers[-1]:
                            if not self.__check_live(i, bucket):
                                self.logger.log_save(self.service, "FATAL",
                                                    "Cluster içinde hiçbir sunucuya ulaşılamıyor.Sunucuları kontrol ediniz.")
                                return False
                    else:
                        self.logger.log_save(self.service, "FATAL",
                                            "'clusterMembers' parametresi altında hiç sunucu bulunmuyor.Sistemlerinizi kontrol ediniz.")
                        return False
            except ConfigParser.NoOptionError:
                self.logger.log_save(self.service, "FATAL",
                                    "'clusterMembers' parametresi tanımlı değil yada sistemde cluster makina bulunmuyor.")
                return False
        else:
            self.mainserver = self.config.get(self.server_section, "server")
            self.logger.log_save(self.service, "INFO",
                                "'mainserver' olarak {0} hostname / IP adresi belirlendi.".format(self.mainserver))
            try:
                self.__find_cluster(bucket)
                self.__find_source(bucket)
                return True
            except:
                return False
