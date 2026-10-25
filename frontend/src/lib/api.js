export function errorDetail(data, fallback = "Request failed") {
  const detail = data?.detail ?? data?.message ?? data?.error;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || (typeof item === "string" ? item : JSON.stringify(item))).join("; ");
  }
  return JSON.stringify(detail);
}

export async function postJson(url, body, signal) {
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err?.name === "AbortError") throw err;
    throw new Error("Can't reach the backend. Start it with: cd backend && uvicorn main:app --port 8000");
  }
  const raw = await response.text();
  let data = null;
  try {
    data = raw ? JSON.parse(raw) : null;
  } catch {
    // The response will be reported below as a proxy/backend setup problem.
  }
  if (!response.ok) {
    if (data) throw new Error(errorDetail(data, `Request failed (${response.status})`));
    throw new Error(`Backend returned ${response.status} (not JSON). Check the Vite proxy and uvicorn.`);
  }
  if (!data) throw new Error("Got an HTML page instead of JSON: restart `npm run dev` after checking the Vite proxy.");
  return data;
}

export function fileToBase64(file, maxSide = 1280) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      const scale = Math.min(1, maxSide / Math.max(image.width, image.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(image.width * scale));
      canvas.height = Math.max(1, Math.round(image.height * scale));
      const ctx = canvas.getContext("2d");
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      resolve((canvas.toDataURL("image/jpeg", 0.85) || "").split(",").pop() || "");
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || "").split(",").pop() || "");
      reader.onerror = reject;
      reader.readAsDataURL(file);
    };
    image.src = url;
  });
}
