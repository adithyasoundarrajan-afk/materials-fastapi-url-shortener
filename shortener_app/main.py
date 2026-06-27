import os  # <-- Make sure this is at the very top
import validators
from sqlalchemy.orm import Session
from starlette.datastructures import URL

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse  # <-- Make sure HTMLResponse is here

from . import crud, models, schemas
from .config import get_settings
from .database import SessionLocal, engine

# 1. First, create the app instance!
app = FastAPI()
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)

def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)


# 2. Now it is safe to use @app.get("/") since 'app' is defined above!
@app.get("/", response_class=HTMLResponse)
def read_root():
    # We are going to hardcode your exact premium html template right here
    html_content = """
<!doctype html>
<html lang="en">
 <head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Premium URL Shortener</title>
  <script src="https://cdn.tailwindcss.com/3.4.17"></script>
  <script src="https://cdn.jsdelivr.net/npm/lucide@0.263.0/dist/umd/lucide.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&amp;family=Space+Mono:wght@400;700&amp;display=swap" rel="stylesheet">
  <style>
    body { font-family: 'DM Sans', sans-serif; background-color: #0f0f1a; color: #ffffff; }
    .mono { font-family: 'Space Mono', monospace; }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes pulse-glow { 0%, 100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.4); } 50% { box-shadow: 0 0 20px 4px rgba(16,185,129,0.2); } }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
    .anim-fade-up { animation: fadeUp 0.7s ease both; }
    .anim-fade-in { animation: fadeIn 0.5s ease both; }
    .anim-slide-in { animation: slideIn 0.4s ease both; }
    .anim-float { animation: float 3s ease-in-out infinite; }
    .anim-pulse-glow { animation: pulse-glow 2s ease-in-out infinite; }
    .delay-1 { animation-delay: 0.1s; }
    .delay-2 { animation-delay: 0.25s; }
    .delay-3 { animation-delay: 0.4s; }
    .url-card { transition: transform 0.25s ease, box-shadow 0.25s ease; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); }
    .url-card:hover { transform: translateY(-3px) scale(1.01); box-shadow: 0 8px 30px rgba(16,185,129,0.12); border-color: rgba(16,185,129,0.3); }
    .btn-shorten { transition: transform 0.15s ease, box-shadow 0.15s ease; }
    .btn-shorten:hover { transform: scale(1.05); box-shadow: 0 4px 20px rgba(16,185,129,0.3); }
    .btn-shorten:active { transform: scale(0.97); }
    .delete-btn { transition: transform 0.2s ease, color 0.2s ease; }
    .delete-btn:hover { transform: scale(1.2); }
    .copy-flash { animation: fadeIn 0.3s ease; color: #10b981 !important; }
    .row-exit { animation: fadeOut 0.3s ease forwards; }
    @keyframes fadeOut { to { opacity: 0; transform: translateX(20px); height: 0; padding: 0; margin: 0; overflow: hidden; } }
  </style>
 </head>
 <body class="min-h-screen w-full">
  <header class="relative overflow-hidden py-24 px-6">
   <div class="absolute inset-0 bg-gradient-to-b from-emerald-950/20 via-transparent to-[#0f0f1a]"></div>
   <div class="relative z-10 max-w-3xl mx-auto text-center">
    <div class="anim-float inline-block mb-6">
     <div class="w-16 h-16 mx-auto rounded-2xl bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
      <i data-lucide="link" style="width:28px;height:28px;color:#10b981"></i>
     </div>
    </div>
    <h1 class="text-4xl font-bold mb-3 anim-fade-up delay-1 text-white">Sleek URL Shortener</h1>
    <p class="text-gray-400 mb-10 anim-fade-up delay-2">Paste your long link to generate an optimized, shareable short link.</p>
    <form id="shorten-form" class="flex gap-3 max-w-xl mx-auto anim-fade-up delay-3">
      <input id="url-input" type="url" placeholder="Paste your long URL here..." required class="flex-1 px-5 py-3.5 rounded-xl border border-white/10 bg-white/5 outline-none text-sm text-white backdrop-blur focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 transition-all"> 
      <button type="submit" class="btn-shorten bg-emerald-500 hover:bg-emerald-600 text-slate-950 px-7 py-3.5 rounded-xl font-bold whitespace-nowrap anim-pulse-glow">Shorten Link</button>
    </form>
    <div id="result" class="hidden mt-6 p-5 rounded-xl bg-white/5 backdrop-blur-lg border border-emerald-500/20 text-left max-w-xl mx-auto anim-slide-in space-y-3">
      <div class="flex items-center justify-between gap-3">
        <div>
          <span class="block text-xs uppercase text-gray-400 font-bold tracking-wider mb-1">Shortened URL</span>
          <span id="result-url" class="mono text-sm text-emerald-300 font-bold break-all"></span>
        </div>
        <button id="copy-btn" class="text-white hover:text-emerald-300 transition-colors shrink-0 p-2 bg-white/5 rounded-lg" title="Copy URL">
          <i data-lucide="copy" style="width:18px;height:18px"></i>
        </button>
      </div>
      <div class="border-t border-white/10 pt-2 flex items-center justify-between gap-3">
        <div>
          <span class="block text-xs uppercase text-amber-400 font-bold tracking-wider mb-1">Admin Info Link (Save to view stats)</span>
          <span id="admin-url" class="mono text-xs text-amber-200 opacity-80 break-all"></span>
        </div>
        <button id="copy-admin-btn" class="text-white hover:text-amber-300 transition-colors shrink-0 p-2 bg-white/5 rounded-lg" title="Copy Admin URL">
          <i data-lucide="copy" style="width:18px;height:18px"></i>
        </button>
      </div>
    </div>
    <p id="error-msg" class="hidden mt-4 text-red-400 text-sm anim-fade-in"></p>
   </div>
  </header>
  <main class="max-w-4xl mx-auto px-6 py-4">
   <h2 class="text-xl font-bold mb-6 anim-fade-up text-white">Your Shortened Links</h2>
   <p id="empty-state" class="text-center text-gray-500 py-8">No links generated in this session yet.</p>
   <div id="url-list" class="space-y-3"></div>
  </main>
  <template id="url-row-template">
   <div class="url-card rounded-xl p-5 flex flex-col sm:flex-row sm:items-center gap-3 anim-slide-in">
    <div class="flex-1 min-w-0">
     <a href="#" target="_blank" data-id="url-row-short" class="mono text-sm font-bold text-emerald-400 hover:underline truncate block"></a>
     <p data-id="url-row-original" class="text-xs truncate text-gray-400 mt-1"></p>
    </div>
    <div class="flex items-center gap-4 shrink-0">
      <span data-id="url-row-clicks" class="text-xs px-3 py-1 rounded-full bg-white/5 border border-white/10 text-gray-300 font-medium"></span> 
      <button class="delete-btn text-red-400 hover:text-red-300 p-1" title="Delete">
        <i data-lucide="trash-2" style="width:16px;height:16px"></i>
      </button>
    </div>
   </div>
  </template>
  <footer class="border-t border-white/10 mt-12 py-10 px-6 bg-black/20">
   <div class="max-w-4xl mx-auto text-center">
    <p class="text-gray-500 text-xs uppercase tracking-widest mb-1">Developer</p>
    <h3 class="text-white font-bold mb-3">Adithya Soundarrajan</h3>
    <div class="flex justify-center gap-6">
      <a href="mailto:adithyasoundarrajan@gmail.com" class="text-sm text-gray-400 hover:text-emerald-400 transition-colors">Email</a> 
      <a href="https://www.linkedin.com/in/adithyasoundarrajan/" target="_blank" rel="noopener noreferrer" class="text-sm text-gray-400 hover:text-emerald-400 transition-colors">LinkedIn</a>
    </div>
   </div>
  </footer>
  <script>
    let localHistory = JSON.parse(localStorage.getItem('shortener_history') || '[]');
    function saveHistory() { localStorage.setItem('shortener_history', JSON.stringify(localHistory)); }
    function showError(msg) {
      const el = document.getElementById('error-msg');
      el.textContent = msg; el.classList.remove('hidden');
      setTimeout(() => el.classList.add('hidden'), 4000);
    }
    function renderList() {
      const container = document.getElementById('url-list');
      const empty = document.getElementById('empty-state');
      container.innerHTML = '';
      empty.classList.toggle('hidden', localHistory.length > 0);
      localHistory.forEach((item) => {
        const tpl = document.getElementById('url-row-template');
        const row = tpl.content.cloneNode(true);
        const wrapper = row.firstElementChild;
        const shortLink = row.querySelector('[data-id="url-row-short"]');
        shortLink.textContent = item.url; shortLink.href = item.url;
        row.querySelector('[data-id="url-row-original"]').textContent = item.target_url;
        row.querySelector('[data-id="url-row-clicks"]').textContent = `${item.clicks || 0} clicks`;
        row.querySelector('.delete-btn').addEventListener('click', () => deleteEntry(item.secret_key, wrapper));
        container.appendChild(row);
      });
      lucide.createIcons();
    }
    async function deleteEntry(secretKey, element) {
      try {
        const response = await fetch(`/admin/${secretKey}`, { method: 'DELETE' });
        if (response.ok) {
          element.classList.add('row-exit');
          setTimeout(() => {
            localHistory = localHistory.filter(h => h.secret_key !== secretKey);
            saveHistory(); renderList();
          }, 300);
        } else { showError("Could not delete link."); }
      } catch (err) { showError("Network error."); }
    }
    async function syncClicks() {
      for (let i = 0; i < localHistory.length; i++) {
        try {
          const res = await fetch(`/admin/${localHistory[i].secret_key}`);
          if (res.ok) { const data = await res.json(); localHistory[i].clicks = data.clicks; }
        } catch (e) { console.error(e); }
      }
      saveHistory(); renderList();
    }
    document.getElementById('shorten-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const input = document.getElementById('url-input');
      const btn = e.target.querySelector('button[type="submit"]');
      btn.disabled = true; btn.style.opacity = '0.5';
      try {
        const response = await fetch('/url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_url: input.value })
        });
        if (!response.ok) { const errData = await response.json(); throw new Error(errData.detail || "Failed."); }
        const data = await response.json();
        document.getElementById('result-url').textContent = data.url;
        document.getElementById('admin-url').textContent = data.admin_url;
        document.getElementById('result').classList.remove('hidden');
        localHistory.unshift(data); saveHistory(); renderList();
        input.value = '';
      } catch (error) { showError(error.message); } finally { btn.disabled = false; btn.style.opacity = '1'; }
    });
    document.getElementById('copy-btn').addEventListener('click', () => {
      navigator.clipboard.writeText(document.getElementById('result-url').textContent);
      const btn = document.getElementById('copy-btn'); btn.classList.add('copy-flash');
      setTimeout(() => btn.classList.remove('copy-flash'), 600);
    });
    document.getElementById('copy-admin-btn').addEventListener('click', () => {
      navigator.clipboard.writeText(document.getElementById('admin-url').textContent);
      const btn = document.getElementById('copy-admin-btn'); btn.classList.add('copy-flash');
      setTimeout(() => btn.classList.remove('copy-flash'), 600);
    });
    renderList(); syncClicks(); lucide.createIcons();
  </script>
 </body>
</html>
    """
    return HTMLResponse(content=html_content)
@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url = crud.create_db_url(db=db, url=url)
    return get_admin_info(db_url)


@app.get("/{url_key}")
def forward_to_target_url(
    url_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@app.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
)
def get_url_info(
    secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)


@app.delete("/admin/{secret_key}")
def delete_url(
    secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.deactivate_db_url_by_secret_key(
        db, secret_key=secret_key
    ):
        message = (
            f"Successfully deleted shortened URL for '{db_url.target_url}'"
        )
        return {"detail": message}
    else:
        raise_not_found(request)