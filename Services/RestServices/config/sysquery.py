#!/usr/bin/python
# -*- coding: utf-8 -*-

import db
import re
import os
import sys
from subprocess import PIPE, Popen

sys.path.append("/Services/GoogleAnalytics")
import analytics_api_app


class Couchbase(object):
    def __init__(self):
        self.db = db.Db()

    def machine_stats(self, table):
        stats = "SELECT HOSTNAME,STATUS,CLUSTERMEMBERSHIP,UPTIME,RAM_TOTAL,SWAP_TOTAL,RAM_USAGE,SWAP_USAGE,CPU_UTILITAZION FROM {0}".format(
            table)
        if self.db.count(stats) > 0:
            statList = []
            for i in self.db.readt(stats):
                s = {"Statistic.HOSTNAME": "0", "Message.HOSTNAME": i[0], "Statistic.STATUS": "0",
                     "Message.STATUS": i[1], "Statistic.CLUSTERMEMBERSHIP": "0", "Message.CLUSTERMEMBERSHIP": i[2],
                     "Statistic.UPTIME": i[3], "Statistic.RAM_TOTAL": i[4], "Statistic.SWAP_TOTAL": i[5],
                     "Statistic.RAM_USAGE": i[6], "Statistic.SWAP_USAGE": i[7], "Statistic.CPU_UTILITAZION": i[8]}
                statList.append({i[0]: s})
            return statList
        else:
            msg = "Hicbir stat bulunamadi.Sistemi kontrol ediniz."
            return msg

    def bucket_stats(self, table):
        stats = "SELECT BUCKET_STATS FROM {0} WHERE STATUS='healthy' AND CLUSTERMEMBERSHIP='active' LIMIT 1".format(
            table)
        if self.db.count(stats) > 0:
            statList = []
            p = re.sub("[\{\} \']+", "", self.db.readt(stats)[0][0]).split(",")
            p = dict((f.split(":")[0], f.split(":")[1]) for f in p)
            for k, v in p.iteritems():
                s = {"Statistic.{0}".format(k): v}
                statList.append(s)
            return statList
        else:
            msg = "Hicbir stat bulunamadi.Sistemi kontrol ediniz."
            return msg

    def basic_cluster_stats(self, table):
        hdd_stats = "SELECT CLUSTER_HDD_STATS FROM {0} WHERE STATUS='healthy' AND CLUSTERMEMBERSHIP='active' LIMIT 1".format(
            table)
        ram_stats = "SELECT CLUSTER_RAM_STATS FROM {0} WHERE STATUS='healthy' AND CLUSTERMEMBERSHIP='active' LIMIT 1".format(
            table)
        if self.db.count(hdd_stats) > 0 and self.db.count(ram_stats) > 0:
            statList = []
            p = re.sub("[\{\} \']+", "", self.db.readt(hdd_stats)[0][0]).split(",")
            p = dict((f.split(":")[0], f.split(":")[1]) for f in p)
            r = re.sub("[\{\} \']+", "", self.db.readt(ram_stats)[0][0]).split(",")
            r = dict((f.split(":")[0], f.split(":")[1]) for f in r)
            s = {"Statistic.total_in_cluster": "{0:.1f}".format(float(r["uquotaTotal"]) / 1024),
                 "Statistic.total_allocated": "{0:.1f}".format(float(r["uquotaUsed"]) / 1024),
                 "Statistic.in_use": "{0:.1f}".format(float(r["uusedByData"]) / 1024),
                 "Statistic.un_used": "{0:.1f}".format((float(r["uquotaUsed"]) - float(r["uusedByData"])) / 1024),
                 "Statistic.un_allocated": "{0:.1f}".format((float(r["uquotaTotal"]) - float(r["uquotaUsed"])) / 1024)}
            statList.append({"RAM STATS": s})
            d = {"Statistic.total_in_cluster": "{0:.1f}".format(float(p["utotal"]) / 1024),
                 "Statistic.usable_free_space": "{0:.1f}".format(float(p["ufree"]) / 1024),
                 "Statistic.in_use": "{0:.1f}".format(float(p["uusedByData"]) / 1024),
                 "Statistic.other_data": "{0:.1f}".format((float(p["uused"]) - float(p["uusedByData"])) / 1024),
                 "Statistic.free": "{0:.1f}".format((float(p["utotal"]) - float(p["uusedByData"])) / 1024)}
            statList.append({"HDD STATS": d})
            return statList
        else:
            msg = "Hicbir stat bulunamadi.Sistemi kontrol ediniz."
            return msg


class Rabbitmq(object):
    def __init__(self):
        self.db = db.Db()

    def node_stats(self, table):
        stats = "SELECT HOSTNAME,STATUS,CLUSTERMEMBERSHIP,RUNING,UPTIME,DISK_FREE,DISK_FREE_LIMIT,MEM_USED,MEM_LIMIT FROM {0}_nodes".format(
            table)
        if self.db.count(stats) > 0:
            statList = []
            for i in self.db.readt(stats):
                s = {"Statistic.HOSTNAME": "0", "Message.HOSTNAME": i[0], "Statistic.STATUS": "0",
                     "Message.STATUS": i[1], "Statistic.CLUSTERMEMBERSHIP": "0", "Message.CLUSTERMEMBERSHIP": i[2],
                     "Statistic.UPTIME": i[3], "Statistic.DISK_FREE": i[4], "Statistic.DISK_FREE_LIMIT": i[5],
                     "Statistic.MEM_USED": i[6], "Statistic.MEM_LIMIT": i[7]}
                statList.append({i[0]: s})
            return statList
        else:
            msg = "Hicbir stat bulunamadi.Sistemi kontrol ediniz."
            return msg

    def queue_stats(self, table):
        stats = "SELECT QUEUENAME,STATUS,STATE,CONSUMERS,MSG_UNACKNOVLEDGED,MSG_READY,DELIVER_GET,PUBLISH_GET FROM {0}_queues".format(
            table)
        if self.db.count(stats) > 0:
            statList = []
            for i in self.db.readt(stats):
                s = {"Statistic.STATUS": "0", "Message.STATUS": i[1], "Statistic.STATE": "0", "Message.STATE": i[2],
                     "Statistic.CONSUMERS": i[3], "Statistic.MSG_UNACKNOVLEDGED": i[4], "Statistic.MSG_READY": i[5],
                     "Statistic.DELIVER_GET": i[6], "Statistic.PUBLISH_GET": i[7]}
                statList.append({i[0]: s})
            return statList
        else:
            msg = "Hicbir stat bulunamadi.Sistemi kontrol ediniz."
            return msg


class Elasticsearch(object):
    def __init__(self):
        self.db = db.Db()

    def general_stats(self, table):
        stats = "SELECT HOST_UNIQUE_NAME,HOSTNAME,CPU_USAGE_PERCENT,JVM_HEAP_USAGE_PERCENT,CLUSTER_STATUS,CLUSTER_NAME,TOTAL_SHARDS,DOCS_TOTAL,USABLE_DISK,NUMBER_OF_NODES FROM {0}".format(
            table)
        if self.db.count(stats) > 0:
            statList = []
            for i in self.db.readt(stats):
                s = {"Statistic.HOSTNAME": "0", "Message.HOSTNAME": i[1], "Statistic.CPU_USAGE_PERCENT": i[2],
                     "Statistic.JVM_HEAP_USAGE_PERCENT": i[3], "Message.CLUSTER_STATUS": i[4],
                     "Statistic.CLUSTER_STATUS": "0", "Message.CLUSTER_NAME": i[5], "Statistic.CLUSTER_NAME": "0",
                     "Statistic.TOTAL_SHARDS": i[6], "Statistic.DOCS_TOTAL": i[7], "Statistic.USABLE_DISK": i[8],
                     "Statistic.NUMBER_OF_NODES": i[9]}
                statList.append({i[0]: s})
            return statList
        else:
            msg = "Hicbir stat bulunamadi.Sistemi kontrol ediniz."
            return msg


class GoogleAnalaytics(object):
    def __init__(self):
        pass

    def count_per_app(self, stuck={}):
        count = 0
        for k, v in stuck.iteritems():
            count += int(v)
        return count

    def active_user(self):
        command = "cd /Services/GoogleAnalytics && timeout 20 /usr/bin/python analytics_api_v3.py"
        a = Popen([command], stdout=PIPE, stderr=PIPE, shell=True)
        a = a.stdout.read().rstrip("\n")
        if a is not None and a.isdigit():
            return {"Statistic.activeUser": a}
        else:
            return {"Statistic.error": "1", "Message.error": "Dosya çalıştırılamadı."}

    def active_user_per_app(self):
        os.chdir("/Services/GoogleAnalytics")
        a = analytics_api_app.main(sys.argv)
        if a is not None and type(a) == dict:
            statlist = []
            for k, v in a.iteritems():
                g = {}
                for i in range(0, len(v), 2):
                    g["Statistic.{0}".format(v[i])] = v[i + 1]
                g["Statistic.AppTotal"] = self.count_per_app(g)
                statlist.append({k: g})
            return statlist
        else:
            return {"Statistic.error": "1", "Message.error": "Dosya çalıştırılamadı."}
