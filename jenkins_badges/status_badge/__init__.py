from flask import send_file, Blueprint, current_app
import requests
import io
from six.moves.urllib_parse import urljoin
from jenkins_badges.coverage_badge import send_error_badge

status_badge = Blueprint('status_badge', __name__)


@status_badge.route("/status/<path:job_name>", methods=['GET'])
def send_status_badge(job_name):
    if job_name == "favicon.ico":
        return "", 200

    jenkins_api_url = generate_jenkins_api_url(job_name)
    auth = (current_app.config['JENKINS_USERNAME'],
            current_app.config['JENKINS_TOKEN'])
    auth = None if auth == (None, None) else auth
    jenkins_resp = requests.get(jenkins_api_url, auth=auth)
    print("GET {} {}".format(jenkins_resp.status_code, jenkins_api_url))
    if jenkins_resp.status_code != 200:
        return send_error_badge()

    status = extract_status(jenkins_resp)
    colour = "brightgreen" if status == "SUCCESS" else "red"
    status_shield_url = generate_shield_url(status, colour)
    shield_resp = requests.get(status_shield_url, stream=True)
    print("GET {} {}".format(shield_resp.status_code, status_shield_url))
    if shield_resp.status_code != 200:
        return send_error_badge()

    path = io.BytesIO(shield_resp.content)
    print("SENDING {} build status badge of {}".format(colour, status))
    return send_file(path, mimetype="image/svg+xml", cache_timeout=30), 200


def generate_jenkins_api_url(job_name):
    api_endpoint = "job/{}/lastBuild/api/json".format(job_name)
    return urljoin(current_app.config["JENKINS_BASE_URL"] + "/", api_endpoint)


def extract_status(jresp):
    jenkins_resp = jresp.json()
    status = jenkins_resp["result"]
    return status


def generate_shield_url(status, colour):
    return "https://img.shields.io/badge/build%20status-{}-{}.svg".format(status, colour)
