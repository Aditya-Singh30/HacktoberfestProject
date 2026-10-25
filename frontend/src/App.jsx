import { useCallback, useEffect, useMemo, useState } from "react";
import AddEvent from "./components/AddEvent";
import AddSchedule from "./components/AddSchedule";
import AskSteamLine from "./components/AskSteamLine";
import MapView from "./components/MapView";
import Timeline from "./components/Timeline";
import buildings from "./data/buildings.json";
import { demoEvents } from "./data/demo";
import { newId, withGaps } from "./lib/walking";

const STORAGE_KEY = "steamline-events-v2";
const byCode = Object.fromEntries(buildings.map((b) => [b.code, b]));

function planningDay() {
  const date = new Date();
  const weekday = date.getDay();
  if (weekday === 0) date.setDate(date.getDate() + 1);
  if (weekday === 6) date.setDate(date.getDate() + 2);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function App() {
  const [day, setDay] = useState(planningDay());
  const [events, setEvents] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(events));
  }, [events]);

  const dayEvents = useMemo(
    () => withGaps(events.filter((ev) => ev.date === day), byCode),
    [events, day],
  );
  const tightCount = dayEvents.filter((ev) => ev.tight).length;

  function addEvent(ev) {
    setEvents((rows) => [...rows, { ...ev, id: ev.id || newId(), date: ev.date || day }]);
  }

  const locateEvent = useCallback((id, found) => {
    setEvents((rows) =>
      rows.map((row) =>
        row.id === id ? { ...row, lat: found.lat, lon: found.lon, location: row.location || found.name } : row,
      ),
    );
  }, []);

  return (
    <div className="min-h-screen bg-ink text-cream">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-6 lg:grid-cols-[300px_1fr]">
        <aside className="rounded-2xl border border-tan/10 bg-ink-soft p-4">
          <p className="text-[0.72rem] uppercase tracking-[0.18em] text-tan-deep">SteamLine · Purdue</p>
          <h1 className="mt-1 font-serif text-3xl text-tan">
            Today’s <span className="text-orange-hot">Line</span>
          </h1>
          <p className="mt-2 text-sm text-cream/70">
            Classes and club posts on one timeline and map. Your schedule never leaves this laptop.
          </p>
          <label className="mt-4 block text-xs text-tan-deep">
            Day
            <input
              type="date"
              value={day}
              onChange={(e) => setDay(e.target.value)}
              className="mt-1 w-full rounded-md border border-tan-deep/30 bg-ink px-2 py-1.5 text-sm text-cream"
            />
          </label>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() =>
                setEvents(demoEvents(day).map((ev) => ({ ...ev, id: newId() })))
              }
              className="rounded-md bg-orange px-2 py-2 text-xs font-semibold text-ink hover:bg-orange-hot"
            >
              Load demo data
            </button>
            <button
              type="button"
              onClick={() => setEvents((rows) => rows.filter((ev) => ev.date !== day))}
              className="rounded-md border border-tan-deep/40 px-2 py-2 text-xs text-tan hover:border-tan"
            >
              Clear day
            </button>
          </div>
          <AddSchedule day={day} onConfirm={addEvent} />
          <AddEvent day={day} onConfirm={addEvent} />
          <AskSteamLine day={day} events={dayEvents} />
        </aside>

        <main>
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-tan/15 pb-4">
            <div>
              <p className="text-[0.72rem] uppercase tracking-[0.18em] text-tan-deep">Dynamic view</p>
              <h2 className="font-serif text-2xl text-tan">Timeline + map</h2>
            </div>
            <span className="rounded-full border border-tan-deep px-3 py-1 text-xs text-tan">{day}</span>
          </div>

          {tightCount > 0 ? (
            <div className="mb-4 rounded-xl border-l-4 border-orange bg-gradient-to-r from-warn/20 to-orange/10 px-4 py-3 text-sm">
              <strong className="text-orange-hot">You won’t make it</strong>
              <span className="text-cream/80">
                {" "}
                — {tightCount} stop{tightCount === 1 ? "" : "s"} need more walk time than the gap.
              </span>
            </div>
          ) : dayEvents.length > 1 ? (
            <div className="mb-4 rounded-xl border border-ok/40 bg-ok/15 px-4 py-3 text-sm text-[#b7d4c0]">
              Gaps look walkable at 80 m/min.
            </div>
          ) : null}

          <div className="grid gap-6 xl:grid-cols-2">
            <Timeline
              events={dayEvents}
              onRemove={(id) => setEvents((rows) => rows.filter((ev) => ev.id !== id))}
            />
            <MapView events={dayEvents} onLocate={locateEvent} />
          </div>
        </main>
      </div>
    </div>
  );
}
