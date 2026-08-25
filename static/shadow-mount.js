// shadow-mount.js — IIFE: host DOM purge + Shadow DOM mounter
// Runs before paint. Returns shadow root for callers via window.__m3ShadowRoot.
(function () {
  "use strict";

  // ── A) Kill Anki's injected <style> tags that target card containers ──
  var sheets = document.querySelectorAll("style");
  for (var s = 0; s < sheets.length; s++) {
    var txt = sheets[s].textContent || "";
    if (/(?:#qa|#qa-body|\.card\b)/.test(txt)) {
      sheets[s].parentNode.removeChild(sheets[s]);
    }
  }

  // ── B) Strip inline styles from host containers ──────────────────────
  var hostSels = ["html", "body", "#qa", "#qa-body", ".card"];
  for (var i = 0; i < hostSels.length; i++) {
    var el = document.querySelector(hostSels[i]);
    if (!el) continue;
    el.removeAttribute("style");
    el.style.cssText =
      "margin:0!important;padding:0!important;border:0!important;" +
      "outline:0!important;width:100%!important;min-height:100vh!important;" +
      "background:transparent!important;overflow:auto!important;" +
      "-webkit-text-size-adjust:100%!important;text-size-adjust:100!important;" +
      "overscroll-behavior:none!important;";
  }

  // ── C) Inject override styles into main document ─────────────────────
  // Ensures no Anki CSS reaches the shadow host or its ancestors.
  var override = document.createElement("style");
  override.textContent =
    "#qa, #qa-body, .card {" +
    "  margin:0!important;padding:0!important;border:0!important;" +
    "  background:transparent!important;overflow:auto!important;" +
    "  min-height:100vh!important;" +
    "}" +
    "#app-root {" +
    "  all:initial!important;display:block!important;" +
    "  min-height:100vh!important;" +
    "}";
  document.head.appendChild(override);

  // Block platform gestures that disrupt native web feel
  var block = function (e) { e.preventDefault(); };
  document.addEventListener("contextmenu", block, true);
  document.addEventListener("dragstart", block, true);
  document.addEventListener("selectstart", block, true);
  document.body.style.userSelect = "none";
  document.body.style.webkitUserSelect = "none";

  // ── D) Shadow DOM mount ─────────────────────────────────────────────
  var root = document.getElementById("app-root");
  if (!root) {
    root = document.createElement("div");
    root.id = "app-root";
    document.body.appendChild(root);
  }

  var tmpl = document.getElementById("app-template");
  var shadow = null;

  try {
    // Detach existing shadow root if present (night mode re-render)
    if (root.shadowRoot) {
      root.shadowRoot.innerHTML = "";
    }
    shadow = root.attachShadow({ mode: "open" });
    if (tmpl) {
      shadow.appendChild(tmpl.content.cloneNode(true));
    }
  } catch (e) {
    // Fallback: light DOM — clone template content directly into root
    if (tmpl) {
      root.innerHTML = "";
      root.appendChild(tmpl.content.cloneNode(true));
    }
    shadow = root;
  }

  // Expose for init scripts
  window.__m3ShadowRoot = shadow;
})();
