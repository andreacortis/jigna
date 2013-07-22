# Standard library imports
from textwrap import dedent
from mako.template import Template

# Enthougt library imports.
from pyface.qt import QtWebKit, QtGui
from traitsui.api import View, Item

# Local imports.
from basic_editors import BasicEditor
import jigna.registry as registry

###############################################################################
# TraitsUIWidget class.
###############################################################################
class TraitsUIWidget(QtGui.QWidget):
    def __init__(self, model, trait_name, view=None, editor=None, width=300,
                 height=300):
        """
        Parameters
        ----------

        model : The model being edited.

        trait_name: The trait name of the model for which we are an editor.

        view : Optional view to view the trait.

        editor: Optional editor to use to generate default view.
            This is not used when an explicit view is supplied.

        width: int: Optional width of widget.

        height: int: Optional height of widget.
        """
        super(TraitsUIWidget, self).__init__()
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        if view is not None:
            if view.height > 0:
                height = view.height
            if view.width > 0:
                width = view.width
        else:
            if editor is not None:
                view = View(Item(trait_name, style='custom', show_label=False,
                                 editor=editor),
                            width=width, height=height, resizable=True)
            else:
                view = View(Item(trait_name, style='custom', show_label=False),
                            width=width, height=height, resizable=True)

        self.setMinimumWidth(width)
        self.setMinimumHeight(height)
        e = model.edit_traits(view=view, parent=self, kind='subpanel')
        self.traits_ui = e
        layout.addChildWidget(e.control)


###############################################################################
# TraitsUIWidgetFactory class.
###############################################################################
class TraitsUIWidgetFactory(QtWebKit.QWebPluginFactory):

    MIME_TYPE = "application/x-traitsuiwidget"

    instance = None

    registry = {}

    def __init__(self, webview):
        """
        Parameters
        -----------

        webview: the webview in which our widget is embedded.
        """

        super(TraitsUIWidgetFactory, self).__init__(webview)
        self.webview = webview

    def plugins(self):
        plugin = QtWebKit.QWebPluginFactory.Plugin()
        plugin.name = "TraitsUIWidget"
        plugin.description = "Embedded TraitsUI widget"
        mimeType = QtWebKit.QWebPluginFactory.MimeType()
        mimeType.name = self.MIME_TYPE
        mimeType.description = "Embedded TraitsUI widget"
        mimeType.fileExtensions = []
        plugin.mimeTypes = [mimeType]
        return [plugin]

    def create(self, mimeType, url, argNames, argValues):
        if mimeType != self.MIME_TYPE:
            return None

        # Put the args in a dictionary so it is easy to fetch the one(s) we
        # are interested in below. These names/values come from the
        # <object> tag attributes or the <param> tags inside the <object> tag.
        args = dict()
        for name, value in zip(argNames, argValues):
            args[name] = value

        model_name = args.get('model_name', '')
        trait_name = args.get('trait_name', '')
        key = '%s.%s' % (model_name, trait_name)
        widget_factory = self.__class__.registry.get(key)
        if widget_factory is not None:
            plugin_widget = widget_factory(model_name, args)
            return plugin_widget
        else:
            return None

    @classmethod
    def setup_session(cls, webview):
        if cls.instance is None:
            # Turn on allowing plugins
            global_settings = QtWebKit.QWebSettings.globalSettings()
            global_settings.setAttribute(
                        QtWebKit.QWebSettings.PluginsEnabled, True)
            global_settings.setAttribute(
                        QtWebKit.QWebSettings.DeveloperExtrasEnabled, True)

            page = webview.page()
            factory = cls(webview)
            cls.instance = factory
            page.setPluginFactory(factory)

    @classmethod
    def register_widget_factory(cls, model_name, trait_name, widget_factory):
        """
        Parameters
        -----------

        model_name: str: The unique name of the model we are editing.

        trait_name: str: The name of the trait that is being edited.

        widget_factory: callable: A factory for our widget.

            This callable is passed the arguments from the object tag used in
            the HTML.
        """
        key = '%s.%s' % (model_name, trait_name)
        cls.registry[key] = widget_factory

###############################################################################
# TraitsUIEditor class.
###############################################################################
class TraitsUIEditor(BasicEditor):

    def html(self):
        template_str = dedent("""
                        <div class="editor ${editor_name}">
                        <object type="application/x-traitsuiwidget"
                                model_name=${model_name} trait_name="${trait_name}"
                                width="100%" height="60%">
                        </object>
                        </div>
                       """)
        model_name = registry.registry['model_names'][id(self.obj)]
        return Template(template_str).render(model_name=model_name,
                                        trait_name=self.tname,
                                        editor_name=self.__class__.__name__)

    def setup_session(self, session=None):
        webview = session.widget.control
        TraitsUIWidgetFactory.setup_session(webview)
        model_name = registry.registry['model_names'][id(self.obj)]
        TraitsUIWidgetFactory.register_widget_factory(model_name, self.tname,
                                                      self.create_widget)

    def _get_int(self, name, args):
        if name in args:
            try:
                value = int(args.get(name))
                return value
            except ValueError:
                return -10000
        return -10000

    def get_size(self, args):
        """Return width and height.  None if they are defaults.
        """
        return self._get_int('width', args), self._get_int('height', args)