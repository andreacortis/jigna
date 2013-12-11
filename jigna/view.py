#
# Enthought product code
#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is confidential and NOT open source.  Do not distribute.
#


# Standard library.
import os
from os.path import abspath, dirname, join

# Enthought library.
from traits.api import HasTraits, Instance, Str

# Jigna libary.
from jigna.server import Server


#### HTML templates ###########################################################

DOCUMENT_HTML_TEMPLATE = """
<html ng-app='jigna'>
  <head>
    <script type="text/javascript" src="/jigna/js/jquery.min.js"></script>
    <script type="text/javascript" src="/jigna/js/angular.min.js"></script>
    <script type="text/javascript" src="/jigna/js/jigna.js"></script>

    {head_html}

  </head>

  <body>
    {body_html}
  </body>
</html>
"""


class View(HasTraits):
    """ A factory for HTML/AngularJS based user interfaces. """

    ### 'View' class protocol #################################################

    @classmethod
    def from_file(cls, html_file):
        with open(html_file, 'rb') as f:
            html = f.read()

        return cls(html=html)

    #### 'View' protocol ######################################################

    #: The base url for all resources (relative urls are resolved corresponding 
    #: to the current working directory).
    base_url = Str

    #: The HTML for the *body* of the view's document.
    body_html = Str

    #: The HTML for the *head* of the view's document.
    head_html = Str

    #: The HTML for the entire document.
    html = Str
    def _html_default(self):
        """ Get the default HTML document for the given model. """

        html = DOCUMENT_HTML_TEMPLATE.format(
            body_html = self.body_html,
            head_html = self.head_html
        )

        return html

    def show(self, **context):
        """ Create and show a view of the given context. """

        from jigna.core.html_widget import HTMLWidget
        from jigna.core.wsgi import FileLoader

        widget = HTMLWidget(
            root_paths = {
                'jigna': FileLoader(
                    root = join(abspath(dirname(__file__)), 'resources')
                )
            },
            open_externally = True,
            debug = True
        )

        from jigna.qt_server import QtServer

        self._server = QtServer(
            base_url = join(os.getcwd(), self.base_url),
            context  = context,
            html     = self.html
        )

        self._server.connect(widget)
        widget.control.show()

        return

    def serve(self, port=8888, **context):
        """ Serve the view of the given context on the given port. """

        from jigna.web_server import WebServer

        self._server = WebServer(
            base_url = join(os.getcwd(), self.base_url),
            context  = context,
            html     = self.html,
            port     = port
        )
        self._server.serve()

        return

    #### Private protocol #####################################################

    #: The server that manages the objects shared via the bridge.
    _server = Instance(Server)

#### EOF ######################################################################
