# Static map service

Start `python map_service.py` (optional `--port 8772`). Default address: `http://127.0.0.1:8771`. A browser can visit `/health` to verify connectivity.

## POST /staticmap

Send UTF-8 JSON with `Content-Type: application/json`. For a base map, send `{}`. Optional fields:

| Field | Type | Meaning |
|---|---|---|
| `path` | array | Ordered points connected by a blue line |
| `markers` | array | Positions drawn as red circles over the path |

Each point is an object with numeric `lat` and `lon`. Example:

```json
{"path":[{"lat":28.602,"lon":77.201},{"lat":28.605,"lon":77.209}],"markers":[]}
```

The fixed viewport covers latitude 28.595–28.635 and longitude 77.195–77.245. All fixtures fit. A successful request returns HTTP 200 and a 512 × 384 `image/png` body. Write those bytes directly to disk. Invalid fields, coordinates or JSON return 400, oversized bodies return 413, and an incorrect content type returns 415. Error bodies are JSON objects with an `error` message. No API key is needed.
