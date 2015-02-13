# tests for dropafile module.
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from dropafile import application


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
