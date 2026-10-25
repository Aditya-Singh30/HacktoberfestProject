export const WALK_M_PER_MIN = 80;

export function haversineM(lat1, lon1, lat2, lon2) {
  const r = 6371000;
  const p1 = (lat1 * Math.PI) / 180;
  const p2 = (lat2 * Math.PI) / 180;
  const dlat = ((lat2 - lat1) * Math.PI) / 180;
  const dlon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dlat / 2) ** 2 +
    Math.cos(p1) * Math.cos(p2) * Math.sin(dlon / 2) ** 2;
  return 2 * r * Math.asin(Math.sqrt(a));
}

export function walkMinutes(fromB, toB) {
  if (!fromB || !toB) return null;
  if (fromB.code === toB.code) return 2;
  const meters = haversineM(fromB.lat, fromB.lon, toB.lat, toB.lon);
  return Math.max(2, Math.round(meters / WALK_M_PER_MIN));
}

export function minutesBetween(endHHMM, startHHMM) {
  const [eh, em] = String(endHHMM || "00:00")
    .split(":")
    .map(Number);
  const [sh, sm] = String(startHHMM || "00:00")
    .split(":")
    .map(Number);
  return sh * 60 + sm - (eh * 60 + em);
}

export function withGaps(events, buildingsByCode) {
  const sorted = [...events].sort((a, b) => {
    const byTime = String(a.start).localeCompare(String(b.start));
    if (byTime !== 0) return byTime;
    return String(a.title).localeCompare(String(b.title));
  });
  return sorted.map((ev, i) => {
    if (i === 0) {
      return { ...ev, gapMin: null, walkMin: null, tight: false, prevBuilding: null };
    }
    const prev = sorted[i - 1];
    const gap = minutesBetween(prev.end, ev.start);
    const walk = walkMinutes(
      buildingsByCode[prev.building],
      buildingsByCode[ev.building],
    );
    return {
      ...ev,
      gapMin: gap,
      walkMin: walk,
      prevBuilding: prev.building,
      tight: walk != null && gap != null && walk > gap,
    };
  });
}

export function newId() {
  return crypto.randomUUID();
}
