(() => {
  'use strict';
  const $ = (selector, parent = document) => parent.querySelector(selector);
  const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
  const root = document.documentElement;
  const settingsKey = 'mini-novels:settings:v1';
  const historyKey = 'mini-novels:reading:v1';
  const defaults = { size: 'medium', font: 'serif', theme: 'light' };
  let storageAvailable = true;
  function read(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) || fallback; }
    catch { return fallback; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch {
      storageAvailable = false;
      const note = $('#storage-note');
      if (note) note.textContent = 'このブラウザでは保存ができません。設定はこのページを開いている間だけ有効です。';
    }
  }
  function history() {
    const value = read(historyKey, {});
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  }
  function validEntry(entry) {
    return entry && typeof entry.title === 'string' && typeof entry.url === 'string'
      && /^(archive\/)?stories\/[a-z0-9_-]+\.html$/.test(entry.url)
      && Number.isFinite(entry.updated) && Number.isFinite(entry.ratio);
  }

  // Discovery still works as a complete linked catalog without JavaScript.
  const search = $('#library-search');
  if (search) {
    let filter = 'all';
    const rows = $$('[data-work]');
    const normalize = value => value.normalize('NFKC').toLocaleLowerCase('ja');
    function filterWorks() {
      const terms = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
      let visible = 0;
      for (const row of rows) {
        row.hidden = !(filter === 'all' || row.dataset.kind === filter)
          || !terms.every(term => normalize(row.dataset.search).includes(term));
        if (!row.hidden) visible++;
      }
      $('.empty-search').hidden = visible !== 0;
      $('.search-status').textContent = `${visible}作品を表示しています。`;
    }
    $$('[data-filter]').forEach(button => button.addEventListener('click', () => {
      filter = button.dataset.filter;
      $$('[data-filter]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      filterWorks();
    }));
    search.addEventListener('input', filterWorks);
    $('[data-reset-search]').addEventListener('click', () => {
      search.value = '';
      $('[data-filter="all"]').click();
      search.focus();
    });
  }

  const continueSlot = $('[data-continue]');
  if (continueSlot) {
    const records = history();
    let catalog = {};
    try { catalog = JSON.parse($('#reading-index')?.textContent || '{}'); } catch { /* Optional enhancement. */ }
    const candidates = Object.values(records).filter(validEntry)
      .filter(entry => !continueSlot.dataset.workId || entry.work === continueSlot.dataset.workId)
      .sort((a, b) => b.updated - a.updated);
    for (const entry of candidates) {
      if (!catalog[entry.url]) continue;
      const next = catalog[entry.url].next;
      let target = entry;
      let resume = true;
      if (entry.completed) {
        if (!next || !catalog[next.url]) continue;
        const nextRecord = Object.values(records).find(item => validEntry(item) && item.url === next.url);
        if (nextRecord?.completed) continue;
        target = nextRecord || next;
        resume = Boolean(nextRecord);
      }
      const link = $('.continue-link', continueSlot);
      link.href = continueSlot.dataset.prefix + target.url + (resume ? '#resume' : '');
      link.textContent = target.title + ' →';
      $('.continue-note', continueSlot).textContent = resume ? '保存した位置から再開' : '次の話へ';
      continueSlot.hidden = false;
      break;
    }
  }

  const storyElement = $('#story-data');
  if (!storyElement) return;
  const story = JSON.parse(storyElement.textContent);
  const body = $('#story-body');
  const blocks = [...body.children].filter(node => node.id);
  let saved = history()[story.id];
  if (!validEntry(saved)) saved = null;
  let hasMoved = false;
  let restoring = false;
  let saveTimer;
  let stablePosition;

  function position() {
    const y = window.scrollY + 32;
    let block = blocks[0];
    for (const item of blocks) {
      if (item.getBoundingClientRect().top + window.scrollY > y) break;
      block = item;
    }
    const rect = block?.getBoundingClientRect();
    const article = body.getBoundingClientRect();
    return {
      anchor: block?.id || '',
      offset: rect ? Math.max(0, Math.min(1, (32 - rect.top) / Math.max(rect.height, 1))) : 0,
      ratio: Math.max(0, Math.min(1, -article.top / Math.max(1, article.height - window.innerHeight + 80)))
    };
  }

  function restorePosition(record) {
    if (!record) return;
    const anchor = typeof record.anchor === 'string' ? document.getElementById(record.anchor) : null;
    if (anchor && body.contains(anchor)) {
      const fraction = Number.isFinite(record.offset) ? Math.min(1, Math.max(0, record.offset)) : 0;
      const rect = anchor.getBoundingClientRect();
      window.scrollTo({ top: window.scrollY + rect.top + fraction * rect.height - 32, behavior: 'instant' });
    } else {
      const rect = body.getBoundingClientRect();
      const ratio = Number.isFinite(record.ratio) ? Math.min(1, Math.max(0, record.ratio)) : 0;
      window.scrollTo({ top: rect.top + window.scrollY + ratio * (rect.height - window.innerHeight + 80), behavior: 'instant' });
    }
  }

  function savePosition() {
    if (!hasMoved || restoring) return;
    const rect = body.getBoundingClientRect();
    if (rect.top > window.innerHeight * .8) return;
    const records = history();
    const record = { ...story, ...position(), updated: Date.now(), completed: rect.bottom <= window.innerHeight - 70 };
    records[story.id] = record;
    const trimmed = Object.fromEntries(Object.entries(records).filter(([, value]) => validEntry(value))
      .sort((a, b) => b[1].updated - a[1].updated).slice(0, 40));
    write(historyKey, trimmed);
  }

  function updateProgress() {
    const rect = body.getBoundingClientRect();
    const fraction = Math.max(0, Math.min(1, (window.innerHeight - 70 - rect.top) / Math.max(1, rect.height)));
    const percent = Math.round(fraction * 100);
    $('#progress-label').textContent = `${percent}%`;
    $('#progress-fill').style.width = `${percent}%`;
    if (!restoring) stablePosition = position();
  }

  let frame;
  window.addEventListener('scroll', () => {
    if (!restoring) hasMoved = true;
    if (!frame) frame = requestAnimationFrame(() => { updateProgress(); frame = null; });
    clearTimeout(saveTimer);
    saveTimer = setTimeout(savePosition, 250);
  }, { passive: true });
  window.addEventListener('resize', () => {
    const current = stablePosition;
    if (!current || !hasMoved || restoring) { updateProgress(); return; }
    restoring = true;
    clearTimeout(saveTimer);
    restorePosition(current);
    requestAnimationFrame(() => {
      restoring = false;
      updateProgress();
      savePosition();
    });
  }, { passive: true });
  window.addEventListener('pagehide', savePosition);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') savePosition(); });

  const resumeNotice = $('.resume-notice');
  if (saved && (saved.ratio > .005 || saved.anchor !== blocks[0]?.id)) {
    resumeNotice.hidden = false;
    async function resume() {
      restoring = true;
      resumeNotice.hidden = true;
      // Wait for font metrics when available, but never hold reading hostage to a font server.
      if (document.fonts) await Promise.race([document.fonts.ready, new Promise(resolve => setTimeout(resolve, 1600))]);
      restorePosition(saved);
      requestAnimationFrame(() => { restoring = false; hasMoved = true; updateProgress(); });
    }
    $('#resume-reading').addEventListener('click', resume);
    if (window.location.hash === '#resume') resume();
  }

  // Native dialogs supply focus trapping, Escape handling, and focus return.
  $$('[data-dialog]').forEach(button => button.addEventListener('click', () => {
    savePosition();
    document.getElementById(button.dataset.dialog).showModal();
  }));
  $$('[data-close-dialog]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  $$('dialog').forEach(dialog => dialog.addEventListener('click', event => {
    const rect = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
  }));

  function updateSettingButtons() {
    $$('[data-setting]').forEach(group => {
      const selected = root.dataset[group.dataset.setting] || defaults[group.dataset.setting];
      $$('button', group).forEach(button => button.setAttribute('aria-pressed', String(button.dataset.value === selected)));
    });
  }
  function applySettings(settings) {
    const current = position();
    const withinBody = body.getBoundingClientRect().top < 32;
    restoring = true;
    for (const key of Object.keys(defaults)) root.dataset[key] = settings[key];
    write(settingsKey, settings);
    updateSettingButtons();
    requestAnimationFrame(() => {
      if (withinBody) restorePosition(current);
      requestAnimationFrame(() => { restoring = false; updateProgress(); });
    });
  }
  $$('[data-setting] button').forEach(button => button.addEventListener('click', () => {
    const settings = Object.fromEntries(Object.entries(defaults).map(([key, value]) => [key, root.dataset[key] || value]));
    settings[button.closest('[data-setting]').dataset.setting] = button.dataset.value;
    applySettings(settings);
  }));
  $('#reset-settings').addEventListener('click', () => applySettings(defaults));
  updateSettingButtons();
  updateProgress();
  if (document.fonts) document.fonts.ready.then(updateProgress);
  // Probe storage without overwriting reading history.
  try { localStorage.setItem('mini-novels:probe', '1'); localStorage.removeItem('mini-novels:probe'); }
  catch { storageAvailable = false; }
  if (!storageAvailable) $('#storage-note').textContent = 'このブラウザでは保存ができません。設定はこのページを開いている間だけ有効です。';
})();
