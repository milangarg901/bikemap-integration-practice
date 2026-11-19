"""Supplied offline schematic map renderer and loopback HTTP service."""
import argparse
import json
import math
import struct
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer


WIDTH, HEIGHT = 512, 384


def pixel(point):
    if not isinstance(point, dict) or set(point) != {"lat", "lon"}:
        raise ValueError("Each point needs lat and lon")
    lat, lon = point["lat"], point["lon"]
    if any(type(n) not in (int, float) for n in (lat, lon)):
        raise ValueError("Coordinates must be numbers")
    if not (28.595 <= lat <= 28.635 and 77.195 <= lon <= 77.245):
        raise ValueError("Coordinate outside the viewport")
    return round((lon - 77.195) / 0.05 * (WIDTH-1)), round((28.635 - lat) / 0.04 * (HEIGHT-1))


def render(payload):
    if not isinstance(payload, dict) or set(payload) - {"path", "markers"}:
        raise ValueError("Expected a map object with optional path and markers")
    layers = []
    for key in ("path", "markers"):
        points = payload.get(key, [])
        if not isinstance(points, list) or len(points) > 5000:
            raise ValueError(f"{key} must be an array of at most 5000 points")
        layers.append([pixel(p) for p in points])
    path, markers = layers
    rows = []
    for y in range(HEIGHT):
        row = bytearray()
        canal = 130 + round(35 * math.sin(y / 70))
        for x in range(WIDTH):
            color = b"\xe9\xe7\xd9"
            if x % 43 < 3 or y % 31 < 3:
                color = b"\xff\xfd\xf4"
            if abs(x - canal) < 11:
                color = b"\x99\xcd\xda"
            row.extend(color)
        rows.append(row)

    def dot(x, y, radius, color):
        for yy in range(max(0, y-radius), min(HEIGHT, y+radius+1)):
            for xx in range(max(0, x-radius), min(WIDTH, x+radius+1)):
                if (xx-x)**2 + (yy-y)**2 <= radius**2:
                    rows[yy][3*xx:3*xx+3] = color

    blue = b"\x22\x56\xad"
    if path:
        dot(*path[0], 2, blue)
    for (x, y), (u, v) in zip(path, path[1:]):
        steps = max(abs(u-x), abs(v-y), 1)
        for step in range(1, steps+1):
            dot(round(x+(u-x)*step/steps), round(y+(v-y)*step/steps), 2, blue)
    for x, y in markers:
        dot(x, y, 6, b"\xc5\x40\x36")

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data)))

    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    pixels = b"".join(b"\x00" + row for row in rows)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, content_type, data):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def error(self, status, message):
        self.reply(status, "application/json", json.dumps({"error": message}).encode())

    def do_GET(self):
        if self.path == "/health":
            self.reply(200, "application/json", b'{"status":"ok"}')
        else:
            self.error(404, "Unknown endpoint")

    def do_POST(self):
        if self.path != "/staticmap":
            return self.error(404, "Unknown endpoint")
        if self.headers.get_content_type() != "application/json":
            return self.error(415, "Use application/json")
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 0 or size > 1_000_000:
                return self.error(413, "Request too large")
            payload = json.loads(self.rfile.read(size))
            image = render(payload)
        except (ValueError, RecursionError) as exc:
            return self.error(400, str(exc))
        self.log_message("path=%d markers=%d", len(payload.get("path", [])), len(payload.get("markers", [])))
        self.reply(200, "image/png", image)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8771)
    args = parser.parse_args()
    with HTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Map service listening on http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
