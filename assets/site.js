/* =========================================================
   メイシル（MEISIRU）サイト共通JS  site.js
   vanilla JSのみ・外部ライブラリ禁止。
   すべての機能は対象要素の存在チェック後に動作し、
   要素が無いページでもエラーを起こさない。
   実装:
     - モバイルナビ開閉（ハンバーガー）
     - スクロールでヘッダー影
     - IntersectionObserverで .reveal / .reveal-stagger フェードイン
       （prefers-reduced-motion時は即表示）
     - 現在ページのナビ active化
     - スムーススクロール（フォールバック）
     - back-to-top ボタン
     - FAQアコーディオン（.js-accordion）
     - タブ（.js-tabs）
     - 数値カウントアップ（.js-count 可視時に data-to まで加算）
     - コピーライト年の自動更新（#copyright-year）
     - CTAクリック計測（.js-cta → gtag cta_click）
========================================================= */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function ready(fn) {
    if (document.readyState !== 'loading') { fn(); }
    else { document.addEventListener('DOMContentLoaded', fn); }
  }

  ready(function () {

    /* ---------- コピーライト年 ---------- */
    var yearEl = document.getElementById('copyright-year');
    if (yearEl) { yearEl.textContent = String(new Date().getFullYear()); }

    /* ---------- モバイルナビ開閉 ---------- */
    var toggle = document.querySelector('.nav-toggle');
    var mobileNav = document.querySelector('.mobile-nav');
    if (toggle && mobileNav) {
      var closeNav = function () {
        toggle.setAttribute('aria-expanded', 'false');
        mobileNav.classList.remove('is-open');
        document.body.classList.remove('nav-open');
      };
      var openNav = function () {
        toggle.setAttribute('aria-expanded', 'true');
        mobileNav.classList.add('is-open');
        document.body.classList.add('nav-open');
      };
      toggle.addEventListener('click', function () {
        var expanded = toggle.getAttribute('aria-expanded') === 'true';
        if (expanded) { closeNav(); } else { openNav(); }
      });
      /* メニュー内リンククリックで閉じる */
      mobileNav.querySelectorAll('a').forEach(function (a) {
        a.addEventListener('click', closeNav);
      });
      /* Escキーで閉じる */
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && mobileNav.classList.contains('is-open')) { closeNav(); }
      });
      /* デスクトップ幅に戻ったら閉じる */
      if (window.matchMedia) {
        var mq = window.matchMedia('(min-width:900px)');
        var mqHandler = function (ev) { if (ev.matches) { closeNav(); } };
        if (mq.addEventListener) { mq.addEventListener('change', mqHandler); }
        else if (mq.addListener) { mq.addListener(mqHandler); }
      }
    }

    /* ---------- スクロールでヘッダー影 ---------- */
    var header = document.querySelector('.site-header');
    if (header) {
      var onScrollHeader = function () {
        if (window.pageYOffset > 8) { header.classList.add('is-scrolled'); }
        else { header.classList.remove('is-scrolled'); }
      };
      onScrollHeader();
      window.addEventListener('scroll', onScrollHeader, { passive: true });
    }

    /* ---------- 現在ページのナビ active化 ---------- */
    (function markActiveNav() {
      var path = window.location.pathname.split('/').pop() || 'index.html';
      if (path === '') { path = 'index.html'; }
      var navLinks = document.querySelectorAll('.header-nav a, .mobile-nav a');
      navLinks.forEach(function (a) {
        var href = a.getAttribute('href');
        if (!href) { return; }
        var file = href.split('#')[0].split('/').pop();
        if (file === '' && path === 'index.html') { file = 'index.html'; }
        if (file && file === path) {
          a.setAttribute('aria-current', 'page');
        }
      });
    })();

    /* ---------- スムーススクロール（CSS非対応環境向けフォールバック） ---------- */
    if (!('scrollBehavior' in document.documentElement.style)) {
      document.querySelectorAll('a[href^="#"]').forEach(function (a) {
        a.addEventListener('click', function (e) {
          var id = a.getAttribute('href');
          if (id.length < 2) { return; }
          var target = document.querySelector(id);
          if (target) { e.preventDefault(); target.scrollIntoView(); }
        });
      });
    }

    /* ---------- back-to-top ---------- */
    var toTop = document.querySelector('.back-to-top');
    if (toTop) {
      var onScrollTop = function () {
        if (window.pageYOffset > 600) { toTop.classList.add('is-visible'); }
        else { toTop.classList.remove('is-visible'); }
      };
      onScrollTop();
      window.addEventListener('scroll', onScrollTop, { passive: true });
      toTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
      });
    }

    /* ---------- FAQアコーディオン（.js-accordion） ---------- */
    document.querySelectorAll('.js-accordion').forEach(function (acc) {
      var items = acc.querySelectorAll('.accordion-item');
      items.forEach(function (item) {
        var q = item.querySelector('.accordion-q');
        var a = item.querySelector('.accordion-a');
        if (!q) { return; }
        /* a11y属性の初期化 */
        var open = item.classList.contains('is-open');
        q.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (a && !a.id) { a.id = 'acc-panel-' + Math.random().toString(36).slice(2, 8); }
        if (a) { q.setAttribute('aria-controls', a.id); }
        q.addEventListener('click', function () {
          var isOpen = item.classList.toggle('is-open');
          q.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });
      });
    });

    /* ---------- タブ（.js-tabs） ---------- */
    document.querySelectorAll('.js-tabs').forEach(function (tabsRoot) {
      var tabs = Array.prototype.slice.call(tabsRoot.querySelectorAll('[role="tab"]'));
      if (!tabs.length) { return; }

      function activate(tab, setFocus) {
        tabs.forEach(function (t) {
          var selected = t === tab;
          t.setAttribute('aria-selected', selected ? 'true' : 'false');
          t.setAttribute('tabindex', selected ? '0' : '-1');
          var panelId = t.getAttribute('aria-controls');
          var panel = panelId && document.getElementById(panelId);
          if (panel) {
            if (selected) { panel.removeAttribute('hidden'); }
            else { panel.setAttribute('hidden', ''); }
          }
        });
        if (setFocus && tab.focus) { tab.focus(); }
      }

      /* 初期状態: aria-selected="true" を尊重、無ければ先頭 */
      var initial = tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0] || tabs[0];
      activate(initial, false);

      tabs.forEach(function (tab, i) {
        tab.addEventListener('click', function () { activate(tab, false); });
        tab.addEventListener('keydown', function (e) {
          var idx = i;
          if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { idx = (i + 1) % tabs.length; }
          else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { idx = (i - 1 + tabs.length) % tabs.length; }
          else if (e.key === 'Home') { idx = 0; }
          else if (e.key === 'End') { idx = tabs.length - 1; }
          else { return; }
          e.preventDefault();
          activate(tabs[idx], true);
        });
      });
    });

    /* ---------- 数値カウントアップ（.js-count） ---------- */
    (function countUp() {
      var counters = document.querySelectorAll('.js-count');
      if (!counters.length) { return; }

      var formatFromTemplate = function (el) {
        var to = parseFloat(el.getAttribute('data-to'));
        if (isNaN(to)) { to = parseFloat((el.textContent || '').replace(/[^\d.]/g, '')) || 0; }
        return to;
      };

      var run = function (el) {
        var to = formatFromTemplate(el);
        var decimals = parseInt(el.getAttribute('data-decimals'), 10);
        if (isNaN(decimals)) { decimals = (String(to).split('.')[1] || '').length; }
        var prefix = el.getAttribute('data-prefix') || '';
        var suffix = el.getAttribute('data-suffix') || '';
        var duration = parseInt(el.getAttribute('data-duration'), 10);
        if (isNaN(duration)) { duration = 1400; }

        var render = function (val) {
          el.textContent = prefix + val.toFixed(decimals) + suffix;
        };

        if (reduceMotion || duration <= 0) { render(to); return; }

        var start = null;
        var from = 0;
        var step = function (ts) {
          if (start === null) { start = ts; }
          var p = Math.min((ts - start) / duration, 1);
          /* ease-out */
          var eased = 1 - Math.pow(1 - p, 3);
          render(from + (to - from) * eased);
          if (p < 1) { requestAnimationFrame(step); }
          else { render(to); }
        };
        render(from);
        requestAnimationFrame(step);
      };

      if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) { run(e.target); io.unobserve(e.target); }
          });
        }, { threshold: 0.4 });
        counters.forEach(function (el) { io.observe(el); });
      } else {
        counters.forEach(run);
      }
    })();

    /* ---------- scroll-reveal（.reveal / .reveal-stagger） ---------- */
    (function reveal() {
      var els = document.querySelectorAll('.reveal, .reveal-stagger');
      if (!els.length) { return; }
      /* reduced-motion時は即表示（CSSで初期非表示にならないが念のためクラス付与） */
      if (reduceMotion || !('IntersectionObserver' in window)) {
        els.forEach(function (el) { el.classList.add('is-in'); });
        return;
      }
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
        });
      }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });
      els.forEach(function (el) { io.observe(el); });
    })();

    /* ---------- 固定CTAバー: フッター到達時に退避 ---------- */
    (function fixedCta() {
      var bar = document.querySelector('.fixed-cta');
      var foot = document.querySelector('.site-footer');
      if (bar && foot && 'IntersectionObserver' in window) {
        var ioBar = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) { bar.classList.toggle('is-hidden', e.isIntersecting); });
        }, { threshold: 0 });
        ioBar.observe(foot);
      }
    })();

    /* ---------- CTAクリック計測（.js-cta → gtag） ---------- */
    document.querySelectorAll('.js-cta').forEach(function (el) {
      el.addEventListener('click', function () {
        var id = el.getAttribute('data-cta-id') || 'unknown';
        var type = id.indexOf('line') > -1 ? 'line_add' : 'consult_form';
        if (typeof window.gtag === 'function') {
          window.gtag('event', 'cta_click', {
            cta_id: id,
            cta_type: type,
            transport_type: 'beacon'
          });
        }
      });
    });

  });
})();
