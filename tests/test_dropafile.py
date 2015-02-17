# tests for dropafile module.
import math
import os
import pytest
import re
import shutil
from io import BytesIO
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from dropafile import (
    DropAFileApplication, execute_cmd, create_ssl_cert, get_random_password,
    ALLOWED_PWD_CHARS,
    )


def test_page_response():
    # we get some HTML page by default
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    resp = client.get('/')
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/html; charset=utf-8'


def test_page_default_is_login():
    # we get the login page by default
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    resp = client.get('/')
    assert b'Passphrase' in resp.data


def test_get_js():
    # we can get the dropzonejs JavaScript
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    resp = client.get('dropzone.js')
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/javascript; charset=utf-8'


def test_get_css():
    # we can get the dropzonejs CSS
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    resp = client.get('dropzone.css')
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/css; charset=utf-8'


def test_send_file():
    # we can send files
    application = DropAFileApplication()
    client = Client(application, BaseResponse)
    resp = client.post(
        '/index.html',
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
