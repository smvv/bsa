#!/usr/bin/env python
from config import proxy_url, default_viewport, default_dataset
from templates import templates
from processors import gzip_response #, load_sqlalchemy
import web

urls = (proxy_url + '/?', 'index',  
        # <base_url>/view/<start>/<end>/<scale>/<threshold>
        proxy_url + '/view/%d/%d/%d/%d', 'view')

app = web.application(urls, globals())
app.add_processor(gzip_response)
#app.add_processor(load_sqlalchemy)

class index:
    def GET(self):
        return templates.index(default_dataset, default_viewport)

if __name__ == '__main__':
    app.run()
