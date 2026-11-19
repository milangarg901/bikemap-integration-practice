# BikeMap integration interview

A cycling club records rides as GPS samples. Before a ride appears in the club newsletter, an editor wants to inspect the recording, see the route on a map and identify a useful stop along the way. You are taking over a small Python client. Work in `ride.py`. A teammate has already written the map service.

This is an independently written practice interview. Set aside 45 minutes for a first run. Start with the request below. When it works, open the next brief in `rounds/`. Each brief extends the same client. You can run earlier parts again at any point.

## Getting started

Use Python 3.10 or newer. The project uses the standard library. From the repository root, run:

```powershell
python ride.py 1
```

On a fresh clone, the starter tells you where to begin. The command already accepts a part number, a ride file, an output directory and a service address. Run `python ride.py --help` to see the defaults. The supplied paths work from the repository root. Use your usual editor and Python documentation.

## Your first request

An editor suspects the coordinates in the preview are reversed. Before adding a map, give them a way to inspect a ride in their terminal.

Running `python ride.py 1` should print the first ten recorded positions from `data/canal.geojson`, in travel order, one JSON object per line. Each object must have numeric fields named `lat` and `lon`. The input uses GeoJSON coordinate order, longitude followed by latitude. A third number, when present, is elevation. The editor only wants the two horizontal coordinates.

The first line for the default ride should represent this position:

```json
{"lat": 28.602, "lon": 77.201}
```

All supplied rides are GeoJSON FeatureCollections containing one LineString feature. Keep repeated positions. If a recording has fewer than ten samples, print all available positions. Support the supplied `--ride` argument so the editor can preview another ride without changing your source.

Demonstrate the short recording with `python ride.py 1 --ride data/short.geojson`. Explain how you checked the first point and why the second coordinate in the file becomes the latitude. Run `python check.py 1` for a repeatable check.

## Continuing the session

Open `rounds/02.md` when the preview works. Start the map service in a second terminal when the brief asks for it. Later requests use the same local service and the contract in `API.md`. Keep each earlier command usable as you extend the client.

At the end of the session, show the last part you completed, one input you used to test it and one assumption you would revisit for a much longer ride.
