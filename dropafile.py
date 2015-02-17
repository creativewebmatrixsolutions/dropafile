#    dropafile -- drop me a file on a webpage
#    Copyright (C) 2015  Uli Fouquet
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Drop a file on a webpage.
"""
import os
import random
import shutil
import ssl
import subprocess
import sys
import tempfile
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response


PATH_MAP = {
    '/dropzone.js': ('dropzone.js', 'text/javascript'),
    '/dropzone.css': ('dropzone.css', 'text/css'),
    '/index.html': ('page.html', 'text/html'),
    '/login.html': ('login.html', 'text/html'),
    }


#: Chars allowed in passwords.
#: We allow plain ASCII chars and numbers, with some entitites removed,
#: that can be easily mixed up: letter `l` and number one, for instance.
ALLOWED_PWD_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789abcdefghjkmnpqrstuvwxyz'


def get_random_password():
    """Get a password generated from `ALLOWED_PWD_CHARS`.

    The password entropy should be >= 128 bits. We use `SystemRandom()`,
    which should provide enough randomness to work properly.
    """
    rnd = random.SystemRandom()
    return ''.join(
        [rnd.choice(ALLOWED_PWD_CHARS) for x in range(23)])


class DropAFileApplication(object):

    def __init__(self, password=None):
        """Drop-A-File application.

        `password` is required to access the application's service. If
        none is provided, we generate one for you.
        """
        if password is None:
            password = get_random_password()
        self.password = password

    @Request.application
    def __call__(self, request):
        path = request.path
        if path not in PATH_MAP.keys():
            path = '/login.html'
        filename, mimetype = PATH_MAP[path]
        with open(os.path.join(os.path.dirname(__file__), filename)) as fd:
            page = fd.read()
        return Response(page, mimetype=mimetype)


def execute_cmd(cmd_list):
    """Excute the command `cmd_list`.

    Returns stdout and stderr output.
    """
    pipe = subprocess.PIPE
    proc = subprocess.Popen(
        cmd_list, stdout=pipe, stderr=pipe, shell=False)
    try:
        stdout, stderr = proc.communicate()
    finally:
        proc.stdout.close()
        proc.stderr.close()
        proc.wait()
    return stdout, stderr


def create_ssl_cert(path=None, bits=4096, days=2, cn='localhost',
                    country='US', state='', location=''):
    """Create an SSL cert and key in directory `path`.
    """
    if path is None:
        path = tempfile.mkdtemp()
    cert_path = os.path.join(path, 'cert.pem')
    key_path = os.path.join(path, 'cert.key')
    openssl_conf = os.path.join(os.path.dirname(__file__), 'openssl.conf')
    subject = '/C=%s/ST=%s/L=%s/O=%s/OU=%s/CN=%s/emailAddress=%s/' % (
        country, state, location, '', '', cn, '')
    cmd = [
        'openssl', 'req', '-x509', '-newkey', 'rsa:%s' % bits, '-nodes',
        '-out', cert_path, '-keyout', key_path, '-days', '%s' % days,
        '-sha256', '-config', openssl_conf, '-batch', "-subj", subject
        ]
    out, err = execute_cmd(cmd)
    return cert_path, key_path


def run_server(args=None):
    if args is None:
        args = sys.argv
    print("Creating temporary self-signed SSL certificate...")
    cert, key = create_ssl_cert()
    temp_cert = True
    print("Done.")
    print("Certificate in: %s" % cert)
    print("Key in:         %s" % key)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ssl_context.options |= ssl.OP_NO_SSLv2  # considered unsafe
    ssl_context.options |= ssl.OP_NO_SSLv3  # considered unsafe
    ssl_context.load_cert_chain(cert, key)
    application = DropAFileApplication()
    print("Password is: %s" % application.password)
    run_simple('localhost', 8443, application, ssl_context=ssl_context)
    if temp_cert:
        shutil.rmtree(os.path.dirname(cert))
