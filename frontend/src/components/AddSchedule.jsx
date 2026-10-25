import { useState } from "react";
import EventCard from "./EventCard";
import { SAMPLE_SCHEDULE } from "../data/demo";
import { postJson } from "../lib/api";
import { newId } from "../lib/walking";

export default function AddSchedule({ day, onConfirm }) {
  const [text, setText] = useState(SAMPLE_SCHEDULE);
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notes, setNotes] = useState([]);
  const isWeekend = [0, 6].includes(new Date(`${day}T12:00:00`).getDay());

  async function extract() {
    setError("");
    setNotes([]);
    setLoading(true);
    try {
      const data = await postJson("/extract/schedule", { text, date: day });
      const events = (data.events || []).map((event) => ({ ...event, id: newId() }));
      setNotes(data.warnings || []);
      if (!events.length) throw new Error("No classes found in that paste. Check times, days, and building codes.");
      setPending(events);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2 className="mb-2 font-serif text-lg text-tan">Add schedule</h2>
      <p className="mb-2 text-xs text-tan-deep">Paste Brightspace / registrar text</p>
      {isWeekend && <p className="mb-2 text-xs text-tan-deep">This date is a weekend. Extraction still runs; classes that meet on weekdays are shown so you can review them.</p>}
      <textarea className="h-40 w-full rounded-lg border border-tan-deep/30 bg-ink p-2 text-sm text-cream" value={text} onChange={(event) => setText(event.target.value)} />
      <button type="button" disabled={loading || !text.trim()} onClick={extract} className="mt-2 w-full rounded-md bg-orange px-3 py-2 text-sm font-semibold text-ink hover:bg-orange-hot disabled:cursor-not-allowed disabled:opacity-60">
        {loading ? "Reading your schedule…" : "Extract schedule"}
      </button>
      {error && <p className="mt-2 text-xs text-[#ffb4a2]">{error}</p>}
      {notes.map((note) => <p key={note} className="mt-1 text-xs text-tan-deep">{note}</p>)}
      <div className="mt-3 grid gap-3">
        {pending.map((event, index) => (
          <EventCard key={event.id} event={event} onChange={(next) => setPending((rows) => rows.map((row, rowIndex) => rowIndex === index ? next : row))} onConfirm={() => { onConfirm(event); setPending((rows) => rows.filter((_, rowIndex) => rowIndex !== index)); }} onDiscard={() => setPending((rows) => rows.filter((_, rowIndex) => rowIndex !== index))} />
        ))}
      </div>
    </section>
  );
}
