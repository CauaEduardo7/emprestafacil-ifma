/**
 * EmprestaFácil — Utilitários e helpers de UI
 */

/* ─────────────────────────────────────────
   Navegação entre páginas
───────────────────────────────────────── */

const pages = {};

function registerPage(id, initFn) {
  pages[id] = initFn;
}

let currentPage = null;

function goTo(pageId, data = {}) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById(`page-${pageId}`);
  if (!el) return console.warn(`Página "${pageId}" não encontrada.`);

  el.classList.add('active');
  currentPage = pageId;

  document.querySelectorAll('.bn-item').forEach(b => {
    b.classList.toggle('active', b.dataset.page === pageId);
  });

  el.querySelector('.scroll-area')?.scrollTo(0, 0);

  if (pages[pageId]) pages[pageId](data);
}

/* ─────────────────────────────────────────
   Toast notifications
───────────────────────────────────────── */

let toastTimer = null;

function showToast(message, type = 'default') {
  let toast = document.getElementById('global-toast');

  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'global-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.className = `toast ${type}`;
  requestAnimationFrame(() => toast.classList.add('show'));

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
}

/* ─────────────────────────────────────────
   Loading state helpers
───────────────────────────────────────── */

function setLoading(container, loading) {
  if (loading) {
    container.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';
  }
}

/* ─────────────────────────────────────────
   Category helpers
───────────────────────────────────────── */

const CATEGORIAS = {
  livros: { label: 'Livros', emoji: '📚' },
  eletronicos: { label: 'Eletrônicos', emoji: '💻' },
  academicos: { label: 'Mat. Acadêmicos', emoji: '📐' },
  ferramentas: { label: 'Ferramentas', emoji: '🔧' },
  moveis: { label: 'Móveis', emoji: '🪑' },
  equipamentos: { label: 'Equipamentos', emoji: '⚙️' },
  outros: { label: 'Outros', emoji: '📦' },
};

const CAMPUS_LABELS = {
  monte_castelo: 'Monte Castelo',
  maracana: 'Maracanã',
  imperatriz: 'Imperatriz',
  caxias: 'Caxias',
  timon: 'Timon',
  bacabal: 'Bacabal',
  codo: 'Codó',
  acailandia: 'Açailândia',
  outro: 'Outro',
};

function getCatEmoji(cat) {
  return CATEGORIAS[cat]?.emoji || '📦';
}

function getCatLabel(cat) {
  return CATEGORIAS[cat]?.label || cat || 'Outro';
}

function getCampusLabel(c) {
  return CAMPUS_LABELS[c] || c || '';
}

/* ─────────────────────────────────────────
   DOM helpers
───────────────────────────────────────── */

function el(selector, parent = document) {
  return parent.querySelector(selector);
}

function els(selector, parent = document) {
  return [...parent.querySelectorAll(selector)];
}

function on(selector, event, handler, parent = document) {
  const elem = typeof selector === 'string' ? parent.querySelector(selector) : selector;
  if (elem) elem.addEventListener(event, handler);
}

function showError(fieldId, message) {
  const errEl = document.getElementById(`err-${fieldId}`);
  if (errEl) {
    errEl.textContent = message;
    errEl.classList.add('show');
  }
}

function clearErrors() {
  document.querySelectorAll('.form-error').forEach(e => e.classList.remove('show'));
}

/* ─────────────────────────────────────────
   Formatters
───────────────────────────────────────── */

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

function relativeTime(dateStr) {
  if (!dateStr) return '';

  const diff = (Date.now() - new Date(dateStr)) / 1000;

  if (diff < 60) return 'agora mesmo';
  if (diff < 3600) return `${Math.floor(diff / 60)} min atrás`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} dias atrás`;

  return formatDate(dateStr);
}

function statusBadge(status) {
  const map = {
    pendente: ['warning', 'Pendente'],
    ativo: ['success', 'Ativo'],
    atrasado: ['warning', 'Atrasado'],
    devolvido: ['info', 'Devolvido'],
    concluido: ['info', 'Concluído'],
    cancelado: ['danger', 'Cancelado'],
  };

  const [type, label] = map[status] || ['default', status];

  const colors = {
    warning: 'background:#fef3c7;color:#92400e',
    success: 'background:#e8f5ee;color:#0f5232',
    info: 'background:#eff6ff;color:#1e40af',
    danger: 'background:#fee2e2;color:#991b1b',
    default: 'background:#f3f4f6;color:#374151',
  };

  return `<span style="font-size:11px;font-weight:600;padding:3px 8px;border-radius:99px;${colors[type]}">${label}</span>`;
}

function initials(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase();
}

/* ─────────────────────────────────────────
   Item card HTML builder
───────────────────────────────────────── */

function buildItemCard(item, onClick) {
  console.log('ITEM:', item);
  console.log('FOTO:', item.foto);

  const cat = CATEGORIAS[item.categoria] || { emoji: '📦', label: 'Outro' };
  const avail = item.disponivel;

  const thumb = item.foto
  ? `<img src="${item.foto}" alt="${item.nome}" loading="lazy">`
  : `<span style="font-size:2.5rem">${cat.emoji}</span>`;

  const card = document.createElement('div');
  card.className = 'item-card';

  card.innerHTML = `
    <div class="card-thumb">
      ${thumb}
      <span class="status-badge ${avail ? 'available' : 'unavailable'}">
        ${avail ? 'Disponível' : 'Ocupado'}
      </span>
    </div>

    <div class="card-info">
      <div class="card-name">${item.nome}</div>
      <div class="card-meta">${item.dono?.campus_display || ''} · ${getCatLabel(item.categoria)}</div>

      <div class="card-footer">
        <div class="card-price">
          Empréstimo gratuito
        </div>

        <div class="card-rating">
          <i class="ti ti-star-filled"></i>
          ${item.dono?.avaliacao || item.dono?.avaliacao_media || '5.0'}
        </div>
      </div>
    </div>
  `;

  if (onClick) {
    card.addEventListener('click', () => onClick(item));
  }

  return card;
}

export {
  goTo,
  registerPage,
  showToast,
  setLoading,
  CATEGORIAS,
  CAMPUS_LABELS,
  getCatEmoji,
  getCatLabel,
  getCampusLabel,
  el,
  els,
  on,
  showError,
  clearErrors,
  formatDate,
  relativeTime,
  statusBadge,
  initials,
  buildItemCard,
};