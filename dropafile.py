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
import sys
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response


@Request.application
def application(request):
    with open(os.path.join(os.path.dirname(__file__), 'page.html')) as fd:
        page_html = fd.read()
    return Response(page_html, mimetype="text/html")


def run_server(args=None):
    if args is None:
        args = sys.argv
    run_simple('localhost', 8080, application)
