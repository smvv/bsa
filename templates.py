from config import base_url, data_url
import web

builtins = {
    'base_url': base_url,
    'data_url': data_url,
    'True': True,
    'False': False,
}

templates_dir = 'tpl'
templates = web.template.render(templates_dir, builtins=builtins)
