# EmprestaFácil — IFMA

Sistema de empréstimos gratuitos entre alunos do Instituto Federal do Maranhão.

## Como rodar

```bash
# 1. Instalar dependências
pip install django djangorestframework django-cors-headers pillow

# 2. Aplicar migrações
python manage.py migrate

# 3. Popular dados de exemplo (opcional)
python seed.py

# 4. Iniciar servidor
python manage.py runserver
```

Acesse a API em: http://localhost:8000/api/
Frontend: abra frontend/index.html no navegador.

## Credenciais de exemplo
- Admin: admin@ifma.edu.br / admin123
- Aluno: joao.santos@acad.ifma.edu.br / senha123

## Endpoints da API

### Auth
| Método | URL | Descrição |
|--------|-----|-----------|
| POST | /api/auth/cadastro/ | Cadastro de aluno |
| POST | /api/auth/login/ | Login |
| POST | /api/auth/logout/ | Logout |

### Itens / Catálogo
| Método | URL | Descrição |
|--------|-----|-----------|
| GET | /api/itens/?busca=&categoria=&campus=&curso=&disponivel= | Listar catálogo com filtros |
| GET | /api/itens/<id>/ | Detalhe do item |
| GET/POST | /api/meus-itens/ | Meus anúncios |
| GET/PUT/DELETE | /api/meus-itens/<id>/ | Gerenciar meu item |

### Empréstimos
| Método | URL | Descrição |
|--------|-----|-----------|
| GET/POST | /api/emprestimos/?tipo=solicitados|cedidos | Listar / criar |
| PATCH | /api/emprestimos/<id>/status/ | Atualizar status |

### Avaliações
| Método | URL | Descrição |
|--------|-----|-----------|
| POST | /api/avaliacoes/ | Avaliar após devolução |
| GET | /api/avaliacoes/recebidas/ | Ver avaliações recebidas |
| GET | /api/alunos/<id>/avaliacoes/ | Avaliações públicas de um aluno |

### Relatório Semanal
| Método | URL | Descrição |
|--------|-----|-----------|
| GET | /api/relatorio/semanal/?semana=2025-W24 | Relatório da semana |
| GET | /api/relatorio/semanal/?formato=csv | Exportar CSV |

### Dashboard
| GET | /api/dashboard/ | Estatísticas gerais |

## Status dos Empréstimos
- **pendente** — Solicitado, aguardando confirmação
- **ativo** — Em andamento
- **atrasado** — Passou da data de devolução (automático)
- **devolvido** — Concluído com sucesso
- **cancelado** — Cancelado por qualquer parte

## Regras de Negócio
- Empréstimos 100% gratuitos — sem cobranças
- Apenas alunos com e-mail @ifma.edu.br ou @acad.ifma.edu.br
- Avaliação só disponível após status = devolvido
- Cada empréstimo pode ter apenas uma avaliação
- Ao marcar como devolvido: item fica disponível + contadores atualizados
- Relatório exportável em CSV com filtro por semana
