# tests for dropafile module.
import base64
import math
import os
import pytest
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from io import BytesIO
from werkzeug.datastructures import Headers
from werkzeug.test import Client, create_environ, EnvironBuilder
from werkzeug.wrappers import BaseResponse, Request
from dropafile import (
    DropAFileApplication, execute_cmd, create_ssl_cert, get_random_password,
    ALLOWED_PWD_CHARS, handle_options, run_server, get_store_path
    )


#: find a certificate path in output.
RE_CERTPATH = re.compile(
    '^.*Certificate in:[\s]+([^\s][^\n]+)\n.*$', re.M + re.S)


@contextmanager
def popen(*args, **kw):
    # a Python 2.6/2.7 compatible Popen contextmanager
    p = subprocess.Popen(*args, **kw)
    try:
        yield p
    finally:
        for stream in (p.stdout, p.stderr, p.stdin):
            if stream:
                stream.close()
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


class TestHelpers(object):

    @pytest.mark.skipif(
        not os.path.exists('/bin/echo'), reason="needs /bin/echo")
    def test_excute_cmd(self):
        # we can execute commands (w/o shell)
        cmd = ["/bin/echo", "Hello $PATH"]
        out, err = execute_cmd(cmd)
        assert out == b'Hello $PATH\n'
        assert err == b''

    def test_create_cert(self, tmpdir):
        # we can create x509 certs
        path = tmpdir.dirname
        cert_path, key_path = create_ssl_cert(path)
        assert os.path.isfile(cert_path)
        assert os.path.isfile(key_path)
        shutil.rmtree(os.path.dirname(cert_path))

    def test_create_cert_no_path(self):
        # w/o a given path, one will be created for us
        cert_path, key_path = create_ssl_cert()
        assert os.path.isfile(cert_path)
        shutil.rmtree(os.path.dirname(cert_path))

    def test_get_random_password(self):
        # we can get a random password
        allowed_chars = '[A-HJ-NP-Z2-9a-hjkmnp-z]'
        RE_PWD = re.compile('^%s+$' % allowed_chars)
        password = get_random_password()
        assert RE_PWD.match(password)

    def test_get_random_password_entropy(self):
        # the entropy delivered by default >= 128 bits
        unique_chars = ''.join(list(set(ALLOWED_PWD_CHARS)))
        entropy_per_char = math.log(len(unique_chars)) / math.log(2)
        password = get_random_password()
        assert len(password) * entropy_per_char >= 128

    def test_get_store_path(self):
        # we can get a safe storage path
        store_dir = tempfile.mkdtemp()
        path = get_store_path(store_dir, 'test.txt')
        assert path == os.path.join(store_dir, 'test.txt')

    def test_get_store_path_one_file_in(self):
        # with one file in we get a modified filename
        store_dir = tempfile.mkdtemp()
        open(os.path.join(store_dir, 'test.txt'), 'w').write('foo')
        path = get_store_path(store_dir, 'test.txt')
        assert path.endswith('/test.txt-1')
        open(path, 'w').write('foo')
        path = get_store_path(store_dir, 'test.txt')
        assert path.endswith('/test.txt-2')
        open(path, 'w').write('foo')
        path = get_store_path(store_dir, 'test.txt')
        assert path.endswith('/test.txt-3')

    def test_get_store_path_two_files_in(self):
        # with two files in we also get a modified filename
        store_dir = tempfile.mkdtemp()
        open(os.path.join(store_dir, 'test.txt'), 'w').write('foo')
        open(os.path.join(store_dir, 'test.txt-2'), 'w').write('foo')
        path = get_store_path(store_dir, 'test.txt')
        assert path.endswith('/test.txt-1')


class TestApp(object):
    # no browser tests here

    def test_app_has_password(self):
        # DropAFileApplications have a password
        app = DropAFileApplication()
        assert hasattr(app, 'password')
        assert len(app.password) > 5

    def test_app_accepts_passwod(self):
        # DropAFileApps accept passwords passed in
        app = DropAFileApplication(password='verysecret')
        assert app.password == 'verysecret'

    def test_check_auth_requires_auth(self):
        # we require at least some creds to authenticate
        app = DropAFileApplication()
        app.password = 'sosecret'
        env = create_environ()
        request = Request(env)
        assert app.check_auth(request) is False

    def test_check_auth_wrong_passwd(self):
        # of course check_auth requires the correct password
        app = DropAFileApplication()
        app.password = 'sosecret'
        env = create_environ()
        env.update(HTTP_AUTHORIZATION=encode_creds(
            username='somename', password='wrong-password'))
        request = Request(env)
        assert app.check_auth(request) is False

    def test_check_auth_correct_passwd(self):
        # the correct password can be seen.
        app = DropAFileApplication()
        app.password = 'sosecret'
        env = create_environ()
        env.update(HTTP_AUTHORIZATION=encode_creds(
            username='somename', password='sosecret'))
        request = Request(env)
        assert app.check_auth(request) is True

    def test_handle_uploaded_files(self):
        # we can send files (that are stored)
        app = DropAFileApplication()
        builder = EnvironBuilder(
            method='POST',
            data={'file': (BytesIO(b'foo'), 'test.txt')}
            )
        req = Request(builder.get_environ())
        app.handle_uploaded_files(req)
        expected_path = os.path.join(app.upload_dir, 'test.txt')
        assert os.path.isfile(expected_path)
        assert open(expected_path, 'r').read() == 'foo'

    def test_handle_uploaded_files_wrong_formfield_name(self):
        # only files with form-name 'file' are considered
        app = DropAFileApplication()
        builder = EnvironBuilder(
            method='POST',
            data={'not_file': (BytesIO(b'foo'), 'test.txt')}
            )
        req = Request(builder.get_environ())
        app.handle_uploaded_files(req)
        assert os.listdir(app.upload_dir) == []

    def test_handle_uploaded_files_multiple_at_once(self):
        # we only take one file, even if multiple are offered
        app = DropAFileApplication()
        builder = EnvironBuilder(
            method='POST',
            data={'file': (BytesIO(b'foo'), 'test.txt'),
                  'file2': (BytesIO(b'bar'), 'test2.txt')}
            )
        req = Request(builder.get_environ())
        app.handle_uploaded_files(req)
        assert os.listdir(app.upload_dir) == ['test.txt']

    def test_handle_uploaded_files_output(self, capsys):
        # sent files are listed on commandline
        app = DropAFileApplication()
        builder = EnvironBuilder(
            method='POST',
            data={'file': (BytesIO(b'foo'), 'test.txt')}
            )
        req = Request(builder.get_environ())
        app.handle_uploaded_files(req)
        out, err = capsys.readouterr()
        assert 'RECEIVED:' in out
        assert 'test.txt' in out

    def test_handle_uploaded_files_no_files(self, capsys):
        # we notice if no files was sent (and do nothing)
        app = DropAFileApplication()
        req = Request(create_environ())
        app.handle_uploaded_files(req)
        out, err = capsys.readouterr()
        assert os.listdir(app.upload_dir) == []
        assert 'RECEIVED' not in out

    def test_handle_uploaded_files_not_overwritten(self):
        # we do not overwrite uploaded files
        app = DropAFileApplication()
        builder = EnvironBuilder(
            method='POST',
            data={'file': (BytesIO(b'uploaded'), 'test.txt')}
            )
        req = Request(builder.get_environ())
        upload_path = os.path.join(app.upload_dir, 'test.txt')
        with open(upload_path, 'w') as fd:
            fd.write('original')
        app.handle_uploaded_files(req)
        assert sorted(
            os.listdir(app.upload_dir)) == ['test.txt', 'test.txt-1']
        with open(os.path.join(app.upload_dir, 'test.txt'), 'r') as fd:
            content1 = fd.read()
        with open(os.path.join(app.upload_dir, 'test.txt-1'), 'r') as fd:
            content2 = fd.read()
        assert content1 == 'original'
        assert content2 == 'uploaded'


class TestArgParser(object):

    def test_help(self, capsys):
        # we support --help
        with pytest.raises(SystemExit) as exc_info:
            handle_options(['foo', '--help'])
        out, err = capsys.readouterr()
        assert exc_info.value.code == 0

    def test_help_lists_all_options(self, capsys):
        # all options are listed in --help
        with pytest.raises(SystemExit):
            handle_options(['foo', '--help'])
        out, err = capsys.readouterr()
        assert '--host' in out
        assert '--port' in out
        assert '--secret' in out

    def test_defaults(self):
        # we can get options with defaults set
        result = handle_options([])
        assert result is not None
        assert result.host == 'localhost'
        assert result.port == 8443
        assert result.secret is None

    def test_host(self):
        result = handle_options(['--host', 'foo'])
        assert result.host == 'foo'

    def test_port(self):
        result = handle_options(['--port', '1234'])
        assert result.port == 1234

    def test_secret(self):
        result = handle_options(['--secret', 'sosecret'])
        assert result.secret == 'sosecret'


class Test_run_server(object):

    def test_no_options(self, proc_runner):
        # we can start a server (no options given)
        proc_runner.argv = ['dropafile', ]
        out, err = proc_runner.run(run_server, args=None)
        assert 'Certificate in:' in out
        assert 'Running' in err

    def test_help(self, proc_runner):
        # we can get help from run_server()
        out, err = proc_runner.run(run_server, args=["dropafile", "--help"])
        assert 'show this help message and exit' in out
        assert proc_runner.exitcode == 0

    def test_secret(self, proc_runner):
        # a passed-in password is respected
        out, err = proc_runner.run(
            run_server, args=["dropafile", "-s", "sosecret"])
        assert 'Password is: sosecret' in out

    def test_host_and_port(self, proc_runner):
        # we can set a custom host and port we want to bind to
        out, err = proc_runner.run(
            run_server, args=["dropafile",
                              "--host", "0.0.0.0",
                              "--port", "12345"]
            )
        assert "https://0.0.0.0:12345/" in err


class TestFunctional(object):
    # Functional browser tests

    def test_page_response(self):
        # we can get some HTML page for any path
        application = DropAFileApplication()
        client = Client(application, BaseResponse)
        headers = get_basic_auth_headers(
            username='somename', password=application.password)
        resp = client.get('/', headers=headers)
        assert resp.status == '200 OK'
        mimetype = resp.headers.get('Content-Type')
        assert mimetype == 'text/html; charset=utf-8'

    def test_get_js(self):
        # we can get the dropzonejs JavaScript
        application = DropAFileApplication()
        client = Client(application, BaseResponse)
        headers = get_basic_auth_headers(
            username='somename', password=application.password)
        resp = client.get('dropzone.js', headers=headers)
        assert resp.status == '200 OK'
        mimetype = resp.headers.get('Content-Type')
        assert mimetype == 'text/javascript; charset=utf-8'

    def test_get_css(self):
        # we can get the dropzonejs CSS
        application = DropAFileApplication()
        client = Client(application, BaseResponse)
        headers = get_basic_auth_headers(
            username='somename', password=application.password)
        resp = client.get('dropzone.css', headers=headers)
        assert resp.status == '200 OK'
        mimetype = resp.headers.get('Content-Type')
        assert mimetype == 'text/css; charset=utf-8'

    def test_send_file(self):
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
        uploaded_path = os.path.join(application.upload_dir, 'sample.txt')
        assert os.path.isfile(uploaded_path)

    def test_unauthorized_by_default(self):
        # By default we get an Unauthorized message
        app = DropAFileApplication()
        client = Client(app, BaseResponse)
        resp = client.get('/')
        assert resp.status == '401 UNAUTHORIZED'

    def test_basic_auth_req_by_default(self):
        # By default we require basic auth from client
        app = DropAFileApplication()
        client = Client(app, BaseResponse)
        resp = client.get('/')
        header = resp.headers.get('WWW-Authenticate', None)
        assert header is not None

    def test_page_set_password(self):
        # we can get some HTML page for any path
        application = DropAFileApplication(password="sosecret")
        client = Client(application, BaseResponse)
        headers = get_basic_auth_headers(
            username='somename', password="sosecret")
        resp = client.get('/', headers=headers)
        assert resp.status == '200 OK'
