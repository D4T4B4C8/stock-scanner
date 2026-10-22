// Shared backend for the jewellery inventory app (Netlify Blobs).
// GET  /.netlify/functions/data           -> { items, purchase, sale }
// GET  /.netlify/functions/data?img=101   -> the uploaded image of item 101
// POST /.netlify/functions/data           -> { action: 'create' | 'move', ... }
import { getStore } from '@netlify/blobs';

const json = (o, s = 200) =>
  new Response(JSON.stringify(o), {
    status: s,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

async function getState(store) {
  const st = (await store.get('state', { type: 'json', consistency: 'strong' })) || {};
  return {
    items: st.items || {},
    purchase: Array.isArray(st.purchase) ? st.purchase : [],
    sale: Array.isArray(st.sale) ? st.sale : [],
  };
}

export default async (req) => {
  const store = getStore('jewellery-inventory');
  const url = new URL(req.url);

  if (req.method === 'GET') {
    const img = url.searchParams.get('img');
    if (img) {
      const d = await store.get('img/' + img, { consistency: 'strong' });
      const m = d && d.match(/^data:(.+?);base64,(.+)$/);
      if (!m) return new Response('Not found', { status: 404 });
      return new Response(Buffer.from(m[2], 'base64'), {
        headers: { 'Content-Type': m[1], 'Cache-Control': 'public, max-age=31536000' },
      });
    }
    return json(await getState(store));
  }

  if (req.method === 'POST') {
    try {
      const b = await req.json();
      const state = await getState(store);

      if (b.action === 'create') {
        const id = String(b.id || '').trim();
        if (!id || !b.name || !b.price) return json({ ok: false, error: 'ID, name and price are required' }, 400);
        const old = state.items[id];
        let link = String(b.link || '');
        if (b.image) {
          await store.set('img/' + id, b.image);
          link = `/.netlify/functions/data?img=${encodeURIComponent(id)}&v=${Date.now()}`;
        } else if (!link && old) link = old.link;
        state.items[id] = { id, name: String(b.name), price: String(b.price), link, qty: old ? old.qty : 0 };
        await store.setJSON('state', state);
        return json({ ok: true, state, item: state.items[id] });
      }

      if (b.action === 'move') {
        const id = String(b.id || '').trim();
        const type = b.type === 'sale' ? 'sale' : 'purchase';
        const it = state.items[id];
        if (!it) return json({ ok: false, error: `ID ${id} not found` }, 404);
        if (type === 'sale' && it.qty <= 0) return json({ ok: false, error: `ID ${id} is out of stock` }, 409);
        it.qty += type === 'purchase' ? 1 : -1;
        state[type].unshift({ id, name: it.name, price: it.price, qty: type === 'purchase' ? 1 : -1, date: new Date().toISOString() });
        await store.setJSON('state', state);
        return json({ ok: true, state, item: it });
      }

      return json({ ok: false, error: 'Unknown action' }, 400);
    } catch (err) {
      return json({ ok: false, error: String(err) }, 400);
    }
  }
  return new Response('Method not allowed', { status: 405 });
};

export const config = { path: '/.netlify/functions/data' };
