// Cloudflare Pages _worker.js — RSS Proxy + Expert News API
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const CORS = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 200, headers: CORS });
    }

    // ── RSS proxy ──────────────────────────────────────────────
    if (url.pathname === '/api/rss') {
      if (request.method === 'OPTIONS') return new Response(null, { status: 200, headers: CORS });
      const rawUrl = url.searchParams.get('url');
      if (!rawUrl) return new Response(JSON.stringify({ error: 'Missing url' }), { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } });
      let parsed;
      try { parsed = new URL(rawUrl); } catch {
        return new Response(JSON.stringify({ error: 'Invalid URL' }), { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return new Response(JSON.stringify({ error: 'Protocol not allowed' }), { status: 403, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }
      try {
        const resp = await fetch(rawUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
          },
          signal: AbortSignal.timeout(9000),
        });
        if (!resp.ok) return new Response(JSON.stringify({ error: `Upstream ${resp.status}` }), { status: resp.status, headers: { ...CORS, 'Content-Type': 'application/json' } });
        const body = await resp.text();
        const ct = resp.headers.get('content-type') || 'application/xml';
        return new Response(body, { status: 200, headers: { ...CORS, 'Content-Type': ct, 'Cache-Control': 'public, s-maxage=300, max-age=60, stale-while-revalidate=1800' } });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 502, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }
    }

    // ── GET /api/expert-news — читаем expert-news.json из GitHub ──
    if (url.pathname === '/api/expert-news' && request.method === 'GET') {
      try {
        const ghResp = await fetch(
          'https://api.github.com/repos/Lex212mont/htdi.by/contents/expert-news.json',
          { headers: { 'User-Agent': 'htdi-by-worker', 'Accept': 'application/vnd.github+json' } }
        );
        if (!ghResp.ok) throw new Error(`GitHub ${ghResp.status}`);
        const data = await ghResp.json();
        // Правильное декодирование UTF-8 из base64 (исправляет кракозябры в кириллице)
        const binaryStr = atob(data.content.replace(/\n/g, ''));
        const bytes = Uint8Array.from(binaryStr, c => c.charCodeAt(0));
        const content = new TextDecoder('utf-8').decode(bytes);
        return new Response(content, { status: 200, headers: { ...CORS, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'public, s-maxage=300, max-age=60, stale-while-revalidate=3600' } });
      } catch (e) {
        return new Response(JSON.stringify([]), { status: 200, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }
    }

    // ── POST /api/expert-news — добавляем новость через GitHub API ──
    if (url.pathname === '/api/expert-news' && request.method === 'POST') {
      const ADMIN_PASSWORD = env.ADMIN_PASSWORD;
      const GITHUB_TOKEN   = env.GITHUB_TOKEN;

      if (!ADMIN_PASSWORD || !GITHUB_TOKEN) {
        return new Response(JSON.stringify({ error: 'Server not configured' }), { status: 500, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }

      let body;
      try { body = await request.json(); } catch {
        return new Response(JSON.stringify({ error: 'Invalid JSON' }), { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }

      if (body.password !== ADMIN_PASSWORD) {
        return new Response(JSON.stringify({ error: 'Wrong password' }), { status: 403, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }

      const { title, summary, link, source } = body;
      if (!title || !link) {
        return new Response(JSON.stringify({ error: 'title and link required' }), { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }

      // Получаем текущий файл + sha
      const getResp = await fetch(
        'https://api.github.com/repos/Lex212mont/htdi.by/contents/expert-news.json',
        { headers: { 'Authorization': `Bearer ${GITHUB_TOKEN}`, 'User-Agent': 'htdi-by-worker', 'Accept': 'application/vnd.github+json' } }
      );
      if (!getResp.ok) return new Response(JSON.stringify({ error: 'Cannot read file' }), { status: 502, headers: { ...CORS, 'Content-Type': 'application/json' } });
      const fileData = await getResp.json();
      const sha = fileData.sha;
      const existing = JSON.parse(atob(fileData.content.replace(/\n/g, '')));

      // Добавляем новую запись в начало
      const newEntry = {
        id: Date.now().toString(),
        title,
        summary: summary || '',
        link,
        source: source || 'НТДИ',
        date: new Date().toISOString().slice(0, 10),
      };
      const updated = [newEntry, ...existing];

      // Обновляем файл через GitHub API
      const newContent = btoa(unescape(encodeURIComponent(JSON.stringify(updated, null, 2))));
      const putResp = await fetch(
        'https://api.github.com/repos/Lex212mont/htdi.by/contents/expert-news.json',
        {
          method: 'PUT',
          headers: { 'Authorization': `Bearer ${GITHUB_TOKEN}`, 'User-Agent': 'htdi-by-worker', 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: `Add expert news: ${title}`, content: newContent, sha }),
        }
      );
      if (!putResp.ok) {
        const err = await putResp.text();
        return new Response(JSON.stringify({ error: `GitHub write failed: ${err}` }), { status: 502, headers: { ...CORS, 'Content-Type': 'application/json' } });
      }

      return new Response(JSON.stringify({ ok: true, entry: newEntry }), { status: 200, headers: { ...CORS, 'Content-Type': 'application/json' } });
    }

    // ── All other requests → static assets ──
    return env.ASSETS.fetch(request);
  },
};
