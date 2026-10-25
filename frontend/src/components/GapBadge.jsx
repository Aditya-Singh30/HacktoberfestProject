export default function GapBadge({ event }) {
  if (event.gapMin == null) return null;
  const walk = event.walkMin;
  const gap = event.gapMin;
  if (walk == null) {
    return (
      <div className="my-2 rounded-lg border border-tan-deep/30 bg-ink-soft px-3 py-1.5 text-xs text-tan">
        {gap} min gap · walking time unknown ({event.prevBuilding} → {event.building})
      </div>
    );
  }
  if (event.tight) {
    return (
      <div className="my-2 rounded-lg border border-warn/60 bg-warn/20 px-3 py-1.5 text-xs font-semibold text-[#ffb4a2]">
        Tight: {gap} min gap, {walk} min walk
      </div>
    );
  }
  return (
    <div className="my-2 rounded-lg border border-ok/50 bg-ok/20 px-3 py-1.5 text-xs font-semibold text-[#b7d4c0]">
      {gap} min gap, {walk} min walk
    </div>
  );
}
