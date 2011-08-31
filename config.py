base_url = ''  # http://doma.in/foo/
               #               ^^^^ = base url (no trailing slash)

# web directory where processed strace/pymake output is written to.
data_url = '/static/data'  

default_dataset = 'strace.json'

default_viewport = {
        # inclusive end of viewport, in milliseconds.
        'end': 40000,

        # start of viewport, in milliseconds.
        'start': 0,

        # scale of the viewport, in milliseconds per pixel.
        'scale': 1.0 / 20,

        # minimal duration to show it, in milliseconds.
        'threshold': 100,
    }
