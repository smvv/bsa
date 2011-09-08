# http://doma.in/foo/
#               ^^^^ = base url (no trailing slash)
base_url = '/bsa'

# Used for internal rerouting (lighttpd, apache).
proxy_url = '/viewer.py'

# web directory where processed strace/pymake output is written to.
data_url = base_url +  '/static/data'  

default_dataset = 'bsa.json'

default_viewport = {
        # inclusive end of viewport, in milliseconds.
        'end': 40000,

        # start of viewport, in milliseconds.
        'start': 0,

        # scale of the viewport, in milliseconds per pixel.
        'scale': 1.0 / 10,

        # minimal duration to show the process in the viewer, in seconds.
        'threshold': 0.1,
    }
