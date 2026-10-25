import buildings from "../data/buildings.json";

const codes = ["unknown", ...buildings.map((b) => b.code)];

export default function EventCard({ event, onChange, onConfirm, onDiscard }) {
  const set = (field) => (e) => onChange({ ...event, [field]: e.target.value });

  return (
    <div className="rounded-xl border border-orange/50 bg-ink-soft p-3">
      <p className="mb-2 text-[0.68rem] uppercase tracking-[0.14em] text-tan-deep">
        Review before adding
      </p>
      <div className="grid gap-2">
        <label className="text-xs text-tan">
          Title
          <input
            className="mt-1 w-full rounded-md border border-tan-deep/30 bg-ink px-2 py-1.5 text-sm text-cream"
            value={event.title}
            onChange={set("title")}
          />
        </label>
        <div className="grid grid-cols-2 gap-2">
          <label className="text-xs text-tan">
            Start
            <input
              className="mt-1 w-full rounded-md border border-tan-deep/30 bg-ink px-2 py-1.5 text-sm text-cream"
              value={event.start}
              onChange={set("start")}
            />
          </label>
          <label className="text-xs text-tan">
            End
            <input
              className="mt-1 w-full rounded-md border border-tan-deep/30 bg-ink px-2 py-1.5 text-sm text-cream"
              value={event.end}
              onChange={set("end")}
            />
          </label>
        </div>
        <label className="text-xs text-tan">
          Building
          <select
            className="mt-1 w-full rounded-md border border-tan-deep/30 bg-ink px-2 py-1.5 text-sm text-cream"
            value={event.building}
            onChange={set("building")}
          >
            {codes.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-tan">
          Notes
          <input
            className="mt-1 w-full rounded-md border border-tan-deep/30 bg-ink px-2 py-1.5 text-sm text-cream"
            value={event.description}
            onChange={set("description")}
          />
        </label>
      </div>
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={onConfirm}
          className="flex-1 rounded-md bg-orange px-3 py-1.5 text-sm font-semibold text-ink hover:bg-orange-hot"
        >
          Confirm
        </button>
        <button
          type="button"
          onClick={onDiscard}
          className="rounded-md border border-tan-deep/40 px-3 py-1.5 text-sm text-tan hover:border-tan"
        >
          Discard
        </button>
      </div>
    </div>
  );
}
