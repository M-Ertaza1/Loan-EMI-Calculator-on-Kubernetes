const express = require('express');
const { MongoClient } = require('mongodb');

const app = express();
app.use(express.json());
app.use(express.static('public'));

const MONGO_URL = process.env.MONGO_URL;
if (!MONGO_URL) { console.error('MONGO_URL is not set'); process.exit(1); }

const client = new MongoClient(MONGO_URL, { serverSelectionTimeoutMS: 3000 });
const col = () => client.db().collection('calculations');

// connect in background so the pod starts even if Mongo is not ready yet
(async function connect() {
  for (;;) {
    try { await client.connect(); console.log('Mongo connected'); return; }
    catch (e) { console.error('Mongo connect failed, retrying:', e.message); await new Promise(r => setTimeout(r, 3000)); }
  }
})();

app.post('/api/emi', async (req, res) => {
  try {
    const P = Number(req.body.principal);
    const rate = Number(req.body.rate);
    const n = Number(req.body.months);
    if (![P, rate, n].every(v => Number.isFinite(v) && v > 0))
      return res.status(400).json({ error: 'All values must be positive numbers' });

    const r = rate / 12 / 100;
    const f = Math.pow(1 + r, n);
    const emi = (P * r * f) / (f - 1);
    const total = emi * n;
    const servedBy = process.env.HOSTNAME || 'unknown';
    const podIp = process.env.POD_IP || 'unknown';

    await col().insertOne({ principal: P, rate, months: n, emi, servedBy, createdAt: new Date() });
    res.json({
      emi: +emi.toFixed(2),
      totalPayment: +total.toFixed(2),
      totalInterest: +(total - P).toFixed(2),
      servedBy, podIp
    });
  } catch (e) {
    console.error(e.message);
    res.status(500).json({ error: 'Database error, please retry' });
  }
});

app.get('/api/history', async (_req, res) => {
  try {
    res.json(await col().find().sort({ createdAt: -1 }).limit(10).toArray());
  } catch (e) {
    res.status(500).json({ error: 'Database error' });
  }
});

app.get('/health', async (_req, res) => {
  try { await client.db().command({ ping: 1 }); res.sendStatus(200); }
  catch { res.sendStatus(503); }
});

app.listen(3000, () => console.log('EMI app listening on 3000'));
