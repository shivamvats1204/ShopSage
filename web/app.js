const icons = {
  leaf: '<path d="M19 3C8 2 2 10 7 16s15 0 12-13Z"/><path d="m4 21 11-13"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  sales: '<path d="M5 3h14v18l-3-2-4 2-4-2-3 2V3Z"/><path d="M9 8h6M9 12h6"/>',
  box: '<path d="m3 7 9-4 9 4v10l-9 4-9-4V7Zm0 0 9 4 9-4M12 11v10M7 5l10 4"/>',
  users:
    '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5"/>',
  wallet: '<path d="M20 7V5a2 2 0 0 0-2-2L4 6a2 2 0 0 0-1 2v11a2 2 0 0 0 2 2h15V7H5M20 12h-6v5h6"/>',
  chart: '<path d="M4 3v17h17M8 15v-4M13 15V7M18 15v-6"/>',
  spark: '<path d="m12 3 2.3 6.7L21 12l-6.7 2.3L12 21l-2.3-6.7L3 12l6.7-2.3L12 3ZM20 2v4M18 4h4"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  task: '<rect x="4" y="4" width="16" height="17" rx="3"/><path d="M9 3h6v4H9zM8 13l2 2 5-5"/>',
  settings:
    '<path d="m9 3-1 3-3 1-2 4 2 3v4l4 2 3-1 3 1 4-2v-4l2-3-2-4-3-1-1-3H9Z"/><circle cx="12" cy="12" r="3"/>',
  search: '<circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  down: '<path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  trend: '<path d="m3 17 6-6 4 4 8-10M15 5h6v6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  store: '<path d="M4 10v11h16V10M3 3h18l1 7a4 4 0 0 1-6 2 4 4 0 0 1-8 0 4 4 0 0 1-6-2l1-7ZM9 21v-7h6v7"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 1 1 4 3v2M12 17h.01"/>',
  bag: '<path d="M4 7h16l1 14H3L4 7ZM8 8V6a4 4 0 0 1 8 0v2"/>',
  dot: '<circle cx="12" cy="12" r="3"/>',
};
const icon = (name, cls = '') =>
  `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.grid}</svg>`;
icons.mic =
  '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>';
icons.speaker = '<path d="m11 4-6 5H2v6h3l6 5V4ZM15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14"/>';
icons.refresh = '<path d="M20 7a9 9 0 1 0 1 8M20 2v6h-6"/>';
icons.link =
  '<path d="m10 13 4-4M8 16l-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0M16 8l2-2a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0" transform="translate(1 0) scale(.9)"/>';
const esc = (v) =>
  String(v ?? '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );
const money = (n) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: n % 100 ? 2 : 0,
  }).format((n || 0) / 100);
const qty = (n) => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 3 }).format(n || 0);
const dateLabel = (s) =>
  new Date(s + 'T12:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
const nav = [
  ['today', 'grid', 'My shop today'],
  ['assistant', 'spark', 'Talk to Sage'],
  ['stock', 'box', 'Stock check'],
  ['customers', 'users', 'Customer dues'],
  ['bills', 'sales', 'My bills'],
  ['suppliers', 'wallet', 'Supplier dues'],
  ['reminders', 'task', 'My reminders'],
];
const pageNames = Object.fromEntries(nav.map((n) => [n[0], n[2]]));
pageNames.connect = 'Connection & voice';
let state,
  connection,
  page = pageNames[location.hash.slice(1)] ? location.hash.slice(1) : 'today',
  query = '',
  filter = 'all',
  menu = false;
let speechToken = 0;
let pending = false,
  messages = [],
  lastFocus,
  recording = null,
  audioBlob = null,
  audioURL = null,
  stream = null,
  voiceToken = 0,
  recordTimer = null,
  speakingIndex = null;
let language = localStorage.getItem('shopsage-language') || 'en-IN',
  voiceName = localStorage.getItem('shopsage-voice') || '',
  autoSpeak = localStorage.getItem('shopsage-auto-speak') === 'yes';
const snapshot = () => state?.snapshot;
const badge = (text, cls = 'green') => `<span class="badge ${cls}">${esc(text)}</span>`;
const button = (text, action, ic = 'plus', cls = 'primary', attrs = '') =>
  `<button class="btn ${cls}" data-action="${action}" ${attrs}>${icon(ic)}${text}</button>`;
const empty = (title, text) => `<div class="empty">${icon('leaf')}<h3>${title}</h3><p>${text}</p></div>`;
const heading = (eyebrow, title, desc, actions = '') =>
  `<div class="page-heading"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${desc}</p></div><div class="heading-actions">${actions}</div></div>`;
const link = (url, text, cls = 'text-button') =>
  `<a class="${cls}" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${text} ${icon('arrow')}</a>`;
const sourceLink = (url, text, cls = 'text-button') =>
  state.config.mode === 'demo'
    ? `<button class="${cls}" data-action="demo-link">${text} ${icon('arrow')}</button>`
    : link(url, text, cls);
const prompts = [
  ['How is my shop doing today?', 'Your daily picture', 'grid'],
  ['What should I restock?', 'Keep shelves ready', 'box'],
  ['Who has overdue customer invoices?', 'A little less pending', 'users'],
  ['Draft a polite payment reminder.', 'Find the right words', 'spark'],
];

async function request(path, data) {
  const r = await fetch('/api/' + path, {
    method: data === undefined ? 'GET' : 'POST',
    headers: data === undefined ? {} : { 'Content-Type': 'application/json' },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  const v = await r.json();
  if (!r.ok) throw Error(v.error || 'Something went wrong. Please try again.');
  return v;
}
function notify(text) {
  const el = document.querySelector('#toast');
  el.textContent = text;
  el.classList.add('visible');
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => el.classList.remove('visible'), 5000);
}
function go(next) {
  if (!pageNames[next]) next = 'today';
  page = next;
  query = '';
  filter = 'all';
  menu = false;
  closeModal();
  location.hash = next;
  render();
  window.scrollTo(0, 0);
  if (page === 'connect') loadConnection();
}
function erpHome() {
  return state.config.erp_url + '/app';
}
function render() {
  if (!state) return;
  const c = state.config,
    s = snapshot();
  document.title = pageNames[page] + ' · ShopSage';
  document.querySelector('#app').innerHTML =
    `${menu ? '<button class="nav-scrim" data-action="menu" aria-label="Close navigation"></button>' : ''}<aside class="sidebar ${menu ? 'open' : ''}"><a class="brand" href="#today" data-page="today"><span class="brand-icon">${icon('leaf')}</span><span>ShopSage<small>YOUR SHOP COMPANION</small></span></a><div class="shop-switch">${icon('store')}<div><strong>${esc(s?.company || c.shop)}</strong><small>${c.mode === 'demo' ? 'Sample shop' : 'ERPNext connected workspace'}</small></div>${icon('link')}</div><div class="nav-label">A LITTLE LESS TO JUGGLE</div><nav aria-label="Main navigation">${nav.map(([key, ic, label]) => `<button class="nav-item ${page === key ? 'active' : ''}" data-page="${key}" ${page === key ? 'aria-current="page"' : ''}>${icon(ic)}${label}${key === 'stock' && s?.summary.low_stock ? `<span class="nav-count">${s.summary.low_stock}</span>` : ''}</button>`).join('')}</nav><div class="sidebar-bottom"><div class="sidebar-note"><span class="status-dot"></span> Works alongside ERPNext.<p>Your billing stays right where it belongs.</p></div><button class="nav-item ${page === 'connect' ? 'active' : ''}" data-page="connect">${icon('settings')}Connection & voice</button><div class="owner"><span class="avatar">${esc(c.owner.charAt(0))}</span><span><strong>${esc(c.owner)}</strong><small>Shop owner</small></span>${badge('ENHANCER')}</div></div></aside><div class="workspace"><header class="topbar"><div class="breadcrumb"><button class="icon-btn mobile-menu" data-action="menu" aria-label="Toggle navigation">${icon('menu')}</button><span>My workspace</span>${icon('chevron')}<strong>${pageNames[page]}</strong></div><div class="top-actions"><button class="icon-btn" data-action="refresh" aria-label="Refresh ERPNext records">${icon('refresh')}</button><span class="sync-status"><i class="status-dot"></i>${s ? `Updated ${new Date(s.captured_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}` : 'Not connected'}</span>${button('Ask Sage', 'open-assistant', 'spark', 'secondary')}</div></header><main>${c.mode === 'demo' ? `<div class="sample-banner">${icon('store')}<span><strong>You’re exploring a sample shop.</strong> Connect ERPNext to see your own bills, stock and dues.</span><button data-page="connect">Connect my shop ${icon('arrow')}</button></div>` : ''}${s?.stale ? `<div class="warning-banner" role="alert"><strong>These records may be out of date.</strong> ${esc(s.sync_error)} Showing the last successful snapshot from ${new Date(s.captured_at).toLocaleString('en-IN')}.</div>` : ''}${{ today: todayPage, assistant: assistantPage, stock: stockPage, customers: () => duesPage('customers'), suppliers: () => duesPage('suppliers'), bills: billsPage, reminders: remindersPage, connect: connectPage }[page]()}<footer>A helping hand for the business you built.<span>${icon('leaf')}ShopSage · ERPNext enhancer</span></footer></main></div>`;
  if (page === 'assistant') document.querySelector('.chat-messages')?.scrollTo(0, 999999);
  if (page === 'connect') populateVoices();
}
function unavailable() {
  return `<section class="card connection-empty">${icon('link')}<h2>Let’s connect your shop.</h2><p>${esc(state.error || 'No records loaded yet.')}</p><div class="inline-actions">${button('Check connection', 'connect', 'settings')}${button('Try again', 'refresh', 'refresh', 'secondary')}</div><p class="field-help">ShopSage won’t substitute sample figures when a live connection fails.</p></section>`;
}
function metric(label, value, note, ic, cls = '') {
  return `<article class="metric ${cls}"><div class="metric-label">${label}<span>${icon(ic)}</span></div><div class="metric-value">${value}</div><div class="metric-detail">${note}</div></article>`;
}
function todayPage() {
  const s = snapshot();
  if (!s)
    return (
      heading(
        'YOUR SHOP, WITH A LITTLE MORE CLARITY',
        'A simpler day starts here.',
        'Connect ERPNext once. Find your daily answers in one place.',
      ) + unavailable()
    );
  const sum = s.summary,
    low = s.stock.filter((p) => p.low),
    tasks = state.reminders.filter((t) => !t.done && t.due <= s.today);
  return (
    heading(
      'YOUR DAILY PICTURE',
      `Good ${new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, ${esc(state.config.owner.split(' ')[0])} <span class="wave">☀</span>`,
      'A clear picture of your shop. A little more room to breathe.',
      sourceLink(state.config.erp_url + '/app/point-of-sale', 'Open billing in ERPNext', 'btn primary'),
    ) +
    `<section class="assistant-hero"><div class="hero-leaf">${icon('spark')}</div><div class="hero-copy"><div class="eyebrow">YOUR BUSINESS, IN PLAIN WORDS</div><h2>Ask a question. Find your next step.</h2><p>Type it, say it, or start with a suggestion.</p></div><div class="hero-actions">${button('Talk to Sage', 'voice', 'mic', 'light')}${button('Type a question', 'open-assistant', 'arrow', 'hero-outline')}</div></section><section class="metrics">${metric('Invoiced today', money(sum.today_sales), `${sum.today_documents} submitted documents · includes tax`, 'sales', 'featured')}${metric('Customers to follow up', money(sum.overdue), 'Overdue submitted sales invoices', 'users')}${metric('Shelves to check', sum.low_stock, 'Items at or below safety stock', 'box')}${metric('Supplier invoices open', money(sum.payable), 'Unpaid submitted purchase invoices', 'wallet')}</section>
 <div class="dashboard-columns"><div class="dashboard-main"><section class="card sales-chart"><div class="card-heading"><div><h2>Your week, at a glance</h2><p>Invoiced sales, including returns and taxes.</p></div>${badge('Last 7 days', 'neutral')}</div>${chart(s.daily.slice(-7))}<div class="chart-foot"><span><i class="legend-dot"></i>Sales + POS invoices · no merged duplicates</span><button class="text-button" data-page="bills">See my bills ${icon('arrow')}</button></div></section><section class="card"><div class="card-heading"><div><h2>Keep your shelves ready</h2><p>A quick check before the next busy hour.</p></div>${badge(low.length + ' to check', 'amber')}</div><div class="stock-list">${
   low
     .slice(0, 3)
     .map((p) => stockRow(p))
     .join('') || empty('Your shelves look healthy.', 'No loaded items are below their safety level.')
 }</div><button class="card-bottom-link" data-page="stock">See the full stock picture ${icon('arrow')}</button></section></div><div class="dashboard-rail"><section class="sage-card"><div class="sage-card-top"><span class="sage-star">${icon('spark')}</span><span>Your shop companion</span>${badge(state.config.groq_ready ? 'GROQ' : 'LOCAL')}</div><h2>Less guessing.<br>More knowing.</h2><p>Understand the numbers. Find the words. Plan the next step.</p>${prompts
   .slice(0, 3)
   .map(
     ([q]) =>
       `<button class="sage-prompt" data-action="ask" data-question="${q}">${q} ${icon('arrow')}</button>`,
   )
   .join(
     '',
   )}<button class="sage-start" data-page="assistant">Let’s talk, Sage ${icon('spark')}</button><small>${state.config.groq_ready ? 'Groq is configured · questions use your shop context' : 'Add your Groq key for conversational answers'}</small></section><section class="card"><div class="card-heading"><h2>A little follow-up helps</h2>${icon('users')}</div><div class="dues-preview">${
   s.receivables
     .filter((r) => r.overdue)
     .slice(0, 2)
     .map(
       (r) =>
         `<div class="follow-up"><span class="avatar pale">${esc(r.party?.charAt(0) || 'C')}</span><div><strong>${esc(r.party)}</strong><small>${r.days_overdue} ${r.days_overdue === 1 ? 'day' : 'days'} overdue</small></div><b>${money(r.amount)}</b></div>`,
     )
     .join('') || '<p>No overdue invoices in the loaded records.</p>'
 }</div><button class="card-bottom-link" data-page="customers">See customer dues ${icon('arrow')}</button></section><section class="card task-card"><div class="card-heading"><h2>On your list</h2>${badge(tasks.length + ' due', 'neutral')}</div>${tasks.slice(0, 2).map(taskRow).join('') || '<p class="rail-note">A little breathing room. Add a reminder for later.</p>'}<button class="text-button" data-page="reminders">My reminders ${icon('arrow')}</button></section></div></div><section class="quick-start-grid">${prompts.map(([q, title, ic]) => `<button data-action="ask" data-question="${q}" class="quick-question">${icon(ic)}<span><small>${title}</small><strong>${q}</strong></span>${icon('arrow')}</button>`).join('')}</section><div class="scope-note">${icon('help')}Sales and dues cover the company. Stock covers ${esc(state.config.warehouse || 'all readable company warehouses')}. Figures are a snapshot, not a live accounting ledger.</div>`
  );
}
function chart(days) {
  const max = Math.ceil((Math.max(...days.map((d) => Math.abs(d.total)), 10000) * 1.15) / 100000) * 100000;
  const min = Math.min(0, ...days.map((d) => d.total)),
    span = max - min;
  const points = days.map((d, i) => [
    55 + i * (600 / (days.length - 1 || 1)),
    178 - ((d.total - min) / span) * 160,
  ]);
  const path = points.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  return `<div class="chart-total">${money(days.reduce((t, d) => t + d.total, 0))}<span>across the last ${days.length} days</span></div><div class="chart-wrap"><svg viewBox="0 0 680 220" role="img" aria-label="Daily invoiced sales: ${days.map((d) => dateLabel(d.date) + ' ' + money(d.total)).join(', ')}"><defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#9bc28c" stop-opacity=".3"/><stop offset="100%" stop-color="#9bc28c" stop-opacity=".02"/></linearGradient></defs>${[0, 1, 2, 3].map((i) => `<line x1="55" x2="660" y1="${18 + (i * 160) / 3}" y2="${18 + (i * 160) / 3}" stroke="#e5ebe0" stroke-dasharray="3 5"/><text x="0" y="${22 + (i * 160) / 3}" font-size="10">${money(Math.round(max - (i * span) / 3))}</text>`).join('')}<path d="${path} L655,178 L55,178 Z" fill="url(#fade)"/><path d="${path}" fill="none" stroke="#568167" stroke-width="2.5"/>${points.map(([x, y], i) => `<circle cx="${x}" cy="${y}" r="3.5" fill="white" stroke="#568167" stroke-width="2"><title>${dateLabel(days[i].date)}: ${money(days[i].total)}</title></circle><text x="${x}" y="208" text-anchor="middle" font-size="10">${dateLabel(days[i].date)}</text>`).join('')}</svg></div>`;
}
function stockRow(p) {
  return `<div class="stock-row"><span class="product-icon ${p.category === 'Dairy' ? 'blue' : p.category === 'Household' ? 'purple' : 'green'}">${icon('box')}</span><div class="grow"><strong>${esc(p.name)}</strong><small>${esc(p.category)} · Safety level ${qty(p.safety)}</small></div><div class="stock-quantity"><strong>${qty(p.actual)} left</strong><small>${esc(p.unit)}</small></div><button class="small-btn" data-action="item" data-code="${esc(p.code)}">Details ${icon('chevron')}</button></div>`;
}
function stockPage() {
  const s = snapshot();
  if (!s) return unavailable();
  const rows = s.stock.filter(
    (p) =>
      (p.name + ' ' + p.code).toLowerCase().includes(query.toLowerCase()) &&
      (filter === 'all' || (filter === 'low' && p.low) || (filter === 'out' && p.actual <= 0)),
  );
  return (
    heading(
      'A LITTLE AHEAD OF THE EMPTY SHELF',
      'Know what’s running low.',
      'Your ERPNext stock, explained in everyday language.',
      `<a class="btn secondary" href="/api/export/stock">${icon('down')}Export stock</a>${button('Plan a restock', 'restock-draft', 'spark')}`,
    ) +
    `<section class="metrics three">${metric('Items in this view', s.stock.length, 'Enabled stock items with a company warehouse Bin', 'box')}${metric('Need a stock check', s.summary.low_stock, 'Actual quantity ≤ item safety stock', 'clock')}${metric('Stock value', money(s.summary.stock_value), 'From ERPNext Bin.stock_value', 'wallet')}</section><section class="card"><div class="toolbar"><label class="input-search">${icon('search')}<input id="filter-search" aria-label="Search stock" placeholder="Find an item or item code…" value="${esc(query)}"></label><select id="stock-filter" aria-label="Filter stock"><option value="all" ${filter === 'all' ? 'selected' : ''}>All items</option><option value="low" ${filter === 'low' ? 'selected' : ''}>Needs attention</option><option value="out" ${filter === 'out' ? 'selected' : ''}>Out of stock</option></select><span class="muted">${rows.length} items</span></div><div class="table-wrap"><table><thead><tr><th>Item</th><th class="num">On hand</th><th class="num">Projected</th><th class="num">Safety level</th><th>Status</th><th></th></tr></thead><tbody>${rows.map((p) => `<tr><td><div class="product-cell"><span class="product-icon ${p.category === 'Dairy' ? 'blue' : 'green'}">${icon('box')}</span><div><strong>${esc(p.name)}</strong><small>${esc(p.code)} · ${esc(p.unit)}</small></div></div></td><td class="num strong">${qty(p.actual)}</td><td class="num">${qty(p.projected)}</td><td class="num">${qty(p.safety)}</td><td>${badge(p.actual <= 0 ? 'Out of stock' : p.low ? 'Check stock' : 'Looking good', p.low ? 'amber' : 'green')}</td><td><button class="small-btn" data-action="item" data-code="${esc(p.code)}">Details ${icon('chevron')}</button></td></tr>`).join('')}</tbody></table></div>${!rows.length ? empty('Nothing matches that search.', 'Try another name or stock filter.') : ''}</section><div class="scope-note">${icon('help')}Projected quantity includes ERPNext’s incoming and reserved movements. Suggestions use item safety stock across selected warehouses, not warehouse reorder rules.</div>`
  );
}
function duesPage(kind) {
  const s = snapshot();
  if (!s) return unavailable();
  const customer = kind === 'customers',
    rows = (customer ? s.receivables : s.payables).filter(
      (r) =>
        (r.party + ' ' + r.name).toLowerCase().includes(query.toLowerCase()) &&
        (filter === 'all' || r.overdue),
    );
  return (
    heading(
      customer ? 'GOOD RELATIONSHIPS. CLEAR FOLLOW-UPS.' : 'KEEP THE PEOPLE WHO KEEP YOU STOCKED',
      customer ? 'A little less left pending.' : 'Know what’s due to suppliers.',
      customer
        ? 'See unpaid sales invoices. Find a friendly way to follow up.'
        : 'A simple view of unpaid purchase invoices from ERPNext.',
      button(
        customer ? 'Draft a reminder' : 'Ask about supplier dues',
        'ask',
        'spark',
        'primary',
        `data-question="${customer ? 'Help me draft a friendly reminder for overdue customer invoices.' : 'Summarize my supplier dues and what is overdue.'}"`,
      ),
    ) +
    `<section class="metrics three">${metric('Open invoice amount', money(rows.reduce((n, r) => n + r.amount, 0)), 'INR equivalent using invoice conversion rate', 'wallet')}${metric('Overdue amount', money(rows.filter((r) => r.overdue).reduce((n, r) => n + r.amount, 0)), 'Due date has passed', 'clock')}${metric('Invoices in view', rows.length, 'Submitted documents with outstanding amounts', 'sales')}</section><section class="card"><div class="toolbar"><label class="input-search">${icon('search')}<input id="filter-search" value="${esc(query)}" aria-label="Search dues" placeholder="Find a name or invoice…"></label><select id="dues-filter" aria-label="Filter dues"><option value="all" ${filter === 'all' ? 'selected' : ''}>All unpaid invoices</option><option value="overdue" ${filter === 'overdue' ? 'selected' : ''}>Only overdue</option></select></div><div class="table-wrap"><table><thead><tr><th>${customer ? 'Customer' : 'Supplier'}</th><th>Invoice</th><th>Due date</th><th>Status</th><th class="num">Amount open</th><th></th></tr></thead><tbody>${rows.map((r) => `<tr><td class="strong">${esc(r.party)}</td><td>${esc(r.name)}</td><td>${dateLabel(r.due_date)}</td><td>${badge(r.overdue ? r.days_overdue + (r.days_overdue === 1 ? ' day overdue' : ' days overdue') : 'Upcoming', r.overdue ? 'amber' : 'green')}</td><td class="num strong">${money(r.amount)}</td><td>${sourceLink(r.url, 'Open invoice')}</td></tr>`).join('')}</tbody></table></div>${!rows.length ? empty('All clear in this view.', 'No unpaid invoices match your filters.') : ''}</section><div class="scope-note">${icon('help')}This is an unpaid invoice list, not the complete ${customer ? 'receivables' : 'payables'} ledger. ${customer ? 'Unconsolidated POS credit and unallocated advances are not included. ' : ''}Record payments in ERPNext; ShopSage never moves money or changes invoices.</div>`
  );
}
function billsPage() {
  const s = snapshot();
  if (!s) return unavailable();
  const rows = s.sales.filter(
    (r) =>
      (r.name + ' ' + r.customer).toLowerCase().includes(query.toLowerCase()) &&
      (filter === 'all' ||
        (filter === 'today' && r.date === s.today) ||
        (filter === 'returns' && r.is_return)),
  );
  return (
    heading(
      'YOUR BILLING. WITH A CLEARER VIEW.',
      'Every little sale adds up.',
      'Submitted bills from the last 30 days. Open originals in ERPNext.',
      sourceLink(state.config.erp_url + '/app/point-of-sale', 'Open ERPNext billing', 'btn primary'),
    ) +
    `<section class="metrics three">${metric('Invoiced today', money(s.summary.today_sales), `${s.summary.today_documents} submitted documents`, 'sales', 'featured')}${metric('Last 30 days', money(s.summary.month_sales), 'Tax-inclusive amounts; returns reduce sales', 'chart')}${metric('Today before invoice taxes', money(s.summary.today_net), 'Net sales, not profit or cash received', 'wallet')}</section><section class="card"><div class="toolbar"><label class="input-search">${icon('search')}<input id="filter-search" value="${esc(query)}" aria-label="Search bills" placeholder="Find a bill or customer…"></label><select id="bill-filter" aria-label="Filter bills"><option value="all" ${filter === 'all' ? 'selected' : ''}>Last 30 days</option><option value="today" ${filter === 'today' ? 'selected' : ''}>Today</option><option value="returns" ${filter === 'returns' ? 'selected' : ''}>Returns</option></select><span class="muted">${rows.length} documents</span></div><div class="table-wrap bills-table"><table><thead><tr><th>Bill</th><th>Customer</th><th>Date</th><th>Type</th><th class="num">Amount</th><th></th></tr></thead><tbody>${rows.map((r) => `<tr><td class="strong">${esc(r.name)}</td><td>${esc(r.customer)}</td><td>${dateLabel(r.date)}</td><td>${badge(r.is_return ? 'Return' : r.doctype, r.is_return ? 'amber' : 'neutral')}</td><td class="num strong">${money(r.total)}</td><td>${sourceLink(r.url, 'View bill')}</td></tr>`).join('')}</tbody></table></div>${!rows.length ? empty('No bills match this view.', 'Try another search or date filter.') : ''}</section><div class="scope-note">${icon('help')}Original POS invoices are counted; their consolidated Sales Invoices are excluded to avoid duplicates. Draft and cancelled documents are excluded. Use ERPNext for tax invoices, printing, payments and returns.</div>`
  );
}
function taskRow(t) {
  return `<div class="task-row"><button class="task-check ${t.done ? 'done' : ''}" data-action="toggle-reminder" data-id="${t.id}" aria-label="${t.done ? 'Reopen' : 'Complete'} ${esc(t.title)}">${t.done ? icon('check') : ''}</button><div><strong class="${t.done ? 'completed' : ''}">${esc(t.title)}</strong><small>${dateLabel(t.due)}${!t.done && t.due < new Date().toLocaleDateString('en-CA') ? ' · Overdue' : ''}</small></div></div>`;
}
function remindersPage() {
  return (
    heading(
      'A LITTLE LESS ON YOUR MIND',
      'Off your mind. On your list.',
      'Personal reminders saved by ShopSage, separate from ERPNext.',
      button('Add reminder', 'add-reminder'),
    ) +
    `<section class="card task-page"><div class="card-heading"><h2>Your reminders</h2>${badge(state.reminders.filter((t) => !t.done).length + ' to go', 'neutral')}</div>${state.reminders.map(taskRow).join('') || empty('Make a little room to breathe.', 'Add your next delivery check, stock review or customer follow-up.')}</section><div class="scope-note">${icon('help')}These are in-app reminders. ShopSage doesn’t send background notifications.</div>`
  );
}
function assistantPage() {
  return (
    heading(
      'TYPE IT. SAY IT. WORK IT OUT.',
      'Your shop, in plain conversation.',
      'From “what’s running low?” to “help me write a reminder”.',
    ) +
    `<div class="assistant-layout"><section class="card chat-card"><div class="chat-header"><span class="sage-star">${icon('spark')}</span><div><h2>Talk to Sage</h2><p>${state.config.groq_ready ? 'Groq configured · grounded in your ERPNext snapshot' : 'Local summaries · add a Groq key for AI conversation'}</p></div><button class="text-button" data-action="new-chat" ${pending ? 'disabled' : ''}>Fresh conversation</button></div><div class="chat-messages" aria-live="polite">${!messages.length ? `<div class="welcome-message"><span class="welcome-orb">${icon('leaf')}</span><h2>A helping hand for your shop day.</h2><p>Ask about bills, stock, customer dues or supplier invoices. I can also help draft a message for you to review.</p><div class="welcome-prompts">${prompts.map(([q, title, ic]) => `<button data-action="ask" data-question="${q}">${icon(ic)}${q}${icon('arrow')}</button>`).join('')}</div><p class="field-help">${state.config.mode === 'demo' ? 'You are using fictional sample shop data.' : ''} I don’t change ERPNext records or send messages.</p></div>` : messages.map((m, i) => `<div class="message ${m.role}"><span class="message-avatar">${m.role === 'assistant' ? icon('spark') : esc(state.config.owner.charAt(0))}</span><div><small>${m.role === 'assistant' ? (m.engine === 'groq' ? 'Sage · Groq' : 'Sage · local summary') : 'You'}</small><div class="message-bubble ${m.error ? 'error-bubble' : ''}">${esc(m.text).replace(/\n/g, '<br>')}</div>${m.role === 'assistant' && !m.error ? `<div class="answer-actions"><button class="text-button" data-action="speak" data-index="${i}">${icon('speaker')}${speakingIndex === i ? 'Stop reading' : 'Read aloud'}</button><button class="text-button" data-action="copy-answer" data-index="${i}">Copy text</button><button class="text-button" data-action="save-answer" data-index="${i}">Save draft</button></div>${m.sources?.length ? `<details class="answer-sources"><summary>Based on ${m.sources.length} record source${m.sources.length === 1 ? '' : 's'}</summary><ul>${m.sources.map((s) => `<li>${esc(s)}</li>`).join('')}</ul><p>Snapshot: ${esc(m.captured_at || '')}${m.stale ? ' · OUT OF DATE' : ''}</p></details>` : ''}` : ''}</div></div>`).join('')}${pending ? '<div class="thinking" role="status"><i></i><i></i><i></i><span>Looking at your shop picture…</span></div>' : ''}</div><form class="chat-form" id="chat-form"><label class="sr-only" for="question">Ask Sage</label><input id="question" name="question" placeholder="Ask me about your shop…" required maxlength="2000" autocomplete="off" ${pending ? 'disabled' : ''}><button type="button" class="icon-btn microphone" data-action="voice" aria-label="Speak your question" ${pending ? 'disabled' : ''}>${icon('mic')}</button><button class="btn primary" aria-label="Send question" ${pending ? 'disabled' : ''}>${icon('arrow')}</button></form><div class="composer-bottom"><span>${state.config.groq_ready ? 'Questions and selected shop summaries are sent to Groq.' : 'No Groq key yet. Showing local, rule-based summaries.'}</span><button data-page="connect" class="text-button">Voice & privacy ${icon('settings')}</button></div></section><aside class="assistant-suggestions"><h3>A good place to start</h3>${prompts.map(([q, title, ic]) => `<button class="suggestion-card" data-action="ask" data-question="${q}" ${pending ? 'disabled' : ''}><span>${icon(ic)}${title}</span><strong>${q}</strong>${icon('arrow')}</button>`).join('')}<section class="voice-tip"><span class="product-icon green">${icon('mic')}</span><h3>Say it your way.</h3><p>Record in English or Hindi. Review the transcript, then send it when you’re ready.</p><button class="text-button" data-action="voice">Try voice input ${icon('arrow')}</button></section><p>Drafts are for your review. Payments, billing and stock changes happen in ERPNext.</p></aside></div>`
  );
}
function connectPage() {
  const c = state.config;
  return (
    heading(
      'SET IT UP ONCE. KEEP YOUR DAY SIMPLE.',
      'Your shop. Your voice.',
      'Connect ERPNext and choose how you’d like to talk to Sage.',
      button('Reload connection', 'refresh', 'refresh', 'secondary'),
    ) +
    `<div class="setup-steps"><span>${c.groq_ready ? icon('check') : '1'} Add your Groq key</span><i></i><span>${c.mode !== 'demo' ? icon('check') : '2'} Connect ERPNext</span><i></i><span>3 Choose your voice</span></div><div class="settings-grid"><div><section class="card settings-info"><div class="section-title"><span class="product-icon green">${icon('spark')}</span><h2>Your assistant</h2>${badge(c.groq_ready ? 'Key configured' : 'Key needed', c.groq_ready ? 'green' : 'amber')}</div><p>ShopSage reads <strong>this project’s .env</strong>. Your key stays on the Python server. Changes are picked up without restarting.</p><div class="config-line"><span>Provider</span><strong>Groq</strong></div><div class="config-line"><span>Chat model</span><code>${esc(c.groq_model)}</code></div><div class="config-line"><span>Speech recognition</span><code>${esc(c.stt_model)}</code></div><p class="field-help">Add your key to <code>GROQ_API_KEY</code> in the provided <code>.env</code>. No need to paste it into the app.</p></section><section class="card settings-info"><div class="section-title"><span class="product-icon blue">${icon('link')}</span><h2>ERPNext connection</h2>${badge(c.mode === 'demo' ? 'Sample shop' : snapshot() && !snapshot().stale ? 'Records loaded' : 'Needs attention', c.mode === 'demo' || !snapshot() ? 'amber' : 'green')}</div><div class="config-line"><span>Source</span><strong>${esc(c.mode)}</strong></div><div class="config-line"><span>Company</span><strong>${esc(c.company) || 'Not set'}</strong></div><div class="config-line"><span>Stock warehouse</span><strong>${esc(c.warehouse) || 'All readable company warehouses'}</strong></div><div class="config-line"><span>ERPNext site</span><code>${esc(c.erp_url)}</code></div><p>For the recommended connection, set <code>DATA_MODE=erpnext-api</code>, the exact company name, and a dedicated Frappe read-only user’s API key and secret.</p><details class="setup-details"><summary>Need a direct database connection?</summary><p>Choose <code>erpnext-db</code> for MariaDB. Install <code>requirements-db.txt</code> and configure a separate SELECT-only account. This bypasses Frappe user permissions, so use a carefully scoped reporting account. ShopSage starts a read-only transaction and uses fixed, parameterized queries.</p></details>${state.error ? `<p class="inline-error" role="alert">${esc(state.error)}</p>` : ''}<div class="inline-actions">${button('Check my connection', 'refresh', 'refresh')}${link(erpHome(), 'Open ERPNext', 'btn secondary')}</div></section><section class="card settings-info"><h2>Repository & site paths</h2><p>Optional: set <code>FRAPPE_BENCH_PATH</code>, <code>FRAPPE_SITE</code> and/or <code>ERPNEXT_REPO_PATH</code>. ShopSage checks the standard ERPNext source locations. It never edits the billing repository or reads out site passwords.</p>${connection ? `<div class="config-line"><span>ERPNext repository</span><strong>${connection.paths.repo_configured ? (connection.paths.repo_exists ? 'Found' : 'Not found') : 'Not configured'}</strong></div><div class="config-line"><span>Site database engine</span><strong>${esc(connection.paths.database_type || 'Not inspected')}</strong></div><details class="setup-details"><summary>View schema & repository mapping</summary><div class="schema-list">${connection.paths.schema.map((r) => `<div><strong>${esc(r.doctype)} <small>${r.found === null ? 'Optional path' : r.missing_fields?.length ? 'Needs review' : r.found ? '✓ Found' : 'Missing'}</small></strong><code>${esc(r.table)}</code><code>${esc(r.relative_path)}</code>${r.missing_fields?.length ? `<p class="inline-error">Missing fields: ${esc(r.missing_fields.join(', '))}</p>` : ''}</div>`).join('')}</div></details>` : '<p class="field-help">Loading source-path checks…</p>'}</section></div><div><section class="card settings-info voice-settings"><div class="section-title"><span class="product-icon purple">${icon('speaker')}</span><h2>Make yourself heard.</h2></div><p>Speak naturally. Let Sage read back the answer.</p><label>Conversation language<select id="language"><option value="en-IN" ${language === 'en-IN' ? 'selected' : ''}>English (India)</option><option value="hi-IN" ${language === 'hi-IN' ? 'selected' : ''}>हिन्दी (Hindi)</option></select></label><label>Reading voice<select id="voice-choice" aria-label="Reading voice"><option value="">Device default voice</option></select></label><label class="checkbox-label"><input id="auto-speak" type="checkbox" ${autoSpeak ? 'checked' : ''}> Read new answers aloud automatically</label><div class="inline-actions">${button('Try this voice', 'test-voice', 'speaker', 'secondary')}${button('Stop reading', 'stop-speech', 'close', 'secondary')}</div><p class="field-help">Voices depend on your device. Hindi needs an installed Hindi voice; your OS may download it separately. Some device voices use their provider’s online service.</p></section><section class="card settings-info"><h2>A little clarity on your data.</h2><ul class="privacy-list"><li><strong>Shop records:</strong> read from ERPNext. Never changed by ShopSage.</li><li><strong>Chat:</strong> your question and selected summary records go to Groq only when you send a question with a key configured.</li><li><strong>Voice input:</strong> audio goes to Groq only when you choose “Transcribe”. The transcript is yours to edit before sending.</li><li><strong>Reminders:</strong> saved in ShopSage’s own local database.</li><li><strong>Conversation:</strong> lives only in browser memory; a refresh clears it.</li></ul></section><section class="card settings-info"><h2>Built to work alongside.</h2><p>ERPNext remains your source for billing, tax invoices, receipts, stock movements and accounting. ShopSage adds a simpler daily view and a helping hand.</p><a class="text-button" href="https://frappe.io/erpnext/india" target="_blank" rel="noopener noreferrer">Why ERPNext? ${icon('arrow')}</a><p class="field-help">No independently verified India-only market-share ranking was found. ERPNext is our integration choice, not a claim of market leadership.</p></section></div></div>`
  );
}

function modal(title, body) {
  lastFocus = document.activeElement;
  document.querySelector('#overlay').innerHTML =
    `<div class="modal-backdrop"><section role="dialog" aria-modal="true" aria-labelledby="modal-title" class="modal"><div class="modal-heading"><h2 id="modal-title">${title}</h2><button class="icon-btn" data-action="close-modal" aria-label="Close dialog">${icon('close')}</button></div>${body}</section></div>`;
  document.body.classList.add('modal-open');
  document.querySelector('.modal input,.modal button')?.focus();
}
function stopStream() {
  stream?.getTracks().forEach((t) => t.stop());
  stream = null;
  clearTimeout(recordTimer);
}
function closeModal() {
  voiceToken++;
  if (recording && recording.state === 'recording') recording.stop();
  recording = null;
  stopStream();
  if (audioURL) URL.revokeObjectURL(audioURL);
  audioURL = null;
  audioBlob = null;
  document.querySelector('#overlay').innerHTML = '';
  document.body.classList.remove('modal-open');
  lastFocus?.focus();
}
function download(text, name, type = 'text/plain;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function restockText() {
  const s = snapshot();
  return (
    `RESTOCK REVIEW — ${s.company}\nSnapshot: ${s.captured_at}${s.stale ? ' (OUT OF DATE)' : ''}\n${s.mode === 'demo' ? 'FICTIONAL SAMPLE SHOP\n' : ''}\n` +
    s.stock
      .filter((p) => p.low)
      .map(
        (p) =>
          `${p.name} (${p.code})\nOn hand: ${qty(p.actual)} ${p.unit}; projected: ${qty(p.projected)}; safety stock: ${qty(p.safety)}\nSuggested top-up for review: ${qty(p.suggested)} ${p.unit}\n`,
      )
      .join('\n') +
    '\nDraft only. Review stock, incoming deliveries, pack sizes and supplier availability in ERPNext. This is not a purchase order.'
  );
}
function showItem(code) {
  const p = snapshot().stock.find((p) => p.code === code);
  if (!p) return;
  modal(
    esc(p.name),
    `<div class="settings-info item-details"><p>${esc(p.code)} · ${esc(p.unit)} ${badge(p.low ? 'Needs a stock check' : 'Looking good', p.low ? 'amber' : 'green')}</p><div class="item-metrics"><div><span>On hand</span><strong>${qty(p.actual)}</strong></div><div><span>Projected</span><strong>${qty(p.projected)}</strong></div><div><span>Safety level</span><strong>${qty(p.safety)}</strong></div></div><h3>In your warehouses</h3>${p.warehouses.map((w) => `<div class="config-line"><span>${esc(w.name)}</span><strong>${qty(w.actual)} on hand · ${qty(w.projected)} projected</strong></div>`).join('')}<p>Suggested top-up: <strong>${qty(p.suggested)} ${esc(p.unit)}</strong>. This aims for twice the item safety stock using projected quantity, subject to minimum order quantity. It is a suggestion, not a supplier order.</p>${sourceLink(p.url, 'Open item in ERPNext', 'btn primary full')}</div>`,
  );
}
async function refresh() {
  const buttons = document.querySelectorAll('[data-action="refresh"]');
  buttons.forEach((b) => (b.disabled = true));
  try {
    state = await request('refresh', {});
    connection = null;
    render();
    if (page === 'connect') loadConnection();
    notify(state.error || snapshot()?.sync_error || 'Your shop picture is up to date.');
  } catch (e) {
    notify(e.message);
    buttons.forEach((b) => (b.disabled = false));
  }
}
async function loadConnection() {
  try {
    connection = await request('connection');
    if (page === 'connect') render();
  } catch (e) {
    notify(e.message);
  }
}
async function ask(question) {
  if (pending) return;
  if (!question.trim()) return;
  if (!snapshot()) {
    notify('Connect your shop before asking about its records.');
    go('connect');
    return;
  }
  if (page !== 'assistant') go('assistant');
  const history = messages
    .filter((m) => !m.error)
    .slice(-8)
    .map((m) => ({ role: m.role, content: m.text }));
  messages.push({ role: 'user', text: question });
  pending = true;
  render();
  try {
    const answer = await request('chat', { question, history, language });
    messages.push({ role: 'assistant', ...answer });
    if (autoSpeak) speak(answer.text, messages.length - 1);
  } catch (e) {
    messages.push({ role: 'assistant', text: e.message, error: true });
  } finally {
    pending = false;
    if (page === 'assistant') render();
  }
}
function speak(text, index = null) {
  if (!('speechSynthesis' in window)) {
    notify('Read-aloud is unavailable in this browser. Try Chrome or Edge.');
    return;
  }
  if (speakingIndex === index && speakingIndex !== null) {
    stopSpeech();
    return;
  }
  const token = ++speechToken;
  window.speechSynthesis.cancel();
  const speech = new SpeechSynthesisUtterance(text.replace(/[#*`]/g, ''));
  speech.lang = language;
  speech.rate = 0.95;
  const voices = window.speechSynthesis.getVoices();
  const chosen =
    voices.find((v) => v.name === voiceName) ||
    voices.find((v) => v.lang.toLowerCase() === language.toLowerCase()) ||
    voices.find((v) => v.lang.startsWith(language.slice(0, 2)));
  if (chosen) speech.voice = chosen;
  else if (language === 'hi-IN') {
    notify('No Hindi voice was found. Add a Hindi voice in your device’s speech settings.');
    return;
  }
  speakingIndex = index;
  speech.onend = () => {
    if (token !== speechToken) return;
    speakingIndex = null;
    updateSpeechButtons();
  };
  speech.onerror = (e) => {
    if (token !== speechToken) return;
    speakingIndex = null;
    updateSpeechButtons();
    if (!['canceled', 'interrupted'].includes(e.error))
      notify('Audio playback could not start. Check your device’s speech voices.');
  };
  window.speechSynthesis.speak(speech);
  updateSpeechButtons();
}
function updateSpeechButtons() {
  document.querySelectorAll('[data-action="speak"]').forEach((b) => {
    b.innerHTML =
      icon('speaker') + (Number(b.dataset.index) === speakingIndex ? 'Stop reading' : 'Read aloud');
  });
}
function stopSpeech() {
  speechToken++;
  window.speechSynthesis?.cancel();
  speakingIndex = null;
  updateSpeechButtons();
}
function populateVoices() {
  if (!window.speechSynthesis) return;
  const select = document.querySelector('#voice-choice');
  if (!select) return;
  select.innerHTML =
    '<option value="">Device default voice</option>' +
    window.speechSynthesis
      .getVoices()
      .map(
        (v) =>
          `<option value="${esc(v.name)}" ${v.name === voiceName ? 'selected' : ''}>${esc(v.name)} · ${esc(v.lang)}</option>`,
      )
      .join('');
}
if (window.speechSynthesis) window.speechSynthesis.addEventListener('voiceschanged', populateVoices);

function voiceDialog() {
  if (!state.config.groq_ready) {
    modal(
      'Let’s enable voice input.',
      `<div class="help-content"><p>Speech recognition uses Groq Whisper. Add your <code>GROQ_API_KEY</code> to this project’s <code>.env</code>, then reload the connection.</p><p>Your voice is recorded only after you press Record. Audio is sent to Groq only when you choose Transcribe.</p><button class="btn primary full" data-page="connect">Open connection & voice ${icon('arrow')}</button></div>`,
    );
    return;
  }
  modal(
    'Say it your way.',
    `<div class="voice-dialog"><div class="voice-orb">${icon('mic')}</div><h3>Your next question, spoken.</h3><p>Record in ${language === 'hi-IN' ? 'Hindi' : 'English'}. You can listen back and review the transcript before sending.</p><p class="voice-notice">Recording stays in memory until you press Transcribe. Then audio is sent to Groq. Maximum 60 seconds or 12 MB.</p><div id="record-state">${button('Record my question', 'record', 'mic')}</div><label class="audio-upload">Or choose an audio file<input id="audio-upload" type="file" accept="audio/webm,audio/ogg,audio/mp4,audio/wav,audio/mpeg,.m4a,.mp3,.wav,.webm,.ogg"></label><div class="form-error" id="voice-error" role="alert"></div></div>`,
  );
}
function showAudio() {
  if (audioURL) URL.revokeObjectURL(audioURL);
  audioURL = URL.createObjectURL(audioBlob);
  document.querySelector('#record-state').innerHTML =
    `<audio controls src="${audioURL}" aria-label="Preview your recording"></audio><div class="inline-actions">${button('Transcribe', 'transcribe', 'spark')}${button('Record again', 'record', 'mic', 'secondary')}</div>`;
}
async function record() {
  const token = voiceToken;
  document.querySelector('#voice-error').textContent = '';
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    document.querySelector('#voice-error').textContent =
      'Recording is unavailable here. Use Chrome/Edge on localhost or choose an audio file.';
    return;
  }
  try {
    stopSpeech();
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (token !== voiceToken) {
      stopStream();
      return;
    }
    const mime = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4'].find((t) =>
      MediaRecorder.isTypeSupported(t),
    );
    recording = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    let chunks = [],
      size = 0;
    recording.ondataavailable = (e) => {
      if (e.data.size) {
        chunks.push(e.data);
        size += e.data.size;
        if (size > 12_000_000 && recording?.state === 'recording') recording.stop();
      }
    };
    recording.onstop = () => {
      stopStream();
      if (token !== voiceToken) return;
      audioBlob = new Blob(chunks, { type: recording.mimeType });
      recording = null;
      if (audioBlob.size > 12_000_000) {
        document.querySelector('#voice-error').textContent =
          'That recording is too large. Try a shorter question.';
        document.querySelector('#record-state').innerHTML = button('Try recording again', 'record', 'mic');
        return;
      }
      showAudio();
    };
    recording.onerror = () => {
      stopStream();
      document.querySelector('#voice-error').textContent = 'Recording failed. Try again or choose a file.';
    };
    recording.start(500);
    document.querySelector('#record-state').innerHTML =
      `<div class="recording-label"><i></i> Recording… speak naturally.</div>${button('Stop recording', 'stop-recording', 'check')}`;
    recordTimer = setTimeout(() => {
      if (recording?.state === 'recording') recording.stop();
    }, 60000);
  } catch (e) {
    stopStream();
    if (token === voiceToken)
      document.querySelector('#voice-error').textContent =
        'Microphone access was unavailable. Allow microphone access in your browser, or choose an audio file.';
  }
}
async function transcribeAudio() {
  if (!audioBlob) return;
  const token = voiceToken;
  document.querySelector('#voice-error').textContent = '';
  document.querySelector('#record-state').innerHTML =
    '<p class="recording-label">Transcribing with Groq…</p>';
  try {
    const r = await fetch('/api/transcribe', {
      method: 'POST',
      headers: { 'Content-Type': audioBlob.type || 'audio/webm', 'X-Language': language.slice(0, 2) },
      body: audioBlob,
    });
    const result = await r.json();
    if (!r.ok) throw Error(result.error || 'Could not transcribe this recording.');
    if (token !== voiceToken) return;
    closeModal();
    go('assistant');
    document.querySelector('#question').value = result.text.slice(0, 2000);
    document.querySelector('#question').focus();
    notify('Your words are ready. Review them, then press Send.');
  } catch (e) {
    if (token === voiceToken) {
      showAudio();
      document.querySelector('#voice-error').textContent = e.message;
    }
  }
}

document.addEventListener('click', async (e) => {
  const el = e.target.closest('[data-page],[data-action]');
  if (!el) return;
  if (el.dataset.page) {
    e.preventDefault();
    go(el.dataset.page);
    return;
  }
  const { action } = el.dataset;
  try {
    switch (action) {
      case 'menu':
        menu = !menu;
        render();
        break;
      case 'open-assistant':
        go('assistant');
        break;
      case 'connect':
        go('connect');
        break;
      case 'close-modal':
        closeModal();
        break;
      case 'refresh':
        await refresh();
        break;
      case 'demo-link':
        notify('This is a sample shop. Connect ERPNext to open your actual billing records.');
        break;
      case 'item':
        showItem(el.dataset.code);
        break;
      case 'restock-draft':
        modal(
          'A restock list to review.',
          `<div class="help-content"><p>This is a local draft, not a supplier order.</p><pre class="draft-preview">${esc(restockText())}</pre><button class="btn primary full" data-action="download-restock">${icon('down')}Download my restock list</button></div>`,
        );
        break;
      case 'download-restock':
        download(restockText(), 'shopsage-restock-review.txt');
        break;
      case 'ask':
        await ask(el.dataset.question);
        break;
      case 'new-chat':
        if (!pending) {
          stopSpeech();
          messages = [];
          render();
        }
        break;
      case 'speak':
        speak(messages[Number(el.dataset.index)].text, Number(el.dataset.index));
        break;
      case 'stop-speech':
        stopSpeech();
        break;
      case 'test-voice':
        speak(
          language === 'hi-IN'
            ? 'नमस्ते! मैं आपके दुकान के काम को आसान बनाने में मदद करूँगा।'
            : 'Hello! Let’s make your shop day a little easier.',
        );
        break;
      case 'copy-answer':
        try {
          await navigator.clipboard.writeText(messages[Number(el.dataset.index)].text);
          notify('Copied. Review it before sharing.');
        } catch {
          notify('Copy is unavailable. Use Save draft instead.');
        }
        break;
      case 'save-answer':
        download(messages[Number(el.dataset.index)].text, 'shopsage-draft.txt');
        notify('Draft saved for your review.');
        break;
      case 'voice':
        voiceDialog();
        break;
      case 'record':
        await record();
        break;
      case 'stop-recording':
        if (recording?.state === 'recording') recording.stop();
        break;
      case 'transcribe':
        await transcribeAudio();
        break;
      case 'add-reminder':
        modal(
          'One less thing to remember.',
          `<form id="reminder-form" class="modal-form"><label>What needs doing?<input name="title" required maxlength="200" placeholder="Check tomorrow’s milk delivery"></label><label>When?<input name="due" type="date" required value="${snapshot()?.today || new Date().toLocaleDateString('en-CA')}"></label><div class="form-error" role="alert"></div><div class="form-actions"><button class="btn secondary" type="button" data-action="close-modal">Cancel</button><button class="btn primary">${icon('check')}Save reminder</button></div></form>`,
        );
        break;
      case 'toggle-reminder':
        el.disabled = true;
        state.reminders = (await request('reminder', { action: 'toggle', id: el.dataset.id })).reminders;
        render();
        break;
    }
  } catch (err) {
    notify(err.message);
    el.disabled = false;
  }
});
document.addEventListener('submit', async (e) => {
  if (e.target.id === 'chat-form') {
    e.preventDefault();
    await ask(new FormData(e.target).get('question'));
  }
  if (e.target.id === 'reminder-form') {
    e.preventDefault();
    const form = e.target;
    form.querySelector('button:not([type="button"])').disabled = true;
    try {
      state.reminders = (await request('reminder', Object.fromEntries(new FormData(form)))).reminders;
      closeModal();
      render();
      notify('A little less on your mind. Reminder saved.');
    } catch (err) {
      form.querySelector('.form-error').textContent = err.message;
      form.querySelector('button:not([type="button"])').disabled = false;
    }
  }
});
document.addEventListener('input', (e) => {
  if (e.target.id === 'filter-search') {
    const pos = e.target.selectionStart;
    query = e.target.value;
    render();
    const input = document.querySelector('#filter-search');
    input.focus();
    input.setSelectionRange(pos, pos);
  }
});
document.addEventListener('change', (e) => {
  if (['stock-filter', 'dues-filter', 'bill-filter'].includes(e.target.id)) {
    filter = e.target.value;
    render();
  }
  if (e.target.id === 'language') {
    language = e.target.value;
    localStorage.setItem('shopsage-language', language);
    stopSpeech();
  }
  if (e.target.id === 'voice-choice') {
    voiceName = e.target.value;
    localStorage.setItem('shopsage-voice', voiceName);
    stopSpeech();
  }
  if (e.target.id === 'auto-speak') {
    autoSpeak = e.target.checked;
    localStorage.setItem('shopsage-auto-speak', autoSpeak ? 'yes' : 'no');
  }
  if (e.target.id === 'audio-upload') {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 12_000_000) {
      document.querySelector('#voice-error').textContent = 'Choose a file smaller than 12 MB.';
      return;
    }
    voiceToken++;
    if (recording?.state === 'recording') recording.stop();
    recording = null;
    stopStream();
    const ext = file.name.split('.').pop().toLowerCase();
    const mime = {
      m4a: 'audio/mp4',
      mp3: 'audio/mpeg',
      wav: 'audio/wav',
      webm: 'audio/webm',
      ogg: 'audio/ogg',
    }[ext];
    audioBlob = new Blob([file], { type: mime || file.type });
    showAudio();
  }
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal();
    menu = false;
    document.querySelector('.sidebar')?.classList.remove('open');
    document.querySelector('.nav-scrim')?.remove();
  }
  if (e.key === 'Tab' && document.querySelector('.modal')) {
    const els = [...document.querySelectorAll('.modal button,.modal input,.modal a,.modal audio')].filter(
      (el) => !el.disabled && el.type !== 'hidden',
    );
    const first = els[0],
      last = els.at(-1);
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
});
document.querySelector('#overlay').addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) closeModal();
});
window.addEventListener('hashchange', () => {
  const next = location.hash.slice(1);
  if (next !== page) go(next);
});
window.addEventListener('beforeunload', () => {
  stopSpeech();
  stopStream();
});
(async () => {
  try {
    state = await request('state');
    render();
    if (page === 'connect') loadConnection();
  } catch (e) {
    document.querySelector('#app').innerHTML =
      `<div class="loading"><h1>Let’s reconnect.</h1><p>${esc(e.message)}</p><p>Start ShopSage with <code>python run.py</code>, then refresh.</p></div>`;
  }
})();
