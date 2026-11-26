// kana-dojo lead worker：收 email → Brevo 寄字帖連結給訪客 → 通知自己
// 綁定：BREVO_KEY(secret)、OWNER_EMAIL、SENDER_EMAIL、SENDER_NAME、PDF_URL、SITE_URL

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'content-type, accept',
  'Access-Control-Max-Age': '86400',
};

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { ...CORS, 'Content-Type': 'application/json; charset=utf-8' } });

const validEmail = (s) => typeof s === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s.trim()) && s.length <= 254;

async function sendBrevo(env, payload) {
  const res = await fetch('https://api.brevo.com/v3/smtp/email', {
    method: 'POST',
    headers: {
      'api-key': env.BREVO_KEY,
      'content-type': 'application/json',
      accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`brevo ${res.status}: ${text.slice(0, 300)}`);
  return text;
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    if (request.method !== 'POST') return json({ ok: false, error: 'POST only' }, 405);

    let body = {};
    try { body = await request.json(); } catch (e) { return json({ ok: false, error: 'bad json' }, 400); }

    if (body._honey) return json({ ok: true });               // 機械人：靜靜回 200
    const email = String(body.email || '').trim();
    if (!validEmail(email)) return json({ ok: false, error: 'invalid email' }, 400);

    const now = new Date().toISOString();

    // 1) 寄給訪客：字帖連結
    try {
      await sendBrevo(env, {
        sender: { name: env.SENDER_NAME, email: env.SENDER_EMAIL },
        to: [{ email }],
        replyTo: { email: env.OWNER_EMAIL, name: env.SENDER_NAME },
        subject: '你的五十音筆順字帖（17 頁 A4）',
        htmlContent: `
          <div style="font-family:-apple-system,'Segoe UI',sans-serif;font-size:16px;line-height:1.7;color:#2c2a26">
            <p>多謝索取五十音筆順字帖。</p>
            <p><a href="${env.PDF_URL}" style="display:inline-block;padding:12px 22px;background:#2c3e6b;color:#fff;border-radius:10px;text-decoration:none;font-weight:600">下載字帖 PDF</a></p>
            <p style="color:#6b6357;font-size:14px">17 頁 A4：平假名與片假名，方格、筆順數字、兩格虛線描紅，可直接列印。</p>
            <p style="color:#6b6357;font-size:14px">練習 app：<a href="${env.SITE_URL}">${env.SITE_URL}</a></p>
            <p style="color:#8c8477;font-size:13px">字帖字形來源：KanjiVG（CC BY-SA 4.0）。如不想再收到郵件，回覆本信寫「取消訂閱」即可。</p>
          </div>`,
        textContent: `多謝索取五十音筆順字帖。\n\n下載連結（17 頁 A4 PDF）：${env.PDF_URL}\n\n練習 app：${env.SITE_URL}\n\n如不想再收到郵件，回覆本信寫「取消訂閱」即可。`,
        tags: ['kana-dojo-lead'],
      });
    } catch (err) {
      return json({ ok: false, error: 'send failed', detail: String(err.message || err) }, 502);
    }

    // 2) 通知自己（失敗不影響訪客體驗）
    try {
      await fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: { 'api-key': env.BREVO_KEY, 'content-type': 'application/json', accept: 'application/json' },
        body: JSON.stringify({
          sender: { name: 'kana-dojo', email: env.SENDER_EMAIL },
          to: [{ email: env.OWNER_EMAIL }],
          replyTo: { email },
          subject: `新名單：${email}`,
          textContent: `新提交\n\nemail: ${email}\n時間: ${now}\n來源: ${body.source || '-'}`,
          tags: ['kana-dojo-notify'],
        }),
      });
    } catch (e) { /* 忽略 */ }

    return json({ ok: true });
  },
};
