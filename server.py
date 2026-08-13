from __future__ import annotations

import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "jia_yi_jing_acupuncture.db"
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
SESSION_COOKIE = "admin_session"

HTML_PAGE = """
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>甲乙經穴位查詢系統</title>
  <style>
    :root{
      --bg:#f4efe9; --bg2:#efe5d6; --card:rgba(255,255,255,0.78); --text:#2d241f; --muted:#6b5d55; --primary:#5a3d32; --primary2:#8f6a4b; --accent:#d9b98c; --border:rgba(90,61,50,0.16); --shadow:rgba(38,27,24,0.12);
    }
    *{box-sizing:border-box} body{margin:0;background:linear-gradient(180deg,var(--bg) 0%,var(--bg2) 100%);color:var(--text);font-family:"Microsoft JhengHei","Segoe UI",sans-serif} a{text-decoration:none;color:inherit}
    .container{max-width:1200px;margin:0 auto;padding:30px 18px 50px}
    .hero{background:linear-gradient(135deg,#5a3d32,#8f6a4b);border-radius:22px;box-shadow:0 18px 48px var(--shadow);padding:26px 24px;color:#fff}
    .hero-row{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
    .hero h1{margin:0 0 8px;font-size:clamp(2rem,4vw,3rem);letter-spacing:.03em}
    .hero p{margin:0;color:rgba(255,255,255,0.8)}
    .badge{padding:8px 14px;border-radius:999px;background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);font-size:12px;white-space:nowrap}
    .toolbar{margin-top:20px;background:var(--card);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:18px;padding:18px;box-shadow:0 12px 28px var(--shadow)}
    .controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
    select,input,button{font:inherit;border-radius:12px;border:1px solid var(--border);padding:11px 12px}
    select{min-width:180px;background:#fff}
    input{flex:1 1 240px;min-width:220px;background:rgba(255,255,255,0.5)}
    button{background:linear-gradient(135deg,var(--primary),var(--primary2));color:white;border:none;cursor:pointer;font-weight:700;box-shadow:0 8px 20px rgba(90,61,50,0.2)}
    .stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
    .chip{padding:8px 12px;border-radius:999px;background:#f2e4d2;color:var(--primary);font-weight:700;border:1px solid rgba(143,106,75,0.12)}
    .grid{display:grid;grid-template-columns:1.7fr .9fr;gap:20px;margin-top:22px}
    .card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:18px;box-shadow:0 10px 25px var(--shadow)}
    .card h3{margin:0 0 12px;color:var(--primary);font-size:1.2rem}
    .small{color:var(--muted);line-height:1.7;margin:8px 0}
    table{width:100%;border-collapse:collapse;border:1px solid var(--border);background:rgba(255,255,255,0.9)}
    th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--border);vertical-align:top}
    th{background:rgba(143,106,75,0.08);color:var(--primary)}
    tbody tr:nth-child(even){background:rgba(90,61,50,0.02)}
    .empty{padding:18px 0;color:var(--muted)}
    .admin-link{display:inline-block;margin-top:12px;padding:10px 14px;border-radius:10px;background:var(--primary);color:white;font-weight:700}
    @media(max-width:760px){.grid{grid-template-columns:1fr}.controls{flex-direction:column}select,input,button{width:100%}}
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <div class="hero-row">
        <div>
          <h1>甲乙經穴位查詢</h1>
          <p>穴位 · 經絡 · 病症關聯查詢系統</p>
        </div>
        <div class="badge">中醫知識庫</div>
      </div>
    </div>

    <div class="toolbar">
      <div class="controls">
        <select id="type">
          <option value="disease">按病症查</option>
          <option value="point">按穴位查</option>
          <option value="meridian">按經絡查</option>
          <option value="by-disease">查病症對應穴位</option>
          <option value="by-meridian">查經絡穴位</option>
        </select>
        <input id="keyword" type="text" placeholder="輸入關鍵字：頭痛 / 合谷 / 手陽明 / 月經不調" />
        <button id="searchBtn">查詢</button>
      </div>
      <div class="stats">
        <div class="chip" id="statMeridians">經絡：0</div>
        <div class="chip" id="statPoints">穴位：0</div>
        <div class="chip" id="statDiseases">病症：0</div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h3>查詢結果</h3>
        <div id="results"></div>
      </div>
      <div class="card">
        <h3>使用說明</h3>
        <p class="small">可查詢：病症名稱、穴位名稱、經絡名稱、或常見關鍵字。</p>
        <p class="small">範例：頭痛、合谷、手陽明、月經不調、咳嗽、失眠。</p>
        <p class="small">本系統亦提供 API：/api/diseases、/api/acupoints、/api/meridians。</p>
        <a class="admin-link" href="/admin">進入管理後台</a>
      </div>
    </div>
  </div>

  <script>
    const resultsEl = document.getElementById('results');
    const typeEl = document.getElementById('type');
    const keywordEl = document.getElementById('keyword');

    async function loadStats(){
      const [diseases, points, meridians] = await Promise.all([
        fetch('/api/diseases').then(r => r.json()),
        fetch('/api/acupoints').then(r => r.json()),
        fetch('/api/meridians').then(r => r.json())
      ]);
      document.getElementById('statDiseases').textContent = `病症：${diseases.length}`;
      document.getElementById('statPoints').textContent = `穴位：${points.length}`;
      document.getElementById('statMeridians').textContent = `經絡：${meridians.length}`;
    }

    function renderRows(rows, columns){
      if(!rows || rows.length===0){ resultsEl.innerHTML='<div class="empty">查無資料</div>'; return; }
      const thead = columns.map(c => `<th>${c.label}</th>`).join('');
      const tbody = rows.map(row => {
        const cells = columns.map(c => `<td>${String(row[c.key] ?? '')}</td>`).join('');
        return `<tr>${cells}</tr>`;
      }).join('');
      resultsEl.innerHTML = `<table><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>`;
    }

    async function search(){
      const type = typeEl.value;
      const keyword = keywordEl.value.trim();
      let url='';
      if(type === 'disease') url = '/api/diseases?keyword=' + encodeURIComponent(keyword);
      if(type === 'point') url = '/api/acupoints?keyword=' + encodeURIComponent(keyword);
      if(type === 'meridian') url = '/api/meridians?keyword=' + encodeURIComponent(keyword);
      if(type === 'by-disease') url = '/api/by-disease?keyword=' + encodeURIComponent(keyword);
      if(type === 'by-meridian') url = '/api/by-meridian?keyword=' + encodeURIComponent(keyword);
      const data = await fetch(url).then(r=>r.json());

      if(type==='disease') renderRows(data,[{key:'id',label:'ID'},{key:'name',label:'病症'},{key:'category',label:'分類'},{key:'description',label:'描述'}]);
      if(type==='point') renderRows(data,[{key:'id',label:'ID'},{key:'name',label:'穴位'},{key:'pinyin',label:'拼音'},{key:'meridian_name',label:'經絡'},{key:'location',label:'位置'},{key:'classic_code',label:'編碼'}]);
      if(type==='meridian') renderRows(data,[{key:'id',label:'ID'},{key:'name',label:'經絡'},{key:'code',label:'代碼'},{key:'category',label:'類別'},{key:'description',label:'說明'}]);
      if(type==='by-disease') renderRows(data,[{key:'point_name',label:'穴位'},{key:'pinyin',label:'拼音'},{key:'meridian_name',label:'經絡'},{key:'disease_name',label:'病症'},{key:'evidence',label:'關聯說明'}]);
      if(type==='by-meridian') renderRows(data,[{key:'point_name',label:'穴位'},{key:'pinyin',label:'拼音'},{key:'meridian_name',label:'經絡'},{key:'location',label:'位置'}]);
    }

    document.getElementById('searchBtn').addEventListener('click', search);
    keywordEl.addEventListener('keydown', (e) => { if(e.key==='Enter') search(); });
    loadStats(); search();
  </script>
</body>
</html>
"""

ADMIN_PAGE = """
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>管理後台</title>
  <style>
    :root{--bg:#f3efe9;--panel:#fff;--primary:#5a3d32;--primary2:#8f6a4b;--text:#2d241f;--muted:#6d5b55;--border:rgba(90,61,50,.15);--shadow:rgba(33,25,22,.12)}
    *{box-sizing:border-box} body{margin:0;background:linear-gradient(180deg,#f3efe9,#ebe0d0);color:var(--text);font-family:"Microsoft JhengHei","Segoe UI",sans-serif}
    .wrap{max-width:1180px;margin:0 auto;padding:24px 18px 40px}
    .topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:20px;padding:18px 20px;border-radius:18px;background:linear-gradient(135deg,#5a3d32,#8f6a4b);color:white;box-shadow:0 16px 32px var(--shadow)}
    h1{margin:0;font-size:clamp(1.6rem,2vw,2.3rem)}
    .btn{padding:10px 14px;border:none;border-radius:10px;cursor:pointer;font-weight:700;background:#fff;color:var(--primary)}
    .btn-danger{background:#a94c45;color:white}
    .grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
    .card{background:var(--panel);border:1px solid var(--border);border-radius:18px;padding:16px;box-shadow:0 12px 28px var(--shadow)}
    .card h3{margin:0 0 12px;color:var(--primary)}
    .stat{display:flex;justify-content:space-between;align-items:center;padding:14px 14px;border:1px solid var(--border);border-radius:12px;background:rgba(143,106,75,.04)}
    .stat strong{font-size:1.5rem}
    .login-box{max-width:420px;margin:80px auto;padding:24px;border:1px solid var(--border);border-radius:18px;background:var(--panel);box-shadow:0 18px 35px var(--shadow)}
    label{display:block;margin:12px 0 8px;font-weight:700} input,select,textarea{width:100%;padding:10px 12px;border-radius:10px;border:1px solid var(--border);font:inherit}
    form{margin-top:12px}
    .row{display:flex;gap:10px;flex-wrap:wrap}
    .pill{display:inline-block;padding:8px 12px;border-radius:999px;background:rgba(143,106,75,0.08);color:var(--primary);font-weight:700}
    table{width:100%;border-collapse:collapse;margin-top:12px;background:#fff;border:1px solid var(--border)}
    th,td{padding:10px 12px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
    th{background:rgba(143,106,75,0.06);color:var(--primary)}
    .muted{color:var(--muted)}
    .hidden{display:none !important}
    .notice{padding:10px 12px;border-radius:10px;margin-bottom:10px}
    .notice.error{background:#fdeaea;color:#9b2c2c}
    .notice.success{background:#e7f7ef;color:#245d42}
    @media(max-width:900px){.grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
  <div class="wrap">
    <div id="login-view">
      <div class="login-box">
        <h1 style="margin-top:0">管理後台登入</h1>
        <div id="loginNotice" class="notice hidden"></div>
        <form id="loginForm">
          <label>帳號</label>
          <input name="username" value="admin" required />
          <label>密碼</label>
          <input name="password" type="password" value="admin123" required />
          <div style="margin-top:16px"><button class="btn" type="submit">登入</button></div>
        </form>
      </div>
    </div>

    <div id="admin-view" class="hidden">
      <div class="topbar">
        <h1>中醫知識庫管理後台</h1>
        <button class="btn btn-danger" id="logoutBtn">登出</button>
      </div>

      <div class="grid">
        <div class="card"><div class="stat"><span class="muted">經絡</span><strong id="statMeridians">0</strong></div></div>
        <div class="card"><div class="stat"><span class="muted">穴位</span><strong id="statPoints">0</strong></div></div>
        <div class="card"><div class="stat"><span class="muted">病症</span><strong id="statDiseases">0</strong></div></div>
      </div>

      <div class="card" style="margin-top:18px">
        <h3>新增經絡</h3>
        <form id="meridianForm">
          <div class="row">
            <div style="flex:1;min-width:160px"><label>名稱</label><input name="name" required /></div>
            <div style="flex:1;min-width:140px"><label>代碼</label><input name="code" required /></div>
            <div style="flex:1;min-width:160px"><label>類別</label><input name="category" required /></div>
          </div>
          <label>說明</label><textarea name="description" rows="3"></textarea>
          <div style="margin-top:12px"><button class="btn" type="submit">新增經絡</button></div>
        </form>
        <div id="meridianTable"></div>
      </div>

      <div class="card" style="margin-top:18px">
        <h3>新增病症</h3>
        <form id="diseaseForm">
          <div class="row">
            <div style="flex:1;min-width:180px"><label>名稱</label><input name="name" required /></div>
            <div style="flex:1;min-width:180px"><label>分類</label><input name="category" required /></div>
          </div>
          <label>描述</label><textarea name="description" rows="3"></textarea>
          <div style="margin-top:12px"><button class="btn" type="submit">新增病症</button></div>
        </form>
        <div id="diseaseTable"></div>
      </div>

      <div class="card" style="margin-top:18px">
        <h3>新增穴位</h3>
        <form id="pointForm">
          <div class="row">
            <div style="flex:1;min-width:180px"><label>名稱</label><input name="name" required /></div>
            <div style="flex:1;min-width:180px"><label>拼音</label><input name="pinyin" required /></div>
            <div style="flex:1;min-width:180px"><label>經絡</label><select name="meridian_id" id="meridianSelect"></select></div>
          </div>
          <div class="row">
            <div style="flex:1;min-width:200px"><label>定位</label><input name="location" required /></div>
            <div style="flex:1;min-width:200px"><label>經典編碼</label><input name="classic_code" /></div>
          </div>
          <label>說明</label><textarea name="note" rows="3"></textarea>
          <div style="margin-top:12px"><button class="btn" type="submit">新增穴位</button></div>
        </form>
        <div id="pointTable"></div>
      </div>
    </div>
  </div>

  <script>
    const loginView = document.getElementById('login-view');
    const adminView = document.getElementById('admin-view');
    const loginForm = document.getElementById('loginForm');
    const loginNotice = document.getElementById('loginNotice');
    const meridianSelect = document.getElementById('meridianSelect');

    async function apiFetch(url, options={}) {
      const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options
      });
      const data = await response.json().catch(() => ({}));
      if(!response.ok){ throw new Error(data.error || '操作失敗'); }
      return data;
    }

    function showNotice(el, text, type='error') {
      el.textContent = text;
      el.className = 'notice ' + type;
      el.classList.remove('hidden');
      setTimeout(() => el.classList.add('hidden'), 3000);
    }

    async function loadStats(){
      const summary = await apiFetch('/api/admin/summary');
      document.getElementById('statMeridians').textContent = summary.meridians;
      document.getElementById('statPoints').textContent = summary.acupoints;
      document.getElementById('statDiseases').textContent = summary.diseases;
    }

    async function loadMeridianOptions(){
      const rows = await apiFetch('/api/admin/meridians');
      meridianSelect.innerHTML = rows.map(r => `<option value="${r.id}">${r.name}</option>`).join('');
    }

    function renderTable(containerId, items, columns, actions){
      const container = document.getElementById(containerId);
      if(!items || items.length===0){ container.innerHTML = '<div class="muted" style="padding-top:14px">暫無資料</div>'; return; }
      const header = columns.map(c => `<th>${c}</th>`).join('');
      const body = items.map(item => {
        const cells = columns.map(c => `<td>${String(item[c] ?? '')}</td>`).join('');
        const actionHtml = actions ? `<td>${actions(item)}</td>` : '';
        return `<tr>${cells}${actionHtml}</tr>`;
      }).join('');
      container.innerHTML = `<table><thead><tr>${header}${actions ? '<th>操作</th>' : ''}</tr></thead><tbody>${body}</tbody></table>`;
    }

    async function refreshAdminData(){
      await loadStats();
      const meridians = await apiFetch('/api/admin/meridians');
      const diseases = await apiFetch('/api/admin/diseases');
      const points = await apiFetch('/api/admin/acupoints');
      loadMeridianOptions();
      renderTable('meridianTable', meridians, ['id','name','code','category','description'], (row) => `<button class="btn btn-danger" data-table="meridians" data-id="${row.id}" data-action="delete">刪除</button>`);
      renderTable('diseaseTable', diseases, ['id','name','category','description'], (row) => `<button class="btn btn-danger" data-table="diseases" data-id="${row.id}" data-action="delete">刪除</button>`);
      renderTable('pointTable', points, ['id','name','pinyin','meridian_name','location','classic_code'], (row) => `<button class="btn btn-danger" data-table="acupoints" data-id="${row.id}" data-action="delete">刪除</button>`);
    }

    async function handleLogin(e){
      e.preventDefault();
      const username = new FormData(e.target).get('username');
      const password = new FormData(e.target).get('password');
      try{
        await apiFetch('/api/admin/login', { method: 'POST', body: JSON.stringify({ username, password }) });
        showAdmin();
      } catch (err){
        showNotice(loginNotice, err.message, 'error');
      }
    }

    async function checkSession(){
      try{
        await apiFetch('/api/admin/session');
        showAdmin();
      } catch {
        showLogin();
      }
    }

    function showAdmin(){
      adminView.classList.remove('hidden');
      loginView.classList.add('hidden');
      refreshAdminData();
    }

    function showLogin(){
      adminView.classList.add('hidden');
      loginView.classList.remove('hidden');
    }

    async function handleCreate(tableName, form){
      const payload = Object.fromEntries(new FormData(form).entries());
      await apiFetch(`/api/admin/${tableName}`, { method: 'POST', body: JSON.stringify({ action: 'create', record: payload }) });
      form.reset();
      refreshAdminData();
    }

    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('logoutBtn').addEventListener('click', async () => {
      await apiFetch('/api/admin/logout', { method: 'POST', body: JSON.stringify({}) });
      showLogin();
    });

    document.getElementById('meridianForm').addEventListener('submit', async (e) => {
      e.preventDefault(); await handleCreate('meridians', e.target);
    });

    document.getElementById('diseaseForm').addEventListener('submit', async (e) => {
      e.preventDefault(); await handleCreate('diseases', e.target);
    });

    document.getElementById('pointForm').addEventListener('submit', async (e) => {
      e.preventDefault(); await handleCreate('acupoints', e.target);
    });

    document.addEventListener('click', async (e) => {
      const t = e.target.closest('[data-action="delete"]');
      if(!t) return;
      const table = t.dataset.table;
      const id = Number(t.dataset.id);
      if(!id) return;
      await apiFetch(`/api/admin/${table}`, { method: 'POST', body: JSON.stringify({ action: 'delete', id }) });
      refreshAdminData();
    });

    checkSession();
  </script>
</body>
</html>
"""


def dict_from_row(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def fetch_query(sql: str, params: tuple = ()) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        return [dict_from_row(r) for r in rows]


def require_auth(cookie_header: str) -> bool:
    if not cookie_header:
        return False
    for part in cookie_header.split(';'):
        item = part.strip().split('=', 1)
        if len(item) == 2 and item[0] == SESSION_COOKIE and item[1] == 'logged-in':
            return True
    return False


def public_api(path: str, params: dict) -> tuple[int, dict | list | str]:
    keyword = params.get('keyword', [None])[0]

    if path == '/api/health':
        return 200, {'status': 'ok', 'database': str(DB_PATH)}

    if path == '/api/meridians':
        sql = """
            SELECT m.id, m.name, m.code, m.category, m.description
            FROM meridians m
            WHERE (? IS NULL OR m.name LIKE '%' || ? || '%' OR m.code LIKE '%' || ? || '%' OR m.category LIKE '%' || ? || '%')
            ORDER BY m.id
        """
        return 200, fetch_query(sql, (keyword, keyword, keyword, keyword))

    if path == '/api/diseases':
        sql = """
            SELECT d.id, d.name, d.category, d.description
            FROM diseases d
            WHERE (? IS NULL OR d.name LIKE '%' || ? || '%' OR d.category LIKE '%' || ? || '%')
            ORDER BY d.id
        """
        return 200, fetch_query(sql, (keyword, keyword, keyword))

    if path == '/api/acupoints':
        sql = """
            SELECT a.id, a.name, a.pinyin, m.name AS meridian_name, a.location, a.note, a.classic_code
            FROM acupoints a
            JOIN meridians m ON m.id = a.meridian_id
            WHERE (? IS NULL OR a.name LIKE '%' || ? || '%' OR a.pinyin LIKE '%' || ? || '%' OR m.name LIKE '%' || ? || '%')
            ORDER BY a.id
        """
        return 200, fetch_query(sql, (keyword, keyword, keyword, keyword))

    if path == '/api/by-disease':
        if not keyword:
            return 200, []
        sql = """
            SELECT a.name AS point_name, a.pinyin, m.name AS meridian_name, d.name AS disease_name, p.evidence
            FROM point_disease p
            JOIN acupoints a ON a.id = p.point_id
            JOIN meridians m ON m.id = a.meridian_id
            JOIN diseases d ON d.id = p.disease_id
            WHERE d.name LIKE '%' || ? || '%'
            ORDER BY a.id
        """
        return 200, fetch_query(sql, (keyword,))

    if path == '/api/by-meridian':
        if not keyword:
            return 200, []
        sql = """
            SELECT a.name AS point_name, a.pinyin, m.name AS meridian_name, a.location
            FROM acupoints a
            JOIN meridians m ON m.id = a.meridian_id
            WHERE m.name LIKE '%' || ? || '%'
            ORDER BY a.id
        """
        return 200, fetch_query(sql, (keyword,))

    return 404, {'error': 'Not found'}


def admin_api(path: str, payload: dict, cookie_header: str) -> tuple[int, dict | list | str]:
    if not require_auth(cookie_header):
        return 401, {'error': 'unauthorized'}

    if path == '/api/admin/session':
        return 200, {'authenticated': True}

    if path == '/api/admin/summary':
        with sqlite3.connect(DB_PATH) as conn:
            meridians = conn.execute('SELECT COUNT(*) FROM meridians').fetchone()[0]
            acupoints = conn.execute('SELECT COUNT(*) FROM acupoints').fetchone()[0]
            diseases = conn.execute('SELECT COUNT(*) FROM diseases').fetchone()[0]
        return 200, {'meridians': meridians, 'acupoints': acupoints, 'diseases': diseases}

    if path == '/api/admin/meridians':
        if payload.get('action') == 'create':
            record = payload.get('record', {})
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    'INSERT INTO meridians (name, code, category, description) VALUES (?, ?, ?, ?)',
                    (record.get('name'), record.get('code'), record.get('category'), record.get('description'))
                )
                conn.commit()
            return 200, {'success': True}

        if payload.get('action') == 'delete':
            item_id = int(payload.get('id', 0))
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('DELETE FROM meridians WHERE id = ?', (item_id,))
                conn.commit()
            return 200, {'success': True}

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT * FROM meridians ORDER BY id').fetchall()
            return 200, [dict_from_row(r) for r in rows]

    if path == '/api/admin/diseases':
        if payload.get('action') == 'create':
            record = payload.get('record', {})
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    'INSERT INTO diseases (name, category, description) VALUES (?, ?, ?)',
                    (record.get('name'), record.get('category'), record.get('description'))
                )
                conn.commit()
            return 200, {'success': True}

        if payload.get('action') == 'delete':
            item_id = int(payload.get('id', 0))
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('DELETE FROM diseases WHERE id = ?', (item_id,))
                conn.commit()
            return 200, {'success': True}

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT * FROM diseases ORDER BY id').fetchall()
            return 200, [dict_from_row(r) for r in rows]

    if path == '/api/admin/acupoints':
        if payload.get('action') == 'create':
            record = payload.get('record', {})
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    'INSERT INTO acupoints (name, pinyin, meridian_id, location, note, classic_code, meridian_name) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (
                        record.get('name'),
                        record.get('pinyin'),
                        int(record.get('meridian_id', 0)),
                        record.get('location'),
                        record.get('note'),
                        record.get('classic_code'),
                        record.get('meridian_name')
                    )
                )
                conn.commit()
            return 200, {'success': True}

        if payload.get('action') == 'delete':
            item_id = int(payload.get('id', 0))
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('DELETE FROM acupoints WHERE id = ?', (item_id,))
                conn.commit()
            return 200, {'success': True}

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT a.*, m.name AS meridian_name
                FROM acupoints a
                JOIN meridians m ON m.id = a.meridian_id
                ORDER BY a.id
            ''').fetchall()
            return 200, [dict_from_row(r) for r in rows]

    return 404, {'error': 'Not found'}


class AcupunctureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/':
            self._send_html(200, HTML_PAGE)
            return

        if path == '/admin':
            self._send_html(200, ADMIN_PAGE)
            return

        if path.startswith('/api/'):
            status, payload = public_api(path, params)
            self._send_json(status, payload)
            return

        self._send_plain(404, 'Not found')

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length).decode('utf-8') if length else ''
        payload = json.loads(body) if body else {}

        if path == '/api/admin/login':
            username = payload.get('username')
            password = payload.get('password')
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                body_b = json.dumps({'status': 'ok'}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Set-Cookie', f'{SESSION_COOKIE}=logged-in; Path=/; HttpOnly')
                self.send_header('Content-Length', str(len(body_b)))
                self.end_headers()
                self.wfile.write(body_b)
                return
            self._send_json(401, {'error': 'invalid credentials'})
            return

        if path == '/api/admin/logout':
            body_b = json.dumps({'status': 'ok'}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Set-Cookie', f'{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly')
            self.send_header('Content-Length', str(len(body_b)))
            self.end_headers()
            self.wfile.write(body_b)
            return

        if path.startswith('/api/admin/'):
            status, payload = admin_api(path, payload, self.headers.get('Cookie', ''))
            self._send_json(status, payload)
            return

        self._send_json(404, {'error': 'Not found'})

    def _send_html(self, status: int, html: str):
        data = html.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: int, payload):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_plain(self, status: int, message: str):
        data = message.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        return


def run() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f'資料庫不存在: {DB_PATH}\n請先執行: py -3 scripts/build_jia_yi_jing_db.py')
    server = ThreadingHTTPServer(('0.0.0.0', 8000), AcupunctureHandler)
    print('甲乙經穴位查詢系統啟動中... http://localhost:8000')
    print(f'管理後台登入：{ADMIN_USERNAME} / {ADMIN_PASSWORD}')
    server.serve_forever()


if __name__ == '__main__':
    run()
