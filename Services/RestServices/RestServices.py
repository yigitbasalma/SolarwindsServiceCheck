# coding=utf-8
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


@app.route('/sys/api/v0.1/dmall_couchbase/machinestats', methods=['GET'])
@auth.login_required
def dmall_couchbase_machinestats():
	stats = cb.machine_stats('dmall_couchbase')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)


@app.route('/sys/api/v0.1/dmall_couchbase/bucketstats', methods=['GET'])
@auth.login_required
def dmall_couchbase_bucketstats():
	stats = cb.bucket_stats('dmall_couchbase')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)


@app.route('/sys/api/v0.1/dmall_couchbase/clusterbasicstats', methods=['GET'])
@auth.login_required
def dmall_couchbase_clusterbasicstats():
	stats = cb.basic_cluster_stats('dmall_couchbase')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)

@app.route('/sys/api/v0.1/bazaar_couchbase/machinestats', methods=['GET'])
@auth.login_required
def bazaar_couchbase_machinestats():
	stats = cb.machine_stats('bazaar_couchbase')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)


@app.route('/sys/api/v0.1/bazaar_couchbase/bucketstats', methods=['GET'])
@auth.login_required
def bazaar_couchbase_bucketstats():
	stats = cb.bucket_stats('bazaar_couchbase')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)


@app.route('/sys/api/v0.1/bazaar_couchbase/clusterbasicstats', methods=['GET'])
@auth.login_required
def bazaar_couchbase_clusterbasicstats():
	stats = cb.basic_cluster_stats('bazaar_couchbase')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)

@app.route('/sys/api/v0.1/rta_elastic/statics', methods=['GET'])
@auth.login_required
def rta_elastic_statics():
	stats = el.general_stats('rta_elasticsearch')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)

@app.route('/sys/api/v0.1/dmall_elastic/statics', methods=['GET'])
@auth.login_required
def dmall_elastic_statics():
	stats = el.general_stats('dmall_elasticsearch')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)

@app.route('/sys/api/v0.1/analytics_n11/totalvisitors', methods=['GET'])
@auth.login_required
def analytics_n11_totalvisitors():
	stats = an.active_user()
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)


@app.route('/sys/api/v0.1/analytics_n11/totalvisitorsperapp', methods=['GET'])
@auth.login_required
def analytics_n11_totalvisitorsperapp():
	stats = an.active_user_per_app()
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)

@app.route('/sys/api/v0.1/dmall_rabbitmq/nodestats', methods=['GET'])
@auth.login_required
def dmall_rabbitmq_nodestats():
	stats = rb.node_stats('dmall_rabbitmq')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)


@app.route('/sys/api/v0.1/dmall_rabbitmq/queuestats', methods=['GET'])
@auth.login_required
def dmall_rabbitmq_queuestats():
	stats = rb.queue_stats('dmall_rabbitmq')
	try:
		return jsonify({'stats':stats})
	except ValueError:
		abort(500)


@app.route('/sys/api/v0.1/up')
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
