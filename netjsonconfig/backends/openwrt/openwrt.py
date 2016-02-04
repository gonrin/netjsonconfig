import json
import re
import six
import gzip
import tarfile
import zipfile
from io import BytesIO
from copy import deepcopy

from jsonschema import validate
from jsonschema.exceptions import ValidationError as JsonSchemaError
from jinja2 import Environment, PackageLoader

from . import renderers
from .schema import schema
from ...utils import merge_config
from ...exceptions import ValidationError

DEFAULT_FILE_MODE = '644'
FILE_SECTION_DELIMITER = '# ------ files ------ #'


class OpenWrt(object):
    """ OpenWrt Backend """
    schema = schema
    renderers = [
        renderers.SystemRenderer,
        renderers.NetworkRenderer,
        renderers.WirelessRenderer,
        renderers.DefaultRenderer
    ]

    def __init__(self, config, templates=[]):
        """
        :param config: ``dict`` containing valid **NetJSON DeviceConfiguration**
        :param templates: ``list`` containing **NetJSON** dictionaries that will be
                          used as a base for the main config, defaults to empty list
        :raises TypeError: raised if ``config`` is not of type ``dict`` or if
                           ``templates`` is not of type ``list``
        """
        # perform deepcopy to avoid modifying the original config argument
        config = deepcopy(self._load(config))
        # allow omitting NetJSON type
        if 'type' not in config:
            config.update({'type': 'DeviceConfiguration'})
        self.config = self._merge_config(config, templates)
        self.env = Environment(loader=PackageLoader('netjsonconfig.backends.openwrt',
                                                    'templates'),
                               trim_blocks=True)

    def _load(self, config):
        """ loads config from string or dict """
        if isinstance(config, six.string_types):
            try:
                config = json.loads(config)
            except ValueError:
                pass
        if not isinstance(config, dict):
            raise TypeError('config block must be an istance '
                            'of dict or a valid NetJSON string')
        return config

    def _merge_config(self, config, templates):
        """ merges config with templates """
        # type check
        if not isinstance(templates, list):
            raise TypeError('templates argument must be an instance of list')
        # merge any present template with main configuration
        base_config = {}
        for template in templates:
            template = self._load(template)
            base_config = merge_config(base_config, template)
        if base_config:
            return merge_config(base_config, config)
        return config

    def render(self, files=True):
        """
        Converts the configuration dictionary into the native OpenWRT UCI format.

        :param files: whether to include "additional files" in the output or not;
                      defaults to ``True``
        :returns: string with output
        """
        self.validate()
        output = ''
        # render config
        for renderer_class in self.renderers:
            renderer = renderer_class(self)
            additional_output = renderer.render()
            # add an additional new line
            # to separate blocks
            if output and additional_output:
                output += '\n'
            output += additional_output
        if files:
            # render files
            files_output = self._render_files()
            if files_output:
                output += files_output.replace('\n\n\n', '\n\n')  # max 3 \n
        return output

    def _render_files(self):
        """ renders "additional files", used in main render method """
        output = ''
        # render files
        files = self.config.get('files', [])
        # add delimiter
        if files:
            output += '\n{0}\n\n'.format(FILE_SECTION_DELIMITER)
        for f in files:
            if isinstance(f['contents'], list):
                contents = '\n'.join(f['contents'])
            else:
                contents = f['contents']
            path = f['path']
            mode = f.get('mode', DEFAULT_FILE_MODE)
            # add file to output
            file_output = '# path: {0}\n'\
                          '# mode: {1}\n\n'\
                          '{2}\n\n'.format(path, mode, contents)
            output += file_output
        return output

    def validate(self):
        try:
            validate(self.config, self.schema)
        except JsonSchemaError as e:
            raise ValidationError(e)

    def json(self, *args, **kwargs):
        """
        returns a string formatted in **NetJSON**;
        performs validation before returning output;

        ``*args`` and ``*kwargs`` will be passed to ``json.dumps``;

        :returns: string
        """
        self.validate()
        return json.dumps(self.config, *args, **kwargs)

    @classmethod
    def get_packages(cls):
        return [r.get_package() for r in cls.renderers]

    def generate(self):
        
        zip = zipfile.ZipFile('zipfile_writestr.zip',mode='w',compression=zipfile.ZIP_DEFLATED,)
        self._generate_contents(zip)
        

    def _generate_contents(self, zip):
        """
        Adds configuration files to tarfile instance.

        :param tar: tarfile instance
        :returns: None
        """
        uci = self.render(files=False)
        
        # create a list with all the packages (and remove empty entries)
        packages = re.split('package ', uci)
        if '' in packages:
            packages.remove('')
        # for each package create a file with its contents in /etc/config
        for package in packages:
            lines = package.split('\n')
            package_name = lines[0]
            text_contents = '\n'.join(lines[2:])
            zip.writestr('etc/config/{0}'.format(package_name), text_contents.encode('utf-8'))
            

    def write(self, name, path='./'):
        """
        Like ``generate`` but writes to disk.

        :param name: file name, the tar.gz extension will be added automatically
        :param path: directory where the file will be written to, defaults to ``./``
        :returns: None
        """
        
        file_name = '{0}.zip'.format(name)
        if not path.endswith('/'):
            path += '/'
       
        zip = zipfile.ZipFile('{0}{1}'.format(path, file_name),mode='w',compression=zipfile.ZIP_DEFLATED,)
        self._generate_contents(zip)
        zip.close()