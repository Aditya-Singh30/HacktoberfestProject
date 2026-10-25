import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from "react-leaflet";
import buildings from "../data/buildings.json";

const byCode = Object.fromEntries(buildings.map((b) => [b.code, b]));
const CENTER = [40.4268, -86.9135];

export default function MapView({ events }) {
  const [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);

  const stops = events
    .map((ev) => {
      const b = byCode[ev.building];
      if (!b) return null;
      return { ...ev, lat: b.lat, lon: b.lon, name: b.name };
    })
    .filter(Boolean);

  const line = stops.map((s) => [s.lat, s.lon]);

  if (!ready) {
    return <div className="h-[420px] rounded-xl border border-tan/15 bg-ink-soft" />;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-tan/15">
      <MapContainer center={CENTER} zoom={16} className="h-[420px] w-full" scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {line.length > 1 && (
          <Polyline positions={line} pathOptions={{ color: "#e85d04", weight: 3, opacity: 0.85 }} />
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
      </MapContainer>
    </div>
  );
}
