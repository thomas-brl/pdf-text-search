import os
import sys
import time
import socket
import threading
import urllib.request
import concurrent.futures
import pdfplumber
from flask import Flask, request, jsonify, send_from_directory, Response
from werkzeug.exceptions import HTTPException

SEARCH_TIMEOUT = 60

PDFS_DIR = None

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PDF Search</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<style>
:root {
  --bg:           #F0F2F5;
  --surface:      #FFFFFF;
  --text:         #111827;
  --text-muted:   #6B7280;
  --border:       #E5E7EB;
  --accent:       #4F46E5;
  --accent-light: #EEF2FF;
  --radius:       12px;
  --shadow-sm:    0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.04);
  --shadow-md:    0 6px 20px rgba(0,0,0,.10), 0 2px 6px rgba(0,0,0,.06);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
  padding: 28px 24px; justify-content: space-between;
  display: flex; align-items: center; gap: 14px;
}

.logo {
  font-size: 25px; font-weight: 700; letter-spacing: -.02em;
  color: var(--accent); white-space: nowrap; flex-shrink: 0;
}
.logo span { color: var(--text); }

.search-wrap {
  flex: 0.8; display: flex;
  background: var(--bg); border: 1.5px solid var(--border);
  border-radius: 50px; padding-left: 18px;
  transition: border-color .15s, box-shadow .15s;
}
.search-wrap:focus-within {
  border-color: var(--accent); box-shadow: 0 0 0 3px rgba(79,70,229,.12); background: #fff;
}
.search-wrap input {
  flex: 1; border: none; background: transparent;
  font-family: inherit; font-size: 18px; color: var(--text); outline: none; padding: 10px 0;
}
.search-wrap input::placeholder { color: var(--text-muted); }
.search-wrap button {
  background: var(--accent); color: #fff; border: none; border-radius: 50px;
  padding: 8px 20px; font-family: inherit; font-size: 18px; font-weight: 400;
  cursor: pointer; white-space: nowrap; transition: background .15s, transform .1s;
}
.search-wrap button:hover  { background: #4338CA; }
.search-wrap button:active { transform: scale(.97); }

#btn-folder {
  display: flex; align-items: center; gap: 7px; flex-shrink: 0;  height: 38px;
  font-family: inherit; font-size: 12px; font-weight: 500; color: var(--text-muted);
  background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
  padding: 7px 12px; cursor: pointer; max-width: 240px;
  transition: border-color .15s, color .15s, background .15s;
}
#btn-folder:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-light); }
#btn-folder svg   { flex-shrink: 0; }
#folder-label     { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

#btn-quit {
  flex-shrink: 0; width: 38px; height: 38px; border: none; background: var(--bg);
  border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: var(--text-muted); transition: background .12s, color .12s;
}
#btn-quit:hover { background: #FFE4E4; color: #DC2626; }

main { max-width: 1280px; margin: 0 auto; padding: 36px 28px 60px; }

.state-center { text-align: center; padding: 90px 20px; }
.state-center .icon { font-size: 52px; margin-bottom: 18px; }
.state-center h2   { font-size: 22px; font-weight: 700; letter-spacing: -.02em; margin-bottom: 8px; }
.state-center p    { font-size: 14px; color: var(--text-muted); line-height: 1.6; }

.folder-prompt-btn {
  margin-top: 24px; display: inline-flex; align-items: center; gap: 8px;
  background: var(--accent); color: #fff; border: none; border-radius: 10px;
  padding: 12px 24px; font-family: inherit; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background .15s, transform .1s;
}
.folder-prompt-btn:hover  { background: #4338CA; }
.folder-prompt-btn:active { transform: scale(.97); }

.spinner-wrap { text-align: center; padding: 70px 20px; }
.spinner {
  width: 100px; height: 100px; border: 5px solid var(--border); border-top-color: var(--accent);
  border-radius: 50%; animation: spin .7s linear infinite; margin: 0 auto 14px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.spinner-wrap p { font-size: 14px; color: var(--text-muted); font-weight: 500; }

.results-meta { font-size: 13px; color: var(--text-muted); margin-bottom: 22px; }
.results-meta strong { color: var(--text); font-weight: 600; }

.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 18px; }

.card {
  background: var(--surface); border-radius: var(--radius); border: 1px solid var(--border);
  box-shadow: var(--shadow-sm); overflow: hidden; cursor: pointer;
  display: flex; flex-direction: column; transition: transform .2s ease, box-shadow .2s ease;
}
.card:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); }

.card-thumb {
  width: 100%; aspect-ratio: 1 / 1.414; background: #F8FAFC;
  position: relative; overflow: hidden; border-bottom: 1px solid var(--border);
}
.card-thumb.shimmer {
  background: linear-gradient(90deg, #F0F2F5 25%, #E4E7EC 50%, #F0F2F5 75%);
  background-size: 200% 100%; animation: shimmer 1.3s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

.card-thumb canvas { position: absolute; top: 0; left: 0; width: 100%; height: auto; display: block; }
.thumb-icon { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #CBD5E1; }

.card-body { padding: 12px 13px 13px; flex: 1; display: flex; flex-direction: column; gap: 3px; }
.card-name {
  font-size: 13px; font-weight: 600; line-height: 1.35;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.card-path { font-size: 11px; color: var(--text-muted); word-break: break-all; margin-bottom: 4px; }
.card-pages { display: flex; flex-wrap: wrap; gap: 4px; margin-top: auto; padding-top: 6px; }

.page-chip {
  font-size: 11px; font-weight: 500; color: var(--accent); background: var(--accent-light);
  border-radius: 4px; padding: 3px 7px; border: none; font-family: inherit;
  cursor: pointer; transition: background .12s, color .12s;
}
.page-chip:hover { background: var(--accent); color: #fff; }

#modal-overlay {
  display: none; position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,.45); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
  align-items: center; justify-content: center; padding: 32px; animation: fadeIn .18s ease;
}
#modal-overlay.open { display: flex; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

#modal-box {
  width: 100%; max-width: 960px; height: 98vh; background: #fff; border-radius: 16px;
  box-shadow: 0 24px 64px rgba(0,0,0,.30); overflow: hidden;
  display: flex; flex-direction: column; animation: slideUp .2s ease;
}
@keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }

#modal-header { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--border); }
#modal-info { flex: 1; overflow: hidden; }
#modal-title { font-size: 13px; font-weight: 600; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#modal-path  { font-size: 11px; color: var(--text-muted); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

#modal-close {
  flex-shrink: 0; width: 32px; height: 32px; border: none; background: var(--bg);
  border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: var(--text-muted); transition: background .12s, color .12s;
}
#modal-close:hover { background: #FFE4E4; color: #DC2626; }
#modal-iframe { flex: 1; border: none; width: 100%; }

</style>
</head>
<body>

<header>
  <div class="logo">PDF <span>Search</span></div>

  <div class="search-wrap">
    <input id="word" type="text" autocomplete="off"
           placeholder="Enter the word to search for in the PDFs"
           onkeydown="if(event.key==='Enter') doSearch()">
    <button onclick="doSearch()">Search</button>
  </div>

  <button id="btn-folder" onclick="chooseFolder()" title="Change PDF folder">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
    </svg>
    <span id="folder-label">Choose a folder…</span>
  </button>

  <button id="btn-quit" onclick="quitApp()" title="Close the application">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
      <path d="M18 6 6 18M6 6l12 12"/>
    </svg>
  </button>
</header>

<main><div id="content"></div></main>

<div id="modal-overlay" onclick="closeModal(event)">
  <div id="modal-box">
    <div id="modal-header">
      <div id="modal-info">
        <div id="modal-title"></div>
        <div id="modal-path"></div>
      </div>
      <button id="modal-close" onclick="closeModal()" title="Close">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <path d="M18 6 6 18M6 6l12 12"/>
        </svg>
      </button>
    </div>
    <iframe id="modal-iframe"></iframe>
  </div>
</div>

<script>
pdfjsLib.GlobalWorkerOptions.workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

const PDF_ICON = `<svg width="40" height="40" viewBox="0 0 24 24" fill="none"
  stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586
           a1 1 0 01.707.293l5.414 5.414A1 1 0 0121 10.414V19a2 2 0 01-2 2z"/></svg>`;

let currentDir = null;

function setFolderLabel(dir) {
  currentDir = dir || null;
  const name = dir ? dir.replace(/\\/g, '/').split('/').filter(Boolean).pop() : null;
  document.getElementById('folder-label').textContent = name || 'Choose a folder…';
  document.getElementById('btn-folder').title = dir || 'Choose the PDF folder';
}

async function chooseFolder() {
  if (window.pywebview) {
    const dir = await window.pywebview.api.choose_folder();
    if (dir) {
      setFolderLabel(dir);
      showIdle();
    }
  } else {
    const dir = prompt("Absolute path to the PDF folder:");
    if (!dir) return;
    const res  = await fetch('/config', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pdfs_dir: dir }),
    });
    const data = await res.json();
    if (data.ok) { setFolderLabel(data.pdfs_dir); showIdle(); }
    else alert("Folder not found: " + dir);
  }
}

function showIdle() {
  setContent(`<div class="state-center">
    <div class="icon">🔍</div>
    <h2>PDF Text Search</h2>
    <p>Enter a word in the search bar to find<br>
       every document and page that contains it.</p>
  </div>`);
}

function showFolderPrompt() {
  setContent(`<div class="state-center">
    <div class="icon">📁</div>
    <h2>Choose the PDF folder</h2>
    <p>Point to where your PDF files are located.<br>
       All subfolders will be included automatically.</p>
    <button class="folder-prompt-btn" onclick="chooseFolder()">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
      </svg>
      Select a folder
    </button>
  </div>`);
}

function setContent(html) {
  document.getElementById('content').innerHTML = html;
}

window.addEventListener('DOMContentLoaded', async () => {
  try {
    const { pdfs_dir } = await fetch('/config').then(r => r.json());
    if (pdfs_dir) { setFolderLabel(pdfs_dir); showIdle(); }
    else showFolderPrompt();
  } catch {
    showFolderPrompt();
  }
});

function openModal(url, filename, folder, page) {
  document.getElementById('modal-iframe').src  = page ? `${url}#page=${page}` : url;
  document.getElementById('modal-title').textContent = filename;
  document.getElementById('modal-path').textContent  = folder || 'Root';
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal(e) {
  if (e && e.target !== document.getElementById('modal-overlay')) return;
  document.getElementById('modal-overlay').classList.remove('open');
  document.getElementById('modal-iframe').src = '';
  document.body.style.overflow = '';
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

const encodePath = p => p.split('/').map(encodeURIComponent).join('/');
const splitPath  = p => {
  const i = p.lastIndexOf('/');
  return i === -1 ? { folder: '', filename: p }
                  : { folder: p.slice(0, i), filename: p.slice(i + 1) };
};

async function renderThumb(pdfUrl, el) {
  try {
    const pdf  = await pdfjsLib.getDocument(pdfUrl).promise;
    const page = await pdf.getPage(1);
    const vp   = page.getViewport({ scale: 1 });
    const svp  = page.getViewport({ scale: (el.clientWidth || 200) / vp.width });
    const c    = document.createElement('canvas');
    c.width = svp.width; c.height = svp.height;
    await page.render({ canvasContext: c.getContext('2d'), viewport: svp }).promise;
    el.classList.remove('shimmer');
    el.innerHTML = '';
    el.appendChild(c);
  } catch {
    el.classList.remove('shimmer');
    el.innerHTML = `<div class="thumb-icon">${PDF_ICON}</div>`;
  }
}

async function doSearch() {
  const word = document.getElementById('word').value.trim();
  if (!word) return;

  setContent(`<div class="spinner-wrap"><div class="spinner"></div><p>Reading documents…</p></div>`);

  let res, data;
  try {
    res  = await fetch(`/search?word=${encodeURIComponent(word)}`);
    data = await res.json();
  } catch {
    setContent(`<div class="state-center"><div class="icon">⚠️</div>
      <h2>Error</h2><p>Unable to reach the Flask server.</p></div>`);
    return;
  }

  if (!res.ok) {
    const icons = { 503: '🔌', 404: '📁', 504: '⏱️' };
    const icon  = icons[res.status] || '⚠️';
    const msg   = data.message || `Error ${res.status}`;
    setContent(`<div class="state-center"><div class="icon">${icon}</div>
      <h2>Error ${res.status}</h2>
      <p>${esc(msg)}</p></div>`);
    return;
  }

  const entries = Object.entries(data);

  if (!entries.length) {
    setContent(`<div class="state-center"><div class="icon">⭕</div>
      <h2>No results</h2>
      <p>"${esc(word)}" was not found in any document in the folder<br>
      <code style="font-size:12px;color:var(--text-muted)">${esc(currentDir)}</code></p></div>`);
    return;
  }

  const n = entries.length;
  setContent(`<p class="results-meta">
      <strong>${n} document${n > 1 ? 's' : ''}</strong>
      found for "${esc(word)}"
    </p><div class="cards-grid" id="grid"></div>`);

  const grid  = document.getElementById('grid');
  const queue = [];

  for (const [relPath, pages] of entries) {
    const { folder, filename } = splitPath(relPath);
    const url = `/pdfs/${encodePath(relPath)}`;

    const card = document.createElement('div');
    card.className = 'card';

    const thumb = document.createElement('div');
    thumb.className = 'card-thumb shimmer';
    thumb.innerHTML = `<div class="thumb-icon">${PDF_ICON}</div>`;

    const nameEl = document.createElement('p');
    nameEl.className = 'card-name';
    nameEl.textContent = filename;

    const pathEl = document.createElement('p');
    pathEl.className = 'card-path';
    pathEl.textContent = folder || 'Root';

    const pagesEl = document.createElement('div');
    pagesEl.className = 'card-pages';
    for (const p of pages) {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'page-chip';
      chip.textContent = `page ${p}`;
      chip.addEventListener('click', (e) => {
        e.stopPropagation();
        openModal(url, filename, folder, p);
      });
      pagesEl.appendChild(chip);
    }

    const body = document.createElement('div');
    body.className = 'card-body';
    body.append(nameEl, pathEl, pagesEl);

    card.append(thumb, body);
    card.addEventListener('click', () => openModal(url, filename, folder));
    grid.appendChild(card);
    queue.push([url, thumb]);
  }

  requestAnimationFrame(() => queue.forEach(([u, el]) => renderThumb(u, el)));
}

const esc = s => String(s).replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[c]));

function quitApp() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.quit();
  } else {
    console.warn("pywebview API not available");
  }
}
</script>
</body>
</html>"""

def search_pdfs(folder_path, word):
    results = {}
    if not word or not folder_path:
        return results
    word_lower = word.lower()
    for root, _dirs, files in os.walk(folder_path):
        for filename in files:
            if not filename.lower().endswith(".pdf"):
                continue
            pdf_path = os.path.join(root, filename)
            rel_path = os.path.relpath(pdf_path, folder_path).replace(os.sep, "/")
            matches  = []
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text() or ""
                        if word_lower in text.lower():
                            matches.append(page_num)
            except Exception as exc:
                print(f"[SKIP] {pdf_path}: {exc}")
                continue
            if matches:
                results[rel_path] = matches
    return results

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return Response(INDEX_HTML, mimetype="text/html")

@flask_app.route("/pdfs/<path:filename>")
def serve_pdf(filename):
    return send_from_directory(PDFS_DIR, filename)

@flask_app.route("/config", methods=["GET", "POST"])
def get_config():
    global PDFS_DIR

    if request.method == "GET":
        return jsonify({"pdfs_dir": PDFS_DIR})

    payload = request.get_json(silent=True) or {}
    new_dir = (payload.get("pdfs_dir") or "").strip()

    if not new_dir or not os.path.isdir(new_dir):
        return jsonify({"ok": False, "message": f"Folder not found: {new_dir}"}), 400

    PDFS_DIR = new_dir
    return jsonify({"ok": True, "pdfs_dir": PDFS_DIR})

@flask_app.route("/search")
def search():
    word = request.args.get("word", "")

    if not PDFS_DIR:
        return jsonify({"error": "not_found", "message": "No folder selected."}), 404

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            accessible = ex.submit(os.path.isdir, PDFS_DIR).result(timeout=5)
    except concurrent.futures.TimeoutError:
        return jsonify({"error": "unreachable", "message": f"Folder unreachable or too slow: {PDFS_DIR}"}), 503
    except Exception as e:
        return jsonify({"error": "check_failed", "message": str(e)}), 503

    if not accessible:
        return jsonify({"error": "not_found", "message": f"Folder not found: {PDFS_DIR}"}), 404

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            results = ex.submit(search_pdfs, PDFS_DIR, word).result(timeout=SEARCH_TIMEOUT)
        return jsonify(results)
    except concurrent.futures.TimeoutError:
        return jsonify({"error": "timeout", "message": f"Search took too long (> {SEARCH_TIMEOUT}s)"}), 504
    except Exception as e:
        return jsonify({"error": "search_failed", "message": str(e)}), 500

@flask_app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify({"error": e.name, "message": e.description}), e.code
    return jsonify({"error": "server_error", "message": str(e)}), 500

class API:
    def choose_folder(self):
        global PDFS_DIR
        import webview
        result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            PDFS_DIR = result[0]
            return PDFS_DIR
        return None

    def quit(self):
        import webview
        webview.windows[0].destroy()

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def wait_for_flask(port, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=0.3)
            return True
        except Exception:
            time.sleep(0.05)
    return False

if __name__ == "__main__":
    import webview

    port = find_free_port()

    threading.Thread(
        target=lambda: flask_app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True),
        daemon=True,
    ).start()

    if not wait_for_flask(port):
        print("Flask did not start in time.", file=sys.stderr)
        sys.exit(1)

    webview.create_window(
        title     = "PDF Search",
        url       = f"http://127.0.0.1:{port}",
        js_api    = API(),
        width     = 1400,
        height    = 900,
        min_size  = (900, 600),
        maximized = True,
    )
    webview.start()