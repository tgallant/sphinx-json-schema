# -*- coding: utf-8 -*-


import os.path

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.directives.code import container_wrapper

from .loader import JsonSchemaLoader


class JsonSchema(Directive):
    optional_arguments = 1
    has_content = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        assert self.name == 'json-schema'

        try:
            file_or_url = self.arguments[0]
            if not file_or_url.startswith('http') and not os.path.isabs(file_or_url):
                # file relative to the path of the current rst file
                dname = os.path.dirname(self.state_machine.input_lines.source(0))
                path = os.path.join(dname, file_or_url)
                if os.path.exists(path):
                    file_or_url = path
                else:
                    root_dir = self.state.document.settings.env.config.json_schema_root_dir
                    if root_dir is None:
                        raise IndexError
                    # no file at relative location, try loading from root directory
                    file_or_url = os.path.join(root_dir, file_or_url)
                    if not os.path.exists(file_or_url):
                        raise IndexError
        except IndexError:
            file_or_url = None

        if file_or_url:
            self.schema = JsonSchemaLoader(file_or_url)
        elif self.content:
            self.schema = JsonSchemaLoader(self.content, self.state_machine.input_lines.source(0))
        else:
            self.schema = None

    def run(self):
        if not self.schema:
            return []

        schema = self.schema.schema
        properties = schema.get('properties', {})
        sorted_props = {k: properties[k] for k in sorted(properties)}
        required_properties = schema.get('required', [])
        content = []
        for title, prop in sorted_props.items():
            section = nodes.section(ids=[title], names=[title])
            titlenode = nodes.title(title, title)
            section += titlenode
            description = prop.get('description', '')
            desc_lines = description.split('\n')
            desc = nodes.description()
            for line in desc_lines:
                desc_text, desc_msg = self.state.inline_text(line, self.lineno)
                p = nodes.line()
                for text_node in desc_text:
                    p += text_node
                desc += p
            section += desc
            is_required = title in required_properties
            required = nodes.description()
            required_tmpl = f'**Required**: {is_required}'
            required_text, required_msg = self.state.inline_text(required_tmpl, self.lineno)
            for text_node in required_text:
                required += text_node
            section += required
            default_value = prop.get('default')
            if default_value:
                default = nodes.description()
                default_tmpl = f'**Default**: {default_value}'
                default_text, default_msg = self.state.inline_text(default_tmpl, self.lineno)
                for text_node in default_text:
                    default += text_node
                section += default
            content.append(section)
        return content
