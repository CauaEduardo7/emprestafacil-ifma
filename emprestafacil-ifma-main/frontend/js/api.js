/**
 * EmprestaFácil — API Service
 */

const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('ef_token');
}

async function request(method, endpoint, data = null, isFormData = false) {
  const token = getToken();
  const headers = {};

  if (token) headers['Authorization'] = `Token ${token}`;
  if (!isFormData) headers['Content-Type'] = 'application/json';

  const options = { method, headers };

  if (data) {
    options.body = isFormData ? data : JSON.stringify(data);
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    const json = await res.json().catch(() => ({}));

    if (!res.ok) {
      const msg = extractError(json) || `Erro ${res.status}`;
      throw new Error(msg);
    }

    return json;
  } catch (err) {
    if (err.name === 'TypeError') {
      throw new Error('Servidor não encontrado. Verifique se o backend está rodando.');
    }
    throw err;
  }
}

function extractError(json) {
  if (!json || typeof json !== 'object') return null;
  const vals = Object.values(json);
  if (!vals.length) return null;
  const first = vals[0];
  if (Array.isArray(first)) return first[0];
  if (typeof first === 'string') return first;
  return JSON.stringify(json);
}

const get = endpoint => request('GET', endpoint);
const post = (endpoint, data, fd) => request('POST', endpoint, data, fd);
const put = (endpoint, data) => request('PUT', endpoint, data);
const patch = (endpoint, data) => request('PATCH', endpoint, data);
const del = endpoint => request('DELETE', endpoint);

const Auth = {
  async cadastro(data) {
    const res = await post('/auth/cadastro/', data);
    localStorage.setItem('ef_token', res.token);
    localStorage.setItem('ef_user', JSON.stringify(res.user));
    return res
  },

  async login(email, password) {
    const res = await post('/auth/login/', { email, password });
    localStorage.setItem('ef_token', res.token);
    localStorage.setItem('ef_user', JSON.stringify(res.user));
    return res;
  },

  async logout() {
    try {
      await post('/auth/logout/');
    } catch (_) {}

    localStorage.removeItem('ef_token');
    localStorage.removeItem('ef_user');
  },

  getUser() {
    const raw = localStorage.getItem('ef_user');
    return raw ? JSON.parse(raw) : null;
  },

  isLoggedIn() {
    return !!getToken();
  },

  updateLocalUser(user) {
    localStorage.setItem('ef_user', JSON.stringify(user));
  },
};

const Itens = {
  async listar(params = {}) {
    const qs = new URLSearchParams();

    Object.entries(params).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') {
        qs.set(k, v);
      }
    });

    const query = qs.toString() ? `?${qs}` : '';
    return get(`/itens/${query}`);
  },

  async detalhe(id) {
    return get(`/itens/${id}/`);
  },

  async meusItens() {
    return get('/meus-itens/');
  },

  async criar(formData) {
    return post('/meus-itens/', formData, true);
  },

  async atualizar(id, formData) {
    return put(`/meus-itens/${id}/`, formData, true);
  },

  async alterarDisponibilidade(id, disponivel) {
    return patch(`/meus-itens/${id}/`, { disponivel });
  },

  async remover(id) {
    return del(`/meus-itens/${id}/`);
  },
};

const Emprestimos = {
  async listar(tipo = 'solicitados') {
    return get(`/emprestimos/?tipo=${tipo}`);
  },

  async solicitar(item_id, prazo_combinado = '', observacoes = '') {
    return post('/emprestimos/', { item_id, prazo_combinado, observacoes });
  },

  async atualizarStatus(id, novo_status) {
    return patch(`/emprestimos/${id}/status/`, { status: novo_status });
  },
};

const Perfil = {
  async meu() {
    return get('/perfil/');
  },

  async atualizar(data) {
    return patch('/perfil/', data);
  },

  async aluno(id) {
    return get(`/alunos/${id}/`);
  },
};

const Denuncias = {
  async criar(data) {
    return post('/denuncias/', data);
  },
};

const Dashboard = {
  async dados() {
    return get('/dashboard/');
  },
};

const Admin = {
  async usuarios(busca = '') {
    const q = busca ? `?busca=${encodeURIComponent(busca)}` : '';
    return get(`/admin-api/usuarios/${q}`);
  },

  async toggleBloqueio(id) {
    return patch(`/admin-api/usuarios/${id}/bloqueio/`, {});
  },

  async denuncias() {
    return get('/admin-api/denuncias/');
  },
};

export { Auth, Itens, Emprestimos, Perfil, Denuncias, Dashboard, Admin };