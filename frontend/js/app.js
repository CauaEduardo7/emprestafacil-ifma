/**
 * EmprestaFácil — App Controller
 * Inicializa páginas e gerencia estado global
 */

import { Auth, Itens, Emprestimos, Perfil, Denuncias, Dashboard } from './api.js';
import {
  goTo, registerPage, showToast, setLoading,
  CATEGORIAS, CAMPUS_LABELS,
  getCatEmoji, getCatLabel, getCampusLabel,
  el, els, on, showError, clearErrors,
  relativeTime, statusBadge, initials,
  buildItemCard,
} from './utils.js';

/* ─────────────────────────────────────────
   Estado global da sessão
───────────────────────────────────────── */

let currentItemId = null;
let catalogParams = {};

/* ─────────────────────────────────────────
   Guard de autenticação
───────────────────────────────────────── */

function checkAuth() {
  if (!Auth.isLoggedIn()) {
    goTo('auth');
    return false;
  }
  return true;
}

/* ─────────────────────────────────────────
   Página: AUTH
───────────────────────────────────────── */

function initAuth() {
  if (Auth.isLoggedIn()) { goTo('home'); return; }

  // Tab switching
  els('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      els('.tab-btn').forEach(b => b.classList.remove('active'));
      els('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      el(`#tab-${btn.dataset.tab}`).classList.add('active');
    });
  });

  // Login
  on('#form-login', 'submit', async e => {
    e.preventDefault();
    clearErrors();
    const email = el('#login-email').value.trim();
    const password = el('#login-password').value;
    const btn = el('#btn-login');

    if (!email || !password) {
      showToast('Preencha todos os campos.', 'error');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Entrando...';
    try {
      await Auth.login(email, password);
      goTo('home');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Entrar';
    }
  });

  // Cadastro
  on('#form-cadastro', 'submit', async e => {
    e.preventDefault();
    clearErrors();

    const data = {
      nome: el('#cad-nome').value.trim(),
      matricula: el('#cad-matricula').value.trim(),
      email: el('#cad-email').value.trim(),
      telefone: el('#cad-telefone').value.trim(),
      curso: el('#cad-curso').value,
      campus: el('#cad-campus').value,
      password: el('#cad-senha').value,
      password2: el('#cad-senha2').value,
    };

    const required = ['nome', 'matricula', 'email', 'curso', 'campus', 'password', 'password2'];
    const missing = required.filter(k => !data[k]);
    if (missing.length) {
      showToast('Preencha todos os campos obrigatórios.', 'error');
      return;
    }

    const btn = el('#btn-cadastro');
    btn.disabled = true;
    btn.textContent = 'Criando conta...';
    try {
      await Auth.cadastro(data);
      showToast('Cadastro realizado! Bem-vindo ao EmprestaFácil!', 'success');
      goTo('home');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Criar conta';
    }
  });
}

/* ─────────────────────────────────────────
   Página: HOME (catálogo)
───────────────────────────────────────── */

async function initHome() {
  if (!checkAuth()) return;

  const user = Auth.getUser();
  if (user) {
    const avatar1 = el('#nav-avatar');
    const avatar2 = el('#nav-avatar-2');

    if (avatar1) {
      avatar1.textContent = initials(user.nome);
    }

    if (avatar2) {
      avatar2.textContent = initials(user.nome);
    }
  }

  catalogParams = {};
  await loadCatalog();

  // Search input — debounce 400ms
  let debounce = null;
  on('#search-input', 'input', e => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      catalogParams.busca = e.target.value.trim();
      catalogParams.page = 1;
      loadCatalog();
    }, 400);
  });

  // Category chips
  els('.cat-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      els('.cat-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      catalogParams.categoria = chip.dataset.cat || '';
      catalogParams.page = 1;
      loadCatalog();
    });
  });

  // Filter modal
  on('#btn-filter', 'click', () => {
    el('#modal-filter').classList.add('show');
  });

  on('#modal-filter-close', 'click', () => {
    el('#modal-filter').classList.remove('show');
  });

  on('#btn-apply-filter', 'click', () => {
    catalogParams.campus = el('#filter-campus').value;
    catalogParams.curso = el('#filter-curso').value;
    catalogParams.disponivel = el('#filter-disponivel').value;
    catalogParams.ordenar = el('#filter-order').value;
    catalogParams.page = 1;
    el('#modal-filter').classList.remove('show');
    loadCatalog();
  });

  on('#btn-clear-filter', 'click', () => {
    catalogParams = {};
    el('#filter-campus').value = '';
    el('#filter-curso').value = '';
    el('#filter-disponivel').value = '';
    el('#filter-order').value = 'recente';
    el('#modal-filter').classList.remove('show');
    loadCatalog();
  });

  // Promo banner → publish
  on('#btn-promo-publish', 'click', () => goTo('publish'));
}

async function loadCatalog() {
  const grid = el('#items-grid');
  setLoading(grid, true);

  try {
    const data = await Itens.listar(catalogParams);
    const items = data.results || data;

    if (!items.length) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1">
          <i class="ti ti-search-off"></i>
          <h3>Nenhum item encontrado</h3>
          <p>Tente outros filtros ou seja o primeiro a publicar!</p>
        </div>`;
      return;
    }

    grid.innerHTML = '';
    items.forEach(item => {
      const card = buildItemCard(item, openDetail);
      grid.appendChild(card);
    });

    // Pagination buttons
    renderPagination(data, el('#pagination'));
  } catch (err) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <i class="ti ti-wifi-off"></i>
      <h3>Erro ao carregar</h3>
      <p>${err.message}</p>
    </div>`;
  }
}

function renderPagination(data, container) {
  if (!container) return;
  if (!data.next && !data.previous) { container.innerHTML = ''; return; }

  const page = catalogParams.page || 1;
  container.innerHTML = `
    <div style="display:flex;gap:8px;justify-content:center;padding:8px 0 16px">
      <button class="btn btn-outline btn-sm" ${!data.previous ? 'disabled' : ''} id="pg-prev">← Anterior</button>
      <button class="btn btn-outline btn-sm" ${!data.next ? 'disabled' : ''} id="pg-next">Próximo →</button>
    </div>`;

  on('#pg-prev', 'click', () => {
    if (data.previous) { catalogParams.page = page - 1; loadCatalog(); }
  }, container);
  on('#pg-next', 'click', () => {
    if (data.next) { catalogParams.page = page + 1; loadCatalog(); }
  }, container);
}

/* ─────────────────────────────────────────
   Detalhe do item
───────────────────────────────────────── */

async function openDetail(item) {
  currentItemId = item.id;
  goTo('detail', { item });
}

async function initDetail({ item } = {}) {
  if (!checkAuth()) return;
  if (!currentItemId) { goTo('home'); return; }

  const container = el('#detail-container');
  setLoading(container, true);

  try {
    const data = await Itens.detalhe(currentItemId);
    renderDetail(data, container);
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><i class="ti ti-alert-circle"></i><h3>Erro</h3><p>${err.message}</p></div>`;
  }
}

function renderDetail(item, container) {
  const cat = CATEGORIAS[item.categoria] || { emoji: '📦' };
  const owner = item.dono || {};
  const avs = initials(owner.nome || '');
  const thumbSrc = item.foto ? `http://localhost:8000${item.foto}` : null;
  const user = Auth.getUser();

  container.innerHTML = `
    <div class="detail-hero">
      ${thumbSrc ? `<img src="${thumbSrc}" alt="${item.nome}">` : `<span>${cat.emoji}</span>`}
      <button class="back-btn" id="btn-back-detail"><i class="ti ti-arrow-left"></i></button>
    </div>
    <div class="detail-body">
      <h1 class="detail-title">${item.nome}</h1>
      <p class="detail-sub">${cat.emoji} ${getCatLabel(item.categoria)} · Publicado ${relativeTime(item.data_publicacao)}</p>

      <div class="meta-pills">
        <span class="meta-pill">${item.disponivel ? '✅ Disponível' : '🔴 Ocupado'}</span>
        <span class="meta-pill">${item.estado_display || item.estado}</span>
        <span class="meta-pill">Máx. ${item.prazo_maximo}</span>
      </div>

      <p class="desc-text">${item.descricao}</p>

      <div class="owner-block">
        <div class="owner-avatar">${avs}</div>
        <div class="owner-info">
          <h4>${owner.nome || 'Anunciante'}</h4>
          <p>${owner.curso_display || ''} · ${owner.campus_display || ''}</p>
          <p class="owner-badge">${owner.emprestimos_realizados || 0} empréstimos realizados</p>
        </div>
        <div class="owner-rating">
          <i class="ti ti-star-filled" style="font-size:20px;color:var(--gold-400)"></i>
          <span class="rate-val">${owner.avaliacao || '5.0'}</span>
          <span class="rate-count">(${owner.total_avaliacoes || 0})</span>
        </div>
      </div>

        <div class="price-block">
  <div>
    <div style="font-size:11px;color:var(--text-3)">Tipo de empréstimo</div>
    <div class="price-val">Gratuito</div>
  </div>
  <div style="text-align:right">
    <div style="font-size:11px;color:var(--text-3)">Prazo máximo</div>
    <div style="font-size:14px;font-weight:600">${item.prazo_maximo}</div>
  </div>
</div>

      ${item.dono?.id !== user?.id ? `
        <button class="btn btn-whatsapp" id="btn-contact" style="margin-bottom:10px">
          <i class="ti ti-brand-whatsapp"></i> Entrar em contato
        </button>
        <button class="btn btn-danger btn-sm" id="btn-report">
          <i class="ti ti-flag"></i> Denunciar anúncio
        </button>
      ` : `
        <button class="btn btn-secondary" id="btn-toggle-avail" style="margin-bottom:10px">
          ${item.disponivel ? '<i class="ti ti-eye-off"></i> Marcar como ocupado' : '<i class="ti ti-eye"></i> Marcar como disponível'}
        </button>
        <button class="btn btn-danger btn-sm" id="btn-remove-item">
          <i class="ti ti-trash"></i> Remover anúncio
        </button>
      `}
    </div>`;

  on('#btn-back-detail', 'click', () => goTo('home'), container);

  if (item.dono?.id !== user?.id) {
    const phone = item.dono?.telefone?.replace(/\D/g, '') || '';
    const msg = encodeURIComponent(`Olá! Vi seu anúncio do item "${item.nome}" no EmprestaFácil. Podemos combinar?`);
    on('#btn-contact', 'click', () => {
      if (phone) window.open(`https://wa.me/55${phone}?text=${msg}`, '_blank');
      else showToast('Telefone não disponível.', 'error');
    }, container);

    on('#btn-report', 'click', () => {
      el('#report-item-id').value = item.id;
      el('#modal-report').classList.add('show');
    }, container);
  } else {
    on('#btn-toggle-avail', 'click', async () => {
      try {
        await Itens.alterarDisponibilidade(item.id, !item.disponivel);
        showToast('Disponibilidade atualizada!', 'success');
        initDetail({});
      } catch (err) { showToast(err.message, 'error'); }
    }, container);

    on('#btn-remove-item', 'click', async () => {
      if (!confirm('Tem certeza que deseja remover este anúncio?')) return;
      try {
        await Itens.remover(item.id);
        showToast('Anúncio removido.', 'success');
        goTo('home');
      } catch (err) { showToast(err.message, 'error'); }
    }, container);
  }
}

/* ─────────────────────────────────────────
   Página: PUBLISH
───────────────────────────────────────── */

function initPublish() {
  if (!checkAuth()) return;

  // Evita registrar eventos várias vezes
  if (window.publishInitialized) return;
  window.publishInitialized = true;

  // Estado options
  els('.estado-opt').forEach(opt => {
    opt.addEventListener('click', () => {
      els('.estado-opt').forEach(o => o.classList.remove('active'));
      opt.classList.add('active');
    });
  });

  // Photo upload preview
  on('#photo-input', 'change', e => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = ev => {
      el('#upload-preview').style.backgroundImage = `url(${ev.target.result})`;
      el('#upload-preview').style.backgroundSize = 'cover';
      el('#upload-icon').style.display = 'none';
    };
    reader.readAsDataURL(file);
  });

  on('#form-publish', 'submit', async e => {
    e.preventDefault();
    clearErrors();

    const form = el('#form-publish');
    const btn = el('#btn-publish');

    if (form.dataset.submitting === 'true') return;
    form.dataset.submitting = 'true';

    const estado = el('.estado-opt.active')?.dataset.estado || 'bom';

    const fd = new FormData();
    fd.append('nome', el('#pub-nome').value.trim());
    fd.append('categoria', el('#pub-categoria').value);
    fd.append('descricao', el('#pub-descricao').value.trim());
    fd.append('prazo_maximo', el('#pub-prazo').value);
    fd.append('estado', estado);
    fd.append('disponivel', 'true');
    fd.append('observacoes', el('#pub-obs').value.trim());

    const photoFile = el('#photo-input')?.files?.[0];
    if (photoFile) fd.append('foto', photoFile);

    if (!fd.get('nome') || !fd.get('categoria') || !fd.get('descricao')) {
      showToast('Preencha nome, categoria e descrição.', 'error');
      form.dataset.submitting = 'false';
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Publicando...';

    try {
      await Itens.criar(fd);

      showToast('Anúncio publicado com sucesso!', 'success');

      form.reset();
      els('.estado-opt').forEach((o, i) => o.classList.toggle('active', i === 0));

      const preview = el('#upload-preview');
      const icon = el('#upload-icon');

      if (preview) preview.style.backgroundImage = '';
      if (icon) icon.style.display = '';

      goTo('home');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      form.dataset.submitting = 'false';
      btn.disabled = false;
      btn.textContent = 'Publicar anúncio';
    }
  });
}

async function initDashboard() {
  if (!checkAuth()) return;

  const container = el('#dashboard-container');
  setLoading(container, true);

  try {
    const data = await Dashboard.dados();
    renderDashboard(data, container);
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><i class="ti ti-wifi-off"></i><h3>Erro</h3><p>${err.message}</p></div>`;
  }
}

function renderDashboard(data, container) {
  const recentHtml = data.emprestimos_recentes.map(e => `
    <div class="list-item">
      <div class="list-icon">📦</div>
      <div class="list-info">
        <h4>${e.item}</h4>
        <p>${e.solicitante} → ${e.dono} · ${e.data}</p>
      </div>
      ${statusBadge(e.status)}
    </div>`).join('');

  const catHtml = data.itens_por_categoria.map(c => `
    <div class="list-item">
      <div class="list-icon">${getCatEmoji(c.categoria)}</div>
      <div class="list-info"><h4>${c.nome}</h4><p>${c.disponiveis} disponíveis de ${c.total}</p></div>
      <span style="font-size:13px;font-weight:600;color:var(--color-primary)">${c.total}</span>
    </div>`).join('');

  container.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-val">${data.total_alunos}</div><div class="stat-label">Alunos cadastrados</div><div class="stat-change up">↑ Crescendo</div></div>
      <div class="stat-card"><div class="stat-val">${data.total_itens}</div><div class="stat-label">Anúncios totais</div></div>
      <div class="stat-card"><div class="stat-val">${data.total_disponiveis}</div><div class="stat-label">Disponíveis agora</div><div class="stat-change up">↑ ${data.total_itens ? Math.round(data.total_disponiveis / data.total_itens * 100) : 0}%</div></div>
      <div class="stat-card"><div class="stat-val">${data.total_emprestimos}</div><div class="stat-label">Empréstimos totais</div></div>
    </div>
    <div class="section-header"><div class="section-title">Por categoria</div></div>
    <div class="card" style="margin:0 16px 12px">${catHtml || '<p class="text-muted p-4">Nenhum dado</p>'}</div>
    <div class="section-header"><div class="section-title">Empréstimos recentes</div></div>
    <div class="card" style="margin:0 16px 80px">${recentHtml || '<p class="text-muted p-4">Nenhum empréstimo ainda</p>'}</div>`;
}

/* ─────────────────────────────────────────
   Página: PERFIL
───────────────────────────────────────── */

async function initProfile() {
  if (!checkAuth()) return;

  const container = el('#profile-container');
  setLoading(container, true);

  try {
    const user = await Perfil.meu();
    Auth.updateLocalUser(user);
    renderProfile(user, container);
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><i class="ti ti-wifi-off"></i><h3>Erro</h3><p>${err.message}</p></div>`;
  }

  // Logout
  on('#btn-logout', 'click', async () => {
    await Auth.logout();
    goTo('auth');
  });
}

function renderProfile(user, container) {
  const avs = initials(user.nome);
  container.innerHTML = `
    <div class="profile-hero">
      <div style="display:flex;justify-content:flex-end;margin-bottom:12px">
        <i class="ti ti-settings" style="font-size:20px;cursor:pointer;opacity:.8"></i>
      </div>
      <div class="profile-avatar-lg">${avs}</div>
      <h1 class="profile-name">${user.nome}</h1>
      <p class="profile-course">${user.curso_display} · ${user.campus_display}</p>
      <span class="verified-badge"><i class="ti ti-shield-check" style="font-size:14px"></i> Aluno verificado</span>
    </div>
    <div class="profile-stats-row">
      <div class="pstat"><div class="val">${user.total_itens || 0}</div><div class="lbl">Anúncios</div></div>
      <div class="pstat"><div class="val">${user.emprestimos_realizados}</div><div class="lbl">Empréstimos</div></div>
      <div class="pstat"><div class="val" style="color:var(--gold-400)">${user.avaliacao} ⭐</div><div class="lbl">Avaliação</div></div>
    </div>
    <div class="info-section">
      <div class="info-section-header"><h3>Informações pessoais</h3><i class="ti ti-edit" style="font-size:18px;color:var(--text-3);cursor:pointer"></i></div>
      <div class="info-row"><i class="ti ti-id-badge"></i><div><div class="info-row-label">Matrícula</div><div class="info-row-val">${user.matricula}</div></div></div>
      <div class="info-row"><i class="ti ti-mail"></i><div><div class="info-row-label">E-mail institucional</div><div class="info-row-val">${user.email}</div></div></div>
      <div class="info-row"><i class="ti ti-phone"></i><div><div class="info-row-label">Telefone</div><div class="info-row-val">${user.telefone || 'Não informado'}</div></div></div>
      <div class="info-row"><i class="ti ti-building"></i><div><div class="info-row-label">Campus</div><div class="info-row-val">${user.campus_display}</div></div></div>
    </div>
    <div class="info-section" style="margin-bottom:8px">
      <div class="info-section-header"><h3>Meus anúncios</h3><span class="see-all" id="btn-my-items-detail">Ver todos</span></div>
      <div id="my-items-preview"></div>
    </div>
    <button class="btn btn-danger" style="margin:12px 16px;width:calc(100% - 32px)" id="btn-logout">
      <i class="ti ti-logout"></i> Sair da conta
    </button>
    <div style="height:80px"></div>`;

  // Load user's items preview
  loadMyItemsPreview(el('#my-items-preview'));

  on('#btn-logout', 'click', async () => {
    await Auth.logout();
    showToast('Até logo!');
    goTo('auth');
  }, container);

  on('#btn-my-items-detail', 'click', () => goTo('my-items'), container);
}

async function loadMyItemsPreview(container) {
  try {
    const data = await Itens.meusItens();
    const items = (data.results || data).slice(0, 3);
    if (!items.length) {
      container.innerHTML = '<p class="text-muted" style="padding:14px 16px">Você ainda não tem anúncios.</p>';
      return;
    }
    container.innerHTML = items.map(item => `
      <div class="list-item">
        <div class="list-icon">${getCatEmoji(item.categoria)}</div>
        <div class="list-info">
          <h4>${item.nome}</h4>
          <p>${formatMoney(item.valor)}/${item.periodo_display || item.periodo} · ${item.disponivel ? 'Disponível' : 'Ocupado'}</p>
        </div>
        <i class="ti ti-chevron-right" style="color:var(--text-3)"></i>
      </div>`).join('');
  } catch (_) { }
}

/* ─────────────────────────────────────────
   Modal: Denúncia
───────────────────────────────────────── */

function initReportModal() {
  on('#modal-report-close', 'click', () => el('#modal-report').classList.remove('show'));
  on('#btn-send-report', 'click', async () => {
    const itemId = el('#report-item-id').value;
    const motivo = el('#report-motivo').value;
    const desc = el('#report-desc').value.trim();

    if (!motivo || !desc) { showToast('Preencha motivo e descrição.', 'error'); return; }

    try {
      await Denuncias.criar({ item: itemId, motivo, descricao: desc });
      el('#modal-report').classList.remove('show');
      el('#report-motivo').value = '';
      el('#report-desc').value = '';
      showToast('Denúncia enviada. Obrigado!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

/* ─────────────────────────────────────────
   Registrar páginas e iniciar app
───────────────────────────────────────── */

registerPage('auth', initAuth);
registerPage('home', initHome);
registerPage('detail', initDetail);
registerPage('publish', initPublish);
registerPage('dashboard', initDashboard);
registerPage('profile', initProfile);

document.addEventListener('DOMContentLoaded', () => {
  // Bottom nav
  els('.bn-item[data-page]').forEach(btn => {
    btn.addEventListener('click', () => goTo(btn.dataset.page));
  });

  // Init report modal
  initReportModal();

  // Start
  localStorage.clear();
  sessionStorage.clear();
  goTo('auth');
}
)
