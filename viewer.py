#!/usr/bin/env python
from config import base_url, default_viewport, default_dataset
from templates import templates
from processors import gzip_response #, load_sqlalchemy
import web

urls = (base_url + '/', 'index',  
        # <base_url>/view/<start>/<end>/<scale>/<threshold>
        base_url + '/view/%d/%d/%d/%d', 'view')

app = web.application(urls, globals())
app.add_processor(gzip_response)
#app.add_processor(load_sqlalchemy)

class index:
    def GET(self):
        return templates.index(default_dataset, default_viewport)

if __name__ == '__main__':
    app.run()

def render_html(processes):
    template = """<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Build order analysis</title>
    <link rel="stylesheet" type="text/css" href="build_order.css"/>
    <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.2/jquery.min.js"></script>
    <script type="text/javascript" src="build_order.js"></script>
  </head>
  <body>
    <h1>Build system analysis for <tt>js/src</tt></h1>
    <div id="details">
        %(details)s
        <div id="process"></div>
    </div>
    <div id="waterfall">%(waterfall)s</div>
    <script type="text/javascript">process_tasks = %(process_tasks)s</script>
  </body>
</html>"""

    viewport_start = 0
    viewport_end = 40000 # 8000
    viewport_scale = 1.0 / 20

    duration_threshold = 100

    html = ''

    details = '<p>viewport from %.3f sec up to %.3f sec.</p>' \
            % (viewport_start / 1000.0, viewport_end / 1000.0)
    details += '<p>scale: %.2f ms/pixel and duration threshold: %.3f sec.</p>' \
            % (1 / viewport_scale, duration_threshold / 1000.0)


    displayed_pids = []

    for pid, tasks in processes.iteritems():

        start = tasks[0].start

        if start > viewport_end:
            break

        end = tasks[-1].end

        if end < viewport_start:
            continue

        if end - start < duration_threshold:
            continue

        start = max(viewport_start, start)
        end = min(viewport_end, end)

        left = (start - viewport_start) * viewport_scale
        width = (end - start) * viewport_scale

        process_type = parse_process_type(tasks)

        html += '<div id=p%s class=%s' \
                ' style="margin-left:%dpx;width:%dpx;"></div>\n' \
                % (pid, process_type, left, width)

        displayed_pids.append(pid)

    process_tasks = {}
    
    for pid in displayed_pids:
        process_tasks[pid] = processes[pid]

    process_tasks = JSONProcessEncoder().encode(process_tasks)

    print template % {'waterfall': html, 'details': details,
                      'process_tasks': process_tasks}

