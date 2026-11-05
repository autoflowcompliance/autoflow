/* AutoFlow Compliance — site behaviour. No dependencies, no build step. */
(function () {
  'use strict';
  document.documentElement.classList.add('js');

  var FORM_ENDPOINT = 'https://formsubmit.co/ajax/autoflowcompliance@outlook.com';

  /* ---------- Mobile menu: button with aria-expanded, Escape closes ---------- */
  function initMenu() {
    var toggle = document.querySelector('.menu-toggle');
    var menu = document.getElementById('site-menu');
    if (!toggle || !menu) return;
    var desktop = window.matchMedia('(min-width: 1024px)');

    function setOpen(open, returnFocus) {
      toggle.setAttribute('aria-expanded', String(open));
      menu.classList.toggle('is-open', open);
      if (!open && returnFocus) toggle.focus();
    }
    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') setOpen(false, true);
    });
    document.addEventListener('click', function (e) {
      if (toggle.getAttribute('aria-expanded') === 'true' && !menu.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
    });
    menu.addEventListener('focusout', function (e) {
      if (desktop.matches) return;
      if (e.relatedTarget && !menu.contains(e.relatedTarget) && e.relatedTarget !== toggle) setOpen(false);
    });
    var onChange = function () { if (desktop.matches) setOpen(false); };
    if (desktop.addEventListener) desktop.addEventListener('change', onChange); else desktop.addListener(onChange);
  }

  /* ---------- Currency switch (pricing page) ---------- */
  function initCurrency() {
    var buttons = document.querySelectorAll('[data-currency]');
    if (!buttons.length) return;
    var live = document.getElementById('currency-status');

    function apply(cur, announce) {
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.currency === cur)); });
      document.querySelectorAll('[data-usd][data-gbp]').forEach(function (el) {
        el.textContent = cur === 'usd' ? el.dataset.usd : el.dataset.gbp;
      });
      if (announce && live) live.textContent = 'Prices now shown in ' + (cur === 'usd' ? 'US dollars' : 'pounds sterling') + '.';
      try { localStorage.setItem('autoflow-currency', cur); } catch (e) { /* storage unavailable */ }
    }
    buttons.forEach(function (b) {
      b.addEventListener('click', function () { apply(b.dataset.currency, true); });
    });

    var saved = null;
    try { saved = localStorage.getItem('autoflow-currency'); } catch (e) { /* ignore */ }
    if (saved !== 'usd' && saved !== 'gbp') {
      var tz = '';
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { /* ignore */ }
      saved = /^America\/|^Pacific\/Honolulu$/.test(tz) ? 'usd' : 'gbp';
    }
    apply(saved, false);
  }

  /* ---------- Prefill the audit form from ?url= ---------- */
  function initPrefill() {
    var input = document.getElementById('audit-url');
    if (!input) return;
    var url = new URLSearchParams(window.location.search).get('url');
    if (url) {
      if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
      input.value = url;
    }
  }

  /* ---------- FormSubmit: AJAX submit with a real HTML POST as fallback ---------- */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function initForms() {
    document.querySelectorAll('form[data-formsubmit]').forEach(function (form) {
      var status = form.querySelector('.form-status');
      var submit = form.querySelector('[type="submit"]');

      // Normalise bare domains in URL fields before the browser validates them.
      form.querySelectorAll('input[type="url"]').forEach(function (input) {
        input.addEventListener('blur', function () {
          var v = input.value.trim();
          if (v && !/^https?:\/\//i.test(v)) input.value = 'https://' + v;
        });
      });

      form.addEventListener('submit', function (e) {
        if (!window.fetch) return; // let the native POST happen
        e.preventDefault();
        var data = {};
        new FormData(form).forEach(function (v, k) { data[k] = v; });
        if (data._honey) return; // bot

        if (status) { status.className = 'form-status'; status.textContent = 'Sending…'; }
        if (submit) submit.disabled = true;

        fetch(FORM_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify(data)
        })
          .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, body: j }; }); })
          .then(function (res) {
            if (!res.ok || String(res.body.success) !== 'true') throw new Error(res.body.message || 'Send failed');
            var heading = form.getAttribute('data-success-heading') || 'Thank you, your message has been sent.';
            var body = form.getAttribute('data-success-body') || 'We reply within 24 hours.';
            var email = data.email ? ' We will reply to <strong>' + escapeHtml(data.email) + '</strong>.' : '';
            var box = document.createElement('div');
            box.className = 'form-success';
            box.setAttribute('role', 'status');
            box.setAttribute('tabindex', '-1');
            box.innerHTML =
              '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m8 12.5 2.5 2.5L16 9.5"/></svg>' +
              '<h3>' + escapeHtml(heading) + '</h3><p>' + escapeHtml(body) + email + '</p>';
            form.replaceWith(box);
            box.focus();
          })
          .catch(function () {
            if (submit) submit.disabled = false;
            if (status) {
              status.className = 'form-status is-error';
              status.innerHTML = 'Sorry, that did not send. Please try again, or email <a href="mailto:autoflowcompliance@outlook.com">autoflowcompliance@outlook.com</a> directly.';
            }
          });
      });
    });
  }

  function init() { initMenu(); initCurrency(); initPrefill(); initForms(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
