#from models import engine
#from sqlalchemy.orm import scoped_session, sessionmaker
import cStringIO
import gzip
import web

#def load_sqlalchemy(handler):
#    web.ctx.orm = scoped_session(sessionmaker(bind=engine))
#    return handler()

def gzip_response(handler):
    resp = handler()

    accepts = web.ctx.env.get('HTTP_ACCEPT_ENCODING', None)

    if not accepts or accepts.find('gzip') == -1:
        return resp 

    resp = str(resp)

    web.webapi.header('Content-Encoding', 'gzip')

    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', fileobj=zbuf, compresslevel=9)
    zfile.write(resp)
    zfile.close()
    data = zbuf.getvalue()

    web.webapi.header('Content-Length', str(len(data)))
    web.webapi.header('Vary','Accept-Encoding', unique=True)
    return data
