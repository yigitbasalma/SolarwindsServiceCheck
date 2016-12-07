#!/usr/bin/env python

import ConfigParser
import os
import datetime

from termcolor import colored


class Logger(object):
    def __init__(self, logger_name, c_path):
        config = ConfigParser.ConfigParser()
        config.read(c_path)
        self.path = config.get("log", "path")
        try:
            os.listdir(self.path)
        except OSError:
            os.makedirs(self.path, 0755)
        self.path = "{0}{1}.txt".format(self.path, logger_name)

    @staticmethod
    def timestamp(pt="ts"):
        date = datetime.datetime.now()
        options = {
            "ts": "%d/%m/%Y %H:%M:%S",
            "br": "%d/%m/%Y",
            "fl": "%a, %d %b %Y %H:%M:%S"
        }
        try:
            return date.strftime(options[pt])
        except NameError:
            return date.strftime(options["ts"])

    def log_save(self, scname, level, msg):
        colors = {
            "INFO": "green",
            "ERROR": "red",
            "ACCESS": "cyan",
            "CRITIC": "red",
            "WARNING": "magenta"
        }
        with open(self.path, "a") as log_file:
            log = "[{0}] [{1}] [{3}] [{2}]\n".format(str(self.timestamp()), str(scname), str(msg),
                                                     colored(str(level), colors[level]))
            log_file.write(log)
