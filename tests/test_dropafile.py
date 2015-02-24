# tests for dropafile module.
import base64
import math
import os
import pytest
import re
import shutil
import subprocess
import time
from contextlib import contextmanager
from io import BytesIO
from werkzeug.datastructures import Headers
from werkzeug.test import Client, create_environ
from werkzeug.wrappers import BaseResponse, Request
from dropafile import (
    DropAFileApplication, execute_cmd, create_ssl_cert, get_random_password,
    ALLOWED_PWD_CHARS, handle_options
    )


@contextmanager
def popen(*args, **kw):
    # a Python 2.6/2.7 compatible Popen contextmanager
    p = subprocess.Popen(*args, **kw)
    try:
        yield p
    finally:
        if p.stdout:
            p.stdout.close()
        if p.stderr:
            p.stderr.close()
        if p.stdin:
            p.stdin.close()
        p.wait()


def encode_creds(username='somename', password=''):
    # turn credentials given into base64 encoded string
    auth_string = '%s:%s' % (username, password)
    encoded = base64.b64encode(auth_string.encode('utf-8'))
    return 'Basic %s' % encoded.decode('utf-8')


def get_basic_auth_headers(username='somename', password=''):
    # get a set of request headers with authorization set to creds.
    headers = Headers()
    headers.add(
        'Authorization', encode_creds(username=username, password=password))
    return headers


def test_page_response():
    # we can get some HTML page for any path
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    headers = get_basic_auth_headers(
        username='somename', password=application.password)
    resp = client.get('/', headers=headers)
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/html; charset=utf-8'


def test_get_js():
    # we can get the dropzonejs JavaScript
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    headers = get_basic_auth_headers(
        username='somename', password=application.password)
    resp = client.get('dropzone.js', headers=headers)
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/javascript; charset=utf-8'


def test_get_css():
    # we can get the dropzonejs CSS
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    headers = get_basic_auth_headers(
        username='somename', password=application.password)
    resp = client.get('dropzone.css', headers=headers)
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/css; charset=utf-8'


def test_send_file():
    # we can send files
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    headers = get_basic_auth_headers(
        username='somename', password=application.password)
    resp = client.post(
        '/index.html',
        headers=headers,
        data={
            'file': (BytesIO(b'Some Content'), 'sample.txt'),
            },
        )
    assert resp.status == '200 OK'


@pytest.mark.skipif(
    not os.path.exists('/bin/echo'), reason="needs /bin/echo")
def test_excute_cmd():
    # we can execute commands (w/o shell)
    cmd = ["/bin/echo", "Hello $PATH"]
    out, err = execute_cmd(cmd)
    assert out == b'Hello $PATH\n'
    assert err == b''


def test_create_cert(tmpdir):
    # we can create x509 certs
    path = tmpdir.dirname
    cert_path, key_path = create_ssl_cert(path)
    assert os.path.isfile(cert_path)
    assert os.path.isfile(key_path)


def test_create_cert_no_path():
    # w/o a given path, one will be created for us
    cert_path, key_path = create_ssl_cert()
    assert os.path.isfile(cert_path)
    shutil.rmtree(os.path.dirname(cert_path))


def test_get_random_password():
    # we can get a random password
    allowed_chars = '[A-HJ-NP-Z2-9a-hjkmnp-z]'
    RE_PWD = re.compile('^%s+$' % allowed_chars)
    password = get_random_password()
    assert RE_PWD.match(password)


def test_get_random_password_entropy():
    # the entropy delivered by default >= 128 bits
    unique_chars = ''.join(list(set(ALLOWED_PWD_CHARS)))
    entropy_per_char = math.log(len(unique_chars)) / math.log(2)
    password = get_random_password()
    assert len(password) * entropy_per_char >= 128


def test_app_has_password():
    # DropAFileApplications have a password
    app = DropAFileApplication()
    assert hasattr(app, 'password')
    assert len(app.password) > 5


def test_app_accepts_passwod():
    # DropAFileApps accept passwords passed in
    app = DropAFileApplication(password='verysecret')
    assert app.password == 'verysecret'


def test_unauthorized_by_default():
    # By default we get an Unauthorized message
    app = DropAFileApplication()
    client = Client(app, BaseResponse)
    resp = client.get('/')
    assert resp.status == '401 UNAUTHORIZED'


def test_basic_auth_req_by_default():
    # By default we require basic auth from client
    app = DropAFileApplication()
    client = Client(app, BaseResponse)
    resp = client.get('/')
    header = resp.headers.get('WWW-Authenticate', None)
    assert header is not None


def test_check_auth_requires_auth():
    # we require at least some creds to authenticate
    app = DropAFileApplication()
    app.password = 'sosecret'
    env = create_environ()
    request = Request(env)
    assert app.check_auth(request) is False


def test_check_auth_wrong_passwd():
    # of course check_auth requires the correct password
    app = DropAFileApplication()
    app.password = 'sosecret'
    env = create_environ()
    env.update(HTTP_AUTHORIZATION=encode_creds(
        username='somename', password='wrong-password'))
    request = Request(env)
    assert app.check_auth(request) is False


def test_check_auth_correct_passwd():
    # the correct password can be seen.
    app = DropAFileApplication()
    app.password = 'sosecret'
    env = create_environ()
    env.update(HTTP_AUTHORIZATION=encode_creds(
        username='somename', password='sosecret'))
    request = Request(env)
    assert app.check_auth(request) is True


def test_main(capfd):
    # we can run the main programme
    out, err = '', ''
    with popen(['dropafile'], bufsize=1) as p:
        timestamp = time.time()
        while True:
            newout, newerr = capfd.readouterr()
            out += newout
            err += newerr
            if p.poll() is not None:
                break
            if err and ('Running' in err):
                break
            if time.time() - timestamp >= 5.0:
                # Timeout happened
                break
            time.sleep(0.1)
        p.terminate()
    assert (out, err) == 'qwe'


class TestArgParser(object):

    def test_help(self, capsys):
        # we support --help
        with pytest.raises(SystemExit) as exc_info:
            handle_options(['foo', '--help'])
        out, err = capsys.readouterr()
        assert exc_info.value.code == 0

    def test_defaults(self):
        # we can get options with defaults set
        result = handle_options([])
        assert result is not None
