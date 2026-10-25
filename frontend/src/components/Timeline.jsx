import GapBadge from "./GapBadge";

export default function Timeline({ events, onRemove }) {
  if (!events.length) {
    return (
      <p className="rounded-xl border border-tan-deep/20 bg-ink-soft p-6 text-sm text-tan-deep">
        No stops yet. Paste a schedule, add an Instagram event, or load demo data.
      </p>
    );
  }

  return (
    <ol className="relative ml-2 border-l-2 border-orange/70 pl-5">
      {events.map((ev) => (
        <li key={ev.id} className="mb-1">
          <GapBadge event={ev} />
          <div
            className={`relative rounded-xl border bg-ink-soft p-3 ${
              ev.tight ? "border-orange shadow-[0_0_0_1px_rgba(232,93,4,0.35)]" : "border-tan/10"
            }`}
          >
            <span
              className={`absolute -left-[1.54rem] top-4 h-3 w-3 rounded-full ${
                ev.source === "instagram" ? "bg-orange" : "bg-tan-deep"
              } shadow-[0_0_0_4px_rgba(232,93,4,0.18)]`}
            />
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-xs font-semibold text-orange-hot">
                  {ev.start}–{ev.end}
                </p>
                <h3 className="font-serif text-lg text-cream">{ev.title}</h3>
                <p className="text-sm text-cream/70">
                  {ev.building}
                  {ev.description ? ` · ${ev.description}` : ""}
                </p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <span
                  className={`rounded px-1.5 py-0.5 text-[0.65rem] uppercase tracking-wide ${
                    ev.source === "instagram"
                      ? "bg-orange/20 text-orange-hot"
                      : "bg-tan/15 text-tan"
                  }`}
                >
                  {ev.source === "instagram" ? "Instagram" : "Class"}
                </span>
                <button
                  type="button"
                  onClick={() => onRemove(ev.id)}
                  className="text-[0.65rem] uppercase tracking-wide text-tan-deep hover:text-cream"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
