/* Apply saved typography before the first paint; reading never requires storage. */
(() => {
  const root = document.documentElement;
  root.classList.add('js');
  try {
    const settings = JSON.parse(localStorage.getItem('mini-novels:settings:v1') || '{}');
    const values = { theme: ['light', 'paper', 'night'], size: ['small', 'medium', 'large', 'xlarge'], font: ['serif', 'sans'] };
    for (const key of Object.keys(values)) {
      if (values[key].includes(settings?.[key])) root.dataset[key] = settings[key];
    }
  } catch { /* System defaults remain readable. */ }
})();
