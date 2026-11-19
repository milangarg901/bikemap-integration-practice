"""Run one interview checkpoint against an isolated local service."""
import argparse
import json
import subprocess
import sys
import tempfile
from http.server import HTTPServer
from pathlib import Path
from threading import Thread

from map_service import Handler, render

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(part, out, server):
    address = f"http://127.0.0.1:{server.server_port}"

    def run(ride, base_url=address, success=True):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "ride.py"), str(part), "--ride", str(ride),
             "--out", str(out), "--base-url", base_url],
            cwd=ROOT, capture_output=True, text=True, timeout=20)
        if success:
            require(completed.returncode == 0, completed.stderr.strip() or completed.stdout.strip() or "Client exited unsuccessfully")
        else:
            require(completed.returncode != 0, "Client reported success after HTTP failure")
        return completed.stdout

    if part == 2:
        run("data/canal.geojson")
        target = out / "base.png"
        require(target.read_bytes() == render({}), "base.png differs from the service response")
        run("data/canal.geojson", address + "/missing", success=False)
        require(target.read_bytes() == render({}), "HTTP failure overwrote base.png")
        return

    jobs = []
    landmarks = json.loads((ROOT / "data/landmarks.json").read_text())
    for ride, nearest, sample in [("canal", "Ferry Steps", 361), ("short", "Clock Court", 1)]:
        filename = ROOT / "data" / (ride + ".geojson")
        doc = json.loads(filename.read_text())
        points = [{"lat": p[1], "lon": p[0]} for p in doc["features"][0]["geometry"]["coordinates"]]
        marker = next(p for p in landmarks if p["name"] == nearest)
        meeting = {"landmark": nearest, "sample": sample}
        layers = {"path": points, "markers": [{"lat": marker["lat"], "lon": marker["lon"]}]}
        if part == 5:
            jobs.append((meeting, render(layers)))
            continue
        stdout = run(filename)
        if part == 1:
            records = [json.loads(line) for line in stdout.splitlines() if line.strip()]
            require(records == points[:10], f"Unexpected preview for {ride}")
        if part == 3:
            require((out / "route.png").read_bytes() == render({"path": points}), f"Route image mismatch for {ride}")
            require(server.last_counts == (len(points), 0), f"Expected all {len(points)} path points and zero markers")
        if part == 4:
            require(json.loads(stdout) == meeting, f"Wrong meeting point or sample for {ride}")
            require((out / "meeting.png").read_bytes() == render(layers), f"Wrong route or marker for {ride}")

    if part == 5:
        lines = run(ROOT / "data/batch.json").splitlines()
        records = [json.loads(line) for line in lines if line.strip()]
        expected = []
        for name, index in [("saturday", 0), ("skills-clinic", 1), ("sunday", 0)]:
            info, image = jobs[index]
            expected.append({"name": name, **info})
            require((out / (name + ".png")).read_bytes() == image, f"Map mismatch for {name}")
        require(records == expected, "Check job order, name, landmark and sample")
        require(server.posts == 2, f"Expected 2 POSTs, received {server.posts}")


class CheckHandler(Handler):
    def log_message(self, fmt, *args):
        if fmt == "path=%d markers=%d":
            self.server.last_counts = args

    def do_POST(self):
        self.server.posts += 1
        super().do_POST()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", type=int, choices=range(1, 6))
    part = parser.parse_args().part
    with tempfile.TemporaryDirectory() as temp, HTTPServer(("127.0.0.1", 0), CheckHandler) as server:
        server.posts = 0
        server.last_counts = None
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            check(part, Path(temp) / "output", server)
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            sys.exit(f"Part {part} FAIL: {exc}")
        finally:
            server.shutdown()
            worker.join()
    print(f"Part {part} PASS")
