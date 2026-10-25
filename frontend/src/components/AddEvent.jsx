import { useState } from "react";
import EventCard from "./EventCard";
import { SAMPLE_CAPTION } from "../data/demo";
import { fileToBase64, postJson } from "../lib/api";
import { newId } from "../lib/walking";

export default function AddEvent({ day, onConfirm }) {
  const [caption, setCaption] = useState(SAMPLE_CAPTION);
  const [file, setFile] = useState(null);
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notes, setNotes] = useState([]);
  const canSubmit = !loading && (caption.trim() || file);

  async function extract() {
    setLoading(true);
    setError("");
    setNotes([]);
    try {
      const images = file ? [await fileToBase64(file)] : [];
      const data = await postJson("/extract/event", { caption, date: day, images });
      const events = (data.events || []).map((event) => ({ ...event, id: newId() }));
      setNotes(data.warnings || []);
      if (!events.length) throw new Error((data.warnings || []).join(" ") || "Gemma found no event with a readable time in that post.");
      setPending(events);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mt-8">
      <h2 className="mb-2 font-serif text-lg text-tan">Add event</h2>
      <p className="mb-2 text-xs text-tan-deep">Paste a caption or upload a flyer screenshot. Ingestion only — no scraping.</p>
      <textarea className="h-32 w-full rounded-lg border border-tan-deep/30 bg-ink p-2 text-sm text-cream" value={caption} onChange={(event) => setCaption(event.target.value)} />
      <label className="mt-2 block rounded-lg border border-dashed border-tan-deep/50 bg-ink px-3 py-2 text-xs text-tan">Screenshot (optional){file ? ` — ${file.name}` : ""}
        <input type="file" accept="image/png,image/jpeg,image/webp" className="mt-1 block w-full text-xs text-cream" onChange={(event) => setFile(event.target.files?.[0] || null)} />
      </label>
      <button type="button" disabled={!canSubmit} onClick={extract} className="mt-2 w-full rounded-md bg-orange px-3 py-2 text-sm font-semibold text-ink hover:bg-orange-hot disabled:cursor-not-allowed disabled:opacity-60">
        {loading ? "Gemma is reading the post…" : "Extract with Gemma 4"}
      </button>
      {error && <p className="mt-2 text-xs text-[#ffb4a2]">{error}</p>}
      {notes.map((note) => <p key={note} className="mt-1 text-xs text-tan-deep">{note}</p>)}
      <div className="mt-3 grid gap-3">
        {pending.map((event, index) => (
          <div key={event.id}>
            {event.date !== day && <p className="mb-1 text-xs text-tan-deep">Dated {event.date}. Switch the day picker to {event.date} to see it on the timeline.</p>}
            <EventCard key={event.id} event={event} onChange={(next) => setPending((rows) => rows.map((row, rowIndex) => rowIndex === index ? next : row))} onConfirm={() => { onConfirm(event); setPending((rows) => rows.filter((_, rowIndex) => rowIndex !== index)); }} onDiscard={() => setPending((rows) => rows.filter((_, rowIndex) => rowIndex !== index))} />
          </div>
        ))}
      </div>
    </section>
  );
}
