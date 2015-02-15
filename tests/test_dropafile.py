# tests for dropafile module.
import os
import pytest
import shutil
import tempfile
from io import BytesIO
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from dropafile import application, execute_cmd, create_ssl_cert


def test_page_response():
    # we get some HTML page by default
    client = Client(application, BaseResponse)
    resp = client.get('/')
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/html; charset=utf-8'


def test_get_js():
    # we can get the dropzonejs JavaScript
    client = Client(application, BaseResponse)
    resp = client.get('dropzone.js')
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/javascript; charset=utf-8'


def test_get_css():
    # we can get the dropzonejs CSS
    client = Client(application, BaseResponse)
    resp = client.get('dropzone.css')
    assert resp.status == '200 OK'
    mimetype = resp.headers.get('Content-Type')
    assert mimetype == 'text/css; charset=utf-8'


def test_send_file():
    # we can send files
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
