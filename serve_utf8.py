# -*- coding: utf-8 -*-
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

DIRECTORY = r"C:\Users\Vetz\Desktop\panini-offline"

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=DIRECTORY, **k)

    def end_headers(self):
        if self.path.endswith((".html", "/")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        t = super().guess_type(path)
        if t in ("text/html", "text/css") or str(path).endswith((".html", ".css")):
            return t.split(";")[0] + "; charset=utf-8"
        return t

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 5600))
    print("serving %s on %d (utf-8)" % (DIRECTORY, port))
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
