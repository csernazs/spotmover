import sys
import socket
import errno

PY3 = sys.version_info.major == 3

if PY3:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qsl
else:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from urlparse import urlparse, parse_qsl

from spotipy import oauth2


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_s = urlparse(self.path).query
        form = dict(parse_qsl(query_s))

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if "code" in form:
            self.server.auth_code = form["code"]
            self.server.error = None
            status = "successful"
        elif "error" in form:
            self.server.error = form["error"]
            self.server.auth_code = None
            status = "failed ({})".format(form["error"])
        else:
            self._write("<html><body><h1>Invalid request</h1></body></html>")
            return

        self._write(
            "<html><body><h1>Authentication status: {}</h1>Now you can close this window.</body></html>".format(status))

    def _write(self, text):
        return self.wfile.write(text.encode("utf-8"))

    def log_message(self, format, *args):
        return


def start_local_http_server(port, handler=RequestHandler):
    while True:
        try:
            server = HTTPServer(("127.0.0.1", port), handler)
        except socket.error as err:
            if err.errno != errno.EADDRINUSE:
                raise
        else:
            server.auth_code = None
            return server


def obtain_token_localhost(username, client_id, client_secret, redirect_uri, cache_path=None, scope=None):
    cache_path = cache_path or ".cache-" + username

    sp_oauth = oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, cache_path=cache_path)

    token_info = sp_oauth.get_cached_token()

    if token_info:
        return token_info['access_token']

    print("Proceeding with user authorization")
    auth_url = sp_oauth.get_authorize_url()
    try:
        import webbrowser
        webbrowser.open(auth_url)
        print("Opened %s in your browser" % auth_url)
    except:
        print("Please navigate here: %s" % auth_url)

    url_info = urlparse(redirect_uri)
    netloc = url_info.netloc
    if ":" in netloc:
        port = int(netloc.split(":", 1)[1])
    else:
        port = 80

    server = start_local_http_server(port)
    server.handle_request()

    if server.auth_code:
        token_info = sp_oauth.get_access_token(server.auth_code)
        return token_info['access_token']
