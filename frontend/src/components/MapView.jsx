import { useEffect, useMemo, useRef, useState } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import buildings from "../data/buildings.json";
import { postJson } from "../lib/api";
import { pointFor } from "../lib/walking";

const byCode = Object.fromEntries(buildings.map((b) => [b.code, b]));
const CENTER = [40.4268, -86.9135];

function FlyTo({ target }) {
  const map = useMap();
  useEffect(() => {
    if (!target) return;
    map.flyTo([target.lat, target.lon], 17, { duration: 0.6 });
  }, [map, target]);
  return null;
}

function FitStops({ positions }) {
  const map = useMap();
  const key = positions.map((p) => p.join(",")).join("|");
  useEffect(() => {
    if (positions.length >= 2) {
      map.fitBounds(positions, { padding: [36, 36], maxZoom: 17 });
    } else if (positions.length === 1) {
      map.setView(positions[0], 17);
    }
  }, [map, key]);
  return null;
}

export default function MapView({ events, onLocate }) {
  const [ready, setReady] = useState(false);
  const [query, setQuery] = useState("");
  const [pin, setPin] = useState(null);
  const [searchError, setSearchError] = useState("");
  const [route, setRoute] = useState([]);
  const [routeNote, setRouteNote] = useState("");
  useEffect(() => setReady(true), []);

  const stops = useMemo(
    () =>
      events
        .map((ev) => {
          const point = pointFor(ev, byCode);
          if (!point) return null;
          return { ...ev, lat: point.lat, lon: point.lon, name: byCode[ev.building]?.name || ev.location || ev.building };
        })
        .filter(Boolean),
    [events],
  );
  const stopKey = stops.map((s) => `${s.id}:${s.lat}:${s.lon}`).join("|");
  const line = route.length > 1 ? route : stops.map((s) => [s.lat, s.lon]);

  const geocodeTried = useRef(new Set());
  useEffect(() => {
    const unique = events.filter((ev) => {
      if (pointFor(ev, byCode) || geocodeTried.current.has(ev.id)) return false;
      return Boolean((ev.location || ev.building || "").trim());
    });
    if (!unique.length) return undefined;
    unique.forEach((ev) => geocodeTried.current.add(ev.id));
    let cancelled = false;
    (async () => {
      for (const ev of unique) {
        try {
          const found = await postJson("/geocode", { text: ev.location || ev.building });
          if (!cancelled && found?.lat != null) onLocate?.(ev.id, found);
        } catch {
          // Unknown buildings stay off the map.
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [events, onLocate]);

  useEffect(() => {
    if (stops.length < 2) {
      setRoute([]);
      setRouteNote(stops.length === 1 ? "One mapped stop. Add another class to draw a walking route." : "");
      return undefined;
    }
    const controller = new AbortController();
    setRouteNote("Updating walking route…");
    postJson(
      "/route",
      { waypoints: stops.map((stop) => ({ lat: stop.lat, lon: stop.lon, name: stop.title })) },
      controller.signal,
    )
      .then((data) => {
        setRoute(data.coordinates || []);
        const meters = Number(data.distance_m);
        const seconds = Number(data.time_s);
        if (Number.isFinite(meters) && Number.isFinite(seconds)) {
          setRouteNote(`Walk ${Math.round(meters)} m · ${Math.max(1, Math.round(seconds / 60))} min (Geoapify)`);
        } else {
          setRouteNote("Walking path from Geoapify.");
        }
      })
      .catch((err) => {
        if (err?.name === "AbortError") return;
        setRoute([]);
        setRouteNote("Street route unavailable — showing straight campus hops.");
      });
    return () => controller.abort();
  }, [stopKey]);

  async function search(event) {
    event.preventDefault();
    setSearchError("");
    if (!query.trim()) return;
    try {
      const found = await postJson("/geocode", { text: query.trim() });
      setPin(found);
    } catch (err) {
      setSearchError(err.message);
    }
  }

  if (!ready) {
    return <div className="h-[420px] rounded-xl border border-tan/15 bg-ink-soft" />;
  }

  return (
    <div>
      <form onSubmit={search} className="mb-2 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Geocode a dorm, hall, or address"
          className="flex-1 rounded-md border border-tan-deep/30 bg-ink px-2 py-1.5 text-sm text-cream"
        />
        <button type="submit" className="rounded-md bg-orange px-3 py-1.5 text-sm font-semibold text-ink hover:bg-orange-hot">
          Find
        </button>
      </form>
      {searchError && <p className="mb-2 text-xs text-[#ffb4a2]">{searchError}</p>}
      {routeNote && <p className="mb-2 text-xs text-tan-deep">{routeNote}</p>}
      <div className="overflow-hidden rounded-xl border border-tan/15">
        <MapContainer center={CENTER} zoom={16} className="h-[420px] w-full" scrollWheelZoom>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <FitStops positions={stops.map((s) => [s.lat, s.lon])} />
          <FlyTo target={pin} />
          {buildings.map((b) => (
            <CircleMarker
              key={b.code}
              center={[b.lat, b.lon]}
              radius={4}
              pathOptions={{ color: "#c4a574", fillColor: "#e8d5b7", fillOpacity: 0.35, weight: 1 }}
            >
              <Popup>
                <strong>{b.code}</strong>
                <br />
                {b.name}
              </Popup>
            </CircleMarker>
          ))}
          {line.length > 1 && (
            <Polyline positions={line} pathOptions={{ color: "#e85d04", weight: route.length > 1 ? 5 : 3, opacity: 0.9 }} />
          )}
          {stops.map((s, i) => (
            <CircleMarker
              key={`${s.id}-${i}`}
              center={[s.lat, s.lon]}
              radius={9}
              pathOptions={{
                color: s.source === "instagram" ? "#e85d04" : "#c4a574",
                fillColor: s.source === "instagram" ? "#f48c06" : "#e8d5b7",
                fillOpacity: 0.95,
                weight: 2,
              }}
            >
              <Popup>
                <strong>{s.title}</strong>
                <br />
                {s.start}–{s.end} · {s.building}
                <br />
                {s.name}
              </Popup>
            </CircleMarker>
          ))}
          {pin && (
            <CircleMarker center={[pin.lat, pin.lon]} radius={8} pathOptions={{ color: "#f48c06", fillColor: "#e85d04", fillOpacity: 1 }}>
              <Popup>
                <strong>{pin.name}</strong>
              </Popup>
            </CircleMarker>
          )}
        </MapContainer>
      </div>
    </div>
  );
}
