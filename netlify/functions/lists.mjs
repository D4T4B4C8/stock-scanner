// Stores the "Left Over IDs" lists on the server (Netlify Blobs) so every device sees the same lists.
import { getStore } from "@netlify/blobs";

const H = { "Content-Type": "application/json", "Cache-Control": "no-store" };
const dedupe = (arr) => {
  const seen = new Set();
  return arr.filter((l) => {
    const k = String(l.name).trim().toLowerCase() + "|" + l.start + "|" + l.end;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
};
const reply = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: H });

export default async (req) => {
  const store = getStore({ name: "leftlists", consistency: "strong" });
  const load = async () => {
    const raw = (await store.get("all", { type: "json" })) || [];
    const clean = dedupe(raw);
    if (clean.length !== raw.length) await store.setJSON("all", clean); // clean up old duplicates
    return clean;
  };
  try {
    if (req.method === "GET") return reply({ ok: true, lists: await load() });
    if (req.method !== "POST") return reply({ ok: false, error: "Method not allowed" }, 405);

    const b = await req.json();
    let lists = await load();

    if (b.action === "add") {
      const l = b.list || {};
      if (!l.name || !Number.isFinite(l.start) || !Number.isFinite(l.end) || l.start > l.end)
        return reply({ ok: false, error: "Invalid list" }, 400);
      lists = lists.filter((x) => x.id !== l.id);
      lists.push({ id: l.id, name: String(l.name), start: l.start, end: l.end });
    } else if (b.action === "merge") {
      const have = new Set(lists.map((x) => x.id));
      for (const l of b.lists || []) {
        if (l && l.name && Number.isFinite(l.start) && Number.isFinite(l.end) && !have.has(l.id)) {
          lists.push({ id: l.id, name: String(l.name), start: l.start, end: l.end });
          have.add(l.id);
        }
      }
    } else if (b.action === "delete") {
      lists = lists.filter((x) => x.id !== b.id);
    } else return reply({ ok: false, error: "Unknown action" }, 400);

    lists = dedupe(lists);
    await store.setJSON("all", lists);
    return reply({ ok: true, lists });
  } catch (e) {
    return reply({ ok: false, error: e.message || "Server error" }, 500);
  }
};

export const config = { path: '/.netlify/functions/lists' };
