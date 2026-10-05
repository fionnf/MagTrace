/* MagTrace web version.
 * Browser port of the PyQt5 desktop app: Cleaner, Plotter and Combiner.
 * Everything runs client side; nothing is uploaded anywhere.
 */
(function () {
  'use strict';

  // ---------------------------------------------------------------- helpers
  const $ = (id) => document.getElementById(id);
  const dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => !!(dark && dark.matches);

  // Matplotlib "tab10" order, as used by the desktop app.
  const COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'];

  function setStatus(id, msg, isError) {
    const el = $(id);
    el.textContent = msg;
    el.classList.toggle('error', !!isError);
  }

  function baseLayout(extra) {
    const d = isDark();
    const ink = d ? '#f1f2f4' : '#15181d';
    const grid = d ? '#353a43' : '#e3e6ea';
    const paper = d ? '#1b1e23' : '#ffffff';
    return Object.assign({
      paper_bgcolor: paper,
      plot_bgcolor: paper,
      font: { color: ink, family: 'system-ui, sans-serif', size: 12 },
      margin: { l: 60, r: 20, t: 40, b: 50 },
      hovermode: 'x unified',
      legend: { orientation: 'h', y: -0.18 },
      xaxis: { gridcolor: grid, zerolinecolor: grid, showgrid: true },
      yaxis: { gridcolor: grid, zerolinecolor: grid, showgrid: true },
    }, extra || {});
  }

  const PLOT_CONFIG = {
    responsive: true,
    displaylogo: false,
    scrollZoom: true,
    toImageButtonOptions: { format: 'png', scale: 2, filename: 'magtrace' },
  };

  function toNumber(s) {
    if (s === undefined) return NaN;
    s = s.trim();
    if (s === '' || s === 'NaN' || s === 'nan') return NaN;
    let v = Number(s);
    if (Number.isNaN(v) && s.indexOf(',') !== -1) v = Number(s.replace(',', '.'));
    return v;
  }

  // Minimal RFC 4180 style splitter for a single line (handles quoted fields).
  function splitCsvLine(line, delim) {
    if (line.indexOf('"') === -1) return line.split(delim);
    const out = [];
    let cur = '';
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (inQ) {
        if (c === '"') {
          if (line[i + 1] === '"') { cur += '"'; i++; } else { inQ = false; }
        } else cur += c;
      } else if (c === '"') inQ = true;
      else if (c === delim) { out.push(cur); cur = ''; }
      else cur += c;
    }
    out.push(cur);
    return out;
  }

  function csvQuote(s) {
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function downloadText(name, text) {
    const blob = new Blob([text], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function readFileText(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(r.result);
      r.onerror = () => reject(r.error);
      r.readAsText(file);
    });
  }

  // Mirrors utils.flatten_col: ('Current', 'A') -> 'Current(A)'.
  function flattenCol(first, second) {
    first = (first || '').trim();
    second = (second || '').trim();
    if (!second || second === first || /^Unnamed/.test(second)) return first;
    return first + '(' + second + ')';
  }

  function fmtNum(v) {
    if (!Number.isFinite(v)) return '';
    return String(v);
  }

  // ---------------------------------------------------------------- dataset
  // A dataset is { name, columns: string[], data: { [col]: Float64Array }, n }.
  function makeDataset(name, columns, rows) {
    const n = rows.length;
    const data = {};
    columns.forEach((c, j) => {
      const arr = new Float64Array(n);
      for (let i = 0; i < n; i++) arr[i] = rows[i][j];
      data[c] = arr;
    });
    return { name, columns: columns.slice(), data, n };
  }

  // Raw LabView export: ';' separated, first line skipped, two header rows.
  // Same as pandas.read_csv(path, delimiter=';', skiprows=1, header=[0, 1]).
  function parseRawLabview(text) {
    const lines = text.split(/\r?\n/);
    if (lines.length < 4) throw new Error('File is too short to be a LabView export.');
    const h1 = lines[1].split(';');
    const h2 = lines[2].split(';');
    const ncol = Math.max(h1.length, h2.length);
    let columns = [];
    for (let j = 0; j < ncol; j++) columns.push(flattenCol(h1[j], h2[j]));
    // Make duplicate names unique (pandas appends .1, .2, ...).
    const seen = {};
    columns = columns.map((c) => {
      if (!(c in seen)) { seen[c] = 0; return c; }
      seen[c] += 1;
      return c + '.' + seen[c];
    });
    const rows = [];
    for (let i = 3; i < lines.length; i++) {
      const line = lines[i];
      if (!line.trim()) continue;
      const parts = line.split(';');
      const row = new Array(ncol);
      for (let j = 0; j < ncol; j++) row[j] = toNumber(parts[j]);
      rows.push(row);
    }
    if (!rows.length) throw new Error('No data rows found.');
    // Drop unnamed or completely empty columns (dropna(axis=1, how="all")).
    const keep = [];
    for (let j = 0; j < ncol; j++) {
      if (!columns[j]) continue;
      let any = false;
      for (let i = 0; i < rows.length; i++) if (Number.isFinite(rows[i][j])) { any = true; break; }
      if (any) keep.push(j);
    }
    const keptCols = keep.map((j) => columns[j]);
    const keptRows = rows.map((r) => keep.map((j) => r[j]));
    return { columns: keptCols, rows: keptRows };
  }

  // Cleaned CSV: ',' separated, single header row (pandas default to_csv).
  function parseCleanedCsv(text) {
    const lines = text.split(/\r?\n/);
    let start = 0;
    while (start < lines.length && !lines[start].trim()) start++;
    if (start >= lines.length) throw new Error('Empty file.');
    const columns = splitCsvLine(lines[start], ',').map((c) => c.trim());
    // pandas writes an unnamed index column as an empty header; drop it.
    const ncol = columns.length;
    const rows = [];
    for (let i = start + 1; i < lines.length; i++) {
      const line = lines[i];
      if (!line.trim()) continue;
      const parts = line.indexOf('"') === -1 ? line.split(',') : splitCsvLine(line, ',');
      const row = new Array(ncol);
      for (let j = 0; j < ncol; j++) row[j] = toNumber(parts[j]);
      rows.push(row);
    }
    if (!rows.length) throw new Error('No data rows found.');
    const keep = [];
    for (let j = 0; j < ncol; j++) if (columns[j]) keep.push(j);
    return { columns: keep.map((j) => columns[j]), rows: rows.map((r) => keep.map((j) => r[j])) };
  }

  function datasetToCsv(ds, mask) {
    const out = [ds.columns.map(csvQuote).join(',')];
    const cols = ds.columns.map((c) => ds.data[c]);
    for (let i = 0; i < ds.n; i++) {
      if (mask && !mask[i]) continue;
      const parts = new Array(cols.length);
      for (let j = 0; j < cols.length; j++) parts[j] = fmtNum(cols[j][i]);
      out.push(parts.join(','));
    }
    return out.join('\n') + '\n';
  }

  // ------------------------------------------------------- shared data store
  // Equivalent of widgets.SharedDataManager: cleaned files visible to all tabs.
  const store = {
    files: [],
    listeners: [],
    add(ds) {
      const idx = this.files.findIndex((f) => f.name === ds.name);
      if (idx >= 0) this.files[idx] = ds; else this.files.push(ds);
      this.listeners.forEach((fn) => fn());
    },
    onChange(fn) { this.listeners.push(fn); },
  };

  async function loadCleanedFiles(fileList, statusId) {
    let last = null;
    for (const file of fileList) {
      try {
        const text = await readFileText(file);
        const { columns, rows } = parseCleanedCsv(text);
        last = makeDataset(file.name, columns, rows);
        store.add(last);
        setStatus(statusId, `Loaded ${file.name}: ${rows.length} rows, ${columns.length} columns.`);
      } catch (e) {
        setStatus(statusId, `Could not read ${file.name}: ${e.message}`, true);
      }
    }
    return last;
  }

  // ---------------------------------------------------------------- tabs
  document.querySelectorAll('.tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach((b) => {
        const on = b === btn;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      document.querySelectorAll('.panel').forEach((p) => {
        const on = p.id === 'tab-' + btn.dataset.tab;
        p.classList.toggle('active', on);
        p.hidden = !on;
      });
      // Plotly needs a resize once the container becomes visible.
      document.querySelectorAll('.panel.active .plot').forEach((div) => {
        if (div.data) Plotly.Plots.resize(div);
      });
    });
  });

  // ================================================================ CLEANER
  const cleaner = {
    ds: null,          // raw dataset as loaded
    excludes: [],      // [start, end] pairs in displayed time units
    sourceName: '',
    timer: null,
  };

  function cleanerTimestamp() {
    // Scaled timestamp (ms -> s / min) as a plain array; null when absent.
    if (!cleaner.ds || !cleaner.ds.data.Timestamp) return null;
    const scale = Number($('cleaner-tsunit').value) || 1;
    const src = cleaner.ds.data.Timestamp;
    const out = new Float64Array(src.length);
    for (let i = 0; i < src.length; i++) out[i] = src[i] * scale;
    return out;
  }

  // Row mask after range + exclusions; also the normalised time axis.
  function cleanerFilter() {
    const ds = cleaner.ds;
    const t = cleanerTimestamp();
    const mask = new Uint8Array(ds.n).fill(1);
    if (!t) return { mask, t: null };
    const tmin = parseFloat($('cleaner-tmin').value);
    const tmax = parseFloat($('cleaner-tmax').value);
    for (let i = 0; i < ds.n; i++) {
      const v = t[i];
      if (!Number.isFinite(v)) { mask[i] = 0; continue; }
      if (Number.isFinite(tmin) && v < tmin) mask[i] = 0;
      if (Number.isFinite(tmax) && v > tmax) mask[i] = 0;
    }
    let tOut = t;
    if ($('cleaner-normalize').checked) {
      let m = Infinity;
      for (let i = 0; i < ds.n; i++) if (mask[i] && t[i] < m) m = t[i];
      if (Number.isFinite(m)) {
        tOut = new Float64Array(ds.n);
        for (let i = 0; i < ds.n; i++) tOut[i] = t[i] - m;
      }
    }
    for (const [s, e] of cleaner.excludes) {
      for (let i = 0; i < ds.n; i++) if (mask[i] && tOut[i] >= s && tOut[i] <= e) mask[i] = 0;
    }
    return { mask, t: tOut };
  }

  function cleanerSelectedColumns() {
    return Array.from($('cleaner-columns').querySelectorAll('input:checked')).map((i) => i.value);
  }

  function cleanerRenderColumns() {
    const box = $('cleaner-columns');
    box.innerHTML = '';
    if (!cleaner.ds) { box.innerHTML = '<div class="empty">No file loaded.</div>'; return; }
    const frag = document.createDocumentFragment();
    cleaner.ds.columns.forEach((c, idx) => {
      if (c === 'Timestamp') return;
      const label = document.createElement('label');
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.value = c;
      // Default: the first few channels, keeps the first draw fast on big files.
      cb.checked = idx < 6;
      cb.addEventListener('change', cleanerSchedulePlot);
      label.appendChild(cb);
      label.appendChild(document.createTextNode(c));
      label.title = c;
      frag.appendChild(label);
    });
    box.appendChild(frag);
  }

  function cleanerRenderExcludes() {
    const ul = $('cleaner-excludes');
    ul.innerHTML = '';
    cleaner.excludes.forEach(([s, e], i) => {
      const li = document.createElement('li');
      li.textContent = `${s} – ${e}`;
      const rm = document.createElement('button');
      rm.type = 'button';
      rm.className = 'icon';
      rm.textContent = '✕';
      rm.title = 'Remove';
      rm.addEventListener('click', () => { cleaner.excludes.splice(i, 1); cleanerRenderExcludes(); cleanerSchedulePlot(); });
      li.appendChild(rm);
      ul.appendChild(li);
    });
  }

  function cleanerSchedulePlot() {
    clearTimeout(cleaner.timer);
    cleaner.timer = setTimeout(cleanerPlot, 80);
  }

  function cleanerPlot() {
    const ds = cleaner.ds;
    const div = $('cleaner-plot');
    if (!ds) return;
    const { mask, t } = cleanerFilter();
    if (!t) {
      Plotly.purge(div);
      setStatus('cleaner-status', 'No "Timestamp" column found; nothing to plot (saving still works).', true);
      return;
    }
    const cols = cleanerSelectedColumns();
    let kept = 0;
    for (let i = 0; i < ds.n; i++) kept += mask[i];
    const x = new Float64Array(kept);
    let k = 0;
    for (let i = 0; i < ds.n; i++) if (mask[i]) x[k++] = t[i];
    const traces = cols.map((c, ci) => {
      const src = ds.data[c];
      const y = new Float64Array(kept);
      let m = 0;
      for (let i = 0; i < ds.n; i++) if (mask[i]) y[m++] = src[i];
      return {
        type: 'scattergl', mode: 'lines', name: c, x, y,
        line: { width: 1.5, color: COLORS[ci % COLORS.length] },
      };
    });
    const shapes = cleaner.excludes.map(([s, e]) => ({
      type: 'rect', xref: 'x', yref: 'paper', x0: s, x1: e, y0: 0, y1: 1,
      fillcolor: 'rgba(196,61,61,0.12)', line: { width: 0 },
    }));
    const unit = $('cleaner-tsunit').selectedOptions[0].textContent;
    const layout = baseLayout({
      title: { text: cleaner.sourceName, font: { size: 14 } },
      xaxis: Object.assign(baseLayout().xaxis, { title: { text: 'Timestamp (' + unit + ')' } }),
      shapes,
    });
    Plotly.react(div, traces, layout, PLOT_CONFIG);
    setStatus('cleaner-status', `${kept} of ${ds.n} rows kept · ${cols.length} column(s) plotted · ${cleaner.excludes.length} excluded region(s).`);
  }

  $('cleaner-file').addEventListener('change', async (ev) => {
    const file = ev.target.files[0];
    if (!file) return;
    setStatus('cleaner-status', 'Reading ' + file.name + '…');
    try {
      const text = await readFileText(file);
      const { columns, rows } = parseRawLabview(text);
      cleaner.ds = makeDataset(file.name, columns, rows);
      cleaner.sourceName = file.name;
      cleaner.excludes = [];
      $('cleaner-tmin').value = '';
      $('cleaner-tmax').value = '';
      $('cleaner-outname').value = file.name.replace(/\.[^.]+$/, '') + '_clean.csv';
      const info = $('cleaner-fileinfo');
      info.hidden = false;
      info.textContent = `${file.name} · ${rows.length} rows · ${columns.length} columns`;
      cleanerRenderColumns();
      cleanerRenderExcludes();
      cleanerPlot();
    } catch (e) {
      setStatus('cleaner-status', 'Could not read file: ' + e.message, true);
    }
    ev.target.value = '';
  });

  $('cleaner-cols-all').addEventListener('click', () => {
    $('cleaner-columns').querySelectorAll('label:not(.hidden) input').forEach((i) => { i.checked = true; });
    cleanerSchedulePlot();
  });
  $('cleaner-cols-none').addEventListener('click', () => {
    $('cleaner-columns').querySelectorAll('input').forEach((i) => { i.checked = false; });
    cleanerSchedulePlot();
  });
  $('cleaner-cols-filter').addEventListener('input', (ev) => {
    const q = ev.target.value.toLowerCase();
    $('cleaner-columns').querySelectorAll('label').forEach((l) => {
      l.classList.toggle('hidden', q && !l.textContent.toLowerCase().includes(q));
    });
  });
  ['cleaner-tsunit', 'cleaner-normalize', 'cleaner-tmin', 'cleaner-tmax'].forEach((id) => {
    $(id).addEventListener('change', cleanerSchedulePlot);
    $(id).addEventListener('input', cleanerSchedulePlot);
  });
  $('cleaner-range-reset').addEventListener('click', () => {
    $('cleaner-tmin').value = '';
    $('cleaner-tmax').value = '';
    cleanerSchedulePlot();
  });
  $('cleaner-exadd').addEventListener('click', () => {
    const s = parseFloat($('cleaner-exstart').value);
    const e = parseFloat($('cleaner-exend').value);
    if (!Number.isFinite(s) || !Number.isFinite(e)) {
      setStatus('cleaner-status', 'Enter numeric start and end values for the excluded region.', true);
      return;
    }
    cleaner.excludes.push([Math.min(s, e), Math.max(s, e)]);
    $('cleaner-exstart').value = '';
    $('cleaner-exend').value = '';
    cleanerRenderExcludes();
    cleanerSchedulePlot();
  });
  $('cleaner-save').addEventListener('click', () => {
    if (!cleaner.ds) { setStatus('cleaner-status', 'Load a raw file first.', true); return; }
    const { mask, t } = cleanerFilter();
    const name = ($('cleaner-outname').value.trim() || 'cleaned.csv').replace(/\.csv$/i, '') + '.csv';
    // Build the output dataset with the scaled / shifted timestamp.
    const out = { name, columns: cleaner.ds.columns.slice(), data: Object.assign({}, cleaner.ds.data), n: cleaner.ds.n };
    if (t) out.data.Timestamp = t;
    const csv = datasetToCsv(out, mask);
    downloadText(name, csv);
    // Register the cleaned (filtered) dataset for the other tabs.
    let kept = 0;
    for (let i = 0; i < out.n; i++) kept += mask[i];
    const data = {};
    out.columns.forEach((c) => {
      const src = out.data[c];
      const arr = new Float64Array(kept);
      let k = 0;
      for (let i = 0; i < out.n; i++) if (mask[i]) arr[k++] = src[i];
      data[c] = arr;
    });
    store.add({ name, columns: out.columns, data, n: kept });
    setStatus('cleaner-status', `Saved ${name} (${kept} rows). It is now available in the Plotter and Combiner.`);
  });

  cleanerRenderColumns();

  // ================================================================ PLOTTER
  const plotter = { current: null };

  function fillSelect(sel, columns, allowNone) {
    const prev = sel.value;
    sel.innerHTML = '';
    if (allowNone) {
      const o = document.createElement('option');
      o.value = '';
      o.textContent = '(none)';
      sel.appendChild(o);
    }
    columns.forEach((c) => {
      const o = document.createElement('option');
      o.value = c;
      o.textContent = c;
      sel.appendChild(o);
    });
    if (prev && columns.includes(prev)) sel.value = prev;
  }

  function plotterRenderFiles() {
    const box = $('plotter-files');
    box.innerHTML = '';
    if (!store.files.length) { box.innerHTML = '<div class="empty">No cleaned files yet. Save one in the Cleaner or load a CSV.</div>'; return; }
    store.files.forEach((ds) => {
      const item = document.createElement('div');
      item.className = 'item' + (plotter.current === ds ? ' selected' : '');
      item.innerHTML = `<span class="name"></span><span class="meta"></span>`;
      item.querySelector('.name').textContent = ds.name;
      item.querySelector('.meta').textContent = ds.n + ' rows';
      item.title = ds.name;
      item.addEventListener('click', () => plotterSelect(ds));
      box.appendChild(item);
    });
  }

  function plotterSelect(ds) {
    plotter.current = ds;
    plotterRenderFiles();
    fillSelect($('plotter-x'), ds.columns, false);
    fillSelect($('plotter-y'), ds.columns, false);
    fillSelect($('plotter-y2'), ds.columns, true);
    fillSelect($('plotter-y3'), ds.columns, true);
    // Sensible defaults: X = Timestamp, Y = first current column if present.
    if (ds.columns.includes('Timestamp')) $('plotter-x').value = 'Timestamp';
    const yGuess = ds.columns.find((c) => /current/i.test(c)) || ds.columns.find((c) => c !== $('plotter-x').value);
    if (yGuess && !$('plotter-y').value) $('plotter-y').value = yGuess;
    setStatus('plotter-status', `Selected ${ds.name}. Choose axes and press Plot.`);
  }

  function plotterPlot() {
    const ds = plotter.current;
    if (!ds) { setStatus('plotter-status', 'Select a cleaned file first.', true); return; }
    const x = $('plotter-x').value;
    const ys = [$('plotter-y').value, $('plotter-y2').value, $('plotter-y3').value].filter(Boolean);
    if (!x || !ys.length) { setStatus('plotter-status', 'Choose X and at least a Y column.', true); return; }
    const markers = $('plotter-markers').checked;
    const traces = ys.map((y, i) => ({
      type: 'scattergl',
      mode: markers ? 'markers' : 'lines',
      name: y,
      x: ds.data[x],
      y: ds.data[y],
      yaxis: i === 0 ? 'y' : 'y' + (i + 1),
      line: { width: 1.5, color: COLORS[i] },
      marker: { size: 4, color: COLORS[i] },
    }));
    const d = isDark();
    const grid = d ? '#353a43' : '#e3e6ea';
    const axis = (title, color, extra) => Object.assign({
      title: { text: title, font: { color } },
      tickfont: { color },
      gridcolor: grid, zerolinecolor: grid,
    }, extra || {});
    const rightAxes = ys.length - 1;
    const layout = baseLayout({
      title: { text: $('plotter-title').value || ds.name, font: { size: 14 } },
      hovermode: 'x unified',
      xaxis: axis(x, d ? '#f1f2f4' : '#15181d', { domain: [0, rightAxes > 1 ? 0.86 : 1] }),
      yaxis: axis(ys[0], COLORS[0]),
      margin: { l: 60, r: rightAxes > 1 ? 30 : 60, t: 40, b: 50 },
    });
    if (ys[1]) layout.yaxis2 = axis(ys[1], COLORS[1], { overlaying: 'y', side: 'right', showgrid: false });
    if (ys[2]) layout.yaxis3 = axis(ys[2], COLORS[2], { overlaying: 'y', side: 'right', anchor: 'free', position: 0.955, showgrid: false });
    Plotly.react($('plotter-plot-div'), traces, layout, PLOT_CONFIG);
    setStatus('plotter-status', `${ds.name}: ${ys.join(', ')} vs ${x}.`);
  }

  $('plotter-file').addEventListener('change', async (ev) => {
    const last = await loadCleanedFiles(Array.from(ev.target.files), 'plotter-status');
    if (last) plotterSelect(last);
    ev.target.value = '';
  });
  $('plotter-plot').addEventListener('click', plotterPlot);
  store.onChange(() => {
    plotterRenderFiles();
    if (!plotter.current && store.files.length) plotterSelect(store.files[store.files.length - 1]);
  });
  plotterRenderFiles();

  // ================================================================ COMBINER
  const combiner = { order: [], selected: new Set() };

  function combinerSync() {
    // Keep the ordering list in sync with the store (new files appended).
    combiner.order = combiner.order.filter((n) => store.files.some((f) => f.name === n));
    store.files.forEach((f) => { if (!combiner.order.includes(f.name)) combiner.order.push(f.name); });
  }

  function combinerRender() {
    combinerSync();
    const box = $('combiner-files');
    box.innerHTML = '';
    if (!combiner.order.length) { box.innerHTML = '<div class="empty">No cleaned files yet.</div>'; return; }
    combiner.order.forEach((name, i) => {
      const ds = store.files.find((f) => f.name === name);
      const item = document.createElement('div');
      item.className = 'item' + (combiner.selected.has(name) ? ' selected' : '');
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = combiner.selected.has(name);
      cb.addEventListener('change', () => {
        if (cb.checked) combiner.selected.add(name); else combiner.selected.delete(name);
        combinerRender();
      });
      const nm = document.createElement('span');
      nm.className = 'name';
      nm.textContent = name;
      nm.title = name;
      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = ds.n + ' rows';
      const up = document.createElement('button');
      up.type = 'button'; up.className = 'icon'; up.textContent = '↑'; up.title = 'Move up'; up.disabled = i === 0;
      up.addEventListener('click', (e) => { e.stopPropagation(); [combiner.order[i - 1], combiner.order[i]] = [combiner.order[i], combiner.order[i - 1]]; combinerRender(); });
      const down = document.createElement('button');
      down.type = 'button'; down.className = 'icon'; down.textContent = '↓'; down.title = 'Move down'; down.disabled = i === combiner.order.length - 1;
      down.addEventListener('click', (e) => { e.stopPropagation(); [combiner.order[i + 1], combiner.order[i]] = [combiner.order[i], combiner.order[i + 1]]; combinerRender(); });
      item.append(cb, nm, meta, up, down);
      item.addEventListener('click', (e) => { if (e.target === item || e.target === nm || e.target === meta) { cb.checked = !cb.checked; cb.dispatchEvent(new Event('change')); } });
      box.appendChild(item);
    });
  }

  function combinerCombine() {
    combinerSync();
    const names = combiner.order.filter((n) => combiner.selected.has(n));
    if (names.length < 1) { setStatus('combiner-status', 'Select at least one file.', true); return; }
    const parts = names.map((n) => store.files.find((f) => f.name === n));
    // Union of columns, in order of first appearance (pandas.concat behaviour).
    const columns = [];
    parts.forEach((ds) => ds.columns.forEach((c) => { if (!columns.includes(c)) columns.push(c); }));
    const total = parts.reduce((s, ds) => s + ds.n, 0);
    const data = {};
    columns.forEach((c) => { data[c] = new Float64Array(total).fill(NaN); });
    let pos = 0;
    let offset = 0;
    const boundaries = [];
    parts.forEach((ds) => {
      columns.forEach((c) => { if (ds.data[c]) data[c].set(ds.data[c], pos); });
      if (ds.data.Timestamp) {
        const ts = data.Timestamp;
        for (let i = 0; i < ds.n; i++) ts[pos + i] += offset;
        offset = ts[pos + ds.n - 1] + 0.01;
        boundaries.push(ts[pos]);
      }
      pos += ds.n;
    });
    const name = ($('combiner-outname').value.trim() || 'combined.csv').replace(/\.csv$/i, '') + '.csv';
    const ds = { name, columns, data, n: total };
    downloadText(name, datasetToCsv(ds));
    store.add(ds);
    combiner.selected.clear();
    combinerRender();
    // Preview: first non-Timestamp column vs Timestamp with file boundaries.
    const yCol = columns.find((c) => /current/i.test(c)) || columns.find((c) => c !== 'Timestamp');
    if (data.Timestamp && yCol) {
      const layout = baseLayout({
        title: { text: name + ' — preview', font: { size: 14 } },
        xaxis: Object.assign(baseLayout().xaxis, { title: { text: 'Timestamp' } }),
        yaxis: Object.assign(baseLayout().yaxis, { title: { text: yCol } }),
        shapes: boundaries.slice(1).map((b) => ({ type: 'line', xref: 'x', yref: 'paper', x0: b, x1: b, y0: 0, y1: 1, line: { color: '#c43d3d', width: 1, dash: 'dot' } })),
      });
      Plotly.react($('combiner-plot'), [{ type: 'scattergl', mode: 'lines', name: yCol, x: data.Timestamp, y: data[yCol], line: { width: 1.5, color: COLORS[0] } }], layout, PLOT_CONFIG);
    }
    setStatus('combiner-status', `Saved ${name}: ${names.length} file(s), ${total} rows. It is now available in the Plotter.`);
  }

  $('combiner-file').addEventListener('change', async (ev) => {
    await loadCleanedFiles(Array.from(ev.target.files), 'combiner-status');
    ev.target.value = '';
  });
  $('combiner-combine').addEventListener('click', combinerCombine);
  store.onChange(combinerRender);
  combinerRender();

  // Re-theme plots when the OS theme changes.
  if (dark && dark.addEventListener) {
    dark.addEventListener('change', () => {
      if (cleaner.ds) cleanerPlot();
      if (plotter.current && $('plotter-plot-div').data) plotterPlot();
    });
  }
})();
