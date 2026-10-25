import { useState } from "react";
import { errorDetail } from "../lib/api";

export default function AskSteamLine({ day, events }) {
  const [question, setQuestion] = useState(
    "Can I make the 6pm club meeting after my last class?",
  );
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function send() {
    setLoading(true);
    setError("");
    setAnswer("");
    try {
      const res = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, events, date: day }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(errorDetail(data, "Ask failed"));
      setAnswer(data.answer);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mt-8">
      <h2 className="mb-2 font-serif text-lg text-tan">Ask SteamLine</h2>
      <input
        className="w-full rounded-lg border border-tan-deep/30 bg-ink px-2 py-2 text-sm text-cream"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button
        type="button"
        disabled={loading}
        onClick={send}
        className="mt-2 w-full rounded-md border border-orange/70 px-3 py-2 text-sm font-semibold text-orange-hot hover:bg-orange/10 disabled:opacity-60"
      >
        {loading ? "Thinking on-device…" : "Ask Gemma 4"}
      </button>
      {error && <p className="mt-2 text-xs text-[#ffb4a2]">{error}</p>}
      {answer && (
        <p className="mt-3 rounded-lg border border-tan-deep/30 bg-ink p-3 text-sm leading-relaxed text-cream/90">
          {answer}
        </p>
      )}
    </section>
  );
}
