#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser
import logMaster
import re
from subprocess import Popen, PIPE


class RestCreator(object):
    def __init__(self):
        self.logger = logMaster.Logger("Babysitter", "/Services/Babysitter/config/config.cfg")
        self.config = ConfigParser.ConfigParser()
        self.system_name = "RestAPI File Creator"
        self.create_script_file()

    @staticmethod
    def match_function_name(endpoint_name):
        usabe_stat_list = {"Couchbase": {"machinestats": "machine_stats", "bucketstats": "bucket_stats",
                                         "clusterbasicstats": "basic_cluster_stats"},
                           "RabbitMQ": {"nodestats": "node_stats", "queuestats": "queue_stats"},
                           "Elasticsearch": {"statics": "general_stats"},
                           "GoogleAnalaytics": {"totalvisitors": "active_user",
                                                "totalvisitorsperapp": "active_user_per_app"}
                           }
        if bool(re.match(".*couchbase.*", endpoint_name)):
            return usabe_stat_list["Couchbase"], "cb"
        elif bool(re.match(".*rabbitmq.*", endpoint_name)):
            return usabe_stat_list["RabbitMQ"], "rb"
        elif bool(re.match(".*elastic.*", endpoint_name)):
            return usabe_stat_list["Elasticsearch"], "el"
        elif bool(re.match(".*analytics.*", endpoint_name)):
            return usabe_stat_list["GoogleAnalaytics"], "an"
        else:
            return False, 0

    @staticmethod
    def create_prefix():
        prefix = """# coding=utf-8
#!/usr/bin/python

from flask import Flask, jsonify, abort, make_response, request, g
from flask_httpauth import HTTPBasicAuth
from subprocess import Popen, PIPE

import sys

sys.path.insert(0, "/Services/Babysitter/config")

import config.sysauth as sysauth
import logMaster
import config.sysquery as sysquery

app = Flask(__name__)
auth = HTTPBasicAuth()

logger = logMaster.Logger("RestServices", "/Services/RestServices/config/config.cfg")
cb = sysquery.Couchbase()
rb = sysquery.Rabbitmq()
el = sysquery.Elasticsearch()
an = sysquery.GoogleAnalaytics()
"""
        return prefix

    def create_suffix(self):
        self.config.read("/Services/Babysitter/config/config.cfg")
        api_version = self.config.get("rest_creator", "api_version")
        health_check_url = "{0}/up".format(api_version)
        suffix = """
@app.route('""" + health_check_url + """')
def up():
	return jsonify({"status": "OK"})

@app.route('/sys/api/v0.1/controller/add_system', methods=['POST'])
@auth.login_required
def add_system():
        param = request.form["test"]
        return jsonify({'stats':param})

@auth.verify_password
def verify_password(username,password):
        parent_control = "ps -ef | grep Babysitter.py | grep -v grep"
	pc = Popen(parent_control, shell=True, stderr=PIPE, stdout=PIPE)
	pc.communicate()[0]
        if pc.returncode != 0:
		msg = "Uygulamayı çalıştırmak için Babysitter.py scriptini çalıştırınız."
		logger.log_save("CouchWatcher Main Process", "ERROR", msg)
		sys.exit(1)
	ip = request.headers.get("X-Real-IP")
	requestpath = request.path
	validator = sysauth.Auth()
	g.result = validator.validate(username,password,ip,requestpath)
	if g.result:
		msg = '{0} , {1} , {2} ,RESPONSE:200 OK'.format(ip,username,requestpath)
		logger.log_save('REST SERVICE','ACCESS',msg)
		return True
	else:
		msg = '{0} , {1} , {2} , RESPONSE:401 UNAUTHORIZED'.format(ip,username,requestpath)
		logger.log_save('REST SERVICE','INFO',msg)
		abort(401)

@app.errorhandler(401)
def auth_error(error):
    return make_response(jsonify({'error': g.result}), 401)

@app.errorhandler(404)
def notfound_error(error):
	ip = request.headers.get("X-Real-IP")
        requestpath = request.path
	msg = '{0} , {1} , {2} ,RESPONSE:404 NOT FOUND'.format(ip,"sysroot",requestpath)
        logger.log_save('REST SERVICE','ACCESS',msg)
	return make_response(jsonify({'error': 'Aradiginiz endpoint bulunamadi yada artik sistemde yer almiyor.'}), 404)

@app.errorhandler(500)
def internal_server_error(error):
    msg = 'Sunucu bir hata ile karsilasti.Lutfen loglari inceleyin.'
    logger.log_save('REST SERVICE','CRITIC',msg)
    return make_response(jsonify({'error': 'Sistem yoneticinizle gorusun'}), 500)

if __name__ == '__main__':
	app.run("127.0.0.1", 5000, debug=True)
"""
        return suffix

    def create_endpoints(self):
        db_table = ""
        self.config.read("/Services/Babysitter/config/config.cfg")
        api_version = self.config.get("rest_creator", "api_version")
        endpoint_names = self.config.get("rest_creator", "endpoint_names").split(",")
        all_endpoints = []
        for endpoints in endpoint_names:
            endpoint_list = []
            get_metrics = self.config.get(endpoints, "get_metrics").split(",")
            if not bool(re.match(".*analytics.*", endpoints)):
                db_table = self.config.get(endpoints, "db_table")
            temporary_stats = self.match_function_name(endpoints)
            if not temporary_stats[0]:
                error_msg = "Tanimlamak istediginiz endpoint alani, desteklnenen bir izleme sistemini icermiyor.Ilgili alan '{0}' .".format(
                    endpoints)
                self.logger.log_save(self.system_name, "ERROR", error_msg)
                continue
            usabe_stats = temporary_stats[0]
            function_object_name = temporary_stats[1]
            for metric in get_metrics:
                endpoint_url = "{0}/{1}/{2}".format(api_version, endpoints, metric)
                def_name = "{0}_{1}".format(endpoints, metric)
                if not bool(re.match(".*analytics.*", endpoints)):
                    statics_function = "{0}.{1}('{2}')".format(function_object_name, usabe_stats[metric], db_table)
                else:
                    statics_function = "{0}.{1}()".format(function_object_name, usabe_stats[metric])
                create_endpoint = """
@app.route('""" + endpoint_url + """', methods=['GET'])
@auth.login_required
def """ + def_name + """():
	stats = """ + statics_function + """
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)
"""
                self.logger.log_save(self.system_name, "INFO",
                                    "'{0}' isimli bir endpoint oluşturuldu.".format(endpoint_url))
                endpoint_list.append(create_endpoint)
            all_endpoints.append("\n".join(endpoint_list))
        return "".join(all_endpoints)

    def create_script_file(self):
        script_file_path = "/Services/RestServices/RestServices.py"
        cmd = "/etc/init.d/solarwinds_services RestServices restart 2>&1 > /dev/null"
        with open(script_file_path, "w") as script:
            script.write("{0}\n{1}\n{2}".format(self.create_prefix(), self.create_endpoints(), self.create_suffix()))
        Popen([cmd], stdout=PIPE, stderr=PIPE, shell=True)
        self.logger.log_save(self.system_name, "INFO", "Script başlatıldı.RestAPI kullanılabilir durumda.")
