# tests for dropafile module.
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
from dropafile import application


def test_page_response():
    # we get some HTML page by default
    client = Client(application, BaseResponse)
    resp = client.get('/')
    assert resp.status == '200 OK'
