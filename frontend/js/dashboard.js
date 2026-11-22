/* Dashboard: gauges (5s), history chart + system info (30s), alerts. */
(function () {
  if (!requireAuth()) return;

  const CIRCUMFERENCE = 2 * Math.PI * 52;
  const LATEST_MS = 5000;
  const HISTORY_MS = 30000;
  const CPU_WARN = 80;
  const DISK_CRIT = 90;

  const $ = (id) => document.getElementById(id);

  /* ---------- gauges ---------- */
  ['cpu', 'memory', 'disk'].forEach((name) => {
    const ring = $(`${name}-ring`);
    ring.style.strokeDasharray = CIRCUMFERENCE;
    ring.style.strokeDashoffset = CIRCUMFERENCE;
  });

  function levelFor(pct) {
    if (pct >= 90) return 'bad';
    if (pct >= 70) return 'warn';
    return '';
  }

  function setGauge(name, value) {
    const pct = Math.max(0, Math.min(100, Number(value) || 0));
    const ring = $(`${name}-ring`);
    ring.style.strokeDashoffset = CIRCUMFERENCE * (1 - pct / 100);
    ring.setAttribute('class', `gauge-ring ${levelFor(pct)}`.trim());
    $(`${name}-value`).textContent = `${pct.toFixed(1)}%`;
  }

  /* ---------- alerts ---------- */
  function renderAlerts(latest) {
    const box = $('alerts');
    box.replaceChildren();
    const items = [];
    if (latest.cpu > CPU_WARN) {
      items.push(['alert-warn', `High CPU usage: ${latest.cpu.toFixed(1)}% (warning above ${CPU_WARN}%)`]);
    }
    if (latest.disk > DISK_CRIT) {
      items.push(['alert-bad', `Disk almost full: ${latest.disk.toFixed(1)}% used (critical above ${DISK_CRIT}%)`]);
    }
    if (items.length === 0) items.push(['alert-ok', 'All clear. CPU and disk are within normal limits.']);
    items.forEach(([cls, text]) => {
      const div = document.createElement('div');
      div.className = `alert ${cls}`;
      div.setAttribute('role', cls === 'alert-ok' ? 'status' : 'alert');
      div.textContent = text;
      box.appendChild(div);
    });
  }

  /* ---------- connection status ---------- */
  function setStatus(ok, text) {
    $('status-dot').className = `status-dot ${ok ? 'live' : 'down'}`;
    $('status-text').textContent = text;
  }

  /* ---------- latest ---------- */
  async function refreshLatest() {
    try {
      const latest = await apiFetch('/metrics/latest');
      setGauge('cpu', latest.cpu);
      setGauge('memory', latest.memory);
      setGauge('disk', latest.disk);
      renderAlerts(latest);
      setStatus(true, 'Live, refreshing every 5 seconds');
      $('updated-at').textContent = new Date().toLocaleTimeString();
    } catch (err) {
      setStatus(false, err.message);
    }
  }

  /* ---------- history chart ---------- */
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  const chart = new Chart($('history-chart'), {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        { label: 'CPU %', data: [], borderColor: css('--accent'), borderWidth: 2, pointRadius: 0, tension: 0.3 },
        { label: 'Memory %', data: [], borderColor: css('--warn'), borderWidth: 2, pointRadius: 0, tension: 0.3 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { min: 0, max: 100, ticks: { callback: (v) => `${v}%`, color: css('--muted') }, grid: { color: css('--border') } },
        x: { ticks: { maxTicksLimit: 8, color: css('--muted') }, grid: { display: false } },
      },
      plugins: { legend: { labels: { color: css('--text') } } },
    },
  });

  function restyleChart() {
    chart.data.datasets[0].borderColor = css('--accent');
    chart.data.datasets[1].borderColor = css('--warn');
    chart.options.scales.y.ticks.color = css('--muted');
    chart.options.scales.y.grid.color = css('--border');
    chart.options.scales.x.ticks.color = css('--muted');
    chart.options.plugins.legend.labels.color = css('--text');
    chart.update('none');
  }

  async function refreshHistory() {
    try {
      const data = await apiFetch('/metrics/history?minutes=60');
      chart.data.labels = data.samples.map((s) =>
        new Date(s.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      chart.data.datasets[0].data = data.samples.map((s) => s.cpu);
      chart.data.datasets[1].data = data.samples.map((s) => s.memory);
      chart.update('none');
      $('chart-empty').hidden = data.samples.length > 0;
    } catch (err) {
      setStatus(false, err.message);
    }
  }

  /* ---------- system info ---------- */
  function formatUptime(seconds) {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return [d ? `${d}d` : null, `${h}h`, `${m}m`].filter(Boolean).join(' ');
  }

  async function refreshInfo() {
    try {
      const info = await apiFetch('/system/info');
      $('info-hostname').textContent = info.hostname;
      $('info-os').textContent = info.os;
      $('info-kernel').textContent = info.kernel;
      $('info-uptime').textContent = formatUptime(info.uptime_seconds);
    } catch (err) {
      setStatus(false, err.message);
    }
  }

  /* ---------- header controls ---------- */
  $('user-email').textContent = localStorage.getItem(EMAIL_KEY) || '';
  $('logout-btn').addEventListener('click', logout);
  const themeBtn = $('theme-btn');
  const syncThemeLabel = () => {
    themeBtn.textContent = document.documentElement.dataset.theme === 'light' ? 'Dark mode' : 'Light mode';
  };
  themeBtn.addEventListener('click', () => { toggleTheme(); syncThemeLabel(); restyleChart(); });
  syncThemeLabel();

  /* ---------- start ---------- */
  refreshLatest();
  refreshHistory();
  refreshInfo();
  setInterval(refreshLatest, LATEST_MS);
  setInterval(() => { refreshHistory(); refreshInfo(); }, HISTORY_MS);
})();
