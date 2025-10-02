<template>
  <div>
    <NavBar />
    <main class="container">
      <router-view />
    </main>
    <SiteFooter />
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
import SiteFooter from './components/SiteFooter.vue'
</script>

<style>
:root {
  /* Light theme similar to YouTube */
  --surface: #ffffff;        /* cards and containers */
  --app-bg: #f8f9fb;         /* page background */
  --border: #e5e7eb;         /* light gray border */
  --text: #0f172a;           /* main text */
  --muted: #6b7280;          /* secondary text */
  --accent: #2563eb;         /* primary action */

  /* Global radius scale */
  --radius-card: 12px;
  --radius-input: 8px;
  --radius-btn: 10px;
}
body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica Neue, Arial, "Apple Color Emoji", "Segoe UI Emoji"; background: var(--app-bg); color: var(--text); }
.container, body, html, * , *::before, *::after { box-sizing: border-box; }
.container { max-width: 1280px; margin: 0 auto 24px; padding: 0 8px; }
.container-fluid { width: 100%; margin: 0 auto; padding: 0; }
/* space below navbar */
main.container { padding-top: 12px; }
/* avoid collapsed top margins from first section (orange gap) */
main.container > *:first-child { margin-top: 0; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-card); padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.btn { background: var(--accent); color: #fff; border: 1px solid rgba(0,0,0,0.08); padding: 10px 16px; border-radius: var(--radius-btn); cursor: pointer; box-sizing: border-box; }
.btn:hover { filter: brightness(0.98); }
.btn.secondary { background: #6b7280; }
.btn.is-loading { position: relative; color: transparent !important; pointer-events: none; }
.btn.is-loading::after { content: ""; position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
.btn.is-loading::before {
  content: "";
  position: absolute;
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.6);
  border-top-color: rgba(255,255,255,0.2);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }
.input { width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: var(--radius-input); box-sizing: border-box; background:#fff; }
.grid { display: grid; gap: 16px; }
.grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
@media (max-width: 900px){ .grid.cols-3 { grid-template-columns: repeat(2, 1fr); }}
@media (max-width: 600px){ .grid.cols-3 { grid-template-columns: 1fr; }}
</style>
